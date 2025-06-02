#!/usr/bin/env bash
set -e

# Nos aseguramos de que el script se ejecute desde el directorio 'backend'
# o que las rutas sean relativas al directorio 'backend'
# Si ejecutas `bash scripts/build_exe.sh` DESDE la carpeta `backend`,
# el directorio actual (pwd) ya es 'backend', lo cual es correcto para las rutas usadas.

echo "Directorio de trabajo actual: $(pwd)"

echo "Construyendo entorno (verificando dependencias)..."
# requirements.txt está en el directorio actual (asumiendo que se ejecuta desde backend/)
pip install -r requirements.txt

echo "Ejecutando PyInstaller..."
# run.py está en el directorio actual
# 'models' es el directorio que contiene tu LLM local
# Usamos ':' como separador para --add-data en Linux/macOS
# Copiamos el contenido del directorio 'models' a una carpeta 'models' dentro del ejecutable
pyinstaller --onefile \
            --add-data "models:models" \
            --noconfirm \
            run.py

# Renombrar y mover
BUILD_DIR="dist" # Se crea en el directorio actual (backend/dist)
if [ ! -d "$BUILD_DIR" ]; then
  echo "Error: carpeta $BUILD_DIR/ no encontrada."
  exit 1
fi

# PyInstaller en Linux genera un ejecutable con el nombre del script (sin .exe)
# Si el script es run.py, el ejecutable se llamará 'run'
TARGET_EXEC_NAME="model-server"
SOURCE_EXEC_NAME="run" # Nombre base del archivo de entrada de PyInstaller

if [ -f "$BUILD_DIR/$SOURCE_EXEC_NAME" ]; then
    mv "$BUILD_DIR/$SOURCE_EXEC_NAME" "$BUILD_DIR/$TARGET_EXEC_NAME"
    echo "$TARGET_EXEC_NAME generado en $BUILD_DIR/"
else
    echo "Error: No se encontró el ejecutable $BUILD_DIR/$SOURCE_EXEC_NAME generado por PyInstaller."
    exit 1
fi

echo "Listo. Copia $BUILD_DIR/$TARGET_EXEC_NAME a la USB (o donde lo necesites)."