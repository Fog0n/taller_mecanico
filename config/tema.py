"""
Tema visual global de la aplicación (CustomTkinter).

Aplica el modo de apariencia y el tema de colores, y define
constantes reutilizables para todas las vistas.
"""

import customtkinter as ctk

# Modo de apariencia y tema de colores base
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Paleta de colores del proyecto
COLOR_FONDO = "#1a1a1a"    # Fondo principal oscuro
COLOR_TEXTO = "#ffffff"    # Texto general
COLOR_BOTON = "#2563eb"    # Color primario de botones
COLOR_ERROR = "#ef4444"    # Mensajes de error / alerta

# Fuentes reutilizables
FUENTE_TITULO = ("Arial", 22, "bold")
FUENTE_TEXTO = ("Arial", 13)
FUENTE_BOTON = ("Arial", 14, "bold")

# Tamaños de ventana por vista
LOGIN_SIZE = "400x500"        # Tarjeta compacta de acceso (fija)
MENU_SIZE = "1100x700"        # Menú principal (redimensionable)
MODULO_SIZE = "1120x720"      # Módulos CRUD (redimensionables)
