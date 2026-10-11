import json
from pathlib import Path

import pygame


DATA_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "enemies.json"
)

UI_DIR = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "maps"
    / "ui"
)

COMBAT_DIR = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "maps"
    / "combate"
)


DEFAULT_DATA = {
    "pino": {
        "nombre": "Piña",
        "imagen": "enemigo.png",
        "descripcion": (
            "Enemigo de contacto que se mueve por la sala y rebota "
            "contra los obstaculos. Hace daño cuando choca con el jugador."
        ),
    },

    "tronco": {
        "nombre": "Tronco",
        "imagen": "tronco.png",
        "descripcion": (
            "Mantiene distancia del jugador y dispara tres proyectiles "
            "que rebotan por la sala."
        ),
    },

    "mosquito": {
        "nombre": "Mosquito",
        "imagen": "mosquito.png",
        "descripcion": (
            "Persigue al jugador y puede acercarse para atacar. "
            "Su aviso indica cuando esta por realizar una accion peligrosa."
        ),
    },

    "hongun": {
        "nombre": "Hongun",
        "imagen": "hongun.png",
        "descripcion": (
            "Camina por la sala y persigue al jugador cuando lo detecta. "
            "Puede cargar y liberar una explosion."
        ),
    },

    "guardian": {
        "nombre": "Guardián",
        "imagen": "guardian_icono.png",
        "descripcion": (
            "Es del tamaño del jugador. Actua de manera tranquila, pero si tu luz lo "
            "toca empieza a perseguirte hasta derrotarte. Ataca "
            "igual que el jugador y es bastante resistente"
        ),
    },

    "guardian_tirador": {
        "nombre": "Guardián Tirador",
        "imagen": "guardian_tirador_icono.png",
        "descripcion": (
            "Es del tamaño del jugador. Actua de manera tranquila, pero si tu luz lo "
            "toca se despierta. No se acerca a pegarte por lo que toma distancia, da vueltas "
            "a tu alrededor y te dispara bolas tan rapidas como las tuyas. Apunta "
            "adelantandose a donde vas a estar, asi que no corras en linea recta"
        ),
    },

    "destello": {
        "nombre": "Destello",
        "imagen": "destello.png",
        "descripcion": (
            "Pasea tranquilo y da un poco de luz con el cuerpo. Si te ve se frena "
            "y parpadea en blanco: ese es el aviso. Despues sale corriendo casi el "
            "doble de rapido que vos, te choca y explota: te saca vida, te empuja y "
            "deja la pantalla en blanco unos 5 segundos. Aguanta 2 golpes y si lo "
            "derrotas antes de que te alcance, no explota."
        ),
    },

    "golem": {
        "nombre": "Golem",
        "imagen": "golem_icono.png",
        "descripcion": (
            "Enorme y muy lento. Pasea tranquilo, pero si te ve va directo hacia "
            "vos sin parar. Si te toca una sola vez te agarra, te levanta y te "
            "aprieta: te saca todo el escudo y, si no tenias escudo, toda la vida "
            "de tu luz. Despues te suelta y queda cansado unos segundos. Tiene "
            "mucha vida: no te dejes alcanzar."
        ),
    },
}


class EnemyEncyclopedia:
    """
    Enciclopedia de enemigos (se ve en la tablet).

    IMPORTANTE:
    Las descripciones son SOLO DE LECTURA.
    El jugador no puede modificarlas.

    Imagenes (en assets/maps/ui/). Si alguna falta, se dibuja con
    colores como antes:
        tablet_enemigos.png      1672x941  fondo completo
        fila_enemigo.png         520x112   fila de la lista
        fila_enemigo_sel.png     520x112   fila seleccionada
        btn_regresar.png         340x92    boton REGRESAR
        btn_regresar_hover.png   340x92    boton REGRESAR resaltado
    """

    ORDER = (
        "pino",
        "tronco",
        "mosquito",
        "hongun",
        "guardian",
        "guardian_tirador",
        "destello",
        "golem",
    )

    # ---------- distribucion (en coordenadas de la imagen 1672x941) ----

    IMG_W = 1672
    IMG_H = 941

    # Pantalla de la tablet
    SCREEN_BOX = (436, 170, 800, 500)

    # Lista de enemigos (izquierda)
    ROW_X = 456
    ROW_Y = 260
    ROW_W = 260
    ROW_H = 46      # 8 enemigos: tienen que entrar dentro de la pantalla de la tablet y sin tapar el boton REGRESAR
    ROW_GAP = 4

    # Ficha del enemigo (derecha)
    CARD_BOX = (740, 252, 480, 403)

    # Boton REGRESAR (abajo a la izquierda)
    BACK_BOX = (456, 692, 170, 46)

    TEXT_COLOR = (235, 245, 250)
    TEXT_DARK = (10, 22, 28)
    TITLE_COLOR = (110, 220, 235)
    MUTED_COLOR = (195, 205, 218)
    LINE_COLOR = (96, 102, 120)
    SHADOW_COLOR = (14, 16, 22)

    def __init__(self, screen, discovered=None):

        self.screen = screen

        # Enemigos que el jugador ya se encontro en esta partida. Los
        # demas aparecen como "???" (como una coleccion por completar).
        self.discovered = set(discovered or ())

        self.data = self._load_data()

        self.selected = 0

        self.images = {}

        # Primero las imagenes, porque resize() arma los iconos
        self._load_all_images()

        self.resize()

    # ---------------------------------------------------------
    # Cargar informacion de los enemigos
    # ---------------------------------------------------------

    def _load_data(self):

        data = None

        try:

            with open(
                DATA_PATH,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

        except (
            OSError,
            json.JSONDecodeError,
            UnicodeDecodeError
        ):

            data = None

        if not isinstance(data, dict):

            data = DEFAULT_DATA

        merged = {}

        for key in self.ORDER:

            base = dict(
                DEFAULT_DATA[key]
            )

            if isinstance(
                data.get(key),
                dict
            ):

                base.update(
                    data[key]
                )

            merged[key] = base

        return merged

    # ---------------------------------------------------------
    # Cargar imagenes
    # ---------------------------------------------------------

    def _load_all_images(self):

        # Dibujos de los enemigos
        for key in self.ORDER:

            filename = self.data[key].get(
                "imagen",
                ""
            )

            path = COMBAT_DIR / filename

            try:

                image = pygame.image.load(
                    path
                ).convert_alpha()

            except (
                OSError,
                pygame.error
            ):

                image = None

            self.images[key] = image

    @staticmethod
    def _load_ui(name, size=None, alpha=True):
        """Carga una imagen de assets/maps/ui. None si no existe."""

        path = UI_DIR / name

        try:

            image = pygame.image.load(path)

            image = (
                image.convert_alpha()
                if alpha
                else image.convert()
            )

        except (OSError, pygame.error):

            return None

        if size is not None and image.get_size() != size:

            image = pygame.transform.smoothscale(
                image,
                size
            )

        return image

    # ---------------------------------------------------------
    # Tamanos de pantalla
    # ---------------------------------------------------------

    def _box(self, box):
        """(x, y, ancho, alto) de la imagen 1672x941 -> Rect en pantalla."""

        x, y, w, h = box

        return pygame.Rect(
            round(x * self.sx),
            round(y * self.sy),
            max(1, round(w * self.sx)),
            max(1, round(h * self.sy)),
        )

    def resize(self):

        self.width, self.height = (
            self.screen.get_size()
        )

        self.sx = self.width / self.IMG_W
        self.sy = self.height / self.IMG_H

        self.title_font = pygame.font.Font(
            None,
            max(30, round(62 * self.sy))
        )

        self.name_font = pygame.font.Font(
            None,
            max(24, round(48 * self.sy))
        )

        self.body_font = pygame.font.Font(
            None,
            max(18, round(32 * self.sy))
        )

        self.small_font = pygame.font.Font(
            None,
            max(14, round(24 * self.sy))
        )

        self.back_font = pygame.font.Font(
            None,
            max(20, round(46 * self.sy * 0.62))
        )

        self._font_cache = {}

        self.screen_rect = self._box(self.SCREEN_BOX)
        self.card_rect = self._box(self.CARD_BOX)
        self.back_rect = self._box(self.BACK_BOX)

        # Lista (todo el recuadro, por si se dibuja con colores)
        rows_h = (
            len(self.ORDER) * (self.ROW_H + self.ROW_GAP)
            + self.ROW_GAP
        )

        self.list_rect = self._box(
            (
                self.ROW_X - self.ROW_GAP,
                self.ROW_Y - self.ROW_GAP,
                self.ROW_W + self.ROW_GAP * 2,
                rows_h,
            )
        )

        back_size = self.back_rect.size

        # Imagenes (escaladas al tamano de la pantalla actual)
        self.bg_img = self._load_ui(
            "tablet_enemigos.png",
            (self.width, self.height),
            alpha=False
        )

        self.row_img = self._load_ui(
            "fila_enemigo.png",
            self._enemy_rect(0).size
        )

        self.row_sel_img = self._load_ui(
            "fila_enemigo_sel.png",
            self._enemy_rect(0).size
        )

        self.back_img = self._load_ui(
            "btn_regresar.png",
            back_size
        )

        self.back_hover_img = self._load_ui(
            "btn_regresar_hover.png",
            back_size
        )

        # Fondo oscuro para cuando no hay imagen de la tablet
        self.dim = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA
        )

        self.dim.fill((8, 14, 22, 245))

        # Panel semitransparente de la ficha y pedestal del dibujo
        self.card_panel = pygame.Surface(
            self.card_rect.size,
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            self.card_panel,
            (28, 30, 38, 150),
            self.card_panel.get_rect(),
            border_radius=16,
        )

        pygame.draw.rect(
            self.card_panel,
            (104, 110, 130, 255),
            self.card_panel.get_rect(),
            width=2,
            border_radius=16,
        )

        self.pedestal_rect = pygame.Rect(
            self.card_rect.left + round(24 * self.sx),
            self.card_rect.top + round(58 * self.sy),
            self.card_rect.width - round(48 * self.sx),
            round(120 * self.sy),
        )

        # Iconos chicos para la lista
        self.icons = {}

        icon_size = max(
            8,
            self._enemy_rect(0).height - round(12 * self.sy)
        )

        for key, image in self.images.items():

            if image is None:
                continue

            scale = min(
                icon_size / image.get_width(),
                icon_size / image.get_height()
            )

            self.icons[key] = pygame.transform.scale(
                image,
                (
                    max(1, round(image.get_width() * scale)),
                    max(1, round(image.get_height() * scale)),
                )
            )

        # Siluetas oscuras para los enemigos todavia no descubiertos
        self.icons_locked = {
            key: self._silhouette(icon)
            for key, icon in self.icons.items()
        }

        self.images_locked = {
            key: self._silhouette(image)
            for key, image in self.images.items()
            if image is not None
        }

    @staticmethod
    def _silhouette(image):
        """Misma forma que la imagen pero toda de un color oscuro."""

        mask = pygame.mask.from_surface(image)

        return mask.to_surface(
            setcolor=(14, 18, 24, 255),
            unsetcolor=(0, 0, 0, 0),
        )

    def is_discovered(self, key):

        return key in self.discovered

    # ---------------------------------------------------------
    # Rectangulo de cada enemigo
    # ---------------------------------------------------------

    def _enemy_rect(self, index):

        return self._box(
            (
                self.ROW_X,
                self.ROW_Y + index * (self.ROW_H + self.ROW_GAP),
                self.ROW_W,
                self.ROW_H,
            )
        )

    # ---------------------------------------------------------
    # Dividir texto
    # ---------------------------------------------------------

    @staticmethod
    def _wrap(font, text, max_width):

        lines = []

        current = ""

        for word in text.split():

            test = (
                f"{current} {word}"
            ).strip()

            if (
                current
                and font.size(test)[0]
                > max_width
            ):

                lines.append(
                    current
                )

                current = word

            else:

                current = test

        if current:

            lines.append(
                current
            )

        return lines

    # ---------------------------------------------------------
    # Helpers de texto
    # ---------------------------------------------------------

    def _font(self, size):
        """Fuente por tamano (cache para no recrearla en cada frame)."""

        font = self._font_cache.get(size)

        if font is None:

            font = pygame.font.Font(None, size)

            self._font_cache[size] = font

        return font

    def _blit_text(self, font, text, color, shadow=True, **anchor):
        """Dibuja texto con una sombrita para que se lea mejor."""

        surf = font.render(text, True, color)

        rect = surf.get_rect(**anchor)

        if shadow:

            offset = max(1, round(2 * self.sy))

            back = font.render(text, True, self.SHADOW_COLOR)

            self.screen.blit(
                back,
                rect.move(offset, offset)
            )

        self.screen.blit(surf, rect)

        return rect

    def _fit_description(self, text, width, height):
        """Busca el tamano de letra mas grande donde entra todo el texto."""

        biggest = max(16, round(32 * self.sy))

        for size in range(biggest, 13, -1):

            font = self._font(size)

            lines = self._wrap(font, text, width)

            total = len(lines) * (font.get_linesize() + 2)

            if total <= height:

                return font, lines

        font = self._font(14)

        return font, self._wrap(font, text, width)

    # ---------------------------------------------------------
    # Seleccion
    # ---------------------------------------------------------

    def _select(self, index):

        self.selected = index % len(self.ORDER)

    def _row_at(self, pos):
        """Indice del enemigo bajo el mouse (o None)."""

        for index in range(len(self.ORDER)):

            if self._enemy_rect(index).collidepoint(pos):

                return index

        return None

    # ---------------------------------------------------------
    # Eventos
    # ---------------------------------------------------------

    def handle_event(self, event):

        if event.type == pygame.KEYDOWN:

            # ESC vuelve al menu de pausa
            if event.key == pygame.K_ESCAPE:
                return "back"

            # Subir
            if event.key in (
                pygame.K_UP,
                pygame.K_w,
                pygame.K_LEFT,
                pygame.K_a,
            ):

                self._select(self.selected - 1)

            # Bajar
            elif event.key in (
                pygame.K_DOWN,
                pygame.K_s,
                pygame.K_RIGHT,
                pygame.K_d,
            ):

                self._select(self.selected + 1)

        # El mouse al pasar por encima tambien selecciona
        elif event.type == pygame.MOUSEMOTION:

            index = self._row_at(event.pos)

            if index is not None:

                self.selected = index

        # Rueda del mouse
        elif event.type == pygame.MOUSEWHEEL:

            self._select(self.selected - event.y)

        elif event.type == pygame.MOUSEBUTTONDOWN:

            # Boton regresar
            if (
                event.button == 1
                and self.back_rect.collidepoint(event.pos)
            ):
                return "back"

            # Click en un enemigo
            if event.button == 1:

                index = self._row_at(event.pos)

                if index is not None:

                    self.selected = index

            # Ruedita en versiones viejas de pygame
            elif event.button == 4:

                self._select(self.selected - 1)

            elif event.button == 5:

                self._select(self.selected + 1)

        return None

    # ---------------------------------------------------------
    # Update
    # ---------------------------------------------------------

    def update(self, dt):

        return None

    # ---------------------------------------------------------
    # Dibujar
    # ---------------------------------------------------------

    def _draw_fallback_frames(self):
        """Sin la imagen de la tablet: paneles de colores."""

        self.screen.blit(
            self.dim,
            (0, 0)
        )

        pygame.draw.rect(
            self.screen,
            (35, 70, 92),
            self.screen_rect,
            border_radius=18,
        )

        pygame.draw.rect(
            self.screen,
            (100, 185, 220),
            self.screen_rect,
            width=3,
            border_radius=18,
        )

        pygame.draw.rect(
            self.screen,
            (20, 36, 52),
            self.list_rect,
            border_radius=12,
        )

        pygame.draw.rect(
            self.screen,
            (82, 125, 150),
            self.list_rect,
            width=2,
            border_radius=12,
        )

    def _draw_header(self):

        self._blit_text(
            self.title_font,
            "ENEMIGOS",
            self.TEXT_COLOR,
            midtop=(
                self.screen_rect.centerx,
                round(180 * self.sy),
            ),
        )

        y = round(238 * self.sy)

        left = self._enemy_rect(0).left
        right = self.card_rect.right

        pygame.draw.line(
            self.screen,
            self.LINE_COLOR,
            (left, y),
            (right, y),
            max(2, round(3 * self.sy)),
        )

        # Detalle de color en el centro de la linea
        half = round(60 * self.sx)

        pygame.draw.line(
            self.screen,
            self.TITLE_COLOR,
            (self.screen_rect.centerx - half, y),
            (self.screen_rect.centerx + half, y),
            max(2, round(3 * self.sy)),
        )

    def _draw_list(self):

        for index, key in enumerate(self.ORDER):

            rect = self._enemy_rect(index)

            selected = index == self.selected

            row = self.row_sel_img if selected else self.row_img

            if row is not None:

                self.screen.blit(row, rect)

            else:

                pygame.draw.rect(
                    self.screen,
                    (77, 170, 191) if selected else (49, 91, 112),
                    rect,
                    border_radius=9,
                )

            found = self.is_discovered(key)

            # Icono del enemigo (silueta si todavia no lo descubriste)
            icon = (
                self.icons.get(key) if found
                else self.icons_locked.get(key)
            )

            text_left = rect.left + round(18 * self.sx)

            if icon is not None:

                self.screen.blit(
                    icon,
                    icon.get_rect(
                        midleft=(
                            rect.left + round(16 * self.sx),
                            rect.centery
                        )
                    )
                )

                text_left = rect.left + round(16 * self.sx) \
                    + icon.get_width() \
                    + round(10 * self.sx)

            # Sin imagen de fila, el seleccionado es claro: texto oscuro
            dark = selected and self.row_sel_img is None

            # Si el nombre no entra en la fila (ej. "Guardián Tirador"),
            # se achica la letra hasta que entre, asi no se sale.
            name = self.data[key]["nombre"] if found else "???"

            max_w = rect.right - text_left - round(34 * self.sx)

            name_font = self.name_font

            size = max(24, round(48 * self.sy))

            while (
                name_font.size(name)[0] > max_w
                and size > 12
            ):

                size -= 1

                name_font = self._font(size)

            self._blit_text(
                name_font,
                name,
                self.TEXT_DARK if dark else self.TEXT_COLOR,
                shadow=not dark,
                midleft=(text_left, rect.centery),
            )

            # Flechita de seleccion
            if selected:

                size = max(6, round(9 * self.sy))

                cx = rect.right - round(24 * self.sx)

                cy = rect.centery

                pygame.draw.polygon(
                    self.screen,
                    self.TITLE_COLOR,
                    [
                        (cx - size, cy - size),
                        (cx + size, cy),
                        (cx - size, cy + size),
                    ],
                )

    def _draw_card(self):

        key = self.ORDER[self.selected]

        enemy = self.data[key]

        found = self.is_discovered(key)

        card = self.card_rect

        pad = round(24 * self.sx)

        # Panel de fondo
        self.screen.blit(self.card_panel, card)

        # Nombre
        self._blit_text(
            self.name_font,
            enemy["nombre"] if found else "???",
            self.TEXT_COLOR,
            midtop=(
                card.centerx,
                card.top + round(12 * self.sy)
            ),
        )

        # Pedestal del dibujo
        pedestal = pygame.Surface(
            self.pedestal_rect.size,
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            pedestal,
            (16, 18, 24, 150),
            pedestal.get_rect(),
            border_radius=14,
        )

        pygame.draw.rect(
            pedestal,
            (70, 76, 92, 255),
            pedestal.get_rect(),
            width=2,
            border_radius=14,
        )

        self.screen.blit(pedestal, self.pedestal_rect)

        # Dibujo del enemigo
        image = (
            self.images.get(key) if found
            else self.images_locked.get(key)
        )

        if image is not None:

            area = self.pedestal_rect.inflate(
                -round(20 * self.sx),
                -round(20 * self.sy)
            )

            scale = min(
                area.width / image.get_width(),
                area.height / image.get_height(),
                2.8,
            )

            sprite = pygame.transform.scale(
                image,
                (
                    max(1, round(image.get_width() * scale)),
                    max(1, round(image.get_height() * scale)),
                )
            )

            self.screen.blit(
                sprite,
                sprite.get_rect(
                    center=self.pedestal_rect.center
                )
            )

        # Titulo de descripcion
        desc_y = self.pedestal_rect.bottom + round(16 * self.sy)

        title_rect = self._blit_text(
            self.body_font,
            "Descripción",
            self.TITLE_COLOR,
            topleft=(card.left + pad, desc_y),
        )

        pygame.draw.line(
            self.screen,
            self.LINE_COLOR,
            (card.left + pad, title_rect.bottom + round(4 * self.sy)),
            (card.right - pad, title_rect.bottom + round(4 * self.sy)),
            2,
        )

        # Descripcion SOLO LECTURA (se achica la letra para que entre)
        text_top = title_rect.bottom + round(12 * self.sy)

        available_h = card.bottom - round(16 * self.sy) - text_top

        font, lines = self._fit_description(
            (
                str(enemy.get("descripcion", ""))
                if found
                else "Todavía no te encontraste con este enemigo. "
                     "Enfrentalo en las oleadas para descubrirlo."
            ),
            card.width - pad * 2,
            available_h,
        )

        y = text_top

        for line in lines:

            surf = font.render(line, True, self.TEXT_COLOR)

            self.screen.blit(surf, (card.left + pad, y))

            y += font.get_linesize() + 2

    def _draw_hint(self):
        """Texto de abajo de la lista. Se achica / acomoda solo para que
        NUNCA pise el boton REGRESAR, sin importar el tamano de pantalla."""

        hint_x = self._enemy_rect(0).left
        width = self._enemy_rect(0).width

        top = (
            self._enemy_rect(len(self.ORDER) - 1).bottom
            + round(4 * self.sy)
        )

        # Lo ultimo que puede llegar el texto: justo antes del boton
        limit = self.back_rect.top - round(4 * self.sy)

        total = len(self.ORDER)

        count = sum(1 for k in self.ORDER if self.is_discovered(k))

        parts = (
            f"Descubiertos: {count}/{total}",
            "Flechas / W-S: elegir   ESC: volver",
        )

        size = max(14, round(24 * self.sy))

        while True:

            font = self._font(max(10, size))

            lines = []

            for part in parts:
                lines.extend(self._wrap(font, part, width))

            line_h = font.get_linesize()

            total_h = len(lines) * line_h

            if top + total_h <= limit or size <= 10:
                break

            size -= 1

        # Si ni con la letra mas chica entra, se sube lo que haga falta
        y = min(top, limit - total_h)

        for line in lines:

            hint = font.render(line, True, self.MUTED_COLOR)

            self.screen.blit(hint, (hint_x, y))

            y += line_h

    def _draw_back_button(self):

        hover = self.back_rect.collidepoint(
            pygame.mouse.get_pos()
        )

        button = (
            self.back_hover_img
            if hover and self.back_hover_img is not None
            else self.back_img
        )

        if button is not None:

            self.screen.blit(button, self.back_rect)

        else:

            pygame.draw.rect(
                self.screen,
                (77, 170, 191) if hover else (49, 91, 112),
                self.back_rect,
                border_radius=9,
            )

        # Las imagenes del boton vienen sin texto: se escribe aca
        self._blit_text(
            self.back_font,
            "REGRESAR",
            (255, 255, 255) if hover else self.TEXT_COLOR,
            center=self.back_rect.center,
        )

    def draw(self):

        # ---------- fondo ----------

        if self.bg_img is not None:

            self.screen.blit(self.bg_img, (0, 0))

        else:

            self._draw_fallback_frames()

        self._draw_header()

        self._draw_list()

        self._draw_card()

        self._draw_hint()

        self._draw_back_button()