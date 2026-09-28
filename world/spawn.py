def get_spawn_points(collision_map):
    return collision_map.spawn_points


def get_spawn_point(collision_map, name="player_start"):
    puntos = get_spawn_points(collision_map)

    return puntos.get(
        name,
        puntos["player_start"]
    )
