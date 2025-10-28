import os
from dotenv import load_dotenv
from llama_index.core.embeddings import resolve_embed_model
import psycopg2
from sqlalchemy import make_url
load_dotenv()

# Nếu cần, lấy API key của LLAMA từ file .env (sử dụng trong các trường hợp cần thiết)
LLAMA_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")

# Đổi tên biến thành embed_model để rõ nghĩa hơn
embedd_model = resolve_embed_model("local:BAAI/bge-m3")
db_name = "vectordb_agentstock"
connection_string = "postgresql://postgres:123456@localhost:5432/vectordb_agentstock"
conn = psycopg2.connect(connection_string)
conn.autocommit = True
url = make_url(connection_string)