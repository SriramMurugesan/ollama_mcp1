import json
import os
import requests
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel

from mcp.client import MCPClient  # You must create this module as discussed earlier

CONFIG_PATH = Path(__file__).parent / "server_config.json"
app = FastAPI()

with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

mcp_servers = config.get("mcpServers", {})
ollama_config = mcp_servers.get("ollama", {})
# Ensure the API URL has the correct format
ollama_url = ollama_config.get("api_url", "http://localhost:11434")
OLLAMA_API_URL = ollama_url.rstrip('/')
OLLAMA_MODEL = ollama_config.get("model")
OLLAMA_API_KEY = ollama_config.get("api_key")

# --- MCP Tools Setup ---
tools_config = mcp_servers.get("tools", {})
mcp_client = MCPClient()

for tool_name, tool_details in tools_config.items():
    mcp_client.register_tool(tool_name, tool_details)

def call_ollama_cloud(messages: list):
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False
    }
    
    # Add authorization header only if API key is provided
    if OLLAMA_API_KEY and OLLAMA_API_KEY.strip():
        headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"
    
    print(f"Calling Ollama API at: {OLLAMA_API_URL}")
    print(f"Payload: {payload}")
    
    try:
        res = requests.post(OLLAMA_API_URL, headers=headers, json=payload, timeout=30)
        res.raise_for_status()
        
        response_data = res.json()
        print(f"Response: {response_data}")
        
        # Handle different response formats
        if "choices" in response_data and response_data["choices"]:
            return response_data["choices"][0]["message"]["content"]
        elif "message" in response_data:
            return response_data["message"]["content"]
        elif "response" in response_data:
            return response_data["response"]
        else:
            return str(response_data)
    
    except requests.exceptions.RequestException as e:
        print(f"Error calling Ollama API: {e}")
        return f"Error: Failed to connect to Ollama API - {str(e)}"
    except Exception as e:
        print(f"Error processing response: {e}")
        return f"Error: {str(e)}"

class ChatRequest(BaseModel):
    user_input: str

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Ollama MCP server is running"}

@app.post("/chat")
async def chat_with_bot(request: ChatRequest):
    user_input = request.user_input
    
    response = call_ollama_cloud([
        {"role": "user", "content": user_input}
    ])

    tool_request = mcp_client.parse_for_tool(response)
    if tool_request:
        tool_result = mcp_client.call_tool(tool_request)
        response = call_ollama_cloud([
            {"role": "system", "content": f"Tool result: {tool_result}"},
            {"role": "user", "content": user_input}
        ])

    return {"response": response}
