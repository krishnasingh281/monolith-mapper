"""
MonolithMapper — Stage 4: The Auto-Coder Agent
Upgrades the LLM with a 'write_file' tool so it can save code to your disk.
"""

import os
import sys
import warnings
from qdrant_client import QdrantClient
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langfuse.langchain import CallbackHandler
from langchain_core.tools import tool
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent

warnings.filterwarnings("ignore")

# --- LANGFUSE SETUP ---
# Copy your keys from chat.py!
os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-79f87666-7fc1-479c-b7b1-0308cb30f5ea"   # Paste your public key here
os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-d45d14e7-1790-4942-9d12-cfb8417fd1b0"   # Paste your secret key here
os.environ["LANGFUSE_HOST"] = "https://us.cloud.langfuse.com"
langfuse_handler = CallbackHandler()

# ==========================================
# 1. DEFINE THE AI'S TOOLBELT
# ==========================================
@tool
def write_file(file_name: str, content: str) -> str:
    """
    Saves generated code to a local file. 
    Use this strictly when the user asks to save, create, or write a file.
    """
    try:
        # Save files in a dedicated folder so we don't mess up your main project
        os.makedirs("generated_code", exist_ok=True)
        path = os.path.join("generated_code", file_name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Success! I have saved the file to {path}"
    except Exception as e:
        return f"System Error saving file: {str(e)}"

# We can give the AI multiple tools later, but right now it just gets one.
tools = [write_file]

# ==========================================
# 2. SETUP THE BRAIN & MEMORY
# ==========================================
print("Connecting to Digital Brain (Qdrant)...")
db_client = QdrantClient(path="qdrant_db")
db_client.set_model("BAAI/bge-small-en-v1.5")

print("Waking up Agent (Ollama - Llama3)...")
# Temperature 0 makes the AI highly logical, which is better for tool-calling
llm = ChatOllama(model="llama3.1", temperature=0)

# ==========================================
# 3. BUILD THE AGENT PROMPT
# ==========================================
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are MonolithMapper, an expert AI software architect. 
    Answer questions using the codebase context provided below.
    
    CRITICAL TOOL INSTRUCTIONS:
    1. ONLY use the `write_file` tool if the user EXPLICITLY asks you to "save", "write", or "create" a file.
    2. If the user is just asking for an explanation, analysis, or trace, DO NOT use any tools. Just answer directly in the chat.
    3. When using the `write_file` tool, the `content` parameter MUST be a plain STRING. Never pass a dictionary, list, or JSON object as the content.
    4. Do NOT output any conversational text before calling the tool. Just trigger it directly.
    
    Codebase Context:
    {context}"""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"), 
])

# Bind the tools to Llama3 and create the Agent execution loop
agent = create_tool_calling_agent(llm, tools, prompt)
# verbose=True lets us watch the AI's internal thought process in the terminal
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

chat_history = []

print("\n" + "="*55)
print("🤖 MonolithMapper Agent Online (Auto-Coder Active)!")
print("Type 'exit' to quit.")
print("="*55 + "\n")

# ==========================================
# 4. THE CHAT LOOP
# ==========================================
while True:
    try:
        user_input = input("\nYou: ")
        if user_input.lower() in ['exit', 'quit']:
            db_client.close()
            break
            
        # Retrieve context from Qdrant
        results = db_client.query(
            collection_name="monolith_nodes",
            query_text=user_input,
            limit=3
        )
        
        context_chunks = [f"--- {h.metadata['name']} ---\n{h.document}" for h in results]
        formatted_context = "\n\n".join(context_chunks)
        
        print("\nAgent is thinking...")
        
        # Invoke the Agent (with Langfuse tracking attached!)
        response = agent_executor.invoke(
            {
                "context": formatted_context, 
                "chat_history": chat_history, 
                "question": user_input
            },
            config={"callbacks": [langfuse_handler]}
        )
        
        # Save to memory
        chat_history.append(HumanMessage(content=user_input))
        chat_history.append(AIMessage(content=response["output"]))
        if len(chat_history) > 10:
            chat_history = chat_history[-10:]
            
    except KeyboardInterrupt:
        db_client.close()
        sys.exit(0)