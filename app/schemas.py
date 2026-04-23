from pydantic import BaseModel
from typing import List

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    source_documents: List[str]

class UploadResponse(BaseModel):
    message: str
    chunks_processed: int
