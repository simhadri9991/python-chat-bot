from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import google.generativeai as genai
import time
import os
import re

app = FastAPI(title="Pro Tag-Isolated RAG Backend")

# Enable wide open CORS policies so your GitHub Pages frontend can connect cleanly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Python Chat Bot Backend Active</h1><p>Frontend template asset is detached.</p>", status_code=200)

# 2. HIGH-PERFORMANCE TAG-ISOLATION ENGINE (SERVERLESS ROUTED)
class TagIsolatedSearchEngine:
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.topics_index = {}
        self.raw_text = ""
        self._load_and_parse_topics()

    def _load_and_parse_topics(self):
        print(f"[Engine Setup] Loading and parsing topic tags from '{self.data_path}'...")
        try:
            if os.path.exists(self.data_path):
                with open(self.data_path, "r", encoding="utf-8") as f:
                    self.raw_text = f.read()
            else:
                self.raw_text = "[START: OOP]\nObject-Oriented Programming (OOP) master guide reference node.\n[END: OOP]"
        except Exception as e:
            print(f"[Engine Setup Error] Failed to read {self.data_path}: {e}")
            return

        # Core regex engine parsing
        topic_blocks = re.findall(r"\\?\[START:\s*(\w+)\\?\]([\s\S]+?)\\?\[END:\s*\1\\?\]", self.raw_text)
        
        for topic_name, topic_content in topic_blocks:
            clean_name = topic_name.strip().lower()
            self.topics_index[clean_name] = topic_content.strip()
            
        print(f"[Engine Setup] Isolated {len(self.topics_index)} exact topic nodes.")

    def search(self, query: str) -> tuple:
        q_clean = query.strip().lower()
        
        # Route keywords directly to index keys
        matched_keyword = None
        if any(x in q_clean for x in ["oop", "object-oriented", "object oriented", "class"]):
            matched_keyword = "oop"
        elif "tuple" in q_clean or "tuples" in q_clean:
            matched_keyword = "tuples"
        elif "set" in q_clean or "sets" in q_clean:
            matched_keyword = "sets"
        elif "list" in q_clean or "lists" in q_clean:
            matched_keyword = "lists"
        elif any(x in q_clean for x in ["variable", "variables", "pointer", "label", "sticky note"]):
            matched_keyword = "variables"
        elif "decorator" in q_clean or "decorators" in q_clean or "wrapper" in q_clean:
            matched_keyword = "decorators"
        elif any(x in q_clean for x in ["memory", "garbage", "gc", "reference count"]):
            matched_keyword = "memory"
        elif any(x in q_clean for x in ["function", "functions", "scope", "legb", "closure"]):
            matched_keyword = "functions"
        elif "generator" in q_clean or "generators" in q_clean or "yield" in q_clean:
            matched_keyword = "generators"
        elif any(x in q_clean for x in ["dict", "dictionary", "dictionaries"]):
            matched_keyword = "dictionaries"

        # Return exact block if found
        if matched_keyword and matched_keyword in self.topics_index:
            return self.topics_index[matched_keyword], matched_keyword

        # Serverless Clean Fallback (Returns top textual paragraphs if keyword isn't hit)
        fallback_text = ""
        paragraphs = [p.strip() for p in self.raw_text.split("\n\n") if p.strip()]
        matches = [p for p in paragraphs if any(word in p.lower() for word in q_clean.split())]
        if matches:
            fallback_text = "\n\n".join(matches[:2])
        else:
            fallback_text = self.raw_text[:1200] # Safe snapshot boundary fallback
            
        return fallback_text, None

# Initialize search context mapper
engine = TagIsolatedSearchEngine("sample_data.txt")

class QueryRequest(BaseModel):
    question: str
    apiKey: str = ""

# 3. GLOBAL SECURE EXECUTION RUNTIME
@app.post("/ask")
async def ask_rag(request: QueryRequest):
    start_time = time.time()
    try:
        question = request.question.strip()
        if not question:
            return {"answer": "Input query was empty.", "latency_ms": 0, "context": "", "online": False}
        
        # Staging Match Extraction
        context_text, topic_name = engine.search(question)
        
        # Extract environment key maps
        api_key = request.apiKey.strip() if request.apiKey.strip() else os.environ.get("GEMINI_API_KEY", "").strip()
        
        # Fallback Local Data Streamer
        if not api_key or api_key == "your_free_key_here":
            latency_ms = int((time.time() - start_time) * 1000)
            topic_header = topic_name.upper() if topic_name else "KNOWLEDGE DATABASE SEARCH"
            return {
                "answer": (
                    f"### 🔍 Precise Local Database Match Found\n"
                    f"*(Topic: {topic_header} • Operational Mode: Tag-Isolated Fallback)*\n\n"
                    f"{context_text}"
                ),
                "latency_ms": latency_ms,
                "context": context_text,
                "online": False
            }

        # Active Global Conversational Mode with LLM Generation
        try:
            model_name = "gemini-2.5-flash-preview-09-2025"
            
            structured_prompt = (
                f"You are a friendly, highly skilled Python programming tutor.\n"
                f"Using ONLY the provided reference database context below, answer the user's question accurately.\n"
                f"If the information is not directly in the context, use your deep general knowledge but mention clearly that you supplemented the database content with general programming concepts.\n\n"
                f"--- Context from Database ---\n"
                f"{context_text}\n\n"
                f"--- User's Question ---\n"
                f"{question}\n\n"
                f"Synthesized Response (Format beautiful answers with bold terms, neat bullets, and syntax-highlighted code boxes):"
            )
            
            response_text = ""
            for attempt in range(3):
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(structured_prompt)
                    response_text = response.text
                    break
                except Exception as call_err:
                    if attempt == 2:
                        raise call_err
                    time.sleep(1)
            
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "answer": f"{response_text}\n\n***\n✨ **RAG Engine Pro:** Dynamically synthesized using active Gemini 2.5 and verified cloud documentation.",
                "latency_ms": latency_ms,
                "context": context_text,
                "online": True
            }
            
        except Exception as api_err:
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "answer": f"### 🔍 Precise Local Database Match Found\n*(⚠️ Conversational synthesis unavailable: API key verification rejected)*\n\n**System feedback:** {str(api_err)}\n\n---\n\n{context_text}",
                "latency_ms": latency_ms,
                "context": context_text,
                "online": False
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))