# app/services/rag_service.py

import asyncio
from typing import List, Optional, Dict, Literal, TypedDict
from motor.motor_asyncio import AsyncIOMotorDatabase
from langchain_google_vertexai import ChatVertexAI, VertexAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langgraph.graph import StateGraph, END
from app.core.logger import service_logger as logger
from app.core.log_helper import log_business_logic
from app.core.config import settings
from app.core.errors import ValidationError
from langchain_community.tools import QuerySQLDataBaseTool
from langchain_community.utilities import SQLDatabase
import re
import concurrent.futures

from app.services.document_service import DocumentService

class AgentState(TypedDict):
    """State definition for the RAG agent"""
    question: str
    context: List[str]
    sql_query: str
    result: str
    answer: str
    decision: Literal["rag", "sql"]

class RAGService:
    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize RAG service with necessary components"""
        self.db = db
        self.llm = ChatVertexAI(model="gemini-1.5-flash")
        self.embeddings = VertexAIEmbeddings(model="text-embedding-004")
        self.sql_db = SQLDatabase.from_uri(settings.DATABASE_URL)
        self.retriever = None
        self._initialize_components()
        # Initialize retriever on startup
        logger.info("RAG Service initialized")

    def _initialize_components(self):
        """Initialize LangChain components"""
        try:
            # Initialize text splitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )

            # Initialize workflow
            self.workflow = self._create_workflow()
            logger.debug("RAG components initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize RAG components", extra={
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise

    def _create_retriever(self, documents: List[dict]) -> FAISS:
        """Create FAISS retriever from documents"""
        try:
            splits = self.text_splitter.split_documents(documents)
            vectorstore = FAISS.from_documents(splits, self.embeddings)
            return vectorstore.as_retriever(search_kwargs={"k": 3})
        except Exception as e:
            logger.error("Failed to create retriever", extra={
                "error": str(e)
            })
            raise

    def _router_agent(self, state: AgentState) -> Dict:
        """Route question to appropriate processing method"""
        try:
            decision_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="You are a routing agent. Analyze the question and decide whether it should be answered using documents (RAG) or database (SQL)."),
                HumanMessage(content=f"Question: {state['question']}\n\nDecision (respond ONLY with 'rag' or 'sql'):")
            ])

            decision = (decision_prompt | self.llm | StrOutputParser()).invoke({
                "question": state["question"]
            }).strip().lower()

            if decision not in ["rag", "sql"]:
                raise ValidationError(f"Invalid decision: {decision}")

            logger.debug("Router decision made", extra={
                "decision": decision,
                "question": state["question"]
            })


            return {"decision": decision}

        except Exception as e:
            logger.error("Router agent error", extra={
                "error": str(e),
                "question": state["question"]
            })
            raise

    async def _rag_node(self, state: AgentState) -> Dict:
        """Process RAG-based queries"""
        try:
            await self.is_ready()
            if self.retriever is None:
                raise ValidationError("Knowledge base not initialized. Please ensure documents are loaded.")

            # Get relevant documents
            docs = self.retriever.invoke(state["question"])
            context = [doc.page_content for doc in docs]

            # Generate answer
            rag_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="You are a helpful assistant. Answer the question using the provided context."),
                HumanMessage(content=f"Question: {state['question']}\n\nContext: {context}\n\nAnswer:")
            ])

            answer = (rag_prompt | self.llm | StrOutputParser()).invoke({
                "question": state["question"],
                "context": context
            })

            logger.debug("RAG processing completed", extra={
                "question": state["question"],
                "context_length": len(context)
            })

            return {"answer": answer}

        except Exception as e:
            logger.error("RAG node error", extra={
                "error": str(e),
                "question": state["question"]
            })
            raise

    def _write_query(self, state: AgentState) -> Dict:
        """Generate SQL query based on question"""
        try:
            # Create SQL generation prompt
            sql_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=f"""You are a SQL expert. Generate a SQL query to answer the question.
                Available tables and schema: {self.sql_db.get_table_info()}"""),
                HumanMessage(content=f"Question: {state['question']}\n\nGenerate SQL query:")
            ])

            # Generate query
            sql_query = (sql_prompt | self.llm | StrOutputParser()).invoke({
                "question": state["question"]
            })

            # Clean up query
            sql_query = self._clean_sql_query(sql_query)

            logger.debug("SQL query generated", extra={
                "question": state["question"],
                "sql_query": sql_query
            })

            return {"sql_query": sql_query}
        except Exception as e:
            logger.error("SQL query generation error", extra={
                "error": str(e),
                "question": state["question"]
            })
            raise

    def _execute_query(self, state: AgentState) -> Dict:
        """Execute generated SQL query"""
        try:
            query_tool = QuerySQLDataBaseTool(db=self.sql_db)
            result = query_tool.invoke(state["sql_query"])

            logger.debug("SQL query executed", extra={
                "sql_query": state["sql_query"]
            })

            return {"result": result}
        except Exception as e:
            logger.error("SQL query execution error", extra={
                "error": str(e),
                "sql_query": state["sql_query"]
            })
            raise

    def _generate_sql_answer(self, state: AgentState) -> Dict:
        """Generate natural language answer from SQL results"""
        try:
            answer_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="You are a helpful assistant. Generate a natural language answer based on the SQL query results."),
                HumanMessage(content=f"""Question: {state['question']}
                SQL Query: {state['sql_query']}
                Query Result: {state['result']}
                
                Please provide a clear and concise answer:""")
            ])

            answer = (answer_prompt | self.llm | StrOutputParser()).invoke(state)

            logger.debug("SQL answer generated", extra={
                "question": state["question"]
            })

            return {"answer": answer}
        except Exception as e:
            logger.error("Answer generation error", extra={
                "error": str(e),
                "question": state["question"]
            })
            raise

    def _clean_sql_query(self, query: str) -> str:
        """Clean and format SQL query"""
        # Remove code blocks if present
        query = re.sub(r'```sql\s*|\s*```', '', query)
        # Remove leading/trailing whitespace
        query = query.strip()
        return query

    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow"""
        try:
            workflow = StateGraph(AgentState)
            
            # Add nodes
            workflow.add_node("decider", self._router_agent)
            workflow.add_node("rag_node", self._rag_node)
            workflow.add_node("write_query", self._write_query)
            workflow.add_node("execute_query", self._execute_query)
            workflow.add_node("generate_sql_answer", self._generate_sql_answer)
            
            # Set entry point and edges
            workflow.set_entry_point("decider")
            
            # Add conditional edges based on decision
            workflow.add_conditional_edges(
                "decider",
                lambda state: state["decision"],
                {
                    "rag": "rag_node",
                    "sql": "write_query"
                }
            )
            
            # Add SQL processing sequence
            workflow.add_edge("write_query", "execute_query")
            workflow.add_edge("execute_query", "generate_sql_answer")
            
            # Add terminal edges
            workflow.add_edge("rag_node", END)
            workflow.add_edge("generate_sql_answer", END)
            
            logger.info("Workflow created successfully")
            return workflow.compile()

        except Exception as e:
            logger.error("Failed to create workflow", extra={"error": str(e)})
            raise

    async def is_ready(self) -> bool:
        """Check if RAG service is ready to handle queries"""
        if self.retriever is None:
            await self.update_knowledge_base()
        return self.retriever is not None

    @log_business_logic("process_question")
    async def process_question(self, question: str) -> Dict:
        """Process a question through the RAG pipeline"""
        try:
            # Ensure service is ready

            response = await self.workflow.ainvoke({
                "question": question,
                "context": [],
                "sql_query": "",
                "result": "",
                "answer": "",
                "decision": ""
            })

            logger.info("Question processed successfully", extra={
                "question": question,
                "decision": response["decision"]
            })

            return {
                "answer": response["answer"],
                "decision": response["decision"]
            }

        except Exception as e:
            logger.error("Failed to process question", extra={
                "question": question,
                "error": str(e)
            })
            raise

    async def update_knowledge_base(self) -> None:
        """Update the knowledge base by loading stored vectorstores"""
        try:
            # Get all processed documents
            cursor = self.db["documents"].find({"status": "processed"}, {'_id': 1})
            documents = await cursor.to_list(length=None)
            
            if not documents:
                logger.warning("No processed documents found in database")
                return
            
            # Create combined vectorstore
            combined_vectorstore = None
            document_service = DocumentService(self.db)
            
            for doc in documents:
                try:
                    # Convert ObjectId to string for vectorstore loading
                    doc_id = str(doc["_id"])
                    
                    # Load vectorstore for each document
                    vectorstore = await document_service.load_vectorstore(doc_id)
                    
                    if combined_vectorstore is None:
                        combined_vectorstore = vectorstore
                    else:
                        # Merge vectorstores
                        combined_vectorstore.merge_from(vectorstore)
                        
                    logger.debug("Loaded vectorstore", extra={
                        "document_id": doc_id,
                    })
                    
                except Exception as e:
                    logger.error("Failed to load vectorstore", extra={
                        "document_id": str(doc["_id"]),
                        "error": str(e)
                    })
                    continue
            
            if combined_vectorstore:
                # Update retriever
                self.retriever = combined_vectorstore.as_retriever(
                    search_kwargs={"k": settings.RAG_TOP_K}
                )
                
                logger.info("Knowledge base updated", extra={
                    "document_count": len(documents)
                })
            else:
                logger.warning("No vectorstores could be loaded")
            
        except Exception as e:
            logger.error("Failed to update knowledge base", extra={"error": str(e)})
            raise