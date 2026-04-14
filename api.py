"""
MonolithMapper — FastAPI Backend
=================================
Compatible with LangChain 1.x / langchain-core 1.x.
Uses RunnableWithMessageHistory (modern replacement for AgentExecutor + memory).
Now secured with JWT Authentication!

Run with:  uvicorn api:app --reload --port 8000
"""

from __future__ import annotations

from google.cloud import storage
import datetime

import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
from datetime import timedelta
import json
import shutil

from fastapi import FastAPI, HTTPException, Request, status, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

# ── Auth Modules ─────────────────────────────────────────────────────────────
from auth import create_access_token, get_current_user, verify_password, fake_users_db, ACCESS_TOKEN_EXPIRE_MINUTES, pwd_context

# ── Local Ingestion Modules ──────────────────────────────────────────────────
from ingestion.pipeline import run_stage1
from ingestion.indexer import GraphEnricher

# ── LangChain 1.x compatible imports ─────────────────────────────────────────
from langchain_ollama import ChatOllama
from langchain_qdrant import QdrantVectorStore
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from qdrant_client import QdrantClient

from google.oauth2 import service_account

# ── Langfuse observability (optional) ────────────────────────────────────────
try:
    from langfuse.callback import CallbackHandler as LangfuseCallback
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False

logger = logging.getLogger("monolith_mapper.api")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s"
)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

class Settings:
    # Pull directly from Cloud Run Environment Variables!
    QDRANT_URL: str         = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_API_KEY: str     = os.getenv("QDRANT_API_KEY", "")
    QDRANT_COLLECTION: str  = "monolith_mapper_v2"

    OLLAMA_BASE_URL: str    = "http://localhost:11434"
    OLLAMA_MODEL: str       = "llama3.1:8b"

    AGENT_TEMPERATURE: float  = 0.1
    MAX_HISTORY_MESSAGES: int = 20

    GENERATED_CODE_DIR: str = "generated_code"

    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

settings = Settings()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — GLOBAL APP STATE
# ══════════════════════════════════════════════════════════════════════════════

class AppState:
    qdrant_client:     Optional[QdrantClient]       = None
    vector_store:      Optional[QdrantVectorStore]  = None
    llm:               Optional[ChatOllama]          = None
    embeddings:        Optional[FastEmbedEmbeddings] = None
    is_ready:          bool                         = False
    session_histories: dict[str, ChatMessageHistory] = {}

state = AppState()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — LIFESPAN
# ══════════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("MonolithMapper API starting up...")
    t0 = time.perf_counter()

    # 1. Qdrant
    try:
        if settings.QDRANT_URL != "localhost" and "http" in settings.QDRANT_URL:
            # PRODUCTION: Connect to Qdrant Cloud using the injected keys
            state.qdrant_client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
            )
        else:
            # LOCAL FALLBACK
            state.qdrant_client = QdrantClient(host="localhost", port=6333)

        state.qdrant_client.get_collections()
        logger.info(f"Qdrant connected to {settings.QDRANT_URL}")
    except Exception as e:
        logger.warning(f"Qdrant not available: {e} — /chat will still work without RAG")

    # 2. Embeddings
    try:
        state.embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")
        logger.info("Embeddings ready: BAAI/bge-small-en-v1.5")
    except Exception as e:
        logger.error(f"Embeddings failed: {e}")

    # 3. Vector store
    if state.qdrant_client and state.embeddings:
        try:
            from qdrant_client.models import Distance, VectorParams
            collections = [c.name for c in state.qdrant_client.get_collections().collections]
            if settings.QDRANT_COLLECTION not in collections:
                state.qdrant_client.create_collection(
                    collection_name=settings.QDRANT_COLLECTION,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
                )
                logger.info(f"Collection created: {settings.QDRANT_COLLECTION}")
            state.vector_store = QdrantVectorStore(
                client=state.qdrant_client,
                collection_name=settings.QDRANT_COLLECTION,
                embedding=state.embeddings,
            )
            logger.info(f"VectorStore ready: {settings.QDRANT_COLLECTION}")
        except Exception as e:
            logger.error(f"VectorStore failed: {e}")

    # 4. LLM
    try:
        state.llm = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=settings.AGENT_TEMPERATURE,
        )
        logger.info(f"LLM ready: {settings.OLLAMA_MODEL}")
    except Exception as e:
        logger.error(f"LLM failed: {e}")

    # 5. Output dir
    Path(settings.GENERATED_CODE_DIR).mkdir(exist_ok=True)

    elapsed = time.perf_counter() - t0
    state.is_ready = state.llm is not None
    logger.info(f"Startup complete in {elapsed:.2f}s — ready={state.is_ready}")

    yield

    logger.info("Shutting down...")
    if state.qdrant_client:
        state.qdrant_client.close()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — RAG + FILE HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _rag_search(query: str, k: int = 4) -> str:
    if not state.vector_store:
        return ""
    try:
        docs = state.vector_store.similarity_search(query, k=k)
        if not docs:
            return ""
        chunks = []
        for doc in docs:
            m = doc.metadata
            chunks.append(
                f"File: {m.get('file_path', 'unknown')} "
                f"(lines {m.get('start_line', '?')}–{m.get('end_line', '?')})\n"
                f"{doc.page_content[:600]}"
            )
        return "\n\n---\n\n".join(chunks)
    except Exception as e:
        logger.warning(f"RAG search failed: {e}")
        return ""

def _write_file(filename: str, code: str) -> str:
    try:
        safe_name = Path(filename).name
        out_path = Path(settings.GENERATED_CODE_DIR) / safe_name
        out_path.write_text(code, encoding="utf-8")
        logger.info(f"Wrote {out_path} ({len(code)} chars)")
        return str(out_path)
    except Exception as e:
        logger.error(f"write_file failed: {e}")
        return ""

def _get_storage_client() -> storage.Client:
    """Returns a Google Cloud Storage client, using injected credentials in production."""
    creds_json_str = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if creds_json_str:
        creds_info = json.loads(creds_json_str)
        credentials = service_account.Credentials.from_service_account_info(creds_info)
        return storage.Client(credentials=credentials)
    return storage.Client()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — CHAIN BUILDER
# ══════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are MonolithMapper, an expert AI assistant specializing \
in legacy codebase analysis and modernization.

You have been provided with relevant code context retrieved from the codebase \
via semantic search. Use this context to give grounded, accurate answers. \
Always cite the file path and line numbers when referencing specific code.

If the context is empty, say so clearly rather than guessing.

Retrieved codebase context:
{context}"""

def _build_chain() -> RunnableWithMessageHistory:
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ])

    chain = prompt | state.llm

    def get_history(session_id: str) -> ChatMessageHistory:
        if session_id not in state.session_histories:
            state.session_histories[session_id] = ChatMessageHistory()
        return state.session_histories[session_id]

    return RunnableWithMessageHistory(
        chain,
        get_history,
        input_messages_key="input",
        history_messages_key="history",
    )

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — PYDANTIC SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3)
    full_name: str
    email: str
    password: str = Field(..., min_length=6)

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    write_to_file: Optional[str] = Field(None)

class ChatResponse(BaseModel):
    reply: str
    session_id: str
    context_used: bool
    saved_to: Optional[str]
    latency_ms: int

class IndexRequest(BaseModel):
    repo_path: str
    force_reindex: bool = False

class IndexResponse(BaseModel):
    status: str
    node_count: int
    message: str

class HealthResponse(BaseModel):
    status: str
    qdrant: bool
    llm: bool
    vector_store: bool
    active_sessions: int
    version: str = "0.1.0"

class SessionResponse(BaseModel):
    session_id: str
    message: str

class HistoryMessage(BaseModel):
    role: str
    content: str

class HistoryResponse(BaseModel):
    session_id: str
    messages: list[HistoryMessage]

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — APP + MIDDLEWARE
# ══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="MonolithMapper API",
    description="AI-powered legacy codebase analysis and modernization engine. Now secured.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 8 — ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/", tags=["System"])
async def root():
    return {"name": "MonolithMapper API", "version": "0.1.0", "docs": "/docs"}

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health():
    qdrant_ok = False
    if state.qdrant_client:
        try:
            state.qdrant_client.get_collections()
            qdrant_ok = True
        except Exception:
            pass
    return HealthResponse(
        status="ready" if state.is_ready else "degraded",
        qdrant=qdrant_ok,
        llm=state.llm is not None,
        vector_store=state.vector_store is not None,
        active_sessions=len(state.session_histories),
    )

# --- LOGIN ENDPOINT ---
@app.post("/login", tags=["Authentication"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Validates user credentials and hands out a JWT Token"""
    user = fake_users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
        
    access_token = create_access_token(
        data={"sub": user["username"]}, 
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/signup", tags=["Authentication"])
async def sign_up(user_data: UserCreate):
    """Registers a brand new user into the database."""
    if user_data.username in fake_users_db:
        raise HTTPException(status_code=400, detail="Username is already taken")
    
    hashed_password = pwd_context.hash(user_data.password)
    
    fake_users_db[user_data.username] = {
        "username": user_data.username,
        "full_name": user_data.full_name,
        "email": user_data.email,
        "hashed_password": hashed_password,
        "disabled": False,
    }
    
    logger.info(f"New user registered: {user_data.username}")
    return {"message": f"Account created for {user_data.username}! You can now log in."}


# --- SECURED ENDPOINTS BELOW ---

@app.post("/session/new", response_model=SessionResponse, tags=["Session"])
async def new_session(current_user: dict = Depends(get_current_user)):
    session_id = str(uuid.uuid4())
    state.session_histories[session_id] = ChatMessageHistory()
    logger.info(f"User {current_user['username']} created a new session: {session_id}")
    return SessionResponse(
        session_id=session_id,
        message="Session created. Send this session_id with every /chat request."
    )

@app.delete("/session/{session_id}", tags=["Session"])
async def clear_session(session_id: str, current_user: dict = Depends(get_current_user)):
    if session_id in state.session_histories:
        del state.session_histories[session_id]
        return {"status": "cleared", "session_id": session_id}
    raise HTTPException(status_code=404, detail="Session not found")

@app.get("/session/{session_id}/history", response_model=HistoryResponse, tags=["Session"])
async def get_history(session_id: str, current_user: dict = Depends(get_current_user)):
    if session_id not in state.session_histories:
        raise HTTPException(status_code=404, detail="Session not found")
    history = state.session_histories[session_id]
    messages = []
    for msg in history.messages:
        if isinstance(msg, HumanMessage):
            messages.append(HistoryMessage(role="human", content=msg.content))
        elif isinstance(msg, AIMessage):
            messages.append(HistoryMessage(role="ai", content=msg.content))
    return HistoryResponse(session_id=session_id, messages=messages)

@app.post("/chat", response_model=ChatResponse, tags=["Agent"])
async def chat(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    if not state.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM not ready. Check /health.",
        )

    logger.info(f"User {current_user['username']} is chatting in session {req.session_id[:8]}...")

    t0 = time.perf_counter()
    context = _rag_search(req.message)
    context_used = bool(context)

    chain = _build_chain()
    callbacks = []
    if LANGFUSE_AVAILABLE:
        try:
            callbacks.append(LangfuseCallback())
        except Exception:
            pass

    try:
        result = await chain.ainvoke(
            {"input": req.message, "context": context or "No relevant code found."},
            config={
                "configurable": {"session_id": req.session_id},
                "callbacks": callbacks,
            },
        )
    except Exception as e:
        logger.error(f"Chain error session={req.session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"LLM error: {e}")

    reply = result.content if hasattr(result, "content") else str(result)
    saved_to = None
    if req.write_to_file:
        saved_to = _write_file(req.write_to_file, reply)

    latency_ms = int((time.perf_counter() - t0) * 1000)
    logger.info(f"[/chat] session={req.session_id[:8]} rag={context_used} latency={latency_ms}ms")

    return ChatResponse(
        reply=reply,
        session_id=req.session_id,
        context_used=context_used,
        saved_to=saved_to,
        latency_ms=latency_ms,
    )

@app.post("/upload", tags=["Repository"])
async def upload_repo_zip(
    file: UploadFile = File(...), 
    current_user: dict = Depends(get_current_user)
):
    """Takes a ZIP file, unzips it securely, and returns the path to the code."""
    
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only .zip files are allowed.")
        
    upload_id = str(uuid.uuid4())[:8]
    user_dir = Path("uploads") / current_user["username"] / upload_id
    user_dir.mkdir(parents=True, exist_ok=True)
    
    zip_path = user_dir / file.filename
    extract_path = user_dir / "extracted_code"
    
    try:
        logger.info(f"Receiving ZIP from {current_user['username']}...")
        with open(zip_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        logger.info(f"Unzipping {file.filename}...")
        shutil.unpack_archive(str(zip_path), str(extract_path))
        
        os.remove(zip_path)
        
        extracted_items = list(extract_path.iterdir())
        final_repo_path = str(extract_path)
        
        if len(extracted_items) == 1 and extracted_items[0].is_dir():
            final_repo_path = str(extracted_items[0])
            
        return {
            "status": "success",
            "message": "Repository uploaded and unzipped successfully.",
            "repo_path": final_repo_path
        }
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process ZIP: {str(e)}")


@app.post("/index", response_model=IndexResponse, tags=["Indexing"])
async def index_repo(req: IndexRequest, current_user: dict = Depends(get_current_user)):
    repo_path = Path(req.repo_path)
    if not repo_path.exists():
        raise HTTPException(status_code=400, detail=f"Path not found: {repo_path}")
    
    if not state.vector_store:
        raise HTTPException(status_code=500, detail="VectorStore is not running.")

    logger.info(f"User {current_user['username']} started indexing {repo_path.name}...")

    try:
        graph_out_path = f"output/{repo_path.name}_graph.json"
        logger.info(f"Running AST extraction on {repo_path}...")
        graph = run_stage1(str(repo_path), graph_out_path)

        logger.info("Enriching nodes with topological context...")
        enricher = GraphEnricher(graph_out_path)

        texts = []
        metadatas = []
        ids = []

        for node_id, node in enricher.nodes.items():
            texts.append(enricher.build_node_context(node_id))
            metadatas.append({
                "node_id": node_id,
                "name": node["name"],
                "kind": node["kind"],
                "file_path": node["file_path"]
            })
            ids.append(node_id)

        logger.info(f"Indexing {len(texts)} chunks into Qdrant server...")
        state.vector_store.add_texts(texts=texts, metadatas=metadatas, ids=ids)

        return IndexResponse(
            status="ok",
            node_count=len(texts),
            message=f"Successfully extracted, enriched, and indexed {len(texts)} nodes from {repo_path.name}.",
        )
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Indexing failed: {e}")


@app.post("/generate-upload-url", tags=["Uploads"])
async def generate_upload_url(
    filename: str, 
    current_user: dict = Depends(get_current_user)
):
    """Step 1: Gives the frontend a secure URL to upload the file directly to Google."""
    
    BUCKET_NAME = "monolith-mapper-uploads-krishna" 
    blob_name = f"uploads/{current_user['username']}/{filename}"
    
    try:
        storage_client = _get_storage_client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(blob_name)
        
        url = blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(minutes=15),
            method="PUT",
            content_type="application/zip"
        )
        
        return {
            "upload_url": url,
            "bucket_path": blob_name
        }
    except Exception as e:
        logger.error(f"Failed to generate URL: {e}")
        raise HTTPException(status_code=500, detail="Could not generate upload URL.")


@app.post("/process-bucket-upload", tags=["Uploads"])
async def process_bucket_upload(
    bucket_path: str,
    current_user: dict = Depends(get_current_user)
):
    """Step 3: Downloads the file from the bucket to the server and unzips it."""
    
    if current_user["username"] not in bucket_path:
        raise HTTPException(status_code=403, detail="Unauthorized path.")

    BUCKET_NAME = "monolith-mapper-uploads-krishna"
    
    try:
        storage_client = _get_storage_client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(bucket_path)
        
        local_dir = Path("uploads") / current_user["username"] / "temp_download"
        local_dir.mkdir(parents=True, exist_ok=True)
        local_zip_path = local_dir / "repo.zip"
        extract_path = local_dir / "extracted_code"
        
        blob.download_to_filename(local_zip_path)
        
        shutil.unpack_archive(str(local_zip_path), str(extract_path))
        
        extracted_items = list(extract_path.iterdir())
        final_repo_path = str(extract_path)
        if len(extracted_items) == 1 and extracted_items[0].is_dir():
            final_repo_path = str(extracted_items[0])
            
        blob.delete()
        
        return {
            "status": "success",
            "message": "Downloaded from bucket and unzipped.",
            "repo_path": final_repo_path 
        }
        
    except Exception as e:
        logger.error(f"Failed to process bucket file: {e}")
        raise HTTPException(status_code=500, detail="Failed to process cloud file.")