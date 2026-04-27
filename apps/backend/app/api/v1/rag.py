"""RAG API routes for LMS."""

import logging
import time
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import tempfile
from pathlib import Path

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.rag import RAGDocument, RAGChunk, RAGSearchSession, RAGSearchResult
from app.schemas.rag import (
    RAGSearchRequest,
    RAGSearchResponse,
    RAGChunkResponse,
    RAGDocumentResponse,
    RAGIngestionResponse,
    RAGStatsResponse,
)
from llm.rag.service import get_rag_service


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/rag", tags=["RAG"])


@router.post("/upload", response_model=RAGIngestionResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    course_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RAGIngestionResponse:
    """Upload a PDF document for RAG indexing.
    
    Args:
        file: PDF file to upload
        title: Document title
        course_id: Associated course ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Ingestion result
    """
    try:
        # Validate file type
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # Get RAG service
            rag_service = get_rag_service()
            
            # Ingest PDF
            result = rag_service.ingest_pdf(
                pdf_path=tmp_path,
                document_id=f"doc_{file.filename.replace('.pdf', '').replace(' ', '_')[:50]}",
            )
            
            if result['status'] == 'success':
                # Store metadata in database
                doc_title = title or file.filename.replace('.pdf', '')
                
                rag_doc = RAGDocument(
                    doc_id=result['document_id'],
                    title=doc_title,
                    source_path=file.filename,
                    source_type="pdf",
                    course_id=course_id,
                    chunks_count=result['chunks'],
                    total_tokens=result['total_tokens'],
                    metadata={
                        'uploaded_by': current_user.id,
                        'original_filename': file.filename,
                    }
                )
                
                db.add(rag_doc)
                db.commit()
                
                logger.info(f"[RAG API] Document uploaded: {result['document_id']}")
                
                return RAGIngestionResponse(
                    status="success",
                    document_id=result['document_id'],
                    title=doc_title,
                    pages=result['pages'],
                    chunks=result['chunks'],
                    total_tokens=result['total_tokens'],
                    message=result['message'],
                )
            else:
                logger.error(f"[RAG API] Ingestion failed: {result.get('error', 'Unknown error')}")
                raise HTTPException(status_code=400, detail=result.get('error', 'Ingestion failed'))
                
        finally:
            # Clean up temporary file
            Path(tmp_path).unlink(missing_ok=True)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[RAG API] Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=RAGSearchResponse)
async def search(
    request: RAGSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RAGSearchResponse:
    """Search using RAG system.
    
    Args:
        request: Search request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Search results
    """
    try:
        start_time = time.time()
        
        # Get RAG service
        rag_service = get_rag_service()
        
        # Perform search
        result = rag_service.search(
            query=request.query,
            top_k=request.top_k,
            document_id=request.document_id,
        )
        
        execution_time = time.time() - start_time
        
        if result['status'] == 'success':
            # Log search session
            search_session = RAGSearchSession(
                user_id=current_user.id,
                query=request.query,
                results_count=len(result['results']),
                search_duration_ms=int(execution_time * 1000),
            )
            
            db.add(search_session)
            db.flush()  # Get the session ID
            
            # Log individual results
            for rank, res in enumerate(result['results'], 1):
                search_result = RAGSearchResult(
                    session_id=search_session.id,
                    chunk_id=res.get('chunk_id', ''),
                    relevance_score=res.get('relevance', 0.0),
                    rank=rank,
                )
                db.add(search_result)
            
            db.commit()
            
            logger.info(f"[RAG API] Search completed: {len(result['results'])} results in {execution_time:.2f}s")
            
            return RAGSearchResponse(
                status="success",
                query=request.query,
                results_count=len(result['results']),
                results=[
                    RAGChunkResponse(
                        chunk_id=res['chunk_id'],
                        content=res['content'][:500],  # Truncate for API
                        page_number=res.get('page_number'),
                        chunk_type="reference",
                        tokens_count=0,
                        relevance=res['relevance'],
                    )
                    for res in result['results']
                ],
                execution_time_ms=execution_time * 1000,
            )
        else:
            logger.warning(f"[RAG API] Search failed: {result.get('error', 'Unknown error')}")
            raise HTTPException(status_code=400, detail=result.get('error', 'Search failed'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[RAG API] Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents", response_model=List[RAGDocumentResponse])
async def list_documents(
    course_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[RAGDocumentResponse]:
    """List all RAG documents.
    
    Args:
        course_id: Optional course filter
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of documents
    """
    try:
        query = db.query(RAGDocument).filter(RAGDocument.is_active == 1)
        
        if course_id:
            query = query.filter(RAGDocument.course_id == course_id)
        
        documents = query.all()
        
        return [
            RAGDocumentResponse(
                doc_id=doc.doc_id,
                title=doc.title or "Untitled",
                description=doc.description,
                source_type=doc.source_type,
                chunks_count=doc.chunks_count,
                total_tokens=doc.total_tokens,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
            )
            for doc in documents
        ]
        
    except Exception as e:
        logger.error(f"[RAG API] List documents error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a RAG document.
    
    Args:
        doc_id: Document ID to delete
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success response
    """
    try:
        # Get document from DB
        doc = db.query(RAGDocument).filter(RAGDocument.doc_id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete from vector store
        rag_service = get_rag_service()
        rag_service.delete_document(doc_id)
        
        # Mark as inactive in DB
        doc.is_active = 0
        db.commit()
        
        logger.info(f"[RAG API] Document deleted: {doc_id}")
        
        return {"status": "success", "message": f"Document {doc_id} deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[RAG API] Delete error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=RAGStatsResponse)
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RAGStatsResponse:
    """Get RAG system statistics.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Statistics
    """
    try:
        # Get counts from database
        total_docs = db.query(RAGDocument).filter(RAGDocument.is_active == 1).count()
        total_chunks = db.query(RAGChunk).count()
        total_tokens = db.query(func.sum(RAGDocument.total_tokens)).scalar() or 0
        search_count = db.query(RAGSearchSession).count()
        
        # Get average relevance from search results
        avg_relevance = db.query(func.avg(RAGSearchResult.relevance_score)).scalar() or 0.0
        
        return RAGStatsResponse(
            total_documents=total_docs,
            total_chunks=total_chunks,
            total_tokens=int(total_tokens),
            search_count=search_count,
            avg_relevance=float(avg_relevance),
            system_status="ready",
        )
        
    except Exception as e:
        logger.error(f"[RAG API] Stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


from sqlalchemy import func
