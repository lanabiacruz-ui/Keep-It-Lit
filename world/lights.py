"""Luces que se pueden equipar (el casillero aislado, al lado de la hotbar).

Las luces NUNCA van al inventario: al agarrarlas del piso se equipan
solas en ese casillero. Cada luz tiene sus propios numeros. Para
balancear, se cambian aca:

  radio           radio de la luz del jugador, en pixeles de pantalla
  radio_suelo     radio de la luz cuando esta tirada en el piso
  consumo         que tan rapido se gasta (1.0 = dura MATCH_DURATION
                  segundos, 0.5 = dura el doble)
  cooldown        espera entre golpe y golpe, en segundos
  golpe_costo     cuanta vida se gasta cada vez que se pega, aunque sea
                  al aire (1.0 = toda la luz). En furia no gasta.
  rompe           tipos de puerta que esta luz puede romper
  furia_cada      segundos de espera hasta la proxima furia (0 = nunca)
  furia_duracion  cuanto dura la furia, en segundos
  furia_velocidad cuantas veces mas rapido pega durante la furia
  dano            cuanto saca cada golpe (si falta, 1)
"""

DEFAULT_LIGHT = "fosforo"

LIGHTS = {
    "fosforo": {
        "nombre": "Fosforo",
        "radio": 100,
        "radio_suelo": 60,
        "consumo": 1.0,
        "cooldown": 0.25,
        "golpe_costo": 0.03,      # ~1 s de fosforo por golpe
        "rompe": ("comun", "verde"),
        "furia_cada": 0,
        "furia_duracion": 0,
        "furia_velocidad": 1.0,
        "dano": 1,
    },
    # Ilumina el doble y dura el doble (60 s). Pega lento, pero cada
    # 20 s entra en furia 15 s y pega rapidisimo. Es la unica que rompe
    # las puertas grises.
    "vela": {
        "nombre": "Vela",
        "radio": 200,
        "radio_suelo": 60,
        "consumo": 0.5,
        "cooldown": 0.40,
        "golpe_costo": 0.006,     # casi nada: la vela dura mucho mas
        "rompe": ("comun", "verde", "gris"),
        "furia_cada": 20.0,       # espera 20 s entre furias
        "furia_duracion": 15.0,   # y cada furia dura 15 s
        "furia_velocidad": 4.0,   # pega 4 veces mas rapido
        "dano": 1,
    },
    # El doble que la vela en todo: ilumina el doble (400), dura el
    # doble (120 s), pega el doble de rapido y el doble de fuerte, y la
    # furia llega el doble de seguido (cada 10 s), dura el doble (30 s)
    # y pega el doble de rapido (x8).
    "antorcha": {
        "nombre": "Antorcha",
        "radio": 250,
        "radio_suelo": 60,
        "consumo": 0.38,
        "cooldown": 0.35,
        "golpe_costo": 0.003,
        "rompe": ("comun", "verde", "gris", "azul"),
        "furia_cada": 10.0,
        "furia_duracion": 30.0,
        "furia_velocidad": 8.0,
        "dano": 2,
    },
}


def light_stats(kind):
    """Numeros de una luz (si no existe, los del fosforo)."""

    return LIGHTS.get(kind, LIGHTS[DEFAULT_LIGHT])