from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import google.generativeai as genai
import time
import os
import re

app = FastAPI(title="Pro Tag-Isolated RAG Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DYNAMIC PATH RESOLUTION
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE_PATH = os.path.join(BASE_DIR, "sample_data.txt")

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    return HTMLResponse(content="<h1>Python Chat Bot Backend Active</h1>", status_code=200)

class TagIsolatedSearchEngine:
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.topics_index = {}
        self.raw_text = ""
        self._load_and_parse_topics()

    def _load_and_parse_topics(self):
        try:
            if os.path.exists(self.data_path):
                with open(self.data_path, "r", encoding="utf-8") as f:
                    self.raw_text = f.read()
            # Regex to find tags
            topic_blocks = re.findall(r"\\?\[START:\s*(\w+)\\?\]([\s\S]+?)\\?\[END:\s*\1\\?\]", self.raw_text)
            for topic_name, topic_content in topic_blocks:
                self.topics_index[topic_name.strip().lower()] = topic_content.strip()
        except Exception:
            pass

    def search(self, query: str) -> tuple:
        q_clean = query.strip().lower()
        for keyword in self.topics_index.keys():
            if keyword in q_clean:
                return self.topics_index[keyword], keyword
        return self.raw_text[:1000], None

engine = TagIsolatedSearchEngine(DATA_FILE_PATH)

class QueryRequest(BaseModel):
    question: str
    apiKey: str = ""

@app.post("/ask")
async def ask_rag(request: QueryRequest):
    start_time = time.time()
    context_text, topic = engine.search(request.question)
    api_key = request.apiKey.strip() or os.environ.get("GEMINI_API_KEY", "")
    
    latency_ms = int((time.time() - start_time) * 1000)

    if not api_key:
        return {
            "answer": f"### Local Match\n{context_text}", 
            "latency_ms": latency_ms, 
            "online": False
        }

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(f"Context: {context_text}\n\nQuestion: {request.question}")
        latency_ms = int((time.time() - start_time) * 1000)
        return {"answer": response.text, "latency_ms": latency_ms, "online": True}
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        return {"answer": f"Error: {str(e)}", "latency_ms": latency_ms, "online": False}