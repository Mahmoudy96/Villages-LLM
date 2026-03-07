from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime
import asyncio
import uuid
import os
from RAGLLM import RAGSystem
from env import CORS_ORIGINS

try:
    from rag_logger import setup_rag_logger, log_query_start, log_response_end, log_error
    setup_rag_logger()
    _LOGGING_ENABLED = True
except ImportError:
    _LOGGING_ENABLED = False

app = FastAPI(title="RAG LLM API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class InitializeRequest(BaseModel):
    model_name: str = "gpt-4o-mini"  # Fixed: Changed to valid model name (was "gpt-4")
    embedding_model: str = "laBSE"

class QueryRequest(BaseModel):
    question: str
    session_id: str  # To maintain chat history per session

class ChatHistoryItem(BaseModel):
    question: str
    answer: str
    timestamp: str

# Global RAG LLM instance
rag_llm = RAGSystem()
chat_history: Dict[str, List[ChatHistoryItem]] = {}  # {session_id: [messages]}

def generate_history_summary(history: List[ChatHistoryItem]) -> str:
    """Generate a concise summary of the chat history"""
    if not history:
        return "No previous conversation history."
    
    # Take last 5 messages (adjust as needed)
    recent_history = history[-5:]
    
    summary = "Previous conversation summary:\n"
    for i, item in enumerate(recent_history, 1):
        summary += f"{i}. Q: {item.question}\n   A: {item.answer[:100]}...\n"
    return summary

# Initialize the RAG system on startup
@app.on_event("startup")
async def startup_event():
    """Initialize the RAG system when the app starts"""
    try:
        print("[STARTUP] Initializing RAG system...")
        rag_llm.initialize_components(use_openAI=True)
        print("[STARTUP] RAG system initialized successfully")
    except Exception as e:
        print(f"[STARTUP ERROR] Initialization failed: {str(e)}")
        import traceback
        traceback.print_exc()

@app.post("/session")
async def create_session():
    """Create a new chat session with a unique session ID"""
    session_id = str(uuid.uuid4())
    chat_history[session_id] = []
    return {"session_id": session_id}

@app.post("/initialize")
async def initialize(request: InitializeRequest):
    """Re-initialize with different parameters"""
    try:
        global rag_llm
        rag_llm = RAGSystem(embedding_model=request.embedding_model)
        rag_llm.initialize_components(use_openAI=True)
        rag_llm.chatbot.set_model(request.model_name)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def query(request: QueryRequest):
    """Handle a query without streaming (returns full response)"""
    if _LOGGING_ENABLED:
        log_query_start(request.session_id, request.question)
    try:
        # Get or create chat history for this session
        if request.session_id not in chat_history:
            chat_history[request.session_id] = []
        
        # Generate history summary
        history_summary = generate_history_summary(chat_history[request.session_id])
        
        # Get response from RAG system (non-streaming)
        response = rag_llm.process_query_sync(request.question, summary=history_summary, stream=False)
        
        # Store the interaction in history
        chat_history[request.session_id].append(
            ChatHistoryItem(
                question=request.question,
                answer=response,
                timestamp=datetime.now().isoformat()
            )
        )
        
        # Ensure we don't keep too much history
        if len(chat_history[request.session_id]) > 10:
            chat_history[request.session_id] = chat_history[request.session_id][-10:]
        
        if _LOGGING_ENABLED:
            log_response_end(request.session_id, request.question, response, success=True)
        return {"response": response}
    except Exception as e:
        if _LOGGING_ENABLED:
            log_response_end(request.session_id, request.question, str(e), success=False)
            log_error("query_error", str(e), {"session_id": request.session_id, "question": request.question})
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stream")
async def stream_query(request: QueryRequest):
    """Stream response tokens using Server-Sent Events (SSE)"""
    if _LOGGING_ENABLED:
        log_query_start(request.session_id or "unknown", request.question)
    try:
        # Get or create chat history for this session
        if request.session_id and request.session_id not in chat_history:
            chat_history[request.session_id] = []
        
        # Generate history summary
        history_summary = generate_history_summary(chat_history.get(request.session_id, []))
        
        # Queue to collect tokens
        queue: asyncio.Queue = asyncio.Queue()
        
        async def on_token(token):
            """Callback to push tokens into queue"""
            await queue.put(token)
        
        async def run_query_and_close():
            """Run the async query and signal when done"""
            try:
                full_response = await rag_llm.process_query(request.question, summary=history_summary, stream=True, on_token=on_token)
                # Store in chat history if session_id provided
                if request.session_id:
                    chat_history[request.session_id].append(
                        ChatHistoryItem(
                            question=request.question,
                            answer=full_response,
                            timestamp=datetime.now().isoformat()
                        )
                    )
                    if len(chat_history[request.session_id]) > 10:
                        chat_history[request.session_id] = chat_history[request.session_id][-10:]
                if _LOGGING_ENABLED:
                    log_response_end(request.session_id or "unknown", request.question, full_response, success=True)
            except Exception as e:
                if _LOGGING_ENABLED:
                    log_response_end(request.session_id or "unknown", request.question, str(e), success=False)
                    log_error("stream_error", str(e), {"session_id": request.session_id, "question": request.question})
                await queue.put(f"ERROR: {str(e)}")
            finally:
                await queue.put(None)  # Signal end of stream
        
        # Start background task
        asyncio.create_task(run_query_and_close())
        
        async def event_generator():
            """Generate SSE events from queued tokens"""
            while True:
                token = await queue.get()
                if token is None:
                    break
                # Send token as-is to preserve spaces and formatting
                # Replace newlines with a special marker to preserve them in SSE
                token_str = str(token).replace('\n', '\\n')
                yield f"data: {token_str}\n\n"
            yield "event: done\ndata: \n\n"
        
        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat_history/{session_id}")
async def get_chat_history(session_id: str):
    """Get full chat history for a session"""
    return chat_history.get(session_id, [])

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)