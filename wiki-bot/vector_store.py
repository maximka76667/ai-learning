import os
import shutil
from config import DB_PATH
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from llm import embeddings
from logger import log_node


def reset_vector_store():
    if os.path.exists(DB_PATH):
        print(f"Cleaning up old database at {DB_PATH}...")
        shutil.rmtree(DB_PATH)
        print("Database removed.")


def get_vector_store():
    return Chroma(persist_directory=DB_PATH, embedding_function=embeddings)


def populate_vector_store(documents, reset=False):
    if reset:
        reset_vector_store()

    vector_store = get_vector_store()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)

    vector_store.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=DB_PATH,
    )

    log_node(
        "VECTOR_STORE", {"message": f"Vector store created with {len(chunks)} chunks"}
    )
    return vector_store
