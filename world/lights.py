"""Luces que se pueden equipar (el casillero donde iba el fosforo).

Cada luz tiene sus propios numeros. Para balancear, se cambian aca:

  radio       radio de la luz del jugador, en pixeles de pantalla
  radio_suelo radio de la luz cuando esta tirada en el piso
  consumo     que tan rapido se gasta (1.0 = dura MATCH_DURATION segundos,
              0.5 = dura el doble)
  cooldown    espera entre golpe y golpe, en segundos
"""

DEFAULT_LIGHT = "fosforo"

LIGHTS = {
    "fosforo": {
        "nombre": "Fosforo",
        "radio": 100,
        "radio_suelo": 60,
        "consumo": 1.0,
        "cooldown": 0.25,
    },
    # Mas luz y dura el doble (60 s), pero pega mas lento
    "vela": {
        "nombre": "Vela",
        "radio": 140,
        "radio_suelo": 84,
        "consumo": 0.5,
        "cooldown": 0.40,
    },
}


def light_stats(kind):
    """Numeros de una luz (si no existe, los del fosforo)."""

    return LIGHTS.get(kind, LIGHTS[DEFAULT_LIGHT])