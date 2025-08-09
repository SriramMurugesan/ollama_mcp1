import os
import json
import subprocess
import requests
from fastapi import FastAPI, Body
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Load servers.json
with open("server_config.json") as f:
    config = json.load(f)

ollama_cfg = config["mcpServers"]["ollama"]
OLLAMA_URL = ollama_cfg["api_url"]
OLLAMA_MODEL = ollama_cfg["model"]
OLLAMA_KEY = os.getenv("OLLAMA_API_KEY")

tool_servers = config["mcpServers"]["tools"]

app = FastAPI()

SYSTEM_PROMPT = """
You are a chatbot with access to external tools.
You can use the following tools by outputting JSON exactly in this format:
{
  "tool_name": "tool-id",
  "parameters": { "param1": "value1", "param2": "value2" }
}
If no tool is needed, reply with a normal message.
"""

def call_ollama(messages):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OLLAMA_KEY}"
    }
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False
    }
    r = requests.post(OLLAMA_URL, headers=headers, json=payload)
    r.raise_for_status()
    data = r.json()
    return data["message"]["content"]

def start_mcp_tool(tool_name):
    cfg = tool_servers[tool_name]
    # Expand ${VAR_NAME} from env in servers.json
    env_vars = {
        **os.environ,
        **{k: os.path.expandvars(v) for k, v in cfg.get("env", {}).items()}
    }
    process = subprocess.Popen(
        [cfg["command"]] + cfg["args"],
        env=env_vars,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return process

@app.post("/chat")
def chat(prompt: str = Body(..., embed=True)):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]

    while True:
        reply = call_ollama(messages).strip()

        try:
            tool_call = json.loads(reply)
            if "tool_name" in tool_call and tool_call["tool_name"] in tool_servers:
                tool_name = tool_call["tool_name"]
                params = tool_call.get("parameters", {})

                proc = start_mcp_tool(tool_name)
                proc.stdin.write(json.dumps(params) + "\n")
                proc.stdin.flush()
                tool_output = proc.stdout.readline().strip()
                proc.kill()

                messages.append({
                    "role": "assistant",
                    "content": f"Tool {tool_name} output: {tool_output}"
                })
                continue  # Loop back to model

        except json.JSONDecodeError:
            return {"final_reply": reply}
