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
MODEL_ID="togethercomputer/DeepSeek-R-1"
DEST_DIR="../models"
MODEL_FILE="deepseek-r1.bin"

# Crear directorio de destino si no existe
mkdir -p "$DEST_DIR"

echo "Descargando DeepSeek-R1 de Hugging Face..."
huggingface-cli download $MODEL_ID --cache-dir "$DEST_DIR" --local-dir "$DEST_DIR"

# Verificar si el archivo existe y tiene tamaño razonable
if [ ! -f "$DEST_DIR/$MODEL_FILE" ]; then
    echo "Error: No se pudo descargar el modelo correctamente"
    exit 1
fi

echo "Modelo DeepSeek-R1 descargado exitosamente en $DEST_DIR/$MODEL_FILE"
