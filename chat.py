"""
MonolithMapper — Stage 3: The LLM Chat Engine (With Memory)
Uses Qdrant for Retrieval, Ollama for Generation, and maintains Conversation History.
"""
import os
from langfuse.langchain import CallbackHandler

# --- LANGFUSE SETUP ---
os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-79f87666-7fc1-479c-b7b1-0308cb30f5ea"   # Paste your public key here
os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-d45d14e7-1790-4942-9d12-cfb8417fd1b0"   # Paste your secret key here
os.environ["LANGFUSE_HOST"] = "https://us.cloud.langfuse.com" # (Or the US host if it gave you one)

# Initialize the tracer
langfuse_handler = CallbackHandler()
# ----------------------
import sys
import warnings
from qdrant_client import QdrantClient
from langchain_ollama import ChatOllama  # <-- Updated import!
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage

warnings.filterwarnings("ignore", category=UserWarning)

# 1. Setup Qdrant (The Retriever)
print("Connecting to Digital Brain (Qdrant)...")
db_client = QdrantClient(path="qdrant_db")
db_client.set_model("BAAI/bge-small-en-v1.5")

# 2. Setup Ollama (The Generator)
print("Waking up local LLM (Ollama - Llama3)...")
llm = ChatOllama(model="llama3")

# 3. Create the Prompt Template (Now with Memory!)
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are MonolithMapper, an expert AI software architect. 
    Answer the user's question based ONLY on the following codebase context:
    
    {context}
    
    Keep your answers concise and reference specific function or class names."""),
    ("placeholder", "{chat_history}"),  # <-- This injects the past conversation
    ("human", "{question}")
])

# 4. Initialize our memory bank
chat_history = []

print("\n" + "="*55)
print("🚀 MonolithMapper Chat Engine Online (Memory Active)!")
print("Type 'exit' to quit.")
print("="*55 + "\n")

while True:
    try:
        user_input = input("\nYou: ")
        if user_input.lower() in ['exit', 'quit']:
            db_client.close()
            break
            
        # --- Step A: Retrieve ---
        results = db_client.query(
            collection_name="monolith_nodes",
            query_text=user_input,
            limit=3
        )
        
        # --- Step B: Augment ---
        context_chunks = []
        for hit in results:
            context_chunks.append(f"--- {hit.metadata['name']} ({hit.metadata['kind']}) ---\n{hit.document}")
        formatted_context = "\n\n".join(context_chunks)
        
        # --- Step C: Generate ---
        chain = prompt | llm
        
        print("\nMonolithMapper: ", end="")
        
        # We need to capture the full response to save it to memory
        full_response = ""
        
        # We pass the Langfuse handler directly into the chain!
        for chunk in chain.stream(
            {
                "context": formatted_context, 
                "chat_history": chat_history, 
                "question": user_input
            },
            config={"callbacks": [langfuse_handler]}
        ):
            print(chunk.content, end="", flush=True)
            full_response += chunk.content
        print("\n")
        
        # --- Step D: Remember ---
        # Save both the user's question and the AI's answer for the next loop
        chat_history.append(HumanMessage(content=user_input))
        chat_history.append(AIMessage(content=full_response))
        
        # Optional: Keep memory from getting too huge (keep last 10 messages)
        if len(chat_history) > 10:
            chat_history = chat_history[-10:]
        
    except KeyboardInterrupt:
        db_client.close()
        print("\nShutting down...")
        sys.exit(0)