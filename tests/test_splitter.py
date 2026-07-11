"""Tests for the markdown splitter."""
from langchain_core.documents import Document

from app.rag.splitter import split_documents
from app.rag.text_utils import count_tokens


def test_split_into_chunks():
    doc = Document(page_content="Sentence one. " * 200, metadata={"source": "t.txt"})
    chunks = split_documents([doc])
    assert len(chunks) >= 2
    for c in chunks:
        assert count_tokens(c.page_content) <= 250


def test_short_doc_single_chunk():
    doc = Document(page_content="Short note about classes and objects.", metadata={"source": "t.txt"})
    chunks = split_documents([doc])
    assert len(chunks) == 1
