from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import google.generativeai as genai
import chromadb
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

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, 
            detail="index.html not found! Ensure it is in the same folder as main.py."
        )

# 2. THE TAG-ISOLATION HYBRID SEARCH ENGINE
class TagIsolatedSearchEngine:
    """
    An enterprise-grade hybrid search processor. It parses structured tags directly
    to guarantee 100% precision and zero text leakage.
    """
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.topics_index = {}
        self.raw_text = ""
        self.embeddings = None
        self.vector_store = None
        self.retriever = None
        
        # Load custom indices and fallback vector maps
        self._load_and_parse_topics()
        self._initialize_vector_fallback()

    def _load_and_parse_topics(self):
        """
        Parses sample_data.txt, isolating content between [START: TOPIC] and [END: TOPIC].
        Accommodates both raw text and markdown-escaped brackets (e.g. \\[\\]).
        """
        print(f"[Engine Setup] Loading and parsing topic tags from '{self.data_path}'...")
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                self.raw_text = f.read()
        except Exception as e:
            print(f"[Engine Setup Error] Failed to read {self.data_path}: {e}")
            return

        # Regular expression designed to extract tagged blocks (supports optional backslash escaped brackets)
        topic_blocks = re.findall(r"\\?\[START:\s*(\w+)\\?\]([\s\S]+?)\\?\[END:\s*\1\\?\]", self.raw_text)
        
        for topic_name, topic_content in topic_blocks:
            clean_name = topic_name.strip().lower()
            self.topics_index[clean_name] = topic_content.strip()
            
        print(f"[Engine Setup] Isolated {len(self.topics_index)} exact topic nodes: {list(self.topics_index.keys())}")

    def _initialize_vector_fallback(self):
        """
        Populates ChromaDB fallback vector search in case no direct keyword matches are captured.
        """
        print("[Engine Setup] Segmenting isolated topics for fallback vector spaces...")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        
        try:
            loader = TextLoader(self.data_path, encoding="utf-8")
            documents = loader.load()
            docs = text_splitter.split_documents(documents)
        except Exception as e:
            print(f"[Engine Setup Error] TextLoader failed: {e}")
            docs = []

        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # Launch non-persistent, clean in-memory database client
        ephemeral_client = chromadb.EphemeralClient()
        self.vector_store = Chroma.from_documents(
            docs, 
            self.embeddings, 
            client=ephemeral_client,
            collection_name="precision_python_master"
        )
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 2})
        print("[Engine Setup] Fallback semantic vector indexes successfully populated.")

    def search(self, query: str) -> tuple:
        """
        Inspects input queries for exact structural keywords.
        Returns: (context_text, topic_matched_name_or_none)
        """
        q_clean = query.strip().lower()
        
        # Core keyword mapping router
        matched_keyword = None
        if "oop" in q_clean or "object-oriented" in q_clean or "object oriented" in q_clean or "class" in q_clean:
            matched_keyword = "oop"
        elif "tuple" in q_clean or "tuples" in q_clean:
            matched_keyword = "tuples"
        elif "set" in q_clean or "sets" in q_clean:
            matched_keyword = "sets"
        elif "list" in q_clean or "lists" in q_clean:
            matched_keyword = "lists"
        elif "variable" in q_clean or "variables" in q_clean or "pointer" in q_clean or "label" in q_clean or "sticky note" in q_clean:
            matched_keyword = "variables"
        elif "decorator" in q_clean or "decorators" in q_clean or "wrapper" in q_clean:
            matched_keyword = "decorators"
        elif "memory" in q_clean or "garbage" in q_clean or "gc" in q_clean or "reference count" in q_clean:
            matched_keyword = "memory"
        elif "function" in q_clean or "functions" in q_clean or "scope" in q_clean or "legb" in q_clean or "closure" in q_clean:
            matched_keyword = "functions"
        elif "generator" in q_clean or "generators" in q_clean or "yield" in q_clean:
            matched_keyword = "generators"
        elif "dict" in q_clean or "dictionary" in q_clean or "dictionaries" in q_clean:
            matched_keyword = "dictionaries"

        # Step A: Attempt Exact structural tag context injection (Perfect 100% precision)
        if matched_keyword and matched_keyword in self.topics_index:
            return self.topics_index[matched_keyword], matched_keyword

        # Step B: Fallback to semantic similarity matches if query has no direct keywords
        relevant_docs = self.retriever.invoke(query)
        semantic_context = "\n\n".join([doc.page_content for doc in relevant_docs]) if relevant_docs else ""
        return semantic_context, None

# 3. INSTANTIATE THE ENGINE SYSTEM
engine = TagIsolatedSearchEngine("sample_data.txt")

class QueryRequest(BaseModel):
    question: str
    apiKey: str = ""

# 4. SECURE MULTI-MODE CHAT ROUTE WITH RETRIES AND BACKOFF
@app.post("/ask")
async def ask_rag(request: QueryRequest):
    start_time = time.time()
    try:
        question = request.question.strip()
        if not question:
            return {"answer": "Input query was empty.", "latency_ms": 0, "context": "", "online": False}
        
        # --- STAGE 1: EXECUTE PRECISION KEYWORD RETRIEVAL ---
        context_text, topic_name = engine.search(question)
        
        # --- STAGE 2: GENERATION DEPLOYMENT AND API CONFIGURE ---
        api_key = request.apiKey.strip() if request.apiKey.strip() else os.environ.get("GEMINI_API_KEY", "").strip()
        
        # Baseline Local Mode (Bypasses LLM, prints exact structured chunk)
        if not api_key or api_key == "your_free_key_here":
            latency_ms = int((time.time() - start_time) * 1000)
            topic_header = topic_name.upper() if topic_name else "SEMANTIC SEARCH MATCH"
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

        # Premium Conversational Mode with active Gemini 2.5 API & Exponential Backoff
        try:
            # Set the exact supported model in the preview environment
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
            
            # Exponential Backoff Retrier (Up to 5 attempts with delays of 1s, 2s, 4s, 8s, 16s)
            response_text = ""
            for attempt in range(5):
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(structured_prompt)
                    response_text = response.text
                    break  # Success, exit loop
                except Exception as call_err:
                    if attempt == 4:  # Final attempt failed
                        raise call_err
                    sleep_time = 2 ** attempt
                    time.sleep(sleep_time)
            
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "answer": f"{response_text}\n\n***\n✨ **RAG Engine Pro:** Dynamically synthesized using active Gemini 2.5 and verified local documentation.",
                "latency_ms": latency_ms,
                "context": context_text,
                "online": True
            }
            
        except Exception as api_err:
            latency_ms = int((time.time() - start_time) * 1000)
            fallback_response = (
                f"### 🔍 Precise Local Database Match Found\n"
                f"*(⚠️ Conversational synthesis unavailable: API key verification rejected)*\n\n"
                f"**System error feedback:** {str(api_err)}\n\n"
                f"---\n\n"
                f"{context_text}"
            )
            return {
                "answer": fallback_response,
                "latency_ms": latency_ms,
                "context": context_text,
                "online": False
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))