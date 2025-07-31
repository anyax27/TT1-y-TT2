#!/usr/bin/env python3
"""
Script para seleccionar un archivo MP4, verificar formato y duración (<= 3min),
mostrar metadatos, comprimirlo a H.264 con distintos perfiles de compresión y
medir el tiempo de compresión.

Requisitos:
- Python 3.x
- FFmpeg (incluye ffprobe y ffmpeg) en PATH: https://ffmpeg.org/download.html
"""

# ----------------------------------------------
# 🔧 CONFIGURACIÓN DE PARÁMETROS DE COMPRESIÓN
# ----------------------------------------------
# Selección de perfil: 'ultra', 'equilibrado', 'rapido'
PERFIL_COMPRESION = 'equilibrado'

def configurar_parametros(perfil):
    """
    Retorna un diccionario con el 'preset' y el 'crf' de ffmpeg
    según el perfil deseado.
    """
    if perfil == 'ultra':
        # Máxima compresión / más lento
        return {'preset': 'veryslow', 'crf': '24'}
    elif perfil == 'rapido':
        # Compresión rápida / menos reducción de tamaño
        return {'preset': 'veryfast', 'crf': '28'}
    else:
        # Perfil equilibrado
        return {'preset': 'faster', 'crf': '27'}

# Aplicamos la configuración elegida
parametros    = configurar_parametros(PERFIL_COMPRESION)
FFMPEG_PRESET = parametros['preset']
FFMPEG_CRF    = parametros['crf']

# Duración máxima permitida (segundos)
MAX_DURACION = 180.0

# ----------------------------------------------
# 📦 IMPORTACIONES Y SEMILLA
# ----------------------------------------------
import random
import numpy as np

# Semilla global
SEED = 42
random.seed(SEED)
np.random.seed(SEED)


# ----------------------------------------------
# 📦 IMPORTACIONES
# ----------------------------------------------
import tkinter as tk
from tkinter import filedialog
import os
import mimetypes
import subprocess
import json
import sys
import time


# ----------------------------------------------
# 📂 FUNCIÓN: SELECCIONAR ARCHIVO MP4
# ----------------------------------------------
def seleccionar_archivo_mp4():
    """
    Abre un diálogo para que el usuario seleccione un archivo .mp4.
    Devuelve la ruta completa o cadena vacía si se canceló.
    """
    root = tk.Tk()
    root.withdraw()  # Oculta la ventana principal de Tkinter

    tipos = [("Archivos MP4", "*.mp4"), ("Todos los archivos", "*")]
    ruta = filedialog.askopenfilename(
        title="Seleccione un archivo MP4",
        filetypes=tipos
    )
    root.destroy()
    return ruta


# ----------------------------------------------
# 📑 FUNCIÓN: OBTENER METADATOS CON FFPROBE
# ----------------------------------------------
def obtener_metadatos_ffprobe(ruta):
    """
    Ejecuta ffprobe para extraer metadatos del video en JSON.
    Retorna un dict con:
      - format_name: nombre del contenedor (p.ej. mov, mp4)
      - duration   : duración en segundos (float)
      - size       : tamaño en bytes (int)
    """
    cmd = [
        'ffprobe', '-v', 'error',
        '-print_format', 'json',
        '-show_format',
        '-show_streams',
        ruta
    ]
    try:
        resultado = subprocess.run(
            cmd, capture_output=True, text=True, check=True
        )
    except FileNotFoundError:
        print("Error: ffprobe no encontrado. Instala FFmpeg y agrégalo al PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar ffprobe: {e.stderr}")
        sys.exit(1)

    info = json.loads(resultado.stdout)
    fmt  = info.get('format', {})
    return {
        'format_name': fmt.get('format_name', 'desconocido'),
        'duration'   : float(fmt.get('duration', 0.0)),
        'size'       : int(fmt.get('size', 0))
    }


# ----------------------------------------------
# 🎥 FUNCIÓN: COMPRIMIR VIDEO A H.264
# ----------------------------------------------
def comprimir_h264(input_path, output_path):
    """
    Lanza ffmpeg para comprimir el video con libx264,
    usando el preset y CRF configurados, y copia la pista de audio.
    """
    cmd = [
        'ffmpeg', '-y',              # Sobre escribir sin preguntar
        '-i', input_path,            # Archivo de entrada
        '-c:v', 'libx264',           # Codec H.264
        '-preset', FFMPEG_PRESET,    # Preset de velocidad/calidad
        '-crf', FFMPEG_CRF,          # Factor de calidad
        '-c:a', 'copy',              # Copiar audio sin recomprimir
        output_path
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        print("Error: ffmpeg no encontrado. Instala FFmpeg y agrégalo al PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error al comprimir video: {e.stderr}")
        sys.exit(1)


# ----------------------------------------------
# 🚀 FUNCIÓN PRINCIPAL
# ----------------------------------------------
def main():
    # Selección de video
    archivo = seleccionar_archivo_mp4()
    if not archivo:
        print("No se seleccionó ningún archivo.")
        return

    # Verificar extensión
    base, ext = os.path.splitext(archivo)
    if ext.lower() != '.mp4':
        print("Formato incorrecto: solo .mp4.")
        return

    # Obtener metadatos originales
    datos_orig = obtener_metadatos_ffprobe(archivo)
    dur = datos_orig['duration']
    if dur > MAX_DURACION:
        print(f"Duración {dur:.2f}s excede el límite de {MAX_DURACION:.0f}s.")
        return

    size_orig_mb = datos_orig['size'] / (1024 * 1024)
    mime, _ = mimetypes.guess_type(archivo)

    print("\n=== Metadatos ANTES de comprimir ===")
    print(f"Duración: {dur:.2f} s")
    print(f"Tamaño  : {size_orig_mb:.2f} MB")
    print(f"Contenedor: {datos_orig['format_name']}")
    print(f"MIME     : {mime or 'desconocido'}")

    # Preparar salida
    salida = f"{base}_compressed.mp4"
    print("\nComprimiendo video... esto puede tardar unos segundos.")
    t0 = time.time()

    # Ejecutar compresión
    comprimir_h264(archivo, salida)

    t1 = time.time()
    tiempo_comp = t1 - t0

    # Obtener metadatos comprimido
    datos_comp = obtener_metadatos_ffprobe(salida)
    size_comp_mb = datos_comp['size'] / (1024 * 1024)

    # Mostrar resultados
    reduccion = size_orig_mb - size_comp_mb
    porcentaje = (reduccion / size_orig_mb * 100) if size_orig_mb > 0 else 0

    print("\n=== Resultados de la compresión ===")
    print(f"Archivo comprimido: {salida}")
    print(f"Tamaño original   : {size_orig_mb:.2f} MB")
    print(f"Tamaño comprimido : {size_comp_mb:.2f} MB")
    print(f"Reducción         : {reduccion:.2f} MB ({porcentaje:.1f}%)")
    print(f"Tiempo de compresión: {tiempo_comp:.2f} segundos")


if __name__ == '__main__':
    main()
