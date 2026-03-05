#!/usr/bin/env python3
"""
Ollama Connection Diagnostic Tool
Run this to identify why Ollama works in terminal but not in your app
"""

import os
import sys
import subprocess
import requests
import socket
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"🔍 {text}")
    print(f"{'='*60}")

def check_terminal_ollama():
    """Check if ollama works in terminal"""
    print_header("Checking Terminal Ollama")
    try:
        result = subprocess.run(["ollama", "list"], 
                              capture_output=True, 
                              text=True, 
                              timeout=10)
        if result.returncode == 0:
            print("✅ 'ollama list' works in terminal")
            print(f"   Models found:")
            for line in result.stdout.split('\n')[1:]:
                if line.strip():
                    print(f"   📦 {line.split()[0]}")
            return True
        else:
            print("❌ 'ollama list' failed in terminal")
            print(f"   Error: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ 'ollama' command not found in terminal PATH")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_ollama_service():
    """Check if Ollama service is running and accessible"""
    print_header("Checking Ollama Service")
    
    # Check if process is running
    try:
        result = subprocess.run(["pgrep", "-f", "ollama"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Ollama process running with PID(s): {result.stdout.strip()}")
        else:
            print("❌ No Ollama process found running")
    except:
        print("⚠️  Could not check processes")
    
    # Check port connectivity
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 11434))
    if result == 0:
        print("✅ Port 11434 is open and listening")
    else:
        print("❌ Port 11434 is not accessible")
    sock.close()
    
    # Test API directly
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama API is responding")
            models = response.json().get('models', [])
            print(f"   API reports {len(models)} models")
            for model in models:
                print(f"   📦 {model['name']}")
        else:
            print(f"❌ API returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama API - Connection refused")
    except requests.exceptions.Timeout:
        print("❌ Connection to Ollama API timed out")
    except Exception as e:
        print(f"❌ API error: {e}")

def check_environment():
    """Check environment variables that might affect the app"""
    print_header("Checking Environment")
    
    # Python environment
    print(f"🐍 Python executable: {sys.executable}")
    print(f"📁 Python version: {sys.version}")
    print(f"📂 Current working dir: {os.getcwd()}")
    
    # Virtual environment
    venv = os.environ.get('VIRTUAL_ENV')
    if venv:
        print(f"✅ Virtual env active: {venv}")
    else:
        print("⚠️  No virtual environment active")
    
    # PATH variable
    path = os.environ.get('PATH', '')
    print(f"\n📋 PATH includes:")
    ollama_in_path = False
    for p in path.split(':'):
        if 'ollama' in p.lower():
            print(f"   ✅ {p}")
            ollama_in_path = True
        elif '/usr/local/bin' in p:
            print(f"   📍 {p} (contains ollama?)")
    
    if not ollama_in_path:
        print("⚠️  No ollama directory found in PATH")
        print("   Common ollama locations:")
        for loc in ['/usr/local/bin/ollama', '/opt/homebrew/bin/ollama', '/usr/bin/ollama']:
            if os.path.exists(loc):
                print(f"   ✅ Found at: {loc}")
    
    # Proxy settings
    http_proxy = os.environ.get('http_proxy') or os.environ.get('HTTP_PROXY')
    https_proxy = os.environ.get('https_proxy') or os.environ.get('HTTPS_PROXY')
    if http_proxy or https_proxy:
        print(f"\n🌐 Proxy detected:")
        if http_proxy:
            print(f"   http_proxy: {http_proxy}")
        if https_proxy:
            print(f"   https_proxy: {https_proxy}")
        print("   This may interfere with local connections")

def test_python_imports():
    """Test if required packages work"""
    print_header("Testing Python Packages")
    
    packages = [
        'requests',
        'langchain_ollama',
        'gradio',
    ]
    
    for package in packages:
        try:
            __import__(package)
            print(f"✅ {package} imported successfully")
        except ImportError as e:
            print(f"❌ {package} import failed: {e}")

def test_langchain_ollama():
    """Test langchain-ollama specifically"""
    print_header("Testing LangChain-Ollama Connection")
    
    try:
        from langchain_ollama import ChatOllama
        
        # Try with explicit base_url
        print("Attempting connection with explicit localhost...")
        llm = ChatOllama(
            model="llama3.2",
            base_url="http://127.0.0.1:11434",
            temperature=0.7,
            num_predict=256
        )
        
        response = llm.invoke("Say 'hello' in one word")
        print(f"✅ Success! Response: {response.content}")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import ChatOllama: {e}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nTroubleshooting tips:")
        print("1. Is Ollama running? Check with: curl http://localhost:11434")
        print("2. Try different base_url: 'http://localhost:11434' or 'http://127.0.0.1:11434'")
        print("3. Check if firewall is blocking")
    return False

if __name__ == "__main__":
    print("\n🦙 OLLAMA CONNECTION DIAGNOSTIC TOOL")
    print("This will help identify why Ollama works in terminal but not in your app\n")
    
    terminal_works = check_terminal_ollama()
    check_ollama_service()
    check_environment()
    test_python_imports()
    
    if terminal_works:
        print_header("🔧 RECOMMENDED FIXES")
        print("Ollama works in terminal but not in app. Try these fixes:\n")
        print("1. Add this to your app.py (top of file):")
        print("""
import os
import subprocess
import requests

# Fix 1: Ensure Ollama is running
def ensure_ollama():
    try:
        requests.get('http://localhost:11434/api/tags', timeout=2)
    except:
        subprocess.Popen(['ollama', 'serve'], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        time.sleep(3)

ensure_ollama()
""")
        print("\n2. Or run Ollama manually in a separate terminal:")
        print("   $ ollama serve")
        print("\n3. In your ChatOllama initialization, use:")
        print("""
llm = ChatOllama(
    model='llama3.2',
    base_url='http://127.0.0.1:11434',  # Use IP instead of localhost
    temperature=0.7
)
""")
    
    test_langchain_ollama()
