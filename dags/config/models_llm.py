from dotenv import load_dotenv
from llama_index.llms.ollama import Ollama
from llama_index.core import Settings
import openai
from llama_index.llms.gemini import Gemini
from llama_index.llms.openai import OpenAI
load_dotenv()
import os

# API_KEY_GOOGLE_GENIMI = os.getenv("API_KEY_GOOGLE_GENIMI")
API_KEY_OPENAI = os.getenv("API_KEY_OPENAI")

llm_qwen25_3b = Ollama(model="qwen2.5:3b", request_timeout=1000.0)
llm_deepseek_r1_1b = Ollama(model="deepseek-r1:1.5b", request_timeout=200.0)

# llm_openai = OpenAI(model="gpt-4o", api_key=API_KEY_OPENAI)
# llm_gemini25_pro = Gemini(model="models/gemini-2.0-flash", api_key=API_KEY_GOOGLE_GENIMI)

llm_gpt4o = OpenAI(model="gpt-4o", api_key=API_KEY_OPENAI)
