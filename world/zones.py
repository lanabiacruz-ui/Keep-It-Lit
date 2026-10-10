from collections import namedtuple

import pygame

Zone = namedtuple("Zone", "id name rect")

ZONES = [
    Zone("inicio", "Sala de inicio", pygame.Rect(820, 900, 240, 144)),
    Zone("central", "Sala central", pygame.Rect(836, 400, 216, 220)),
    Zone("tienda", "Tienda", pygame.Rect(856, 36, 184, 142)),
    Zone("cofres", "Sala de cofres", pygame.Rect(316, 44, 272, 176)),
    Zone("combate", "Sala de combate", pygame.Rect(1244, 388, 436, 284)),

   


class ZoneTracker:
    """Avisa cuando el jugador ENTRA a una zona (no mientras esta
    adentro). Al salir, y volver a entrar, avisa de nuevo."""

   
    EXIT_MARGIN = 10

    def __init__(self, zones=None):

        self.zones = list(zones if zones is not None else ZONES)
        self.current = None

    def zone_at(self, point):

        for zone in self.zones:

            if zone.rect.collidepoint(point):
                return zone

        return None

    def update(self, point):
        """Devuelve la Zone si el jugador acaba de entrar a una (si no,
        None). `point` es la posicion del jugador en el mundo."""

        if self.current is not None:

            margin = self.EXIT_MARGIN

            area = self.current.rect.inflate(margin * 2, margin * 2)

            if not area.collidepoint(point):
                self.current = None

        zone = self.zone_at(point)

        if zone is not None and zone is not self.current:

            self.current = zone

            return zone

        return None
