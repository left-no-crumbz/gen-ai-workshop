import streamlit as st
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ["GEMINI_API_KEY"]

client = genai.Client(api_key=API_KEY)

st.title("From RAGs to Responses: Code Your Own AI Study Buddy")

response = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    contents=["Explain what is Retrieval Augmented Generation (RAG) in simple terms."]
)

st.write(response.text)

# If you want a stream of data similar to how ChatGPT works, uncomment the following lines
# response = client.models.generate_content_stream(
#     model="gemini-2.5-flash-lite",
#     contents=["Explain what is Retrieval Augmented Generation (RAG) in simple terms."]
# )
# st.write_stream(chunk.text for chunk in response)