from core.config import OPENAI_API_KEY, LLM_MODEL
from langchain_openai import ChatOpenAI
from openai import OpenAI
import os

def get_client():
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=OPENAI_API_KEY)

def get_supervisor_model():
    """Return default llm for supervisor."""
    return ChatOpenAI(model=LLM_MODEL,temperature=0.7)

def get_generation_model():
    """Return default llm model for a Korean Writing generation task."""
    return ChatOpenAI(model=LLM_MODEL, temperature=0.7)

def get_evaluation_model():
    """Return default llm model for a Korean Blank type of Writing evaluation task."""
    return ChatOpenAI(model=LLM_MODEL, temperature=0.1)

def get_summarization_model():
    """Return default llm model for conversation summarization task."""
    return ChatOpenAI(model=LLM_MODEL)

def get_qa_model():
    """Return default llm model for general conversation or specified tasks."""
    return ChatOpenAI(model=LLM_MODEL)
