import ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import BSHTMLLoader
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from langchain_ollama.chat_models import ChatOllama
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

import logging
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn

from opentelemetry import trace
from traceloop.sdk import Traceloop
from traceloop.sdk.decorators import workflow, task

import weaviate
import weaviate.classes as wvc
from langchain_weaviate.vectorstores import WeaviateVectorStore


# disable traceloop telemetry
os.environ["TRACELOOP_TELEMETRY"] = "false"

def read_token():
    return os.environ.get("API_TOKEN", read_secret("token"))


def read_endpoint():
    return os.environ.get("OTEL_ENDPOINT", read_secret("endpoint"))

def read_secret(secret: str):
    try:
        with open(f"/etc/secrets/{secret}", "r") as f:
            return f.read().rstrip()
    except Exception as e:
        print(f"No {secret} was provided")
        print(e)
        return ""


# Clean up endpoint making sure it is correctly follow the format:
# https://<YOUR_ENV>.live.dynatrace.com/api/v2/otlp
OTEL_ENDPOINT = read_endpoint()
if OTEL_ENDPOINT.endswith("/v1/traces"):
    OTEL_ENDPOINT = OTEL_ENDPOINT[: OTEL_ENDPOINT.find("/v1/traces")]

## Configuration of OLLAMA & Weaviate
OLLAMA_ENDPOINT = os.environ.get("OLLAMA_ENDPOINT", "http://localhost:11434")
WEAVIATE_ENDPOINT = os.environ.get("WEAVIATE_ENDPOINT", "localhost")

# By default we use orca-mini:3b because it's small enough to run easily on codespace
# Make sure if you change this, you need to also change the deployment script
AI_MODEL = os.environ.get("AI_MODEL", "orca-mini:3b")
AI_EMBEDDING_MODEL = os.environ.get("AI_EMBEDDING_MODEL", "orca-mini:3b")
MAX_PROMPT_LENGTH = 50

# Initialise the logger
logging.basicConfig(level=logging.INFO, filename="run.log")
logger = logging.getLogger(__name__)

#################
# CONFIGURE TRACELOOP & OTel

TOKEN = read_token()
headers = {"Authorization": f"Api-Token {TOKEN}"}

# Use the OTel API to instanciate a tracer to generate Spans
otel_tracer = trace.get_tracer("travel-advisor")

# Initialize OpenLLMetry
Traceloop.init(
    app_name="travel-advisor",
    api_endpoint=OTEL_ENDPOINT,
    disable_batch=True, # This is recomended for testing but NOT for production
    headers=headers,
)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def prep_system():
    # Create the embedding and the Weaviate Client
    embeddings = OllamaEmbeddings(model=AI_EMBEDDING_MODEL, base_url=OLLAMA_ENDPOINT)
    weaviate_client = weaviate.connect_to_local(host=WEAVIATE_ENDPOINT)
    # Cleanup the collection containing our documents and recreate it
    weaviate_client.collections.delete("KB")
    weaviate_client.collections.create(
        name = "KB",
        vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_ollama(api_endpoint=OLLAMA_ENDPOINT, model=AI_EMBEDDING_MODEL),
        properties = [
            wvc.config.Property(
                name="text",
                data_type=wvc.config.DataType.TEXT,
            ),
            wvc.config.Property(
                name="source",
                data_type=wvc.config.DataType.TEXT,
            ),
            wvc.config.Property(
                name="title",
                data_type=wvc.config.DataType.TEXT,
            ),
        ],
    )

    # Retrieve the source data
    docs_list = []
    for item in os.listdir(path="destinations"):
        if item.endswith(".html"):
            item_docs_list = BSHTMLLoader(file_path=f"destinations/{item}").load()
            for item in item_docs_list:
                docs_list.append(item)

    # Split Document into tokens
    text_splitter = RecursiveCharacterTextSplitter()
    documents = text_splitter.split_documents(docs_list)

    vector = WeaviateVectorStore.from_documents(
        documents,
        embeddings,
        client=weaviate_client,
        index_name="KB"
    )
    retriever = vector.as_retriever()

    llm = ChatOllama(model=AI_MODEL, base_url=OLLAMA_ENDPOINT)

    prompt = ChatPromptTemplate.from_template(
        """Answer the following question based only on the provided context:
    <context>
    {context}
    </context>
    Question: Give travel advise in a paragraph of max 50 words about {input}                                           
    """
    )
    # Build the RAG Pipeline
    rag_chain = (
            {"context": retriever | format_docs, "input": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
    )

    return rag_chain


############
# Setup the endpoints and LangChain

app = FastAPI()
retrieval_chain = prep_system()


####################################
@app.get("/api/v1/completion")
def submit_completion(framework: str, prompt: str):
    with otel_tracer.start_as_current_span(name="/api/v1/completion") as span:
        if framework == "llm":
            return llm_chat(prompt)
        if framework == "rag":
            return rag_chat(prompt)
        return {"message": "invalid Mode"}


@task(name="ollama_chat")
def llm_chat(prompt: str):
    prompt = f"Give travel advise in a paragraph of max 50 words about {prompt}"
    res = ollama.generate(model=AI_MODEL, prompt=prompt)
    return {"message": res.get("response")}


@workflow(name="travelgenerator")
def rag_chat(prompt: str):
    if prompt:
        logger.info(f"Calling RAG to get the answer to the question: {prompt}...")
        response = retrieval_chain.invoke( prompt, config={})
        return {"message": response}
    else:  # No, or invalid prompt given
        err_msg = f"No prompt provided or prompt too long (over {MAX_PROMPT_LENGTH} chars)"
        # Try to augment existing Spans with info
        span = trace.get_current_span()
        span.add_event(err_msg)
        span.set_status(trace.StatusCode.ERROR)
        return {
            "message": err_msg
        }


####################################
@app.get("/api/v1/thumbsUp")
@otel_tracer.start_as_current_span("/api/v1/thumbsUp")
def thumbs_up(prompt: str):
    logger.info(f"Positive user feedback for search term: {prompt}")


@app.get("/api/v1/thumbsDown")
@otel_tracer.start_as_current_span("/api/v1/thumbsDown")
def thumbs_down(prompt: str):
    logger.info(f"Negative user feedback for search term: {prompt}")


if __name__ == "__main__":

    # Mount static files at the root
    app.mount("/", StaticFiles(directory="./public", html=True), name="public")

    # Run the app using uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082)
