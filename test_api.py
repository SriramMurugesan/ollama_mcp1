
import requests
import json

def test_ollama_api():
    url = "http://49.13.101.239:11434/api/chat"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "openhermes:v2.5",
        "messages": [{"role": "user", "content": "Hello, this is a test"}],
        "stream": False
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Parsed JSON: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"Exception: {e}")
        return False

def test_local_server():
    url = "http://localhost:8000/health"
    try:
        response = requests.get(url, timeout=10)
        print(f"Health check status: {response.status_code}")
        if response.status_code == 200:
            print(f"Health response: {response.json()}")
            return True
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Ollama API...")
    test_ollama_api()
    
    print("\nTesting local server...")
    test_local_server()
