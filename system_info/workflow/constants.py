import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

PRO_MODEL = os.getenv('GEMINI_PRO_MODEL', "gemini-3.0-pro-preview")
FLASH_MODEL = os.getenv('GEMINI_FLASH_MODEL', "gemini-2.5-flash")

pro_llm = ChatGoogleGenerativeAI(model=PRO_MODEL, temperature=0)
flash_llm = ChatGoogleGenerativeAI(model=FLASH_MODEL, temperature=0)

if os.getenv("INTEGRATION_ROOT_PATH"):
    INTEGRATION_ROOT_PATH = os.getenv("INTEGRATION_ROOT_PATH")
else:
    raise ValueError("INTEGRATION_ROOT_PATH is not set")