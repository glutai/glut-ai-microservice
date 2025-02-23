from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from app.core.logger import db_logger as logger
from app.core.log_helper import log_database_query
from app.core.errors import NotFoundError

ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    model: Type[ModelType]
    collection_name: str = None

    @classmethod
    def get_collection(cls, db: AsyncIOMotorDatabase):
        if not hasattr(cls, 'collection_name') or cls.collection_name is None:
            error_msg = f"'collection_name' not set on {cls.__name__}"
            logger.error(error_msg)
            raise AttributeError(error_msg)
        return db[cls.collection_name]

    @classmethod
    @log_database_query("get_by_id")
    async def get(cls, db: AsyncIOMotorDatabase, id: str) -> Optional[ModelType]:
        try:
            collection = cls.get_collection(db)
            obj = await collection.find_one({"_id": ObjectId(id)})
            if obj:
                logger.debug("Document found", extra={
                    "collection": cls.collection_name,
                    "id": id
                })
                return cls.model(**obj)
            logger.debug("Document not found", extra={
                "collection": cls.collection_name,
                "id": id
            })
            return None
        except Exception as e:
            logger.error("Error retrieving document", extra={
                "collection": cls.collection_name,
                "id": id,
                "error": str(e)
            })
            raise

    @classmethod
    @log_database_query("get_by_query")
    async def get_by_query(
        cls, 
        db: AsyncIOMotorDatabase, 
        query: Dict,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        try:
            collection = cls.get_collection(db)
            cursor = collection.find(query).skip(skip).limit(limit)
            results = await cursor.to_list(length=limit)
            
            logger.debug("Query executed successfully", extra={
                "collection": cls.collection_name,
                "query": str(query),
                "results_count": len(results)
            })
            
            return [cls.model(**result) for result in results]
        except Exception as e:
            logger.error("Error executing query", extra={
                "collection": cls.collection_name,
                "query": str(query),
                "error": str(e)
            })
            raise

    @classmethod
    @log_database_query("create")
    async def create(
        cls, 
        db: AsyncIOMotorDatabase, 
        obj_in: Union[CreateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        try:
            obj_in_data = obj_in.model_dump() if isinstance(obj_in, BaseModel) else obj_in
            collection = cls.get_collection(db)
            
            result = await collection.insert_one(obj_in_data)
            obj_in_data["_id"] = result.inserted_id
            
            logger.debug("Document created successfully", extra={
                "collection": cls.collection_name,
                "id": str(result.inserted_id)
            })
            
            return cls.model(**obj_in_data)
        except Exception as e:
            logger.error("Error creating document", extra={
                "collection": cls.collection_name,
                "error": str(e)
            })
            raise

    @classmethod
    @log_database_query("update")
    async def update(
        cls,
        db: AsyncIOMotorDatabase,
        id: str,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        try:
            obj_data = obj_in.dict(exclude_unset=True) if isinstance(obj_in, BaseModel) else obj_in
            collection = cls.get_collection(db)
            
            result = await collection.update_one(
                {"_id": ObjectId(id)},
                {"$set": obj_data}
            )
            
            if result.modified_count == 0:
                logger.warning("Document not found for update", extra={
                    "collection": cls.collection_name,
                    "id": id
                })
                raise NotFoundError(f"Document with id {id} not found")
                
            updated_doc = await collection.find_one({"_id": ObjectId(id)})
            
            logger.debug("Document updated successfully", extra={
                "collection": cls.collection_name,
                "id": id,
                "modified_count": result.modified_count
            })
            
            return cls.model(**updated_doc)
        except Exception as e:
            logger.error("Error updating document", extra={
                "collection": cls.collection_name,
                "id": id,
                "error": str(e)
            })
            raise

    @classmethod
    @log_database_query("delete")
    async def delete(cls, db: AsyncIOMotorDatabase, id: str) -> bool:
        try:
            collection = cls.get_collection(db)
            result = await collection.delete_one({"_id": ObjectId(id)})
            
            success = result.deleted_count > 0
            log_level = logger.debug if success else logger.warning
            
            log_level(
                "Document deletion attempt",
                extra={
                    "collection": cls.collection_name,
                    "id": id,
                    "success": success,
                    "deleted_count": result.deleted_count
                }
            )
            
            return success
        except Exception as e:
            logger.error("Error deleting document", extra={
                "collection": cls.collection_name,
                "id": id,
                "error": str(e)
            })
            raise