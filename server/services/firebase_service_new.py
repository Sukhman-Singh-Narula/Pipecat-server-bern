"""
Simplified Firebase service for handling database operations
"""
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
import json
import os
from loguru import logger

from server.config.settings import get_settings


class FirebaseService:
    """Simplified Firebase service with in-memory fallback"""
    
    def __init__(self):
        self.settings = get_settings()
        self.db = None
        self.use_firebase = False
        
        # In-memory storage for when Firebase is not available
        self._storage: Dict[str, Dict[str, Any]] = {}
        
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK or use in-memory storage"""
        try:
            # Try to initialize Firebase if credentials exist
            if os.path.exists(self.settings.firebase_credentials_path):
                import firebase_admin
                from firebase_admin import credentials, firestore
                
                try:
                    firebase_admin.get_app()
                    logger.info("Firebase already initialized")
                except ValueError:
                    cred = credentials.Certificate(self.settings.firebase_credentials_path)
                    firebase_admin.initialize_app(cred)
                    logger.info("Firebase initialized successfully")
                
                self.db = firestore.client()
                self.use_firebase = True
                logger.info("✅ Firebase Firestore connected")
            else:
                logger.info("Firebase credentials not found, using in-memory storage")
                self.use_firebase = False
                
        except ImportError:
            logger.warning("Firebase Admin SDK not installed, using in-memory storage")
            self.use_firebase = False
        except Exception as e:
            logger.error(f"Firebase initialization failed: {e}")
            self.use_firebase = False
    
    async def set_document(self, collection: str, document_id: str, data: Dict[str, Any]) -> None:
        """Set a document in a collection"""
        try:
            if self.use_firebase:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.db.collection(collection).document(document_id).set(data)
                )
            else:
                # Use in-memory storage with collection namespacing
                if collection not in self._storage:
                    self._storage[collection] = {}
                self._storage[collection][document_id] = data
            
            logger.info(f"Document set: {collection}/{document_id}")
        except Exception as e:
            logger.error(f"Failed to set document {collection}/{document_id}: {e}")
            raise e

    async def get_document(self, collection: str, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a document from a collection"""
        try:
            if self.use_firebase:
                doc_ref = self.db.collection(collection).document(document_id)
                doc = await asyncio.get_event_loop().run_in_executor(None, doc_ref.get)
                if doc.exists:
                    return doc.to_dict()
                return None
            else:
                # Get from in-memory storage
                collection_data = self._storage.get(collection, {})
                return collection_data.get(document_id)
        except Exception as e:
            logger.error(f"Failed to get document {collection}/{document_id}: {e}")
            return None

    async def update_document(self, collection: str, document_id: str, data: Dict[str, Any]) -> None:
        """Update a document in a collection"""
        try:
            if self.use_firebase:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.db.collection(collection).document(document_id).update(data)
                )
            else:
                # Update in-memory storage
                if collection not in self._storage:
                    self._storage[collection] = {}
                if document_id in self._storage[collection]:
                    self._storage[collection][document_id].update(data)
                else:
                    self._storage[collection][document_id] = data
            
            logger.info(f"Document updated: {collection}/{document_id}")
        except Exception as e:
            logger.error(f"Failed to update document {collection}/{document_id}: {e}")
            raise e

    async def delete_document(self, collection: str, document_id: str) -> None:
        """Delete a document from a collection"""
        try:
            if self.use_firebase:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.db.collection(collection).document(document_id).delete()
                )
            else:
                # Delete from in-memory storage
                if collection in self._storage and document_id in self._storage[collection]:
                    del self._storage[collection][document_id]
            
            logger.info(f"Document deleted: {collection}/{document_id}")
        except Exception as e:
            logger.error(f"Failed to delete document {collection}/{document_id}: {e}")
            raise e

    async def query_collection(self, collection: str, filters: List[tuple]) -> List[Dict[str, Any]]:
        """Query a collection with filters"""
        try:
            if self.use_firebase:
                query = self.db.collection(collection)
                for field, operator, value in filters:
                    query = query.where(field, operator, value)
                
                docs = await asyncio.get_event_loop().run_in_executor(None, query.get)
                return [doc.to_dict() for doc in docs]
            else:
                # Simple in-memory filtering
                collection_data = self._storage.get(collection, {})
                results = []
                for doc_data in collection_data.values():
                    match = True
                    for field, operator, value in filters:
                        doc_value = doc_data.get(field)
                        if operator == "==" and doc_value != value:
                            match = False
                            break
                        elif operator == ">" and doc_value <= value:
                            match = False
                            break
                        elif operator == "<" and doc_value >= value:
                            match = False
                            break
                    if match:
                        results.append(doc_data)
                return results
        except Exception as e:
            logger.error(f"Failed to query collection {collection}: {e}")
            return []

    async def get_all_documents(self, collection: str) -> List[Dict[str, Any]]:
        """Get all documents from a collection"""
        try:
            if self.use_firebase:
                docs = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.db.collection(collection).get()
                )
                return [doc.to_dict() for doc in docs]
            else:
                # Get all from in-memory storage
                collection_data = self._storage.get(collection, {})
                return list(collection_data.values())
        except Exception as e:
            logger.error(f"Failed to get all documents from {collection}: {e}")
            return []

    async def health_check(self) -> bool:
        """Check if the service is healthy"""
        try:
            if self.use_firebase:
                # Try a simple read operation
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.db.collection('health_check').limit(1).get()
                )
            return True
        except Exception:
            return False


# Global service instance
_firebase_service: Optional[FirebaseService] = None


def get_firebase_service() -> FirebaseService:
    """Get Firebase service singleton"""
    global _firebase_service
    if _firebase_service is None:
        _firebase_service = FirebaseService()
    return _firebase_service
