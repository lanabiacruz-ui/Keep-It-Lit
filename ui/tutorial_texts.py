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
            "Está oscuro: busca el fósforo en el piso (sigue la flecha) y "
            "agárralo con E. Si en {countdown} segundos no tienes luz, pierdes."
        ),
        "tuto": [
            "¡Buuu! Jaja, perdón, es el trabajo. Soy [[Cenizo]], el fantasma de las cenizas, y voy a ayudarte a sobrevivir en este lugar tan oscuro. Yo ya fallé en lo de sobrevivir, pero de consejos entiendo.",
            "Tu luz es tu vida: la barra naranja de abajo. Se gasta con el tiempo y con cada golpe. Si se apaga, pierdes. Te lo digo por experiencia: yo me apagué hace rato.",
            "Ahora no tienes ni una chispa. Sigue la flecha naranja con [[W]] [[A]] [[S]] [[D]] hasta el fósforo y agárralo con [[E]]. ¡Tienes {countdown} segundos, y yo no puedo apurarte porque floto!",
        ],
        "hint": "Sigue la flecha naranja hasta el fósforo y presiona [[E]] al llegar. ¡Rápido, que el tiempo corre y yo no tengo reloj!",
        "cheer": "¡Fuego! Ya tienes tu primera lucecita. Sniff... crecen tan rápido.",
    },

    # 1 - moverse
    {
        "text": "Practica moverte con las cuatro teclas: W, A, S y D.",
        "tuto": [
            "¡Ya tienes luz! Primero lo básico: presiona [[W]] [[A]] [[S]] [[D]], una por una. La lista de arriba se tilda sola. Yo no necesito teclas: atravieso paredes.",
        ],
        "hint": "Prueba cada tecla de la lista: las que faltan están sin tildar. No es tan difícil, te lo juro.",
        "cheer": "¡Ya caminas como un campeón! Un campeón con piernas, qué lujo.",
    },

    # 2 - atacar
    {
        "text": (
            "Prueba atacar con click izquierdo. "
            "Cada golpe gasta un poco de luz."
        ),
        "tuto": [
            "Atacar: [[CLICK IZQ.]]. Golpeas con tu propia luz, pero cada golpe la gasta un poquito: no le pegues al aire (salvo ahora, que es práctica). Yo le pegaba al aire y mira cómo terminé. ¡Pruébalo!",
        ],
        "hint": "Haz click izquierdo en cualquier lado. Es solo una prueba, no te va a retar nadie. Yo menos.",
        "cheer": "¡Pum! Pegas fuerte. Menos mal que soy intocable.",
    },

    # 3 - agarrar
    {
        "text": (
            "Agarra un objeto del piso con E (madera, resina, aceite): "
            "sirven para que tu luz no se apague."
        ),
        "tuto": [
            "Agarrar: acércate a un objeto del piso (madera, resina, aceite) y presiona [[E]]. Sirven para recargar tu luz: son como el desayuno, pero para llamas. ¡Sigue la flecha!",
        ],
        "hint": "Camina hasta el objeto que marca la flecha y presiona [[E]] cuando estés cerca. Yo lo agarraría, pero mis manos son decorativas.",
        "cheer": "¡Botín conseguido! Ahora eres oficialmente un acumulador.",
    },

    # 4 - casilleros
    {
        "text": (
            "Prueba elegir casilleros: teclas 1 a 4, 5 y 6 (pociones), "
            "la tecla 7 (tu luz) y la rueda del mouse."
        ),
        "tuto": [
            "Inventario: tienes 4 casilleros ([[1]] al [[4]]), 2 marcos de pociones ([[5]] y [[6]]) y la tecla [[7]] elige tu luz equipada. Qué organizado, yo ni bolsillos tengo.",
            "También puedes recorrerlos con la [[RUEDA]] del mouse. Prueba todo: la lista se tilda sola, como por arte de magia. Magia fantasmal, claro.",
        ],
        "hint": "Presiona las teclas del 1 al 7 y gira la rueda del mouse. Faltan las que están sin tildar. Sí, hay que apretarlas todas: ni los fantasmas tenemos atajos.",
        "cheer": "¡Ya manejas el inventario como un pro! Hasta yo me perdí un poquito.",
    },

    # 5 - usar y soltar
    {
        "text": (
            "Usa un objeto (F o click derecho) y suelta otro con Q. "
            "Si te quedas sin objetos, agarra más del piso."
        ),
        "tuto": [
            "Usar: elige un casillero con algo y presiona [[F]] o [[CLICK DER.]]. Soltar: [[Q]] tira el objeto elegido (junto a una bolsa o un cofre, va adentro).",
            "Lo que queda en el piso se esfuma a los 5 minutos, como cualquier buen fantasma. ¡Pero lo puedes volver a agarrar con [[E]] antes!",
            "Madera: +25% de luz. Resina: +90% de a poco. Aceite: te deja en 75% y te da velocidad. Úsalos ANTES de quedarte a oscuras. Después no vas a poder leer este cartel, y me ofendo.",
        ],
        "hint": "Elige un casillero con un objeto y presiona [[F]]. Después, con otro, presiona [[Q]] para soltarlo. Primero usar, después soltar. Como en la vida.",
        "cheer": "¡Sabes cuidar tus recursos! Ni una chispa desperdiciada.",
    },

    # 6 - ayuda
    {
        "text": (
            "Prueba los botones de ayuda: ESC (pausa) y TAB "
            "(ocultar el objetivo)."
        ),
        "tuto": [
            "Ayuda: [[ESC]] abre la pausa (ahí está la enciclopedia de criaturas) y [[TAB]] esconde o muestra el objetivo. Prueba las dos. La pausa es mi botón favorito: nadie me apura.",
        ],
        "hint": "Presiona [[ESC]] y vuelve a apretarlo para seguir. Después prueba [[TAB]]. ¡Es un botón, no una bomba!",
        "cheer": "¡Entrenamiento básico completo! Ahora, a salir de aquí. Yo te espero... bueno, no: te sigo.",
    },

    # 7 - puerta de la cabana
    {
        "text": (
            "Sal de la cabaña: golpea la puerta con click izquierdo "
            "hasta romperla. Cada golpe gasta luz."
        ),
        "tuto": [
            "Puertas: golpéala con tu luz ([[CLICK IZQ.]]) hasta romperla. Cada golpe gasta luz, y cada tipo de puerta pide una luz distinta. Yo las atravieso, pero tengo ventajas. ¡Sigue la flecha!",
        ],
        "hint": "Acércate a la puerta que marca la flecha y dale click izquierdo varias veces. Insiste: la puerta es dura, pero tú más.",
        "cheer": "¡CRASH! Puerta fuera de servicio. Perdón, vecino.",
    },

    # 8 - sala central
    {
        "text": "Sigue el camino al norte hasta la sala central.",
        "tuto": [
            "Sigue el camino hacia el norte. La flecha te lleva a la sala central, que conecta todo el mapa. ¡Va a ser tu base! Vas a conocer cada rincón, a diferencia de mí, que nunca salí de aquí.",
        ],
        "hint": "Ve siempre hacia el norte (arriba). La flecha te va marcando el camino. Norte es arriba. Sí, arriba. No, no es un chiste.",
        "cheer": "¡Llegamos al centro del mapa! Yo flotaba, pero cuenta igual.",
    },

    # 9 - monedas
    {
        "text": (
            "Junta 10 monedas: hay tiradas por el mapa, en los cofres y "
            "las sueltan los slimes (mátalos a golpes)."
        ),
        "tuto": [
            "Monedas: sirven para comprar luces y objetos (a mí ya no me sirven, qué lástima). Se juntan solas al acercarte. Dorada = 1, azul = 5, roja = 10. ¡Junta 10!",
            "Slimes: son tranquilos y no atacan. Pégales con tu luz hasta matarlos: sueltan 10 monedas y una gelea que cura al comerla. Sí, es una gelatina. Sí, se come.",
        ],
        "hint": "Sigue la flecha hasta las monedas del piso, o busca un slime y golpéalo. Con cariño, pero golpéalo.",
        "cheer": "¡Tienes dinero! Ahora, a la tienda. No te las gastes todas en caramelos.",
    },

    # 10 - ir a la tienda
    {
        "text": (
            "Ve a la tienda (al norte de la sala central) y presiona F "
            "cerca del vendedor para hablarle."
        ),
        "tuto": [
            "Tienda: está al norte de la sala central. Acércate al vendedor hasta que aparezca la tecla [[F]] y presiónala. Se cierra con [[E]] o [[ESC]]. Ojo, el vendedor tiene costumbres muy raras.",
            "Ahí gastas tus monedas en luces, objetos y construcciones. Algunos productos se desbloquean al terminar cierta oleada en las salas de combate. Es como un centro comercial, pero con más oscuridad y menos aire acondicionado.",
        ],
        "hint": "La tienda queda al norte de la sala central. Cuando estés cerca del vendedor, presiona [[F]]. No muerde. Escupe, pero no muerde.",
        "cheer": "¡Bienvenido a la tienda! Se aceptan monedas, no se aceptan quejas.",
    },

    # 11 - info del producto
    {
        "text": (
            "Con la tienda abierta, haz click con la RUEDA del mouse "
            "sobre un producto para ver qué hace."
        ),
        "tuto": [
            "Info: apunta a un producto y haz click con la rueda del mouse (el botón del medio). Te explica qué hace y, en las luces, cuánto duran. Otro click la cierra. Sí, el botón del medio existe. Casi nadie lo usa, pobrecito.",
        ],
        "hint": "Con la tienda abierta, apunta a un producto y presiona la rueda del mouse como si fuera un botón. Porque es un botón. Sorpresa.",
        "cheer": "¡Informadísimo! Ya puedes dar una charla sobre madera.",
    },

    # 12 - comprar
    {
        "text": (
            "Cómprale algo al vendedor: elige un objeto, la cantidad "
            "y presiona Comprar."
        ),
        "tuto": [
            "Comprar: click en un producto lo suma al carrito, click derecho saca uno y el botón x15 suma 15 de golpe. Abajo ves el total; la papelera vacía el carrito.",
            "Cuando estés listo, presiona Comprar. Si no te alcanzan las monedas no cobra nada: saca algo o junta más. Te conviene un objeto (madera, cera...). Comprar sin dinero sería robar, y aquí somos gente de bien. Bueno, gente no, pero entiendes.",
        ],
        "hint": "Haz click en un producto para ponerlo en el carrito y después presiona el botón Comprar. ¡Es más fácil que hacer la fila del banco!",
        "cheer": "¡Primera compra! Se siente bien, ¿no? Casi tan bien como estar vivo. Casi.",
    },

    # 13 - agarrar lo comprado
    {
        "text": (
            "El vendedor escupe lo que compras: agárralo del piso "
            "con E."
        ),
        "tuto": [
            "Lo comprado: el vendedor lo escupe al piso, cerca de él. Sí, lo escupe. No preguntes. Acércate y presiona [[E]] para agarrarlo.",
            "Tip: con el imán ([[O]]) los objetos sueltos vuelan solos hacia ti.",
        ],
        "hint": "Mira el piso cerca del vendedor y presiona [[E]] sobre lo que escupió. Está un poco baboso, pero funciona igual.",
        "cheer": "¡Ñam! Ya es tuyo. Que aproveche.",
    },

    # 14 - inventario de la tienda
    {
        "text": (
            "Vuelve a abrir la tienda (F) y presiona TAB para ir a la "
            "pestaña Inventario."
        ),
        "tuto": [
            "Inventario de la tienda: con [[TAB]] cambias entre Tienda e Inventario. Ahí armas tus casilleros y tu luz como quieras y compras todo junto con 'Comprar inventario'. ¡Pruébalo! Yo te dejaría el mío, pero está vacío.",
        ],
        "hint": "Abre la tienda con [[F]] y presiona [[TAB]] para cambiar de pestaña. Tranquilo, no hay examen.",
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
            "Cofres: están en la sala de arriba a la izquierda. Acércate y presiona [[F]] (cuenta como un golpe) y después [[ESPACIO]] cuando el marcador esté en la zona marcada. Es un juego de timing, pero con tesoro.",
            "Cada cofre se abre 10 veces seguidas y después descansa 3 minutos. Dan monedas, madera, cera, aceite... y con suerte una GANZÚA, que abre un cofre sin minijuego (3 usos). Un tesoro que se abre solo. Qué envidia.",
        ],
        "hint": "Sigue la flecha a la sala de cofres. Cerca de uno, presiona [[F]] y después [[ESPACIO]] en el momento justo. Ritmo, paciencia y un poco de suerte.",
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
            "Luces: la vela ilumina más y dura más que el fósforo. Solo se consigue en la tienda (los cofres no la dan) y cuesta 55 monedas. Es el upgrade del fósforo: más luz, más drama.",
            "Solo puedes llevar una luz. Con el fósforo en la mano, la vela no se cambia: primero suéltalo (elige el casillero de la luz y presiona [[Q]]).",
            "Después agarra la vela con [[E]] y se equipa sola. ¡Junta las 55 monedas! Ahorra como una hormiga.",
        ],
        "hint": "Necesitas 55 monedas. Compra la vela en la tienda, suelta el fósforo con [[Q]] y agarra la vela con [[E]]. Paciencia: las velas no se compran solas.",
        "cheer": "¡Una vela! Ahora sí hay luz de verdad. Qué elegante, pareces de cumpleaños.",
    },

    # 17 - puerta gris
    {
        "text": (
            "Golpea con tu vela una puerta gris de la sala "
            "central para romperla."
        ),
        "tuto": [
            "Puertas: las grises de la sala central llevan a las zonas de combate. Se rompen solo con vela o antorcha: con un fósforo ni cosquillas. ¡Sigue la flecha!",
        ],
        "hint": "Con la vela equipada, dale click izquierdo a la puerta gris que marca la flecha.",
        "cheer": "¡Puerta rota! Se viene la acción. Yo miro desde aquí, con palomitas.",
    },

    # 18 - entrar al combate
    {
        "text": (
            "Entra a una zona de combate y elige cómo jugar: con escape "
            "o sin escape (premio doble)."
        ),
        "tuto": [
            "Zonas de combate: tienen oleadas de enemigos. Antes de entrar te avisa el nombre de la zona y, al entrar, eliges cómo jugar. Spoiler: hay enemigos.",
            "Con escape: la salida queda abierta, así que si te complicas puedes irte caminando y volver después. Ideal para aprender (o para cobardes: no te juzgo, yo soy un fantasma asustado).",
            "Sin escape (premio x2): la salida se cierra hasta terminar la oleada. No hay huida, pero ganas el doble de monedas. Si tu luz se apaga, pierdes. Bienvenido al club de los valientes... o de los locos.",
        ],
        "hint": "Sigue la flecha hasta la zona de combate y elige una opción. Para empezar, te sugiero 'con escape'. Para morir con dignidad hay tiempo.",
        "cheer": "¡A pelear! Cuida que tu luz no baje de la mitad. ¡Y no me mires, que me da vergüenza!",
    },

    # 19 - oleada
    {
        "text": (
            "Derrota a todos los enemigos de la oleada golpeándolos "
            "con tu luz y junta las monedas del premio."
        ),
        "tuto": [
            "Combate: golpea a los enemigos con tu luz hasta eliminarlos a todos. Al terminar la oleada aparece el premio: ¡junta las monedas! Es la parte divertida, o eso dicen.",
            "Cuidado con los mosquitos: se te pegan y te chupan la luz. Son como las visitas pesadas: no se van más. Mátalos rápido y usa tus objetos a tiempo.",
            "Al completar todas las oleadas de una zona ganas una gema, que sirve para abrir la puerta final del mapa.",
        ],
        "hint": "Golpea a los enemigos con [[CLICK IZQ.]]. Si hay mosquitos, empieza por ellos: te chupan la luz.",
        "cheer": "¡Oleada superada! Qué guerrero. Hasta a mí me dio un escalofrío, y eso que estoy muerto.",
    },

    # 20 - antorcha
    {
        "text": (
            "Consigue la antorcha: con G cambias de golpe y "
            "lanzas una bola de fuego. ¡Pruébala!"
        ),
        "tuto": [
            "Antorcha: se desbloquea en la tienda al terminar la oleada {antorcha_wave} (en la Zona 1). Con [[G]] cambias de golpe y lanzas una bola de fuego. ¡Pruébala! Y no me apuntes a mí, que ya soy ceniza.",
        ],
        "hint": "La antorcha se desbloquea en la tienda al terminar la oleada {antorcha_wave}. Con ella equipada, usa [[G]] para cambiar de golpe.",
        "cheer": "¡FUEGO! Eres un pirotécnico. Quemas muy bien.",
    },

    # 21 - construir
    {
        "text": (
            "Arma una base: compra una fogata en la tienda, "
            "elígela en tu casillero y haz click en el mapa para "
            "ponerla."
        ),
        "tuto": [
            "Construir: la sección Construcción de la tienda vende bolsa, cofre, basurero, yunque, máquina, fogata y candil (el martillo está en Objetos). Hora de jugar a la casita.",
            "La bolsa y el candil salen al piso y los mueves con click izquierdo mantenido. El cofre, el basurero, el yunque, la máquina y la fogata los eliges en tu casillero y haces click en el mapa: quedan fijos.",
            "La FOGATA ilumina mucho y te devuelve luz si estás cerca: dale madera con [[F]]. El CANDIL es más chico, gasta cera y mantiene lejos a los mosquitos.",
            "El BASURERO borra objetos: elige uno y haz click sobre él ([[CTRL]] + click borra toda la casilla). Con el MARTILLO desarmas lo que construiste y lo vuelves a mover.",
            "La bolsa y el cofre guardan lo que sueltas o agarras con el inventario lleno, y lo de adentro nunca vence. A diferencia de la leche.",
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
            "¡Último tramo! Completa Orkun: 10 oleadas, un jefe y una gema verde clara te esperan. Su jefe suelta una llave dorada para la Zona 2. Sí, son 10. Cuéntalas conmigo, aunque no tengo dedos.",
            "A los jefes se los esquiva saltando con [[ESPACIO]]. Mira bien sus movimientos antes de atacar. ¡Tú puedes! Y si no puedes... también te quiero.",
        ],
        "hint": "Orkun es la zona de la derecha. Completa sus 10 oleadas y vence al jefe.",
        "cheer": "¡Orkun es tuyo! Y con gema verde. Brillas más que yo, qué envidia.",
    },

    # 23 - Stonun
    {
        "text": (
            "Ahora sí, Stonun (zona 2, izquierda, la del "
            "Guardián): 10 oleadas y una gema verde oscuro."
        ),
        "hint": "Stonun es la zona de la izquierda. La llave dorada del jefe de Orkun abre su puerta de oro.",
        "cheer": "¡Stonun conquistada! Eres imparable. Ya me da miedo hasta a mí.",
    },

    # 24 - enciclopedia
    {
        "text": (
            "Completa la enciclopedia: descubre las {creatures} "
            "criaturas del juego (la abres desde la pausa con ESC)."
        ),
        "hint": "Abre la pausa con [[ESC]] y mira la enciclopedia. Las criaturas se descubren peleando contra ellas.",
        "cheer": "¡Enciclopedia completa! Eres una leyenda. Escribo tu nombre en la pared. Con ceniza.",
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