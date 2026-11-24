"""Zona del mapa 2 donde SI aparecen slimes (lo verde que dibujaste).

Va dentro del codigo (comprimida). Cada bit = un pixel del mapa (2000 x 1600):
1 = se puede spawnear, 0 = no.
"""

import base64
import zlib

MASK_W = 2000
MASK_H = 1600

_DATA = (
    "eNrt3Uty8kYYhtFWKVUaaglaipYmlsZSWAJDBhSdyyCp5Lcdg21Q93ueqT3gWBda+BMqRZIkSZIkSZIkSVJP/ZYKP9Q/mhLlxz/l"
    "NVF++ku+xMrrGCv/8FA/1v809CSvd8D7oP8tXz48+3dI/1v+3qH+JrwH+j/y7e1fqLVT+j/yOr/189t78rkj+Vub8V14XXuS/4q5"
    "1vcbOpL/cpY7fABvfrF/+ujoPX8kX/uS/9vz0c7e/GXO6SPQh/DWd/dTfbxc+RQrX2PlNVc+xsqXWPkWK2967f41+RwrX2PlNVc+"
    "xcrXWHnNlQ+x8jFWPsXK51j5EitfY+VbrLzmyodY+Rgrn2PlS6x8jZXXXPkQKx9j5XOsfImVr7HymisfYuVjrHyOlS+x8i1WXnPl"
    "Y6x8ipUvsfI1Vl5z5UOsfIqVz7HyNVa+xcqbPMV9j3yMlU+x8jlWvsTKt1h5iyf3b5JPsfIlVr7FymuufIiVj7HyiZw8Rj6Tx8kX"
    "8jj5Sh4n38jJY+SVPE8+kMfJR3LyGPlEHiefyePkCzl5jHwlj5Nv5OQx8kpOniMfyMlj5CM5eYx8IiePkc/k5DHyhZw8Rr6Sk8fI"
    "N3LyGHklJ8+RD+TkMfKRnJycnJycnJycnJycnJycnJycnJycnJycnJycnJycnJycnJycnJycnJycnJycnJycnJz8B+UTOTk5OTk5"
    "OXmz8pmcnJycnJycvFn5Qk5OTk5OTk7erHwlJycnJycnJ29WvpGTk5OTk5M3L6/k5OTk5OTk7csHcnJycnJy8ublIzk5OTk5eTfy"
    "iZycnJycvBv5TE5OTk5O3o18IScnJycn70a+kpOTk5OTdyPfyMnJycnJu5FXcnJycnLyfuQDOTk5OTl5N/KRnJycnJycnJycnJyc"
    "nJycnJycnJycnJycnJycnJycnJycnJycnJycnJycnJycnJycnJycnPwbc6ceOTk5OXk/8kJOTk5OTt6L3DdgkpOTk5P3I/e0AnJy"
    "cnJycvJ25Z4mSE5O3q/cU8DJyfuXT+Tk5OS76pw68EtOHiS/kKcNf5IHyq/kaeNw5IHyGzl5ymgUOTk5eb8jE+Tk5P0PDpCTk5P3"
    "OzJBTk5O3u/IBDk5ef+DA+Tk5OTk5OTk7Y5GkZOTk/c7GkVOTk7e72gUOTk5eb9DYeTk5OT9DoWRk5OT9zsURk5OTt7vOBw5OTl5"
    "v2My5OTk5P2OyZCTk5P3OyZDTk5O3u+YDDk5OXm/YzLfJ19i5XOsfCKPk4/k5OTk5N3JB3JycnJycvLm5YWcnJycnJy8dflGTk5O"
    "Tk5O3rx8JScnJycnJycnb06+xMrnWPkUKx9j5UOsvKTKN/I4+UpOTk5OTk5OTt6cfCEnJycnJycnJycnJycn3418JicnJycnJycn"
    "JycnJyffjXwib6dKTk5O3qv8QE5OTt6t/EhOTt79bam58hM5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OXmr"
    "8uOQKr/MqfLrkiqva4r8/N/XmyL/9Z6VFPk1Vf4GMkL+JjFCfk2Vv31HXoL8nCp/53s0+pe/d29W//JLrLwmya+feb09yj93X3mP"
    "8mOs/EROTk5OTk5OTk5OTk7uKpWcnNzncOTk5M/7two5OXk/8hs5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5"
    "OTk5OTk5OTk5OTk5OTl5+/KBnJyc/HldyePkl+fKC/nrO5PHyU/k5D8q38jJycnJyV8t3z631PvMn3A/Hck/Xnpd+pN/7ksBh2uq"
    "fKr9yUt9ZrnyZU/yGzk5OTk5+VeaycnJycm7k0/k5OSv6Borv8TKz+TPaNyT/EROTk5OTk5OTk5OTk5OTk5OTv60juTkMfIDOXmM"
    "vJCT58hv5OTk5OTk5OTkzcmv5HHyC3mc/EweJz+Rk5OTk5OTk5M3Jz+Sx8kP5HHyQp4nv5GTk5OTk5OTk5OTk5OTk5OTk5OTk5OT"
    "k5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5N3"
    "Lq/kafLcZ/DkPnHKk+XIycnJycnJycnJycnJM+UTOTk5OTk5OTl5c/KZnJycnJycnJycvBn5Qk5OTk5OTk5O3px8JScnJycnJycn"
    "J29GvpGTk5OTk5OTk39Lz/yeibor+SFWXsjz5DdycnJycnLyBxrIycnJycnJycmbk4/k5OTk5OTk5OTk5OS7lU/k5OTk5OTkzctn"
    "cnJycnLybuQLOTk5OTk5efPylZycnJycvBv5Rk5OTk5OTt68fF83I1fyNPkhVn6MlZ/IyX+0gXwHncnj5JdY+TVWXkPlz13B7Ul+"
    "ebJ8DD3K9ySvofJnH+X7kV9i5ddYeW1B/vwdcy/ymio/xsrPqfJbDZX3sq/fL7/Eymuq/BArP8bKT+Tk5OTk5OTk5OTk5OTk5OTk"
    "5OTkPyY/k5PHyC/k5DHyKzl5jPxGTk7evbySk5OTk/cmP5CTk5OTdyc/kpOTN9hETp7y73NycnJycnJycvIGm8nJycnJycnJycnJ"
    "yXfbQk5OTk5OTk5OTk5OvttWcnJycnJycnJycnJycnJycnJycnJycnJycnJycnJycnJycnJycnJycnJycnJycvIXtpHHySt5nnwg"
    "j5OP5OQx8omcnJycvDv5TE5OTk7enXwhJycnJ+9OvpKTk5OTdyffyMnJycm7k1dycnJy8v7kAzk5OTl5d/KRnJycnJycnJycnJyc"
    "nJycnJycnJycnJycnJycnJycnJycnJycnJycnJycnJycnJycnJycnJycnJycnJycnJycnJycnJycnJycnJycnJycnJycnJz8W/NN"
    "t+Tk5OTk5OTk7VXIycnJycnJyVvN81LJycnJycnJydtrJScnJycnJydvtoWcnJycnJycnLy5ZnJycnJycvIs+bEn+XSP/BArL7ny"
    "W6z8Giu/xMrP5HHyEzl5w40ldfl6n/wQKy+58lusvKM39KGknuLulHd0iisl9RR3r/wWK+/mCn27V36JlZ/JW2+9V34ib73lXvmR"
    "PE7ezfJ1Jo9buOfKp5J6yZIrH8nJY+QDOXmMvJCnyTdy8hj5Sk4eI1/I4+QzOXmMfCInj5GP5HEjQvd/GNXLiNAD8v0NyiyP7JEP"
    "yHc3OrA+dDCWB9r55eb15+SXXcM/Sy+tb/TtwXefrTS+0bdH33gfkx93Dv8MfX1Ivp9l3OPLrQfl573D//9c9KB8J+e44Qtr7KU0"
    "vNGHr7zCubS70YcvDSwOj8pfPPE8ldf10v19K6/slcuZ+aXyV35CUV7cKXSTv3CrDy+Xv2jUfSmv7xy6yV+0oll3AX/Fe9u4D/kx"
    "dZO/4FJ9KjvqGup+Kn0oofS1lFD6XEqofSyh9K3ss59f1SwllT7tVf7jVzClhNLXHct/9nOaec/yH72EGYr0Df0OkNr2kg=="
)

_bits = None


def _load():

    global _bits

    if _bits is None:

        _bits = zlib.decompress(base64.b64decode(_DATA))

    return _bits


def is_allowed(x, y):

    x = int(x)
    y = int(y)

    if x < 0 or y < 0 or x >= MASK_W or y >= MASK_H:
        return False

    i = y * MASK_W + x

    return bool((_load()[i >> 3] >> (i & 7)) & 1)