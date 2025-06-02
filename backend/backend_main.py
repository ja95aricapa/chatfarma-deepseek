import os
from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.llms import HuggingFacePipeline  # <--- Para LLM Local
from langchain_community.embeddings import (
    HuggingFaceEmbeddings,
)  # <--- Para Embeddings Locales
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain_community.document_loaders import (
    UnstructuredPDFLoader,
    Docx2txtLoader,
    UnstructuredExcelLoader,
    UnstructuredImageLoader,  # Asegúrate de tener Tesseract OCR instalado en tu sistema
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tempfile
import shutil
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
LOCAL_LLM_MODEL_PATH = os.path.join(
    BASE_DIR, "models"
)  # Ruta a tu modelo LLM descargado

# ---- Configuración del Modelo LLM Local ----
print(f"Intentando cargar LLM desde: {LOCAL_LLM_MODEL_PATH}")
if not os.path.exists(os.path.join(LOCAL_LLM_MODEL_PATH, "config.json")):
    raise RuntimeError(
        f"No se encontró config.json en {LOCAL_LLM_MODEL_PATH}. Asegúrate de haber descargado el modelo LLM correctamente."
    )

llm = HuggingFacePipeline.from_model_id(
    model_id=LOCAL_LLM_MODEL_PATH,
    task="text-generation",
    device_map="auto",
    pipeline_kwargs={  # Parámetros para la pipeline de Hugging Face Transformers
        "temperature": 0.7,
        # "max_new_tokens": 512, # Puedes añadir esto aquí si lo necesitas para la generación
    },
    model_kwargs={  # Parámetros pasados al método .from_pretrained() del modelo
        # "torch_dtype": "auto",
        # "trust_remote_code": True, # Solo si es necesario y confías en el código
    },
)
print("LLM local cargado exitosamente.")

# ---- Configuración de Embeddings Locales ----
# Para embeddings locales, usaremos un modelo estándar de Sentence Transformers.
# DEBES ASEGURARTE DE TENER ESTE MODELO DESCARGADO O ACCESIBLE.
# Puedes descargarlo una vez y apuntar a la ruta local, o dejar que HuggingFaceEmbeddings lo descargue la primera vez.
# Ejemplo: "sentence-transformers/all-MiniLM-L6-v2" (bueno y ligero, en inglés)
# Si necesitas español, considera "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
print(f"Cargando modelo de embeddings: {EMBEDDING_MODEL_NAME}")
# Si quieres forzar el uso de CPU para embeddings (útil si la GPU está ocupada por el LLM):
# model_kwargs_embeddings = {'device': 'cpu'}
# embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME, model_kwargs=model_kwargs_embeddings)
embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL_NAME,
    # encode_kwargs={'normalize_embeddings': True} # Algunos modelos se benefician de esto
)
print("Modelo de embeddings cargado exitosamente.")


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
    try:
        result = qa_chain({"question": question, "chat_history": history})
        return {
            "answer": result["answer"],
            "sources": [doc.metadata for doc in result["source_documents"]],
        }
    except Exception as e:
        print(f"Error en chat_endpoint: {e}")  # Loguear el error
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/train")
async def train_endpoint():
    """
    Recorre TODA la carpeta data_to_train/ y la indexa en persistent_store.
    Cada archivo (PDF, DOCX, XLSX, JPG, PNG) se lee con el loader adecuado,
    se fragmenta en chunks y se añade a persistent_store. Luego persiste en disco.
    """
    # Verificar que exista la carpeta
    if not os.path.exists(DATA_DIR):
        raise HTTPException(status_code=404, detail=f"No existe la carpeta {DATA_DIR}")

    # Listar todos los archivos que haya en data_to_train/
    all_files = os.listdir(DATA_DIR)
    if not all_files:
        return {"status": "vacio", "message": f"No hay archivos en {DATA_DIR}"}

    docs_to_add = []
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    for filename in all_files:
        filepath = os.path.join(DATA_DIR, filename)
        lower = filename.lower()
        loader = None

        # Elegir loader según extensión
        if lower.endswith(".pdf"):
            loader = UnstructuredPDFLoader(filepath)
        elif lower.endswith((".docx", ".doc")):
            loader = Docx2txtLoader(filepath)
        elif lower.endswith((".xlsx", ".xls")):
            loader = UnstructuredExcelLoader(filepath)
        elif lower.endswith((".png", ".jpg", ".jpeg")):
            # Asegúrate que Tesseract OCR está instalado y en el PATH del sistema
            # sudo apt-get install tesseract-ocr (en Debian/Ubuntu)
            # y el paquete de idioma español: sudo apt-get install tesseract-ocr-spa
            try:
                loader = UnstructuredImageLoader(
                    filepath, lang="spa"
                )  # Especificar idioma para Tesseract
            except Exception as e:
                print(
                    f"Error inicializando UnstructuredImageLoader para {filename} (¿Tesseract instalado?): {e}"
                )
                continue
        else:
            print(f"Archivo no soportado: {filename}")
            continue

        try:
            print(f"Procesando archivo: {filename}")
            loaded = loader.load()
            split_docs = text_splitter.split_documents(loaded)
            docs_to_add.extend(split_docs)
            print(f"Añadidos {len(split_docs)} chunks de {filename}")
        except Exception as e:
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
            "message": f"No se encontró texto indexable en {DATA_DIR}.",
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
        loader = None

        try:
            if lower.endswith(".pdf"):
                loader = UnstructuredPDFLoader(temp_path)
            elif lower.endswith((".docx", ".doc")):
                loader = Docx2txtLoader(temp_path)
            elif lower.endswith((".xlsx", ".xls")):
                loader = UnstructuredExcelLoader(temp_path)
            elif lower.endswith((".png", ".jpg", ".jpeg")):
                loader = UnstructuredImageLoader(temp_path, lang="spa")
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Formato no soportado para historia clínica.",
                )

            loaded = loader.load()
            split_docs = text_splitter.split_documents(loaded)
            docs_to_add.extend(split_docs)
        except HTTPException as http_exc:  # Re-lanzar HTTPException
            raise http_exc
        except Exception as e:
            print(f"Error en upload_patient procesando {file.filename}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Fallo al procesar el archivo: {e}"
            )

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
    global session_store
    # Recrear el Chroma store en memoria para limpiarlo
    session_store = Chroma(persist_directory=None, embedding_function=embeddings)
    return {"status": "success", "message": "Sesión de pacientes limpiada."}
