import pygame,sys,os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ruta import *

def caminar():
    der=[]
    izq=[]
    ap=[]
    arr=[]
    for i in range(1,5):
        der.append(pygame.image.load(conseguir_archivo_sprites("Caminar",f"der ({i}).png")).convert_alpha())
    for i in range(1,5):
        izq.append(pygame.image.load(conseguir_archivo_sprites("Caminar",f"izqu ({i}).png")).convert_alpha())
    for i in range(1,5):
        ap.append(pygame.image.load(conseguir_archivo_sprites("Caminar",f"ap ({i}).png")).convert_alpha())
    for i in range(1,5):
        arr.append(pygame.image.load(conseguir_archivo_sprites("Caminar",f"arr ({i}).png")).convert_alpha())
    return der ,izq,ap,arr