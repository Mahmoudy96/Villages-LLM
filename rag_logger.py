"""
Structured logging for RAG pipeline - MongoDB, ChromaDB, and LLM context.
Logs to stdout (JSON lines) for easy monitoring and log aggregation.
"""
import os
import json
import logging
from datetime import datetime
from typing import Any, Optional

# Env: LOG_LEVEL (DEBUG, INFO, WARNING, ERROR), RAG_LOG_FILE (optional path)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("RAG_LOG_FILE", "")


def _truncate(value: Any, max_len: int = 2000) -> Any:
    """Truncate long strings for readability; recurse into dicts/lists."""
    if isinstance(value, str):
        if len(value) > max_len:
            return value[:max_len] + f"... [truncated, total {len(value)} chars]"
        return value
    if isinstance(value, list):
        return [_truncate(v, max_len) for v in value[:20]] + (["..."] if len(value) > 20 else [])
    if isinstance(value, dict):
        return {k: _truncate(v, max_len) for k, v in list(value.items())[:30]}
    return value


def _log_event(event_type: str, data: dict, level: str = "INFO"):
    """Emit a structured JSON log line."""
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event": event_type,
        "level": level,
        **data,
    }
    line = json.dumps(entry, ensure_ascii=False, default=str)
    # Use standard logger so it goes to configured handlers
    log = logging.getLogger("rag")
    if level == "DEBUG":
        log.debug(line)
    elif level == "WARNING":
        log.warning(line)
    elif level == "ERROR":
        log.error(line)
    else:
        log.info(line)


def setup_rag_logger():
    """Configure the RAG logger. Call once at startup."""
    log = logging.getLogger("rag")
    log.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    log.propagate = False
    log.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(handler)
    if LOG_FILE:
        fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(message)s"))
        log.addHandler(fh)


def log_query_start(session_id: str, query: str):
    """Log when a query is received."""
    _log_event("query_start", {"session_id": session_id, "query": query})


def log_mongo_query(translated_query: str, results: list, query: str):
    """Log MongoDB translated query and results."""
    _log_event(
        "mongo_result",
        {
            "query": query,
            "translated_mongo_query": translated_query,
            "result_count": len(results),
            "results": _truncate(results, 1500),
        },
    )


def log_chroma_result(query: str, documents: list, metadatas: Optional[list] = None, distances: Optional[list] = None):
    """Log ChromaDB query results."""
    data = {
        "query": query,
        "document_count": len(documents) if documents else 0,
        "documents": _truncate(documents, 1500),
    }
    if metadatas:
        data["metadatas"] = _truncate(metadatas, 500)
    if distances:
        data["distances"] = distances
    _log_event("chroma_result", data)


def log_llm_context(query: str, mongo_data: Any, chroma_data: Any, history_summary: Optional[str] = None):
    """Log the full context being sent to the LLM."""
    _log_event(
        "llm_context",
        {
            "query": query,
            "history_summary": _truncate(history_summary, 500) if history_summary else None,
            "mongo_context": _truncate(mongo_data, 2000),
            "chroma_context": _truncate(chroma_data, 2000),
        },
    )


def log_response_end(session_id: str, query: str, response_preview: str, success: bool = True):
    """Log when response is complete."""
    _log_event(
        "response_end",
        {
            "session_id": session_id,
            "query": query,
            "response_preview": _truncate(response_preview, 300),
            "success": success,
        },
    )


def log_error(event_type: str, message: str, extra: Optional[dict] = None):
    """Log an error event."""
    data = {"message": message}
    if extra:
        data.update(extra)
    _log_event(event_type, data, level="ERROR")
