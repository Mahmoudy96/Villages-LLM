import requests
from typing import Dict, Any

class BackendAPIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def health_check(self) -> bool:
        """Check if backend is healthy"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def initialize_model(self, model_config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize the model"""
        try:
            response = requests.post(
                f"{self.base_url}/initialize",
                json=model_config,
                timeout=30
            )
            return {
                "success": response.status_code == 200,
                "message": response.text if response.status_code != 200 else "Model initialized successfully"
            }
        except Exception as e:
            return {"success": False, "message": f"Connection error: {str(e)}"}
    
    def query(self, question: str, session_id: str = "default_session") -> str:
        """Send query to backend"""
        try:
            response = requests.post(
                f"{self.base_url}/query",
                json={"question": question, "session_id": session_id},
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()["response"]
            else:
                return f"❌ **Error:** {response.json().get('detail', 'Unknown error')}"
        except requests.exceptions.Timeout:
            return "❌ **Error:** Request timed out. Please try again."
        except requests.exceptions.ConnectionError:
            return "❌ **Error:** Cannot connect to backend server."
        except Exception as e:
            return f"❌ **Connection error:**"# {str(e)}"