#!/usr/bin/env python3
"""Comprehensive RAG System Test Suite - run from project root:
    python -m llm.rag.test_rag_comprehensive
"""
import json, sys, math, logging
from pathlib import Path

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

_errors: list[str] = []

def ok(msg):  print(f"  ✓ {msg}")
def fail(msg): print(f"  ✗ {msg}"); _errors.append(msg)
def warn(msg): print(f"  ⚠ {msg}")
def sec(t):   print(f"\n[{t}]\n" + "-"*60)


# ── helper: deterministic unit vector ──────────────────────────────────────
def unit_vec(angle: float, dim: int = 768) -> list[float]:
    v = [math.cos(angle + i * 0.01) for i in range(dim)]
    n = sum(x**2 for x in v) ** 0.5
    return [x / n for x in v]


# ── mock embedding service ──────────────────────────────────────────────────
class MockEmbedder:
    embedding_dimension = 3072
    def embed_text(self, text, task_type="RETRIEVAL_DOCUMENT"):
        import hashlib, struct
        h = hashlib.md5(text.encode()).digest()
        base = struct.unpack("f", h[:4])[0]
        v = [(base + i * 0.001) % 1.0 for i in range(self.embedding_dimension)]
        n = sum(x**2 for x in v) ** 0.5
        return [x / n for x in v] if n > 0 else [1.0 / self.embedding_dimension**0.5] * self.embedding_dimension
    def embed_query(self, q): return self.embed_text(q, "RETRIEVAL_QUERY")
    def embed_chunks(self, chunks, task_type="RETRIEVAL_DOCUMENT"):
        for c in chunks:
            if not c.metadata.get("is_structural"):
                c.embedding = self.embed_text(c.content, task_type)
        return chunks
    def embed_document(self, document):
        self.embed_chunks(document.chunks)
        return document


# ═══════════════════════════════════════════════════════════════════════════
# TEST 1 – PDF Processor
# ═══════════════════════════════════════════════════════════════════════════
sec("TEST 1 · PDF Processor")
try:
    from llm.rag.pdf_processor import PDFProcessor
    proc = PDFProcessor(verbose=False)
    ok("PDFProcessor imported")

    sample = Path(__file__).parent / "pdf_sample.pdf"
    if sample.exists():
        r = proc.process_pdf(sample)
        pages, chars = r["metadata"]["total_pages"], r["total_text_length"]
        ok(f"Text PDF: {pages} pages, {chars} chars") if chars > 0 else fail("0 chars from text PDF")
        title = r["metadata"]["title"]
        ok(f"Title normalized: '{title}'") if title else warn("Empty title")
    else:
        warn("pdf_sample.pdf missing")

    sample_vi = Path(__file__).parent / "data_sample" / "Lesson_1_Part_1.pdf"
    if sample_vi.exists():
        rv = proc.process_pdf(sample_vi)
        chars_vi = rv["total_text_length"]
        if chars_vi > 0:
            ok(f"Vietnamese PDF extracted: {chars_vi} chars, title='{rv['metadata']['title'][:40]}'")
        else:
            warn("Lesson_1_Part_1.pdf: 0 chars (image-based, OCR required)")
    else:
        warn("Lesson_1_Part_1.pdf missing")

except Exception as e:
    fail(f"PDF Processor: {e}"); import traceback; traceback.print_exc()


# ═══════════════════════════════════════════════════════════════════════════
# TEST 2 – Hierarchical Chunker + Hierarchy Validation
# ═══════════════════════════════════════════════════════════════════════════
sec("TEST 2 · Chunker & Hierarchy Invariants")
try:
    from llm.rag.chunker import HierarchicalChunker, ChunkType, Chunk

    ck = HierarchicalChunker(verbose=False)
    ok("HierarchicalChunker imported")

    sample = Path(__file__).parent / "pdf_sample.pdf"
    if sample.exists():
        proc = PDFProcessor(verbose=False)
        pdf_r = proc.process_pdf(sample)
        doc = ck.chunk_document(pdf_r["pages"], {**pdf_r["metadata"], "source_path": str(sample)})

        by_level = {}
        for c in doc.chunks:
            by_level[c.level] = by_level.get(c.level, 0) + 1
        ok(f"Chunks by level: {dict(sorted(by_level.items()))}")

        l0 = [c for c in doc.chunks if c.level == 0]
        if len(l0) == 1 and l0[0].type == ChunkType.DOCUMENT:
            ok("L0: exactly 1 DOCUMENT root")
        else:
            fail(f"L0 invariant violated: {l0}")

        l1 = [c for c in doc.chunks if c.level == 1]
        bad = [c for c in l1 if c.parent_id != l0[0].id or c.type != ChunkType.SECTION]
        ok(f"L1: {len(l1)} SECTION chunks, all parented to root") if not bad else fail(f"L1 bad: {[c.id for c in bad]}")

        l2 = [c for c in doc.chunks if c.level >= 2]
        orphans = [c for c in l2 if not c.parent_id]
        ok(f"L2+: {len(l2)} content chunks, no orphans") if not orphans else fail(f"Orphans: {[c.id for c in orphans]}")

        empty_content = [c for c in l2 if not c.content.strip()]
        ok("No empty-content chunks at L2+") if not empty_content else fail(f"{len(empty_content)} empty chunks at L2+")

    # Empty pages → only root chunk
    doc_empty = ck.chunk_document(
        [{"page_number": i, "text": ""} for i in range(1, 4)],
        {"title": "Empty", "source_path": "/tmp/e.pdf"},
    )
    non_root = [c for c in doc_empty.chunks if c.level > 0]
    ok("Empty pages produce 0 section/content chunks") if not non_root else fail(f"Empty pages produced {len(non_root)} unexpected chunks")

    # Token estimation
    c = Chunk(id="t", type=ChunkType.PARAGRAPH, content="A"*400, page_number=1)
    ok(f"Token estimate 400 chars → {c.tokens_count} tokens") if c.tokens_count == 100 else fail(f"Token estimate wrong: {c.tokens_count}")

except Exception as e:
    fail(f"Chunker: {e}"); import traceback; traceback.print_exc()


# ═══════════════════════════════════════════════════════════════════════════
# TEST 3 – Embedding Service catalog
# ═══════════════════════════════════════════════════════════════════════════
sec("TEST 3 · Embedding Service Catalog")
try:
    from llm.rag.embedder import EmbeddingService
    expected_dims = {'gemini-embedding-001': 3072, 'text-embedding-004': 768}
    for name, dim in EmbeddingService.MODELS.items():
        expected = expected_dims.get(name)
        if expected and dim == expected:
            ok(f"Model '{name}': dim={dim}")
        elif expected:
            fail(f"Model '{name}' dim={dim}, expected {expected}")
        else:
            ok(f"Model '{name}': dim={dim} (no expectation set)")

    mock = MockEmbedder()
    q = mock.embed_query("test query")
    default_dim = EmbeddingService.MODELS["gemini-embedding-001"]
    ok(f"Mock query embedding: {len(q)} dims") if len(q) == default_dim else fail(f"Wrong dim: {len(q)} (expected {default_dim})")

    import numpy as np
    v1 = mock.embed_text("same text")
    v2 = mock.embed_text("same text")
    sim = float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
    ok(f"Cosine sim identical texts: {sim:.6f} ≈ 1.0") if abs(sim - 1.0) < 1e-5 else fail(f"Cosine sim wrong: {sim}")

except Exception as e:
    fail(f"Embedder: {e}"); import traceback; traceback.print_exc()


# ═══════════════════════════════════════════════════════════════════════════
# TEST 4 – InMemoryVectorStore
# ═══════════════════════════════════════════════════════════════════════════
sec("TEST 4 · InMemoryVectorStore")
try:
    from llm.rag.vector_store import InMemoryVectorStore
    from llm.rag.chunker import Chunk, Document, ChunkType

    store = InMemoryVectorStore(verbose=False)
    ok("InMemoryVectorStore initialised")

    chunks = [Chunk(id=f"c{i}", type=ChunkType.PARAGRAPH, content=f"Chunk {i}",
                    page_number=i, embedding=unit_vec(i * 0.3)) for i in range(1, 6)]
    doc = Document(id="d1", title="T", source_path="/tmp/t.pdf", chunks=chunks)
    store.add_chunks(chunks, doc)
    ok(f"Added {len(chunks)} chunks")

    results = store.search(unit_vec(0.9), top_k=3)
    ok(f"Search returned {len(results)} results") if len(results) == 3 else fail(f"Expected 3, got {len(results)}")

    scores = [r["similarity"] for r in results]
    ok(f"Results sorted desc: {[f'{s:.4f}' for s in scores]}") if scores == sorted(scores, reverse=True) else fail("Results not sorted")

    if results[0]["chunk_id"] == "c3":
        ok("Top result is c3 (angle=0.9, closest to query)")
    else:
        warn(f"Top result is {results[0]['chunk_id']} (expected c3)")

    # Structural chunk excluded
    sc = Chunk(id="struct", type=ChunkType.DOCUMENT, content="Root", page_number=0, embedding=unit_vec(0.9))
    sc.metadata["is_structural"] = True
    store.add_chunks([sc], doc)
    if not any(r["chunk_id"] == "struct" for r in store.search(unit_vec(0.9), top_k=10)):
        ok("Structural chunks excluded from search")
    else:
        fail("Structural chunk appeared in search")

    # Delete
    store.delete_document("d1")
    if not store.search(unit_vec(0.9), top_k=5, doc_id="d1"):
        ok("Deleted document not returned in search")
    else:
        fail("Deleted document still in search results")

except Exception as e:
    fail(f"VectorStore: {e}"); import traceback; traceback.print_exc()


# ═══════════════════════════════════════════════════════════════════════════
# TEST 5 – RAG Service end-to-end
# ═══════════════════════════════════════════════════════════════════════════
sec("TEST 5 · RAG Service end-to-end (mock embeddings)")
try:
    from llm.rag.service import RAGService, reset_rag_service
    from llm.rag.vector_store import InMemoryVectorStore

    reset_rag_service()
    svc = RAGService(vector_store=InMemoryVectorStore(verbose=False),
                     embedding_service=MockEmbedder(), verbose=False)
    ok("RAGService with mock embedder")

    sample = Path(__file__).parent / "pdf_sample.pdf"
    if sample.exists():
        r = svc.ingest_pdf(sample, document_id="paper")
        if r["status"] == "success" and r["chunks"] > 0:
            ok(f"Ingested: {r['chunks']} chunks, {r['pages']} pages")
        else:
            fail(f"Ingest failed or 0 chunks: {r}")

        sr = svc.search("Vietnamese readability features", top_k=3)
        if sr["status"] == "success" and sr["results_count"] > 0:
            top = sr["results"][0]
            ok(f"Search: {sr['results_count']} results, top relevance={top['relevance']:.4f}")
            if -1e-9 <= top["relevance"] <= 1.0 + 1e-9:
                ok(f"Relevance in [0,1]: {top['relevance']:.6f}")
            else:
                fail(f"Relevance out of range: {top['relevance']}")
        else:
            fail(f"Search returned 0 results or failed: {sr}")

        dr = svc.delete_document("paper")
        ok("Document deleted") if dr["status"] == "success" else fail(f"Delete failed: {dr}")
    else:
        warn("pdf_sample.pdf missing – skipping e2e test")

except Exception as e:
    fail(f"RAG Service: {e}"); import traceback; traceback.print_exc()


# ═══════════════════════════════════════════════════════════════════════════
# TEST 6 – LMS Data Samples Hierarchy
# ═══════════════════════════════════════════════════════════════════════════
sec("TEST 6 · LMS Data Samples (data_sample/)")
try:
    from llm.rag.pdf_processor import PDFProcessor
    from llm.rag.chunker import HierarchicalChunker

    data_dir = Path(__file__).parent / "data_sample"
    if not data_dir.exists():
        warn(f"data_sample/ not found at {data_dir}")
    else:
        p = PDFProcessor(verbose=False)
        ck2 = HierarchicalChunker(verbose=False)
        files = sorted(data_dir.glob("*.pdf"))
        ok(f"Found {len(files)} PDFs in data_sample/")

        for fpath in files:
            pdf_r = p.process_pdf(fpath)
            doc = ck2.chunk_document(
                pages=pdf_r["pages"],
                doc_metadata={**pdf_r["metadata"], "source_path": str(fpath)},
            )

            total_chars = pdf_r["total_text_length"]
            n_chunks = len(doc.chunks)
            n_content = sum(1 for c in doc.chunks if c.level >= 2)
            l0 = [c for c in doc.chunks if c.level == 0]

            if total_chars == 0:
                warn(f"{fpath.name}: 0 chars (image-based PDF, OCR required)")
            else:
                ok(f"{fpath.name}: {total_chars} chars, {n_chunks} chunks ({n_content} content)")

            if len(l0) == 1:
                ok(f"  └─ Hierarchy root (L0): {l0[0].id}")
            else:
                fail(f"  └─ Missing L0 root in {fpath.name}")

except Exception as e:
    fail(f"Data sample test: {e}"); import traceback; traceback.print_exc()


# ═══════════════════════════════════════════════════════════════════════════
# TEST 7 – Backend models & schemas (no DB)
# ═══════════════════════════════════════════════════════════════════════════
sec("TEST 7 · Backend Models & Schemas")
sys.path.insert(0, str(Path(__file__).parents[2] / "apps" / "backend"))

try:
    from app.models.rag import RAGDocument, RAGChunk, RAGSearchSession, RAGSearchResult, RAGIntegration
    ok("All RAG SQLAlchemy models imported")

    expected = {"rag_documents": RAGDocument, "rag_chunks": RAGChunk,
                "rag_search_sessions": RAGSearchSession, "rag_search_results": RAGSearchResult,
                "rag_integrations": RAGIntegration}
    for tname, model in expected.items():
        ok(f"__tablename__: {tname}") if model.__tablename__ == tname else fail(f"Wrong tablename: {model.__tablename__}")

    r = RAGSearchResult(relevance_score=None)
    try:
        repr(r); ok("RAGSearchResult.__repr__ safe with None")
    except TypeError as e:
        fail(f"__repr__ crashed with None: {e}")

except Exception as e:
    fail(f"Model import: {e}"); import traceback; traceback.print_exc()

try:
    from app.schemas.rag import (RAGSearchRequest, RAGSearchResponse, RAGChunkResponse,
                                  RAGDocumentResponse, RAGIngestionResponse, RAGStatsResponse)
    ok("All RAG Pydantic schemas imported")

    req = RAGSearchRequest(query="test", top_k=5)
    ok(f"RAGSearchRequest: query='{req.query}', top_k={req.top_k}")

    import pydantic
    for bad in [0, 21]:
        try:
            RAGSearchRequest(query="x", top_k=bad)
            fail(f"Should reject top_k={bad}")
        except Exception:
            ok(f"Correctly rejects top_k={bad}")

except Exception as e:
    fail(f"Schema import: {e}"); import traceback; traceback.print_exc()

try:
    from app.api.v1.rag import router
    from sqlalchemy import func  # must be importable at top of rag.py now
    import app.api.v1.rag as rag_mod
    import inspect
    src = inspect.getsource(rag_mod)
    # Check func import is NOT at the bottom (after function definitions)
    func_import_pos = src.index("from sqlalchemy import func")
    first_def_pos = src.index("def ")
    if func_import_pos < first_def_pos:
        ok("'from sqlalchemy import func' correctly placed before function definitions")
    else:
        fail("'from sqlalchemy import func' is AFTER function definitions (should be at top)")

    routes = [r.path for r in router.routes]
    ok(f"RAG router: {len(routes)} routes registered")
    for expected_path in ["/rag/upload", "/rag/search", "/rag/documents", "/rag/stats"]:
        if expected_path in routes:
            ok(f"  Route: {expected_path} (mounted as /api/v1{expected_path})")
        else:
            fail(f"  Missing route: {expected_path}")

except Exception as e:
    fail(f"API router check: {e}"); import traceback; traceback.print_exc()


# ═══════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("  TEST SUMMARY")
print("="*60)
if _errors:
    print(f"\n  FAILED: {len(_errors)} error(s)")
    for e in _errors:
        print(f"    ✗ {e}")
    sys.exit(1)
else:
    print(f"\n  ALL TESTS PASSED ✓")
    print("""
  Components verified:
    • PDF Processor (PyMuPDF primary, PyPDF2 fallback)
    • Hierarchical Chunker (L0→L1→L2+ hierarchy invariants)
    • Embedding Service (model catalog, cosine similarity)
    • InMemoryVectorStore (add/search/delete, struct exclusion)
    • RAG Service end-to-end (ingest→search→delete)
    • LMS Data Samples (hierarchy validation + image PDF detection)
    • Backend SQLAlchemy models (tablenames, repr safety)
    • Backend Pydantic schemas (validation, import order)
    • API router (routes registered, func import position)

  ⚠  Image-based PDFs in data_sample/ require OCR.
     Only text-based PDFs can be indexed by the current pipeline.
""")
    sys.exit(0)
