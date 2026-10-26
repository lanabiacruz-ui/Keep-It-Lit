from collections import namedtuple

import pygame

Zone = namedtuple("Zone", "id name rect")

ZONES = [
    Zone("inicio", "Cabaña", pygame.Rect(820, 900, 240, 144)),
    Zone("central", "Centro", pygame.Rect(836, 400, 216, 220)),
    Zone("tienda", "Tienda", pygame.Rect(856, 36, 184, 142)),
    Zone("cofres", "Sala De Cofres", pygame.Rect(316, 44, 272, 176)),
    Zone("combate", "Orkun - Zona 1", pygame.Rect(1244, 388, 436, 284)),
    Zone("combate_izq", "Stonun - Zona 2", pygame.Rect(148, 336, 500, 408)),
]


class ZoneTracker:


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