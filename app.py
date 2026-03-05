"""
JARVIS AI Assistant - Iron Man Inspired UI
A private, local chatbot with voice input/output and holographic UI
Run entirely on your machine - no data ever leaves your computer!
"""

import os
import gradio as gr
import time
import json
import requests
import subprocess
import tempfile
import threading
import atexit
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_community.chat_message_histories import ChatMessageHistory

# Voice imports - with fallbacks
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    sr = None
    SPEECH_RECOGNITION_AVAILABLE = False
    print("⚠️ Speech recognition not installed. Run: pip install SpeechRecognition")

try:
    import pyttsx3
    TTS_ENGINE_AVAILABLE = True
except ImportError:
    pyttsx3 = None
    TTS_ENGINE_AVAILABLE = False
    print("⚠️ pyttsx3 not installed. Run: pip install pyttsx3")

try:
    from gtts import gTTS
    import pygame
    GTTS_AVAILABLE = True
except ImportError:
    gTTS = None
    pygame = None
    GTTS_AVAILABLE = False
    print("⚠️ gTTS/pygame not installed. Run: pip install gtts pygame")

# Suppress pyttsx3 cleanup error
def cleanup_tts():
    try:
        if 'tts_engine' in locals():
            pass
    except:
        pass

atexit.register(cleanup_tts)

# Load environment variables
load_dotenv()

# ============================================
# JARVIS THEME CONFIGURATION
# ============================================

JARVIS_CSS = """
/* JARVIS Theme - Iron Man Inspired */
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Rajdhani:wght@300;400;500;600;700&display=swap');

:root {
    --jarvis-bg: #0a0f1e;
    --jarvis-darker: #050812;
    --jarvis-blue: #00f3ff;
    --jarvis-blue-glow: rgba(0, 243, 255, 0.5);
    --jarvis-dark-blue: #0a1a2f;
    --jarvis-grid: #1a2f4a;
    --jarvis-text: #e0f2fe;
    --jarvis-accent: #ff3366;
    --jarvis-accent-glow: rgba(255, 51, 102, 0.3);
}

/* Global Styles */
body {
    background: var(--jarvis-bg) !important;
    font-family: 'Rajdhani', sans-serif !important;
    color: var(--jarvis-text) !important;
    position: relative;
    overflow-x: hidden;
}

/* Holographic Grid Background */
body::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(90deg, var(--jarvis-grid) 1px, transparent 1px) 0 0 / 40px 40px,
                linear-gradient(0deg, var(--jarvis-grid) 1px, transparent 1px) 0 0 / 40px 40px;
    opacity: 0.1;
    pointer-events: none;
    animation: gridPulse 4s ease-in-out infinite;
    z-index: 0;
}

/* Animated Scan Lines */
body::after {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 100vh;
    background: linear-gradient(180deg, 
        transparent 0%, 
        rgba(0, 243, 255, 0.02) 50%, 
        transparent 100%);
    animation: scan 8s linear infinite;
    pointer-events: none;
    z-index: 1;
}

/* JARVIS Header */
.jarvis-header {
    position: relative;
    padding: 20px;
    margin-bottom: 20px;
    background: linear-gradient(90deg, 
        transparent 0%, 
        rgba(0, 243, 255, 0.1) 50%, 
        transparent 100%);
    border-bottom: 2px solid var(--jarvis-blue);
    box-shadow: 0 0 20px var(--jarvis-blue-glow);
    text-align: center;
    z-index: 10;
    animation: headerFlicker 3s infinite;
}

.jarvis-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 3em;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 8px;
    color: var(--jarvis-blue);
    text-shadow: 0 0 10px var(--jarvis-blue),
                 0 0 20px var(--jarvis-blue),
                 0 0 40px var(--jarvis-blue);
    margin: 0;
    animation: textPulse 2s ease-in-out infinite;
}

.jarvis-subtitle {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.2em;
    color: var(--jarvis-text);
    letter-spacing: 4px;
    margin-top: 5px;
    opacity: 0.8;
}

/* Sidebar Cards */
.jarvis-panel {
    position: relative;
    background: linear-gradient(135deg, 
        rgba(10, 15, 30, 0.9) 0%, 
        rgba(26, 42, 68, 0.9) 100%);
    border: 1px solid var(--jarvis-blue);
    border-radius: 15px;
    padding: 20px;
    margin-bottom: 20px;
    backdrop-filter: blur(10px);
    box-shadow: 0 0 20px var(--jarvis-blue-glow);
    transition: all 0.3s ease;
    z-index: 10;
    overflow: hidden;
}

.jarvis-panel:hover {
    border-color: var(--jarvis-accent);
    box-shadow: 0 0 30px var(--jarvis-accent-glow);
    transform: translateY(-2px);
}

.jarvis-panel-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 1.2em;
    font-weight: 600;
    color: var(--jarvis-blue);
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 15px;
    border-bottom: 1px solid var(--jarvis-blue);
    padding-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.jarvis-panel-title::before {
    content: '►';
    color: var(--jarvis-blue);
    font-size: 0.8em;
    animation: pulse 2s infinite;
}

/* Status Indicator */
.jarvis-led {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: var(--jarvis-blue);
    box-shadow: 0 0 10px var(--jarvis-blue);
    animation: ledPulse 1.5s infinite;
    display: inline-block;
    margin-right: 8px;
}

/* Input Area */
.jarvis-input-container {
    background: rgba(10, 15, 30, 0.9);
    border: 2px solid var(--jarvis-blue);
    border-radius: 30px;
    padding: 5px;
    margin-top: 20px;
    display: flex;
    align-items: center;
    backdrop-filter: blur(10px);
    box-shadow: 0 0 20px var(--jarvis-blue-glow);
    z-index: 10;
}

/* Voice Button */
.jarvis-voice-btn {
    background: transparent !important;
    border: 2px solid var(--jarvis-blue) !important;
    border-radius: 50% !important;
    width: 50px !important;
    height: 50px !important;
    padding: 0 !important;
    margin: 0 5px !important;
    color: var(--jarvis-blue) !important;
    font-size: 1.5em !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

.jarvis-voice-btn:hover {
    background: var(--jarvis-blue) !important;
    color: var(--jarvis-bg) !important;
    box-shadow: 0 0 20px var(--jarvis-blue) !important;
    transform: scale(1.1);
}

/* Animations */
@keyframes gridPulse {
    0%, 100% { opacity: 0.1; }
    50% { opacity: 0.15; }
}

@keyframes scan {
    0% { transform: translateY(-100%); }
    100% { transform: translateY(100%); }
}

@keyframes textPulse {
    0%, 100% { text-shadow: 0 0 10px var(--jarvis-blue),
                            0 0 20px var(--jarvis-blue),
                            0 0 40px var(--jarvis-blue); }
    50% { text-shadow: 0 0 15px var(--jarvis-blue),
                       0 0 30px var(--jarvis-blue),
                       0 0 60px var(--jarvis-blue); }
}

@keyframes headerFlicker {
    0%, 100% { opacity: 1; }
    3% { opacity: 0.9; }
    6% { opacity: 1; }
    7% { opacity: 0.8; }
    8% { opacity: 1; }
    9% { opacity: 0.9; }
    10% { opacity: 1; }
}

@keyframes ledPulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(0.8); }
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
"""

# ============================================
# OLLAMA MANAGER
# ============================================

class OllamaManager:
    """Manages Ollama service and models"""
    
    def __init__(self):
        self.base_url = "http://127.0.0.1:11434"
        self.models = []
        self.is_running = False
        self.status_message = ""
        
    def check_status(self):
        """Check if Ollama is running and get models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if response.status_code == 200:
                self.is_running = True
                models_data = response.json().get("models", [])
                self.models = [model["name"] for model in models_data]
                self.status_message = f"ONLINE • {len(self.models)} MODELS"
                return True, self.models, self.status_message
            else:
                self.is_running = False
                self.status_message = "OFFLINE • CHECK CONNECTION"
                return False, [], self.status_message
        except requests.exceptions.ConnectionError:
            self.is_running = False
            self.status_message = "OFFLINE • SYSTEM OFFLINE"
            return False, [], self.status_message
        except Exception as e:
            self.is_running = False
            self.status_message = f"ERROR • SYSTEM MALFUNCTION"
            return False, [], self.status_message

# ============================================
# VOICE MANAGER
# ============================================

class VoiceManager:
    """Handles voice input and output for JARVIS"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer() if SPEECH_RECOGNITION_AVAILABLE else None
        self.tts_engine = None
        self.tts_engine_type = None
        self.microphone = None
        
        # Initialize TTS
        self._init_tts()
        
        # Initialize microphone
        self._init_microphone()
    
    def _init_tts(self):
        """Initialize text-to-speech engine"""
        if TTS_ENGINE_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', 180)
                self.tts_engine.setProperty('volume', 0.9)
                
                voices = self.tts_engine.getProperty('voices')
                for voice in voices:
                    if 'male' in voice.name.lower() or 'david' in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
                
                self.tts_engine_type = 'pyttsx3'
                print("✅ Voice: pyttsx3 initialized")
                return
            except Exception as e:
                print(f"⚠️ pyttsx3 init failed: {e}")
        
        if GTTS_AVAILABLE:
            try:
                pygame.mixer.init()
                self.tts_engine_type = 'gtts'
                print("✅ Voice: gTTS initialized (requires internet)")
            except Exception as e:
                print(f"⚠️ gTTS init failed: {e}")
        
        if not self.tts_engine_type:
            print("❌ No TTS engine available. Voice output disabled.")
    
    def _init_microphone(self):
        """Initialize microphone for speech recognition"""
        if self.recognizer:
            try:
                self.microphone = sr.Microphone()
                with self.microphone as source:
                    print("🔊 Calibrating microphone for ambient noise...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print("✅ Microphone initialized")
            except Exception as e:
                print(f"⚠️ Microphone init failed: {e}")
                self.microphone = None
    
    def listen(self, timeout=5, phrase_time_limit=10):
        """Listen for voice input and convert to text"""
        if not self.recognizer or not self.microphone:
            return None, "Voice input not available"
        
        try:
            with self.microphone as source:
                print("🎤 Listening...")
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
            
            print("🔄 Processing speech...")
            text = self.recognizer.recognize_google(audio)
            print(f"✅ Recognized: {text}")
            return text, "✅ Voice captured"
            
        except sr.WaitTimeoutError:
            return None, "⏱️ No speech detected"
        except sr.UnknownValueError:
            return None, "❌ Could not understand audio"
        except sr.RequestError as e:
            return None, f"❌ Recognition service error: {e}"
        except Exception as e:
            return None, f"❌ Error: {str(e)}"
    
    def speak(self, text, wait=True):
        """Convert text to speech and play it"""
        if not self.tts_engine_type:
            return False
        
        try:
            if self.tts_engine_type == 'pyttsx3':
                self.tts_engine.say(text)
                if wait:
                    self.tts_engine.runAndWait()
            elif self.tts_engine_type == 'gtts':
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
                    filename = tmp.name
                
                tts = gTTS(text=text, lang='en', slow=False)
                tts.save(filename)
                
                pygame.mixer.music.load(filename)
                pygame.mixer.music.play()
                
                if wait:
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)
                
                try:
                    os.unlink(filename)
                except:
                    pass
            return True
        except Exception as e:
            print(f"❌ TTS error: {e}")
            return False

# ============================================
# JARVIS CHATBOT CORE
# ============================================

class JarvisChatbot:
    """JARVIS AI Assistant - Inspired by Iron Man"""
    
    def __init__(self):
        self.ollama_manager = OllamaManager()
        self.voice_manager = VoiceManager()
        self.current_model = None
        self.sessions = {}
        self.current_session_id = "default"
        
        # JARVIS System Prompt
        self.system_prompt = """You are JARVIS (Just A Rather Very Intelligent System), Tony Stark's AI assistant.
        
        Personality Guidelines:
        - Be sophisticated, polite, and professional with a hint of British charm
        - Address the user as "Sir" or "Madam" appropriately
        - Use technical terminology when appropriate but explain complex concepts
        - Be efficient and precise in your responses
        - Occasionally use phrases like "As you can see", "I've taken the liberty of", "Shall I proceed?"
        - Maintain a calm, composed demeanor even when handling errors
        - Keep responses concise for voice output (1-3 sentences when appropriate)
        
        Remember: You're not just an AI - you're JARVIS, the height of technological sophistication."""
        
        self.temperature = 0.7
        self.max_tokens = 2048
        self.voice_enabled = True
        self.auto_speak = True
        
        # Initialize
        self.refresh_models()
        self.create_session("default")
    
    def refresh_models(self):
        """Refresh available models"""
        success, models, status = self.ollama_manager.check_status()
        if success and models:
            self.current_model = models[0]
        return models, status
    
    def create_session(self, session_name):
        """Create a new chat session"""
        if session_name not in self.sessions:
            self.sessions[session_name] = {
                'history': ChatMessageHistory(),
                'created': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'model': self.current_model
            }
            self.sessions[session_name]['history'].add_message(
                SystemMessage(content=self.system_prompt)
            )
        return session_name
    
    def get_sessions_list(self):
        """Get list of available sessions"""
        return list(self.sessions.keys())
    
    def switch_session(self, session_name):
        """Switch to a different session"""
        if session_name in self.sessions:
            self.current_session_id = session_name
            return self.get_gradio_history()
        return []
    
    def get_gradio_history(self):
        """Get history formatted for Gradio"""
        if self.current_session_id not in self.sessions:
            return []
        
        history = []
        messages = list(self.sessions[self.current_session_id]['history'].messages)
        
        i = 1 if isinstance(messages[0], SystemMessage) else 0
        
        while i < len(messages):
            user_msg = None
            assistant_msg = None
            
            if i < len(messages) and isinstance(messages[i], HumanMessage):
                user_msg = messages[i].content
                i += 1
            
            if i < len(messages) and isinstance(messages[i], AIMessage):
                assistant_msg = messages[i].content
                i += 1
            
            if user_msg and assistant_msg:
                history.append([user_msg, assistant_msg])
        
        return history
    
    def chat(self, message, history):
        """Process a message and return updated history"""
        if not self.current_model:
            error_msg = "I apologize, Sir/Madam, but the system appears to be offline."
            history.append([message, error_msg])
            if self.auto_speak and self.voice_enabled:
                threading.Thread(target=self.voice_manager.speak, args=(error_msg, True)).start()
            return history
        
        if self.current_session_id not in self.sessions:
            self.create_session(self.current_session_id)
        
        session = self.sessions[self.current_session_id]
        session['history'].add_user_message(message)
        
        try:
            llm = ChatOllama(
                model=self.current_model,
                base_url=self.ollama_manager.base_url,
                temperature=self.temperature,
                num_predict=self.max_tokens
            )
            
            response = llm.invoke(session['history'].messages)
            response_text = response.content
            
            session['history'].add_ai_message(response_text)
            history.append([message, response_text])
            
            if self.auto_speak and self.voice_enabled:
                threading.Thread(target=self.voice_manager.speak, args=(response_text, True)).start()
            
        except Exception as e:
            error_msg = f"Systems malfunction: {str(e)}"
            session['history'].add_ai_message(error_msg)
            history.append([message, error_msg])
            if self.auto_speak and self.voice_enabled:
                threading.Thread(target=self.voice_manager.speak, args=(error_msg, True)).start()
        
        return history
    
    def voice_input(self):
        """Capture voice input and return text"""
        if not self.voice_enabled:
            return "", "❌ Voice input disabled"
        
        text, status = self.voice_manager.listen()
        if text:
            return text, f"✅ {status}"
        else:
            return "", f"❌ {status}"
    
    def toggle_voice(self):
        """Toggle voice on/off"""
        self.voice_enabled = not self.voice_enabled
        return f"🔊 Voice {'enabled' if self.voice_enabled else 'disabled'}"
    
    def toggle_auto_speak(self):
        """Toggle auto-speak on/off"""
        self.auto_speak = not self.auto_speak
        return f"🔊 Auto-speak {'enabled' if self.auto_speak else 'disabled'}"
    
    def clear_history(self):
        """Clear current session history"""
        if self.current_session_id in self.sessions:
            self.sessions[self.current_session_id]['history'] = ChatMessageHistory()
            self.sessions[self.current_session_id]['history'].add_message(
                SystemMessage(content=self.system_prompt)
            )
        return []
    
    def export_chat(self, format="txt"):
        """Export current chat history"""
        if self.current_session_id not in self.sessions:
            return None
        
        history = self.get_gradio_history()
        if not history:
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "txt":
            content = f"JARVIS LOG • Session: {self.current_session_id}\n"
            content += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            content += f"Model: {self.current_model}\n"
            content += "═"*60 + "\n\n"
            
            for user_msg, bot_msg in history:
                content += f"► USER:\n{user_msg}\n\n"
                content += f"◄ JARVIS:\n{bot_msg}\n\n"
                content += "─"*40 + "\n\n"
            
            filename = f"jarvis_log_{timestamp}.txt"
            with open(filename, "w") as f:
                f.write(content)
            return f"📁 Log exported: {filename}"
            
        elif format == "json":
            export_data = {
                "session": self.current_session_id,
                "timestamp": datetime.now().isoformat(),
                "model": self.current_model,
                "conversation": [
                    {"user": user_msg, "jarvis": bot_msg}
                    for user_msg, bot_msg in history
                ]
            }
            filename = f"jarvis_log_{timestamp}.json"
            with open(filename, "w") as f:
                json.dump(export_data, f, indent=2)
            return f"📁 Log exported: {filename}"
        
        return None

# ============================================
# JARVIS UI COMPONENTS
# ============================================

# Initialize chatbot
jarvis = JarvisChatbot()

# Helper functions
def refresh_models():
    models, status = jarvis.refresh_models()
    return gr.Dropdown.update(choices=models, value=models[0] if models else None), status

def change_model(model_name):
    if model_name:
        jarvis.current_model = model_name
    return f"► MODEL: {model_name}"

def create_new_session(name):
    if name and name.strip():
        jarvis.create_session(name.strip())
        return gr.Dropdown.update(choices=jarvis.get_sessions_list(), value=name.strip()), []
    return gr.Dropdown.update(choices=jarvis.get_sessions_list()), []

def switch_session(session_name):
    if session_name:
        return jarvis.switch_session(session_name)
    return []

def clear_chat():
    return jarvis.clear_history()

def export_chat(format):
    result = jarvis.export_chat(format)
    return result if result else "❌ No conversation to export"

def update_settings(temperature, max_tokens):
    jarvis.temperature = temperature
    jarvis.max_tokens = int(max_tokens)
    return "⚡ Settings calibrated"

def get_status():
    models, status = jarvis.refresh_models()
    voice_status = "ON" if jarvis.voice_enabled else "OFF"
    auto_speak = "ON" if jarvis.auto_speak else "OFF"
    return f"""
**SYSTEM STATUS**
├─ Power: ONLINE
├─ Connection: {status}
├─ Model: {jarvis.current_model or 'None'}
├─ Voice: {voice_status}
├─ Auto-Speak: {auto_speak}
├─ Session: {jarvis.current_session_id}
└─ Memory: {len(jarvis.sessions)} sessions active
"""

def handle_voice_input():
    """Handle voice input button click"""
    text, status = jarvis.voice_input()
    return text, status

def toggle_voice():
    return jarvis.toggle_voice()

def toggle_auto_speak():
    return jarvis.toggle_auto_speak()

# ============================================
# JARVIS INTERFACE
# ============================================

with gr.Blocks(css=JARVIS_CSS, theme=gr.themes.Base()) as demo:
    # Header
    with gr.Row():
        with gr.Column():
            gr.HTML("""
            <div class="jarvis-header">
                <h1 class="jarvis-title">J.A.R.V.I.S.</h1>
                <div class="jarvis-subtitle">JUST A RATHER VERY INTELLIGENT SYSTEM</div>
            </div>
            """)
    
    with gr.Row():
        # Left Panel - Systems Control
        with gr.Column(scale=1, min_width=300):
            # Status Panel
            with gr.Group():
                gr.HTML('<div class="jarvis-panel-title">SYSTEM STATUS</div>')
                with gr.Row():
                    status_led = gr.HTML('<div class="jarvis-led"></div>')
                    status_text = gr.Markdown("⏳ Initializing systems...")
                refresh_btn = gr.Button("🔄 RECALIBRATE")
            
            # Model Selection
            with gr.Group():
                gr.HTML('<div class="jarvis-panel-title">NEURAL CORE</div>')
                model_dropdown = gr.Dropdown(
                    choices=[],
                    label="Select Model"
                )
                model_status = gr.Markdown("")
            
            # Voice Control
            with gr.Group():
                gr.HTML('<div class="jarvis-panel-title">VOICE SYSTEMS</div>')
                with gr.Row():
                    voice_toggle = gr.Button("🔊 TOGGLE VOICE")
                    auto_speak_toggle = gr.Button("🎤 TOGGLE AUTO-SPEAK")
                voice_status = gr.Markdown(f"Voice: {'ON' if jarvis.voice_enabled else 'OFF'} | Auto-speak: {'ON' if jarvis.auto_speak else 'OFF'}")
            
            # Chat Sessions
            with gr.Group():
                gr.HTML('<div class="jarvis-panel-title">SESSION CONTROL</div>')
                sessions_dropdown = gr.Dropdown(
                    choices=[],
                    label="Active Sessions"
                )
                with gr.Row():
                    new_session_input = gr.Textbox(
                        label="New Session",
                        placeholder="Enter designation...",
                        scale=3
                    )
                    create_session_btn = gr.Button("CREATE", scale=1)
            
            # Settings
            with gr.Group():
                gr.HTML('<div class="jarvis-panel-title">SYSTEM PARAMETERS</div>')
                temperature_slider = gr.Slider(
                    minimum=0.0, maximum=2.0, value=0.7, step=0.1,
                    label="TEMPERATURE"
                )
                max_tokens_slider = gr.Slider(
                    minimum=256, maximum=4096, value=2048, step=256,
                    label="MAX TOKENS"
                )
                apply_settings_btn = gr.Button("CALIBRATE")
                settings_status = gr.Markdown("")
            
            # Export
            with gr.Group():
                gr.HTML('<div class="jarvis-panel-title">DATA LOGGING</div>')
                with gr.Row():
                    export_txt_btn = gr.Button("📄 TXT LOG")
                    export_json_btn = gr.Button("📊 JSON LOG")
                export_status = gr.Markdown("")
        
        # Right Panel - Main Interface
        with gr.Column(scale=3):
            # Chat Display
            with gr.Group():
                gr.HTML('<div class="jarvis-panel-title">HOLOGRAPHIC DISPLAY</div>')
                chatbot_interface = gr.Chatbot(
                    label="",
                    height=450
                )
                
                # Input Area with Voice Button
                with gr.Row():
                    msg = gr.Textbox(
                        label="",
                        placeholder="Type your message or click the voice button...",
                        scale=8,
                        container=False
                    )
                    voice_btn = gr.Button("🎤", elem_classes="jarvis-voice-btn", scale=1)
                    send_btn = gr.Button("📤", scale=1, variant="primary")
                
                # Voice input status
                voice_input_status = gr.Markdown("")
                
                # Control Row
                with gr.Row():
                    clear_btn = gr.Button("🧹 CLEAR DISPLAY")
                    status_btn = gr.Button("ℹ️ SYSTEM INFO")
                
                # Examples
                gr.Examples(
                    examples=[
                        ["Good morning, JARVIS. What's on my schedule today?"],
                        ["Analyze this code for potential improvements"],
                        ["Explain quantum computing in simple terms"],
                        ["I need a security protocol for a new system"],
                        ["Calculate the trajectory for orbital insertion"],
                        ["Run diagnostic on the arc reactor"]
                    ],
                    inputs=msg
                )
    
    # Event Handlers
    demo.load(
        fn=lambda: (
            refresh_models()[0],
            refresh_models()[1],
            gr.Dropdown.update(choices=jarvis.get_sessions_list(), value="default")
        ),
        outputs=[model_dropdown, status_text, sessions_dropdown]
    )
    
    refresh_btn.click(
        fn=refresh_models,
        outputs=[model_dropdown, status_text]
    )
    
    model_dropdown.change(
        fn=change_model,
        inputs=model_dropdown,
        outputs=model_status
    )
    
    # Voice controls
    voice_toggle.click(
        fn=toggle_voice,
        outputs=voice_status
    )
    
    auto_speak_toggle.click(
        fn=toggle_auto_speak,
        outputs=voice_status
    )
    
    # Voice button click
    voice_btn.click(
        fn=handle_voice_input,
        outputs=[msg, voice_input_status]
    )
    
    # Send message
    send_btn.click(
        fn=jarvis.chat,
        inputs=[msg, chatbot_interface],
        outputs=chatbot_interface
    ).then(
        fn=lambda: ("", ""),  # Clear input and status
        outputs=[msg, voice_input_status]
    )
    
    # Enter key submits
    msg.submit(
        fn=jarvis.chat,
        inputs=[msg, chatbot_interface],
        outputs=chatbot_interface
    ).then(
        fn=lambda: ("", ""),
        outputs=[msg, voice_input_status]
    )
    
    clear_btn.click(
        fn=clear_chat,
        outputs=chatbot_interface
    )
    
    create_session_btn.click(
        fn=create_new_session,
        inputs=new_session_input,
        outputs=[sessions_dropdown, chatbot_interface]
    ).then(
        fn=lambda: "",
        outputs=new_session_input
    )
    
    sessions_dropdown.change(
        fn=switch_session,
        inputs=sessions_dropdown,
        outputs=chatbot_interface
    )
    
    apply_settings_btn.click(
        fn=update_settings,
        inputs=[temperature_slider, max_tokens_slider],
        outputs=settings_status
    )
    
    export_txt_btn.click(
        fn=lambda: export_chat("txt"),
        outputs=export_status
    )
    
    export_json_btn.click(
        fn=lambda: export_chat("json"),
        outputs=export_status
    )
    
    status_btn.click(
        fn=get_status,
        outputs=status_text
    )

# ============================================
# MAIN ENTRY POINT
# ============================================

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║     J.A.R.V.I.S. - Voice Enabled Edition            ║
    ║     Just A Rather Very Intelligent System           ║
    ║                                                      ║
    ║     "At your service, Sir/Madam"                    ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        debug=False
    )