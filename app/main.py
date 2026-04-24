from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.schemas import QueryRequest, QueryResponse, UploadResponse
from app.rag import process_and_store_document, query_rag, stream_query_rag
import os
import traceback
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(title="RAG API", description="Retrieval-Augmented Generation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "RAG API is running"}

@app.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
    try:
        chunks_processed = await process_and_store_document(file)
        return UploadResponse(
            message=f"Successfully processed {file.filename}",
            chunks_processed=chunks_processed
        )
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def query_document(request: QueryRequest):
    if not os.getenv("GOOGLE_API_KEY"):
        raise HTTPException(status_code=500, detail="GOOGLE_API_KEY is not set")
        
    try:
        result = await query_rag(request.query)
        return QueryResponse(
            answer=result["answer"],
            source_documents=result["source_documents"]
        )
    except Exception as e:
        logger.error(f"Error querying RAG system: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error querying RAG system: {str(e)}")
@app.post("/stream-query")
async def stream_query(request: QueryRequest):
    """
    Endpoint for streaming RAG responses via Server-Sent Events (SSE).
    """
    if not os.getenv("GOOGLE_API_KEY"):
        raise HTTPException(status_code=500, detail="GOOGLE_API_KEY is not set")
        
    try:
        return StreamingResponse(
            stream_query_rag(request.query),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"Error in streaming query: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
