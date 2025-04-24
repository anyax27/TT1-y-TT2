#!/usr/bin/env python3
"""
Script para seleccionar un archivo MP4, verificar formato y duración (<= 30s), y mostrar metadatos usando ffprobe.

Requisitos:
- Python 3.x
- FFmpeg (ffprobe) en PATH: https://ffmpeg.org/download.html
"""
import tkinter as tk                  # Para interfaz gráfica
from tkinter import filedialog        # Para diálogos de selección de archivos
import os                              # Para manejar archivos
import mimetypes                       # Para determinar tipo MIME
import subprocess                      # Para llamar a ffprobe
import json                            # Para parsear salida JSON de ffprobe
import sys                             # Para exit

# Duración máxima permitida (segundos)
MAX_DURACION = 30.0


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
    format_name = fmt.get('format_name', 'desconocido')
    duration = float(fmt.get('duration', 0.0))
    size = int(fmt.get('size', 0))
    return {
        'format_name': format_name,
        'duration': duration,
        'size': size
    }


def main():
    archivo = seleccionar_archivo_mp4()
    if not archivo:
        print("No se seleccionó ningún archivo.")
        return

    # Verificar extensión .mp4
    _, ext = os.path.splitext(archivo)
    if ext.lower() != '.mp4':
        print("Formato incorrecto: debe ser un archivo .mp4.")
        return

    # Obtener metadatos con ffprobe
    datos = obtener_metadatos_ffprobe(archivo)
    dur = datos['duration']
    if dur > MAX_DURACION:
        print(f"Duración: {dur:.2f}s. Excede el límite de {MAX_DURACION:.0f}s.")
        return

    # Calcular tamaño en MB
    size_mb = datos['size'] / (1024 * 1024)

    # Tipo MIME y demás
    mime, _ = mimetypes.guess_type(archivo)
    mime = mime or 'desconocido'

    # Mostrar resultados
    print("\n=== Datos del video seleccionado ===")
    print(f"Formato contenedor (ffprobe): {datos['format_name']}")
    print(f"Tipo MIME: {mime}")
    print(f"Extensión: {ext}")
    print(f"Duración: {dur:.2f} segundos")
    print(f"Peso: {size_mb:.2f} MB")

if __name__ == '__main__':
    main()
