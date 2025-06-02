#!/bin/bash

# Script para descargar DeepSeek-R1 desde Hugging Face
# Requiere tener instalado huggingface-cli y estar logueado

set -e

echo "Verificando si existe huggingface-cli..."
if ! command -v huggingface-cli &> /dev/null; then
    echo "Error: huggingface-cli no está instalado. Por favor instálalo con:"
    echo "pip install huggingface_hub"
    exit 1
fi

echo "Verificando si estás logueado en Hugging Face..."
huggingface-cli whoami

# Configuración
MODEL_ID="deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B" # <--- CORREGIDO
DEST_DIR="../backend/models"
# MODEL_FILE="deepseek-r1.bin" # Ya no se usa esta variable para la comprobación directa

# Crear directorio de destino si no existe
mkdir -p "$DEST_DIR"

echo "Descargando $MODEL_ID de Hugging Face..."
huggingface-cli download $MODEL_ID --cache-dir "$DEST_DIR" --local-dir "$DEST_DIR" --local-dir-use-symlinks False

# Verificar si el directorio de destino contiene archivos (o si el comando anterior tuvo éxito debido a set -e)
if [ -z "$(ls -A "$DEST_DIR/$MODEL_ID")" ]; then # El download crea una subcarpeta con el nombre del modelo
    echo "Error: El directorio de destino $DEST_DIR/$MODEL_ID está vacío después del intento de descarga."
    echo "Asegúrate que el modelo existe y tienes acceso."
    exit 1
fi

echo "Modelo $MODEL_ID descargado exitosamente en $DEST_DIR/$MODEL_ID"