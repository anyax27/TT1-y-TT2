#!/usr/bin/env python3
"""
Script para seleccionar un archivo MP4, verificar formato y duración (<= 30s), mostrar metadatos y comprimirlo a H.264 para reducir su tamaño,
medir el tiempo de compresión.

Requisitos:
- Python 3.x
- FFmpeg (incluye ffprobe y ffmpeg) en PATH: https://ffmpeg.org/download.html
"""
import tkinter as tk                  # Para interfaz gráfica
from tkinter import filedialog        # Para diálogos de selección de archivos
import os                              # Para manejo de archivos
import mimetypes                       # Para determinar tipo MIME
import subprocess                      # Para llamadas a ffprobe y ffmpeg
import json                            # Para parsear salida JSON de ffprobe
import sys                             # Para exit
import time                            # Para medir tiempo de compresión

# Duración máxima permitida (segundos)
MAX_DURACION = 30.0
# Parámetros de compresión H.264
FFMPEG_PRESET = 'slow'  # presets: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
FFMPEG_CRF = '28'       # Calidad CRF: 0 (sin pérdida) a 51 (peor calidad). Valores 18-28 son comunes.


def seleccionar_archivo_mp4():
    """
    Abre diálogo para seleccionar un archivo y devuelve la ruta.
    """
    root = tk.Tk()
    root.withdraw()
    tipos = [("Archivos MP4", "*.mp4"), ("Todos los archivos", "*")]
    ruta = filedialog.askopenfilename(title="Seleccione un archivo MP4", filetypes=tipos)
    return ruta


def obtener_metadatos_ffprobe(ruta):
    """
    Obtiene metadatos del video usando ffprobe en formato JSON.
    Retorna diccionario con 'format_name', 'duration' (float), y 'size' (bytes).
    """
    cmd = [
        'ffprobe', '-v', 'error',
        '-print_format', 'json',
        '-show_format',
        '-show_streams',
        ruta
    ]
    try:
        resultado = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except FileNotFoundError:
        print("Error: ffprobe no encontrado. Asegúrate de tener FFmpeg instalado y ffprobe en tu PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar ffprobe: {e.stderr}")
        sys.exit(1)

    info = json.loads(resultado.stdout)
    fmt = info.get('format', {})
    return {
        'format_name': fmt.get('format_name', 'desconocido'),
        'duration': float(fmt.get('duration', 0.0)),
        'size': int(fmt.get('size', 0))
    }


def comprimir_h264(input_path, output_path):
    """
    Comprime el video de entrada usando H.264 con ffmpeg y guarda en output_path.
    Usa CRF y preset definidos.
    """
    cmd = [
        'ffmpeg', '-y',             # Sobrescribir sin preguntar
        '-i', input_path,           # Archivo de entrada
        '-c:v', 'libx264',          # Codec video H.264
        '-preset', FFMPEG_PRESET,   # Preset de velocidad/calidad
        '-crf', FFMPEG_CRF,         # Factor de calidad
        '-c:a', 'copy',             # Copia la pista de audio sin recomprimir
        output_path
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        print("Error: ffmpeg no encontrado. Asegúrate de tener FFmpeg instalado y ffmpeg en tu PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error al comprimir video: {e.stderr}")
        sys.exit(1)


def main():
    archivo = seleccionar_archivo_mp4()
    if not archivo:
        print("No se seleccionó ningún archivo.")
        return

    # Verificar extensión .mp4
    base, ext = os.path.splitext(archivo)
    if ext.lower() != '.mp4':
        print("Formato incorrecto: debe ser un archivo .mp4.")
        return

    # Metadatos originales
    datos_orig = obtener_metadatos_ffprobe(archivo)
    dur = datos_orig['duration']
    if dur > MAX_DURACION:
        print(f"Duración: {dur:.2f}s. Excede el límite de {MAX_DURACION:.0f}s.")
        return
    size_orig_mb = datos_orig['size'] / (1024 * 1024)

    # Mostrar metadatos originales
    mime, _ = mimetypes.guess_type(archivo)
    print("\n=== Metadatos antes de comprimir ===")
    print(f"Duración      : {dur:.2f} segundos")
    print(f"Tamaño        : {size_orig_mb:.2f} MB")
    print(f"Formato       : {datos_orig['format_name']}")
    print(f"Tipo MIME     : {mime or 'desconocido'}")

    # Ruta de salida para video comprimido
    ruta_salida = f"{base}_compressed.mp4"

    # Comprimir video y medir tiempo
    print("\nComprimiendo video con H.264... Esto puede tardar unos segundos.")
    inicio = time.time()
    comprimir_h264(archivo, ruta_salida)
    fin = time.time()
    tiempo_comp = fin - inicio

    # Metadatos comprimido
    datos_comp = obtener_metadatos_ffprobe(ruta_salida)
    size_comp_mb = datos_comp['size'] / (1024 * 1024)

    # Mostrar comparación
    print("\n=== Resultado de la compresión ===")
    print(f"Archivo comprimido: {ruta_salida}")
    print(f"Tamaño original   : {size_orig_mb:.2f} MB")
    print(f"Tamaño comprimido : {size_comp_mb:.2f} MB")
    reduccion = size_orig_mb - size_comp_mb
    porcentaje = (reduccion / size_orig_mb * 100) if size_orig_mb > 0 else 0
    print(f"Reducción         : {reduccion:.2f} MB ({porcentaje:.1f}%)")
    print(f"Tiempo compresión : {tiempo_comp:.2f} segundos")

if __name__ == '__main__':
    main()
