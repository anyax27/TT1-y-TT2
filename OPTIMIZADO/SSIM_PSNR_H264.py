#!/usr/bin/env python3
"""
Script para seleccionar 2 vídeos (original + H.264 comprimido),
calcular PSNR y SSIM del comprimido respecto al original
e imprimir una valoración de calidad.

Requisitos:
- Python 3.x
- OpenCV       (pip install opencv-python)
- scikit-image (pip install scikit-image)
"""

import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

import tkinter as tk
from tkinter import filedialog
import os
import sys
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
from typing import Tuple

# ----------------------------------------------
# 📂 Seleccionar los 2 vídeos (original + H.264)
# ----------------------------------------------
def seleccionar_videos() -> Tuple[str, str]:
    root = tk.Tk()
    root.withdraw()
    tipos = [("Vídeos", "*.mp4 *.avi"), ("Todos", "*.*")]
    rutas = []
    for etiqueta in ("Original", "H.264 comprimido"):
        ruta = filedialog.askopenfilename(
            title=f"Seleccione el vídeo {etiqueta}",
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
    return rutas[0], rutas[1]

# ----------------------------------------------
# 🔢 Métricas PSNR y SSIM para dos imágenes
# ----------------------------------------------
def calcular_psnr(img1: np.ndarray, img2: np.ndarray) -> float:
    return cv2.PSNR(img1, img2)

def calcular_ssim(img1: np.ndarray, img2: np.ndarray) -> float:
    # Normalizar a [0,1]
    img1_f = img1.astype(np.float32) / 255.0
    img2_f = img2.astype(np.float32) / 255.0
    # Asegurar mismo tamaño
    if img1_f.shape != img2_f.shape:
        img2_f = cv2.resize(img2_f, (img1_f.shape[1], img1_f.shape[0]))
    h, w = img1_f.shape[:2]
    if min(h, w) < 7:
        return 1.0
    return ssim(img1_f, img2_f,
                channel_axis=2,
                data_range=1.0,
                win_size=7)

# ----------------------------------------------
# 🔍 Comparar dos vídeos muestreando frames
# ----------------------------------------------
def evaluar_videos(video_ref: str, video_cmp: str) -> Tuple[float, float]:
    cap_ref = cv2.VideoCapture(video_ref)
    cap_cmp = cv2.VideoCapture(video_cmp)
    if not cap_ref.isOpened() or not cap_cmp.isOpened():
        print("No se pudo abrir alguno de los vídeos.")
        sys.exit(1)

    n_ref = int(cap_ref.get(cv2.CAP_PROP_FRAME_COUNT))
    n_cmp = int(cap_cmp.get(cv2.CAP_PROP_FRAME_COUNT))
    n = min(n_ref, n_cmp)
    if n == 0:
        print("Vídeos sin frames.")
        sys.exit(1)

    muestras   = min(50, n)
    frame_skip = max(1, n // muestras)
    target_size = (640, 360)

    suma_psnr = 0.0
    suma_ssim = 0.0
    cont      = 0

    for i in range(0, n, frame_skip):
        cap_ref.set(cv2.CAP_PROP_POS_FRAMES, i)
        cap_cmp.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok_r, f_r = cap_ref.read()
        ok_c, f_c = cap_cmp.read()
        if not (ok_r and ok_c):
            break

        r_small = cv2.resize(f_r, target_size)
        c_small = cv2.resize(f_c, target_size)

        suma_psnr += calcular_psnr(r_small, c_small)
        suma_ssim += calcular_ssim(r_small, c_small)
        cont      += 1

    cap_ref.release()
    cap_cmp.release()

    if cont == 0:
        print("No se compararon frames.")
        sys.exit(1)

    return suma_psnr / cont, suma_ssim / cont

# ----------------------------------------------
# 🚀 Función principal
# ----------------------------------------------
def main():
    orig, h264 = seleccionar_videos()
    print("\nComparando H.264 comprimido vs original...\n")

    psnr_val, ssim_val = evaluar_videos(orig, h264)

    print(f"PSNR promedio: {psnr_val:.2f} dB", end="  ")
    if psnr_val > 40:
        print("(Excelente calidad)")
    elif psnr_val > 30:
        print("(Buena calidad)")
    else:
        print("(Calidad baja)")

    print(f"SSIM promedio: {ssim_val:.4f}", end="  ")
    if ssim_val > 0.95:
        print("(Muy alta similitud)")
    elif ssim_val > 0.85:
        print("(Buena preservación estructural)")
    else:
        print("(Estructura degradada)")

if __name__ == '__main__':
    main()
