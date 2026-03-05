# minimal_test.py
import os
import requests
from langchain_ollama import ChatOllama

# Set PATH
os.environ["PATH"] = "/usr/local/bin:/opt/homebrew/bin:" + os.environ.get("PATH", "")

print("1️⃣ Testing direct API connection...")
try:
    r = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
    print(f"✅ API response: {r.status_code}")
    print(f"Models: {r.json().get('models', [])}")
except Exception as e:
    print(f"❌ API failed: {e}")

print("\n2️⃣ Testing LangChain connection...")
try:
    llm = ChatOllama(
        model="llama3.2",
        base_url="http://127.0.0.1:11434",
        temperature=0.7
    )
    response = llm.invoke("Say 'hello'")
    print(f"✅ LangChain works! Response: {response.content}")
except Exception as e:
    print(f"❌ LangChain failed: {e}")
    