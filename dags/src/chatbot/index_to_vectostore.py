import os
from dotenv import load_dotenv
from llama_parse import LlamaParse
from llama_index.core import (
    VectorStoreIndex, 
    SimpleDirectoryReader,
    StorageContext,
)
import logging
from llama_index.vector_stores.postgres import PGVectorStore
from ...config.vectostore import embedd_model, db_name, url  # Sử dụng url từ config
from sqlalchemy import make_url

logging.basicConfig(level=logging.INFO)

def load_data_vectostore(table_name, data_path):
    current_dir = r'D:\project_NCKH\oral-exam-chatbot-'
    env_path = os.path.join(current_dir, '.env')
    load_dotenv(env_path)

    # Parse connection URL từ config
    connection_url = make_url(url)
    
    # Khởi tạo parser
    parser = LlamaParse(
        result_type="markdown",
        async_mode=True,
        encoding="utf-8",
        language="vi",
        api_key=os.getenv("LLAMA_CLOUD_API_KEY")
    )
    file_extractor = {".pdf": parser, ".docx": parser}

    # Đọc tài liệu
    documents = SimpleDirectoryReader(
        input_files=data_path,
        file_extractor=file_extractor
    ).load_data()

    # Khởi tạo vector store
    vector_store = PGVectorStore.from_params(
        database=db_name,
        host=connection_url.host,
        password=connection_url.password,
        port=connection_url.port,
        user=connection_url.username,
        table_name=table_name,
        embed_dim=1024,
        hnsw_kwargs={
            "hnsw_m": 16,
            "hnsw_ef_construction": 64,
            "hnsw_ef_search": 40,
            "hnsw_dist_method": "vector_cosine_ops",
        }
    )

    # Tạo index
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_documents(
        documents,
        embed_model=embedd_model,
        storage_context=storage_context,
        show_progress=True
    )

    return table_name

def load_indexs(vectorstore_table):
    try:
        logging.info(f"Khởi tạo vector store cho bảng: {vectorstore_table}")
        
        # Parse connection URL từ config
        connection_url = make_url(url)
        
        vector_store = PGVectorStore.from_params(
            database=db_name,
            host=connection_url.host,
            password=connection_url.password,
            port=connection_url.port,
            user=connection_url.username,
            table_name=vectorstore_table,
            embed_dim=1024,
            hybrid_search=False,
            hnsw_kwargs={
                "hnsw_m": 16,
                "hnsw_ef_construction": 64,
                "hnsw_ef_search": 40,
                "hnsw_dist_method": "vector_cosine_ops",
            },
        )
        
        index = VectorStoreIndex.from_vector_store(
            embed_model=embedd_model,
            vector_store=vector_store
        )
        return index
    except Exception as e:
        logging.error(f"Lỗi khi khởi tạo index: {str(e)}")
        raise