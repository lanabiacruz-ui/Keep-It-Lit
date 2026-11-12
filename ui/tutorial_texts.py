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

from ui.tutorial import ASK_MARK

TEXTS = [

    # 0 - fosforo
    {
        "text": (
            "Está oscuro: busca el fósforo en el piso (sigue la flecha) y "
            "agárralo con E. Si en {countdown} segundos no tienes luz, pierdes."
        ),
        "tuto": [
            "¡Buuu! Perdón, es el trabajo. Soy [[Cenizo]], un fantasma, y te voy a ayudar a sobrevivir acá. Yo ya fallé, pero de consejos entiendo.",
            ASK_MARK + "Antes de seguir: ¿cómo te llamas?",
            "¡{nombre}! Buen nombre. Los fantasmas tenemos mucha memoria: no lo olvido.",
            "Este mundo tenía luz en cada rincón. Una noche todo se apagó, y ahora la oscuridad se come a quien se queda sin llama.",
            "Tu luz es tu VIDA y tu ARMA a la vez. Es la barra naranja de abajo: se gasta con el tiempo y con cada golpe. Si se apaga, pierdes.",
            "Abajo también tienes tus casilleros, donde guardas los objetos que encuentres.",
            "Ahora no tienes ni una chispa, {nombre}. Ve hasta el fósforo con [[W]] [[A]] [[S]] [[D]] y agárralo con [[E]]. ¡Tienes {countdown} segundos!",
        ],
        "hint": "Sigue la flecha naranja hasta el fósforo y presiona [[E]] al llegar. ¡Rápido, que el tiempo corre!",
        "cheer": "¡Fuego! Ya tienes tu primera lucecita. Sniff... crecen tan rápido.",
    },

    # 1 - moverse
    {
        "text": "Practica moverte con las cuatro teclas: W, A, S y D.",
        "tuto": [
            "¡Ya tienes luz! Prueba [[W]] [[A]] [[S]] [[D]], una por una. La lista de arriba se tilda sola.",
        ],
        "hint": "Prueba cada tecla de la lista: las que faltan están sin tildar.",
        "cheer": "¡Ya caminas como un campeón! Con piernas y todo, qué lujo.",
    },

    # 2 - atacar
    {
        "text": (
            "Prueba atacar con click izquierdo. "
            "Cada golpe gasta un poco de luz."
        ),
        "tuto": [
            "Atacar: [[CLICK IZQ.]]. Ojo: cada golpe gasta un poquito de luz, así que no le pegues al aire. Salvo ahora, que es práctica.",
        ],
        "hint": "Haz click izquierdo en cualquier lado. Es solo una prueba.",
        "cheer": "¡Pum! Pegas fuerte, {nombre}. Menos mal que soy intocable.",
    },

    # 3 - agarrar
    {
        "text": (
            "Agarra un objeto del piso con E (madera o aceite): "
            "sirven para que tu luz no se apague."
        ),
        "tuto": [
            "Hay objetos tirados por el mapa. Acércate a uno y presiona [[E]] para guardarlo en tus casilleros. Siguiendo la flecha lo encuentras.",
        ],
        "hint": "Camina hasta el objeto que marca la flecha y presiona [[E]] cuando estés cerca.",
        "cheer": "¡Botín conseguido, {nombre}! Ahora eres oficialmente un acumulador.",
    },

    # 4 - casilleros
    {
        "text": (
            "Prueba elegir casilleros: teclas 1 a 4, 5 y 6 (pociones), "
            "la tecla 7 (tu luz) y la rueda del mouse."
        ),
        "tuto": [
            "Tus casilleros: [[1]] al [[4]] guardan objetos, [[5]] y [[6]] son marcos extra, y [[7]] elige tu luz.",
            "También puedes pasar de uno a otro con la [[RUEDA]] del mouse. Prueba todo: la lista se tilda sola.",
        ],
        "hint": "Presiona las teclas del 1 al 7 y gira la rueda del mouse. Faltan las que están sin tildar.",
        "cheer": "¡Ya manejas el inventario como un pro, {nombre}!",
    },

    # 5 - ver, usar y soltar
    {
        "text": (
            "Mantén click izquierdo sobre un casillero para ver qué hace "
            "el objeto, úsalo (F o click derecho) y suelta otro con Q."
        ),
        "tuto": [
            "¿No sabes qué hace un objeto? ¡Pregúntale! Mantén apretado el [[CLICK IZQ.]] sobre su casillero y aparece un cartel con su nombre y su efecto. Suelta y se va.",
            "Ya sabiendo qué hace, úsalo: elígelo y presiona [[F]] o [[CLICK DER.]]. Y para tirar uno al piso, [[Q]].",
            "Lo que sueltas se esfuma a los 5 minutos, pero puedes volver a agarrarlo con [[E]].",
            "Un consejo: usa tus objetos ANTES de quedarte a oscuras. Si no, ni vas a poder leer mis carteles, y me ofendo.",
        ],
        "hint": "Mantén click izquierdo sobre un casillero con un objeto para ver qué hace. Después elige uno y presiona [[F]], y con otro presiona [[Q]].",
        "cheer": "¡Sabes cuidar tus recursos! Ni una chispa desperdiciada.",
    },

    # 6 - ayuda
    {
        "text": (
            "Prueba los botones de ayuda: ESC (pausa) y TAB "
            "(ocultar el objetivo)."
        ),
        "tuto": [
            "[[ESC]] abre la pausa (ahí está la enciclopedia de criaturas) y [[TAB]] esconde o muestra el objetivo. Prueba las dos.",
        ],
        "hint": "Presiona [[ESC]] y vuelve a apretarlo para seguir. Después prueba [[TAB]].",
        "cheer": "¡Entrenamiento básico completo! Ahora, a salir de aquí.",
    },

    # 6b - baile (Six Seven)
    {
        "text": "Haz un baile: abre la rueda de bailes con B y elige Six Seven.",
        "tuto": [
            "Tengo un pedido muy importante: ¡hazme un Six Seven! Es una orden oficial de fantasma.",
            "Presiona [[B]], apunta con el mouse a Six Seven y haz click. Ahí también hay un Dab y un Saludo.",
        ],
        "hint": "Presiona [[B]], elige Six Seven en la rueda y haz click.",
        "cheer": "¡SIX SEVEN! Eres oficialmente el mejor bailarín de la mazmorra.",
    },

    # 7 - puerta de la cabana
    {
        "text": (
            "Sal de la cabaña: golpea la puerta con click izquierdo "
            "hasta romperla. Cada golpe gasta luz."
        ),
        "tuto": [
            "Para salir hay que romper la puerta: golpéala con [[CLICK IZQ.]] hasta que ceda. Cada golpe gasta luz. ¡Sigue la flecha!",
        ],
        "hint": "Acércate a la puerta que marca la flecha y haz click izquierdo varias veces.",
        "cheer": "¡CRASH! Puerta fuera de servicio. Perdón, vecino.",
    },

    # 8 - sala central
    {
        "text": "Sigue el camino al norte hasta la sala central.",
        "tuto": [
            "Sigue el camino hacia el norte. La flecha te lleva a la sala central, que conecta todo el mapa. ¡Va a ser tu base!",
        ],
        "hint": "Ve siempre hacia el norte (arriba). La flecha te va marcando el camino.",
        "cheer": "¡Llegamos al centro del mapa! Yo flotaba, pero cuenta igual.",
    },

    # 9 - monedas
    {
        "text": (
            "Junta 10 monedas: hay tiradas por el mapa, en los cofres y "
            "las sueltan los slimes (mátalos a golpes)."
        ),
        "tuto": [
            "Las monedas sirven para comprar cosas y las consigues del piso, de los cofres, matando slimes, ganando oleadas de enemigos (la forma más rentable) y cobrando recompensas en la enciclopedia de la pausa por cada criatura que descubres. Se juntan solas al acercarte: dorada = 1, azul = 5, roja = 10. ¡Junta 10!",
            "Los slimes no atacan: pégales hasta matarlos y sueltan monedas y una gelea que cura al comerla. Sí, se come.",
        ],
        "hint": "Sigue la flecha hasta las monedas del piso, o busca un slime y golpéalo.",
        "cheer": "¡Tienes dinero! Ahora, a la tienda.",
    },

    # 10 - ir a la tienda
    {
        "text": (
            "Ve a la tienda (al norte de la sala central) y presiona F "
            "cerca del vendedor para hablarle."
        ),
        "tuto": [
            "La tienda está al norte de la sala central. Acércate al vendedor hasta que aparezca la tecla [[F]] y presiónala. Para cerrarla: [[E]] o [[ESC]].",
            "Ahí gastas monedas en luces, objetos y construcciones. Algunos productos se desbloquean al pasar oleadas en las salas de combate.",
        ],
        "hint": "La tienda queda al norte de la sala central. Cerca del vendedor, presiona [[F]].",
        "cheer": "¡Bienvenido a la tienda! Se aceptan monedas, no se aceptan quejas.",
    },

    # 11 - info del producto
    {
        "text": (
            "Con la tienda abierta, haz click con la RUEDA del mouse "
            "sobre un producto para ver qué hace."
        ),
        "tuto": [
            "En la tienda también puedes preguntar qué hace cada cosa: apunta a un producto y haz click con la [[RUEDA]] del mouse (el botón del medio).",
            "Te muestra qué hace y, en las luces, cuánta luz da y cuánto dura. Otro click cierra el cartel. ¡Mira antes de comprar!",
        ],
        "hint": "Con la tienda abierta, apunta a un producto y aprieta la rueda del mouse como si fuera un botón.",
        "cheer": "¡Informadísimo! Ya puedes dar una charla sobre madera.",
    },

    # 12 - comprar
    {
        "text": (
            "Cómprale algo al vendedor: elige un objeto, la cantidad "
            "y presiona Comprar."
        ),
        "tuto": [
            "Comprar: click en un producto lo suma al carrito, click derecho saca uno y el botón x15 suma 15 de golpe. La papelera vacía el carrito.",
            "Cuando estés listo, presiona Comprar. Si no te alcanza, saca algo o junta más monedas. Te conviene un objeto (madera, cera...).",
        ],
        "hint": "Haz click en un producto para ponerlo en el carrito y después presiona el botón Comprar.",
        "cheer": "¡Primera compra! Se siente bien, ¿no?",
    },

    # 13 - agarrar lo comprado
    {
        "text": (
            "El vendedor escupe lo que compras: agárralo del piso "
            "con E."
        ),
        "tuto": [
            "El vendedor escupe lo que compras al piso, cerca de él. Sí, lo escupe. Acércate y presiona [[E]] para agarrarlo.",
        ],
        "hint": "Mira el piso cerca del vendedor y presiona [[E]] sobre lo que escupió.",
        "cheer": "¡Ñam! Ya es tuyo. Que aproveche.",
    },

    # 14 - inventario de la tienda
    {
        "text": (
            "Vuelve a abrir la tienda (F) y presiona TAB para ir a la "
            "pestaña Inventario."
        ),
        "tuto": [
            "Con [[TAB]] cambias entre Tienda e Inventario. En Inventario ordenas tus casilleros y tu luz como quieras, y compras todo junto con 'Comprar inventario'.",
        ],
        "hint": "Abre la tienda con [[F]] y presiona [[TAB]] para cambiar de pestaña.",
        "cheer": "¡Ya eres todo un comerciante!",
    },

    # 15 - cofres
    {
        "text": (
            "Ve a la sala de cofres (arriba a la izquierda). Acércate a "
            "un cofre y presiona F, después ESPACIO en la zona marcada para "
            "abrirlo."
        ),
        "tuto": [
            "Los cofres están en la sala de arriba a la izquierda. Acércate, presiona [[F]] y después [[ESPACIO]] cuando el marcador esté en la zona marcada. Es un juego de timing.",
            "Cada cofre se abre 10 veces y después descansa 3 minutos. Dan monedas y objetos.",
        ],
        "hint": "Sigue la flecha a la sala de cofres. Cerca de uno, presiona [[F]] y después [[ESPACIO]] en el momento justo.",
        "cheer": "¡Cofre abierto! ¿Qué habrá adentro? ¡Yo esperaba un fantasma amigo!",
    },

    # 16 - vela
    {
        "text": (
            "Consigue una vela, una luz mejor que el fósforo: solo se "
            "consigue en la tienda y cuesta 55 monedas. Suelta el fósforo "
            "antes (casillero de luz y Q)."
        ),
        "tuto": [
            "La vela ilumina más y dura más que el fósforo. Solo se vende en la tienda: 55 monedas.",
            "Solo puedes llevar una luz. Primero suelta el fósforo (elige el casillero de la luz y presiona [[Q]]) y después agarra la vela con [[E]]: se equipa sola.",
        ],
        "hint": "Necesitas 55 monedas. Compra la vela, suelta el fósforo con [[Q]] y agarra la vela con [[E]].",
        "cheer": "¡Una vela! Ahora sí hay luz de verdad. Qué elegante, pareces de cumpleaños.",
    },

    # 17 - puerta gris
    {
        "text": (
            "Golpea con tu vela una puerta gris de la sala "
            "central para romperla."
        ),
        "tuto": [
            "La puerta gris de la sala central (a la derecha) lleva a Orkun, la primera zona de combate. Solo se rompe con vela o antorcha: con un fósforo, ni cosquillas.",
        ],
        "hint": "Con la vela equipada, haz click izquierdo sobre la puerta gris que marca la flecha.",
        "cheer": "¡Puerta rota! Se viene la acción. Yo miro desde aquí, con palomitas.",
    },

    # 18 - entrar al combate
    {
        "text": (
            "Entra a una zona de combate y elige cómo jugar: con escape "
            "o sin escape (premio doble)."
        ),
        "tuto": [
            "Las zonas de combate tienen oleadas de enemigos. Al entrar eliges cómo jugar.",
            "CON ESCAPE: la salida queda abierta. Si te complicas, te vas y vuelves después. Ideal para aprender.",
            "SIN ESCAPE: la salida se cierra hasta terminar la oleada, pero ganas el doble de monedas. Si tu luz se apaga, pierdes.",
        ],
        "hint": "Sigue la flecha hasta la zona de combate y elige una opción. Para empezar, te sugiero 'con escape'.",
        "cheer": "¡A pelear! Cuida que tu luz no baje de la mitad.",
    },

    # 19 - oleada
    {
        "text": (
            "Derrota a todos los enemigos de la oleada golpeándolos "
            "con tu luz y junta las monedas del premio."
        ),
        "tuto": [
            "Golpea a los enemigos con tu luz hasta eliminarlos a todos. Al terminar la oleada aparece un premio en monedas: es la mejor forma de ganar plata, y cada oleada paga más que la anterior. ¡Júntalas!",
            "Cada oleada es más difícil que la anterior y van apareciendo enemigos nuevos. En la enciclopedia de la pausa ([[ESC]]) ves cómo es cada uno.",
            "Si completas todas las oleadas de una zona ganas una gema, que sirve para abrir la puerta final del mapa.",
        ],
        "hint": "Golpea a los enemigos con [[CLICK IZQ.]] hasta eliminarlos a todos y después junta las monedas del premio.",
        "cheer": "¡Oleada superada! Hasta a mí me dio un escalofrío, y eso que estoy muerto.",
    },

    # 21 - construir
    {
        "text": (
            "Arma una base: compra una fogata en la tienda, "
            "elígela en tu casillero y haz click en el mapa para "
            "ponerla."
        ),
        "tuto": [
            "En la sección Construcción de la tienda hay cosas para armar tu base. Empieza por la FOGATA: ilumina mucho y te devuelve luz si estás cerca. Ponle madera con [[F]].",
            "Para ponerla, elígela en tu casillero y haz click en el mapa: queda fija. Con el MARTILLO (en Objetos) la desarmas para moverla.",
        ],
        "hint": "Compra una fogata en la sección Construcción de la tienda, elígela en tu casillero y haz click en el mapa.",
        "cheer": "¡Tu primera base! Qué hogareño. Falta la alfombra de bienvenida.",
    },

    # 22 - Orkun
    {
        "text": (
            "Completa Orkun (zona 1, derecha): 10 oleadas, un "
            "jefe y una gema verde clara te esperan."
        ),
        "tuto": [
            "¡Último tramo, {nombre}! Completa Orkun: 10 oleadas, un jefe y una gema verde clara. El jefe suelta una llave dorada para la Zona 2.",
            "A los jefes se los esquiva saltando con [[ESPACIO]]. Mira bien sus movimientos antes de atacar.",
        ],
        "hint": "Orkun es la zona de la derecha. Completa sus 10 oleadas y vence al jefe.",
        "cheer": "¡Orkun es tuyo, {nombre}! Y con gema verde. Brillas más que yo.",
    },

    # 23 - Stonun
    {
        "tuto": [
            "Stonun es la zona de la izquierda y es MUCHO más difícil. No entres sin haber terminado Orkun, sin una buena luz (vela o antorcha) y sin objetos en tus casilleros.",
            "Ahí manda el Guardián y, al final, te espera el Golem Colosal. Salta sus ondas con [[ESPACIO]] y ten paciencia.",
        ],
        "text": (
            "Ahora sí, Stonun (zona 2, izquierda, la del "
            "Guardián): 10 oleadas y una gema verde oscuro."
        ),
        "hint": "Stonun es la zona de la izquierda. La llave dorada del jefe de Orkun abre su puerta de oro.",
        "cheer": "¡Stonun conquistada, {nombre}! Eres imparable.",
    },

    # 24 - enciclopedia
    {
        "text": (
            "Completa la enciclopedia: descubre las {creatures} "
            "criaturas del juego (la abres desde la pausa con ESC)."
        ),
        "tuto": [
            "Repaso rápido, {nombre}: [[B]] bailes, [[G]] cambia el golpe, [[TAB]] esconde el objetivo, [[RUEDA]] cambia de casillero, [[Q]] suelta ([[SHIFT]] + [[Q]] toda la casilla), [[F]] usa o abre la tienda, [[ESC]] pausa.",
            "Si cambias teclas en Ajustes, la guía de ahí te las recuerda.",
            "Ahora sí, el resto es cosa tuya. Yo sigo flotando por aquí.",
        ],
        "hint": "Abre la pausa con [[ESC]] y mira la enciclopedia. Las criaturas se descubren peleando contra ellas.",
        "cheer": "¡Enciclopedia completa! Eres una leyenda, {nombre}. Escribo tu nombre en la pared. Con ceniza.",
    },
]


def apply_texts(objectives, **ctx):
    """Pisa los textos de la lista de objetivos con los de TEXTS."""

    ctx.setdefault("nombre", "{nombre}")

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