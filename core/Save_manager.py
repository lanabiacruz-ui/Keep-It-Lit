import hashlib
import hmac
import json
import os
from datetime import datetime
from pathlib import Path


SAVES_DIR = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "saves"
)

SLOTS = ["save_01.json", "save_02.json", "save_03.json"]


# Modos de juego (se elige al crear la partida)
MODE_NORMAL = "normal"
MODE_HARDCORE = "hardcore"
MODES = (MODE_NORMAL, MODE_HARDCORE)


def normalize_mode(mode):
    """Cualquier cosa rara (o una partida vieja sin modo) es normal."""

    return mode if mode in MODES else MODE_NORMAL


EMPTY = "empty"
OK = "ok"
CORRUPT = "corrupt"


def _read_slot(path):

 

    path = Path(path)

    if not path.exists() or path.stat().st_size == 0:
        return EMPTY, {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return CORRUPT, {}

    if not isinstance(data, dict):
        return CORRUPT, {}

    if not data:
        return EMPTY, {}

    return OK, data


def _slot_is_empty(path):

    status, _ = _read_slot(path)

    return status == EMPTY


# ---------- contraseñas de las partidas ----------
# Nunca se guarda la contraseña: solo un hash con sal.

PASSWORD_MIN = 1
PASSWORD_MAX = 16
_PBKDF2_ROUNDS = 60_000


def _hash_password(password, salt_hex):

    return hashlib.pbkdf2_hmac(
        "sha256",
        str(password).encode("utf-8"),
        bytes.fromhex(salt_hex),
        _PBKDF2_ROUNDS,
    ).hex()


def make_password_fields(password):
    """Campos para guardar en la partida ({} si no hay contraseña)."""

    if not password:
        return {}

    salt = os.urandom(16).hex()

    return {
        "password_salt": salt,
        "password_hash": _hash_password(password, salt),
    }


def has_password(data):

    return bool(data.get("password_hash")) and bool(data.get("password_salt"))


def check_password(data, password):
    """True si la contraseña es correcta. Una partida vieja, sin
    contraseña, deja pasar siempre."""

    if not has_password(data):
        return True

    try:
        wanted = _hash_password(password, data["password_salt"])
    except (ValueError, TypeError):
        return False

    return hmac.compare_digest(wanted, str(data["password_hash"]))


def list_slots():

   

    slots = []

    for number, slot in enumerate(SLOTS, start=1):

        path = SAVES_DIR / slot

        status, data = _read_slot(path)

        slots.append({
            "slot": number,
            "path": path,
            "status": status,
            "empty": status == EMPTY,
            "player_name": str(data.get("player_name", "")),
            "mode": normalize_mode(data.get("mode")),
            "has_password": has_password(data),
            "created_at": data.get("created_at", ""),
            "last_played": data.get("last_played", ""),
            "data": data,
        })

    return slots


def name_exists(player_name):
    """True si ya hay una partida guardada con ese nombre.

    Ignora mayusculas y espacios de los costados ("Juan" y " juan "
    son el mismo nombre). Los slots vacios (partidas borradas) no
    cuentan, asi que un nombre se puede volver a usar despues de
    borrar su partida.
    """

    wanted = str(player_name).strip().casefold()

    if not wanted:
        return False

    for slot in list_slots():

        if slot["empty"]:
            continue

        if slot["player_name"].strip().casefold() == wanted:
            return True

    return False


def get_free_slot():



    for slot in SLOTS:

        candidate = SAVES_DIR / slot

        if _slot_is_empty(candidate):
            return candidate

    return None


def create_new_save(player_name, mode=MODE_NORMAL, password=""):

 

    SAVES_DIR.mkdir(parents=True, exist_ok=True)

    path = get_free_slot()

    if path is None:
        return None

    now = datetime.now().isoformat(timespec="seconds")

    data = {
        "player_name": player_name,
        "mode": normalize_mode(mode),
        "created_at": now,
        "last_played": now,
    }

    data.update(make_password_fields(password))

    with open(path, "w", encoding="utf-8") as f:

        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )

    return path


def load_save(path):



    status, data = _read_slot(path)

    if status != OK:
        return None

    return data


def save_progress(path, **fields):



    if path is None:
        return False

    status, data = _read_slot(path)

    if status == CORRUPT:
        return False

    data = dict(data)

    data.update(fields)

    data["last_played"] = datetime.now().isoformat(timespec="seconds")

    try:

        with open(path, "w", encoding="utf-8") as f:

            json.dump(
                data,
                f,
                indent=4,
                ensure_ascii=False
            )

    except OSError:
        return False

    return True


def delete_save(path):


    try:

        with open(path, "w", encoding="utf-8"):
            pass

    except OSError:
        return False

    return True