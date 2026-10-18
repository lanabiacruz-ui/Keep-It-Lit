DEFAULT_LIGHT = "fosforo"

LIGHTS = {
    "fosforo": {
        "nombre": "Fosforo",
        "radio": 100,
        "radio_suelo": 60,
        "consumo": 1.0,
        "cooldown": 0.25,
        "golpe_costo": 0.03,
        "rompe": ("comun", "verde"),
        "furia_cada": 0,
        "furia_duracion": 0,
        "furia_velocidad": 1.0,
        "dano": 1,
    },
    "vela": {
        "nombre": "Vela",
        "radio": 200,
        "radio_suelo": 60,
        "consumo": 0.5,
        "cooldown": 0.40,
        "golpe_costo": 0.006,
        "rompe": ("comun", "verde", "gris"),
        "furia_cada": 20.0,
        "furia_duracion": 15.0,
        "furia_velocidad": 4.0,
        "dano": 1,
    },
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

    return LIGHTS.get(kind, LIGHTS[DEFAULT_LIGHT])
