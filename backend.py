from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os

# Assuming your RAGLLM class is in a module called rag_llm.py
from RAGLLM import RAGLLM

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
    model_name: str = "gpt2"
    db_config: Optional[dict] = None

class QueryRequest(BaseModel):
    question: str
    rag_enabled: bool = True

# Global RAG LLM instance
rag_llm = RAGLLM()

@app.on_event("startup")
async def startup_event():
    """Initialize the RAG system when the app starts"""
    try:
        rag_llm.initialize_db()
        rag_llm.initialize_embedding_model()
        rag_llm.initialize_llm(model_name="gpt2")  # Default model
        print("RAG LLM initialized successfully")
    except Exception as e:
        print(f"Initialization failed: {str(e)}")

@app.post("/initialize")
async def initialize(request: InitializeRequest):
    """Re-initialize with different parameters"""
    try:
        if request.db_config:
            rag_llm.initialize_db(**request.db_config)
        
        rag_llm.initialize_llm(model_name=request.model_name)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def query(request: QueryRequest):
    """Handle a query with optional RAG"""
    try:
        # if request.rag_enabled:
        rag_llm.set_natural_language_query(request.question)
        response = rag_llm.perform_rag()
        # else:
        #     # Direct LLM query if RAG is disabled
        #     response = rag_llm.llm.generate(request.question)
        #     print(response)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)