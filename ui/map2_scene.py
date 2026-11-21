"""Escena de entrada al mapa 2 (despues del comic final).

Orden:
  1. termina el comic final
  2. transicion MapReveal (la misma del comienzo del juego)
  3. al terminar, las arañas ya estan ahi, QUIETAS, y el monstruo del ojo
     (el del comic) se ve a lo lejos, poco visible en la oscuridad
  4. dialogos: Cenizo (2) -> Monstruo -> Cenizo -> Monstruo
  5. el monstruo tira un rayo de su ojo y lastima a Cenizo
  6. Cenizo herido: "Estoy bien..." y empieza el combate con las arañas
     (el monstruo NO participa: se queda mirando)

Para mover cosas, editar SOLO este archivo (coordenadas = pixeles de
assets/maps/region_01/mapa2.png, 2000 x 1600).

Dibujos del monstruo (PNG con fondo transparente) en assets/maps/combate/:
    monstruo_ojo.png        base: se ve en el mapa y es la cara por defecto
    monstruo_ojo_burla.png  cara de "Asi que traes a un ayudante..."
    monstruo_ojo_ira.png    cara de "Pues no lo necesitaras mas."
Si falta una cara se usa la base; si falta la base se dibuja uno
provisorio (rocas con un ojo amarillo). Mas caras: agregar nombres a
MONSTER_1_FACES / MONSTER_2_FACES (uno por pagina).
"""

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
MONSTER_POS = (131, 1209)
MONSTER_HEIGHT = 84          # alto en pixeles del mundo
MONSTER_ALPHA = 200          # 0-255: "no se ve tanto"
# donde esta el ojo dentro del dibujo (0 a 1, desde arriba-izquierda)
EYE_FRAC = (0.5, 0.40)

# ------------------------------------------------------------ dialogos
# Cenizo ya vio el comic: el gato era un señuelo del monstruo del ojo.
CENIZO_1 = [
    "¡Buuu! Perdón por el susto, {nombre}... aunque creo que hoy te toca "
    "uno peor. Lo viste en el cómic: nunca fue tu gato, era un cebo de ese "
    "[[monstruo del ojo]]. Y caíste. ¡Estás en peligro!",

    "Esas son [[arañas]]: te lanzan telarañas que te ralentizan y, si te "
    "atrapan, vienen a morderte. Las doradas son [[Aurantulas]]: más "
    "grandes, tiran ráfagas y su veneno MATA. ¡Atácalas con tu luz y no te "
    "quedes quieto!",
]

MONSTER_1 = [
    "Así que traes a un ayudante... y algo más que imponga.",
]
# cara del monstruo en cada pagina de arriba (archivo
# assets/maps/combate/monstruo_ojo_<cara>.png; si falta usa monstruo_ojo.png)
MONSTER_1_FACES = ["burla"]

CENIZO_2 = [
    "Oh... parece que él puede verme. Emmh...",
]

MONSTER_2 = [
    "Pues no lo necesitarás más.",
]
MONSTER_2_FACES = ["ira"]

CENIZO_HURT = [
    "Estoy bien... Solo salgamos de esta...",
]