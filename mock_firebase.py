"""
Mock Firebase service for testing authentication endpoints
"""
from typing import Optional, Dict, Any, List
from datetime import datetime

class MockFirebaseService:
    """Mock Firebase service for testing"""
    
    def __init__(self):
        self.data = {}
    
    async def set_document(self, collection: str, document_id: str, data: Dict[str, Any]):
        """Set document in mock storage"""
        if collection not in self.data:
            self.data[collection] = {}
        self.data[collection][document_id] = data
        return True
    
    async def get_document(self, collection: str, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document from mock storage"""
        if collection in self.data and document_id in self.data[collection]:
            return self.data[collection][document_id]
        return None
    
    async def update_document(self, collection: str, document_id: str, data: Dict[str, Any]):
        """Update document in mock storage"""
        if collection not in self.data:
            self.data[collection] = {}
        if document_id not in self.data[collection]:
            self.data[collection][document_id] = {}
        self.data[collection][document_id].update(data)
        return True
    
    async def query_collection(self, collection: str, filters: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Query collection from mock storage"""
        if collection not in self.data:
            return []
        
        results = []
        for doc_id, doc_data in self.data[collection].items():
            doc_data['id'] = doc_id
            
            if filters:
                match = True
                for filter_item in filters:
                    field = filter_item.get('field')
                    operator = filter_item.get('operator', '==')
                    value = filter_item.get('value')
                    
                    if field in doc_data:
                        if operator == '==' and doc_data[field] != value:
                            match = False
                            break
                        elif operator == '!=' and doc_data[field] == value:
                            match = False
                            break
                
                if match:
                    results.append(doc_data)
            else:
                results.append(doc_data)
        
        return results
    
    async def delete_document(self, collection: str, document_id: str):
        """Delete document from mock storage"""
        if collection in self.data and document_id in self.data[collection]:
            del self.data[collection][document_id]
            return True
        return False
