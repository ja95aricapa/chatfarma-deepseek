# ChatFarma-DeepSeek

Sistema de chat para farmacéuticos basado en DeepSeek-R1 que permite:
- Consultar información de farmacología
- Manejar historias clínicas de pacientes
- Actualizar conocimientos con documentos médicos

## Estructura del Proyecto

```
chatfarma-deepseek/
├── backend/                         # Servidor REST con DeepSeek-R1
│   ├── models/                      # Peso del modelo DeepSeek-R1
│   ├── data_to_train/               # Documentos de farmacología
│   ├── embeddings_index/            # Índice de embeddings
│   ├── backend_main.py              # Lógica FastAPI + LangChain
│   └── scripts/                     # Scripts de utilidad
│
├── chat-app/                        # Frontend Electron + React
│   ├── frontend/                    # React application
│   └── main.js                      # Proceso principal de Electron
│
└── scripts/                         # Scripts de ayuda
```

## Requisitos de Desarrollo

- Python 3.9+
- Node.js 18+
- Hugging Face CLI
- Git

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/chatfarma-deepseek.git
cd chatfarma-deepseek
```

2. Instalar dependencias del backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Descargar DeepSeek-R1:
```bash
bash scripts/download_deepseek.sh
```

4. Instalar dependencias del frontend:
```bash
cd ../chat-app/frontend
npm install
```

## Desarrollo

1. Levantar el servidor backend:
```bash
cd backend
python run.py
```

2. En otra terminal, levantar el frontend:
```bash
cd chat-app/frontend
npm run start
```

## Empaquetado para USB

1. Empaquetar el backend:
```bash
cd backend
pyinstaller --onefile --add-data "models/deepseek-r1.bin;models" run.py
```

2. Empaquetar el frontend:
```bash
cd ../chat-app
npm run dist
```

## Licencia

MIT
