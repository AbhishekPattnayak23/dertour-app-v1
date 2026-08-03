from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from uuid import uuid4


class KnowledgeDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    partition_key: str = Field(alias="partitionKey")
    title: str
    content: str
    document_type: str = Field(alias="documentType")
    source_url: Optional[str] = Field(None, alias="sourceUrl")
    file_path: Optional[str] = Field(None, alias="filePath")
    chunk_index: Optional[int] = Field(None, alias="chunkIndex")
    total_chunks: Optional[int] = Field(None, alias="totalChunks")
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")
    version: int = 1
    is_active: bool = Field(True, alias="isActive")
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def to_cosmos_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format suitable for Cosmos DB"""
        data = self.dict(by_alias=True)
        data["_ts"] = int(self.updated_at.timestamp())
        return data
    
    @classmethod
    def from_cosmos_dict(cls, data: Dict[str, Any]) -> "KnowledgeDocument":
        """Create instance from Cosmos DB dictionary"""
        # Remove Cosmos DB system fields
        cosmos_fields = ["_rid", "_self", "_etag", "_attachments", "_ts"]
        for field in cosmos_fields:
            data.pop(field, None)
        
        # Convert datetime strings back to datetime objects
        if isinstance(data.get("createdAt"), str):
            data["createdAt"] = datetime.fromisoformat(data["createdAt"])
        if isinstance(data.get("updatedAt"), str):
            data["updatedAt"] = datetime.fromisoformat(data["updatedAt"])
            
        return cls(**data)
    
    def update_embedding(self, embedding: List[float]) -> None:
        """Update the document embedding and timestamp"""
        self.embedding = embedding
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata field"""
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the document"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.utcnow()
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the document"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Mark document as inactive"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """Mark document as active"""
        self.is_active = True
        self.updated_at = datetime.utcnow()