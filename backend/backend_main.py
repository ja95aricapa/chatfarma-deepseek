import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain.embeddings import DeepSeekEmbeddings
from langchain.vectorstores import Chroma
from langchain.llms import DeepSeek
from langchain.chains import ConversationalRetrievalChain
import tempfile
import shutil
import uvicorn

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
persistent_store = Chroma(persist_directory=EMBEDDINGS_DIR, embedding_function=embeddings)
session_store = Chroma(persist_directory=EMBEDDINGS_DIR, embedding_function=embeddings)

# Crear la cadena de conversación
qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=persistent_store.as_retriever(search_kwargs={"k": 5}),
    return_source_documents=True
)

@app.get("/health")
async def health_check():
    return {"status": "up"}

@app.post("/chat")
async def chat(question: str, chat_history: list[tuple[str, str]] = []):
    result = qa_chain({"question": question, "chat_history": chat_history})
    return {
        "answer": result["answer"],
        "sources": [doc.metadata for doc in result["source_documents"]]
    }

@app.post("/train")
async def train(file: UploadFile = File(...)):
    # Crear un directorio temporal para el archivo
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = os.path.join(temp_dir, file.filename)
        
        # Guardar el archivo temporalmente
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Procesar el archivo según su tipo
        if file.filename.lower().endswith(('.pdf', '.docx', '.xlsx')):
            # Aquí iría el procesamiento del archivo
            pass
        
        # Agregar el texto procesado al vectorstore
        # Esto es un ejemplo y necesitaría implementación específica
        text = "Ejemplo de texto extraído del documento"
        docs = [{"page_content": text, "metadata": {"source": file.filename}}]
        
        session_store.add_documents(docs)
        persistent_store.add_documents(docs)
        
    return {"status": "success", "message": f"Documento {file.filename} procesado y añadido al índice"}

@app.post("/upload_patient")
async def upload_patient(file: UploadFile = File(...)):
    # Similar a /train pero los documentos se mantienen solo en RAM
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = os.path.join(temp_dir, file.filename)
        
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Procesar y agregar al vectorstore de sesión
        text = "Ejemplo de texto extraído del documento"
        docs = [{"page_content": text, "metadata": {"source": file.filename}}]
        
        session_store.add_documents(docs)
        
    return {"status": "success", "message": f"Historia clínica {file.filename} cargada en sesión"}

@app.post("/clear_session")
async def clear_session():
    session_store.delete_collection()
    return {"status": "success", "message": "Sesión limpia"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
