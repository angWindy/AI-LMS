"""
RAG Integration Examples for LMS Components

This file shows how to integrate RAG with specific LMS features:
lesson content, assignments, and the chatbot.
"""

# ============================================================================
# 1. LESSON INTEGRATION
# ============================================================================

from sqlalchemy.orm import Session
from app.models.lesson import Lesson
from app.models.rag import RAGDocument, RAGIntegration
from llm.rag.service import get_rag_service


def attach_rag_to_lesson(
    db: Session,
    lesson_id: int,
    document_id: int,
    integration_type: str = "supplementary"
) -> RAGIntegration:
    """Attach a RAG document to a lesson for student reference.
    
    Args:
        db: Database session
        lesson_id: Lesson ID
        document_id: RAG document ID
        integration_type: "required", "supplementary", or "reference"
        
    Returns:
        RAGIntegration model
    """
    integration = RAGIntegration(
        lesson_id=lesson_id,
        document_id=document_id,
        integration_type=integration_type,
    )
    
    db.add(integration)
    db.commit()
    
    return integration


def get_lesson_rag_documents(
    db: Session,
    lesson_id: int
) -> list[RAGDocument]:
    """Get all RAG documents attached to a lesson.
    
    Args:
        db: Database session
        lesson_id: Lesson ID
        
    Returns:
        List of RAG documents
    """
    integrations = db.query(RAGIntegration)\
        .filter(RAGIntegration.lesson_id == lesson_id)\
        .filter(RAGIntegration.is_active == 1)\
        .all()
    
    doc_ids = [i.document_id for i in integrations]
    
    documents = db.query(RAGDocument)\
        .filter(RAGDocument.id.in_(doc_ids))\
        .filter(RAGDocument.is_active == 1)\
        .all()
    
    return documents


def search_lesson_content(
    db: Session,
    lesson_id: int,
    query: str,
    top_k: int = 3
) -> dict:
    """Search within a lesson's RAG documents.
    
    Args:
        db: Database session
        lesson_id: Lesson ID
        query: Search query
        top_k: Number of results
        
    Returns:
        Search results
    """
    # Get lesson's RAG documents
    documents = get_lesson_rag_documents(db, lesson_id)
    
    if not documents:
        return {
            'status': 'no_documents',
            'results': [],
            'message': 'No RAG documents attached to this lesson'
        }
    
    # Search each document
    rag = get_rag_service()
    all_results = []
    
    for doc in documents:
        doc_results = rag.search(
            query=query,
            top_k=top_k,
            document_id=doc.doc_id
        )
        
        if doc_results['status'] == 'success':
            all_results.extend(doc_results['results'])
    
    # Sort by relevance and return top K
    all_results.sort(key=lambda x: x['relevance'], reverse=True)
    
    return {
        'status': 'success',
        'query': query,
        'results_count': len(all_results[:top_k]),
        'results': all_results[:top_k]
    }


# Example usage in lesson endpoint:
"""
@router.get("/lessons/{lesson_id}/search")
async def search_lesson(
    lesson_id: int,
    q: str,  # query
    db: Session = Depends(get_db),
):
    results = search_lesson_content(db, lesson_id, q)
    return results
"""


# ============================================================================
# 2. ASSIGNMENT INTEGRATION
# ============================================================================

from app.models.assignment import Assignment


def attach_rag_to_assignment(
    db: Session,
    assignment_id: int,
    document_id: int,
    integration_type: str = "reference"
) -> RAGIntegration:
    """Attach reference materials to an assignment.
    
    Args:
        db: Database session
        assignment_id: Assignment ID
        document_id: RAG document ID
        integration_type: "required", "supplementary", or "reference"
        
    Returns:
        RAGIntegration model
    """
    integration = RAGIntegration(
        assignment_id=assignment_id,
        document_id=document_id,
        integration_type=integration_type,
    )
    
    db.add(integration)
    db.commit()
    
    return integration


def get_assignment_rag_documents(
    db: Session,
    assignment_id: int
) -> list[RAGDocument]:
    """Get all RAG documents attached to an assignment.
    
    Args:
        db: Database session
        assignment_id: Assignment ID
        
    Returns:
        List of RAG documents
    """
    integrations = db.query(RAGIntegration)\
        .filter(RAGIntegration.assignment_id == assignment_id)\
        .filter(RAGIntegration.is_active == 1)\
        .all()
    
    doc_ids = [i.document_id for i in integrations]
    
    documents = db.query(RAGDocument)\
        .filter(RAGDocument.id.in_(doc_ids))\
        .filter(RAGDocument.is_active == 1)\
        .all()
    
    return documents


def suggest_assignment_resources(
    db: Session,
    assignment_id: int,
) -> dict:
    """Get relevant resources for completing an assignment.
    
    Args:
        db: Database session
        assignment_id: Assignment ID
        
    Returns:
        Resource suggestions
    """
    assignment = db.query(Assignment).get(assignment_id)
    if not assignment:
        return {'error': 'Assignment not found'}
    
    # Search attached documents for assignment description
    rag = get_rag_service()
    
    documents = get_assignment_rag_documents(db, assignment_id)
    results = []
    
    for doc in documents:
        doc_results = rag.search(
            query=assignment.description or assignment.title,
            top_k=3,
            document_id=doc.doc_id
        )
        
        if doc_results['status'] == 'success':
            results.extend(doc_results['results'])
    
    return {
        'assignment_id': assignment_id,
        'assignment': assignment.title,
        'suggested_resources': results[:5]
    }


# ============================================================================
# 3. CHATBOT INTEGRATION
# ============================================================================

from llm.providers.base import LLMProvider
from llm.models import ChatMessage


def get_chatbot_context(
    db: Session,
    query: str,
    lesson_id: int = None,
    top_k: int = 3
) -> str:
    """Get RAG context for chatbot responses.
    
    Args:
        db: Database session
        query: User question
        lesson_id: Optional lesson context
        top_k: Number of documents to retrieve
        
    Returns:
        Context string for LLM prompt
    """
    rag = get_rag_service()
    
    # Search RAG system
    if lesson_id:
        # Search within lesson documents
        results = search_lesson_content(db, lesson_id, query, top_k)
    else:
        # Global search
        results = rag.search(query, top_k)
    
    if results['status'] != 'success' or not results['results']:
        return ""
    
    # Build context from top results
    context_parts = []
    for result in results['results']:
        relevance = result.get('relevance', 0)
        content = result['content'][:300]  # Truncate for brevity
        context_parts.append(f"[Page {result.get('page_number', '?')}, Relevance: {relevance:.1%}]\n{content}")
    
    context = "\n\n".join(context_parts)
    
    return context


def create_rag_prompt(
    user_question: str,
    rag_context: str
) -> list[ChatMessage]:
    """Create a prompt that includes RAG context for the chatbot.
    
    Args:
        user_question: The user's question
        rag_context: Retrieved context from RAG
        
    Returns:
        List of ChatMessage objects for LLM
    """
    messages = [
        ChatMessage(
            role="system",
            content="""You are a helpful learning assistant. Answer questions based on the provided context from course materials. 
If the context doesn't contain relevant information, say so. Always cite the source when using provided materials."""
        ),
    ]
    
    if rag_context:
        messages.append(ChatMessage(
            role="user",
            content=f"""Here is relevant context from course materials:

{rag_context}

Based on this context, please answer the following question:
{user_question}"""
        ))
    else:
        messages.append(ChatMessage(
            role="user",
            content=user_question
        ))
    
    return messages


# Example usage in chatbot endpoint:
"""
@router.post("/lessons/{lesson_id}/chat")
async def lesson_chat(
    lesson_id: int,
    message: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Get RAG context
    context = get_chatbot_context(db, message, lesson_id)
    
    # Create LLM prompt with context
    messages = create_rag_prompt(message, context)
    
    # Get LLM response
    llm = get_llm_provider()
    response = llm.generate(messages)
    
    return {
        'answer': response,
        'context_used': bool(context),
        'sources': get_lesson_rag_documents(db, lesson_id)
    }
"""


# ============================================================================
# 4. ANALYTICS & FEEDBACK
# ============================================================================

def track_rag_usage(
    db: Session,
    document_id: int,
    integration_type: str = None
) -> None:
    """Track RAG document usage for analytics.
    
    Args:
        db: Database session
        document_id: RAG document ID
        integration_type: Type of integration being used
    """
    doc = db.query(RAGDocument).get(document_id)
    if doc:
        integrations = db.query(RAGIntegration)\
            .filter(RAGIntegration.document_id == document_id)\
            .all()
        
        for integration in integrations:
            integration.usage_count += 1
        
        db.commit()


def get_rag_analytics(
    db: Session,
    document_id: int = None,
    lesson_id: int = None
) -> dict:
    """Get analytics about RAG usage.
    
    Args:
        db: Database session
        document_id: Optional document filter
        lesson_id: Optional lesson filter
        
    Returns:
        Analytics summary
    """
    # Build queries
    doc_query = db.query(RAGDocument)
    if document_id:
        doc_query = doc_query.filter(RAGDocument.id == document_id)
    
    documents = doc_query.filter(RAGDocument.is_active == 1).all()
    
    # Get search stats
    search_query = db.query(RAGSearchSession)
    if lesson_id:
        search_query = search_query.filter(RAGSearchSession.lesson_id == lesson_id)
    
    search_sessions = search_query.all()
    
    # Calculate metrics
    total_searches = len(search_sessions)
    avg_results = sum(s.results_count for s in search_sessions) / total_searches if total_searches > 0 else 0
    avg_duration = sum(s.search_duration_ms for s in search_sessions if s.search_duration_ms) / total_searches if total_searches > 0 else 0
    
    return {
        'documents': {
            'total': len(documents),
            'total_chunks': sum(d.chunks_count for d in documents),
            'total_tokens': sum(d.total_tokens for d in documents),
        },
        'searches': {
            'total': total_searches,
            'avg_results_per_search': avg_results,
            'avg_duration_ms': avg_duration,
        },
        'engagement': {
            'documents_with_usage': sum(1 for i in db.query(RAGIntegration).filter(RAGIntegration.usage_count > 0).all()),
            'total_usage_count': sum(i.usage_count for i in db.query(RAGIntegration).all()),
        }
    }


# ============================================================================
# 5. WORKFLOW EXAMPLE: Complete Integration Flow
# ============================================================================

async def create_lesson_with_rag_documents(
    db: Session,
    lesson_data: dict,
    pdf_files: list,
    user_id: int
):
    """
    Complete workflow: Create lesson and attach RAG documents.
    
    Args:
        db: Database session
        lesson_data: Lesson information
        pdf_files: List of PDF file uploads
        user_id: Creator user ID
        
    Returns:
        Created lesson with attached documents
    """
    # 1. Create the lesson
    from app.models.lesson import Lesson
    
    lesson = Lesson(
        title=lesson_data['title'],
        description=lesson_data['description'],
        course_id=lesson_data['course_id'],
        created_by=user_id,
    )
    db.add(lesson)
    db.flush()  # Get lesson ID
    
    # 2. Upload RAG documents
    rag = get_rag_service()
    
    for pdf_file in pdf_files:
        # Save PDF to temporary location
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.pdf') as tmp:
            content = await pdf_file.read()
            tmp.write(content)
            tmp.flush()
            
            # Ingest to RAG
            result = rag.ingest_pdf(tmp.name)
            
            if result['status'] == 'success':
                # Store in database
                rag_doc = RAGDocument(
                    doc_id=result['document_id'],
                    title=pdf_file.filename,
                    course_id=lesson_data['course_id'],
                )
                db.add(rag_doc)
                db.flush()
                
                # Attach to lesson
                attach_rag_to_lesson(
                    db,
                    lesson.id,
                    rag_doc.id,
                    integration_type="supplementary"
                )
    
    db.commit()
    
    return lesson


"""
This module provides integration patterns for using the RAG system with
various LMS components. Each function is documented and can be copy-pasted
directly into your route handlers or service functions.

Key patterns:
1. Attach documents to lessons/assignments
2. Search within document scope
3. Get context for chatbot
4. Track usage and analytics
5. Complete workflow examples

For more examples, see:
- app/api/v1/lessons.py - Lesson routes
- app/api/v1/assignments.py - Assignment routes
- app/api/v1/chatbot.py - Chatbot routes
"""
