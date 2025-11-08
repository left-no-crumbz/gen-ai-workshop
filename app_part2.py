import streamlit as st
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

st.title("From RAGs to Responses: Code Your Own AI Study Buddy")

messages = st.container(height=600)

user_input = st.chat_input("Ask a question about the PDF", accept_file="multiple", file_type=["pdf"])

if user_input:
    user_question = user_input.text
    uploaded_files = user_input.files

    messages.chat_message("user").write(user_question)

    # Upload the files
    gemini_files = []
    for file in uploaded_files:
        # Create a file config
        upload_config = types.UploadFileConfig(display_name=file.name, mime_type=file.type)

        # Upload the file/s
        messages.chat_message("ai").write("Uploading file:" + file.name)
        gemini_file = client.files.upload(file=file, config=upload_config)
        gemini_files.append(gemini_file)

    # Generate a response
    contents = [user_question] + gemini_files
    response = client.models.generate_content_stream(model="gemini-2.5-flash-lite", contents=contents)
    messages.chat_message("ai").write_stream(chunk.text for chunk in response)