import pygame
import sys

# Inicializar Pygame
pygame.init()

# Configuración de la ventana (ajusta el tamaño si tu juego usa otro)
ANCHO, ALTO = 800, 600
ventana = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Animación de Fletchling")
reloj = pygame.time.Clock()

# --- VARIABLES DEL JUGADOR Y ANIMACIÓN ---
# Carga las 15 imágenes (000 a 014) usando una lista por comprensión limpia
animacion_caminar = [
    pygame.image.load(f"pokemon/fletching/caminar-Fletchling{i:03d}.png").convert_alpha() 
    for i in range(15)
]

indice_imagen = 0
contador_pasos = 0
velocidad_animacion = 5  # Cambia cada 5 fotogramas

x = 100
y = 100
velocidad_movimiento = 5

moviendose = False
direccion_derecha = True  # Para saber hacia dónde mira el personaje

# --- BUCLE PRINCIPAL DEL JUEGO ---
ejecutando = True
while ejecutando:
    # Fondo de pantalla (puedes cambiarlo por tu propio fondo o color)
    ventana.fill((50, 50, 50))  # Gris oscuro paso a paso

    # 1. Manejo de eventos de salida
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            ejecutando = False

    # 2. Captura de teclas presionadas
    teclas = pygame.key.get_pressed()
    moviendose = False  # Se asume falso al inicio de cada fotograma

    if teclas[pygame.K_LEFT]:
        x -= velocidad_movimiento
        moviendose = True
        direccion_derecha = False  # Mira a la izquierda

    if teclas[pygame.K_RIGHT]:
        x += velocidad_movimiento
        moviendose = True
        direccion_derecha = True   # Mira a la derecha

    # 3. Lógica estricta de Animación (¡Cuidado con la sangría aquí!)
    if moviendose:
        contador_pasos += 1
        # Dividimos los pasos por la velocidad para ralentizar el aleteo
        indice_imagen = (contador_pasos // velocidad_animacion) % len(animacion_caminar)
    else:
        # Si se detiene por completo, vuelve al fotograma inicial
        indice_imagen = 0
        contador_pasos = 0

    # 4. Asignación y volteo de imagen según la dirección
    imagen_actual = animacion_caminar[indice_imagen]
    
    if not direccion_derecha:
        # Si va a la izquierda, invertimos la imagen horizontalmente (True, False)
        imagen_actual = pygame.transform.flip(imagen_actual, True, False)

    # 5. Dibujar en la ventana
    ventana.blit(imagen_actual, (x, y))

    # Actualizar pantalla y mantener a 60 FPS estables
    pygame.display.flip()
    reloj.tick(60)

pygame.quit()
sys.exit()
