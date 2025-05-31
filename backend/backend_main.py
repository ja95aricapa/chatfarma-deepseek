import os
from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from langchain.embeddings import DeepSeekEmbeddings
from langchain.vectorstores import Chroma
from langchain.llms import DeepSeek
from langchain.chains import ConversationalRetrievalChain
from langchain.document_loaders import (
    UnstructuredPDFLoader,
    Docx2txtLoader,
    PandasExcelLoader,
    PytesseractLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tempfile
import shutil
import uvicorn
from pydantic import BaseModel


class ChatPayload(BaseModel):
    question: str
    chat_history: list[list[str]] = []


app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de directorios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data_to_train")
EMBEDDINGS_DIR = os.path.join(BASE_DIR, "embeddings_index")

# Inicializar el modelo DeepSeek
llm = DeepSeek(model_name="togethercomputer/DeepSeek-R-1")
embeddings = DeepSeekEmbeddings()

# Crear los vectorstores
persistent_store = Chroma(
    persist_directory=EMBEDDINGS_DIR, embedding_function=embeddings
)
# El índice de sesión NO persiste en disco (solo vive en RAM)
session_store = Chroma(persist_directory=None, embedding_function=embeddings)

# Crear la cadena de conversación
qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=persistent_store.as_retriever(search_kwargs={"k": 5}),
    return_source_documents=True,
)


@app.get("/health")
async def health_check():
    return {"status": "up"}


@app.post("/chat")
async def chat_endpoint(payload: ChatPayload):
    question = payload.question
    history = payload.chat_history
    result = qa_chain({"question": question, "chat_history": history})
    return {
        "answer": result["answer"],
        "sources": [doc.metadata for doc in result["source_documents"]],
    }


@app.post("/train")
async def train_endpoint():
    """
    Recorre TODA la carpeta data_to_train/ y la indexa en persistent_store.
    Cada archivo (PDF, DOCX, XLSX, JPG, PNG) se lee con el loader adecuado,
    se fragmenta en chunks y se añade a persistent_store. Luego persiste en disco.
    """
    # Verificar que exista la carpeta
    if not os.path.exists(DATA_DIR):
        raise HTTPException(
            status_code=500, detail="No existe la carpeta data_to_train/"
        )

    # Listar todos los archivos que haya en data_to_train/
    all_files = os.listdir(DATA_DIR)
    if not all_files:
        return {"status": "vacio", "message": "No hay archivos en data_to_train/"}

    docs_to_add = []
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    for filename in all_files:
        filepath = os.path.join(DATA_DIR, filename)
        lower = filename.lower()

        # Elegir loader según extensión
        if lower.endswith(".pdf"):
            loader = UnstructuredPDFLoader(filepath)
        elif lower.endswith(".docx") or lower.endswith(".doc"):
            loader = Docx2txtLoader(filepath)
        elif lower.endswith(".xlsx") or lower.endswith(".xls"):
            loader = PandasExcelLoader(filepath)
        elif (
            lower.endswith(".png") or lower.endswith(".jpg") or lower.endswith(".jpeg")
        ):
            loader = PytesseractLoader(filepath)
        else:
            # Si no es un tipo soportado, saltar
            continue

        # Cargar y dividir en chunks
        try:
            loaded = loader.load()
            split_docs = text_splitter.split_documents(loaded)
            docs_to_add.extend(split_docs)
        except Exception as e:
            # Podríamos hacer logging aquí, pero devolvemos un mensaje de error parcial
            print(f"Error procesando {filename}: {e}")
            continue

    if docs_to_add:
        # Añadir solo a persistent_store
        persistent_store.add_documents(docs_to_add)
        # Guardar índice en disco
        persistent_store.persist()
        return {
            "status": "success",
            "message": f"Índice global actualizado con {len(docs_to_add)} fragmentos.",
        }
    else:
        return {
            "status": "sin_contenido",
            "message": "No se encontró texto indexable en data_to_train/.",
        }


@app.post("/upload_patient")
async def upload_patient(file: UploadFile = File(...)):
    # Procesar el archivo recibido y añadirlo SOLO a session_store (en memoria)
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = os.path.join(temp_dir, file.filename)
        # Guardar archivo en temp
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Elegir loader según tipo de archivo
        lower = file.filename.lower()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        )
        docs_to_add = []

        try:
            if lower.endswith(".pdf"):
                loader = UnstructuredPDFLoader(temp_path)
            elif lower.endswith(".docx") or lower.endswith(".doc"):
                loader = Docx2txtLoader(temp_path)
            elif lower.endswith(".xlsx") or lower.endswith(".xls"):
                loader = PandasExcelLoader(temp_path)
            elif (
                lower.endswith(".png")
                or lower.endswith(".jpg")
                or lower.endswith(".jpeg")
            ):
                loader = PytesseractLoader(temp_path)
            else:
                return {
                    "status": "error",
                    "message": "Formato no soportado para historia clínica.",
                }

            loaded = loader.load()
            split_docs = text_splitter.split_documents(loaded)
            docs_to_add.extend(split_docs)
        except Exception as e:
            return {"status": "error", "message": f"Fallo al procesar el archivo: {e}"}

        # Añadir SOLO a session_store (in-memory)
        if docs_to_add:
            session_store.add_documents(docs_to_add)
            return {
                "status": "success",
                "message": f"Historia clínica {file.filename} indexada en sesión con {len(docs_to_add)} fragmentos.",
            }
        else:
            return {
                "status": "sin_texto",
                "message": "No se extrajo texto del archivo.",
            }


@app.post("/clear_session")
async def clear_session():
    # Volver a instanciar session_store en memoria (sin persistir)
    global session_store
    session_store = Chroma(persist_directory=None, embedding_function=embeddings)
    return {"status": "success", "message": "Sesión de pacientes limpiada."}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
