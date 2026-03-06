import requests
import streamlit as st

class BackendAPIClient:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url.rstrip("/")
    
    def health_check(self) -> bool:
        """Check if backend is reachable"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=3)
            return response.status_code == 200
        except Exception:
            return False
    
    def query(self, question: str, session_id: str):
        """Send a query to the backend (non-streaming)"""
        url = f"{self.base_url}/query"
        payload = {"question": question, "session_id": session_id}
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json().get("response", "No response received")
        except Exception:
            return "Service unavailable. Please try again later."
    
    def stream_query(self, question: str, session_id: str):
        """Stream a query from the backend (yields tokens).
        Sends JSON body to match FastAPI QueryRequest Pydantic model.
        """
        url = f"{self.base_url}/stream"
        payload = {"question": question, "session_id": session_id}
        headers = {"Content-Type": "application/json"}
        try:
            # POST JSON body and stream the response
            with requests.post(url, json=payload, headers=headers, stream=True, timeout=120) as resp:
                # Helpful debug if backend rejects the body
                if resp.status_code == 422:
                    # print backend validation error for debugging
                    print("Backend 422 response:", resp.text)
                    resp.raise_for_status()
                resp.raise_for_status()
                for raw in resp.iter_lines(decode_unicode=True):
                    if not raw:
                        continue
                    line = raw.strip()
                    # ignore SSE control events
                    if line.startswith("event:"):
                        continue
                    if line.startswith("data:"):
                        # Preserve leading/trailing spaces in tokens (critical for word boundaries)
                        content = line[6:] if len(line) > 5 and line[5] == ' ' else line[5:]
                        content = content.replace('\\n', '\n')
                        if content:
                            yield content
        except Exception:
            yield "Service unavailable. Please try again later."