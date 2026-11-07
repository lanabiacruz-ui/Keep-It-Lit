"""Textos del tutorial: objetivos, charlas de Cenizo, consejos y festejos.

Cada entrada corresponde (en orden) a un objetivo de
NewGame._build_objectives. Campos:

  text   cartel del objetivo (texto plano, sin [[ ]])
  tuto   paginas que dice Cenizo al empezar el paso (con [[TECLA]])
  hint   consejo que da Cenizo si el jugador se traba
  cheer  festejo al completar el paso (si falta, elige uno al azar)

Se pueden usar {countdown}, {antorcha_wave} y {creatures}.
Si se agregan o sacan objetivos en new_game.py hay que actualizar esta
lista: si el largo no coincide, no se aplica nada.
"""

TEXTS = [

    # 0 - fosforo
    {
        "text": (
            "Está oscuro: buscá el fósforo en el piso (seguí la flecha) y "
            "agarralo con E. Si en {countdown} segundos no tenés luz, perdés."
        ),
        "tuto": [
            "¡Ey, despertaste! Soy [[Cenizo]], el fantasma de las cenizas. Voy a ayudarte a sobrevivir en este lugar tan oscuro.",
            "Tu luz es tu vida: la barra naranja de abajo. Se gasta con el tiempo y con cada golpe. Si se apaga, perdés.",
            "Ahora no tenés nada. Seguí la flecha naranja con [[W]] [[A]] [[S]] [[D]] hasta el fósforo y agarralo con [[E]]. ¡Tenés {countdown} segundos!",
        ],
        "hint": "Seguí la flecha naranja hasta el fósforo y apretá [[E]] al llegar. ¡Rápido, que el tiempo corre!",
        "cheer": "¡Fuego! Ya tenés tu primera lucecita.",
    },

    # 1 - moverse
    {
        "text": "Practicá moverte con las cuatro teclas: W, A, S y D.",
        "tuto": [
            "¡Ya tenés luz! Primero lo básico: apretá [[W]] [[A]] [[S]] [[D]], una por una. La lista de arriba se tilda sola.",
        ],
        "hint": "Probá cada tecla de la lista: las que faltan están sin tildar.",
        "cheer": "¡Ya caminás como un campeón!",
    },

    # 2 - atacar
    {
        "text": (
            "Probá atacar con click izquierdo. "
            "Cada golpe gasta un poco de luz."
        ),
        "tuto": [
            "Atacar: [[CLICK IZQ.]]. Golpeás con tu propia luz, pero cada golpe la gasta un poquito: no le pegues al aire. ¡Probalo!",
        ],
        "hint": "Hacé click izquierdo en cualquier lado. Es solo una prueba.",
        "cheer": "¡Pum! Pegás fuerte.",
    },

    # 3 - agarrar
    {
        "text": (
            "Agarrá un objeto del piso con E (madera, resina, aceite): "
            "sirven para que tu luz no se apague."
        ),
        "tuto": [
            "Agarrar: acercate a un objeto del piso (madera, resina, aceite) y apretá [[E]]. Sirven para recargar tu luz. ¡Seguí la flecha!",
        ],
        "hint": "Caminá hasta el objeto que marca la flecha y apretá [[E]] cuando estés cerca.",
        "cheer": "¡Botín conseguido!",
    },

    # 4 - casilleros
    {
        "text": (
            "Probá elegir casilleros: teclas 1 a 4, 5 y 6 (pociones), "
            "la tecla 7 (tu luz) y la rueda del mouse."
        ),
        "tuto": [
            "Inventario: tenés 4 casilleros ([[1]] al [[4]]), 2 marcos de pociones ([[5]] y [[6]]) y la tecla [[7]] elige tu luz equipada.",
            "También podés recorrerlos con la [[RUEDITA]] del mouse. Probá todo: la lista se tilda sola.",
        ],
        "hint": "Apretá las teclas del 1 al 7 y girá la ruedita del mouse. Faltan las que están sin tildar.",
        "cheer": "¡Ya manejás el inventario como un pro!",
    },

    # 5 - usar y soltar
    {
        "text": (
            "Usá un objeto (F o click derecho) y soltá otro con Q. "
            "Si te quedás sin objetos, agarrá más del piso."
        ),
        "tuto": [
            "Usar: elegí un casillero con algo y apretá [[F]] o [[CLICK DER.]]. Soltar: [[Q]] tira el objeto elegido (junto a una bolsa o un cofre, va adentro).",
            "Lo que queda en el piso se esfuma a los 5 minutos, ¡pero lo podés volver a agarrar con [[E]]!",
            "Madera: +25% de luz. Resina: +90% de a poco. Aceite: te deja en 75% y te da velocidad. Usalos ANTES de quedarte a oscuras.",
        ],
        "hint": "Elegí un casillero con un objeto y apretá [[F]]. Después, con otro, apretá [[Q]] para soltarlo.",
        "cheer": "¡Sabés cuidar tus recursos!",
    },

    # 6 - ayuda
    {
        "text": (
            "Probá los botones de ayuda: ESC (pausa) y TAB "
            "(ocultar el objetivo)."
        ),
        "tuto": [
            "Ayuda: [[ESC]] abre la pausa (ahí está la enciclopedia de criaturas) y [[TAB]] esconde o muestra el objetivo. Probá las dos.",
        ],
        "hint": "Apretá [[ESC]] y volvé a apretarlo para seguir. Después probá [[TAB]].",
        "cheer": "¡Entrenamiento básico completo! Ahora, a salir de acá.",
    },

    # 7 - puerta de la cabana
    {
        "text": (
            "Salí de la cabaña: golpeá la puerta con click izquierdo "
            "hasta romperla. Cada golpe gasta luz."
        ),
        "tuto": [
            "Puertas: golpeala con tu luz ([[CLICK IZQ.]]) hasta romperla. Cada golpe gasta luz, y cada tipo de puerta pide una luz distinta. ¡Seguí la flecha!",
        ],
        "hint": "Acercate a la puerta que marca la flecha y dale click izquierdo varias veces.",
        "cheer": "¡CRASH! Puerta fuera de servicio.",
    },

    # 8 - sala central
    {
        "text": "Seguí el camino al norte hasta la sala central.",
        "tuto": [
            "Seguí el camino hacia el norte. La flecha te lleva a la sala central, que conecta todo el mapa. ¡Va a ser tu base!",
        ],
        "hint": "Andá siempre hacia el norte (arriba). La flecha te va marcando el camino.",
        "cheer": "¡Llegamos al centro del mapa!",
    },

    # 9 - monedas
    {
        "text": (
            "Juntá 10 monedas: hay tiradas por el mapa, en los cofres y "
            "las sueltan los slimes (matalos a golpes)."
        ),
        "tuto": [
            "Monedas: sirven para comprar luces y objetos. Se juntan solas al acercarte. Dorada = 1, azul = 5, roja = 10. ¡Juntá 10!",
            "Slimes: son tranquilos y no atacan. Pegales con tu luz hasta matarlos: sueltan 10 monedas y una gelea que cura al comerla.",
        ],
        "hint": "Seguí la flecha hasta las monedas del piso, o buscá un slime y golpealo.",
        "cheer": "¡Tenés plata! Ahora, a la tienda.",
    },

    # 10 - ir a la tienda
    {
        "text": (
            "Andá a la tienda (al norte de la sala central) y apretá F "
            "cerca del vendedor para hablarle."
        ),
        "tuto": [
            "Tienda: está al norte de la sala central. Acercate al vendedor hasta que aparezca la tecla [[F]] y apretala. Se cierra con [[E]] o [[ESC]].",
            "Ahí gastás tus monedas en luces, objetos y construcciones. Algunos productos se desbloquean al llegar a cierta oleada en las salas de combate.",
        ],
        "hint": "La tienda queda al norte de la sala central. Cuando estés cerca del vendedor, apretá [[F]].",
        "cheer": "¡Bienvenido a la tienda!",
    },

    # 11 - info del producto
    {
        "text": (
            "Con la tienda abierta, hacé click con la RUEDA del mouse "
            "sobre un producto para ver qué hace."
        ),
        "tuto": [
            "Info: apuntá a un producto y hacé click con la rueda del mouse (el botón del medio). Te explica qué hace y, en las luces, cuánto duran. Otro click la cierra.",
        ],
        "hint": "Con la tienda abierta, apuntá a un producto y apretá la ruedita del mouse como si fuera un botón.",
        "cheer": "¡Informadísimo!",
    },

    # 12 - comprar
    {
        "text": (
            "Comprale algo al vendedor: elegí un objeto, la cantidad "
            "y apretá Comprar."
        ),
        "tuto": [
            "Comprar: click en un producto lo suma al carrito, click derecho saca uno y el botón x15 suma 15 de golpe. Abajo ves el total; la papelera vacía el carrito.",
            "Cuando estés listo, apretá Comprar. Si no te alcanzan las monedas no cobra nada: sacá algo o juntá más. Te conviene un objeto (madera, cera...).",
        ],
        "hint": "Hacé click en un producto para ponerlo en el carrito y después apretá el botón Comprar.",
        "cheer": "¡Primera compra! Se siente bien, ¿no?",
    },

    # 13 - agarrar lo comprado
    {
        "text": (
            "El vendedor escupe lo que comprás: agarralo del piso "
            "con E."
        ),
        "tuto": [
            "Lo comprado: el vendedor lo escupe al piso, cerca de él. Acercate y apretá [[E]] para agarrarlo.",
            "Tip: con el imán ([[O]]) los objetos sueltos vuelan solos hacia vos.",
        ],
        "hint": "Mirá el piso cerca del vendedor y apretá [[E]] sobre lo que escupió.",
        "cheer": "¡Ñam! Ya es tuyo.",
    },

    # 14 - inventario de la tienda
    {
        "text": (
            "Volvé a abrir la tienda (F) y apretá TAB para ir a la "
            "pestaña Inventario."
        ),
        "tuto": [
            "Inventario de la tienda: con [[TAB]] cambiás entre Tienda e Inventario. Ahí armás tus casilleros y tu luz como quieras y comprás todo junto con 'Comprar inventario'. ¡Probalo!",
        ],
        "hint": "Abrí la tienda con [[F]] y apretá [[TAB]] para cambiar de pestaña.",
        "cheer": "¡Ya sos todo un comerciante!",
    },

    # 15 - cofres
    {
        "text": (
            "Andá a la sala de cofres (arriba a la izquierda). Acercate a "
            "un cofre y apretá F, después ESPACIO en la zona marcada para "
            "abrirlo."
        ),
        "tuto": [
            "Cofres: están en la sala de arriba a la izquierda. Acercate y apretá [[F]] (cuenta como un golpe) y después [[ESPACIO]] cuando el marcador esté en la zona marcada.",
            "Cada cofre se abre 10 veces seguidas y después descansa 3 minutos. Dan monedas, madera, cera, aceite... y con suerte una GANZÚA, que abre un cofre sin minijuego (3 usos).",
        ],
        "hint": "Seguí la flecha a la sala de cofres. Cerca de uno, apretá [[F]] y después [[ESPACIO]] en el momento justo.",
        "cheer": "¡Cofre abierto! ¿Qué habrá adentro?",
    },

    # 16 - vela
    {
        "text": (
            "Conseguí una vela, una luz mejor que el fósforo: solo se "
            "consigue en la tienda y cuesta 55 monedas. Soltá el fósforo "
            "antes (casillero de luz y Q)."
        ),
        "tuto": [
            "Luces: la vela ilumina más y dura más que el fósforo. Solo se consigue en la tienda (los cofres no la dan) y cuesta 55 monedas.",
            "Solo podés llevar una luz. Con el fósforo en la mano, la vela no se cambia: primero soltalo (elegí el casillero de la luz y apretá [[Q]]).",
            "Después agarrá la vela con [[E]] y se equipa sola. ¡Juntá las 55 monedas!",
        ],
        "hint": "Necesitás 55 monedas. Comprá la vela en la tienda, soltá el fósforo con [[Q]] y agarrá la vela con [[E]].",
        "cheer": "¡Una vela! Ahora sí hay luz de verdad.",
    },

    # 17 - puerta gris
    {
        "text": (
            "Golpeá con tu vela una puerta gris de la sala "
            "central para romperla."
        ),
        "tuto": [
            "Puertas: las grises de la sala central llevan a las zonas de combate. Se rompen solo con vela o antorcha. ¡Seguí la flecha!",
        ],
        "hint": "Con la vela equipada, dale click izquierdo a la puerta gris que marca la flecha.",
        "cheer": "¡Puerta rota! Se viene la acción.",
    },

    # 18 - entrar al combate
    {
        "text": (
            "Entrá a una zona de combate y elegí cómo jugar: con escape "
            "o sin escape (premio doble)."
        ),
        "tuto": [
            "Zonas de combate: tienen oleadas de enemigos. Antes de entrar te avisa el nombre de la zona y, al entrar, elegís cómo jugar.",
            "Con escape: la salida queda abierta, así que si te complicás podés irte caminando y volver después. Ideal para aprender.",
            "Sin escape (premio x2): la salida se cierra hasta terminar la oleada. No hay huida, pero ganás el doble de monedas. Si tu luz se apaga, perdés.",
        ],
        "hint": "Seguí la flecha hasta la zona de combate y elegí una opción. Para empezar, te sugiero 'con escape'.",
        "cheer": "¡A pelear! Cuidá que tu luz no baje de la mitad.",
    },

    # 19 - oleada
    {
        "text": (
            "Derrotá a todos los enemigos de la oleada golpeándolos "
            "con tu luz y juntá las monedas del premio."
        ),
        "tuto": [
            "Combate: golpeá a los enemigos con tu luz hasta eliminarlos a todos. Al terminar la oleada aparece el premio: ¡juntá las monedas!",
            "Cuidado con los mosquitos: se te pegan y te chupan la luz. Matalos rápido y usá tus objetos a tiempo.",
            "Al completar todas las oleadas de una zona ganás una gema, que sirve para abrir la puerta final del mapa.",
        ],
        "hint": "Golpeá a los enemigos con [[CLICK IZQ.]]. Si hay mosquitos, empezá por ellos: te chupan la luz.",
        "cheer": "¡Oleada superada! Qué guerrero.",
    },

    # 20 - antorcha
    {
        "text": (
            "Conseguí la antorcha: con G cambiás de golpe y "
            "lanzás una bola de fuego. ¡Probala!"
        ),
        "tuto": [
            "Antorcha: se desbloquea en la tienda al empezar la oleada {antorcha_wave} (en la Zona 1). Con [[G]] cambiás de golpe y lanzás una bola de fuego. ¡Probala!",
        ],
        "hint": "La antorcha se desbloquea en la tienda al llegar a la oleada {antorcha_wave}. Con ella equipada, usá [[G]] para cambiar de golpe.",
        "cheer": "¡FUEGO! Sos un pirotécnico.",
    },

    # 21 - construir
    {
        "text": (
            "Armá una base: comprá una fogata en la tienda, "
            "elegila en tu casillero y hacé click en el mapa para "
            "ponerla."
        ),
        "tuto": [
            "Construir: la sección Construcción de la tienda vende bolsa, cofre, tacho, yunque, máquina, fogata y candil (el martillo está en Objetos).",
            "La bolsa y el candil salen al piso y los movés con click izquierdo mantenido. El cofre, el tacho, el yunque, la máquina y la fogata los elegís en tu casillero y hacés click en el mapa: quedan fijos.",
            "La FOGATA ilumina mucho y te devuelve luz si estás cerca: dale madera con [[F]]. El CANDIL es más chico, gasta cera y mantiene lejos a los mosquitos.",
            "El TACHO borra objetos: elegí uno y hacé click sobre él ([[CTRL]] + click borra toda la casilla). Con el MARTILLO desarmás lo que construiste y lo volvés a mover.",
            "La bolsa y el cofre guardan lo que soltás o agarrás con el inventario lleno, y lo de adentro nunca vence.",
        ],
        "hint": "Comprá una fogata en la sección Construcción de la tienda, elegila en tu casillero y hacé click en el mapa.",
        "cheer": "¡Tu primera base! Qué hogareño.",
    },

    # 22 - Orkun
    {
        "text": (
            "Completá Orkun (zona 1, derecha): 10 oleadas, un "
            "jefe y una gema verde clara te esperan."
        ),
        "tuto": [
            "¡Último tramo! Completá Orkun: 10 oleadas, un jefe y una gema verde clara te esperan. Su jefe suelta una llave dorada para la Zona 2.",
            "A los jefes se los esquiva saltando con [[ESPACIO]]. Mirá bien sus movimientos antes de atacar. ¡Vos podés!",
        ],
        "hint": "Orkun es la zona de la derecha. Completá sus 10 oleadas y vencé al jefe.",
        "cheer": "¡Orkun es tuyo! Y con gema verde.",
    },

    # 23 - Stonun
    {
        "text": (
            "Ahora sí, Stonun (zona 2, izquierda, la del "
            "Guardián): 10 oleadas y una gema verde oscuro."
        ),
        "hint": "Stonun es la zona de la izquierda. La llave dorada del jefe de Orkun abre su puerta de oro.",
        "cheer": "¡Stonun conquistada! Sos imparable.",
    },

    # 24 - enciclopedia
    {
        "text": (
            "Completá la enciclopedia: descubrí las {creatures} "
            "criaturas del juego (la abrís desde la pausa con ESC)."
        ),
        "hint": "Abrí la pausa con [[ESC]] y mirá la enciclopedia. Las criaturas se descubren peleando contra ellas.",
        "cheer": "¡Enciclopedia completa! Sos una leyenda.",
    },
]


def apply_texts(objectives, **ctx):
    """Pisa los textos de la lista de objetivos con los de TEXTS."""

    if len(objectives) != len(TEXTS):

        print(
            "[tutorial] tutorial_texts.py tiene "
            f"{len(TEXTS)} pasos y el juego {len(objectives)}: "
            "no se aplican los textos nuevos"
        )

        return objectives

    for obj, texts in zip(objectives, TEXTS):

        obj["text"] = texts["text"].format(**ctx)

        if "tuto" in texts:
            obj["tuto"] = [p.format(**ctx) for p in texts["tuto"]]

        if "hint" in texts:
            obj["hint"] = texts["hint"].format(**ctx)

        if "cheer" in texts:
            obj["cheer"] = texts["cheer"].format(**ctx)

    return objectives