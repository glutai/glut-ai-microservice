# app/core/google_auth.py

import os
import json
from typing import Optional
from functools import lru_cache
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.auth.exceptions import DefaultCredentialsError
from app.core.config import settings
from app.core.logger import logger

class GoogleAuthHelper:
    """Helper class for Google Cloud authentication"""
    
    def __init__(self):
        self.credentials = None
        self._initialize_credentials()
        
    def _initialize_credentials(self):
        """Initialize Google Cloud credentials"""
        try:
            # First try getting credentials from environment variable
            if os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON'):
                logger.debug("Using credentials from GOOGLE_APPLICATION_CREDENTIALS_JSON")
                credentials_info = json.loads(os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON'))
                self.credentials = service_account.Credentials.from_service_account_info(
                    credentials_info,
                    scopes=['https://www.googleapis.com/auth/cloud-platform']
                )
                
            # Then try getting from a file path
            elif os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
                logger.debug("Using credentials from GOOGLE_APPLICATION_CREDENTIALS file")
                self.credentials = service_account.Credentials.from_service_account_file(
                    os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
                    scopes=['https://www.googleapis.com/auth/cloud-platform']
                )
                
            # Finally try getting from AWS Secrets Manager
            else:
                logger.debug("Attempting to get credentials from AWS Secrets Manager")
                credentials_info = self._get_credentials_from_aws()
                if credentials_info:
                    self.credentials = service_account.Credentials.from_service_account_info(
                        credentials_info,
                        scopes=['https://www.googleapis.com/auth/cloud-platform']
                    )
                    
            if not self.credentials:
                raise DefaultCredentialsError("No valid Google credentials found")
                
            logger.info("Google Cloud credentials initialized successfully")
            
        except Exception as e:
            logger.error("Error initializing Google credentials", extra={
                "error": str(e)
            })
            raise
            
    def _get_credentials_from_aws(self) -> Optional[dict]:
        """Get Google credentials from AWS Secrets Manager"""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            secret_name = os.getenv('GOOGLE_CREDENTIALS_SECRET_NAME')
            region_name = os.getenv('AWS_REGION', 'us-east-1')
            
            if not secret_name:
                logger.warning("GOOGLE_CREDENTIALS_SECRET_NAME not set")
                return None
                
            # Create a Secrets Manager client
            session = boto3.session.Session()
            client = session.client(
                service_name='secretsmanager',
                region_name=region_name
            )
            
            try:
                get_secret_value_response = client.get_secret_value(
                    SecretId=secret_name
                )
            except ClientError as e:
                logger.error("Error getting secret from AWS", extra={
                    "error": str(e)
                })
                raise
            else:
                if 'SecretString' in get_secret_value_response:
                    secret = get_secret_value_response['SecretString']
                    return json.loads(secret)
                    
            return None
            
        except Exception as e:
            logger.error("Error getting credentials from AWS", extra={
                "error": str(e)
            })
            return None
            
    def get_credentials(self):
        """Get the initialized credentials"""
        if self.credentials and self.credentials.expired:
            self.credentials.refresh(Request())
        return self.credentials
        
    def verify_credentials(self) -> bool:
        """Verify that credentials are valid"""
        try:
            if not self.credentials:
                return False
                
            # Force token refresh if expired
            if self.credentials.expired:
                self.credentials.refresh(Request())
                
            return True
        except Exception as e:
            logger.error("Error verifying credentials", extra={
                "error": str(e)
            })
            return False

@lru_cache()
def get_google_auth() -> GoogleAuthHelper:
    """Get or create GoogleAuthHelper instance"""
    return GoogleAuthHelper()