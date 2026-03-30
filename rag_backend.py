import os
from langchain.tools.retriever import create_retriever_tool
from dotenv import load_dotenv
from astrapy import DataAPIClient
from langchain import hub
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_astradb import AstraDBVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from doc_loader import load_paths_as_docs
load_dotenv()

ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")
ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
ASTRA_DB_KEYSPACE = os.getenv("ASTRA_DB_KEYSPACE") or None

if not ASTRA_DB_API_ENDPOINT or not ASTRA_DB_APPLICATION_TOKEN:
    raise RuntimeError("Astra DB env vars not set. Check .env / Streamlit secrets.")



def delete_user_docs(user_id: str) -> int:
    client = DataAPIClient(ASTRA_DB_APPLICATION_TOKEN)
    db = client.get_database(api_endpoint=ASTRA_DB_API_ENDPOINT)
    coll = db.get_collection("user_docs")

    result = coll.delete_many({"metadata.user_id": user_id})
    if isinstance(result, dict):
        return result.get("status", {}).get("deletedCount", 0)
    return getattr(result, "deleted_count", 0)

def connect_to_vstore():
    embeddings = OpenAIEmbeddings()
    vstore = AstraDBVectorStore(
        embedding=embeddings,
        collection_name="user_docs",
        api_endpoint=ASTRA_DB_API_ENDPOINT,
        token=ASTRA_DB_APPLICATION_TOKEN,
        namespace=ASTRA_DB_KEYSPACE,
    )
    return vstore

def build_retriever(user_id: str):
    vstore = connect_to_vstore()
 
    retriever = vstore.as_retriever(
        search_kwargs={
            "k": 5,
            "filter": {"user_id": user_id},
        }
    )

    return retriever


def get_prompt():
    try:
        return hub.pull("hwchase17/openai-functions-agent")
    except Exception as e:
        print("hub.pull failed, falling back:", repr(e))
        return ChatPromptTemplate.from_template(
            "Use these documents to answer the question.\n\n{context}\n\nQuestion: {question}"
        )


def rag_answer(question: str, user_id: str = "user123"):
    retriever = build_retriever(user_id)

    docs = retriever.get_relevant_documents(question)
    if not docs:
        return (
            f"You currently have no documents stored for user '{user_id}'. "
            "Please upload a PDF first.",
            [],
        )

    retriever_tool = create_retriever_tool(
        retriever,
        "docs_search",
        "Search for information in the loaded documents. For any questions about the documents, you must use this tool!",
    )

    prompt = get_prompt()  # or hub.pull(...) if you use that
    llm = ChatOpenAI()
    tools = [retriever_tool]
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    result = agent_executor.invoke({"input": question})
    answer = result["output"]

    return answer, docs

def split_documents(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=80,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)

def upload_pdf_to_astra(path: str, user_id: str, display_name: str | None = None) -> int:
    docs = load_paths_as_docs([path])

    for d in docs:
        d.metadata["user_id"] = user_id
        if display_name is not None:
            d.metadata["source"] = display_name
            d.metadata["display_name"] = display_name

    chunks = split_documents(docs)
    if not chunks:
        return 0

    page_counters = {}
    for chunk in chunks:
        page = chunk.metadata.get("page")
        page_counters[page] = page_counters.get(page, 0) + 1
        chunk.metadata["chunk_index"] = page_counters[page]

    source = chunks[0].metadata["source"]

    vstore = connect_to_vstore()
    vstore.delete({"user_id": user_id, "source": source})
    vstore.add_documents(chunks)

    return len(chunks)

def list_user_sources(user_id: str):
    vstore = connect_to_vstore()

    # get all docs for this user (you can limit k if needed)
    docs = vstore.similarity_search(
        query="*",  # dummy query
        k=100,      # or some upper bound
        filter={"user_id": user_id},
    )

    files = {}
    for d in docs:
        meta = d.metadata or {}
        display = meta.get("display_name") or meta.get("source")
        source = meta.get("source")
        if source is None:
            continue
        files[display] = source  # de‑duplicate by source

    return list(files.items())
def delete_user_file(user_id: str, source: str) -> int:
    client = DataAPIClient(ASTRA_DB_APPLICATION_TOKEN)
    db = client.get_database(api_endpoint=ASTRA_DB_API_ENDPOINT)
    coll = db.get_collection("user_docs")

    result = coll.delete_many(
        {"metadata.user_id": user_id, "metadata.source": source}
    )

    if isinstance(result, dict):
        return result.get("status", {}).get("deletedCount", 0)
    return getattr(result, "deleted_count", 0)















