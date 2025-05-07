#!/usr/bin/env python3
"""
Script para seleccionar 4 videos (original + 3 comprimidos) en formato .mp4 o .avi,
calcular PSNR y SSIM de cada comprimido respecto al original, e imprimir interpretaciones.

Requisitos:
- Python 3.x
- OpenCV    (pip install opencv-python)
- scikit-image (pip install scikit-image)
"""

# ----------------------------------------------
# 🚫 SUIMIR ADVERTENCIAS DE NUMPY EN WINDOWS
# ----------------------------------------------
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

# ----------------------------------------------
# 📦 IMPORTACIONES
# ----------------------------------------------
import tkinter as tk
from tkinter import filedialog
import os
import sys
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
from typing import Tuple


# ----------------------------------------------
# 📂 FUNCIÓN: SELECCIÓN DE 4 VIDEOS
# ----------------------------------------------
def seleccionar_videos() -> Tuple[str,str,str,str]:
    """
    Abre diálogo para elegir 4 archivos de vídeo (.mp4 o .avi):
    1) Original
    2) H.264 comprimido
    3) Motion JPEG comprimido
    4) MPEG-4 comprimido
    Devuelve una tupla con las 4 rutas.
    """
    root = tk.Tk()
    root.withdraw()
    tipos = [("Videos", "*.mp4 *.avi"), ("Todos", "*")]
    rutas = []
    for etiqueta in ("Original", "H.264", "M-JPEG", "MPEG-4"):
        ruta = filedialog.askopenfilename(
            title=f"Seleccione el video {etiqueta}",
            filetypes=tipos
        )
        if not ruta:
            print("Selección cancelada.")
            sys.exit(0)
        ext = os.path.splitext(ruta)[1].lower()
        if ext not in ('.mp4', '.avi'):
            print(f"Formato no válido ({ruta}). Debe ser .mp4 o .avi.")
            sys.exit(1)
        rutas.append(ruta)
    root.destroy()
    return tuple(rutas)

# ----------------------------------------------
# 🔢 MÉTRICAS: PSNR Y SSIM
# ----------------------------------------------
def calcular_psnr(img1: np.ndarray, img2: np.ndarray) -> float:
    """Calcula PSNR entre dos imágenes."""
    return cv2.PSNR(img1, img2)

def calcular_ssim(img1: np.ndarray, img2: np.ndarray) -> float:
    """
    Calcula SSIM entre dos imágenes RGB normalizadas en [0,1].
    Usa channel_axis=2 y data_range=1.0.
    """
    # Normalizar a [0,1]
    img1_f = img1.astype(np.float32) / 255.0
    img2_f = img2.astype(np.float32) / 255.0

    # Asegurar que las dos imágenes tengan el mismo tamaño
    if img1_f.shape != img2_f.shape:
        img2_f = cv2.resize(img2_f, (img1_f.shape[1], img1_f.shape[0]))

    # Estrategia de ventana fija pequeña para evitar excesos
    # La ventana por defecto es 7, funciona si la imagen >7×7
    h, w = img1_f.shape[:2]
    if min(h, w) < 7:
        # Si es muy pequeña, devolvemos similitud perfecta
        return 1.0

    # Calcular SSIM directo sin full=True
    return ssim(
        img1_f,
        img2_f,
        channel_axis=2,
        data_range=1.0,
        win_size=7
    )

def evaluar_videos(video_ref: str, video_cmp: str) -> Tuple[float,float]:
    """
    Compara dos vídeos muestreando frames:
      - Toma ~50 muestras equiespaciadas en el clip
      - Reduce cada frame a resolución 640×360 para acelerar
      - Calcula PSNR y SSIM en estas muestras
      - Retorna los valores promedio.
    """
    cap_ref = cv2.VideoCapture(video_ref)
    cap_cmp = cv2.VideoCapture(video_cmp)
    if not cap_ref.isOpened() or not cap_cmp.isOpened():
        print("Error al abrir vídeos.")
        sys.exit(1)

    # Número mínimo de frames
    n_ref = int(cap_ref.get(cv2.CAP_PROP_FRAME_COUNT))
    n_cmp = int(cap_cmp.get(cv2.CAP_PROP_FRAME_COUNT))
    n = min(n_ref, n_cmp)
    if n == 0:
        print("Vídeos sin frames.")
        sys.exit(1)

    # Configuración de muestreo y reducción de resolución
    muestras = min(50, n)
    frame_skip = max(1, n // muestras)
    target_size = (640, 360)

    suma_psnr = 0.0
    suma_ssim = 0.0
    cont = 0

    for i in range(0, n, frame_skip):
        cap_ref.set(cv2.CAP_PROP_POS_FRAMES, i)
        cap_cmp.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret_r, f_r = cap_ref.read()
        ret_c, f_c = cap_cmp.read()
        if not (ret_r and ret_c):
            break

        # Reducir resolución para cálculo
        small_r = cv2.resize(f_r, target_size)
        small_c = cv2.resize(f_c, target_size)

        suma_psnr += calcular_psnr(small_r, small_c)
        suma_ssim += calcular_ssim(small_r, small_c)
        cont += 1

    cap_ref.release()
    cap_cmp.release()

    if cont == 0:
        print("No se compararon muestras.")
        sys.exit(1)

    return suma_psnr / cont, suma_ssim / cont


# ----------------------------------------------
# 🚀 FUNCIÓN PRINCIPAL
# ----------------------------------------------
def main():
    # Selección interactiva de 4 vídeos
    orig, h264, mjpeg, mpeg4 = seleccionar_videos()

    print("\nComparando cada video comprimido contra el original...\n")

    comparativos = {
        "H.264"  : h264,
        "M-JPEG" : mjpeg,
        "MPEG-4" : mpeg4
    }

    for label, ruta in comparativos.items():
        psnr_val, ssim_val = evaluar_videos(orig, ruta)

        print(f"=== {label} ===")
        print(f"PSNR: {psnr_val:.2f} dB", end="  ")
        if psnr_val > 40:
            print("(Excelente calidad)")
        elif psnr_val > 30:
            print("(Buena calidad)")
        else:
            print("(Calidad baja)")

        print(f"SSIM: {ssim_val:.4f}", end="  ")
        if ssim_val > 0.95:
            print("(Muy alta similitud)")
        elif ssim_val > 0.85:
            print("(Buena preservación estructural)")
        else:
            print("(Estructura degradada)")
        print()

if __name__ == '__main__':
    main()
