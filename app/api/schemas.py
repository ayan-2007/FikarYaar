"""
Pydantic request/response models.

Keeping them in one place makes the API contract easy to read at a glance.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    history: List[Message] = Field(default_factory=list)


class SourceInfo(BaseModel):
    name: str
    type: str
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceInfo] = Field(default_factory=list)
    used_notes: bool = False


class HealthResponse(BaseModel):
    status: str
    version: str
    chunks: int
    sources: int
    llm_configured: bool
    embeddings_loaded: bool


class IngestResponse(BaseModel):
    status: str
    files_processed: int
    chunks_added: int


class UploadResponse(BaseModel):
    status: str
    files: List[str]
    chunks_added: int


class QuizStartRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200)


class QuizAnswerRequest(BaseModel):
    session_id: str
    question_num: int
    answer: str = Field(..., min_length=1, max_length=5000)
