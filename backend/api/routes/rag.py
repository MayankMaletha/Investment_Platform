"""api/routes/rag.py — RAG document ingestion and Q&A endpoints."""

from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db, get_current_user
from core.exceptions import ValidationError
from database.models.models import User
from schemas.schemas import RAGQueryRequest, RAGQueryResponse, DocumentUploadResponse
from rag.pipeline import RAGPipeline

router = APIRouter()

@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(default="annual_report"),
    company: str = Form(default=""),
    year: str = Form(default=""),
    current_user: User = Depends(get_current_user),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise ValidationError("Only PDF files are supported")
    content = await file.read()
    return await RAGPipeline().ingest_document(
        content=content, filename=file.filename,
        metadata={"user_id": current_user.id, "document_type": document_type, "company": company, "year": year},
    )

@router.post("/query", response_model=RAGQueryResponse)
async def query_documents(request: RAGQueryRequest, current_user: User = Depends(get_current_user)):
    return await RAGPipeline().query(query=request.query, top_k=request.top_k,
                                      user_id=current_user.id, document_ids=request.document_ids)

@router.get("/documents")
async def list_documents(current_user: User = Depends(get_current_user)):
    docs = await RAGPipeline().list_documents(user_id=current_user.id)
    return {"documents": docs}
