# pylint: disable=C0114

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

MODEL = os.environ.get("GOOGLE_MODEL", "gemini-2.5-flash")
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
LLM = ChatGoogleGenerativeAI(model=MODEL)
