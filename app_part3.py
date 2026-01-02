import streamlit as st
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
import chromadb
import chromadb.utils.embedding_functions as embedding_functions
import uuid
from typing import Iterable
from PyPDF2 import PdfReader

class GeminiEmbeddingFunction(embedding_functions.EmbeddingFunction):
    def __init__(self, client: genai.Client, model_name: str = "gemini-embedding-001"):
        self._client = client
        self._model_name = model_name

    def __call__(self, texts: Iterable[str]) -> list[list[float]]:
        if isinstance(texts, str):
            texts = [texts]
        embeddings: list[list[float]] = []
        for text in texts:
            response = self._client.models.embed_content(
                model=self._model_name,
                contents=text,
                config=types.EmbedContentConfig(task_type="QUESTION_ANSWERING")
            )
            embeddings.append(response.embeddings[0].values)
        return embeddings

# This function extracts text from a PDF and saves it into our database
def upsert_pdf(file):
    reader = PdfReader(file)
    # Loop through every page in the PDF
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if not text.strip():  # Skip empty pages
            continue
        # Create a unique ID for this specific page
        doc_id = f"{file.name}-{page_num}-{uuid.uuid4().hex}"
        # Save the text and its source information into the database
        chroma_collection.upsert(
            ids=[doc_id],
            documents=[text],
            metadatas=[{"source": file.name, "page": page_num + 1}]
        )


load_dotenv()

API_KEY = os.environ["GEMINI_API_KEY"]
TOP_K = 4  # Number of relevant text snippets to retrieve from the database

# Initialize the Gemini AI client
client = genai.Client(api_key=API_KEY)

# Set up our custom embedding function using Gemini
embedding_fn = GeminiEmbeddingFunction(client)

# Initialize ChromaDB (it runs in-memory by default here)
chromadb_client = chromadb.Client()

# Create or open a 'collection' (like a table in a database) for our study buddy
chroma_collection = chromadb_client.get_or_create_collection(
    name="study_buddy_collection",
    embedding_function=embedding_fn,
)

# --- USER INTERFACE (Streamlit) ---
st.title("From RAGs to Responses: Code Your Own AI Study Buddy")

# Set up chat history so our app remembers what was said
chat_history: list[dict[str, str]] = st.session_state.setdefault("chat_history", [])
messages = st.container(height=600)  # Box to display the conversation

# Display all messages from the current session
for past_message in chat_history:
    messages.chat_message(past_message["role"]).write(past_message["content"])

# Create a chat input box that also accepts PDF files
user_input = st.chat_input("Ask a question about the PDF", accept_file="multiple", file_type=["pdf"])

# If the user sends a message or uploads files
if user_input:
    user_question = user_input.text
    uploaded_files = user_input.files

    # Save and show the user's question
    chat_history.append({"role": "user", "content": user_question})
    messages.chat_message("user").write(user_question)

    # STEP 1: Process any newly uploaded files
    for file in uploaded_files:
        messages.chat_message("ai").write("Uploading file:" + file.name)
        upsert_pdf(file)

    # STEP 2: Retrieval - Search the database for text snippets related to the user's question
    query_result = chroma_collection.query(
        query_texts=[user_question],
        n_results=TOP_K,
    )

    print(query_result)  # Helpful for debugging in the terminal

    # STEP 3: Augmentation - Extract the found text chunks and their sources
    retrieved_documents = query_result.get("documents", [[]])[0]
    retrieved_metadatas = query_result.get("metadatas", [[]])[0]

    # Combine the source info and the text into a readable block
    retrieved_chunks = [
        f"[{meta['source']} p.{meta['page']}] {doc}"
        for doc, meta in zip(retrieved_documents, retrieved_metadatas)
    ]

    context_block = "\n\n".join(retrieved_chunks) if retrieved_chunks else "No relevant context found."

    # STEP 4: Generation - Ask Gemini to answer the question using ONLY the provided context
    SYSTEM_PROMPT = """You are a study buddy. Use only the provided context to answer. If information is missing, say you don't know."""

    # Create the prompt combining context and the actual question
    user_prompt = (
        f"Context:\n{context_block}\n\nQuestion:\n{user_question}"
    )

    contents = [
        types.Content(
            role="user",
            parts=[types.Part(text=user_prompt)],
        )
    ]

    # Stream the response back from the AI for a "typing" effect
    response = client.models.generate_content_stream(
        model="gemini-2.5-flash-lite",
        contents=contents,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
    )

    # Prepare the chat interface to show the AI's response as it's generated
    assistant_message = messages.chat_message("ai")
    assistant_placeholder = assistant_message.empty()
    full_response = []
    latest_text = ""

    # Loop through chunks of text as they arrive from the AI
    for chunk in response:
        chunk_text = getattr(chunk, "text", "")
        if not chunk_text:
            continue
        full_response.append(chunk_text)
        latest_text = "\n".join(full_response)
        assistant_placeholder.write(latest_text)

    chat_history.append({"role": "ai", "content": latest_text})