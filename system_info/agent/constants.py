# pylint: disable=C0114

import os
from langchain_google_genai import ChatGoogleGenerativeAI


MODEL = os.environ.get("GOOGLE_MODEL", "gemini-2.5-flash")

LLM = ChatGoogleGenerativeAI(model=MODEL)
