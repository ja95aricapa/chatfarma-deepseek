#!/usr/bin/env bash
set -e

echo "Construyendo entorno..."
pip install -r requirements.txt

echo "Ejecutando PyInstaller..."
# Se asume que `deepseek-r1.bin` ya está en backend/models/
pyinstaller --onefile --add-data "models/deepseek-r1.bin;models" run.py

# Renombrar y mover
BUILD_DIR="dist"
if [ ! -d "$BUILD_DIR" ]; then
  echo "Error: carpeta dist/ no encontrada."
  exit 1
fi

mv dist/run.exe dist/model-server.exe
echo "model-server.exe generado en dist/"

echo "Listo. Copia dist/model-server.exe a la USB en backend/."
