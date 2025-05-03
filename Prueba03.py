#!/usr/bin/env python3
"""
Script para seleccionar un archivo MP4, verificar formato y duración (<= 3min), mostrar metadatos,
comprimirlo simultáneamente con H.264, Motion JPEG (M-JPEG) y MPEG-4, medir tiempos y comparar resultados.

Requisitos:
- Python 3.x
- FFmpeg (ffprobe y ffmpeg) en PATH
"""

# ----------------------------------------------
# 🔧 CONFIGURACIÓN DE PARÁMETROS DE COMPRESIÓN
# ----------------------------------------------
PERFIL_COMPRESION = 'equilibrado'  # 'ultra', 'equilibrado', 'rapido'

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
        return {'preset': 'veryfast', 'crf': '27'}
    else:
        # Perfil equilibrado
        return {'preset': 'medium', 'crf': '25'}

parametros    = configurar_parametros(PERFIL_COMPRESION)
FFMPEG_PRESET = parametros['preset']
FFMPEG_CRF    = parametros['crf']
# Duración máxima (s)
MAX_DURACION = 180.0


# ----------------------------------------------
# 📦 IMPORTACIONES
# ----------------------------------------------
import tkinter as tk
from tkinter import filedialog
import os, mimetypes, subprocess, json, sys, time


# ----------------------------------------------
# 📂 FUNCIONES AUXILIARES
# ----------------------------------------------
def seleccionar_archivo_mp4():
    """Diálogo para seleccionar .mp4"""
    root = tk.Tk()
    root.withdraw()
    tipos = [("MP4","*.mp4"),("Todos","*")]
    ruta = filedialog.askopenfilename(title="Seleccione un archivo MP4", filetypes=tipos)
    root.destroy()
    return ruta


def obtener_metadatos_ffprobe(ruta):
    """Extrae formato, duración, tamaño y resolución"""
    cmd = ['ffprobe','-v','error','-print_format','json','-show_format','-show_streams', ruta]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except Exception as e:
        print(f"Error ffprobe: {e}")
        sys.exit(1)
    info = json.loads(res.stdout)
    fmt = info.get('format',{})
    # resolución
    w = h = None
    for s in info.get('streams',[]):
        if s.get('codec_type') == 'video':
            w, h = s.get('width'), s.get('height')
            break
    return {
        'format_name': fmt.get('format_name','desconocido'),
        'duration'   : float(fmt.get('duration',0.0)),
        'size'       : int(fmt.get('size',0)),
        'width'      : w, 
        'height'     : h
    }


# ----------------------------------------------
# 🎥 COMPRESIÓN H.264
# ----------------------------------------------
def comprimir_h264(input_path, output_path):
    cmd = [
        'ffmpeg','-y','-i', input_path,
        '-c:v','libx264','-preset',FFMPEG_PRESET,'-crf',FFMPEG_CRF,
        '-c:a','copy', output_path
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)


# ----------------------------------------------
# 🎞 COMPRIMIR CON M-JPEG
# ----------------------------------------------
# Calidad MJPEG: 2 (mejor) a 31 (peor). Ajustar para asegurar compresión.
MJPEG_QUALITY = '15'

def comprimir_mjpeg(input_path, output_path):
    """
    Comprime usando Motion JPEG manteniendo resolución original,
    con fps y calidad configurables.
    """
    MJPEG_QUALITY = '20'  # 2–31, 2 mejor calidad
    FPS = '24'            # Frames por segundo deseados

    cmd = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-r', FPS,           # Mantener o ajustar fps
        '-c:v', 'mjpeg',
        '-q:v', MJPEG_QUALITY,
        '-c:a', 'copy',
        output_path
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        print("Error: ffmpeg no encontrado al comprimir M-JPEG.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error en M-JPEG: {e.stderr}")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error en M-JPEG: {e.stderr}")
        sys.exit(1)


# ----------------------------------------------
# 📦 COMPRESIÓN MPEG-4
# ----------------------------------------------
def comprimir_mpeg4(input_path, output_path):
    """
    Comprime usando códec MPEG-4 ASP (libxvid), bitrate 1.5 Mbps
    """
    BITRATE = '1500k'
    cmd = [
        'ffmpeg','-y','-i', input_path,
        '-c:v','mpeg4','-b:v', BITRATE,
        '-c:a','copy', output_path
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        print("Error: ffmpeg no encontrado al comprimir MPEG-4.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error en MPEG-4: {e.stderr}")
        sys.exit(1)


# ----------------------------------------------
# 🚀 PROCESO PRINCIPAL
# ----------------------------------------------
def main():
    archivo = seleccionar_archivo_mp4()
    if not archivo:
        print("Cancelado")
        return

    base, ext = os.path.splitext(archivo)
    if ext.lower() != '.mp4':
        print("Solo .mp4")
        return

    # Metadatos originales
    datos_orig = obtener_metadatos_ffprobe(archivo)
    dur        = datos_orig['duration']
    if dur > MAX_DURACION:
        print(f"Duración {dur:.2f}s > {MAX_DURACION}s")
        return

    size_o_mb = datos_orig['size'] / (1024 * 1024)
    res       = f"{datos_orig['width']}x{datos_orig['height']}"

    print(f"\nORIGINAL → Dur: {dur:.2f}s | Tamaño: {size_o_mb:.2f}MB | Resol: {res}")

    # H.264
    out_h264 = f"{base}_h264.mp4"
    t0       = time.time()
    comprimir_h264(archivo, out_h264)
    t_h264   = time.time() - t0
    d_h264   = obtener_metadatos_ffprobe(out_h264)
    size_h264 = d_h264['size'] / (1024 * 1024)
    print(f"\nH.264    → Tamaño: {size_h264:.2f}MB | Tiempo: {t_h264:.2f}s")

    # M-JPEG
    out_mjpeg = f"{base}_mjpeg.avi"
    t0        = time.time()
    comprimir_mjpeg(archivo, out_mjpeg)
    t_mjpeg   = time.time() - t0
    d_mjpeg   = obtener_metadatos_ffprobe(out_mjpeg)
    size_mjpeg = d_mjpeg['size'] / (1024 * 1024)
    print(f"M-JPEG   → Tamaño: {size_mjpeg:.2f}MB | Tiempo: {t_mjpeg:.2f}s")

    # MPEG-4
    out_mpeg4 = f"{base}_mpeg4.mp4"
    t0        = time.time()
    comprimir_mpeg4(archivo, out_mpeg4)
    t_mpeg4   = time.time() - t0
    d_mpeg4   = obtener_metadatos_ffprobe(out_mpeg4)
    size_mpeg4 = d_mpeg4['size'] / (1024 * 1024)
    print(f"MPEG-4   → Tamaño: {size_mpeg4:.2f}MB | Tiempo: {t_mpeg4:.2f}s")

    # Comparación general
    red_h264  = size_o_mb - size_h264
    red_mjpeg = size_o_mb - size_mjpeg
    red_mpeg4 = size_o_mb - size_mpeg4

    print("\n--- Comparación ---")
    print(f"H.264    : -{red_h264:.2f}MB ({red_h264/size_o_mb*100:.1f}%) en {t_h264:.2f}s")
    print(f"M-JPEG   : -{red_mjpeg:.2f}MB ({red_mjpeg/size_o_mb*100:.1f}%) en {t_mjpeg:.2f}s")
    print(f"MPEG-4   : -{red_mpeg4:.2f}MB ({red_mpeg4/size_o_mb*100:.1f}%) en {t_mpeg4:.2f}s")
    print(f"Ratio tiempos: MJPEG/H264={t_mjpeg/t_h264:.1f}x, MPEG4/H264={t_mpeg4/t_h264:.1f}x")


if __name__ == '__main__':
    main()
