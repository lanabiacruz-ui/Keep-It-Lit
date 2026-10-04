"""Luces que se pueden equipar (el casillero aislado, al lado de la hotbar).

Las luces NUNCA van al inventario: al agarrarlas del piso se equipan
solas en ese casillero. Cada luz tiene sus propios numeros. Para
balancear, se cambian aca:

  radio           radio de la luz del jugador, en pixeles de pantalla
  radio_suelo     radio de la luz cuando esta tirada en el piso
  consumo         que tan rapido se gasta (1.0 = dura MATCH_DURATION
                  segundos, 0.5 = dura el doble)
  cooldown        espera entre golpe y golpe, en segundos
  rompe           tipos de puerta que esta luz puede romper
  furia_cada      cada cuantos segundos entra en furia (0 = nunca)
  furia_duracion  cuanto dura la furia, en segundos
  furia_velocidad cuantas veces mas rapido pega durante la furia
"""

DEFAULT_LIGHT = "fosforo"

LIGHTS = {
    "fosforo": {
        "nombre": "Fosforo",
        "radio": 100,
        "radio_suelo": 60,
        "consumo": 1.0,
        "cooldown": 0.25,
        "rompe": ("comun", "verde"),
        "furia_cada": 0,
        "furia_duracion": 0,
        "furia_velocidad": 1.0,
    },
    # Ilumina el doble y dura el doble (60 s). Pega lento, pero cada
    # 20 s entra en furia 4 s y pega rapidisimo. Es la unica que rompe
    # las puertas grises.
    "vela": {
        "nombre": "Vela",
        "radio": 200,
        "radio_suelo": 120,
        "consumo": 0.5,
        "cooldown": 0.40,
        "rompe": ("comun", "verde", "gris"),
        "furia_cada": 20.0,
        "furia_duracion": 4.0,
        "furia_velocidad": 4.0,
    },
}


def light_stats(kind):
    """Numeros de una luz (si no existe, los del fosforo)."""

    return LIGHTS.get(kind, LIGHTS[DEFAULT_LIGHT])