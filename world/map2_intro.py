"""Configuracion de la escena de entrada al mapa 2 (despues del comic final).

La logica esta en ui/map2_scene.py; aca solo van las coordenadas y los
textos. Orden de la escena:
  1. termina el comic final
  2. transicion MapReveal (la misma del comienzo del juego)
  3. al terminar, las arañas ya estan ahi, QUIETAS, y el monstruo del ojo
     (el del comic) se ve a lo lejos, poco visible en la oscuridad. Cenizo
     esta al lado del jugador
  4. dialogos: Cenizo (2) -> Monstruo -> Cenizo -> Monstruo (por el panel,
     con su cara en cada frase)
  5. el monstruo tira un rayo de su ojo y lastima a Cenizo
  6. Cenizo herido: "Estoy bien..." y empieza el combate con las arañas
     (el monstruo NO participa: se queda mirando)

Coordenadas = pixeles de assets/maps/region_01/mapa2.png, 2000 x 1600.

Dibujos del monstruo (PNG con fondo transparente, las 3 del mismo tamaño y
con el mismo contorno) en assets/maps/combate/:
    monstruo_ojo.png        base: se ve en el mapa y es la cara por defecto
    monstruo_ojo_burla.png  cara de "Asi que traes a un ayudante..."
    monstruo_ojo_ira.png    cara de "Pues no lo necesitaras mas."
Si falta una cara se usa la base; si falta la base se dibuja uno
provisorio. Mas caras: agregar nombres a MONSTER_1_FACES / MONSTER_2_FACES
(uno por pagina) y el archivo monstruo_ojo_<nombre>.png.
"""

# ------------------------------------------------------------ camara
# Mientras habla Cenizo (y despues del rayo) la camara encuadra al jugador y a
# Cenizo JUNTOS, un poco mas arriba del centro de la pantalla: el cuadro de
# dialogo ocupa la esquina de abajo a la derecha y si ellos quedaran ahi
# abajo se taparian. Asi se ven los dos enteros y, arriba, se asoma el
# monstruo. CAMERA_ANCHOR_TALK = a que altura de la pantalla queda el punto
# medio entre los dos (0 = arriba de todo, 1 = abajo de todo).
CAMERA_ANCHOR_TALK = 0.58

# Mientras habla el monstruo la camara se desplaza hacia el (CAMERA_MIX_MONSTER
# = 1.0: lo centra). En el rayo sigue al rayo desde el ojo hasta Cenizo (ver
# mas abajo). Valores de 0 (el jugador) a 1 (el monstruo).
CAMERA_MIX_MONSTER = 1.0
CAMERA_SMOOTH = 3.0          # velocidad del movimiento de camara en la escena (mas bajo = mas lento)

# El rayo: la camara arranca en el ojo mientras se carga, viaja junto con el
# rayo hasta Cenizo y se queda en el cuando le pega (y mientras sale
# despedido). Mas alto = la camara acompaña mas rapido.
CAMERA_SMOOTH_RAY = 6.0
RAY_TRAVEL_TIME = 0.35       # segundos que tarda el rayo en llegar del ojo a Cenizo

# Al terminar la intro la camara se abre para mostrar mas del lugar (zoom
# normal del juego: 4). Mas bajo = se ve mas mapa (3 = un tercio mas; 2.5 no
# es entero: usar 3 o 2).
MAP2_ZOOM = 3
ZOOM_FADE_OUT = 0.25         # oscurece antes del cambio (segundos)
ZOOM_FADE_IN = 0.45          # y vuelve a mostrarse ya con la vista amplia

# VERDE: donde aparece el personaje
PLAYER_POS = (120, 1356)

# ROJOS: arañas comunes (x, y)
SPIDER_POS = [
    (72, 1250), (234, 1254),
    (60, 1292), (234, 1298),
    (50, 1326), (252, 1350),
]

# NARANJAS: aurantulas (x, y)
AURA_POS = [
    (200, 1238), (80, 1266),
]

# AZUL: monstruo del ojo (centro del dibujo en el mundo)
# (con MONSTER_HEIGHT = 260 el centro sube a y=1123: los pies quedan donde
# estaban, en y=1253, y crece hacia arriba en vez de pisar a las arañas.
# Si cambias el alto: y = 1253 - alto / 2)
MONSTER_POS = (150, 1123)
MONSTER_HEIGHT = 260         # alto en pixeles del mundo (era 176, antes 84: ahora imponente)
MONSTER_ALPHA = 255          # 0-255 (el dibujo ya viene con el cuerpo tenue)
# donde esta el ojo dentro del dibujo (0 a 1, desde arriba-izquierda)
EYE_FRAC = (0.452, 0.465)

# COLISION: el monstruo es solido, no se lo puede atravesar. La caja esta en
# sus pies (la base del dibujo), quieta aunque el flote suba y baje.
MONSTER_HITBOX_W = 0.50      # ancho de la caja (fraccion del ancho del dibujo)
MONSTER_HITBOX_H = 40        # alto de la caja (pixeles del mundo)

# ------------------------------------------------------------ vida del monstruo
# Nombre que se ve en el cartel cuando habla.
MONSTER_NAME = "Oculumbra"

# Flota como si respirara en el aire. Las cantidades son fracciones del alto
# del monstruo (MONSTER_HEIGHT): 0.025 = sube y baja un 2,5% de su alto.
FLOAT_SPEED = 1.0        # 1 = normal, mas alto = mas agitado (furioso ya va 1,5x)
FLOAT_BOB = 0.025        # sube y baja
FLOAT_SWAY = 0.012       # se balancea de costado
FLOAT_LEAN = 0.010       # se inclina hacia donde mira

# Las dos manos de roca flotan por su cuenta. Cada una es un rectangulo del
# dibujo (x0, y0, x1, y1) en fracciones de 0 a 1: izquierda y derecha.
HAND_RECTS = (
    (0.00, 0.68, 0.27, 1.00),
    (0.60, 0.70, 1.00, 1.00),
)

# El ojo te mira: la pupila se mueve hacia el jugador. Solo en estas caras
# (en "burla" e "ira" la pupila va fija, como esta dibujada).
EYE_LOOK_FACES = ("base",)
EYE_LOOK_X = 0.066       # cuanto se corre la pupila de costado (fraccion del ancho)
EYE_LOOK_Y = 0.012       # y hacia arriba/abajo (fraccion del alto)
EYE_LOOK_SMOOTH = 5.0    # que tan rapido la pupila te sigue (mas alto = mas rapido)

# ------------------------------------------------------------ dialogos
# Cenizo NO vio el comic (el comic es la historia del juego, no de el).
# Ya conoce al jugador, habla por los codos y sabe un poco de las arañas,
# pero no sabe como se llama el monstruo ni que son las doradas.
# Cada linea es una pagina: mantenerlas cortas para que no se achique la letra.
CENIZO_1 = [
    "¡Buuu! ¡{nombre}! ¿Te asusté? ¡Te asusté! Perdón, perdón, es que \
llegué volando y no me pude aguantar.",

    "Oye, oye, ¿viste dónde estamos? Qué oscuro, qué húmedo, qué FEO. \
Y encima está lleno de patitas. ¡Muchas patitas!",

    "Esas son [[arañas]], eso sí lo sé. Lanzan telarañas que te ralentizan y, \
si te atrapan, vienen a morderte. ¡Y muerden feo!",

    "Y esas doradas... mmm, esas no sé qué son. Nunca vi unas así. Son más \
grandes, brillan raro y no me dan ninguna confianza.",

    "Tú atácalas con tu luz y no te quedes quieto, ¿sí? Yo te animo desde \
aquí atrás... con mucho respeto a la distancia. Espera...",

    "¿Sientes eso? Es como si algo nos estuviera mirando. Algo GRANDE. \
Ay, no me gusta nada esto, {nombre}...",
]

MONSTER_1 = [
    "Así que traes a un ayudante... Se ve muy facil lo dependiente que eres..",
]
# cara del monstruo en cada pagina de arriba (archivo
# assets/maps/combate/monstruo_ojo_<cara>.png; si falta usa monstruo_ojo.png)
MONSTER_1_FACES = ["burla"]

CENIZO_2 = [
    "¿¡ESO HABLÓ!? ¿¡Dijo 'ayudante'!! Oh... parece que él puede verme. \
Emmh...",

    "Nunca he entrado por esta cueva porque hablaban de que era muy peligroso.. Creo que debemos de irnos.. ¿Podemos hablarlo? ¿Un té? ¿Algo?",
]

MONSTER_2 = [
    "No necesitaras mas a tu fantasma burlon..",
]
MONSTER_2_FACES = ["ira"]

CENIZO_HURT = [
    "¡AAAH! Eso... eso dolió un montón. ¡Estoy bien! ¡Estoy bien! Es solo \
un rasguñito... Estoy... Bien..",

    "Solo salgamos de esta... {nombre}.... Tu puedes... Yo resisto..",
]