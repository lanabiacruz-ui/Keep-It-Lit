NAME_MAX = 14
DEFAULT_NAME = "amigo"
FORBIDDEN = "[]{}@\\"

_name = ""


def clean_name(text):

    out = "".join(
        c for c in str(text or "")
        if c.isprintable() and c not in FORBIDDEN
    )

    return " ".join(out.split())[:NAME_MAX].strip()


def get_name():

    return _name


def set_name(text):

    global _name

    _name = clean_name(text)


def display_name():

    return _name or DEFAULT_NAME


def with_name(text):

    if "{nombre}" not in text:
        return text

    return text.replace("{nombre}", display_name())