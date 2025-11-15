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

def upsert_pdf(file):
    reader = PdfReader(file)
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if not text.strip():
            continue
        doc_id = f"{file.name}-{page_num}-{uuid.uuid4().hex}"
        chroma_collection.upsert(
            ids=[doc_id],
            documents=[text],
            metadatas=[{"source": file.name, "page": page_num + 1}]
        )


load_dotenv()

API_KEY = os.environ["GEMINI_API_KEY"]
TOP_K = 4

client = genai.Client(api_key=API_KEY)

embedding_fn = GeminiEmbeddingFunction(client)

chromadb_client = chromadb.Client()

chroma_collection = chromadb_client.get_or_create_collection(
    name="study_buddy_collection",
    embedding_function=embedding_fn,
)

st.title("From RAGs to Responses: Code Your Own AI Study Buddy")

chat_history: list[dict[str, str]] = st.session_state.setdefault("chat_history", [])
messages = st.container(height=600)

for past_message in chat_history:
    messages.chat_message(past_message["role"]).write(past_message["content"])

user_input = st.chat_input("Ask a question about the PDF", accept_file="multiple", file_type=["pdf"])

if user_input:
    user_question = user_input.text
    uploaded_files = user_input.files

    chat_history.append({"role": "user", "content": user_question})
    messages.chat_message("user").write(user_question)

    # Upload the files
    for file in uploaded_files:
        messages.chat_message("ai").write("Uploading file:" + file.name)
        upsert_pdf(file)

    query_result = chroma_collection.query(
        query_texts=[user_question],
        n_results=TOP_K,
    )

    print(query_result)

    retrieved_documents = query_result.get("documents", [[]])[0]
    retrieved_metadatas = query_result.get("metadatas", [[]])[0]

    retrieved_chunks = [
        f"[{meta['source']} p.{meta['page']}] {doc}"
        for doc, meta in zip(retrieved_documents, retrieved_metadatas)
    ]

    context_block = "\n\n".join(retrieved_chunks) if retrieved_chunks else "No relevant context found."

    SYSTEM_PROMPT = """You are a study buddy. Use only the provided context to answer. If information is missing, say you don't know."""

    user_prompt = (
        f"Context:\n{context_block}\n\nQuestion:\n{user_question}"
    )

    contents = [
        types.Content(
            role="user",
            parts=[types.Part(text=user_prompt)],
        )
    ]

    response = client.models.generate_content_stream(model="gemini-2.5-flash-lite", contents=contents, config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT))

    assistant_message = messages.chat_message("ai")
    assistant_placeholder = assistant_message.empty()
    full_response = []
    latest_text = ""

    for chunk in response:
        chunk_text = getattr(chunk, "text", "")
        if not chunk_text:
            continue
        full_response.append(chunk_text)
        latest_text = "\n".join(full_response)
        assistant_placeholder.write(latest_text)

    chat_history.append({"role": "ai", "content": latest_text})