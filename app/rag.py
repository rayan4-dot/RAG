import os
import time
import json
from fastapi import UploadFile
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from tempfile import NamedTemporaryFile
from langchain_core.globals import set_llm_cache
from langchain_core.caches import InMemoryCache
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever, ContextualCompressionRetriever
from langchain_community.document_compressors.flashrank_rerank import FlashrankRerank
from langchain_core.documents import Document

CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")

# Enable Caching Layer
set_llm_cache(InMemoryCache())

_embeddings = None
_vector_store = None
_bm25_retriever = None

def get_vector_store():
    global _embeddings, _vector_store
    if _vector_store is None:
        _embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        _vector_store = Chroma(
            collection_name="rag_collection",
            embedding_function=_embeddings,
            persist_directory=CHROMA_PERSIST_DIRECTORY
        )
    return _vector_store

def get_bm25_retriever():
    global _bm25_retriever
    if _bm25_retriever is None:
        vs = get_vector_store()
        try:
            collection = vs.get()
            docs = collection.get('documents', [])
            metadatas = collection.get('metadatas', [])
            if docs:
                langchain_docs = [Document(page_content=d, metadata=m) for d, m in zip(docs, metadatas)]
                _bm25_retriever = BM25Retriever.from_documents(langchain_docs)
            else:
                _bm25_retriever = None
        except Exception:
            _bm25_retriever = None
    return _bm25_retriever

def update_bm25_retriever():
    global _bm25_retriever
    vs = get_vector_store()
    try:
        collection = vs.get()
        docs = collection.get('documents', [])
        metadatas = collection.get('metadatas', [])
        if docs:
            langchain_docs = [Document(page_content=d, metadata=m) for d, m in zip(docs, metadatas)]
            _bm25_retriever = BM25Retriever.from_documents(langchain_docs)
    except Exception:
        pass

def get_query_type_instructions(query: str) -> str:
    query_lower = query.lower()
    
    temporal_keywords = ["when", "timeline", "order", "after", "before", "sequence", "chronological", "dates"]
    contradiction_keywords = ["conflict", "oppose", "contradict", "disagree", "fake", "lying", "lie", "true", "vs", "versus", "differ"]
    
    if any(keyword in query_lower for keyword in contradiction_keywords):
        return "Strictly apply contradiction handling format:\n- List Conflicting Evidence first\n- Attribute each to a source\n- Give a Final Conclusion assessing the discrepancy."
    
    if any(keyword in query_lower for keyword in temporal_keywords):
        return "Focus on timeline reconstruction: Order all events strictly chronologically based on timestamps or logical sequence."
        
    return "Focus on providing a precise, factual summary."

def get_retrieval_chain(query: str):
    # Use Flash for fast latency
    llm = ChatGoogleGenerativeAI(model="models/gemini-1.5-flash-latest", temperature=0)
    
    query_type_instructions = get_query_type_instructions(query)
    
    system_prompt_text = (
        "You are an advanced analyst for question-answering tasks.\n"
        "Use the following provided context chunks to answer the user's question.\n"
        "Instructions:\n"
        "- Attribute information directly to the provided [Source: X] tags.\n"
        f"{query_type_instructions}\n"
        "If the information is not in the context, explicitly state you don't know.\n"
        "\nContext:\n{context}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt_text),
        ("human", "{input}"),
    ])

    document_prompt = PromptTemplate(
        input_variables=["page_content", "source", "page"],
        template="[Source: {source} (Page {page})]\n{page_content}"
    )

    question_answer_chain = create_stuff_documents_chain(
        llm, prompt, document_prompt=document_prompt, document_variable_name="context"
    )

    vs = get_vector_store()
    # Configure hybrid retrieval pool sizes (20 each, allowing parallel ensemble fetch)
    vector_retriever = vs.as_retriever(search_kwargs={"k": 20})
    bm25 = get_bm25_retriever()
    
    if bm25:
        bm25.k = 20
        ensemble_retriever = EnsembleRetriever(
            retrievers=[bm25, vector_retriever], weights=[0.4, 0.6]
        )
        base_retriever = ensemble_retriever
    else:
        base_retriever = vector_retriever

    # Configure the Reranker (Top 20 compressed to Top 5)
    compressor = FlashrankRerank(top_n=5)
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor, base_retriever=base_retriever
    )

    return create_retrieval_chain(compression_retriever, question_answer_chain)

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
            update_bm25_retriever()
            
        return len(chunks)
    finally:
        os.remove(tmp_path)

import json

async def stream_query_rag(query: str):
    """
    Asynchronously streams the RAG response chunk by chunk.
    Yields JSON strings containing either context (first) or answer chunks.
    """
    start_time = time.time()
    retrieval_chain = get_retrieval_chain(query)
    
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
            yield f"data: {json.dumps({'type': 'sources', 'data': list(set(sources))})}\n\n"
            yield f"data: {json.dumps({'type': 'metrics', 'data': {'retrieval_latency': retrieval_latency}})}\n\n"
        
        if "answer" in chunk:
            yield f"data: {json.dumps({'type': 'content', 'data': chunk['answer']})}\n\n"
            
    total_latency = round((time.time() - start_time) * 1000, 2)
    yield f"data: {json.dumps({'type': 'metrics', 'data': {'total_latency': total_latency}})}\n\n"
    yield "data: [DONE]\n\n"

async def query_rag(query: str) -> dict:
    retrieval_chain = get_retrieval_chain(query)
    response = await retrieval_chain.ainvoke({"input": query})
    answer = response.get("answer")
    
    sources = []
    if "context" in response:
        for doc in response["context"]:
            source_file = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", "Unknown")
            sources.append(f"{source_file} (Page {page})")
            
    unique_sources = list(set(sources))
    return {"answer": answer, "source_documents": unique_sources}
