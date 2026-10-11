"""Sala de combate (la sala grande de la derecha).

Al entrar aparece un menu transparente: Salir / Jugar con escape /
Jugar sin escape (premio X2). Despues vienen las oleadas:

  - Con escape: podes irte caminando de la sala (cancela la oleada).
  - Sin escape: la entrada se bloquea mientras pelean. El premio vale
    el doble.
  - En los dos modos, si te quedas sin vida perdes la partida de verdad.

Al matar al ultimo enemigo aparece un cofre que brilla y explota,
tirando las monedas del premio. Cuando las juntas vuelve el menu para
la siguiente oleada.

Al terminar la oleada LAST_WAVE (10) el mapa queda completado: el cofre
tambien tira una gema, aparece el cartel de 'Mapa completado', te sacan
de la sala y la entrada se cierra para siempre (se guarda en la partida).

Imagenes (todas opcionales: si falta alguna se dibuja un reemplazo):
  assets/maps/combate/enemigo.png            56x56
  assets/maps/combate/enemigo_anim.png       224x56 (4 frames)
  assets/maps/combate/enemigo_golpe.png      56x56
  assets/maps/combate/panel_sala_combate.png 420x300
  assets/maps/combate/btn_salir.png          260x56  (+ _hover)
  assets/maps/combate/btn_jugar_escape.png   260x56  (+ _hover)
  assets/maps/combate/btn_jugar_sin_escape.png 260x56 (+ _hover)
  assets/maps/combate/hud_oleada.png         180x40
  assets/maps/combate/pantalla_oleada_completa.png 420x200
  assets/maps/combate/pantalla_mapa_completado.png 420x200 (oleada 10)
  assets/maps/combate/sala_sellada.png       40x160 (entrada cerrada)
  assets/maps/hud/icon_gema.png              64x64
  assets/maps/combate/hongun_anim.png        224x56 (4 frames, caminar)
  assets/maps/combate/hongun_carga.png       112x56 (2 frames, recargando)
  assets/maps/combate/hongun.png             56x56  (opcional, 1 solo cuadro)
  assets/maps/combate/hongun_golpe.png       56x56  (opcional)

La sala grande de la IZQUIERDA tambien es una sala de oleadas (ver
LEFT_ARENA): 2 oleadas. La 1 trae los mobs de siempre y la 2 trae al
Guardian. Imagenes del Guardian (opcionales, ver GuardianArt):
  assets/maps/combate/guardian.png           256x320 (4x4: caminar)
  assets/maps/combate/guardian_ataque.png    128x320 (2x4: aviso y golpe)
  assets/maps/combate/guardian_arma.png      el arma, apuntando hacia arriba
  assets/maps/combate/guardian_icono.png     56x56 (enciclopedia)

Destello (hongun flashbang: tranquilo e ilumina, cuando te ve corre muy
rapido, te choca, explota y te deja la pantalla blanca ~5 s). Imagenes
(todas opcionales, ver DestelloArt):
  assets/maps/combate/destello_anim.png      224x56 (4 cuadros, caminar tranquilo)
  assets/maps/combate/destello_correr.png    224x56 (4 cuadros, corriendo)
  assets/maps/combate/destello_alerta.png    112x56 (2 cuadros, aviso antes de correr)
  assets/maps/combate/destello.png           56x56  (1 cuadro, tambien es el icono de la enciclopedia)
  assets/maps/combate/destello_golpe.png     56x56  (cuando le pegas)

Golem (enorme y MUY lento: pasea tranquilo, si te ve va directo hacia vos
y si te toca te agarra: una animacion lo muestra apretandote y te saca
TODO el escudo; si no tenias escudo te saca TODA la vida de la luz). Ver
GolemArt. Imagenes opcionales (si falta alguna se dibuja un reemplazo):
  assets/maps/combate/golem_anim.png         448x112 (4 cuadros de 112x112, caminar tranquilo)
  assets/maps/combate/golem_perseguir.png    448x112 (4 cuadros, persiguiendote; opcional)
  assets/maps/combate/golem_alerta.png       224x112 (2 cuadros, aviso al verte)
  assets/maps/combate/golem_agarre.png       672x112 (6 cuadros, la animacion del agarre)
  assets/maps/combate/golem.png              112x112 (1 cuadro, por si falta golem_anim)
  assets/maps/combate/golem_golpe.png        112x112 (cuando le pegas; opcional)
  assets/maps/combate/golem_icono.png        128x128 (enciclopedia)

Guardian Tirador (igual al Guardian pero dispara bolas, ver
GuardianShooterArt). Imagenes opcionales:
  assets/maps/combate/guardian_tirador.png          256x320 (4x4: caminar)
  assets/maps/combate/guardian_tirador_disparo.png  128x320 (2x4: apuntar y disparar)
  assets/maps/combate/guardian_tirador_icono.png    128x128 (enciclopedia)
  assets/maps/combate/bola_guardian.png             32x32 (la bola, mirando a la derecha)
"""

import math
import random
from pathlib import Path

import pygame

from world.fireball import FIRE_SPEED
from world import pathing
from world.items import WorldItem, get_gem_icon
from world.melee import (
    ARC_DEGREES, COOLDOWN, INNER_RADIUS, OUTER_RADIUS, SWING_TIME,
    ease_out, sector_outline,
)


BASE_DIR = Path(__file__).resolve().parent.parent

COMBAT_DIR = BASE_DIR / "assets" / "maps" / "combate"
CHEST_DIR = BASE_DIR / "assets" / "maps" / "cofre"
HUD_DIR = BASE_DIR / "assets" / "maps" / "hud"


# ---------------------------------------------------------------
# Lugar (unidades del mundo)
# ---------------------------------------------------------------

# La sala grande de la derecha (igual que en world/collision.py)
ROOM = pygame.Rect(1244, 388, 436, 284)

# El menu aparece cuando el jugador pisa esta zona (un poco adentro)
TRIGGER = pygame.Rect(1262, 400, 400, 260)

# Donde te deja "Salir": en el pasillo, afuera de la sala
EXIT_POS = (1190, 520)

# Barrera que cierra la entrada en "sin escape" / mapa completado.
# Llena el hueco del pasillo de pared a pared (el hueco dibujado en
# mapa.png mide 41 px de alto: y 499 a 540), dentro del tramo con
# paredes y pegada a la sala, sin pisar la puerta gris (x 1206-1222).
GATE = pygame.Rect(1224, 498, 14, 44)


# La sala grande de la IZQUIERDA (igual que en world/collision.py).
# Se entra por el pasillo de la derecha (el que sale del hub).
ROOM_LEFT = pygame.Rect(148, 336, 500, 408)
TRIGGER_LEFT = pygame.Rect(166, 348, 464, 384)
EXIT_POS_LEFT = (700, 518)
# El hueco dibujado mide 42 px de alto (y 497 a 539) y las paredes
# empiezan en x=658: la barrera va dentro del tramo con paredes.
GATE_LEFT = pygame.Rect(660, 495, 14, 46)


# ---------------------------------------------------------------
# Oleadas (para balancear, se cambia todo aca)
# ---------------------------------------------------------------
# (pinos, troncos, mosquitos, hongunes, guardianes, guardianes tiradores,
#  destellos, golems)  <- las tablas pueden traer de 4 a 8 numeros
LEFT_WAVE_COMPOSITION = {
    1: (0,0,0,0,0,0,4,3),
    2: (0, 0, 0, 0, 2, 1,),
}
# Que trae cada oleada: (pinos, troncos, mosquitos, hongunes). Los pinos rebotan y te
# pegan al chocarte; los troncos te siguen de lejos y disparan 3 bolas que rebotan;
# los hongunes caminan tranquilos, te persiguen cuando te detectan y explotan.
# Despues de la ultima definida sube PINOS_STEP pinos y TRONCOS_STEP
# troncos por oleada, sin pasar de ENEMIES_MAX en total.
WAVE_COMPOSITION = {
    # Oleada 1: un pino y el primer destello (el 7mo numero)
    1: (1, 0, 0, 0),
    2: (4, 0, 0, 0),
    3: (5, 1, 0, 0),
    4: (5, 2, 0, 0),
    5: (4, 4, 0, 0),

    # Oleada 6
    6: (4, 7, 3, 0),

    # Oleada 7
    7: (10, 5, 6, 0),

    # Oleadas 8, 9 y 10: aparecen los hongunes
    8: (10, 5, 8, 1),
    # El 7mo numero son los destellos (hongun flashbang)
    9: (4, 6, 10, 3, 0, 0, 2, 1),
    # El 8vo numero son los golems (lentos, te agarran y te sacan el escudo)
    10: (5, 6, 7, 8, 0, 0, 4, 2),
}
# Ultima oleada del mapa: al pasarla el mapa queda completado, el cofre
# tira una gema y la sala se cierra para siempre.
LAST_WAVE = 10

PINOS_STEP = 1
TRONCOS_STEP = 1
TRONCOS_MAX = 8
ENEMIES_MAX = 32
MOSQUITOS_STEP = 1   # mosquitos que se suman por oleada despues de la ultima definida
MOSQUITOS_MAX = 20
HONGUNS_STEP = 0     # hongunes que se suman por oleada despues de la ultima definida (0 = se quedan igual)
HONGUNS_MAX = 8
DESTELLOS_STEP = 0   # destellos que se suman por oleada despues de la ultima definida
DESTELLOS_MAX = 8
GOLEMS_STEP = 0      # golems que se suman por oleada despues de la ultima definida
GOLEMS_MAX = 4

# Oleada de PRUEBA (solo mosquitos). La usa la partida "Prueba mosquitos".
# Para cambiar cuantos salen, cambia el 3. Se puede borrar cuando termines.
MOSQUITO_TEST_WAVE = 99
MOSQUITO_TEST_COUNT = 3

# Oleada de PRUEBA (solo destellos), igual que la de los mosquitos: poner
# la oleada 98 en una partida de prueba. Se puede borrar cuando termines.
DESTELLO_TEST_WAVE = 98
DESTELLO_TEST_COUNT = 3

# Oleada de PRUEBA (solo golems): poner la oleada 97 en una partida de
# prueba. Se puede borrar cuando termines.
GOLEM_TEST_WAVE = 97
GOLEM_TEST_COUNT = 2

# Monedas de premio por oleada (la 1 vale 18). Despues de la ultima
# definida sube REWARD_STEP por oleada. "Sin escape" lo multiplica.
WAVE_REWARDS = {1: 18, 2: 30, 3: 45}
REWARD_STEP = 15
NO_ESCAPE_MULT = 2

# Vida y velocidad de los enemigos segun la oleada
ENEMY_HP_BASE = 2          # vida = BASE + oleada
ENEMY_HP_MAX = 10
ENEMY_SPEED_BASE = 58      # unidades del mundo por segundo
ENEMY_SPEED_STEP = 4
ENEMY_SPEED_MAX = 90

# Cuanta vida de la llama le saca cada choque (1.0 = toda la llama)
ENEMY_DAMAGE = 0.08
ENEMY_DAMAGE_STEP = 0.01
ENEMY_DAMAGE_MAX = 0.15

# Si te quedas sin vida en "con escape", te dejan con esta llama
ESCAPE_REVIVE_LIFE = 0.15


# ---------------------------------------------------------------
# Piña
# ---------------------------------------------------------------

ENEMY_DRAW_SIZE = 14       # tamano dibujado (unidades del mundo)
ENEMY_HITBOX = (12, 10)    # lo que choca y lo que golpea el fosforo

ENEMY_BALL_MULT = 1.8      # velocidad de la bola = velocidad de la oleada x esto
ENEMY_ACCEL = 320.0        # que tan rapido vuelve a su velocidad tras un empujon
ENEMY_BOUNCE_AIM = 0.85    # 0 = rebota normal, 1 = sale derecho hacia el jugador
ENEMY_BOUNCE_JITTER = 6.0  # grados al azar en cada rebote (para que no sea predecible)
ENEMY_DRAG = 1.6           # frenado del empujon cuando le pegas
ENEMY_HIT_BOUNCE = 1.2     # velocidad con la que sale rebotado tras chocarte (x bola)
ENEMY_TOUCH_COOLDOWN = 0.6
WALL_BOUNCE = 1.0          # cuanta velocidad conserva al rebotar (1 = toda)
ENEMY_KNOCKBACK = 150.0    # empujon cuando le pegas
ENEMY_STUN_TIME = 0.25
ENEMY_FLASH_TIME = 0.12
ENEMY_SPAWN_TIME = 0.8     # aparece transparente y no hace daño
ENEMY_ANIM_FRAME = 0.15
ENEMY_SPIN_RATE = 2.0      # cuanto gira mientras rueda (grados por unidad recorrida)
ENEMY_HOP_DIST = 38.0      # cada cuantas unidades recorridas da un saltito
ENEMY_HOP_HEIGHT = 3.0     # altura del saltito (unidades del mundo)

# ---------------------------------------------------------------
# Tronco (dispara 3 bolas que rebotan)
# ---------------------------------------------------------------

TRONCO_HITBOX = (14, 12)
TRONCO_DRAW_SIZE = 16      # tamano dibujado (unidades del mundo)
TRONCO_HP_EXTRA = 0        # vida = la del pino + esto
TRONCO_FIRST_DELAY = (2.0, 3.0)  # primera espera (al azar, para que no disparen todos juntos)
TRONCO_WINDUP = 1.0        # cuanto tarda quieto apuntandote antes de soltar las bolas
TRONCO_SHOOT_TIME = 0.45   # duracion de la animacion de disparo
TRONCO_COOLDOWN = 8.0      # segundos entre un disparo y el siguiente
TRONCO_HIT_PAUSE = 1.5     # si le pegas mientras carga, se le corta y espera esto
TRONCO_SHOTS = 3           # bolas por disparo
TRONCO_SPREAD = 24.0       # grados entre una bola y la siguiente
TRONCO_LEAD = 0.45         # cuanto adelanta la punteria hacia donde te estas moviendo (seg)
TRONCO_ANIM_FRAME = 0.12

# Movimiento del tronco: te sigue pero manteniendo distancia y sin
# meterse en tu luz (asi no lo ves ni lo alcanzas a pegar).
TRONCO_SPEED = 70.0        # unidades del mundo por segundo (el jugador va a 95)
TRONCO_KEEP_DIST = 60.0    # distancia minima que intenta mantener
TRONCO_MAX_DIST = 120.0    # distancia maxima a la que se queda (si tu luz es enorme)
TRONCO_LIGHT_MARGIN = 14.0 # cuanto afuera del borde de tu luz se queda
TRONCO_BAND = 8.0          # tolerancia: dentro de esta franja no se mueve
TRONCO_FIRE_EXTRA = 10.0   # puede empezar a cargar si esta a ideal + BAND + esto

SHOT_SPEED = 95.0          # unidades del mundo por segundo
SHOT_HITBOX = 6
SHOT_DRAW_SIZE = 8
SHOT_BOUNCES = 2           # cuantas veces rebota (al tercer choque desaparece)
SHOT_LIFE = 7.0            # maximo de segundos en el aire
SHOT_DAMAGE_MULT = 4.5     # x el dano de un choque de pino

# ---------------------------------------------------------------
# Mosquito
# ---------------------------------------------------------------

MOSQUITO_HP = 2   # golpes que aguanta (el fosforo y la vela pegan 1 por golpe)
MOSQUITO_HITBOX = (9, 7)
MOSQUITO_DRAW_SIZE = 13

# Vuelo libre por la sala
MOSQUITO_WANDER_SPEED = 45.0     # velocidad volando libre
MOSQUITO_TURN_TIME = (0.8, 2.2)  # cada cuanto cambia un poco de rumbo

# Alerta en el HUD: aparece cuando esta a esta distancia EXTRA del borde
# de tu luz (o sea, antes de que lo toque tu luz)
MOSQUITO_ALERT_MARGIN = 90.0

# Ataque: cuando tu luz lo toca va directo hacia vos y se pega
MOSQUITO_ATTACK_SPEED = 280.0
MOSQUITO_ATTACK_ACCEL = 900.0
MOSQUITO_ATTACH_DIST = 10.0

# Ciclo (segundos)
MOSQUITO_ATTACH_TIME = 60.0      # pegado: te chupa 1 minuto y se suelta
MOSQUITO_REST_TIME = 60.0        # despues de soltarte, a este tiempo vuelve a atacar
MOSQUITO_FLEE_TIME = 8.0         # apenas te suelta, intenta irse (se aleja rapido)
MOSQUITO_FLEE_SPEED = 85.0

# Repelente: despues de espantarlo, el mosquito no vuelve a intentar
# atacar antes de este tiempo (s) y huye al menos este tiempo (s)
MOSQUITO_REPEL_REST = 4.0
MOSQUITO_REPEL_FLEE = 0.8

# Daño
# 0.02 = 2% de la vida de la luz
MOSQUITO_DAMAGE = 0.02
MOSQUITO_DAMAGE_INTERVAL = 1.0

# Animación
MOSQUITO_ANIM_FRAME = 0.10
MOSQUITO_FLASH_TIME = 0.10
MOSQUITO_SPAWN_TIME = 0.8

# ---------------------------------------------------------------
# Hongun (el creeper: camina tranquilo, te persigue y explota)
# ---------------------------------------------------------------

HONGUN_HP = 6                  # golpes que aguanta (si lo matas a golpes NO explota)
HONGUN_HITBOX = (10, 12)
HONGUN_DRAW_SIZE = 18          # tamano dibujado (unidades del mundo)

# Movimiento (unidades del mundo por segundo; el jugador va a 95)
HONGUN_WANDER_SPEED = 22.0     # paseando tranquilo
HONGUN_CHASE_SPEED = 52.0      # persiguiendote (caminata normal)
HONGUN_TURN_TIME = (1.0, 2.6)  # cada cuanto cambia de rumbo paseando

# Deteccion
HONGUN_DETECT_RADIUS = 85.0    # si entras en este radio te empieza a perseguir
HONGUN_LOSE_RADIUS = 140.0     # si te alejas mas que esto te deja de perseguir

# Recarga y explosion
HONGUN_FUSE_DIST = 24.0        # a esta distancia empieza a recargar
HONGUN_FUSE_CANCEL_DIST = 46.0 # si te alejas mas que esto durante la recarga, se cancela
HONGUN_FUSE_TIME = 1.3         # segundos recargando hasta explotar
HONGUN_BLAST_RADIUS = 40.0     # radio de la explosion (unidades del mundo)
HONGUN_DAMAGE = 0.75           # 0.75 = 75% de la vida de la luz
HONGUN_KNOCKBACK = 340.0       # empujon al jugador (el golpe normal de un pino es 120)
HONGUN_LIGHT_MIN = 24          # luz que da al empezar a recargar (px de pantalla)
HONGUN_LIGHT_MAX = 80          # luz que da justo antes de explotar
HONGUN_BLAST_TIME = 0.5        # duracion del aro de la explosion

HONGUN_ANIM_FRAME = 0.15
HONGUN_CHARGE_FRAME = 0.12

# ---------------------------------------------------------------
# Destello (un hongun mas veloz: flashbang)
# Pasea tranquilo y da un poco de luz con el cuerpo. Cuando te ve se
# frena un instante (aviso), sale corriendo muy rapido hacia vos, te
# choca, te saca vida, te deja la pantalla en blanco unos 5 segundos y
# muere. El tiempo del blanco se cambia en states/new_game.py (FLASH_*).
# ---------------------------------------------------------------

DESTELLO_HP = 5                 # golpes que aguanta (si lo matas a golpes NO explota)
DESTELLO_HITBOX = (10, 12)
DESTELLO_DRAW_SIZE = 17         # tamano dibujado (unidades del mundo)

# Movimiento (unidades del mundo por segundo; el jugador va a 95)
DESTELLO_WANDER_SPEED = 20.0    # paseando tranquilo
DESTELLO_CHARGE_SPEED = 175.0   # corriendo hacia vos (casi el doble que el jugador)
DESTELLO_TURN_TIME = (1.0, 2.6) # cada cuanto cambia de rumbo paseando

# Luz que da con el cuerpo, siempre prendida (px de pantalla; la luz del
# fosforo es 100). Durante el aviso y la carrera brilla un poco mas.
DESTELLO_LIGHT = 40
DESTELLO_LIGHT_ALERT = 64

# Deteccion: te tiene que ver (distancia y sin paredes en el medio)
DESTELLO_DETECT_RADIUS = 120.0
DESTELLO_LOSE_RADIUS = 220.0    # si corriendo te alejas mas que esto, te pierde
DESTELLO_ALERT_TIME = 0.35      # aviso quieto (parpadea blanco) antes de salir corriendo
# Primeras oleadas: el aviso dura mas, asi el primer encuentro es justo
# (te da tiempo a verlo parpadear y a reaccionar). Para volver a como
# era, poner DESTELLO_EARLY_WAVES = 0.
DESTELLO_EARLY_WAVES = 2
DESTELLO_ALERT_TIME_EARLY = 0.60

# Choque
DESTELLO_DAMAGE = 0.15          # 0.15 = 15% de la vida de la luz
DESTELLO_KNOCKBACK = 200.0      # empujon al jugador

DESTELLO_ANIM_FRAME = 0.15
DESTELLO_RUN_FRAME = 0.06
DESTELLO_ALERT_FRAME = 0.10

# ---------------------------------------------------------------
# Golem (enorme y muy lento)
# Pasea tranquilo. Si te ve (distancia y sin paredes en el medio) ruge un
# instante (aviso) y va DIRECTO hacia vos, despacito pero sin parar. Si te
# toca UNA sola vez te agarra: una animacion lo muestra levantandote y
# apretandote. Al apretar te saca TODO el escudo; si no tenias escudo, te
# saca TODA la vida de la luz. Despues te suelta, te empuja y queda
# cansado unos segundos.
# ---------------------------------------------------------------

GOLEM_HP = 40                   # golpes que aguanta
GOLEM_HITBOX = (16, 18)         # lo que choca y lo que golpea el jugador
# Tamano dibujado (unidades del mundo). Con zoom x4 son 112 x 112 px,
# que es el tamano de cada cuadro de las imagenes.
GOLEM_DRAW_SIZE = 28

# Movimiento (unidades del mundo por segundo; el jugador va a 95)
GOLEM_WANDER_SPEED = 12.0       # paseando tranquilo
GOLEM_CHASE_SPEED = 30.0        # persiguiendote (muy lento)
GOLEM_TURN_TIME = (1.8, 4.0)    # cada cuanto cambia de rumbo paseando

# Deteccion: te tiene que ver (distancia y sin paredes en el medio)
GOLEM_DETECT_RADIUS = 110.0
GOLEM_LOSE_RADIUS = 200.0       # si te alejas mas que esto, te pierde
GOLEM_ALERT_TIME = 0.9          # aviso quieto (ruge) antes de empezar a perseguirte

# Agarre
GOLEM_GRAB_REACH = 3            # cuanto "alcanza" mas alla de su cuerpo (unidades)
GOLEM_GRAB_TIME = 1.8           # duracion de la animacion completa
GOLEM_SQUEEZE_AT = 0.8          # segundo del agarre en que aprieta (ahi se saca el escudo / la vida)
GOLEM_GRAB_LIFT = 5.0           # cuanto te levanta (unidades del mundo)
GOLEM_HOLD_DY = 2               # donde te sostiene: pies del jugador = base del golem + esto
GOLEM_HOLD_PULL = 120.0         # que tan rapido te acomoda en sus manos (unidades/s)
GOLEM_KNOCKBACK = 230.0         # empujon al soltarte
GOLEM_POST_INVULN = 1.5         # segundos que no te puede agarrar nadie despues de soltarte
GOLEM_REST_TIME = 3.0           # cansado (quieto) despues de agarrarte

GOLEM_HIT_PUSH = 14.0           # cuanto lo mueve un golpe tuyo (casi nada: es pesado)
GOLEM_ANIM_FRAME = 0.28         # caminar tranquilo (lento)
GOLEM_CHASE_FRAME = 0.20        # persiguiendote
GOLEM_ALERT_FRAME = 0.12
GOLEM_FLASH_TIME = 0.10
GOLEM_SPAWN_TIME = 1.0

# ---------------------------------------------------------------
# Tiempos
# ---------------------------------------------------------------

BANNER_TIME = 3.0          # cuanto se ve "Oleada completada"
BANNER_TIME_FINAL = 5.0    # cuanto se ve "Mapa completado"
# El menu de la siguiente oleada NO sale hasta que juntes todas las
# recompensas. Este tiempo es solo un seguro por si una quedo
# inalcanzable (si no, el jugador se quedaria trabado).
COLLECT_TIMEOUT = 60.0
MAX_COIN_ITEMS = 30        # monedas dibujadas (cada una vale mas)


# ---------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------

_images = {}
_fonts = {}


def load_image(path, size=None):
    """Carga un PNG (cacheado). None si no existe."""

    key = (str(path), size)

    if key in _images:
        return _images[key]

    img = None

    if Path(path).exists():

        try:

            img = pygame.image.load(str(path)).convert_alpha()

            if size is not None and img.get_size() != size:
                img = pygame.transform.smoothscale(img, size)

        except pygame.error:
            img = None

    _images[key] = img

    return img


def get_font(size):

    if size not in _fonts:
        _fonts[size] = pygame.font.Font(None, size)

    return _fonts[size]


def draw_text(screen, text, size, color, **anchor):
    """Texto con sombra. anchor: center=, midtop=, topleft=, midleft="""

    font = get_font(size)

    shadow = font.render(text, True, (0, 0, 0))
    label = font.render(text, True, color)

    rect = label.get_rect(**anchor)

    screen.blit(shadow, rect.move(2, 2))
    screen.blit(label, rect)

    return rect


def quantize_radius(radius):
    """Radio de luz en pasos de 8 px (minimo 8): la luz se cachea por
    radio, asi no se crea una superficie nueva en cada frame."""

    return max(8, int(round(radius / 8.0)) * 8)


def wave_composition(wave, table=None):
    """(pinos, troncos, mosquitos, hongunes, guardianes, tiradores,
    destellos, golems) de una oleada.

    `table` es la tabla de la sala (por defecto la de la sala derecha).
    Las tablas pueden tener de 4 a 8 numeros (los que faltan valen 0)."""
    if table is None:
        table = WAVE_COMPOSITION
    # Oleadas de prueba (solo en la sala de la derecha). Antes estaban
    # adentro del "if table is None" y como la arena siempre pasa su
    # tabla nunca se activaban.
    if table is WAVE_COMPOSITION:
        if wave == MOSQUITO_TEST_WAVE:
            return 0, 0, MOSQUITO_TEST_COUNT, 0, 0, 0, 0, 0
        if wave == DESTELLO_TEST_WAVE:
            return 0, 0, 0, 0, 0, 0, DESTELLO_TEST_COUNT, 0
        if wave == GOLEM_TEST_WAVE:
            return 0, 0, 0, 0, 0, 0, 0, GOLEM_TEST_COUNT
    if wave in table:
        return tuple(table[wave]) + (0,) * (8 - len(table[wave]))
    last = max(table)
    row = tuple(table[last]) + (0,) * (8 - len(table[last]))
    pinos, troncos, mosquitos, honguns, guardians, shooters, destellos, golems = row
    extra = max(0, wave - last)
    pinos += PINOS_STEP * extra
    troncos = min(TRONCOS_MAX, troncos + TRONCOS_STEP * extra)
    mosquitos = min(MOSQUITOS_MAX, mosquitos + MOSQUITOS_STEP * extra)
    honguns = min(HONGUNS_MAX, honguns + HONGUNS_STEP * extra)
    destellos = min(DESTELLOS_MAX, destellos + DESTELLOS_STEP * extra)
    golems = min(GOLEMS_MAX, golems + GOLEMS_STEP * extra)
    total = pinos + troncos + mosquitos + honguns + destellos + golems
    if total > ENEMIES_MAX:
        mosquitos = max(0, mosquitos - (total - ENEMIES_MAX))
    return (pinos, troncos, mosquitos, honguns, guardians, shooters,
            destellos, golems)


def enemies_for_wave(wave, table=None):
    """Cuantos enemigos trae la oleada en total."""

    return sum(wave_composition(wave, table))


def base_reward(wave, table=None):

    if table is None:
        table = WAVE_REWARDS

    if wave in table:
        return table[wave]

    last = max(table)

    return table[last] + REWARD_STEP * (wave - last)

# ---------------------------------------------------------------
# Mosquito - sprites
# ---------------------------------------------------------------

class MosquitoArt:

    def __init__(self):

        idle = load_strip(
            COMBAT_DIR / "mosquito_anim.png"
        )

        single = load_image(
            COMBAT_DIR / "mosquito.png"
        )

        warning = load_image(
            COMBAT_DIR / "mosquito_advertencia.png"
        )

        if idle:

            self.frames = idle

        elif single is not None:

            self.frames = [single]

        else:

            self.frames = [
                self._placeholder()
            ]

        if warning is not None:

            self.warning = warning

        else:

            self.warning = self._warning_placeholder()

        self._zoom = None
        self._scaled = None
        self._warning_scaled = None

    @staticmethod
    def _placeholder():

        surf = pygame.Surface(
            (56, 56),
            pygame.SRCALPHA
        )

        # cuerpo
        pygame.draw.ellipse(
            surf,
            (45, 35, 40),
            (23, 19, 14, 25)
        )

        # abdomen
        pygame.draw.ellipse(
            surf,
            (180, 45, 55),
            (25, 31, 10, 13)
        )

        # alas
        pygame.draw.ellipse(
            surf,
            (205, 220, 225, 190),
            (8, 12, 24, 12)
        )

        pygame.draw.ellipse(
            surf,
            (205, 220, 225, 190),
            (24, 10, 24, 12)
        )

        # ojos
        pygame.draw.circle(
            surf,
            (240, 80, 90),
            (27, 20),
            3
        )

        pygame.draw.circle(
            surf,
            (240, 80, 90),
            (33, 20),
            3
        )

        # aguijón
        pygame.draw.line(
            surf,
            (220, 220, 220),
            (30, 42),
            (30, 50),
            2
        )

        return surf

    @staticmethod
    def _warning_placeholder():

        surf = pygame.Surface(
            (48, 48),
            pygame.SRCALPHA
        )

        pygame.draw.polygon(
            surf,
            (255, 65, 65, 240),
            [
                (24, 4),
                (44, 40),
                (4, 40)
            ]
        )

        pygame.draw.polygon(
            surf,
            (20, 20, 25, 255),
            [
                (24, 11),
                (36, 35),
                (12, 35)
            ]
        )

        pygame.draw.rect(
            surf,
            (255, 80, 80),
            (22, 16, 4, 12)
        )

        pygame.draw.circle(
            surf,
            (255, 80, 80),
            (24, 33),
            2
        )

        return surf

    def get(self, zoom):

        if self._zoom != zoom:

            px = max(
                1,
                int(MOSQUITO_DRAW_SIZE * zoom)
            )

            self._scaled = [
                pygame.transform.scale(
                    frame,
                    (px, px)
                )
                for frame in self.frames
            ]

            warning_px = max(
                16,
                int(16 * zoom)
            )

            self._warning_scaled = (
                pygame.transform.smoothscale(
                    self.warning,
                    (warning_px, warning_px)
                )
            )

            self._zoom = zoom

        return (
            self._scaled,
            self._warning_scaled
        )
# ---------------------------------------------------------------
# Imagenes del enemigo (se cargan una sola vez para todos)
# ---------------------------------------------------------------

class EnemyArt:

    def __init__(self):

        sheet = load_image(COMBAT_DIR / "enemigo_anim.png")
        single = load_image(COMBAT_DIR / "enemigo.png")
        hit = load_image(COMBAT_DIR / "enemigo_golpe.png")

        frames = []

        if sheet is not None and sheet.get_height() > 0:

            fw = sheet.get_height()

            for i in range(max(1, sheet.get_width() // fw)):

                frames.append(
                    sheet.subsurface((i * fw, 0, fw, fw)).copy()
                )

        elif single is not None:
            frames.append(single)

        if not frames:
            frames.append(self._placeholder())

        if hit is None:

            hit = frames[0].copy()
            hit.fill((170, 170, 170, 0), special_flags=pygame.BLEND_RGB_ADD)

        self.frames = frames
        self.hit = hit

        self._zoom = None
        self._scaled = None
        self._scaled_hit = None

    @staticmethod
    def _placeholder():

        surf = pygame.Surface((56, 56), pygame.SRCALPHA)

        pygame.draw.circle(surf, (120, 80, 50), (28, 30), 22)
        pygame.draw.circle(surf, (50, 30, 20), (28, 30), 22, 3)
        pygame.draw.circle(surf, (20, 10, 10), (20, 26), 4)
        pygame.draw.circle(surf, (20, 10, 10), (36, 26), 4)

        return surf

    def get(self, zoom):
        """Frames y sprite de golpe ya escalados al zoom actual."""

        if self._zoom != zoom:

            px = max(1, int(ENEMY_DRAW_SIZE * zoom))

            self._scaled = [
                pygame.transform.scale(f, (px, px)) for f in self.frames
            ]

            self._scaled_hit = pygame.transform.scale(self.hit, (px, px))

            self._zoom = zoom

        return self._scaled, self._scaled_hit


class Enemy:
    """Persigue al jugador, le pega al chocarlo y rebota por toda la
    sala (paredes y obstaculos). Es un objetivo mas de los golpes del
    fosforo (tiene .rect y .take_damage)."""

    # fixed: no se mueve solo (los otros rebotan contra el)
    # contact_damage: te saca vida al tocarte
    fixed = False
    contact_damage = True

    # La sala donde vive (la arena se la cambia segun la sala)
    room = ROOM

    def __init__(self, x, y, hp, max_speed, spawn_delay=0.0):

        self.rect = pygame.Rect(0, 0, *ENEMY_HITBOX)
        self.rect.center = (round(x), round(y))

        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2()

        self.hp = hp
        self.max_hp = hp
        self.max_speed = max_speed

        # Velocidad de "bola": rebota siempre a este ritmo
        self.ball_speed = max_speed * ENEMY_BALL_MULT

        self.flash = 0.0
        self.stun = 0.0
        self.touch_cd = 0.0

        # Mientras es > 0 el enemigo esta apareciendo: no se mueve,
        # no hace dano y tampoco se lo puede golpear
        self.spawn_t = ENEMY_SPAWN_TIME + spawn_delay

        self.anim_t = random.uniform(0, 1)
        self.last_target = pygame.Vector2(x, y)

        # Para dibujarlo rodando y saltando como una pelota
        self.spin = random.uniform(0, 360)
        self.hop_t = random.uniform(0, 1)

    @property
    def dead(self):

        return self.hp <= 0

    @property
    def spawning(self):

        return self.spawn_t > 0

    # ---------- golpes ----------

    def take_damage(self, amount):

        if self.spawning or self.dead:
            return 0

        self.hp -= amount
        self.flash = ENEMY_FLASH_TIME
        self.stun = ENEMY_STUN_TIME

        # Empujon hacia atras, lejos del jugador
        away = self.pos - self.last_target

        if away.length_squared() > 0.01:
            self.vel = away.normalize() * ENEMY_KNOCKBACK

        return amount

    def bounce_from(self, point):
        """Sale rebotado despues de chocar al jugador."""

        away = self.pos - pygame.Vector2(point)

        if away.length_squared() < 0.01:
            away = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

        self.vel = away.normalize() * self.ball_speed * ENEMY_HIT_BOUNCE
        self.touch_cd = ENEMY_TOUCH_COOLDOWN

    # ---------- movimiento ----------

    def update(self, dt, target, collision_map, others=None):
        """Es una pelota: NO camina ni gira hacia el jugador. Va en
        linea recta y solo cambia de direccion al rebotar (contra las
        paredes, los bloques del mapa o otro enemigo). En cada rebote
        sale apuntando hacia donde esta el jugador, asi siempre rebota
        cerca suyo para pegarle."""

        self.last_target = pygame.Vector2(target)
        self.anim_t += dt

        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

        if self.touch_cd > 0:
            self.touch_cd = max(0.0, self.touch_cd - dt)

        if self.spawn_t > 0:

            self.spawn_t -= dt

            return

        to_target = pygame.Vector2(target) - self.pos

        if self.stun > 0:

            # Empujon del golpe: se frena solo, sin controlarse
            self.stun = max(0.0, self.stun - dt)
            self.vel *= max(0.0, 1.0 - ENEMY_DRAG * dt)

        else:

            self._keep_speed(dt, to_target)

        before = self.pos.copy()

        hit_x, hit_y = self._move(dt, collision_map)

        if hit_x or hit_y:
            self.aim_after_bounce(to_target, hit_x, hit_y)

        # Si quedo incrustado en una pared (spawn o empujon), lo saca
        if not self._free(self.rect, collision_map):
            self._rescue(collision_map)

        # Rueda y salta segun lo que recorrio (no camina)
        moved = self.pos.distance_to(before)
        side = 1.0 if self.vel.x >= 0 else -1.0

        self.spin = (self.spin + side * moved * ENEMY_SPIN_RATE) % 360.0
        self.hop_t = (self.hop_t + moved / ENEMY_HOP_DIST) % 1.0

    def _keep_speed(self, dt, to_target):
        """Mantiene la velocidad de bola SIN cambiar la direccion."""

        speed = self.vel.length()

        # Recien aparecido (o frenado del todo): sale disparado hacia
        # el jugador, y de ahi en adelante solo rebota
        if speed < 1.0:

            if to_target.length_squared() > 0.01:
                direction = to_target.normalize()
            else:
                direction = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

            direction = direction.rotate(
                random.uniform(-ENEMY_BOUNCE_JITTER, ENEMY_BOUNCE_JITTER)
            )

            self.vel = direction * self.ball_speed

            return

        if speed < self.ball_speed:
            speed = min(self.ball_speed, speed + ENEMY_ACCEL * dt)
        else:
            speed = max(self.ball_speed, speed - ENEMY_ACCEL * dt)

        self.vel.scale_to_length(speed)

    def aim_after_bounce(self, to_target, hit_x, hit_y, away=None):
        """Despues de rebotar, la direccion del rebote se acerca a la
        direccion hacia el jugador (sin volver a meterse en la pared
        que acaba de tocar)."""

        speed = self.vel.length()

        if speed < 1.0 or to_target.length_squared() < 0.01:
            return

        current = self.vel / speed
        want = to_target.normalize()

        mix = current * (1.0 - ENEMY_BOUNCE_AIM) + want * ENEMY_BOUNCE_AIM

        if mix.length_squared() < 0.0001:
            return

        mix = mix.normalize().rotate(
            random.uniform(-ENEMY_BOUNCE_JITTER, ENEMY_BOUNCE_JITTER)
        )

        # Nunca apuntar de nuevo contra la pared que acaba de tocar
        if hit_x and mix.x * current.x < 0:
            mix.x = current.x * 0.3

        if hit_y and mix.y * current.y < 0:
            mix.y = current.y * 0.3

        # Ni contra el enemigo con el que acaba de chocar
        if away is not None and mix.dot(away) < 0:
            mix = mix - away * mix.dot(away) + away * 0.3

        if mix.length_squared() < 0.0001:
            return

        self.vel = mix.normalize() * speed

    def _free(self, rect, collision_map):
        """True si el enemigo puede estar en `rect`: dentro de la sala
        (no se escapa por el pasillo) y sin tocar paredes ni bloques."""

        return self.room.contains(rect) and collision_map.can_move(rect)

    def _move(self, dt, collision_map):
        """Mueve al enemigo y rebota contra paredes y bloques del mapa.
        Devuelve (choco_en_x, choco_en_y)."""

        hit_x = False
        hit_y = False

        # Eje X
        nx = self.pos.x + self.vel.x * dt
        test = self.rect.copy()
        test.centerx = round(nx)

        if self._free(test, collision_map):

            self.pos.x = nx
            self.rect.centerx = test.centerx

        else:

            hit_x = True
            self.vel.x = -self.vel.x * WALL_BOUNCE

        # Eje Y
        ny = self.pos.y + self.vel.y * dt
        test = self.rect.copy()
        test.centery = round(ny)

        if self._free(test, collision_map):

            self.pos.y = ny
            self.rect.centery = test.centery

        else:

            hit_y = True
            self.vel.y = -self.vel.y * WALL_BOUNCE

        return hit_x, hit_y

    def push(self, offset, collision_map):
        """Mueve al enemigo `offset` (para separarlo de otro), solo si
        hay lugar. Prueba cada eje por separado."""

        nx = self.pos.x + offset.x
        test = self.rect.copy()
        test.centerx = round(nx)

        if self._free(test, collision_map):
            self.pos.x = nx
            self.rect.centerx = test.centerx

        ny = self.pos.y + offset.y
        test = self.rect.copy()
        test.centery = round(ny)

        if self._free(test, collision_map):
            self.pos.y = ny
            self.rect.centery = test.centery


    # ---------- navegacion y anti-atasco ----------

    NAV_REPLAN = 0.35        # cada cuanto recalcula el camino (seg)
    STUCK_CHECK = 0.25       # cada cuanto mide si avanzo (seg)
    STUCK_MIN_MOVE = 1.2     # menos que esto en STUCK_CHECK = no avanza

    def _nav_init(self):
        """Prepara el estado de navegacion la primera vez que se usa."""

        if getattr(self, "_nav_ready", False):
            return

        self._nav_ready = True
        self._nav_path = []
        self._nav_t = 0.0
        self._nav_force = 0.0

        self._stk_pos = self.pos.copy()
        self._stk_clock = 0.0
        self._stk_time = 0.0
        self._stk_stage = 0

        self._esc_t = 0.0
        self._esc_dir = pygame.Vector2()

        self.last_good = self.pos.copy()

    def _body_line_free(self, a, b, collision_map):
        """True si el cuerpo del enemigo puede ir en linea recta de a a b."""

        a = pygame.Vector2(a)
        b = pygame.Vector2(b)

        steps = max(1, int(a.distance_to(b) // 3))

        probe = self.rect.copy()

        for i in range(1, steps + 1):

            p = a.lerp(b, i / steps)

            probe.center = (round(p.x), round(p.y))

            if not self._free(probe, collision_map):
                return False

        return True

    def nav_dir(self, goal, collision_map, dt):
        """Direccion (unitaria) para ir hacia `goal` rodeando paredes.
        Si el camino esta libre va derecho; si no, sigue un camino A*
        que se recalcula cada NAV_REPLAN segundos."""

        self._nav_init()

        goal = pygame.Vector2(goal)

        self._nav_t -= dt
        self._nav_force = max(0.0, self._nav_force - dt)

        if self._nav_t <= 0:

            self._nav_t = self.NAV_REPLAN

            if (
                self._nav_force <= 0
                and self._body_line_free(self.pos, goal, collision_map)
            ):
                self._nav_path = []

            else:

                path = pathing.find_path(
                    self.pos, goal, self.rect.size, self.room, collision_map
                )

                self._nav_path = path or []

        # Ya llego a los puntos de adelante: se descartan
        while self._nav_path and self.pos.distance_to(self._nav_path[0]) < 4.0:
            self._nav_path.pop(0)

        # Atajo: si ve el siguiente punto en linea recta, saltea el actual
        if len(self._nav_path) > 1 and self._body_line_free(
            self.pos, self._nav_path[1], collision_map
        ):
            self._nav_path.pop(0)

        aim = pygame.Vector2(self._nav_path[0]) if self._nav_path else goal

        d = aim - self.pos

        if d.length_squared() < 0.01:
            d = goal - self.pos

        if d.length_squared() < 0.01:
            return pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

        return d.normalize()

    def _nudge(self, dt, direction, speed, collision_map):
        """Empuja al enemigo un poco hacia `direction` (si hay lugar)."""

        step = speed * dt

        for angle in (0, 45, -45):

            d = direction.rotate(angle)

            test = self.rect.copy()
            test.center = (
                round(self.pos.x + d.x * step),
                round(self.pos.y + d.y * step),
            )

            if self._free(test, collision_map):

                self.pos.update(
                    self.pos.x + d.x * step, self.pos.y + d.y * step
                )
                self.rect.center = test.center

                return True

        return False

    def _random_open_dir(self, collision_map):
        """Una direccion con lugar libre adelante (la prueba al azar)."""

        angles = list(range(0, 360, 45))
        random.shuffle(angles)

        for angle in angles:

            d = pygame.Vector2(1, 0).rotate(angle)

            test = self.rect.copy()
            test.center = (
                round(self.pos.x + d.x * 8),
                round(self.pos.y + d.y * 8),
            )

            if self._free(test, collision_map):
                return d

        return pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

    def _teleport(self, point):

        self.pos.update(point[0], point[1])
        self.rect.center = (round(point[0]), round(point[1]))

        self.vel = pygame.Vector2()
        self._nav_path = []
        self._nav_t = 0.0

    def _rescue(self, collision_map):
        """Lo saca al lugar libre mas cercano (incrustado o atascado)."""

        self._nav_init()

        spot = pathing.nearest_free(
            self.last_good, self.rect.size, self.room, collision_map
        )

        # Si el ultimo lugar bueno es justo donde esta atascado, busca
        # desde donde esta ahora
        if spot is None or self.pos.distance_to(spot) < 3.0:

            spot = pathing.nearest_free(
                self.pos, self.rect.size, self.room, collision_map
            )

        if spot is not None and self.pos.distance_to(spot) >= 3.0:
            self._teleport(spot)

        self._stk_time = 0.0
        self._stk_stage = 0
        self._stk_pos = self.pos.copy()

    def anti_stuck(self, dt, collision_map, goal=None, speed=40.0):
        """Llamar CADA frame mientras el enemigo esta tratando de
        caminar. Si no avanza, lo destraba en etapas:

          0.5 s -> fuerza recalcular el camino y se desliza de costado
          1.5 s -> prueba otra direccion libre
          3.0 s -> lo saca al lugar libre mas cercano

        Devuelve True cuando acaba de detectar un atasco (asi quien
        lo llama puede cambiar de rumbo)."""

        self._nav_init()

        # Incrustado en una pared: afuera ya
        if not self._free(self.rect, collision_map):

            self._rescue(collision_map)

            return True

        # Se esta deslizando para salir del atasco
        if self._esc_t > 0:

            self._esc_t -= dt
            self._nudge(dt, self._esc_dir, speed, collision_map)

        self._stk_clock += dt

        if self._stk_clock < self.STUCK_CHECK:
            return False

        self._stk_clock = 0.0

        moved = self.pos.distance_to(self._stk_pos)
        self._stk_pos = self.pos.copy()

        # Ya esta encima del objetivo: no es un atasco
        if goal is not None and self.pos.distance_to(goal) < 14.0:

            self._stk_time = 0.0
            self._stk_stage = 0

            return False

        if moved >= self.STUCK_MIN_MOVE:

            self._stk_time = 0.0
            self._stk_stage = 0
            self.last_good = self.pos.copy()

            return False

        self._stk_time += self.STUCK_CHECK

        if self._stk_time >= 3.0:

            self._rescue(collision_map)

            return True

        if self._stk_time >= 1.5 and self._stk_stage < 2:

            self._stk_stage = 2
            self._esc_dir = self._random_open_dir(collision_map)
            self._esc_t = 0.8
            self._nav_force = 2.0
            self._nav_t = 0.0

            return True

        if self._stk_time >= 0.5 and self._stk_stage < 1:

            self._stk_stage = 1
            self._esc_dir = self._random_open_dir(collision_map)
            self._esc_t = 0.45
            self._nav_force = 1.5
            self._nav_t = 0.0

            return True

        return False

    # ---------- dibujo ----------

    def draw(self, screen, camera, art):

        frames, hit = art.get(camera.zoom)

        if self.flash > 0:

            img = hit

        else:

            # Sin animacion de caminar: es una pelota, usa un solo
            # cuadro y se lo hace rodar
            img = frames[0]

            # Herido = mas oscuro (asi se nota sin barras de vida)
            if self.hp < self.max_hp:

                shade = int(255 * (0.55 + 0.45 * self.hp / self.max_hp))

                img = img.copy()
                img.fill(
                    (shade, shade, shade, 255),
                    special_flags=pygame.BLEND_RGBA_MULT
                )

        if not self.spawning:
            img = pygame.transform.rotate(img, self.spin)

        if self.spawning:

            k = 1.0 - max(0.0, self.spawn_t) / ENEMY_SPAWN_TIME

            img = img.copy()
            img.set_alpha(int(50 + 150 * max(0.0, min(1.0, k))))

        dest = camera.apply(self.rect)

        # Saltito (la sombra se queda en el piso)
        hop = 0
        if not self.spawning:
            hop = int(
                abs(math.sin(self.hop_t * math.pi))
                * ENEMY_HOP_HEIGHT * camera.zoom
            )

        # Sombra
        shadow = pygame.Surface(
            (int(dest.width * 1.3), int(dest.height * 0.6)),
            pygame.SRCALPHA
        )

        pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())

        screen.blit(
            shadow,
            shadow.get_rect(center=(dest.centerx, dest.bottom))
        )

        screen.blit(
            img,
            img.get_rect(
                center=(dest.centerx, dest.centery - hop)
            )
        )


def _overlap_depth(a, b):
    """Cuanto se pisan dos rects (para separarlos)."""

    overlap_x = min(a.rect.right, b.rect.right) - max(a.rect.left, b.rect.left)
    overlap_y = min(a.rect.bottom, b.rect.bottom) - max(a.rect.top, b.rect.top)

    return max(1.0, min(overlap_x, overlap_y))


def bounce_enemies(enemies, collision_map, target=None):
    """Choque entre enemigos: si se tocan, rebotan hacia otro lado y
    se separan para no quedar pegados. Los troncos no se mueven: el
    pino rebota contra ellos como contra una pared. Si se pasa `target`
    (posicion del jugador) cada uno se reorienta hacia el despues del
    choque."""

    live = [e for e in enemies if not e.spawning and not e.dead and not getattr(e, "attached", False)]

    for i, a in enumerate(live):

        for b in live[i + 1:]:

            if not a.rect.colliderect(b.rect):
                continue

            normal = b.pos - a.pos

            if normal.length_squared() < 0.01:
                normal = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

            normal = normal.normalize()

            # Dos troncos: solo se separan
            if a.fixed and b.fixed:

                depth = _overlap_depth(a, b) / 2.0 + 1.0

                a.push(-normal * depth, collision_map)
                b.push(normal * depth, collision_map)

                continue

            # Un tronco y un pino: el pino rebota contra el tronco
            if a.fixed or b.fixed:

                mobile, wall = (b, a) if a.fixed else (a, b)

                away = mobile.pos - wall.pos

                if away.length_squared() < 0.01:
                    away = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

                away = away.normalize()

                closing = mobile.vel.dot(away)

                if closing < 0:

                    mobile.vel -= away * (2.0 * closing)

                    if target is not None:

                        mobile.aim_after_bounce(
                            pygame.Vector2(target) - mobile.pos,
                            False, False, away
                        )

                mobile.push(away * (_overlap_depth(a, b) + 1.0), collision_map)

                continue

            # Dos pinos: choque elastico entre iguales (intercambian la
            # velocidad que llevaban uno contra el otro)
            closing = (a.vel - b.vel).dot(normal)

            if closing > 0:

                a.vel -= normal * closing
                b.vel += normal * closing

                # Si quedaron casi quietos, se empujan igual
                for e, sign in ((a, -1), (b, 1)):

                    if e.vel.length() < 40:
                        e.vel = normal * sign * max(40.0, e.ball_speed * 0.6)

                if target is not None:

                    a.aim_after_bounce(
                        pygame.Vector2(target) - a.pos, False, False, -normal
                    )
                    b.aim_after_bounce(
                        pygame.Vector2(target) - b.pos, False, False, normal
                    )

            # Separarlos para que no queden uno dentro del otro
            depth = _overlap_depth(a, b) / 2.0 + 1.0

            a.push(-normal * depth, collision_map)
            b.push(normal * depth, collision_map)


# ---------------------------------------------------------------
# Imagenes del tronco y de la bola (opcionales: si falta alguna se
# dibuja un reemplazo)
# ---------------------------------------------------------------

def load_strip(path):
    """Tira horizontal de cuadros cuadrados (ancho de cuadro = alto).
    Devuelve la lista de cuadros, o [] si no existe el archivo."""

    sheet = load_image(path)

    if sheet is None or sheet.get_height() <= 0:
        return []

    fw = sheet.get_height()

    return [
        sheet.subsurface((i * fw, 0, fw, fw)).copy()
        for i in range(max(1, sheet.get_width() // fw))
    ]

class Mosquito(Enemy):
    """Ciclo: vuela tranquilo -> la luz lo toca y va directo al jugador ->
    se pega 1 minuto -> se suelta e intenta irse -> a los 60 s vuelve a
    chuparte (sin necesitar la luz) -> y asi."""

    fixed = False
    contact_damage = False

    def __init__(self, x, y, hp, spawn_delay=0.0):

        super().__init__(x, y, hp, MOSQUITO_ATTACK_SPEED, spawn_delay)

        self.rect = pygame.Rect(0, 0, *MOSQUITO_HITBOX)
        self.rect.center = (round(x), round(y))

        # "wander" = vuela tranquilo esperando que lo toque la luz
        # "attack" = va directo al jugador
        # "leave"  = ya te solto: se va y descansa hasta volver
        self.phase = "wander"

        self.heading = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))
        self.turn_t = random.uniform(*MOSQUITO_TURN_TIME)

        self.attack_vel = pygame.Vector2()
        self.flash = 0.0

        self.attached = False
        self.attach_offset = pygame.Vector2()
        self.attach_t = 0.0

        self.rest_t = 0.0
        self.flee_t = 0.0

        # True si vuelve solo (no lo toco la luz)
        self.returning = False

        # True mientras esta cerca del jugador y viene a chuparlo pero
        # todavia no se pego (el HUD muestra la advertencia)
        self.alert = False

        self.damage_t = random.uniform(0, MOSQUITO_DAMAGE_INTERVAL)
        self.anim_t = random.uniform(0, 1)

    @property
    def dead(self):

        return self.hp <= 0

    @property
    def spawning(self):

        return self.spawn_t > 0

    def take_damage(self, amount):

        # Un mosquito pegado NO puede recibir ataques
        if self.spawning or self.dead or self.attached:
            return 0

        self.hp -= amount
        self.flash = MOSQUITO_FLASH_TIME

        # Si todavia no te chupo y lo golpean, ataca. Si ya se estaba
        # yendo, sigue yendose.
        if self.phase == "wander":
            self._start_attack()

        return amount

    def _repelled(self, target, light_radius, dt, collision_map):
        """Con repelente, los mosquitos dentro del area de la luz se
        alejan: si estaban pegados se sueltan, y si venian a atacar se
        dan vuelta. Devuelve True si este cuadro ya se movio asi."""

        if self.attached:

            # Pegado = esta encima tuyo, o sea adentro de la luz
            self._detach(target)

            self.rest_t = max(self.rest_t, MOSQUITO_REPEL_REST)

            return True

        away = self.pos - target
        dist = away.length()

        if dist > light_radius:
            return False

        if dist < 0.01:
            away = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))
        else:
            away = away / dist

        self.alert = False
        self.returning = False
        self.phase = "leave"
        self.rest_t = max(self.rest_t, MOSQUITO_REPEL_REST)
        self.flee_t = max(self.flee_t, MOSQUITO_REPEL_FLEE)

        self.heading = away

        self._wander(dt, collision_map, MOSQUITO_FLEE_SPEED, turn=False)

        return True

    def _start_attack(self):

        self.phase = "attack"

        to_player = self.last_target - self.pos

        if to_player.length_squared() < 0.01:
            to_player = pygame.Vector2(1, 0)

        self.attack_vel = to_player.normalize() * MOSQUITO_ATTACK_SPEED

    def _detach(self, target):

        self.attached = False
        self.phase = "leave"
        self.rest_t = MOSQUITO_REST_TIME
        self.flee_t = MOSQUITO_FLEE_TIME
        self.returning = False

        away = self.pos - target

        if away.length_squared() < 0.01:
            away = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

        self.heading = away.normalize()
        self.turn_t = random.uniform(*MOSQUITO_TURN_TIME)

    def update(self, dt, target, collision_map, light_on, light_radius,
               repel=False):

        target = pygame.Vector2(target)
        self.last_target = target.copy()

        self.anim_t += dt

        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

        if self.spawning:
            self.spawn_t -= dt
            return

        # -------------------------------------------------------
        # REPELENTE: el area de la luz los espanta (no los mata)
        # -------------------------------------------------------

        if repel and self._repelled(target, light_radius, dt, collision_map):
            return

        # -------------------------------------------------------
        # PEGADO: te chupa 1 minuto y despues se suelta
        # -------------------------------------------------------

        if self.attached:

            self.alert = False
            self.attach_t -= dt
            self.damage_t -= dt

            self.pos = target + self.attach_offset
            self.rect.center = (round(self.pos.x), round(self.pos.y))

            if self.attach_t <= 0:
                self._detach(target)

            return

        to_player = target - self.pos
        dist = max(0.01, to_player.length())
        toward = to_player / dist

        # -------------------------------------------------------
        # ATAQUE: va directo al jugador y se pega
        # -------------------------------------------------------

        if self.phase == "attack":

            # Si vuelve solo, avisa en el HUD hasta que se pega
            self.alert = self.returning

            desired = toward * MOSQUITO_ATTACK_SPEED

            self.attack_vel += (desired - self.attack_vel) * min(
                1.0,
                MOSQUITO_ATTACK_ACCEL * dt / max(1.0, MOSQUITO_ATTACK_SPEED)
            )

            self.vel = self.attack_vel.copy()
            self._move(dt, collision_map)

            if self.pos.distance_to(target) <= MOSQUITO_ATTACH_DIST:

                self.attached = True
                self.alert = False
                self.attach_t = MOSQUITO_ATTACH_TIME

                offset = self.pos - target

                if offset.length_squared() < 0.01:
                    offset = pygame.Vector2(0, -10)

                if offset.length() > 16:
                    offset.scale_to_length(16)

                self.attach_offset = offset
                self.vel = pygame.Vector2()
                self.attack_vel = pygame.Vector2()
                self.damage_t = MOSQUITO_DAMAGE_INTERVAL

            return

        # -------------------------------------------------------
        # SE FUE: se aleja y despues vuela tranquilo hasta que
        # pasa el minuto y vuelve a chuparte
        # -------------------------------------------------------

        if self.phase == "leave":

            self.alert = False
            self.rest_t -= dt

            if self.rest_t <= 0:

                self.returning = True
                self._start_attack()

                return

            if self.flee_t > 0:

                self.flee_t -= dt

                # Se aleja del jugador
                self.heading = -toward

                self._wander(dt, collision_map, MOSQUITO_FLEE_SPEED, turn=False)

            else:

                self._wander(dt, collision_map, MOSQUITO_WANDER_SPEED)

            return

        # -------------------------------------------------------
        # VUELO LIBRE: tranquilo por el mapa (no huye de la luz)
        # -------------------------------------------------------

        # Lo toca tu luz -> va directo hacia vos
        if light_on and dist <= light_radius:

            self.alert = False
            self._start_attack()

            return

        # Advertencia en el HUD: esta cerca pero todavia no lo toca la luz
        self.alert = light_on and dist <= light_radius + MOSQUITO_ALERT_MARGIN

        self._wander(dt, collision_map, MOSQUITO_WANDER_SPEED)

    def _wander(self, dt, collision_map, speed, turn=True):

        if turn:

            self.turn_t -= dt

            if self.turn_t <= 0:

                self.heading = self.heading.rotate(random.uniform(-70, 70))
                self.turn_t = random.uniform(*MOSQUITO_TURN_TIME)

        step = speed * dt

        # Si choca con algo, prueba otros rumbos hasta encontrar uno libre
        for angle in (0, 40, -40, 90, -90, 140, -140, 180):

            d = self.heading.rotate(angle)

            nx = self.pos.x + d.x * step
            ny = self.pos.y + d.y * step

            test = self.rect.copy()
            test.center = (round(nx), round(ny))

            if self._free(test, collision_map):

                self.pos.update(nx, ny)
                self.rect.center = test.center

                if angle:
                    self.heading = d
                    self.turn_t = random.uniform(*MOSQUITO_TURN_TIME)

                return

    def draw(self, screen, camera, art):

        frames, _ = art.get(camera.zoom)

        frame = frames[int(self.anim_t / MOSQUITO_ANIM_FRAME) % len(frames)]

        if self.attached:

            frame = pygame.transform.smoothscale(
                frame,
                (max(1, int(frame.get_width() * 0.85)),
                 max(1, int(frame.get_height() * 0.85)))
            )

            center = camera.apply(self.rect).center
            screen.blit(frame, frame.get_rect(center=center))

            return

        if self.flash > 0:
            frame = frame.copy()
            frame.fill((255, 255, 255, 90), special_flags=pygame.BLEND_RGBA_ADD)

        dest = camera.apply(self.rect)
        screen.blit(frame, frame.get_rect(center=dest.center))

class TroncoArt:
    """Imagenes del tronco y de sus bolas (se cargan una sola vez).

      assets/maps/combate/tronco.png          56x56   (reposo)
      assets/maps/combate/tronco_carga.png    56x56 o tira de cuadros 56x56
      assets/maps/combate/tronco_disparo.png  tira de cuadros 56x56 (4)
      assets/maps/combate/tronco_golpe.png    56x56   (cuando le pegas)
      assets/maps/combate/bola_enemiga.png    24x24   (la bola)
    """

    def __init__(self):

        idle = load_strip(COMBAT_DIR / "tronco.png")
        charge = load_strip(COMBAT_DIR / "tronco_carga.png")
        shoot = load_strip(COMBAT_DIR / "tronco_disparo.png")
        hit = load_image(COMBAT_DIR / "tronco_golpe.png")
        shot = load_image(COMBAT_DIR / "bola_enemiga.png")

        self.idle = idle or [self._placeholder("idle")]
        self.charge = charge or [
            self._placeholder("charge", k) for k in (0.4, 1.0)
        ]
        self.shoot = shoot or [
            self._placeholder("shoot", k) for k in (0.0, 0.5, 1.0)
        ]

        if hit is None:

            hit = self.idle[0].copy()
            hit.fill((170, 170, 170, 0), special_flags=pygame.BLEND_RGB_ADD)

        self.hit = hit
        self.shot = shot if shot is not None else self._shot_placeholder()

        self._zoom = None
        self._scaled = None

    @staticmethod
    def _placeholder(mode, k=0.0):

        surf = pygame.Surface((56, 56), pygame.SRCALPHA)

        # cuerpo del tronco
        pygame.draw.rect(surf, (118, 78, 44), (12, 8, 32, 44), border_radius=6)
        pygame.draw.rect(surf, (60, 36, 18), (12, 8, 32, 44), 3, border_radius=6)
        pygame.draw.line(surf, (80, 50, 26), (20, 14), (20, 46), 2)
        pygame.draw.line(surf, (80, 50, 26), (36, 14), (36, 46), 2)

        # ojos
        pygame.draw.circle(surf, (20, 10, 10), (22, 20), 3)
        pygame.draw.circle(surf, (20, 10, 10), (34, 20), 3)

        # boca: se abre y se pone naranja cuando carga o dispara
        mouth_h = 4 + int(10 * k) if mode != "idle" else 3
        color = (20, 10, 10) if mode == "idle" else (
            255, int(140 - 80 * k), 40
        )

        pygame.draw.ellipse(
            surf, color, (22, 30, 12, mouth_h)
        )

        return surf

    @staticmethod
    def _shot_placeholder():

        surf = pygame.Surface((24, 24), pygame.SRCALPHA)

        pygame.draw.circle(surf, (255, 90, 40, 110), (12, 12), 12)
        pygame.draw.circle(surf, (255, 150, 60), (12, 12), 8)
        pygame.draw.circle(surf, (255, 235, 170), (12, 12), 4)

        return surf

    def get(self, zoom):
        """Todo ya escalado al zoom actual."""

        if self._zoom != zoom:

            tpx = max(1, int(TRONCO_DRAW_SIZE * zoom))
            spx = max(1, int(SHOT_DRAW_SIZE * zoom))

            def scale(frames):
                return [pygame.transform.scale(f, (tpx, tpx)) for f in frames]

            self._scaled = {
                "idle": scale(self.idle),
                "charge": scale(self.charge),
                "shoot": scale(self.shoot),
                "hit": pygame.transform.scale(self.hit, (tpx, tpx)),
                "shot": pygame.transform.scale(self.shot, (spx, spx)),
            }

            self._zoom = zoom

        return self._scaled


# ---------------------------------------------------------------
# Bola que dispara el tronco
# ---------------------------------------------------------------

class Shot:
    """Bola que rebota SHOT_BOUNCES veces contra las paredes y los
    bloques del mapa; al siguiente choque desaparece. Si te toca, te
    saca vida y desaparece."""

    room = ROOM

    def __init__(self, pos, angle):

        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(SHOT_SPEED, 0).rotate(angle)

        self.rect = pygame.Rect(0, 0, SHOT_HITBOX, SHOT_HITBOX)
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        self.bounces_left = SHOT_BOUNCES
        self.life = SHOT_LIFE
        self.t = 0.0
        self.dead = False

    def _free(self, rect, collision_map):

        return self.room.contains(rect) and collision_map.can_move(rect)

    def update(self, dt, collision_map):

        self.t += dt
        self.life -= dt

        if self.life <= 0:

            self.dead = True

            return

        hit = False

        # Eje X
        nx = self.pos.x + self.vel.x * dt
        test = self.rect.copy()
        test.centerx = round(nx)

        if self._free(test, collision_map):

            self.pos.x = nx
            self.rect.centerx = test.centerx

        else:

            hit = True
            self.vel.x = -self.vel.x

        # Eje Y
        ny = self.pos.y + self.vel.y * dt
        test = self.rect.copy()
        test.centery = round(ny)

        if self._free(test, collision_map):

            self.pos.y = ny
            self.rect.centery = test.centery

        else:

            hit = True
            self.vel.y = -self.vel.y

        if hit:

            # Los dos primeros choques rebotan, el tercero la rompe
            if self.bounces_left <= 0:
                self.dead = True
            else:
                self.bounces_left -= 1

    def draw(self, screen, camera, art):

        img = art.get(camera.zoom)["shot"]

        # Late un poco para que se note en la oscuridad
        pulse = 0.85 + 0.15 * math.sin(self.t * 14)

        size = max(1, int(img.get_width() * pulse))

        if size != img.get_width():
            img = pygame.transform.scale(img, (size, size))

        center = camera.apply(self.rect).center

        screen.blit(img, img.get_rect(center=center))


# ---------------------------------------------------------------
# Tronco
# ---------------------------------------------------------------

class Tronco(Enemy):
    """Te sigue por la sala pero manteniendo distancia: si te acercas
    retrocede, y se queda siempre afuera del borde de tu luz para que
    no lo veas. Cuando le toca disparar (cada TRONCO_COOLDOWN segundos)
    se queda quieto apuntandote y suelta 3 bolas abiertas en abanico
    hacia donde te podrias mover. Despues hace la animacion de disparo
    y vuelve a seguirte.
    Si le pegas mientras carga se le corta el disparo.
    No te hace dano al tocarlo."""

    # fixed: es el tipo que dispara (los pinos rebotan contra el)
    fixed = True
    contact_damage = False

    IDLE = "idle"
    WINDUP = "windup"
    SHOOT = "shoot"

    def __init__(self, x, y, hp, spawn_delay=0.0):

        super().__init__(x, y, hp, TRONCO_SPEED, spawn_delay)

        self.rect = pygame.Rect(0, 0, *TRONCO_HITBOX)
        self.rect.center = (round(x), round(y))

        self.phase = self.IDLE
        self.phase_t = random.uniform(*TRONCO_FIRST_DELAY)

        # Radio de la luz del jugador en unidades del mundo (lo setea
        # la arena en cada frame)
        self.light_radius = 0.0

        # Velocidad del jugador (para adelantar la punteria)
        self.target_vel = pygame.Vector2()
        self._prev_target = None

        self._shots = []

    # ---------- golpes ----------

    def take_damage(self, amount):

        result = super().take_damage(amount)

        # Le pegaste mientras cargaba: se le corta el disparo
        if result and self.phase == self.WINDUP:

            self.phase = self.IDLE
            self.phase_t = TRONCO_HIT_PAUSE

        return result

    # ---------- disparo ----------

    def take_shots(self):
        """Las bolas que acaba de soltar (y se vacia la lista)."""

        shots, self._shots = self._shots, []

        return shots

    def _fire(self, target):

        # Hacia donde vas a estar: la posicion de ahora mas lo que te
        # moves en TRONCO_LEAD segundos (sin salirse de la sala)
        aim = pygame.Vector2(target) + self.target_vel * TRONCO_LEAD

        aim.x = max(self.room.left + 4, min(self.room.right - 4, aim.x))
        aim.y = max(self.room.top + 4, min(self.room.bottom - 4, aim.y))

        direction = aim - self.pos

        if direction.length_squared() < 0.01:
            direction = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

        base = pygame.Vector2(1, 0).angle_to(direction)

        for k in range(TRONCO_SHOTS):

            offset = (k - (TRONCO_SHOTS - 1) / 2.0) * TRONCO_SPREAD

            shot = Shot(self.pos, base + offset)
            shot.room = self.room
            self._shots.append(shot)

    # ---------- movimiento / estado ----------

    def _ideal_distance(self):
        """A que distancia del jugador quiere estar: afuera de su luz
        (para que no lo vea) y nunca mas cerca que TRONCO_KEEP_DIST."""

        want = max(
            TRONCO_KEEP_DIST, self.light_radius + TRONCO_LIGHT_MARGIN
        )

        return min(TRONCO_MAX_DIST, want)

    def _walk(self, dt, direction, collision_map):
        """Camina hacia `direction`. Si hay una pared o un bloque
        adelante, prueba rodearlo en diagonal o de costado."""

        step = TRONCO_SPEED * dt

        for angle in (0, 45, -45, 90, -90):

            d = direction.rotate(angle)

            nx = self.pos.x + d.x * step
            ny = self.pos.y + d.y * step

            test = self.rect.copy()
            test.center = (round(nx), round(ny))

            if self._free(test, collision_map):

                self.pos.update(nx, ny)
                self.rect.center = test.center

                return True

        return False

    def update(self, dt, target, collision_map, others=None):

        target = pygame.Vector2(target)

        self.last_target = target.copy()
        self.anim_t += dt

        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

        if self.touch_cd > 0:
            self.touch_cd = max(0.0, self.touch_cd - dt)

        if self.spawn_t > 0:

            self.spawn_t -= dt
            self._prev_target = target

            return

        # Velocidad del jugador, suavizada
        if self._prev_target is not None and dt > 0:

            raw = (target - self._prev_target) / dt

            self.target_vel += (raw - self.target_vel) * min(1.0, dt * 8.0)

        self._prev_target = target

        # Empujon del golpe: se desliza un poco y se frena
        if self.stun > 0:

            self.stun = max(0.0, self.stun - dt)
            self.vel *= max(0.0, 1.0 - 6.0 * dt)

            hit_x, hit_y = self._move(dt, collision_map)

            if hit_x or hit_y:
                self.vel = pygame.Vector2()

            return

        self.vel = pygame.Vector2()

        # ---- apuntando: quieto, mirandote hasta soltar las bolas ----
        if self.phase == self.WINDUP:

            self.phase_t -= dt

            if self.phase_t <= 0:

                self._fire(target)

                self.phase = self.SHOOT
                self.phase_t = TRONCO_SHOOT_TIME

            return

        # ---- animacion de disparo: tambien quieto ----
        if self.phase == self.SHOOT:

            self.phase_t -= dt

            if self.phase_t <= 0:

                self.phase = self.IDLE
                self.phase_t = TRONCO_COOLDOWN

            return

        # ---- siguiendote (esperando el proximo disparo) ----
        self.phase_t = max(0.0, self.phase_t - dt)

        to_player = target - self.pos
        dist = to_player.length()

        if dist < 0.01:
            to_player = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))
            dist = 0.01

        toward = to_player / dist

        ideal = self._ideal_distance()

        if dist > ideal + TRONCO_BAND:

            self._walk(
                dt, self.nav_dir(target, collision_map, dt), collision_map
            )

            self.anti_stuck(dt, collision_map, target, TRONCO_SPEED)

        elif dist < ideal - TRONCO_BAND:

            # Muy cerca o adentro de la luz: se aleja
            self._walk(dt, -toward, collision_map)

        # Le toca disparar: cuando ya esta a buena distancia, frena
        # y empieza a apuntar
        if (
            self.phase_t <= 0
            and dist <= ideal + TRONCO_BAND + TRONCO_FIRE_EXTRA
        ):

            self.phase = self.WINDUP
            self.phase_t = TRONCO_WINDUP

    # ---------- dibujo ----------

    def draw(self, screen, camera, art):

        sprites = art.get(camera.zoom)

        shake = 0

        if self.flash > 0:

            img = sprites["hit"]

        else:

            if self.phase == self.WINDUP:

                frames = sprites["charge"]
                index = int(self.anim_t / TRONCO_ANIM_FRAME) % len(frames)

                # Tiembla cada vez mas fuerte hasta soltar las bolas
                k = 1.0 - max(0.0, self.phase_t) / TRONCO_WINDUP
                shake = int(math.sin(self.anim_t * 55) * 1.5 * k * camera.zoom)

            elif self.phase == self.SHOOT:

                frames = sprites["shoot"]
                progress = 1.0 - max(0.0, self.phase_t) / TRONCO_SHOOT_TIME
                index = min(len(frames) - 1, int(progress * len(frames)))

            else:

                frames = sprites["idle"]
                index = int(self.anim_t / (TRONCO_ANIM_FRAME * 4)) % len(frames)

            img = frames[index]

            # Herido = mas oscuro
            if self.hp < self.max_hp:

                shade = int(255 * (0.55 + 0.45 * self.hp / self.max_hp))

                img = img.copy()
                img.fill(
                    (shade, shade, shade, 255),
                    special_flags=pygame.BLEND_RGBA_MULT
                )

        if self.spawning:

            k = 1.0 - max(0.0, self.spawn_t) / ENEMY_SPAWN_TIME

            img = img.copy()
            img.set_alpha(int(50 + 150 * max(0.0, min(1.0, k))))

        dest = camera.apply(self.rect)

        # Sombra
        shadow = pygame.Surface(
            (int(dest.width * 1.3), int(dest.height * 0.6)),
            pygame.SRCALPHA
        )

        pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())

        screen.blit(
            shadow,
            shadow.get_rect(center=(dest.centerx, dest.bottom))
        )

        screen.blit(
            img,
            img.get_rect(
                midbottom=(
                    dest.centerx + shake,
                    dest.bottom + int(2 * camera.zoom)
                )
            )
        )


# ---------------------------------------------------------------
# Hongun
# ---------------------------------------------------------------

class HongunArt:
    """Imagenes del hongun (se cargan una sola vez).

      assets/maps/combate/hongun_anim.png   224x56  (4 cuadros de 56x56, caminar)
      assets/maps/combate/hongun_carga.png  112x56  (2 cuadros de 56x56, recargando)
      assets/maps/combate/hongun.png        56x56   (opcional: un solo cuadro de caminar)
      assets/maps/combate/hongun_golpe.png  56x56   (opcional: cuando le pegas)

    Lo blanco de la recarga lo hace el codigo (parpadea hacia blanco), asi
    que hongun_carga.png se dibuja con los colores normales (hinchado).
    """

    def __init__(self):

        walk = load_strip(COMBAT_DIR / "hongun_anim.png")
        single = load_strip(COMBAT_DIR / "hongun.png")
        charge = load_strip(COMBAT_DIR / "hongun_carga.png")
        hit = load_image(COMBAT_DIR / "hongun_golpe.png")

        self.walk = walk or single or [self._placeholder(0), self._placeholder(1)]
        self.charge = charge or [self.walk[0], self.walk[0]]

        if hit is None:

            hit = self.walk[0].copy()
            hit.fill((170, 170, 170, 0), special_flags=pygame.BLEND_RGB_ADD)

        self.hit = hit

        self._zoom = None
        self._scaled = None

    @staticmethod
    def _placeholder(step=0):

        surf = pygame.Surface((56, 56), pygame.SRCALPHA)

        dark = (40, 120, 50)
        mid = (80, 175, 80)
        light = (120, 205, 110)

        # cuerpo
        pygame.draw.rect(surf, mid, (14, 6, 28, 30))
        pygame.draw.rect(surf, dark, (14, 6, 28, 30), 2)

        # manchas
        for x, y in ((18, 10), (32, 12), (22, 28), (34, 26)):
            pygame.draw.rect(surf, light, (x, y, 6, 6))

        # patas (se alternan para que parezca que camina)
        off = 2 if step % 2 == 0 else -2

        pygame.draw.rect(surf, dark, (14 + off, 36, 12, 14))
        pygame.draw.rect(surf, dark, (30 - off, 36, 12, 14))

        # cara
        pygame.draw.rect(surf, (15, 40, 20), (19, 14, 6, 6))
        pygame.draw.rect(surf, (15, 40, 20), (31, 14, 6, 6))
        pygame.draw.rect(surf, (15, 40, 20), (25, 20, 6, 10))
        pygame.draw.rect(surf, (15, 40, 20), (21, 24, 4, 8))
        pygame.draw.rect(surf, (15, 40, 20), (31, 24, 4, 8))

        return surf

    def get(self, zoom):

        if self._zoom != zoom:

            px = max(1, int(HONGUN_DRAW_SIZE * zoom))

            def scale(frames):
                return [pygame.transform.scale(f, (px, px)) for f in frames]

            self._scaled = {
                "walk": scale(self.walk),
                "charge": scale(self.charge),
                "hit": pygame.transform.scale(self.hit, (px, px)),
            }

            self._zoom = zoom

        return self._scaled


class Hongun(Enemy):
    """Un creeper: pasea tranquilo -> si entras en su area te persigue
    caminando normal -> cuando se acerca se frena y recarga (parpadea
    en blanco, se hincha y da un poco de luz) -> explota: empuja al
    jugador y le saca HONGUN_DAMAGE de vida. Muere al explotar.

    Los golpes le sacan vida pero NO lo empujan ni lo frenan ni le
    cortan la recarga: sigue persiguiendote para explotar. Si te
    alejas mientras recarga, se cancela. Si lo matas a golpes antes
    de que explote, simplemente muere (no explota)."""

    fixed = False
    contact_damage = False

    WANDER = "wander"
    CHASE = "chase"
    FUSE = "fuse"

    def __init__(self, x, y, spawn_delay=0.0):

        super().__init__(x, y, HONGUN_HP, HONGUN_CHASE_SPEED, spawn_delay)

        self.rect = pygame.Rect(0, 0, *HONGUN_HITBOX)
        self.rect.center = (round(x), round(y))

        self.phase = self.WANDER

        self.heading = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))
        self.turn_t = random.uniform(*HONGUN_TURN_TIME)

        self.fuse_t = 0.0      # 0 .. HONGUN_FUSE_TIME
        self.boom = False      # True = acaba de explotar (la arena hace el efecto)
        self.boomed = False

    # ---------- estado ----------

    @property
    def fuse_k(self):
        """0 a 1: cuanto falta para que explote."""

        return max(0.0, min(1.0, self.fuse_t / HONGUN_FUSE_TIME))

    def light(self):
        """(x, y, radio) de la luz que da al recargar, o None."""

        if self.fuse_t <= 0.0 or self.spawning or self.dead:
            return None

        k = self.fuse_k

        return (
            self.pos.x, self.pos.y,
            quantize_radius(
                HONGUN_LIGHT_MIN + (HONGUN_LIGHT_MAX - HONGUN_LIGHT_MIN) * k
            )
        )

    # ---------- golpes ----------

    def take_damage(self, amount):
        """Recibe el dano pero NO retrocede, no se atonta y no se le
        corta la recarga: su mision es explotar mientras te persigue."""

        if self.spawning or self.dead:
            return 0

        self.hp -= amount
        self.flash = ENEMY_FLASH_TIME

        # Si lo golpean paseando, ya sabe donde estas: te persigue
        if self.phase == self.WANDER:
            self.phase = self.CHASE

        return amount

    # ---------- movimiento ----------

    def _walk(self, dt, direction, speed, collision_map,
              angles=(0, 45, -45, 90, -90)):
        """Camina hacia `direction`; si hay algo adelante prueba rodearlo.
        Devuelve la direccion que uso o None si no pudo moverse."""

        step = speed * dt

        for angle in angles:

            d = direction.rotate(angle)

            nx = self.pos.x + d.x * step
            ny = self.pos.y + d.y * step

            test = self.rect.copy()
            test.center = (round(nx), round(ny))

            if self._free(test, collision_map):

                self.pos.update(nx, ny)
                self.rect.center = test.center
                self.vel = d * speed

                return d

        return None

    def update(self, dt, target, collision_map, others=None):

        target = pygame.Vector2(target)

        self.last_target = target.copy()
        self.anim_t += dt

        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

        if self.touch_cd > 0:
            self.touch_cd = max(0.0, self.touch_cd - dt)

        if self.spawn_t > 0:

            self.spawn_t -= dt

            return

        self.vel = pygame.Vector2()

        to_player = target - self.pos
        dist = to_player.length()

        if dist < 0.01:
            to_player = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))
            dist = 0.01

        toward = to_player / dist

        # ---- recargando: quieto, brillando hasta explotar ----
        if self.phase == self.FUSE:

            if dist > HONGUN_FUSE_CANCEL_DIST:

                # Te alejaste: se cancela y vuelve a perseguirte
                self.phase = self.CHASE

            else:

                self.fuse_t += dt

                if self.fuse_t >= HONGUN_FUSE_TIME:

                    self.boom = True
                    self.hp = 0

                return

        # La luz de la recarga se apaga de a poco si no esta recargando
        if self.fuse_t > 0:
            self.fuse_t = max(0.0, self.fuse_t - dt * 2.0)

        # ---- persiguiendote ----
        if self.phase == self.CHASE:

            if dist > HONGUN_LOSE_RADIUS:

                self.phase = self.WANDER
                self.heading = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

            elif dist <= HONGUN_FUSE_DIST:

                self.phase = self.FUSE
                self.fuse_t = max(self.fuse_t, 0.001)

            else:

                self._walk(
                    dt,
                    self.nav_dir(target, collision_map, dt),
                    HONGUN_CHASE_SPEED,
                    collision_map,
                )

                self.anti_stuck(
                    dt, collision_map, target, HONGUN_CHASE_SPEED
                )

            return

        # ---- paseando tranquilo ----
        if dist <= HONGUN_DETECT_RADIUS:

            self.phase = self.CHASE

            return

        self.turn_t -= dt

        if self.turn_t <= 0:

            self.heading = self.heading.rotate(random.uniform(-80, 80))
            self.turn_t = random.uniform(*HONGUN_TURN_TIME)

        d = self._walk(
            dt, self.heading, HONGUN_WANDER_SPEED, collision_map,
            angles=(0, 40, -40, 90, -90, 140, -140, 180)
        )

        if d is not None:
            self.heading = d

        if self.anti_stuck(dt, collision_map, None, HONGUN_WANDER_SPEED):
            self.heading = self._random_open_dir(collision_map)

    # ---------- dibujo ----------

    def draw(self, screen, camera, art):

        sprites = art.get(camera.zoom)

        shake = 0
        k = self.fuse_k
        fusing = self.phase == self.FUSE and self.fuse_t > 0

        if self.flash > 0:

            img = sprites["hit"]

        else:

            if fusing:

                frames = sprites["charge"]
                index = int(self.anim_t / HONGUN_CHARGE_FRAME) % len(frames)

            else:

                frames = sprites["walk"]
                moving = self.vel.length_squared() > 1.0

                index = (
                    int(self.anim_t / HONGUN_ANIM_FRAME) % len(frames)
                    if moving else 0
                )

            img = frames[index]

            # Herido = mas oscuro (no mientras recarga, ahi se ve blanco)
            if self.hp < self.max_hp and not fusing:

                shade = int(255 * (0.55 + 0.45 * self.hp / self.max_hp))

                img = img.copy()
                img.fill(
                    (shade, shade, shade, 255),
                    special_flags=pygame.BLEND_RGBA_MULT
                )

            if fusing:

                # Parpadea a blanco cada vez mas rapido y se hincha
                blink_on = math.sin(self.anim_t * (14 + 36 * k)) > 0

                white = 255 if blink_on else int(70 * k)

                img = img.copy()
                img.fill((white, white, white, 0), special_flags=pygame.BLEND_RGB_ADD)

                grow = 1.0 + 0.30 * k

                size = (
                    max(1, int(img.get_width() * grow)),
                    max(1, int(img.get_height() * grow))
                )

                img = pygame.transform.scale(img, size)

                shake = int(math.sin(self.anim_t * 60) * 1.5 * k * camera.zoom)

        if self.spawning:

            t = 1.0 - max(0.0, self.spawn_t) / ENEMY_SPAWN_TIME

            img = img.copy()
            img.set_alpha(int(50 + 150 * max(0.0, min(1.0, t))))

        dest = camera.apply(self.rect)

        # Sombra
        shadow = pygame.Surface(
            (int(dest.width * 1.4), int(dest.height * 0.6)),
            pygame.SRCALPHA
        )

        pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())

        screen.blit(
            shadow,
            shadow.get_rect(center=(dest.centerx, dest.bottom))
        )

        screen.blit(
            img,
            img.get_rect(
                midbottom=(
                    dest.centerx + shake,
                    dest.bottom + int(2 * camera.zoom)
                )
            )
        )


# ---------------------------------------------------------------
# Destello - imagenes y enemigo
# ---------------------------------------------------------------

class DestelloArt:
    """Imagenes del destello (se cargan una sola vez). Todas opcionales:

      assets/maps/combate/destello_anim.png    224x56  (4 cuadros de 56x56, caminar tranquilo)
      assets/maps/combate/destello_correr.png  224x56  (4 cuadros de 56x56, corriendo)
      assets/maps/combate/destello_alerta.png  112x56  (2 cuadros de 56x56, aviso antes de correr)
      assets/maps/combate/destello.png         56x56   (1 cuadro: caminar si falta destello_anim)
      assets/maps/combate/destello_golpe.png   56x56   (cuando le pegas)

    Si falta destello_correr usa los de caminar (mas rapido). Si falta
    destello_alerta usa el primer cuadro de caminar. El parpadeo blanco
    del aviso lo hace el codigo.
    """

    def __init__(self):

        walk = load_strip(COMBAT_DIR / "destello_anim.png")
        single = load_strip(COMBAT_DIR / "destello.png")
        run = load_strip(COMBAT_DIR / "destello_correr.png")
        alert = load_strip(COMBAT_DIR / "destello_alerta.png")
        hit = load_image(COMBAT_DIR / "destello_golpe.png")

        self.walk = walk or single or [self._placeholder(0), self._placeholder(1)]
        self.run = run or self.walk
        self.alert = alert or [self.walk[0]]

        if hit is None:

            hit = self.walk[0].copy()
            hit.fill((170, 170, 170, 0), special_flags=pygame.BLEND_RGB_ADD)

        self.hit = hit

        self._zoom = None
        self._scaled = None

    @staticmethod
    def _placeholder(step=0):

        surf = pygame.Surface((56, 56), pygame.SRCALPHA)

        dark = (150, 120, 40)
        mid = (240, 220, 110)
        light = (255, 250, 200)

        # cuerpo
        pygame.draw.rect(surf, mid, (14, 6, 28, 30))
        pygame.draw.rect(surf, dark, (14, 6, 28, 30), 2)

        # brillos
        for x, y in ((18, 10), (32, 12), (22, 28), (34, 26)):
            pygame.draw.rect(surf, light, (x, y, 6, 6))

        # patas (se alternan para que parezca que camina)
        off = 2 if step % 2 == 0 else -2

        pygame.draw.rect(surf, dark, (14 + off, 36, 12, 14))
        pygame.draw.rect(surf, dark, (30 - off, 36, 12, 14))

        # cara (ojos grandes)
        pygame.draw.rect(surf, (40, 30, 10), (19, 14, 6, 8))
        pygame.draw.rect(surf, (40, 30, 10), (31, 14, 6, 8))
        pygame.draw.rect(surf, (40, 30, 10), (24, 26, 8, 3))

        return surf

    def get(self, zoom):

        if self._zoom != zoom:

            px = max(1, int(DESTELLO_DRAW_SIZE * zoom))

            def scale(frames):
                return [pygame.transform.scale(f, (px, px)) for f in frames]

            self._scaled = {
                "walk": scale(self.walk),
                "run": scale(self.run),
                "alert": scale(self.alert),
                "hit": pygame.transform.scale(self.hit, (px, px)),
            }

            self._zoom = zoom

        return self._scaled


class Destello(Enemy):
    """Un hongun flashbang: pasea tranquilo dando un poco de luz -> si te
    ve (distancia y sin paredes en el medio) se frena un instante
    parpadeando en blanco -> sale corriendo muy rapido hacia vos -> al
    chocarte explota: te saca DESTELLO_DAMAGE de vida, te empuja y te
    deja la pantalla en blanco unos 5 segundos (flashbang). Muere al
    explotar.

    Los golpes le sacan vida pero no lo frenan ni lo empujan: sigue
    corriendo. Si lo matas a golpes antes de que te choque, muere sin
    explotar (sin flash)."""

    fixed = False
    contact_damage = False

    WANDER = "wander"
    ALERT = "alert"
    CHARGE = "charge"

    def __init__(self, x, y, spawn_delay=0.0):

        super().__init__(x, y, DESTELLO_HP, DESTELLO_CHARGE_SPEED, spawn_delay)

        self.rect = pygame.Rect(0, 0, *DESTELLO_HITBOX)
        self.rect.center = (round(x), round(y))

        self.phase = self.WANDER

        self.heading = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))
        self.turn_t = random.uniform(*DESTELLO_TURN_TIME)

        self.alert_t = 0.0
        self.alert_time = DESTELLO_ALERT_TIME   # lo cambia la arena segun la oleada
        self.boom = False      # True = exploto contra el jugador
        self.boomed = False

    # ---------- estado ----------

    @property
    def can_explode(self):
        """Solo explota si ya salio corriendo (no paseando ni apareciendo)."""

        return (
            self.phase == self.CHARGE
            and not self.spawning
            and not self.dead
            and not self.boomed
        )

    def light(self):
        """(x, y, radio) de la luz de su cuerpo (siempre prendida)."""

        if self.spawning or self.dead:
            return None

        radius = (
            DESTELLO_LIGHT if self.phase == self.WANDER
            else DESTELLO_LIGHT_ALERT
        )

        return (self.pos.x, self.pos.y, quantize_radius(radius))

    # ---------- golpes ----------

    def take_damage(self, amount):
        """Recibe el dano pero NO retrocede ni se atonta."""

        if self.spawning or self.dead:
            return 0

        self.hp -= amount
        self.flash = ENEMY_FLASH_TIME

        # Si lo golpean paseando, ya te vio: se pone en alerta
        if self.phase == self.WANDER and not self.dead:

            self.phase = self.ALERT
            self.alert_t = self.alert_time

        return amount

    # ---------- movimiento ----------

    def _line_clear(self, a, b, collision_map):
        """True si no hay paredes ni bloques entre `a` y `b`."""

        a = pygame.Vector2(a)
        b = pygame.Vector2(b)

        steps = max(1, int(a.distance_to(b) // 4))

        probe = pygame.Rect(0, 0, 4, 4)

        for i in range(1, steps + 1):

            p = a.lerp(b, i / steps)

            probe.center = (round(p.x), round(p.y))

            if not (self.room.contains(probe) and collision_map.can_move(probe)):
                return False

        return True

    def _walk(self, dt, direction, speed, collision_map,
              angles=(0, 45, -45, 90, -90)):
        """Camina hacia `direction`; si hay algo adelante prueba rodearlo.
        Devuelve la direccion que uso o None si no pudo moverse."""

        step = speed * dt

        for angle in angles:

            d = direction.rotate(angle)

            nx = self.pos.x + d.x * step
            ny = self.pos.y + d.y * step

            test = self.rect.copy()
            test.center = (round(nx), round(ny))

            if self._free(test, collision_map):

                self.pos.update(nx, ny)
                self.rect.center = test.center
                self.vel = d * speed

                return d

        return None

    def _run(self, dt, direction, collision_map):
        """Corre hacia `direction` en pasos cortos (a esta velocidad un
        solo paso por frame se saltaria paredes finas)."""

        pieces = max(1, math.ceil(DESTELLO_CHARGE_SPEED * dt / 3.0))

        last = None

        for _ in range(pieces):

            d = self._walk(
                dt / pieces, direction, DESTELLO_CHARGE_SPEED, collision_map
            )

            if d is None:
                break

            last = d

        return last

    def update(self, dt, target, collision_map, others=None):

        target = pygame.Vector2(target)

        self.last_target = target.copy()
        self.anim_t += dt

        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

        if self.touch_cd > 0:
            self.touch_cd = max(0.0, self.touch_cd - dt)

        if self.spawn_t > 0:

            self.spawn_t -= dt

            return

        self.vel = pygame.Vector2()

        to_player = target - self.pos
        dist = to_player.length()

        if dist < 0.01:
            to_player = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))
            dist = 0.01

        toward = to_player / dist

        # ---- aviso: quieto, parpadeando, mirandote ----
        if self.phase == self.ALERT:

            self.alert_t -= dt

            if self.alert_t <= 0:
                self.phase = self.CHARGE

            return

        # ---- corriendo hacia vos ----
        if self.phase == self.CHARGE:

            if dist > DESTELLO_LOSE_RADIUS:

                self.phase = self.WANDER
                self.heading = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

            else:

                self._run(
                    dt, self.nav_dir(target, collision_map, dt), collision_map
                )

                self.anti_stuck(
                    dt, collision_map, target, DESTELLO_CHARGE_SPEED
                )

            return

        # ---- paseando tranquilo ----
        if (
            dist <= DESTELLO_DETECT_RADIUS
            and self._line_clear(self.pos, target, collision_map)
        ):

            self.phase = self.ALERT
            self.alert_t = self.alert_time

            return

        self.turn_t -= dt

        if self.turn_t <= 0:

            self.heading = self.heading.rotate(random.uniform(-80, 80))
            self.turn_t = random.uniform(*DESTELLO_TURN_TIME)

        d = self._walk(
            dt, self.heading, DESTELLO_WANDER_SPEED, collision_map,
            angles=(0, 40, -40, 90, -90, 140, -140, 180)
        )

        if d is not None:
            self.heading = d

        # Atascado paseando: cambia de rumbo
        if self.anti_stuck(dt, collision_map, None, DESTELLO_WANDER_SPEED):
            self.heading = self._random_open_dir(collision_map)

    # ---------- dibujo ----------

    def draw(self, screen, camera, art):

        sprites = art.get(camera.zoom)

        shake = 0
        alerting = self.phase == self.ALERT
        charging = self.phase == self.CHARGE

        if self.flash > 0:

            img = sprites["hit"]

        else:

            if alerting:

                frames = sprites["alert"]
                index = int(self.anim_t / DESTELLO_ALERT_FRAME) % len(frames)

            elif charging:

                frames = sprites["run"]
                index = int(self.anim_t / DESTELLO_RUN_FRAME) % len(frames)

            else:

                frames = sprites["walk"]
                moving = self.vel.length_squared() > 1.0

                index = (
                    int(self.anim_t / DESTELLO_ANIM_FRAME) % len(frames)
                    if moving else 0
                )

            img = frames[index]

            # Herido = mas oscuro (no durante el aviso, ahi parpadea blanco)
            if self.hp < self.max_hp and not alerting:

                shade = int(255 * (0.55 + 0.45 * max(0, self.hp) / self.max_hp))

                img = img.copy()
                img.fill(
                    (shade, shade, shade, 255),
                    special_flags=pygame.BLEND_RGBA_MULT
                )

            if alerting:

                # Parpadea a blanco y tiembla: esta por salir corriendo
                blink_on = math.sin(self.anim_t * 40) > 0

                white = 255 if blink_on else 60

                img = img.copy()
                img.fill((white, white, white, 0), special_flags=pygame.BLEND_RGB_ADD)

                shake = int(math.sin(self.anim_t * 70) * 1.5 * camera.zoom)

        if self.spawning:

            t = 1.0 - max(0.0, self.spawn_t) / ENEMY_SPAWN_TIME

            img = img.copy()
            img.set_alpha(int(50 + 150 * max(0.0, min(1.0, t))))

        dest = camera.apply(self.rect)

        # Sombra
        shadow = pygame.Surface(
            (int(dest.width * 1.4), int(dest.height * 0.6)),
            pygame.SRCALPHA
        )

        pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())

        screen.blit(
            shadow,
            shadow.get_rect(center=(dest.centerx, dest.bottom))
        )

        # Estela de velocidad: dos copias transparentes detras
        if charging and self.vel.length_squared() > 1.0 and not self.spawning:

            back = -self.vel.normalize()

            for i, alpha in ((2, 50), (1, 100)):

                ghost = img.copy()
                ghost.set_alpha(alpha)

                screen.blit(
                    ghost,
                    ghost.get_rect(
                        midbottom=(
                            dest.centerx + int(back.x * 3 * i * camera.zoom),
                            dest.bottom + int(2 * camera.zoom)
                            + int(back.y * 3 * i * camera.zoom)
                        )
                    )
                )

        screen.blit(
            img,
            img.get_rect(
                midbottom=(
                    dest.centerx + shake,
                    dest.bottom + int(2 * camera.zoom)
                )
            )
        )


# ---------------------------------------------------------------
# Golem (enorme y muy lento: te agarra y te saca el escudo / la luz)
# ---------------------------------------------------------------

class GolemArt:
    """Imagenes del golem (se cargan una sola vez). Todas opcionales:

      assets/maps/combate/golem_anim.png       448x112 (4 cuadros de 112x112, caminar tranquilo)
      assets/maps/combate/golem_perseguir.png  448x112 (4 cuadros de 112x112, persiguiendote)
      assets/maps/combate/golem_alerta.png     224x112 (2 cuadros de 112x112, aviso al verte)
      assets/maps/combate/golem_agarre.png     672x112 (6 cuadros de 112x112, el agarre)
      assets/maps/combate/golem.png            112x112 (1 cuadro: caminar si falta golem_anim)
      assets/maps/combate/golem_golpe.png      112x112 (cuando le pegas)

    Cada cuadro es cuadrado de 112x112 y se dibuja de 28x28 unidades del
    mundo (zoom x4). El golem mira de frente (no hay una hoja por
    direccion), con los pies pegados al borde de abajo del cuadro.

    El AGARRE (golem_agarre.png) son 6 cuadros seguidos:
      cuadros 1-2: estira los brazos hacia vos y te levanta
      cuadros 3-4: aprieta (el cuadro 3 es cuando se saca el escudo / vida)
      cuadros 5-6: te suelta / te tira para atras
    Mientras dura, el jugador se dibuja ENCIMA del golem, centrado abajo:
    con zoom x4 sus pies quedan ~20 px por debajo del borde de abajo del
    cuadro, y lo levanta 20 px. Dibuja las manos del golem alrededor de
    esa zona (aprox. x 30 a 82, y 60 a 105).

    Si falta golem_perseguir usa los de caminar (mas rapido). Si falta
    golem_alerta usa el primer cuadro de caminar. El temblor del aviso
    lo hace el codigo.
    """

    FRAME = 112

    def __init__(self):

        walk = load_strip(COMBAT_DIR / "golem_anim.png")
        single = load_strip(COMBAT_DIR / "golem.png")
        chase = load_strip(COMBAT_DIR / "golem_perseguir.png")
        alert = load_strip(COMBAT_DIR / "golem_alerta.png")
        grab = load_strip(COMBAT_DIR / "golem_agarre.png")
        hit = load_image(COMBAT_DIR / "golem_golpe.png")

        self.walk = walk or single or [self._placeholder("walk", 0),
                                       self._placeholder("walk", 1)]
        self.chase = chase or self.walk
        self.alert = alert or (
            [self._placeholder("alert", 0), self._placeholder("alert", 1)]
            if not (walk or single) else [self.walk[0]]
        )
        self.grab = grab or [
            self._placeholder("grab", i) for i in range(6)
        ]

        if hit is None:

            hit = self.walk[0].copy()
            hit.fill((150, 150, 150, 0), special_flags=pygame.BLEND_RGB_ADD)

        self.hit = hit

        self._zoom = None
        self._scaled = None

    @classmethod
    def _placeholder(cls, mode="walk", step=0):
        """Golem de piedra dibujado con rectangulos (por si faltan las
        imagenes)."""

        s = cls.FRAME
        surf = pygame.Surface((s, s), pygame.SRCALPHA)

        stone = (116, 116, 128)
        dark = (66, 66, 78)
        light = (158, 158, 170)
        eye = (255, 170, 50) if mode != "alert" else (255, 60, 40)

        bob = 2 if (step % 2 == 1 and mode == "walk") else 0

        # patas
        off = 4 if step % 2 == 0 else -4

        if mode == "walk":
            pygame.draw.rect(surf, dark, (32 + off, 82, 20, 28))
            pygame.draw.rect(surf, dark, (60 - off, 82, 20, 28))
        else:
            pygame.draw.rect(surf, dark, (32, 82, 20, 28))
            pygame.draw.rect(surf, dark, (60, 82, 20, 28))

        # torso
        pygame.draw.rect(surf, stone, (24, 32 - bob, 64, 54))
        pygame.draw.rect(surf, dark, (24, 32 - bob, 64, 54), 3)

        # grietas y musgo
        pygame.draw.line(surf, dark, (40, 44 - bob), (52, 62 - bob), 2)
        pygame.draw.line(surf, dark, (52, 62 - bob), (46, 76 - bob), 2)
        pygame.draw.rect(surf, (80, 120, 74), (66, 38 - bob, 14, 8))

        # cabeza
        pygame.draw.rect(surf, stone, (38, 8 - bob, 36, 28))
        pygame.draw.rect(surf, dark, (38, 8 - bob, 36, 28), 3)
        pygame.draw.rect(surf, eye, (45, 18 - bob, 8, 7))
        pygame.draw.rect(surf, eye, (59, 18 - bob, 8, 7))

        # brazos
        if mode == "walk":

            sw = 5 if step % 2 == 0 else -5

            pygame.draw.rect(surf, stone, (6, 38 + sw, 20, 46))
            pygame.draw.rect(surf, dark, (6, 38 + sw, 20, 46), 3)
            pygame.draw.rect(surf, stone, (86, 38 - sw, 20, 46))
            pygame.draw.rect(surf, dark, (86, 38 - sw, 20, 46), 3)

        elif mode == "alert":

            # brazos arriba (ruge)
            up = 0 if step % 2 == 0 else 6

            pygame.draw.rect(surf, stone, (4, 6 + up, 20, 44))
            pygame.draw.rect(surf, dark, (4, 6 + up, 20, 44), 3)
            pygame.draw.rect(surf, stone, (88, 6 + up, 20, 44))
            pygame.draw.rect(surf, dark, (88, 6 + up, 20, 44), 3)

        else:   # grab: 6 cuadros

            # (x de cada mano, y de las manos): se abren, aprietan y sueltan
            hands = [
                (14, 70), (26, 84), (38, 90),   # estira y levanta
                (44, 86), (40, 86),            # aprieta
                (6, 54),                       # suelta
            ][min(step, 5)]

            hx, hy = hands

            for side in (-1, 1):

                shoulder = (56 + side * 34, 48)
                hand = (56 + side * (56 - hx), hy)

                pygame.draw.line(surf, dark, shoulder, hand, 18)
                pygame.draw.line(surf, stone, shoulder, hand, 12)
                pygame.draw.rect(
                    surf, light, (hand[0] - 9, hand[1] - 9, 18, 18)
                )
                pygame.draw.rect(
                    surf, dark, (hand[0] - 9, hand[1] - 9, 18, 18), 3
                )

        return surf

    def get(self, zoom):

        if self._zoom != zoom:

            px = max(1, int(GOLEM_DRAW_SIZE * zoom))

            def scale(frames):
                return [pygame.transform.scale(f, (px, px)) for f in frames]

            self._scaled = {
                "walk": scale(self.walk),
                "chase": scale(self.chase),
                "alert": scale(self.alert),
                "grab": scale(self.grab),
                "hit": pygame.transform.scale(self.hit, (px, px)),
            }

            self._zoom = zoom

        return self._scaled


class Golem(Enemy):
    """Enorme y MUY lento. Pasea tranquilo -> si te ve (distancia y sin
    paredes en el medio) se frena y ruge (aviso) -> va directo hacia
    vos, despacito pero sin parar -> si te toca UNA vez te agarra: te
    levanta y te aprieta (animacion). Al apretar te saca TODO el escudo;
    si no tenias escudo, te saca TODA la vida de la luz. Despues te
    suelta, te empuja y queda cansado unos segundos.

    Los golpes le sacan vida pero casi no lo mueven ni lo frenan, y
    mientras te tiene agarrado no se lo puede lastimar. Lo de pegarle al
    jugador (escudo / vida) lo hace la arena (Arena._golem_step)."""

    fixed = False
    contact_damage = False

    WANDER = "wander"
    ALERT = "alert"
    CHASE = "chase"
    GRAB = "grab"
    REST = "rest"

    def __init__(self, x, y, spawn_delay=0.0):

        super().__init__(x, y, GOLEM_HP, GOLEM_CHASE_SPEED, spawn_delay)

        self.spawn_t = GOLEM_SPAWN_TIME + spawn_delay

        self.rect = pygame.Rect(0, 0, *GOLEM_HITBOX)
        self.rect.center = (round(x), round(y))

        self.phase = self.WANDER

        self.heading = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))
        self.turn_t = random.uniform(*GOLEM_TURN_TIME)

        self.phase_t = 0.0
        self.moving = False

        self.grab_dir = pygame.Vector2(0, 1)   # hacia donde tira al jugador al soltarlo
        self._squeeze_pending = False   # apreto y la arena todavia no lo aplico
        self._release_pending = False   # solto y la arena todavia no lo aplico
        self._squeezed = False          # ya apreto en este agarre

    # ---------- estado ----------

    @property
    def holding(self):
        """True mientras tiene agarrado al jugador."""

        return self.phase == self.GRAB

    @property
    def lift(self):
        """Cuanto levanta al jugador ahora mismo (unidades del mundo):
        sube al empezar el agarre y baja al soltarlo."""

        if self.phase != self.GRAB:
            return 0.0

        up = min(1.0, self.phase_t / 0.35)
        down = min(1.0, max(0.0, (GOLEM_GRAB_TIME - self.phase_t) / 0.25))

        return GOLEM_GRAB_LIFT * ease_out(min(up, down))

    def can_grab(self, body):
        """True si esta persiguiendo y toca el cuerpo del jugador."""

        if self.phase != self.CHASE or self.spawning or self.dead:
            return False

        reach = self.rect.inflate(GOLEM_GRAB_REACH * 2, GOLEM_GRAB_REACH * 2)

        return reach.colliderect(body)

    def start_grab(self, direction=None):
        """`direction`: de que lado vino el jugador (para tirarlo para
        ese mismo lado al soltarlo)."""

        if direction is not None and pygame.Vector2(direction).length_squared() > 0.01:
            self.grab_dir = pygame.Vector2(direction).normalize()
        else:
            self.grab_dir = pygame.Vector2(0, 1)

        self.phase = self.GRAB
        self.phase_t = 0.0
        self.vel = pygame.Vector2()
        self._squeeze_pending = False
        self._release_pending = False
        self._squeezed = False

    def take_squeeze(self):
        """True UNA vez por agarre: cuando aprieta."""

        if self._squeeze_pending:

            self._squeeze_pending = False

            return True

        return False

    def take_release(self):
        """True UNA vez por agarre: cuando suelta al jugador."""

        if self._release_pending:

            self._release_pending = False

            return True

        return False

    # ---------- golpes que recibe ----------

    def take_damage(self, amount):
        """Pierde vida, parpadea y se da cuenta de que lo atacan. Casi no
        retrocede y no se atonta: es pesado. Mientras te agarra no se le
        puede hacer dano."""

        if self.spawning or self.dead or self.phase == self.GRAB:
            return 0

        self.hp -= amount
        self.flash = GOLEM_FLASH_TIME

        away = self.pos - self.last_target

        if away.length_squared() > 0.01 and self.phase != self.ALERT:
            self.pos += away.normalize() * GOLEM_HIT_PUSH * 0.05
            self.rect.center = (round(self.pos.x), round(self.pos.y))

        # Si lo golpean paseando, ya te vio
        if self.phase == self.WANDER:

            self.phase = self.ALERT
            self.phase_t = 0.0

        return amount

    # ---------- movimiento ----------

    def _line_clear(self, a, b, collision_map):
        """True si no hay paredes ni bloques entre `a` y `b`."""

        a = pygame.Vector2(a)
        b = pygame.Vector2(b)

        steps = max(1, int(a.distance_to(b) // 4))

        probe = pygame.Rect(0, 0, 4, 4)

        for i in range(1, steps + 1):

            p = a.lerp(b, i / steps)

            probe.center = (round(p.x), round(p.y))

            if not (self.room.contains(probe) and collision_map.can_move(probe)):
                return False

        return True

    def _walk(self, dt, direction, speed, collision_map,
              angles=(0, 45, -45, 90, -90)):
        """Camina hacia `direction`; si hay algo adelante prueba rodearlo.
        Devuelve la direccion que uso o None si no pudo moverse."""

        step = speed * dt

        for angle in angles:

            d = direction.rotate(angle)

            nx = self.pos.x + d.x * step
            ny = self.pos.y + d.y * step

            test = self.rect.copy()
            test.center = (round(nx), round(ny))

            if self._free(test, collision_map):

                self.pos.update(nx, ny)
                self.rect.center = test.center
                self.vel = d * speed

                return d

        return None

    def update(self, dt, target, collision_map, others=None):

        target = pygame.Vector2(target)

        self.last_target = target.copy()
        self.anim_t += dt
        self.moving = False

        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

        if self.touch_cd > 0:
            self.touch_cd = max(0.0, self.touch_cd - dt)

        if self.spawn_t > 0:

            self.spawn_t -= dt

            return

        self.vel = pygame.Vector2()

        to_player = target - self.pos
        dist = to_player.length()

        # ---- agarrando: no se mueve, la animacion manda ----
        if self.phase == self.GRAB:

            self.phase_t += dt

            if not self._squeezed and self.phase_t >= GOLEM_SQUEEZE_AT:

                self._squeezed = True
                self._squeeze_pending = True

            if self.phase_t >= GOLEM_GRAB_TIME:

                self.phase = self.REST
                self.phase_t = 0.0
                self._release_pending = True

            return

        # ---- cansado despues de agarrarte: quieto ----
        if self.phase == self.REST:

            self.phase_t += dt

            if self.phase_t >= GOLEM_REST_TIME:

                self.phase = (
                    self.CHASE if dist <= GOLEM_LOSE_RADIUS else self.WANDER
                )
                self.phase_t = 0.0

            return

        # ---- aviso: quieto, ruge, mirandote ----
        if self.phase == self.ALERT:

            self.phase_t += dt

            if self.phase_t >= GOLEM_ALERT_TIME:

                self.phase = self.CHASE
                self.phase_t = 0.0

            return

        # ---- persiguiendote, directo, despacito pero sin parar ----
        if self.phase == self.CHASE:

            if dist > GOLEM_LOSE_RADIUS:

                self.phase = self.WANDER
                self.heading = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

                return

            d = self._walk(
                dt,
                self.nav_dir(target, collision_map, dt),
                GOLEM_CHASE_SPEED,
                collision_map,
            )

            self.anti_stuck(dt, collision_map, target, GOLEM_CHASE_SPEED)

            if d is not None:
                self.moving = True

            return

        # ---- paseando tranquilo ----
        if (
            dist <= GOLEM_DETECT_RADIUS
            and self._line_clear(self.pos, target, collision_map)
        ):

            self.phase = self.ALERT
            self.phase_t = 0.0

            return

        self.turn_t -= dt

        if self.turn_t <= 0:

            self.heading = self.heading.rotate(random.uniform(-80, 80))
            self.turn_t = random.uniform(*GOLEM_TURN_TIME)

        d = self._walk(
            dt, self.heading, GOLEM_WANDER_SPEED, collision_map,
            angles=(0, 40, -40, 90, -90, 140, -140, 180)
        )

        if d is not None:
            self.heading = d
            self.moving = True

        # Atascado paseando: cambia de rumbo
        if self.anti_stuck(dt, collision_map, None, GOLEM_WANDER_SPEED):
            self.heading = self._random_open_dir(collision_map)

    # ---------- dibujo ----------

    def draw(self, screen, camera, art):

        sprites = art.get(camera.zoom)

        shake = 0
        alerting = self.phase == self.ALERT

        if self.flash > 0:

            img = sprites["hit"]

        else:

            if self.phase == self.GRAB:

                frames = sprites["grab"]
                index = min(
                    len(frames) - 1,
                    int(self.phase_t / GOLEM_GRAB_TIME * len(frames))
                )

            elif alerting:

                frames = sprites["alert"]
                index = int(self.anim_t / GOLEM_ALERT_FRAME) % len(frames)

            elif self.phase == self.CHASE:

                frames = sprites["chase"]
                index = (
                    int(self.anim_t / GOLEM_CHASE_FRAME) % len(frames)
                    if self.moving else 0
                )

            else:

                frames = sprites["walk"]
                index = (
                    int(self.anim_t / GOLEM_ANIM_FRAME) % len(frames)
                    if self.moving else 0
                )

            img = frames[index]

            # Herido = mas oscuro
            if self.hp < self.max_hp:

                shade = int(255 * (0.55 + 0.45 * max(0, self.hp) / self.max_hp))

                img = img.copy()
                img.fill(
                    (shade, shade, shade, 255),
                    special_flags=pygame.BLEND_RGBA_MULT
                )

            if alerting:

                # Tiembla y se tiñe de rojo: te vio
                blink_on = math.sin(self.anim_t * 30) > 0

                img = img.copy()
                img.fill(
                    (90 if blink_on else 30, 0, 0, 0),
                    special_flags=pygame.BLEND_RGB_ADD
                )

                shake = int(math.sin(self.anim_t * 60) * 1.5 * camera.zoom)

            elif self.phase == self.GRAB:

                # Tiembla de la fuerza cuando aprieta
                if abs(self.phase_t - GOLEM_SQUEEZE_AT) < 0.3:
                    shake = int(math.sin(self.anim_t * 80) * 1.2 * camera.zoom)

            elif self.phase == self.REST:

                # Cansado: se ve un poco mas apagado
                img = img.copy()
                img.fill(
                    (200, 200, 215, 255),
                    special_flags=pygame.BLEND_RGBA_MULT
                )

        if self.spawning:

            t = 1.0 - max(0.0, self.spawn_t) / GOLEM_SPAWN_TIME

            img = img.copy()
            img.set_alpha(int(50 + 150 * max(0.0, min(1.0, t))))

        dest = camera.apply(self.rect)

        # Sombra (mas grande: es enorme)
        shadow = pygame.Surface(
            (int(img.get_width() * 0.7), int(img.get_height() * 0.22)),
            pygame.SRCALPHA
        )

        pygame.draw.ellipse(shadow, (0, 0, 0, 100), shadow.get_rect())

        screen.blit(
            shadow,
            shadow.get_rect(center=(dest.centerx, dest.bottom))
        )

        screen.blit(
            img,
            img.get_rect(
                midbottom=(
                    dest.centerx + shake,
                    dest.bottom + int(2 * camera.zoom)
                )
            )
        )


# ---------------------------------------------------------------
# Guardian (del tamano del jugador, pega con un golpe en arco igual
# que el jugador, tiene mucha vida)
# ---------------------------------------------------------------

GUARDIAN_HP = 48                  # golpes que aguanta
GUARDIAN_HITBOX = (10, 16)        # lo que choca y lo que golpea el jugador
# Tamano dibujado en unidades del mundo: el mismo que el personaje
# (54x74 px en pantalla con el zoom x4)
GUARDIAN_DRAW_SIZE = (14.5, 18.5)

# Movimiento (unidades del mundo por segundo; el jugador va a 95)
GUARDIAN_WANDER_SPEED = 35.0      # paseando tranquilo
GUARDIAN_CHASE_SPEED = 70.0       # yendo directo hacia el jugador
GUARDIAN_TURN_TIME = (1.2, 3.0)   # cada cuanto cambia de rumbo paseando

# Su golpe es EL MISMO que el del jugador (world/melee.py): mismo arco,
# mismo alcance y misma duracion. Si cambias esos numeros alla, cambian aca.
GUARDIAN_INNER = INNER_RADIUS
GUARDIAN_OUTER = OUTER_RADIUS
GUARDIAN_ARC = ARC_DEGREES
GUARDIAN_SWING_TIME = SWING_TIME

GUARDIAN_ATTACK_DIST = 22.0       # a esta distancia del jugador empieza a pegar
GUARDIAN_WINDUP = 0.15            # aviso cortito: levanta el arma y se ve la zona roja
GUARDIAN_COOLDOWN = COOLDOWN      # espera despues del golpe: la misma que el jugador
GUARDIAN_DAMAGE = 0.45            # 0.10 = 10% de la vida de la luz
GUARDIAN_KNOCKBACK = 150.0        # empujon al jugador (el de un pino es 120)
GUARDIAN_HIT_PUSH = 28.0          # cuanto lo mueve un golpe tuyo (casi nada: es pesado)
GUARDIAN_WEAPON_LENGTH = 21.0     # largo del arma dibujada (unidades del mundo)

GUARDIAN_ANIM_FRAME = 0.14
GUARDIAN_FLASH_TIME = 0.10
GUARDIAN_SPAWN_TIME = 1.0


class GuardianArt:
    """Imagenes del guardian (todas opcionales: si falta alguna se
    dibuja un reemplazo).

      guardian.png         hoja de caminar: 4 columnas x 4 filas
                           (filas: arriba, abajo, izquierda, derecha,
                           igual que el personaje)
      guardian_ataque.png  hoja de golpe: 2 columnas x 4 filas (mismas
                           filas). Columna 1 = arma levantada (aviso),
                           columna 2 = golpe
      guardian_arma.png    el arma sola, apuntando hacia ARRIBA, con el
                           mango abajo (se la hace girar en el golpe)
      guardian_icono.png   dibujo para la enciclopedia (56x56)
    """

    DIRS = ("up", "down", "left", "right")
    CELL = (64, 80)

    # Archivos (el Guardian Tirador usa otros) y colores del reemplazo
    WALK_FILE = "guardian.png"
    ATTACK_FILE = "guardian_ataque.png"
    WEAPON_FILE = "guardian_arma.png"
    CLOTH = (88, 58, 120)
    DARK = (46, 30, 68)

    def __init__(self):

        walk = load_image(COMBAT_DIR / self.WALK_FILE)
        attack = load_image(COMBAT_DIR / self.ATTACK_FILE)

        self.walk = self._cut(walk, 4) or self._placeholder_walk()
        self.attack = self._cut(attack, 2) or self._placeholder_attack()
        self.weapon = (
            load_image(COMBAT_DIR / self.WEAPON_FILE)
            if self.WEAPON_FILE else None
        )

        self._zoom = None
        self._scaled = None
        self._weapon_zoom = None
        self._weapon_scaled = None

    # ---------- carga ----------

    @classmethod
    def _cut(cls, sheet, cols):
        """Corta una hoja de `cols` columnas x 4 filas. None si no hay."""

        if sheet is None:
            return None

        cw = sheet.get_width() // cols
        ch = sheet.get_height() // 4

        if cw <= 0 or ch <= 0:
            return None

        return {
            d: [
                sheet.subsurface((c * cw, r * ch, cw, ch)).copy()
                for c in range(cols)
            ]
            for r, d in enumerate(cls.DIRS)
        }

    # ---------- reemplazos dibujados con codigo ----------

    @classmethod
    def _body(cls, direction, step, raised):
        """Un muneco simple (mientras no haya imagenes)."""

        w, h = cls.CELL
        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        cloth = cls.CLOTH
        dark = cls.DARK
        skin = (200, 175, 150)
        eye = (255, 215, 90)

        off = (0, 3, 0, -3)[step % 4]

        # piernas
        pygame.draw.rect(surf, dark, (w // 2 - 12, 52 + off, 10, 22))
        pygame.draw.rect(surf, dark, (w // 2 + 2, 52 - off, 10, 22))

        # cuerpo
        pygame.draw.rect(surf, cloth, (w // 2 - 15, 24, 30, 32), border_radius=4)
        pygame.draw.rect(surf, dark, (w // 2 - 15, 24, 30, 32), 2, border_radius=4)

        # brazos
        arm_y = 14 if raised else 28
        if direction in ("down", "up"):
            pygame.draw.rect(surf, cloth, (w // 2 - 22, arm_y, 8, 22))
            pygame.draw.rect(surf, cloth, (w // 2 + 14, arm_y, 8, 22))
        elif direction == "left":
            pygame.draw.rect(surf, cloth, (w // 2 - 20, arm_y, 8, 22))
        else:
            pygame.draw.rect(surf, cloth, (w // 2 + 12, arm_y, 8, 22))

        # cabeza
        pygame.draw.circle(surf, skin, (w // 2, 14), 12)
        pygame.draw.circle(surf, dark, (w // 2, 14), 12, 2)

        # ojos (de espaldas no se ven)
        if direction == "down":
            pygame.draw.rect(surf, eye, (w // 2 - 7, 11, 4, 4))
            pygame.draw.rect(surf, eye, (w // 2 + 3, 11, 4, 4))
        elif direction == "left":
            pygame.draw.rect(surf, eye, (w // 2 - 9, 11, 4, 4))
        elif direction == "right":
            pygame.draw.rect(surf, eye, (w // 2 + 5, 11, 4, 4))
        else:
            pygame.draw.rect(surf, dark, (w // 2 - 8, 4, 16, 6))

        return surf

    @classmethod
    def _placeholder_walk(cls):

        return {
            d: [cls._body(d, i, False) for i in range(4)]
            for d in cls.DIRS
        }

    @classmethod
    def _placeholder_attack(cls):

        return {
            d: [cls._body(d, 0, True), cls._body(d, 2, False)]
            for d in cls.DIRS
        }

    # ---------- escalado ----------

    def get(self, zoom):
        """Hojas ya escaladas al tamano del personaje en pantalla."""

        if self._zoom != zoom:

            size = (
                max(1, int(GUARDIAN_DRAW_SIZE[0] * zoom)),
                max(1, int(GUARDIAN_DRAW_SIZE[1] * zoom)),
            )

            def scale(table):
                return {
                    d: [pygame.transform.smoothscale(f, size) for f in frames]
                    for d, frames in table.items()
                }

            self._scaled = (scale(self.walk), scale(self.attack))
            self._zoom = zoom

        return self._scaled

    def get_weapon(self, zoom):
        """El arma escalada (None si no hay imagen: se dibuja con codigo)."""

        if self.weapon is None:
            return None

        if self._weapon_zoom != zoom:

            h = max(1, int(GUARDIAN_WEAPON_LENGTH * zoom))
            w = max(1, int(self.weapon.get_width() * h / self.weapon.get_height()))

            self._weapon_scaled = pygame.transform.smoothscale(self.weapon, (w, h))
            self._weapon_zoom = zoom

        return self._weapon_scaled


class Guardian(Enemy):
    """Del tamano del jugador. Pasea tranquilo por la sala; cuando tu luz
    lo toca (o le pegas) se despierta y va DIRECTO hacia vos, sin parar
    hasta que muere. Cuando llega a tu alcance levanta el arma (aviso) y
    pega con el mismo golpe en arco que el jugador. Tiene mucha vida y
    casi no retrocede cuando lo golpeas."""

    fixed = False
    contact_damage = False

    WANDER = "wander"
    CHASE = "chase"
    WINDUP = "windup"
    SWING = "swing"

    def __init__(self, x, y, spawn_delay=0.0):

        super().__init__(x, y, GUARDIAN_HP, GUARDIAN_CHASE_SPEED, spawn_delay)

        self.spawn_t = GUARDIAN_SPAWN_TIME + spawn_delay

        self.rect = pygame.Rect(0, 0, *GUARDIAN_HITBOX)
        self.rect.center = (round(x), round(y))

        self.phase = self.WANDER

        self.heading = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))
        self.turn_t = random.uniform(*GUARDIAN_TURN_TIME)

        self.facing = "down"
        self.moving = False

        self.phase_t = 0.0       # tiempo dentro de WINDUP / SWING
        self.cooldown = 0.0
        self.aim = 0.0           # angulo (radianes) hacia donde pega
        self.hit_done = False    # ya le pego al jugador en este golpe

    # ---------- estado ----------

    @property
    def awake(self):

        return self.phase != self.WANDER

    @property
    def attacking(self):

        return self.phase in (self.WINDUP, self.SWING)

    @property
    def swing_k(self):
        """0 a 1: cuanto avanzo el golpe (solo en SWING)."""

        return max(0.0, min(1.0, self.phase_t / GUARDIAN_SWING_TIME))

    def weapon_angle(self):
        """Angulo (radianes) del arma ahora mismo."""

        half = math.radians(GUARDIAN_ARC) / 2

        if self.phase == self.WINDUP:
            return self.aim - half

        if self.phase == self.SWING:
            return self.aim - half + 2 * half * ease_out(self.swing_k)

        return self.aim

    # ---------- golpes que recibe ----------

    def take_damage(self, amount):
        """Pierde vida, parpadea y se despierta. Casi no retrocede y no
        se le corta el golpe: es pesado."""

        if self.spawning or self.dead:
            return 0

        self.hp -= amount
        self.flash = GUARDIAN_FLASH_TIME

        away = self.pos - self.last_target

        if away.length_squared() > 0.01 and not self.attacking:
            self.pos += away.normalize() * GUARDIAN_HIT_PUSH * 0.05
            self.rect.center = (round(self.pos.x), round(self.pos.y))

        if self.phase == self.WANDER:
            self.phase = self.CHASE

        return amount

    # ---------- movimiento ----------

    def _walk(self, dt, direction, speed, collision_map,
              angles=(0, 45, -45, 90, -90)):
        """Camina hacia `direction`; si hay algo adelante prueba rodearlo.
        Devuelve la direccion que uso o None si no pudo moverse."""

        step = speed * dt

        for angle in angles:

            d = direction.rotate(angle)

            nx = self.pos.x + d.x * step
            ny = self.pos.y + d.y * step

            test = self.rect.copy()
            test.center = (round(nx), round(ny))

            if self._free(test, collision_map):

                self.pos.update(nx, ny)
                self.rect.center = test.center
                self.vel = d * speed

                return d

        return None

    def _face(self, direction):
        """Hacia donde mira (el eje que mas pesa)."""

        if abs(direction.x) > abs(direction.y):
            self.facing = "right" if direction.x > 0 else "left"
        elif abs(direction.y) > 0.001:
            self.facing = "down" if direction.y > 0 else "up"

    def swing_hits(self, point):
        """True UNA vez por golpe si el arma toca `point` (centro del
        cuerpo del jugador). Mismo arco y alcance que el golpe del
        jugador: un sector entre INNER y OUTER, barrido hasta ahora."""

        if self.phase != self.SWING or self.hit_done:
            return False

        offset = pygame.Vector2(point) - self.pos
        dist = offset.length()

        # El jugador tiene cuerpo: se le perdona un poco de alcance
        if dist < GUARDIAN_INNER - 8 or dist > GUARDIAN_OUTER + 5:
            return False

        half = math.radians(GUARDIAN_ARC) / 2
        angle = math.atan2(offset.y, offset.x)

        # Barrido: desde donde empezo el golpe hasta donde esta ahora
        start = self.aim - half
        now = self.weapon_angle()

        delta = (angle - start + math.pi) % math.tau - math.pi
        reach = now - start

        # un poco de margen para el ancho del cuerpo
        if -0.15 <= delta <= reach + 0.15:

            self.hit_done = True

            return True

        return False

    def update(self, dt, target, collision_map, light_on, light_radius):

        target = pygame.Vector2(target)
        self.last_target = target.copy()

        self.anim_t += dt
        self.moving = False

        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

        if self.spawning:
            self.spawn_t -= dt
            return

        if self.cooldown > 0:
            self.cooldown = max(0.0, self.cooldown - dt)

        to_player = target - self.pos
        dist = to_player.length()
        toward = to_player / dist if dist > 0.01 else pygame.Vector2(1, 0)

        # ---- paseando tranquilo: la luz lo despierta ----
        if self.phase == self.WANDER:

            if light_on and dist <= light_radius:

                self.phase = self.CHASE

            else:

                self.turn_t -= dt

                if self.turn_t <= 0:

                    self.heading = self.heading.rotate(random.uniform(-80, 80))
                    self.turn_t = random.uniform(*GUARDIAN_TURN_TIME)

                d = self._walk(
                    dt, self.heading, GUARDIAN_WANDER_SPEED, collision_map,
                    angles=(0, 40, -40, 90, -90, 140, -140, 180)
                )

                if d is not None:
                    self.heading = d
                    self.moving = True
                    self._face(d)

                return

        # ---- levanta el arma: aviso, quieto, apuntandote ----
        if self.phase == self.WINDUP:

            self.phase_t += dt

            # Sigue apuntando mientras carga (con un poco de demora)
            want = math.atan2(toward.y, toward.x)
            diff = (want - self.aim + math.pi) % math.tau - math.pi
            self.aim += diff * min(1.0, 6.0 * dt)

            self._face(pygame.Vector2(math.cos(self.aim), math.sin(self.aim)))

            if self.phase_t >= GUARDIAN_WINDUP:

                self.phase = self.SWING
                self.phase_t = 0.0
                self.hit_done = False

            return

        # ---- el golpe ----
        if self.phase == self.SWING:

            self.phase_t += dt

            if self.phase_t >= GUARDIAN_SWING_TIME:

                self.phase = self.CHASE
                self.cooldown = GUARDIAN_COOLDOWN

            return

        # ---- persiguiendo, directo al jugador, hasta morir ----
        if dist <= GUARDIAN_ATTACK_DIST and self.cooldown <= 0:

            self.phase = self.WINDUP
            self.phase_t = 0.0
            self.aim = math.atan2(toward.y, toward.x)

            return

        # Si esta en su alcance (esperando el cooldown) se queda pegado
        # a vos sin empujarte
        if dist > GUARDIAN_ATTACK_DIST * 0.7:

            d = self._walk(
                dt,
                self.nav_dir(target, collision_map, dt),
                GUARDIAN_CHASE_SPEED,
                collision_map,
            )

            self.anti_stuck(dt, collision_map, target, GUARDIAN_CHASE_SPEED)

            if d is not None:
                self.moving = True
                self._face(d)

        else:

            self._face(toward)

    # ---------- dibujo ----------

    def draw(self, screen, camera, art):

        walk, attack = art.get(camera.zoom)

        if self.attacking:

            frames = attack[self.facing]
            img = frames[0] if self.phase == self.WINDUP else frames[min(1, len(frames) - 1)]

        else:

            frames = walk[self.facing]

            index = (
                int(self.anim_t / GUARDIAN_ANIM_FRAME) % len(frames)
                if self.moving else 0
            )

            img = frames[index]

        if self.flash > 0:

            img = img.copy()
            img.fill((200, 200, 200, 0), special_flags=pygame.BLEND_RGB_ADD)

        if self.spawning:

            k = 1.0 - max(0.0, self.spawn_t) / GUARDIAN_SPAWN_TIME

            img = img.copy()
            img.set_alpha(int(40 + 160 * max(0.0, min(1.0, k))))

        dest = camera.apply(self.rect)

        # Sombra
        shadow = pygame.Surface(
            (int(dest.width * 1.5), int(dest.height * 0.35)),
            pygame.SRCALPHA
        )

        pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())

        screen.blit(
            shadow,
            shadow.get_rect(center=(dest.centerx, dest.bottom))
        )

        sprite_rect = img.get_rect(
            midbottom=(dest.centerx, dest.bottom + int(2 * camera.zoom))
        )

        screen.blit(img, sprite_rect)

        if self.spawning or self.dead:
            return

        if self.attacking:
            self._draw_attack(screen, camera, dest, art)

    def _draw_attack(self, screen, camera, dest, art):
        """Solo se dibuja el arma girando (sin zona roja de aviso)."""

        zoom = camera.zoom
        cx, cy = dest.center

        r_in = GUARDIAN_INNER * zoom

        # Arma
        angle = self.weapon_angle()
        direction = pygame.Vector2(math.cos(angle), math.sin(angle))
        length = GUARDIAN_WEAPON_LENGTH * zoom

        weapon = art.get_weapon(zoom)

        start = pygame.Vector2(cx, cy) + direction * r_in * 0.6

        if weapon is not None:

            # La imagen mira hacia arriba: se gira hasta apuntar al angulo
            img = pygame.transform.rotate(weapon, -(math.degrees(angle) + 90))
            center = start + direction * (weapon.get_height() / 2)

            screen.blit(img, img.get_rect(center=(round(center.x), round(center.y))))

            return

        end = start + direction * length

        pygame.draw.line(screen, (60, 40, 25), start, end, max(3, int(zoom * 1.1)))
        pygame.draw.line(screen, (150, 105, 60), start, end, max(2, int(zoom * 0.6)))
        pygame.draw.circle(screen, (255, 160, 60), (int(end.x), int(end.y)), max(2, int(zoom * 0.9)))


# ---------------------------------------------------------------
# Guardian Tirador (igual al Guardian, pero en vez de pegar dispara
# bolas como las del jugador, apunta muy bien y toma distancia)
# ---------------------------------------------------------------

GSHOOT_HP = 40                     # golpes que aguanta (el Guardian: 48)

# Movimiento (unidades del mundo por segundo; el jugador va a 95)
GSHOOT_WANDER_SPEED = GUARDIAN_WANDER_SPEED   # paseando tranquilo
GSHOOT_MOVE_SPEED = 70.0           # acercandose / dando vueltas
GSHOOT_RETREAT_SPEED = 80.0        # alejandose de vos
GSHOOT_STRAFE_TIME = (1.0, 2.2)    # cada cuanto cambia el lado al dar vueltas

# Distancias: busca quedarse entre MIN y MAX. Mas cerca que MIN retrocede,
# mas lejos que MAX se acerca, y en el medio da vueltas a tu alrededor.
GSHOOT_MIN_DIST = 70.0
GSHOOT_MAX_DIST = 120.0

# La bola: MISMA velocidad que la bola de fuego del jugador
GSHOOT_BOLT_SPEED = FIRE_SPEED
GSHOOT_BOLT_RANGE = 190.0          # hasta donde llega antes de apagarse
GSHOOT_BOLT_HITBOX = 5
GSHOOT_BOLT_DRAW_SIZE = 7.0        # tamano dibujado (mundo)
GSHOOT_MUZZLE = 8.0                # a que distancia del cuerpo nace

# Disparo
GSHOOT_AIM_TIME = 0.35             # aviso: queda quieto apuntandote y carga
GSHOOT_RECOVER = 0.18              # quieto un ratito despues de disparar
GSHOOT_COOLDOWN = 1.2              # espera entre un disparo y el otro
                                   # (la del jugador es 0.45: con esta punteria seria imposible)
GSHOOT_AIM_TURN = 14.0             # que tan rapido gira la punteria mientras carga
GSHOOT_LEAD_MAX = 0.8              # lo maximo (seg) que adelanta la punteria
GSHOOT_DAMAGE = 0.15               # 0.10 = 10% de la vida de la luz
GSHOOT_KNOCKBACK = 90.0            # empujon al jugador si lo toca la bola


_gshoot_bolt_cache = {}


def _gshoot_bolt_base():
    """Imagen de la bola (32x32, mirando a la DERECHA). Si no hay
    imagen se dibuja una violeta, para no confundirla con las tuyas."""

    img = load_image(COMBAT_DIR / "bola_guardian.png")

    if img is None:

        img = pygame.Surface((32, 32), pygame.SRCALPHA)

        pygame.draw.circle(img, (120, 50, 200), (22, 16), 9)
        pygame.draw.circle(img, (190, 130, 255), (22, 16), 6)
        pygame.draw.circle(img, (245, 230, 255), (22, 16), 3)

    return img


def _gshoot_bolt_sprite(zoom, angle_deg):
    """Bola ya escalada al zoom y girada hacia donde vuela."""

    deg = round(-angle_deg / 10) * 10

    key = (zoom, deg)

    if key not in _gshoot_bolt_cache:

        size = max(4, int(GSHOOT_BOLT_DRAW_SIZE * zoom))

        sprite = pygame.transform.smoothscale(_gshoot_bolt_base(), (size, size))

        _gshoot_bolt_cache[key] = pygame.transform.rotate(sprite, deg)

    return _gshoot_bolt_cache[key]


class GuardianShooterArt(GuardianArt):
    """Imagenes del Guardian Tirador (todas opcionales: si falta alguna
    se dibuja un reemplazo).

      guardian_tirador.png          256x320  hoja de caminar: 4 columnas x
                                    4 filas (arriba, abajo, izquierda,
                                    derecha), igual que el Guardian
      guardian_tirador_disparo.png  128x320  2 columnas x 4 filas (mismas
                                    filas). Columna 1 = apuntando/cargando,
                                    columna 2 = disparando
      guardian_tirador_icono.png    128x128  enciclopedia
      bola_guardian.png             32x32    la bola, mirando a la DERECHA
    """

    WALK_FILE = "guardian_tirador.png"
    ATTACK_FILE = "guardian_tirador_disparo.png"
    WEAPON_FILE = None

    # Colores del muneco de reemplazo
    CLOTH = (40, 96, 112)
    DARK = (20, 52, 66)


class GuardianBolt(Shot):
    """Bola del Guardian Tirador: vuela derecho (no rebota), a la misma
    velocidad que la bola de fuego del jugador. Se apaga al tocar una
    pared o al llegar a su alcance."""

    damage = GSHOOT_DAMAGE
    knockback = GSHOOT_KNOCKBACK

    def __init__(self, pos, angle_deg):

        super().__init__(pos, angle_deg)

        self.angle = angle_deg
        self.vel = pygame.Vector2(GSHOOT_BOLT_SPEED, 0).rotate(angle_deg)

        self.rect = pygame.Rect(0, 0, GSHOOT_BOLT_HITBOX, GSHOOT_BOLT_HITBOX)
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        self.range_left = GSHOOT_BOLT_RANGE

    def update(self, dt, collision_map):

        self.t += dt

        if self.dead:
            return

        dist = self.vel.length() * dt

        # De a pasitos para no atravesar paredes finas si un frame tarda
        steps = max(1, math.ceil(dist / 3.0))
        step = dist / steps

        move = self.vel.normalize() * step if self.vel.length_squared() > 0 else None

        if move is None:
            self.dead = True
            return

        for _ in range(steps):

            self.pos += move
            self.range_left -= step

            self.rect.center = (round(self.pos.x), round(self.pos.y))

            if self.range_left <= 0 or not self._free(self.rect, collision_map):

                self.dead = True

                return

    def draw(self, screen, camera, art=None):

        img = _gshoot_bolt_sprite(camera.zoom, self.angle)

        center = camera.apply(self.rect).center

        screen.blit(img, img.get_rect(center=center))


class GuardianShooter(Guardian):
    """Del tamano del jugador. Pasea tranquilo; cuando tu luz lo toca (o
    le pegas) se despierta y NO se acerca a pegarte: toma distancia (se
    aleja si te acercas, se acerca si te alejas y da vueltas a tu
    alrededor) y te dispara bolas como las tuyas. Antes de disparar queda
    quieto un instante cargando (aviso). Apunta adelantandose a donde vas
    a estar, y solo dispara cuando te ve (sin paredes en el medio)."""

    def __init__(self, x, y, spawn_delay=0.0):

        super().__init__(x, y, spawn_delay)

        self.hp = GSHOOT_HP
        self.max_hp = GSHOOT_HP
        self.max_speed = GSHOOT_MOVE_SPEED

        self.target_vel = pygame.Vector2()
        self._prev_target = None

        self.strafe_dir = random.choice((-1, 1))
        self.strafe_t = random.uniform(*GSHOOT_STRAFE_TIME)

        # Que no disparen todos juntos apenas se despiertan
        self.cooldown = random.uniform(0.3, 0.9)

        self._shots = []

    # ---------- disparo ----------

    def take_shots(self):
        """Las bolas que acaba de soltar (y se vacia la lista)."""

        shots, self._shots = self._shots, []

        return shots

    def _line_clear(self, a, b, collision_map):
        """True si no hay paredes ni bloques entre `a` y `b`."""

        a = pygame.Vector2(a)
        b = pygame.Vector2(b)

        steps = max(1, int(a.distance_to(b) // 4))

        probe = pygame.Rect(0, 0, 4, 4)

        for i in range(1, steps + 1):

            p = a.lerp(b, i / steps)

            probe.center = (round(p.x), round(p.y))

            if not (self.room.contains(probe) and collision_map.can_move(probe)):
                return False

        return True

    def _lead_point(self, target):
        """Donde va a estar el jugador cuando llegue la bola (puntería
        con intercepcion: usa la velocidad real del jugador y la de la
        bola)."""

        origin = self.pos
        d = target - origin
        v = self.target_vel
        speed = GSHOOT_BOLT_SPEED

        # |d + v*t| = speed*t  ->  a*t^2 + b*t + c = 0
        a = v.dot(v) - speed * speed
        b = 2.0 * d.dot(v)
        c = d.dot(d)

        t = None

        if abs(a) < 1e-6:

            if abs(b) > 1e-6:
                t = -c / b

        else:

            disc = b * b - 4.0 * a * c

            if disc >= 0:

                root = math.sqrt(disc)

                times = [
                    x for x in ((-b - root) / (2.0 * a), (-b + root) / (2.0 * a))
                    if x > 0
                ]

                if times:
                    t = min(times)

        if t is None or t <= 0:
            t = d.length() / speed

        t = min(t, GSHOOT_LEAD_MAX)

        point = pygame.Vector2(target) + v * t

        # Si el jugador corre contra una pared, no le apunta afuera de la sala
        point.x = max(self.room.left + 4, min(self.room.right - 4, point.x))
        point.y = max(self.room.top + 4, min(self.room.bottom - 4, point.y))

        return point

    def _aim_angle(self, target):
        """Angulo (radianes) hacia donde hay que tirar para pegarte."""

        point = self._lead_point(target)

        direction = point - self.pos

        if direction.length_squared() < 0.01:
            direction = pygame.Vector2(target) - self.pos

        if direction.length_squared() < 0.01:
            return self.aim

        return math.atan2(direction.y, direction.x)

    def _fire(self):

        direction = pygame.Vector2(math.cos(self.aim), math.sin(self.aim))

        start = self.pos + direction * GSHOOT_MUZZLE

        shot = GuardianBolt(start, math.degrees(self.aim))
        shot.room = self.room

        self._shots.append(shot)

    # ---------- movimiento ----------

    def _keep_distance(self, dt, toward, dist, can_see, collision_map):
        """Retrocede / se acerca / da vueltas segun la distancia."""

        side = self.strafe_dir

        self.strafe_t -= dt

        if self.strafe_t <= 0:

            self.strafe_dir = side = -side
            self.strafe_t = random.uniform(*GSHOOT_STRAFE_TIME)

        perp = pygame.Vector2(-toward.y, toward.x) * side

        if dist < GSHOOT_MIN_DIST:

            # Se aleja (prefiere irse de costado, asi no se encajona)
            d = self._walk(
                dt, -toward, GSHOOT_RETREAT_SPEED, collision_map,
                angles=(0, 40 * side, -40 * side, 80 * side, -80 * side)
            )

            if d is None:
                # Arrinconado: da vueltas igual (y sigue disparando)
                d = self._walk(
                    dt, perp, GSHOOT_MOVE_SPEED, collision_map,
                    angles=(0, 30, -30)
                )

        elif dist > GSHOOT_MAX_DIST:

            d = self._walk(
                dt,
                self.nav_dir(self.last_target, collision_map, dt),
                GSHOOT_MOVE_SPEED,
                collision_map,
            )

            self.anti_stuck(
                dt, collision_map, self.last_target, GSHOOT_MOVE_SPEED
            )

        else:

            # Dentro de su distancia: da vueltas. Si hay una pared en el
            # medio, tambien: asi cambia de angulo hasta verte.
            d = self._walk(
                dt, perp, GSHOOT_MOVE_SPEED, collision_map,
                angles=(0, 25, -25)
            )

            if d is None:
                self.strafe_dir = -side

        if d is not None:
            self.moving = True

        self._face(toward)

    # ---------- actualizar ----------

    def update(self, dt, target, collision_map, light_on, light_radius):

        target = pygame.Vector2(target)
        self.last_target = target.copy()

        self.anim_t += dt
        self.moving = False

        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

        if self.spawning:

            self.spawn_t -= dt
            self._prev_target = target.copy()

            return

        # Velocidad del jugador, suavizada (para adelantar la punteria)
        if self._prev_target is not None and dt > 0:

            raw = (target - self._prev_target) / dt

            if raw.length() > 140.0:
                raw.scale_to_length(140.0)

            self.target_vel += (raw - self.target_vel) * min(1.0, dt * 10.0)

        self._prev_target = target.copy()

        if self.cooldown > 0:
            self.cooldown = max(0.0, self.cooldown - dt)

        to_player = target - self.pos
        dist = to_player.length()
        toward = to_player / dist if dist > 0.01 else pygame.Vector2(1, 0)

        # ---- paseando tranquilo: la luz lo despierta ----
        if self.phase == self.WANDER:

            if light_on and dist <= light_radius:

                self.phase = self.CHASE

            else:

                self.turn_t -= dt

                if self.turn_t <= 0:

                    self.heading = self.heading.rotate(random.uniform(-80, 80))
                    self.turn_t = random.uniform(*GUARDIAN_TURN_TIME)

                d = self._walk(
                    dt, self.heading, GSHOOT_WANDER_SPEED, collision_map,
                    angles=(0, 40, -40, 90, -90, 140, -140, 180)
                )

                if d is not None:
                    self.heading = d
                    self.moving = True
                    self._face(d)

                return

        # ---- cargando: quieto, apuntandote (aviso) ----
        if self.phase == self.WINDUP:

            self.phase_t += dt

            want = self._aim_angle(target)
            diff = (want - self.aim + math.pi) % math.tau - math.pi
            self.aim += diff * min(1.0, GSHOOT_AIM_TURN * dt)

            self._face(pygame.Vector2(math.cos(self.aim), math.sin(self.aim)))

            if self.phase_t >= GSHOOT_AIM_TIME:

                # Se corto la linea (te metiste detras de algo): no dispara
                if not self._line_clear(self.pos, target, collision_map):

                    self.phase = self.CHASE
                    self.cooldown = 0.3

                    return

                # Justo antes de soltarla, apunta lo mas fino posible
                self.aim = self._aim_angle(target)

                self._fire()

                self.phase = self.SWING
                self.phase_t = 0.0
                self.cooldown = GSHOOT_COOLDOWN

            return

        # ---- recien disparo: quieto un ratito ----
        if self.phase == self.SWING:

            self.phase_t += dt

            if self.phase_t >= GSHOOT_RECOVER:
                self.phase = self.CHASE

            return

        # ---- despierto: toma distancia y dispara ----
        can_see = False

        if self.cooldown <= 0 or dist <= GSHOOT_MAX_DIST:

            can_see = self._line_clear(self.pos, target, collision_map)

        if (
            can_see
            and self.cooldown <= 0
            and dist <= GSHOOT_MAX_DIST + 25.0
        ):

            self.phase = self.WINDUP
            self.phase_t = 0.0
            self.aim = self._aim_angle(target)

            return

        self._keep_distance(dt, toward, dist, can_see, collision_map)

    # ---------- dibujo ----------

    def _draw_attack(self, screen, camera, dest, art):
        """Mientras carga se ve una bolita creciendo en la punta."""

        if self.phase != self.WINDUP:
            return

        zoom = camera.zoom

        direction = pygame.Vector2(math.cos(self.aim), math.sin(self.aim))

        pos = pygame.Vector2(dest.center) + direction * GSHOOT_MUZZLE * zoom

        k = min(1.0, self.phase_t / GSHOOT_AIM_TIME)

        radius = max(2, int((1.0 + 2.5 * k) * zoom))

        center = (round(pos.x), round(pos.y))

        pygame.draw.circle(screen, (120, 50, 200), center, radius)
        pygame.draw.circle(screen, (190, 130, 255), center, max(1, int(radius * 0.65)))
        pygame.draw.circle(screen, (245, 230, 255), center, max(1, int(radius * 0.3)))


# ---------------------------------------------------------------
# Cofre del premio
# ---------------------------------------------------------------

class RewardChest:
    """Aparece al ganar la oleada, brilla cada vez mas y explota."""

    APPEAR_TIME = 0.6
    GLOW_TIME = 2.4
    OPEN_TIME = 0.5
    SIZE = 20                 # unidades del mundo (igual que los cofres)

    def __init__(self, x, y):

        self.x = x
        self.y = y

        self.t = 0.0
        self.phase = "appear"      # appear -> glow -> open
        self.done = False

        self._glow_cache = {}

    # ---------- logica ----------

    def update(self, dt):
        """Devuelve True justo el frame en que explota."""

        self.t += dt

        if self.phase == "appear" and self.t >= self.APPEAR_TIME:
            self.phase = "glow"

        if self.phase == "glow" and self.t >= (
            self.APPEAR_TIME + self.GLOW_TIME
        ):

            self.phase = "open"
            self.t = 0.0

            return True

        if self.phase == "open" and self.t >= self.OPEN_TIME:
            self.done = True

        return False

    @property
    def glow_k(self):
        """0 a 1: cuanto falta para que explote."""

        if self.phase == "appear":
            return 0.0

        if self.phase == "open":
            return 1.0

        return min(1.0, (self.t - self.APPEAR_TIME) / self.GLOW_TIME)

    def light(self):
        """(x, y, radio en pixeles de pantalla) para iluminar."""

        if self.phase == "appear":

            return (
                self.x, self.y,
                quantize_radius(60 * (self.t / self.APPEAR_TIME))
            )

        k = self.glow_k

        pulse = math.sin(self.t * (6 + 14 * k))

        return (
            self.x, self.y, quantize_radius(95 + 55 * k + 18 * pulse)
        )

    # ---------- dibujo ----------

    def _sprite(self, name, zoom):

        px = int(self.SIZE * zoom)

        return load_image(CHEST_DIR / name, (px, px))

    def _glow_surface(self, radius):

        radius = max(4, int(radius))

        if radius not in self._glow_cache:

            surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

            for r in range(radius, 0, -3):

                a = int(150 * (1 - r / radius) ** 1.6)

                pygame.draw.circle(
                    surf, (255, 210, 90, a), (radius, radius), r
                )

            self._glow_cache[radius] = surf

        return self._glow_cache[radius]

    def _center_px(self, camera):

        return (
            int(self.x * camera.zoom - camera.x),
            int(self.y * camera.zoom - camera.y)
        )

    def draw(self, screen, camera):
        """El cofre en si (va debajo de la oscuridad)."""

        if self.phase == "open" and self.t > 0.15:
            sprite = self._sprite("cofre_abierto.png", camera.zoom)
        else:
            sprite = self._sprite("cofre_cerrado.png", camera.zoom)

        if sprite is None:
            return

        cx, cy = self._center_px(camera)

        dx = 0
        dy = 0

        if self.phase == "appear":

            # Cae desde arriba con rebotito
            k = min(1.0, self.t / self.APPEAR_TIME)
            fall = (1 - k) ** 2

            dy = -int(fall * 26 * camera.zoom)

        elif self.phase == "glow":

            # Tiembla cada vez mas fuerte antes de explotar
            k = self.glow_k

            dx = int(math.sin(self.t * 70) * (1 + 4 * k))

        if self.phase == "glow" and self.glow_k > 0.5:

            sprite = sprite.copy()

            add = int(140 * (self.glow_k - 0.5) * 2)

            sprite.fill(
                (add, add, add // 2, 0),
                special_flags=pygame.BLEND_RGB_ADD
            )

        screen.blit(sprite, sprite.get_rect(center=(cx + dx, cy + dy)))

    def draw_glow(self, screen, camera):
        """El brillo (va encima de la oscuridad)."""

        if self.phase == "appear":
            return

        k = self.glow_k

        radius = (20 + 30 * k + 4 * math.sin(self.t * 10)) * camera.zoom

        # Por pasos de 16 px, asi se reutilizan las superficies
        radius = max(16, int(round(radius / 16.0)) * 16)

        glow = self._glow_surface(radius)

        cx, cy = self._center_px(camera)

        screen.blit(glow, glow.get_rect(center=(cx, cy)))


# ---------------------------------------------------------------
# La sala
# ---------------------------------------------------------------

# ---------------------------------------------------------------
# Las salas de combate (una config por sala)
# ---------------------------------------------------------------

class ArenaConfig:
    """Todo lo que cambia de una sala de oleadas a otra."""

    def __init__(self, key, title, room, trigger, exit_pos, gate,
                 table, rewards, last_wave, save_wave, save_done,
                 show_total=False,
                 sealed_text="Mapa completado: la sala esta cerrada",
                 done_text="Mapa completado! La sala se cerro para siempre"):

        self.key = key
        self.title = title
        self.room = room
        self.trigger = trigger
        self.exit_pos = exit_pos
        self.gate = gate
        self.table = table
        self.rewards = rewards
        self.last_wave = last_wave
        self.save_wave = save_wave        # clave en la partida: oleada que sigue
        self.save_done = save_done        # clave en la partida: sala completada
        self.show_total = show_total      # "Oleada 1/2" en el cartel
        self.sealed_text = sealed_text
        self.done_text = done_text


# Sala grande de la DERECHA: 10 oleadas
RIGHT_ARENA = ArenaConfig(
    "right", "Sala de combate",
    ROOM, TRIGGER, EXIT_POS, GATE,
    WAVE_COMPOSITION, WAVE_REWARDS, LAST_WAVE,
    "arena_wave", "arena_completed",
)

# ---------------------------------------------------------------
# Sala grande de la IZQUIERDA: solo 2 oleadas.
#   Oleada 1: mobs de siempre.
#   Oleada 2: el Guardian (mismo tamano que el personaje).
# Cada numero: (pinos, troncos, mosquitos, hongunes, guardianes, tiradores)
# ---------------------------------------------------------------



LEFT_WAVE_REWARDS = {1: 40, 2: 90}

LEFT_LAST_WAVE = 2

LEFT_ARENA = ArenaConfig(
    "left", "Sala del Guardian",
    ROOM_LEFT, TRIGGER_LEFT, EXIT_POS_LEFT, GATE_LEFT,
    LEFT_WAVE_COMPOSITION, LEFT_WAVE_REWARDS, LEFT_LAST_WAVE,
    "arena_left_wave", "arena_left_completed",
    sealed_text="Sala completada: esta cerrada",
    done_text="Sala completada! Se cerro para siempre",
)


class Arena:

    IDLE = "idle"
    MENU = "menu"
    WAVE = "wave"
    CLEAR = "clear"
    COLLECT = "collect"

    PANEL_SIZE = (420, 300)
    BUTTON_SIZE = (260, 56)

    BUTTONS = ["exit", "escape", "noescape"]

    BUTTON_FILES = {
        "exit": "btn_salir",
        "escape": "btn_jugar_escape",
        "noescape": "btn_jugar_sin_escape",
    }

    BUTTON_LABELS = {
        "exit": "Salir",
        "escape": "Jugar con escape",
        "noescape": "Jugar sin escape  X2 premio",
    }

    def __init__(self, screen_size, cfg=None):

        # Que sala es (la derecha por defecto, o la de la izquierda)
        self.cfg = cfg or RIGHT_ARENA

        self.size = screen_size

        self.state = self.IDLE

        # True = puede abrir el menu al pisar la sala. Se desarma al
        # abrirlo y se arma de nuevo cuando el jugador sale.
        self.armed = True

        self.wave = 1
        self.mode = None            # "escape" / "noescape"

        self.enemies = []
        self.shots = []
        self.art = EnemyArt()
        self.tronco_art = TroncoArt()
        self.mosquito_art = MosquitoArt()
        self.hongun_art = HongunArt()
        self.destello_art = DestelloArt()
        self.golem_art = GolemArt()
        self.guardian_art = GuardianArt()
        self.shooter_art = GuardianShooterArt()
        self.blasts = []            # explosiones de hongunes (aro + luz)
        self.mosquito_alert = False

        self.chest = None
        self.reward = 0
        self.reward_coins = []

        self.banner_t = 0.0
        self.collect_t = 0.0
        self.last_death = None
        self.gate_on = False

        # Mapa completado: la sala queda cerrada para siempre
        self.completed = False
        self.final_clear = False    # True mientras se cobra la oleada final
        self._sealed_msg_t = -10.0

        self.particles = []
        self.ring_t = None
        self.ring_pos = (0, 0)
        self.boom_light_t = None

        self._gate_time = 0.0

        # ---------- imagenes ----------

        w, h = screen_size

        self.dim = pygame.Surface((w, h), pygame.SRCALPHA)
        self.dim.fill((0, 0, 0, 150))

        self.panel_img = load_image(
            COMBAT_DIR / "panel_sala_combate.png", self.PANEL_SIZE
        )

        self.hud_img = load_image(
            COMBAT_DIR / "hud_oleada.png", (180, 40)
        )

        self.banner_img = load_image(
            COMBAT_DIR / "pantalla_oleada_completa.png", (420, 200)
        )

        self.map_banner_img = load_image(
            COMBAT_DIR / "pantalla_mapa_completado.png", (420, 200)
        )

        self.sealed_img = load_image(
            COMBAT_DIR / "sala_sellada.png", (40, 160)
        )

        self.coin_icon = load_image(HUD_DIR / "icon_moneda.png", (22, 22))
        self.gem_icon = get_gem_icon()

        self.btn_imgs = {}

        for key, name in self.BUTTON_FILES.items():

            self.btn_imgs[key] = (
                load_image(COMBAT_DIR / f"{name}.png", self.BUTTON_SIZE),
                load_image(COMBAT_DIR / f"{name}_hover.png", self.BUTTON_SIZE),
            )

        # ---------- posiciones del menu ----------

        self.panel_rect = pygame.Rect(0, 0, *self.PANEL_SIZE)
        self.panel_rect.center = (w // 2, h // 2)

        self.button_rects = {}

        for i, key in enumerate(self.BUTTONS):

            rect = pygame.Rect(0, 0, *self.BUTTON_SIZE)

            rect.midtop = (
                self.panel_rect.centerx,
                self.panel_rect.top + 78 + i * 70
            )

            self.button_rects[key] = rect

    # ---------- estado ----------

    @property
    def menu_open(self):

        return self.state == self.MENU

    @property
    def active(self):

        return self.state in (self.WAVE, self.CLEAR, self.COLLECT)

    @property
    def current_reward(self):
        """Premio de la oleada actual (con el X2 si es sin escape)."""

        mult = NO_ESCAPE_MULT if self.mode == "noescape" else 1

        return base_reward(self.wave, self.cfg.rewards) * mult

    def targets(self):
        """Lo que el fosforo puede golpear."""

        return [e for e in self.enemies if not e.spawning and not e.dead and not getattr(e, "attached", False)]

    def hurt_in_radius(self, center, radius, damage):
        """Quema a los enemigos que estan dentro de la luz (polvora).

        center, radius -> en unidades del mundo.
        Resta vida directo (sin empujon ni atontamiento: es un dano
        que se repite varias veces por segundo) y los hace parpadear.
        """

        cx, cy = center

        for enemy in self.targets():

            size = max(enemy.rect.width, enemy.rect.height) / 2

            dist = math.hypot(
                enemy.rect.centerx - cx,
                enemy.rect.centery - cy
            )

            if dist <= radius + size:

                enemy.hp -= damage
                enemy.flash = max(enemy.flash, ENEMY_FLASH_TIME)

    def light_sources(self):
        """Luces extra (el cofre ilumina y la explosion tambien)."""

        sources = []

        if self.chest is not None and not self.chest.done:
            sources.append(self.chest.light())

        # Cada hongun que recarga da un poco de luz, y su explosion tambien
        for enemy in self.enemies:

            if isinstance(enemy, (Hongun, Destello)):

                light = enemy.light()

                if light is not None:
                    sources.append(light)

        for blast in self.blasts:

            k = blast["t"] / HONGUN_BLAST_TIME

            sources.append((
                blast["x"], blast["y"],
                quantize_radius(70 + 110 * (1 - k))
            ))

        if self.boom_light_t is not None:

            k = self.boom_light_t / 0.7

            sources.append((
                self.ring_pos[0], self.ring_pos[1],
                quantize_radius(120 + 200 * (1 - k))
            ))

        return sources

    # ---------- menu ----------

    def _open_menu(self, game):

        self.state = self.MENU
        self.armed = False
        self.banner_t = 0.0

        game.melee.cancel()

    def update_menu(self, dt):
        """El juego esta en pausa mientras el menu esta abierto."""

        self._gate_time += dt

    def handle_event(self, game, event):

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:

            self._leave(game)

            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            for key, rect in self.button_rects.items():

                if rect.collidepoint(event.pos):

                    if key == "exit":
                        self._leave(game)
                    else:
                        self._begin(game, key)

                    return

    def _begin(self, game, mode):

        if not game.has_match:

            game.show_message("Necesitas una luz encendida para pelear")

            return

        self.mode = mode
        self.state = self.WAVE
        self.banner_t = 0.0
        self.last_death = None

        if mode == "noescape":
            self._close_gate(game)

        self._spawn_wave(game)

        game.show_message(f"Oleada {self.wave}")

    # ---------- barrera ----------

    def _close_gate(self, game):

        if not self.gate_on:

            game.collision_map.obstacles.append(self.cfg.gate.copy())
            self.gate_on = True

    def _open_gate(self, game):

        # Mapa completado: la entrada no se vuelve a abrir
        if self.completed:
            return

        if self.gate_on:

            obstacles = game.collision_map.obstacles

            if self.cfg.gate in obstacles:
                obstacles.remove(self.cfg.gate)

            self.gate_on = False

    def restore_completed(self, game):
        """Al cargar una partida con el mapa completado: la sala queda
        cerrada. Si el jugador quedo adentro (o pisando la entrada) se
        lo saca afuera para que no quede atrapado."""

        if not self.completed:
            return

        self._seal(game)

    def _seal(self, game):
        """Cierra la entrada para siempre."""

        p = game.player

        if self.cfg.room.collidepoint(p.rect.center) or p.rect.colliderect(
            self.cfg.gate.inflate(24, 24)
        ):
            self._teleport_out(game)

        self._close_gate(game)

    # ---------- oleadas ----------

    def _spawn_wave(self, game):

        (pinos, troncos, mosquitos, honguns, guardians,
         shooters, destellos, golems) = wave_composition(
            self.wave, self.cfg.table
        )

        kinds = (
            ["pino"] * pinos + ["tronco"] * troncos
            + ["mosquito"] * mosquitos + ["hongun"] * honguns
            + ["guardian"] * guardians + ["tirador"] * shooters
            + ["destello"] * destellos + ["golem"] * golems
        )
        random.shuffle(kinds)

        hp = min(ENEMY_HP_MAX, ENEMY_HP_BASE + self.wave)
        tronco_hp = min(ENEMY_HP_MAX, hp + TRONCO_HP_EXTRA)
        speed = min(ENEMY_SPEED_MAX, ENEMY_SPEED_BASE + ENEMY_SPEED_STEP * self.wave)

        cmap = game.collision_map
        player_pos = pygame.Vector2(game.player.rect.center)
        corners = [
            (self.cfg.room.left + 40, self.cfg.room.top + 30),
            (self.cfg.room.right - 40, self.cfg.room.top + 30),
            (self.cfg.room.left + 40, self.cfg.room.bottom - 30),
            (self.cfg.room.right - 40, self.cfg.room.bottom - 30),
        ]

        self.enemies = []
        self.shots = []
        self.blasts = []

        for i, kind in enumerate(kinds):
            pos = None
            min_dist = 135 if kind in ("mosquito", "hongun", "guardian", "tirador", "destello", "golem") else 110

            if kind == "mosquito":
                hitbox = MOSQUITO_HITBOX
            elif kind == "hongun":
                hitbox = HONGUN_HITBOX
            elif kind == "destello":
                hitbox = DESTELLO_HITBOX
            elif kind == "golem":
                hitbox = GOLEM_HITBOX
            elif kind in ("guardian", "tirador"):
                hitbox = GUARDIAN_HITBOX
            else:
                hitbox = ENEMY_HITBOX

            for _ in range(120):
                x = random.randint(self.cfg.room.left + 16, self.cfg.room.right - 16)
                y = random.randint(self.cfg.room.top + 16, self.cfg.room.bottom - 16)
                probe = pygame.Rect(0, 0, *hitbox)
                probe.center = (x, y)
                if pygame.Vector2(x, y).distance_to(player_pos) < min_dist:
                    continue
                if not (self.cfg.room.contains(probe) and cmap.can_move(probe)):
                    continue
                if any(pygame.Vector2(x, y).distance_to(e.pos) < 18 for e in self.enemies):
                    continue
                pos = (x, y)
                break

            if pos is None:
                pos = corners[i % len(corners)]

            delay = i * 0.15
            if kind == "tronco":
                enemy = Tronco(pos[0], pos[1], tronco_hp, spawn_delay=delay)
            elif kind == "mosquito":
                enemy = Mosquito(pos[0], pos[1], MOSQUITO_HP, spawn_delay=delay)
            elif kind == "hongun":
                enemy = Hongun(pos[0], pos[1], spawn_delay=delay)
            elif kind == "destello":
                enemy = Destello(pos[0], pos[1], spawn_delay=delay)
                if self.wave <= DESTELLO_EARLY_WAVES:
                    enemy.alert_time = DESTELLO_ALERT_TIME_EARLY
            elif kind == "golem":
                enemy = Golem(pos[0], pos[1], spawn_delay=delay)
            elif kind == "guardian":
                enemy = Guardian(pos[0], pos[1], spawn_delay=delay)
            elif kind == "tirador":
                enemy = GuardianShooter(pos[0], pos[1], spawn_delay=delay)
            else:
                enemy = Enemy(pos[0], pos[1], hp, speed, spawn_delay=delay)

            # Clave de la enciclopedia (para marcarlo como descubierto)
            enemy.codex_key = (
                "guardian_tirador" if kind == "tirador" else kind
            )

            # Se mueve solo dentro de ESTA sala
            enemy.room = self.cfg.room

            self.enemies.append(enemy)

    def _wave_cleared(self, game):

        pos = self.last_death or self.cfg.room.center

        self.reward = self.current_reward
        self.chest = RewardChest(pos[0], pos[1])
        self.state = self.CLEAR

        # Ya no quedan enemigos: se puede salir
        self._open_gate(game)

    def _explode(self, game):
        """El cofre explota y tira las monedas del premio."""

        cx, cy = self.chest.x, self.chest.y

        self.ring_t = 0.0
        self.ring_pos = (cx, cy)
        self.boom_light_t = 0.0

        for _ in range(45):

            angle = random.uniform(0, math.tau)
            speed = random.uniform(30, 120)
            life = random.uniform(0.4, 0.9)

            self.particles.append({
                "x": cx,
                "y": cy - 4,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed - 30,
                "life": life,
                "max": life,
                "color": random.choice([
                    (255, 235, 140), (255, 200, 70),
                    (255, 255, 255), (255, 160, 50)
                ]),
            })

        # Monedas: como mucho MAX_COIN_ITEMS dibujadas, cada una con
        # su parte del premio (la suma da exacto el premio)
        items = max(1, min(self.reward, MAX_COIN_ITEMS))

        base, extra = divmod(self.reward, items)

        self.reward_coins = []

        for n in range(items):

            coin = WorldItem("moneda", cx, cy)

            coin.value = base + (1 if n < extra else 0)

            target = self._coin_target(game, cx, cy)

            coin.start_fly((cx, cy), target, delay=n * 0.025, height=18)

            self.reward_coins.append(coin)

        game.world_items.extend(self.reward_coins)

        self.state = self.COLLECT
        self.collect_t = 0.0
        self.banner_t = BANNER_TIME

        # Oleada final: el cofre tambien tira una gema y el mapa queda
        # completado. La gema se cuenta ya (asi no se pierde si cerras
        # el juego mientras juntas las monedas); value = 0 evita
        # contarla dos veces al agarrarla.
        if self.wave == self.cfg.last_wave:

            game.gems += 1

            gem = WorldItem("gema", cx, cy)
            gem.value = 0

            gem.start_fly(
                (cx, cy), self._coin_target(game, cx, cy),
                delay=0.25, height=26, duration=0.6
            )

            self.reward_coins.append(gem)
            game.world_items.append(gem)

            self.final_clear = True
            self.completed = True
            self.banner_t = BANNER_TIME_FINAL

        # La siguiente oleada ya queda lista
        self.wave += 1

    def _coin_target(self, game, cx, cy):

        for _ in range(30):

            angle = random.uniform(0, math.tau)
            dist = random.uniform(14, 46)

            x = cx + math.cos(angle) * dist
            y = cy + math.sin(angle) * dist

            if self.cfg.room.collidepoint(x, y) and game.collision_map.point_is_walkable(x, y):
                return (x, y)

        return (cx, cy + 14)

    def _coins_left(self, game):

        return [c for c in self.reward_coins if c in game.world_items]

    def _credit_leftover(self, game):
        """Las monedas que quedaron en el piso se suman solas."""

        for coin in self._coins_left(game):

            game.world_items.remove(coin)

            # La gema ya se conto al explotar el cofre (value = 0)
            if coin.item_id == "gema":
                game.gems += getattr(coin, "value", 1)
            else:
                game.add_coins(getattr(coin, "value", 1))

        self.reward_coins = []

    # ---------- salir / terminar ----------

    def _teleport_out(self, game):

        p = game.player

        p.rect.center = self.cfg.exit_pos
        p.image_rect.midbottom = (p.rect.centerx, p.rect.bottom + 3)

        p.kb_vel = pygame.Vector2()

        game.camera.update(p)
        game.melee.cancel()

    def _release_player(self, game):
        """Por si el jugador quedo agarrado por un golem (termina la
        oleada, sale de la sala, muere...): lo deja libre."""

        p = game.player

        p.grabbed = False
        p.grab_lift = 0.0

    def _end_run(self, game):

        self._release_player(game)
        self._credit_leftover(game)
        self._open_gate(game)

        self.enemies = []
        self.shots = []
        self.chest = None
        self.reward = 0
        self.mode = None
        self.banner_t = 0.0
        self.final_clear = False
        self.state = self.IDLE

        # Mapa completado: la entrada queda cerrada para siempre
        if self.completed:
            self._seal(game)

    def _finish_map(self, game):
        """Termino de cobrarse la oleada final: se saca al jugador de la
        sala, la entrada se cierra para siempre y se guarda."""

        self._end_run(game)
        self._teleport_out(game)

        game.show_message(self.cfg.done_text)
        game.save_progress()

    def _leave(self, game):
        """Boton Salir (o ESC en el menu)."""

        self._end_run(game)
        self._teleport_out(game)

    def _player_died(self, game):
        """Morir en la sala (con o sin escape) es perder de verdad:
        termina la partida."""

        self._end_run(game)

        game.state = "dying"
        game.fade_alpha = 0

    # ---------- update ----------

    def _update_fx(self, dt):

        for p in self.particles:

            p["life"] -= dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vx"] *= max(0.0, 1 - 2.0 * dt)
            p["vy"] *= max(0.0, 1 - 2.0 * dt)

        self.particles = [p for p in self.particles if p["life"] > 0]

        if self.ring_t is not None:

            self.ring_t += dt

            if self.ring_t > 0.5:
                self.ring_t = None

        if self.boom_light_t is not None:

            self.boom_light_t += dt

            if self.boom_light_t > 0.7:
                self.boom_light_t = None

        for blast in self.blasts:
            blast["t"] += dt

        self.blasts = [b for b in self.blasts if b["t"] < HONGUN_BLAST_TIME]

        self._gate_time += dt

    def update(self, game, dt):
        """Se llama una vez por frame con el juego en marcha."""

        self._update_fx(dt)

        # La alerta del mosquito solo vale durante la oleada
        if self.state != self.WAVE:
            self.mosquito_alert = False

        p = game.player

        if self.state == self.IDLE:

            # Mapa completado: no se abre mas el menu. Si te acercas a
            # la entrada cerrada te avisa.
            if self.completed:

                if (
                    p.rect.colliderect(self.cfg.gate.inflate(40, 30))
                    and self._gate_time - self._sealed_msg_t > 2.5
                ):
                    self._sealed_msg_t = self._gate_time
                    game.show_message(
                        self.cfg.sealed_text
                    )

                return

            center = p.rect.center

            if self.armed and self.cfg.trigger.collidepoint(center):
                self._open_menu(game)

            elif not self.armed and not self.cfg.room.collidepoint(center):
                self.armed = True

            return

        if self.state == self.MENU:
            return

        if self.banner_t > 0:
            self.banner_t = max(0.0, self.banner_t - dt)

        # Con escape podes irte caminando
        if not self.cfg.room.collidepoint(p.rect.center):

            if self.state == self.WAVE:

                game.show_message("Saliste de la sala. Oleada cancelada")

            elif self.state == self.CLEAR:

                # Se va antes de la explosion: el premio se cobra igual
                game.add_coins(self.reward)

                game.show_message(f"+{self.reward} monedas")

                # Oleada final: tambien se lleva la gema y el mapa queda
                # completado (si no, podria repetir la oleada 10)
                if self.wave == self.cfg.last_wave:

                    game.gems += 1

                    self.wave += 1
                    self.completed = True

                    game.show_message(
                        f"+{self.reward} monedas y 1 gema. "
                        "Mapa completado!"
                    )

                    game.save_progress()

            self._end_run(game)

            if self.completed:
                game.save_progress()

            return

        if self.state == self.WAVE:
            self._update_wave(game, dt)

        elif self.state == self.CLEAR:

            if self.chest.update(dt):
                self._explode(game)

        elif self.state == self.COLLECT:
            self._update_collect(game, dt)

    def _update_wave(self, game, dt):

        # Enciclopedia: cada enemigo que ya aparecio en la sala queda
        # descubierto en esta partida
        for e in self.enemies:

            key = getattr(e, "codex_key", None)

            if key and not e.spawning:
                game.discover_enemy(key)

        p = game.player
        target = p.rect.center
        body = pygame.Rect(0, 0, 10, 16)
        body.midbottom = (p.rect.centerx, p.rect.bottom)
        light_on = bool(game.has_match)
        light_world = game._light_radius() / game.camera.zoom if light_on else 0.0
        # Repelente: la luz espanta a los mosquitos mientras dura
        repel = light_on and game.repel_timer > 0

        for enemy in self.enemies:
            if isinstance(enemy, Mosquito):
                enemy.update(dt, target, game.collision_map, light_on, light_world, repel)
                if enemy.attached and enemy.damage_t <= 0.0:
                    game.take_damage(MOSQUITO_DAMAGE)
                    enemy.damage_t = MOSQUITO_DAMAGE_INTERVAL
            elif isinstance(enemy, GuardianShooter):
                # No pega: dispara bolas (se mueven y pegan con self.shots)
                enemy.update(dt, target, game.collision_map, light_on, light_world)
                self.shots.extend(enemy.take_shots())
            elif isinstance(enemy, Golem):
                enemy.update(dt, target, game.collision_map, others=self.enemies)
                self._golem_step(game, enemy, body, dt)
            elif isinstance(enemy, Guardian):
                enemy.update(dt, target, game.collision_map, light_on, light_world)
                if enemy.swing_hits(body.center):
                    # Su golpe es como el tuyo: si te toca, te saca vida
                    if p.hurt(enemy.pos):
                        game.take_damage(GUARDIAN_DAMAGE)
                        away = pygame.Vector2(body.center) - enemy.pos
                        if away.length_squared() > 0.01:
                            p.kb_vel = away.normalize() * GUARDIAN_KNOCKBACK
            else:
                if enemy.fixed:
                    enemy.light_radius = light_world
                enemy.update(dt, target, game.collision_map, self.enemies)
                if enemy.fixed:
                    self.shots.extend(enemy.take_shots())

        # Si el golem que te tenia murio (polvora, bola de fuego...) o ya
        # no hay ninguno agarrandote, quedas libre
        if p.grabbed and not any(
            isinstance(e, Golem) and e.holding and not e.dead
            for e in self.enemies
        ):
            self._release_player(game)

        self.mosquito_alert = any(
            isinstance(e, Mosquito) and e.alert and not e.dead
            for e in self.enemies
        )

        bounce_enemies(self.enemies, game.collision_map, target)

        for shot in self.shots:
            shot.update(dt, game.collision_map)

        damage = min(ENEMY_DAMAGE_MAX, ENEMY_DAMAGE + ENEMY_DAMAGE_STEP * (self.wave - 1))

        for enemy in self.enemies:
            if (enemy.spawning or enemy.touch_cd > 0 or enemy.dead
                    or not enemy.contact_damage or getattr(enemy, "attached", False)):
                continue
            if enemy.rect.colliderect(body):
                if p.hurt(enemy.pos):
                    game.take_damage(damage)
                enemy.bounce_from(body.center)

        for shot in self.shots:
            if shot.dead:
                continue
            if shot.rect.colliderect(body):
                if p.hurt(shot.pos):
                    # Las bolas del Guardian Tirador traen su propio dano
                    amount = getattr(shot, "damage", None)
                    game.take_damage(
                        amount if amount is not None
                        else damage * SHOT_DAMAGE_MULT
                    )
                    push = getattr(shot, "knockback", 0.0)
                    away = pygame.Vector2(body.center) - shot.pos
                    if push and away.length_squared() > 0.01:
                        p.kb_vel = away.normalize() * push
                shot.dead = True

        self.shots = [s for s in self.shots if not s.dead]

        # Hongunes que terminaron de recargar: explotan
        for enemy in self.enemies:
            if isinstance(enemy, Hongun) and enemy.boom and not enemy.boomed:
                enemy.boomed = True
                self._hongun_explode(game, enemy)

        # Destellos que te alcanzaron corriendo: explotan (flashbang)
        for enemy in self.enemies:
            if (
                isinstance(enemy, Destello)
                and enemy.can_explode
                and enemy.rect.colliderect(body)
            ):
                enemy.boom = True
                enemy.boomed = True
                enemy.hp = 0
                self._destello_explode(game, enemy)

        for enemy in self.enemies:
            if enemy.dead:
                self.last_death = (enemy.pos.x, enemy.pos.y)
                game.count_stat("kills")
                # El hongun que explota ya tiene su propio efecto
                if not getattr(enemy, "boom", False):
                    self._death_puff(enemy.pos)

        self.enemies = [e for e in self.enemies if not e.dead]

        if game.vida <= 0:
            self._player_died(game)
            return

        # La oleada termina solo cuando no queda NINGUN enemigo (los
        # mosquitos pegados tambien cuentan: aunque te chupen todos, la
        # partida sigue)
        if not self.enemies:
            self.shots = []
            self._wave_cleared(game)

    # ---------- golem ----------

    def _golem_step(self, game, enemy, body, dt):
        """Todo lo que pasa entre un golem y el jugador: agarrarlo,
        sostenerlo, apretar (escudo / vida) y soltarlo."""

        p = game.player

        # ---- empieza el agarre: lo tocó una vez y listo ----
        if (
            enemy.can_grab(body)
            and not p.grabbed
            and p.invuln_timer <= 0
        ):
            enemy.start_grab(pygame.Vector2(p.rect.center) - enemy.pos)

            p.grabbed = True
            p.kb_vel = pygame.Vector2()
            game.melee.cancel()

        # ---- lo tiene agarrado: lo acomoda en sus manos y lo levanta ----
        if enemy.holding:

            self._golem_hold(game, enemy, dt)

            # El apreton: se saca el escudo (o toda la vida de la luz)
            if enemy.take_squeeze():
                self._golem_squeeze(game, enemy)

        # ---- lo suelta: empujon e invulnerabilidad ----
        if enemy.take_release():

            p.grabbed = False
            p.grab_lift = 0.0

            # Te tira para el lado de donde viniste
            p.kb_vel = enemy.grab_dir * GOLEM_KNOCKBACK
            p.invuln_timer = max(p.invuln_timer, GOLEM_POST_INVULN)

    def _golem_hold(self, game, enemy, dt):
        """Mientras dura el agarre el jugador no se mueve ni pega: el
        golem lo va acomodando adelante de sus manos y lo levanta."""

        p = game.player

        hold = pygame.Vector2(
            enemy.rect.centerx, enemy.rect.bottom + GOLEM_HOLD_DY
        )
        cur = pygame.Vector2(p.rect.center)
        gap = hold - cur
        dist = gap.length()

        if dist > 0.5:

            nxt = cur + gap / dist * min(dist, GOLEM_HOLD_PULL * dt)

            test = p.rect.copy()
            test.center = (round(nxt.x), round(nxt.y))

            if game.collision_map.can_move(test):
                p.rect.center = test.center

        p.image_rect.midbottom = (p.rect.centerx, p.rect.bottom + 3)

        p.kb_vel = pygame.Vector2()
        p.grabbed = True
        p.grab_lift = enemy.lift

        game.melee.cancel()

    def _golem_squeeze(self, game, enemy):
        """El golem aprieta: te saca TODO el escudo; si no tenias
        escudo, te saca TODA la vida de la luz."""

        p = game.player
        pos = pygame.Vector2(p.rect.center)

        p.hurt_timer = p.HURT_TIME   # se pone rojo

        if game.escudo > 0:

            game.escudo = 0.0

            game.show_message("El Golem te saco todo el escudo!")

        else:

            game.vida = 0.0

            game.show_message("El Golem te aplasto: se apago tu luz!")

        # Polvo de piedra
        for _ in range(34):

            angle = random.uniform(0, math.tau)
            speed = random.uniform(25, 110)
            life = random.uniform(0.3, 0.8)

            self.particles.append({
                "x": pos.x,
                "y": pos.y - 6,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": life,
                "max": life,
                "color": random.choice([
                    (150, 150, 160), (110, 110, 122),
                    (190, 190, 198), (90, 80, 70)
                ]),
            })

    def _hongun_explode(self, game, enemy):
        """Explota el hongun: efecto, dano y empujon al jugador."""

        p = game.player
        pos = pygame.Vector2(enemy.pos)

        self.blasts.append({"x": pos.x, "y": pos.y, "t": 0.0})

        for _ in range(40):

            angle = random.uniform(0, math.tau)
            speed = random.uniform(30, 120)
            life = random.uniform(0.3, 0.7)

            self.particles.append({
                "x": pos.x,
                "y": pos.y - 3,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": life,
                "max": life,
                "color": random.choice([
                    (255, 255, 255), (235, 255, 220),
                    (120, 205, 110), (80, 175, 80), (255, 235, 140)
                ]),
            })

        body = pygame.Vector2(p.rect.center)

        if body.distance_to(pos) > HONGUN_BLAST_RADIUS:
            return

        # La explosion pega siempre, aunque el jugador estuviera en su
        # ratito de invulnerabilidad
        p.invuln_timer = 0.0
        p.hurt(pos)

        game.take_damage(HONGUN_DAMAGE)

        away = body - pos

        if away.length_squared() < 0.01:
            away = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

        p.kb_vel = away.normalize() * HONGUN_KNOCKBACK

    def _destello_explode(self, game, enemy):
        """Explota el destello: dano, empujon y pantalla en blanco."""

        p = game.player
        pos = pygame.Vector2(enemy.pos)
        body = pygame.Vector2(p.rect.center)

        # Pega siempre, aunque el jugador estuviera en su ratito de
        # invulnerabilidad
        p.invuln_timer = 0.0
        p.hurt(pos)

        game.take_damage(DESTELLO_DAMAGE)

        away = body - pos

        if away.length_squared() < 0.01:
            away = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))

        p.kb_vel = away.normalize() * DESTELLO_KNOCKBACK

        # El "pum": la pantalla se pone blanca (lo dibuja el juego)
        game.flashbang(pos.x, pos.y)

    def _death_puff(self, pos):

        for _ in range(10):

            angle = random.uniform(0, math.tau)
            speed = random.uniform(15, 50)

            self.particles.append({
                "x": pos.x,
                "y": pos.y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": 0.4,
                "max": 0.4,
                "color": (150, 105, 70),
            })

    def _update_collect(self, game, dt):

        self.collect_t += dt

        self.chest.update(dt)

        left = self._coins_left(game)

        done = not left and self.collect_t > 1.0

        # Oleada final: se espera a que se vea el cartel de mapa completado
        if self.final_clear:
            done = done and self.banner_t <= 0

        if done or self.collect_t > COLLECT_TIMEOUT:

            self.chest = None

            if self.final_clear:
                self._finish_map(game)
            else:
                self._open_menu(game)

    # ---------- dibujo ----------

    def draw_world(self, screen, camera):
        """Enemigos, cofre y barrera (debajo de la oscuridad)."""

        for enemy in self.enemies:
            if isinstance(enemy, Mosquito):
                enemy.draw(screen, camera, self.mosquito_art)
            elif isinstance(enemy, Hongun):
                enemy.draw(screen, camera, self.hongun_art)
            elif isinstance(enemy, Destello):
                enemy.draw(screen, camera, self.destello_art)
            elif isinstance(enemy, Golem):
                enemy.draw(screen, camera, self.golem_art)
            elif isinstance(enemy, GuardianShooter):
                enemy.draw(screen, camera, self.shooter_art)
            elif isinstance(enemy, Guardian):
                enemy.draw(screen, camera, self.guardian_art)
            else:
                enemy.draw(
                    screen, camera,
                    self.tronco_art if enemy.fixed else self.art
                )

        if self.chest is not None and not self.chest.done:
            self.chest.draw(screen, camera)

        # Mapa completado: entrada sellada (fija, no parpadea)
        if self.gate_on and self.completed:

            rect = camera.apply(self.cfg.gate)

            if self.sealed_img is not None:

                img = self.sealed_img

                if img.get_size() != rect.size:
                    img = pygame.transform.smoothscale(img, rect.size)

                screen.blit(img, rect)

            else:

                pygame.draw.rect(screen, (46, 46, 54), rect)
                pygame.draw.rect(screen, (120, 120, 134), rect, 2)

        elif self.gate_on:

            rect = camera.apply(self.cfg.gate)

            pulse = 0.5 + 0.5 * math.sin(self._gate_time * 6)

            bar = pygame.Surface(rect.size, pygame.SRCALPHA)
            bar.fill((255, 60, 50, int(90 + 90 * pulse)))

            screen.blit(bar, rect)

    def draw_fx(self, screen, camera):
        """Brillo, explosion y chispas (encima de la oscuridad)."""

        if self.chest is not None and not self.chest.done:
            self.chest.draw_glow(screen, camera)

        # Las bolas se ven siempre, aunque no las alumbres
        for shot in self.shots:
            shot.draw(screen, camera, self.tronco_art)

        # Brillo blanco de los hongunes que estan recargando
        for enemy in self.enemies:

            if isinstance(enemy, Hongun) and enemy.fuse_t > 0 and not enemy.dead:
                self._draw_hongun_glow(screen, camera, enemy)

        # Aro blanco de las explosiones de hongun
        for blast in self.blasts:

            k = blast["t"] / HONGUN_BLAST_TIME

            radius = int((4 + HONGUN_BLAST_RADIUS * k) * camera.zoom)

            cx = int(blast["x"] * camera.zoom - camera.x)
            cy = int(blast["y"] * camera.zoom - camera.y)

            ring = pygame.Surface((radius * 2 + 8, radius * 2 + 8), pygame.SRCALPHA)

            pygame.draw.circle(
                ring, (255, 255, 255, int(70 * (1 - k))),
                (radius + 4, radius + 4), radius
            )

            pygame.draw.circle(
                ring, (255, 255, 235, int(230 * (1 - k))),
                (radius + 4, radius + 4), radius,
                max(2, int(7 * (1 - k)))
            )

            screen.blit(ring, ring.get_rect(center=(cx, cy)))

        if self.ring_t is not None:

            k = self.ring_t / 0.5

            radius = int((6 + 46 * k) * camera.zoom)

            cx = int(self.ring_pos[0] * camera.zoom - camera.x)
            cy = int(self.ring_pos[1] * camera.zoom - camera.y)

            ring = pygame.Surface((radius * 2 + 8, radius * 2 + 8), pygame.SRCALPHA)

            pygame.draw.circle(
                ring,
                (255, 240, 170, int(220 * (1 - k))),
                (radius + 4, radius + 4),
                radius,
                max(2, int(8 * (1 - k)))
            )

            screen.blit(ring, ring.get_rect(center=(cx, cy)))

        for part in self.particles:

            alpha = max(0.0, part["life"] / part["max"])

            sx = int(part["x"] * camera.zoom - camera.x)
            sy = int(part["y"] * camera.zoom - camera.y)

            size = max(2, int(3 * camera.zoom * alpha))

            pygame.draw.circle(screen, part["color"], (sx, sy), size)

    def _draw_hongun_glow(self, screen, camera, enemy):
        """Resplandor blanco alrededor del hongun mientras recarga."""

        k = enemy.fuse_k

        blink = 0.5 + 0.5 * math.sin(enemy.anim_t * (14 + 36 * k))

        radius = max(4, int((10 + 16 * k) * camera.zoom))

        cx = int(enemy.pos.x * camera.zoom - camera.x)
        cy = int(enemy.pos.y * camera.zoom - camera.y)

        glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

        for i in range(4, 0, -1):

            alpha = int((25 + 55 * k) * (0.5 + 0.5 * blink) * (5 - i) / 4)

            pygame.draw.circle(
                glow, (255, 255, 255, alpha),
                (radius, radius), int(radius * i / 4)
            )

        screen.blit(glow, glow.get_rect(center=(cx, cy)))

    def draw_hud(self, screen):
        """Cartel de oleada arriba a la izquierda + aviso de victoria."""

        if not self.active:
            return

        # ---------- cartel de oleada ----------

        rect = pygame.Rect(18, 18, 180, 40)

        if self.hud_img is not None:

            screen.blit(self.hud_img, rect)

        else:

            pygame.draw.rect(screen, (138, 146, 158), rect, border_radius=8)
            pygame.draw.rect(screen, (84, 92, 104), rect, 3, border_radius=8)

        # En CLEAR todavia no se sumo la oleada; en COLLECT ya si
        number = self.wave - 1 if self.state == self.COLLECT else self.wave

        label = f"Oleada {number}"

        if self.cfg.show_total:
            label += f"/{self.cfg.last_wave}"

        draw_text(
            screen, label, 28, (255, 255, 255),
            center=rect.center
        )

        if self.state == self.WAVE:

            draw_text(
                screen, f"Enemigos: {len(self.enemies)}", 24,
                (235, 235, 235), topleft=(rect.left + 4, rect.bottom + 8)
            )

            premio_y = rect.bottom + 34

        else:

            premio_y = rect.bottom + 8

        premio = self.current_reward if self.state == self.WAVE else self.reward

        x = rect.left + 4

        if self.coin_icon is not None:

            screen.blit(self.coin_icon, (x, premio_y - 2))
            x += 28

        text_rect = draw_text(
            screen, f"{premio}", 26, (255, 225, 120),
            topleft=(x, premio_y)
        )

        if self.mode == "noescape":

            draw_text(
                screen, "X2", 26, (255, 150, 60),
                topleft=(text_rect.right + 8, premio_y)
            )

        # (la alerta del mosquito ahora la dibuja EffectsBar, arriba junto
        # a los cubitos de efectos: ui/effects_bar.py)

        # ---------- oleada completada ----------

        if self.banner_t > 0:
            self._draw_banner(screen)

    def _draw_banner(self, screen):

        w, h = self.size

        alpha = int(255 * min(1.0, self.banner_t / 0.5))

        rect = pygame.Rect(0, 0, 420, 200)
        rect.center = (w // 2, int(h * 0.30))

        layer = pygame.Surface(rect.size, pygame.SRCALPHA)
        local = layer.get_rect()

        final = self.final_clear

        img = self.map_banner_img if final else self.banner_img

        if img is not None:

            layer.blit(img, (0, 0))

        else:

            pygame.draw.rect(layer, (30, 30, 38, 225), local, border_radius=14)
            pygame.draw.rect(layer, (200, 200, 210), local, 3, border_radius=14)

            draw_text(
                layer,
                "Mapa completado!" if final else "Oleada completada!",
                40, (255, 240, 170),
                center=(local.centerx, 56)
            )

        if final:

            # Monedas a la izquierda, gema a la derecha
            y = local.centery + 28

            if self.coin_icon is not None:

                coin = pygame.transform.smoothscale(self.coin_icon, (40, 40))

                layer.blit(coin, coin.get_rect(center=(local.centerx - 130, y)))

            draw_text(
                layer, f"+{self.reward}", 56, (255, 225, 120),
                midleft=(local.centerx - 104, y)
            )

            gem = pygame.transform.smoothscale(self.gem_icon, (40, 40))

            layer.blit(gem, gem.get_rect(center=(local.centerx + 50, y)))

            draw_text(
                layer, "+1", 56, (190, 235, 255),
                midleft=(local.centerx + 76, y)
            )

        else:

            draw_text(
                layer, f"+{self.reward}", 64, (255, 225, 120),
                center=(local.centerx + 14, local.centery + 28)
            )

            if self.coin_icon is not None:

                coin = pygame.transform.smoothscale(self.coin_icon, (40, 40))

                layer.blit(coin, coin.get_rect(center=(local.centerx - 62, local.centery + 28)))

        layer.set_alpha(alpha)

        screen.blit(layer, rect)

    def draw_menu(self, screen, game):
        """Pantalla transparente con Salir / Jugar con escape / Jugar
        sin escape."""

        screen.blit(self.dim, (0, 0))

        if self.panel_img is not None:

            screen.blit(self.panel_img, self.panel_rect)

        else:

            pygame.draw.rect(
                screen, (24, 24, 32), self.panel_rect, border_radius=16
            )
            pygame.draw.rect(
                screen, (180, 180, 192), self.panel_rect, 3, border_radius=16
            )

        draw_text(
            screen, self.cfg.title, 36, (255, 240, 200),
            center=(self.panel_rect.centerx, self.panel_rect.top + 26)
        )

        reward = base_reward(self.wave, self.cfg.rewards)

        draw_text(
            screen,
            f"Oleada {self.wave}   Premio: {reward}   "
            f"(sin escape: {reward * NO_ESCAPE_MULT})",
            22, (255, 225, 120),
            center=(self.panel_rect.centerx, self.panel_rect.top + 54)
        )

        mouse = pygame.mouse.get_pos()

        for key in self.BUTTONS:

            rect = self.button_rects[key]

            hover = rect.collidepoint(mouse)

            normal, over = self.btn_imgs[key]

            img = over if (hover and over is not None) else normal

            if img is not None:

                screen.blit(img, rect)

            else:

                color = (92, 92, 116) if hover else (60, 60, 76)

                pygame.draw.rect(screen, color, rect, border_radius=10)
                pygame.draw.rect(
                    screen, (200, 200, 212), rect, 2, border_radius=10
                )

                draw_text(
                    screen, self.BUTTON_LABELS[key], 26, (255, 255, 255),
                    center=rect.center
                )

            # Sin luz no se puede pelear
            if key != "exit" and not game.has_match:

                veil = pygame.Surface(rect.size, pygame.SRCALPHA)
                veil.fill((0, 0, 0, 140))

                screen.blit(veil, rect)

        if not game.has_match:

            draw_text(
                screen, "Necesitas una luz encendida para pelear", 22,
                (255, 150, 130),
                center=(self.panel_rect.centerx, self.panel_rect.bottom - 14)
            )