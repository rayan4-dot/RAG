import os
import time
from fastapi import UploadFile
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from tempfile import NamedTemporaryFile

CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")

def get_vector_store():
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    vector_store = Chroma(
        collection_name="rag_collection",
        embedding_function=embeddings,
        persist_directory=CHROMA_PERSIST_DIRECTORY
    )
    return vector_store

def get_retrieval_chain():
    llm = ChatGoogleGenerativeAI(model="models/gemini-flash-latest", temperature=0)
    
    system_prompt = (
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer the question. "
        "If you don't know the answer, say that you don't know. "
        "Use three sentences maximum and keep the answer concise."
        "\n\n"
        "{context}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})
    return create_retrieval_chain(retriever, question_answer_chain)

async def process_and_store_document(file: UploadFile) -> int:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )

    with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        # Read file chunks to handle large files
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        loader = PyPDFLoader(tmp_path)
        docs = loader.load()
        chunks = text_splitter.split_documents(docs)
        
        if chunks:
            # Add metadata to chunks to identify the source file better
            for chunk in chunks:
                chunk.metadata["source"] = file.filename
                
            vector_store = get_vector_store()
            vector_store.add_documents(chunks)
            
        return len(chunks)
    finally:
        os.remove(tmp_path)

async def stream_query_rag(query: str):
    """
    Asynchronously streams the RAG response chunk by chunk.
    Yields JSON strings containing either context (first) or answer chunks.
    """
    start_time = time.time()
    retrieval_chain = get_retrieval_chain()
    
    # We use astream to get chunks as they are generated
    async for chunk in retrieval_chain.astream({"input": query}):
        # LangChain's retrieval chain returns a dict
        if "context" in chunk:
            retrieval_latency = round((time.time() - start_time) * 1000, 2)
            sources = []
            for doc in chunk["context"]:
                source_file = doc.metadata.get("source", "Unknown")
                page = doc.metadata.get("page", "Unknown")
                sources.append(f"{source_file} (Page {page})")
            yield f"data: {{\"type\": \"sources\", \"data\": {list(set(sources))}}}\n\n"
            yield f"data: {{\"type\": \"metrics\", \"data\": {{\"retrieval_latency\": {retrieval_latency}}}}}\n\n"
        
        if "answer" in chunk:
            yield f"data: {{\"type\": \"content\", \"data\": \"{chunk['answer']}\"}}\n\n"
            
    total_latency = round((time.time() - start_time) * 1000, 2)
    yield f"data: {{\"type\": \"metrics\", \"data\": {{\"total_latency\": {total_latency}}}}}\n\n"
    yield "data: [DONE]\n\n"

def query_rag(query: str) -> dict:
    retrieval_chain = get_retrieval_chain()
    response = retrieval_chain.invoke({"input": query})
    answer = response.get("answer")
    
    sources = []
    if "context" in response:
        for doc in response["context"]:
            source_file = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", "Unknown")
            sources.append(f"{source_file} (Page {page})")
            
    unique_sources = list(set(sources))
    return {"answer": answer, "source_documents": unique_sources}
