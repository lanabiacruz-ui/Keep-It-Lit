"""Skins del personaje.

Todo sale de data/skins.json. Cada skin puede ser:
  "gratis": true    -> siempre disponible (Clasico)
  "logro": "<id>"   -> se desbloquea al conseguir ese logro
  "precio": N       -> se compra en la tienda del tendero con monedas
                       de la partida (una vez comprada queda para siempre)

Arte de una skin: carpeta assets/maps/skins/<id>/ con las mismas hojas que
el personaje base (ver assets/maps/skins/LEEME.txt). Lo que falte se toma
del personaje base. Si la carpeta no existe se usa "color" como tinte
provisorio.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SETTINGS_PATH = ROOT / "data" / "settings.json"
SKINS_PATH = ROOT / "data" / "skins.json"
SKINS_DIR = ROOT / "assets" / "maps" / "skins"

DEFAULT_SKIN = "clasico"

SHOP_PREFIX = "skin_"

SHEET_NAMES = (
    "player.png",
    "player_phosphor.png",
    "player_vela.png",
    "player_antorcha.png",
)


def _read_json(path):

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data

    except (OSError, ValueError, UnicodeDecodeError):
        return None


def _read_settings():

    data = _read_json(SETTINGS_PATH)

    return data if isinstance(data, dict) else {}


def _write_settings(data):

    try:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)

        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    except OSError:
        return False

    return True


def _load_catalog():

    data = _read_json(SKINS_PATH)

    raw = data.get("skins", []) if isinstance(data, dict) else []

    skins = []
    seen = set()

    for entry in raw:

        if not isinstance(entry, dict) or "id" not in entry:
            continue

        sid = str(entry["id"])

        if sid in seen:
            continue

        seen.add(sid)

        color = entry.get("color")

        if (
            isinstance(color, (list, tuple))
            and len(color) == 3
            and all(isinstance(c, (int, float)) for c in color)
        ):
            color = tuple(max(0, min(255, int(c))) for c in color)
        else:
            color = None

        try:
            price = int(entry["precio"]) if "precio" in entry else None
        except (TypeError, ValueError):
            price = None

        skins.append({
            "id": sid,
            "nombre": str(entry.get("nombre", sid)),
            "logro": entry.get("logro"),
            "precio": price,
            "gratis": bool(entry.get("gratis", False)),
            "color": color,
        })

    if not any(s["id"] == DEFAULT_SKIN for s in skins):

        skins.insert(0, {
            "id": DEFAULT_SKIN, "nombre": "Clásico", "logro": None,
            "precio": None, "gratis": True, "color": None,
        })

    return skins


SKINS = _load_catalog()

SKIN_IDS = [s["id"] for s in SKINS]


def get(skin_id):

    for skin in SKINS:

        if skin["id"] == skin_id:
            return skin

    return None


def paid_skins():

    return [s for s in SKINS if s["precio"] is not None]


# ---------- desbloqueo ----------

def owned_ids():

    raw = _read_settings().get("skins_owned", [])

    return {str(x) for x in raw} if isinstance(raw, list) else set()


def is_unlocked(skin_id):

    skin = get(skin_id)

    if skin is None:
        return False

    if skin["gratis"] or skin_id == DEFAULT_SKIN:
        return True

    if skin["logro"]:

        from core.achievements import achievements

        if achievements.is_unlocked(skin["logro"]):
            return True

    return skin_id in owned_ids()


def buy(skin_id):

    """Marca como comprada una skin de pago (las monedas las cobra la
    tienda). Devuelve False si no existe o no es de pago."""

    skin = get(skin_id)

    if skin is None or skin["precio"] is None:
        return False

    data = _read_settings()

    owned = data.get("skins_owned", [])

    if not isinstance(owned, list):
        owned = []

    if skin_id not in owned:
        owned.append(skin_id)

    data["skins_owned"] = owned

    return _write_settings(data)


def requirement_text(skin_id):

    skin = get(skin_id)

    if skin is None:
        return ""

    if skin["logro"]:

        from core.achievements import achievements

        title = achievements.title_of(skin["logro"]) or skin["logro"]

        return f"Se consigue con el logro \"{title}\""

    if skin["precio"] is not None:

        return (
            f"Se compra en la tienda del tendero por "
            f"{skin['precio']} monedas"
        )

    return ""


# ---------- skin elegida ----------

def get_skin():

    skin = _read_settings().get("skin", DEFAULT_SKIN)

    if skin in SKIN_IDS and is_unlocked(skin):
        return skin

    return DEFAULT_SKIN


def set_skin(skin_id):

    if skin_id not in SKIN_IDS or not is_unlocked(skin_id):
        return False

    data = _read_settings()
    data["skin"] = skin_id

    return _write_settings(data)


# ---------- arte ----------

def art_dir(skin_id):

    path = SKINS_DIR / skin_id

    return path if path.is_dir() else None


def sheet_path(skin_id, name):

    """Ruta de una hoja de la skin, o None si la skin no la trae."""

    folder = art_dir(skin_id)

    if folder is None:
        return None

    path = folder / name

    return path if path.exists() else None


def tint_color(skin_id):

    """Tinte provisorio: solo si la skin todavia no tiene carpeta de arte."""

    if art_dir(skin_id) is not None:
        return None

    skin = get(skin_id)

    return skin["color"] if skin else None


BODY_COLOR = (190, 200, 235)     # tono del cuerpo claro del personaje base
BODY_RANGE = 48                  # cuanto se admite que se aleje de ese tono


def tint_surface(surface, color):

    """Copia con el cuerpo claro del personaje pintado de `color`. Los
    contornos oscuros y los colores fuertes (fuego) no se tocan. Usa
    mascaras de pygame (rapido, sin numpy)."""

    import pygame

    if color is None:
        return surface

    try:

        mask = pygame.mask.from_threshold(
            surface,
            (*BODY_COLOR, 255),
            (BODY_RANGE, BODY_RANGE, BODY_RANGE, 255),
        )

        tinted = surface.copy()

        tinted.fill(
            (color[0], color[1], color[2], 255),
            special_flags=pygame.BLEND_RGBA_MULT
        )

        out = surface.copy()

        mask.to_surface(out, setsurface=tinted, unsetcolor=None)

        return out

    except (pygame.error, TypeError, ValueError):

        return surface


def tint_frames(frames, skin_id=None):

    if frames is None:
        return None

    color = tint_color(skin_id or get_skin())

    if color is None:
        return frames

    return {
        direction: [tint_surface(f, color) for f in images]
        for direction, images in frames.items()
    }


# ---------- vista previa (menu Skins y tienda) ----------

_loader = None
_previews = {}


def preview_sprite(skin_id):

    """Personaje de frente, recortado, sin escalar. Se guarda en cache."""

    if skin_id in _previews:
        return _previews[skin_id]

    global _loader

    import pygame

    from player.player import Player

    if _loader is None:
        _loader = Player(0, 0, skin=DEFAULT_SKIN)

    sprite = None

    # icon.png (opcional): imagen de la skin para el menu y la tienda
    icon = sheet_path(skin_id, "icon.png")

    if icon is not None:

        try:
            sprite = pygame.image.load(str(icon)).convert_alpha()
        except (pygame.error, OSError):
            sprite = None

    path = sheet_path(skin_id, "player.png") if sprite is None else None

    if path is not None:

        try:

            sheet = pygame.image.load(str(path)).convert_alpha()

            frames = _loader.load_frames_from_sheet(sheet)

            sprite = frames["down"][0]

        except (pygame.error, OSError):
            sprite = None

    if sprite is None:

        sprite = tint_surface(
            _loader.frames["down"][0], tint_color(skin_id)
        )

    bounds = sprite.get_bounding_rect()

    if bounds.width > 0 and bounds.height > 0:
        sprite = sprite.subsurface(bounds).copy()

    _previews[skin_id] = sprite

    return sprite