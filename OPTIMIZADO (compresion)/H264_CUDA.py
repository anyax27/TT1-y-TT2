#!/usr/bin/env python3
"""
Script para comprimir un MP4 usando únicamente GPU NVIDIA (CUDA/NVENC),
mostrando además resolución, duración y tamaño antes y después.
"""

import os
import sys
import json
import time
import mimetypes
import subprocess
import tkinter as tk
from tkinter import filedialog

# ----------------------------------------------
# 🔧 CONFIGURACIÓN NVENC
# ----------------------------------------------
PRESET_NVENC = 'hq'    # Opciones: 'llhq', 'hq', 'bd', 'll', etc.
CQ_VALUE    = '31'     # Calidad NVENC: 27=alta, 30=media, 32=ligera
USE_BITRATE = False    # Si True, usamos rate control + bitrate abajo
TARGET_BITRATE = '1M'  # e.g. '800k', '1M', '2M'

# Duración máxima permitida (segundos)
MAX_DURACION = 180.0

# ----------------------------------------------
# Función: abrir diálogo y seleccionar MP4
# ----------------------------------------------
def seleccionar_archivo_mp4():
    root = tk.Tk()
    root.withdraw()
    tipos = [("Archivos MP4", "*.mp4"), ("Todos los archivos", "*")]
    ruta = filedialog.askopenfilename(title="Seleccione un archivo MP4", filetypes=tipos)
    root.destroy()
    return ruta

# ----------------------------------------------
# Función: obtener metadatos básicos + resolución
# ----------------------------------------------
def obtener_metadatos(ruta):
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
        print("Error: ffprobe no encontrado. Instala FFmpeg y agrégalo al PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar ffprobe: {e.stderr}")
        sys.exit(1)

    info = json.loads(resultado.stdout)
    fmt    = info.get('format', {})
    streams = info.get('streams', [])

    # Duración y tamaño
    duration = float(fmt.get('duration', 0.0))
    size     = int(fmt.get('size', 0))

    # Buscar primer stream de video para resolución
    width = height = None
    for s in streams:
        if s.get('codec_type') == 'video':
            width  = s.get('width')
            height = s.get('height')
            break

    resolution = f"{width}x{height}" if width and height else "desconocida"
    format_name = fmt.get('format_name', 'desconocido')
    return duration, size, format_name, resolution

# ----------------------------------------------
# Función: comprimir video usando solo GPU
# ----------------------------------------------
def comprimir_gpu(input_path, output_path):
    cmd = [
        'ffmpeg', '-y',
        '-hwaccel', 'cuda',
        '-hwaccel_output_format', 'cuda',
        '-i', input_path,
        '-c:v', 'h264_nvenc',
        '-preset', PRESET_NVENC,
    ]

    if USE_BITRATE:
        cmd += ['-rc', 'vbr_hq', '-b:v', TARGET_BITRATE]
    else:
        cmd += ['-cq', CQ_VALUE]

    cmd += ['-c:a', 'copy', output_path]

    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        print("Error: ffmpeg no encontrado. Instala FFmpeg y agrégalo al PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error al comprimir video: {e.stderr}")
        sys.exit(1)

# ----------------------------------------------
# Función principal
# ----------------------------------------------
def main():
    archivo = seleccionar_archivo_mp4()
    if not archivo:
        print("No se seleccionó ningún archivo. Saliendo.")
        return

    base, ext = os.path.splitext(archivo)
    if ext.lower() != '.mp4':
        print("Formato incorrecto: solo se permiten archivos .mp4.")
        return

    dur, size, fmt, res = obtener_metadatos(archivo)
    if dur > MAX_DURACION:
        print(f"Duración {dur:.1f}s excede el límite de {MAX_DURACION:.0f}s.")
        return

    mime, _ = mimetypes.guess_type(archivo)
    print(f"\nANTES → Resolución: {res} | Duración: {dur:.1f}s | Tamaño: {size/1e6:.2f} MB | Contenedor: {fmt} | MIME: {mime}")

    salida = f"{base}_gpu.mp4"
    t0 = time.time()
    comprimir_gpu(archivo, salida)
    t1 = time.time()

    dur2, size2, _, res2 = obtener_metadatos(salida)
    reduccion_mb = (size - size2) / 1e6
    porcentaje   = (reduccion_mb / (size/1e6)) * 100 if size > 0 else 0

    print(f"\nDESPUÉS → Resolución: {res2} | Duración: {dur2:.1f}s | Tamaño: {size2/1e6:.2f} MB")
    print(f"Reducción: {reduccion_mb:.2f} MB ({porcentaje:.1f}%)")
    print(f"Tiempo de compresión: {t1 - t0:.2f} segundos")

if __name__ == '__main__':
    main()
