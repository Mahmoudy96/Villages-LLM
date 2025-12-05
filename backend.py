from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime

# Assuming your RAGLLM class is in a module called rag_llm.py
from RAGLLM import RAGSystem

app = FastAPI(title="RAG LLM API")

# CORS configuration (needed for frontend-backend communication)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class InitializeRequest(BaseModel):
    model_name: str = "gpt-4"
    embedding_model: str = "laBSE"
    #db_config: Optional[dict] = None

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
        rag_llm.initialize_components(use_openAI=True)
        print("RAG system initialized successfully")
    except Exception as e:
        print(f"Initialization failed: {str(e)}")

@app.post("/initialize")
async def initialize(request: InitializeRequest):
    """Re-initialize with different parameters"""
    try:
        #global rag_system
        rag_llm = RAGSystem(embedding_model=request.embedding_model)
        rag_llm.initialize_components(
            use_openAI=True
        )
        rag_llm.chatbot.set_model(request.model_name)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def query(request: QueryRequest):
    """Handle a query with chat history"""
    try:
        # Get or create chat history for this session
        if request.session_id not in chat_history:
            chat_history[request.session_id] = []
        
        # Generate history summary
        history_summary = generate_history_summary(chat_history[request.session_id])
        
        # Get response from RAG system
        response = rag_llm.process_query(request.question, summary=history_summary,stream=True)
        
        # Store the interaction in history
        chat_history[request.session_id].append(
            ChatHistoryItem(
                question=request.question,
                answer=response,
                timestamp=datetime.now().isoformat()
            )
        )
        
        # Ensure we don't keep too much history
        if len(chat_history[request.session_id]) > 10:  # Keep last 10 messages
            chat_history[request.session_id] = chat_history[request.session_id][-10:]
        
        return {"response": response}
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