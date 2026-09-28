



def get_spawn_points(collision_map):
    return {
        "player_start": collision_map.habitacion_central.center,
        "cabana": collision_map.cabana.center,
        "habitacion_superior": collision_map.habitacion_superior.center,
        "habitacion_izquierda": collision_map.habitacion_izquierda.center,
        "habitacion_derecha": collision_map.habitacion_derecha.center,
        "habitacion_inferior": collision_map.habitacion_inferior.center,
        "habitacion_jefe": collision_map.habitacion_jefe.center,
    }


def get_spawn_point(collision_map, name="player_start"):
    puntos = get_spawn_points(collision_map)

    return puntos.get(
        name,
        puntos["player_start"]
    )
