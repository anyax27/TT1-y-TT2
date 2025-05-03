#!/usr/bin/env python3
"""
Script para seleccionar un archivo MP4, verificar formato y duración (<= 3min),
mostrar metadatos, comprimirlo a H.264 con distintos perfiles de compresión,
medir el tiempo de compresión y registrar los resultados en un CSV para comparar los perfiles
de compresión para el estandar H.264

REQUISITOS:
- Python 3.x
- FFmpeg (ffprobe y ffmpeg) en PATH
"""

# ----------------------------------------------
# 🔧 CONFIGURACIÓN DE PARÁMETROS DE COMPRESIÓN
# ----------------------------------------------
# Elige uno de: 'ultra', 'equilibrado', 'rapido'
PERFIL_COMPRESION = 'rapido'

def configurar_parametros(perfil):
    """
    Retorna un dict con 'preset' y 'crf' según el perfil:
      - ultra: máxima compresión, más lento
      - rapido: menos compresión, muy rápido
      - equilibrado: balance
    """
    if perfil == 'ultra':
        return {'preset': 'veryslow',  'crf': '21'}
    elif perfil == 'rapido':
        return {'preset': 'veryfast',  'crf': '26'}
    else:
        return {'preset': 'medium',    'crf': '23'}

parametros    = configurar_parametros(PERFIL_COMPRESION)
FFMPEG_PRESET = parametros['preset']
FFMPEG_CRF    = parametros['crf']

# Duración máxima permitida (segundos)
MAX_DURACION = 180.0


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
import csv


# ----------------------------------------------
# 📂 FUNCIÓN: SELECCIONAR ARCHIVO MP4
# ----------------------------------------------
def seleccionar_archivo_mp4():
    """
    Abre un diálogo para seleccionar un .mp4.
    Devuelve la ruta o '' si se canceló.
    """
    root = tk.Tk()
    root.withdraw()
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
    Extrae metadatos con ffprobe:
      - format_name : contenedor (e.g. mp4)
      - duration    : segundos (float)
      - size        : bytes (int)
      - width, height : resolución (int)
    """
    cmd = [
        'ffprobe', '-v', 'error',
        '-print_format', 'json',
        '-show_format', '-show_streams',
        ruta
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except FileNotFoundError:
        print("Error: ffprobe no encontrado.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"ffprobe error: {e.stderr}")
        sys.exit(1)

    info = json.loads(res.stdout)
    fmt = info.get('format', {})
    # extraer resolución del primer stream de video
    width = height = None
    for s in info.get('streams', []):
        if s.get('codec_type') == 'video':
            width  = s.get('width')
            height = s.get('height')
            break

    return {
        'format_name': fmt.get('format_name', 'desconocido'),
        'duration'   : float(fmt.get('duration', 0.0)),
        'size'       : int(fmt.get('size', 0)),
        'width'      : width,
        'height'     : height
    }


# ----------------------------------------------
# 🎥 FUNCIÓN: COMPRIMIR VIDEO A H.264
# ----------------------------------------------
def comprimir_h264(input_path, output_path):
    """
    Ejecuta ffmpeg para recodificar a H.264 (libx264) con los parámetros
    configurados, copiando la pista de audio.
    """
    cmd = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-c:v', 'libx264',
        '-preset', FFMPEG_PRESET,
        '-crf', FFMPEG_CRF,
        '-c:a', 'copy',
        output_path
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        print("Error: ffmpeg no encontrado.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"ffmpeg error: {e.stderr}")
        sys.exit(1)


# ----------------------------------------------
# 🚀 FUNCIÓN PRINCIPAL
# ----------------------------------------------
def main():
    # Seleccionar
    archivo = seleccionar_archivo_mp4()
    if not archivo:
        print("No se seleccionó ningún archivo.")
        return

    base, ext = os.path.splitext(archivo)
    if ext.lower() != '.mp4':
        print("Formato incorrecto: solo .mp4.")
        return

    # Metadatos antes
    datos_orig = obtener_metadatos_ffprobe(archivo)
    dur   = datos_orig['duration']
    if dur > MAX_DURACION:
        print(f"Duración {dur:.2f}s excede {MAX_DURACION:.0f}s.")
        return

    size_o = datos_orig['size'] / (1024*1024)
    mime, _ = mimetypes.guess_type(archivo)

    print(f"\nAntes → Duración: {dur:.2f}s | Tamaño: {size_o:.2f}MB | "
          f"Resolución: {datos_orig['width']}×{datos_orig['height']}")

    # Comprimir y medir tiempo
    salida   = f"{base}_compressed.mp4"
    print("\nComprimiendo...")
    t0 = time.time()
    comprimir_h264(archivo, salida)
    dt = time.time() - t0

    # Metadatos después
    datos_comp = obtener_metadatos_ffprobe(salida)
    size_c     = datos_comp['size'] / (1024*1024)

    # Cálculos
    redu   = size_o - size_c
    pct    = (redu / size_o * 100) if size_o>0 else 0

    print(f"\nDespués → Tamaño: {size_c:.2f}MB | Reducción: {redu:.2f}MB ({pct:.1f}%) | Tiempo: {dt:.2f}s")

    # ------------------------------------------
    # 📊 GUARDAR RESULTADOS EN CSV
    # ------------------------------------------
    csv_file = 'resultados_compresion.csv'
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # cabecera
        writer.writerow([
            'Archivo', 'Duración_s', 'Resolución',
            'TamañoAntes_MB', 'TamañoDespués_MB',
            'Reducción_MB', 'Reducción_%', 'Tiempo_s'
        ])
        # fila de datos
        writer.writerow([
            os.path.basename(archivo),
            f"{dur:.2f}",
            f"{datos_orig['width']}x{datos_orig['height']}",
            f"{size_o:.2f}",
            f"{size_c:.2f}",
            f"{redu:.2f}",
            f"{pct:.1f}",
            f"{dt:.2f}"
        ])

    print(f"\nResultados guardados en '{csv_file}'.")

if __name__ == '__main__':
    main()
