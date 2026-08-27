import chromadb
# import google.generativeai as genai # <-- Đã tắt Google
import ollama  # <-- Thêm thư viện Ollama
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import settings
import uuid
import os

# genai.configure(api_key=settings.GOOGLE_API_KEY) # <-- Không cần cấu hình key nữa

chroma_client = chromadb.PersistentClient(path="chroma_db")

# LƯU Ý: Đổi tên collection để tránh xung đột dimension với vector cũ của Google
# Google text-embedding-004 (768 dims) vs BGE-M3 (1024 dims)
collection = chroma_client.get_or_create_collection(name="lecture_knowledge_base_local", metadata={"hnsw:space": "cosine"})

def get_embedding(text: str):
    """
    Gọi Local Ollama (BGE-M3) để biến Text -> Vector
    """
    try:
        # Sử dụng model bge-m3 (đã pull về máy qua lệnh: ollama pull bge-m3)
        result = ollama.embeddings(
            model="bge-m3", 
            prompt=text
        )
        return result['embedding']
    except Exception as e:
        print(f"Lỗi Embedding Local: {e}")
        return None

def process_and_store_document(full_text: str, filename: str):
    """
    Quy trình: Cắt nhỏ -> Vector hóa -> Lưu vào DB
    Giữ nguyên logic cũ.
    """
    print(f"--> [RAG Local] Bắt đầu xử lý file: {filename}")
    
    # 1. Chunking (Cắt nhỏ văn bản)
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_text(full_text)
    
    print(f"--> [RAG Local] Đã chia thành {len(chunks)} đoạn nhỏ. Đang tạo Vector trên GPU MX330...")

    # 2. Embedding & Saving (Lưu theo batch)
    ids = []
    embeddings = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        vector = get_embedding(chunk)
        if vector:
            ids.append(f"{filename}_{i}")          
            embeddings.append(vector)              
            documents.append(chunk)                
            metadatas.append({"source": filename}) 

    if ids:
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        print(f"--> [RAG Local] Đã lưu {len(ids)} vector vào ChromaDB thành công!")
        return len(ids)
    else:
        print("--> [RAG Local] Không tạo được vector nào.")
        return 0

def query_knowledge_base(query_text: str, n_results=10, source_file: str = None):
    """
    Hàm tìm kiếm có hỗ trợ lọc theo file nguồn.
    """
    # 1. Vector hóa câu hỏi (Dùng model Local luôn)
    try:
        query_instruction = "Represent this sentence for searching relevant passages: "
        query_vector = ollama.embeddings(
            model="bge-m3", 
            prompt=query_instruction + query_text
        )['embedding']
        # query_vector = ollama.embeddings(
        #     model="bge-m3",
        #     prompt=query_text
        # )['embedding']
    except Exception as e:
        print(f"Lỗi khi vector hóa câu query: {e}")
        return []

    # 2. Chuẩn bị tham số Query
    query_params = {
        "query_embeddings": [query_vector],
        "n_results": n_results,
        "include": ["documents", "distances"]
    }

    if source_file:
        filename_only = os.path.basename(source_file)
        query_params["where"] = {"source": filename_only}

    # 3. Tìm kiếm
    results = collection.query(**query_params)
    
    if not results['documents'] or not results['documents'][0]:
        return []

    # Lưu ý: Distance của Chroma mặc định là L2 (Euclidean).
    # Với BGE-M3, vector thường được chuẩn hóa nên Cosine distance hiệu quả hơn, 
    # nhưng L2 vẫn hoạt động tốt. Bạn có thể cần chỉnh THRESHOLD nếu thấy kết quả bị lọc hết.
    THRESHOLD = 0.55
    filtered_docs = []
    
    for doc, dist in zip(results['documents'][0], results['distances'][0]):
        #print(f"--- [DEBUG RAG Local] Distance: {dist:.4f} | Content: {doc[:50]}...")
        
        if dist < THRESHOLD:
            filtered_docs.append(doc)
            print(f"--- [DEBUG RAG Local] Distance: {dist:.4f} | Content: {doc[:50]}...")
        else:
            print(f"    -> BỊ LOẠI do khoảng cách quá lớn (> {THRESHOLD})")
    return filtered_docs

def get_full_file_content(filename: str):
    """
    Lấy toàn bộ nội dung của một file cụ thể.
    Giữ nguyên logic.
    """
    results = collection.get(
        where={"source": filename},
        include=["documents"]
    )
    
    if not results['documents']:
        return ""
        
    full_text = "\n\n".join(results['documents'])
    return full_text

# import chromadb
# import google.generativeai as genai
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from app.config import settings
# import uuid
# import os

# genai.configure(api_key=settings.GOOGLE_API_KEY)

# chroma_client = chromadb.PersistentClient(path="chroma_db")

# collection = chroma_client.get_or_create_collection(name="lecture_knowledge_base")

# def get_embedding(text: str):
#     """
#     Gọi Gemini để biến Text -> Vector
#     """
#     try:
#         result = genai.embed_content(
#             model="models/text-embedding-004",
#             content=text,
#             task_type="retrieval_document"
#         )
#         return result['embedding']
#     except Exception as e:
#         print(f"Lỗi Embedding: {e}")
#         return None

# def process_and_store_document(full_text: str, filename: str):
#     """
#     Quy trình: Cắt nhỏ -> Vector hóa -> Lưu vào DB
#     """
#     print(f"--> [RAG] Bắt đầu xử lý file: {filename}")
    
#     # 1. Chunking (Cắt nhỏ văn bản)
#     # chunk_size=1000: Mỗi đoạn khoảng 1000 ký tự
#     # chunk_overlap=200: Các đoạn gối đầu lên nhau 200 ký tự (không mất ngữ cảnh ở vết cắt)
#     splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
#     chunks = splitter.split_text(full_text)
    
#     print(f"--> [RAG] Đã chia thành {len(chunks)} đoạn nhỏ. Đang tạo Vector...")

#     # 2. Embedding & Saving (Lưu theo batch)
#     ids = []
#     embeddings = []
#     documents = []
#     metadatas = []

#     for i, chunk in enumerate(chunks):
#         vector = get_embedding(chunk)
#         if vector:
#             ids.append(f"{filename}_{i}")          
#             embeddings.append(vector)              
#             documents.append(chunk)                
#             metadatas.append({"source": filename}) 

#     if ids:
#         collection.add(
#             ids=ids,
#             embeddings=embeddings,
#             documents=documents,
#             metadatas=metadatas
#         )
#         print(f"--> [RAG] Đã lưu {len(ids)} vector vào ChromaDB thành công!")
#         return len(ids)
#     else:
#         print("--> [RAG] Không tạo được vector nào.")
#         return 0

# def query_knowledge_base(query_text: str, n_results=3, source_file: str = None):
#     """
#     Hàm tìm kiếm có hỗ trợ lọc theo file nguồn.
#     """
#     # 1. Vector hóa câu hỏi
#     query_vector = genai.embed_content(
#         model="models/text-embedding-004",
#         content=query_text,
#         task_type="retrieval_query"
#     )['embedding']

#     # 2. Chuẩn bị tham số Query
#     query_params = {
#         "query_embeddings": [query_vector],
#         "n_results": n_results,
#         "include": ["documents", "distances"]
#     }

#     if source_file:
#         filename_only = os.path.basename(source_file)
#         query_params["where"] = {"source": filename_only}

#     # 3. Tìm kiếm
#     results = collection.query(**query_params)
    
#     if not results['documents'] or not results['documents'][0]:
#         return []

#     THRESHOLD = 1.5
#     filtered_docs = []
    
#     for doc, dist in zip(results['documents'][0], results['distances'][0]):
#         print(f"--- [DEBUG RAG] Distance: {dist:.4f} | Content: {doc[:50]}...")
        
#         if dist < THRESHOLD:
#             filtered_docs.append(doc)
#         else:
#             print(f"    -> BỊ LOẠI do khoảng cách quá lớn (> {THRESHOLD})")
#     return filtered_docs

# def get_full_file_content(filename: str):
#     """
#     Lấy toàn bộ nội dung của một file cụ thể.
#     """
#     results = collection.get(
#         where={"source": filename},
#         include=["documents"]
#     )
    
#     if not results['documents']:
#         return ""
        
#     full_text = "\n\n".join(results['documents'])
#     return full_text