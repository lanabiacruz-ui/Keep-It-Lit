import pygame,sys,os
from load_spri import *
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ruta import *
from config import *

###tamanio original=32*32###

pygame.init()

pantalla = pygame.display.set_mode((ANCHO, ALTO))
reloj = pygame.time.Clock()

# --- CONFIGURACIÓN DEL JUGADOR ---
jugador_x, jugador_y = 400, 300
jugador_velocidad = velocidad_jugador

caminar()
sprites = {
    "quieto": [pygame.image.load(conseguir_archivo_sprites("Caminar",f"quieto.png")).convert_alpha()],
    "derecha": der,
    "izquierda": izq,
    "arriba": arr,
    "abajo": ap
}

# Variables de control de animación
accion_actual = "quieto"
indice_sprite = 0
tiempo_animacion = 0
velocidad_animacion = v_cambio_sprit # Controla qué tan rápido cambian los sprites (menor = más lento)
# -----------------------------------------------------------

ejecutando = True
while ejecutando:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            ejecutando = False

    # 2. Captura de movimiento y cambio de acción
    teclas = pygame.key.get_pressed()
    moviendose = False
    nueva_accion = "quieto"

    if teclas[pygame.K_LEFT]:
        jugador_x -= jugador_velocidad
        nueva_accion = "izquierda"
        moviendose = True
    elif teclas[pygame.K_RIGHT]:
        jugador_x += jugador_velocidad
        nueva_accion = "derecha"
        moviendose = True
    elif teclas[pygame.K_UP]:
        jugador_y -= jugador_velocidad
        nueva_accion = "arriba"
        moviendose = True
    elif teclas[pygame.K_DOWN]:
        jugador_y += jugador_velocidad
        nueva_accion = "abajo"
        moviendose = True

    # 3. Lógica matemática para recorrer las listas de sprites
    if moviendose:
        # Si cambia de dirección, reiniciamos la animación para que no salte frames viejos
        if nueva_accion != accion_actual:
            accion_actual = nueva_accion
            indice_sprite = 0
            tiempo_animacion = 0
        
        # Avanzamos el temporizador
        tiempo_animacion += velocidad_animacion
        # El truco: convertimos el tiempo flotante a un índice entero válido para la lista
        indice_sprite = int(tiempo_animacion) % len(sprites[accion_actual])
    else:
        accion_actual = "quieto"
        indice_sprite = 0
        tiempo_animacion = 0

    # 4. Dibujar
    pantalla.fill((30, 30, 30))  # Dibuja tu mapa aquí debajo
    
    # Seleccionamos el sprite exacto usando la acción y el índice actual
    sprite_a_dibujar = pygame.transform.scale(sprites[accion_actual][indice_sprite],(alto_juga,bajo_juga))
    
    pantalla.blit(sprite_a_dibujar, (jugador_x, jugador_y))

    pygame.display.flip()
    reloj.tick(60)

pygame.quit()
sys.exit()  