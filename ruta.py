import os
import pygame , sys
def conseguir_ruta_raiz():
    raiz = os.path.dirname(__file__)
    return raiz

def conseguir_ruta_assets(carpeta, archivo):
    raiz = os.path.dirname(__file__)
    return os.path.join(raiz, "assets")

def conseguir_archivo_sprites(carpeta, archivo):
    return  os.path.join(conseguir_ruta_raiz(), "sprites", carpeta, archivo)
