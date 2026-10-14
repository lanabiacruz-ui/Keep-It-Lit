import pygame

from states.main_menu import MainMenu
from states.menu_carga import MenuCarga
from states.mode_select import ModeSelect
from states.password_menu import PasswordMenu
from states.continue_game import ContinueGame
from states.loading import Loading
from states.comic import Comic
from states.new_game import NewGame
from states.startup import Startup
from states.settings import Settings, load_settings
from ui.slide_transition import SlideTransition
from ui.zoom_transition import ZoomTransition

from core.Save_manager import create_new_save, load_save
from core.audio_manager import audio

pygame.init()
audio.preload()

ANCHO = 1280
ALTO = 720

# SCALED: el juego siempre se dibuja en 1280x720 y pygame lo estira a
# la pantalla. Asi la pantalla completa se prende y apaga bien (y el
# mouse sigue coincidiendo con lo que se ve).
# Se arranca como dice Configuraciones (antes siempre arrancaba en
# ventana, aunque el interruptor dijera "activado").
_flags = pygame.SCALED

if load_settings().get("fullscreen"):
    _flags |= pygame.FULLSCREEN

try:
    screen = pygame.display.set_mode((ANCHO, ALTO), _flags)
except pygame.error:
    screen = pygame.display.set_mode((ANCHO, ALTO))

pygame.display.set_caption(
    "Keep It Lit"
)

clock = pygame.time.Clock()
startup = Startup(screen)
menu = MainMenu(screen)
settings_menu = None
name_menu = None
password_menu = None
mode_menu = None
continue_menu = None
loading = None
comic = None
game = None

player_name = ""
current_mode = "normal"
current_password = ""

current_save_path = None
pending_save_data = None
is_continue = False

# Transicion de entrada al juego (la pantalla anterior se desliza). Mientras
# esta activa el juego no avanza (ni el tutorial) y no recibe clicks.
transition = None

# Tambien hacer la transicion al volver a jugar despues de perder
SLIDE_ON_RESPAWN = True


current_state = "startup"


running = True


def handle_menu_action(action):
    """Lo que pasa cuando el menu principal entrega una opcion."""

    global name_menu, continue_menu, settings_menu
    global current_state, running

    if action == "new_game":

        name_menu = MenuCarga(screen)

        current_state = "name_input"

    elif action == "continue_game":

        continue_menu = ContinueGame(screen)

        current_state = "continue"

    elif action == "settings":

        settings_menu = Settings(screen)

        current_state = "settings"

    elif action == "achievements":

        print("Logros")

    elif action == "quit":

        running = False


while running:

    dt = min(clock.tick(60) / 1000, 0.05)

    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            if (
                current_state == "gameplay"
                and game is not None
                and game.state == "playing"
            ):

                game.save_progress()

            elif (
                current_state == "gameplay"
                and game is not None
                and game.state in ("dying", "lost")
            ):

                # Cerrar la ventana al perder no evita la derrota
                game.apply_loss()

            running = False
        
        if current_state == "menu":

            # La accion elegida la entrega menu.poll() cuando termina el
            # efecto del clic (mas abajo, en la parte de update)
            menu.handle_event(event)

        elif current_state == "settings":

            if settings_menu.handle_event(event) == "back":

                current_state = "menu"

        elif current_state == "name_input":

            result = name_menu.handle_event(
                event
            )

            if result == "back":

              
                current_state = "menu"

            elif result is not None:

                player_name = result[1]

                # Despues del nombre: contraseña, y luego el modo.
                # La partida se crea al final.
                password_menu = PasswordMenu(screen, mode="set")

                current_state = "password_set"

        elif current_state == "password_set":

            result = password_menu.handle_event(
                event
            )

            if result == "back":

                # Vuelve al nombre (se sigue escribiendo)
                pygame.key.start_text_input()

                current_state = "name_input"

            elif result is not None:

                current_password = result[1]

                password_menu.finish()

                mode_menu = ModeSelect(screen)

                current_state = "mode_select"

        elif current_state == "mode_select":

            result = mode_menu.handle_event(
                event
            )

            if result == "back":

                # Vuelve a la contraseña (se sigue escribiendo)
                pygame.key.start_text_input()

                current_state = "password_set"

            elif result is not None:

                current_mode = result[1]

                save_path = create_new_save(
                    player_name,
                    current_mode,
                    current_password
                )

                current_password = ""

                if save_path is None:

                    # Los 3 slots estan ocupados: no se pisa ninguna
                    # partida, se avisa y se vuelve al nombre.
                    name_menu.message = (
                        "No hay espacio. Borrá una partida primero."
                    )

                    pygame.key.start_text_input()

                    current_state = "name_input"

                else:

                    current_save_path = save_path
                    pending_save_data = None
                    is_continue = False

                    loading = Loading(screen)

                    current_state = "loading"

        elif current_state == "continue":

            result = continue_menu.handle_event(
                event
            )

            if result == "back":

                current_state = "menu"

            elif result is not None:

                _, save_path, save_data = result

                player_name = save_data.get(
                    "player_name",
                    "Jugador"
                )

                current_save_path = save_path
                pending_save_data = save_data
                is_continue = True

                loading = Loading(screen)

                current_state = "loading"

        elif current_state == "comic":

            # Durante el zoom al monitor el comic todavia no arranca
            if transition is not None:
                continue

            if comic.handle_event(event) == "done":

                
                game = NewGame(
                    screen,
                    player_name,
                    save_path=current_save_path,
                    mode=current_mode
                )

                # Partida nueva: al terminar las instrucciones hay una
                # transicion al juego (la luz se enciende de a poco)
                game._intro_pending = True

                # La pantalla del comic se desliza y deja ver el juego
                # (el tutorial arranca recien cuando termina)
                transition = SlideTransition(screen.copy())

                current_state = "gameplay"

        elif current_state == "gameplay":

            # Durante la transicion de entrada no se juega: el tutorial
            # espera y los clicks no pasan al juego
            if transition is not None:
                continue

            result = game.handle_event(
                event
            )

            if result == "menu":

                current_state = "menu"

                menu.play_intro()


    # La pantalla de inicio avanza sola, una vez por frame (antes se
    # actualizaba dentro del bucle de eventos y solo avanzaba con
    # clicks, teclas o movimiento del mouse).
    if current_state == "startup":

        if startup.update(dt) == "done":

            current_state = "menu"

            menu.play_intro()

    elif current_state == "menu":

        action = menu.poll()

        if action is not None:

            handle_menu_action(action)

    elif current_state == "loading":

        if loading.update(dt) == "done":

            if is_continue:

                game = NewGame(
                    screen,
                    player_name,
                    save_path=current_save_path,
                    save_data=pending_save_data
                )

                # Al continuar una partida: zoom al monitor y aparece la
                # partida (parte del ultimo cuadro de la pantalla de carga)
                transition = ZoomTransition(screen.copy())

                current_state = "gameplay"

            else:

                comic = Comic(screen)

                # Zoom al monitor y aparece el comic
                transition = ZoomTransition(screen.copy())

                current_state = "comic"
    elif current_state == "settings":

        settings_menu.update(dt)

    elif current_state == "comic":

        if transition is not None:

            # Zoom de entrada: el comic espera
            if transition.update(dt) == "done":
                transition = None

        else:

            comic.update(dt)

    elif current_state == "gameplay":

        if transition is not None:

            # Transicion de entrada: el juego espera
            if transition.update(dt) == "done":
                transition = None

            result = None

        else:

            result = game.update(dt)

        if result == "menu":

            current_state = "menu"

            menu.play_intro()

        elif result == "respawn":

            # Perdiste en modo normal: vuelve directo a la partida
            data = (
                load_save(current_save_path)
                if current_save_path else None
            )

            if data is None:

                current_state = "menu"

            else:

                game = NewGame(
                    screen,
                    player_name,
                    save_path=current_save_path,
                    save_data=data
                )

                if SLIDE_ON_RESPAWN:
                    transition = SlideTransition(screen.copy())


    screen.fill((0, 0, 0))
    
    if current_state == "startup":

        startup.draw()

    elif current_state == "menu":

        menu.draw()
        
    elif current_state == "settings":

        settings_menu.draw()

    elif current_state == "name_input":

        name_menu.draw()

    elif current_state == "password_set":

        password_menu.draw()

    elif current_state == "mode_select":

        mode_menu.draw()

    elif current_state == "continue":

        continue_menu.draw()

    elif current_state == "loading":

        loading.draw()

    elif current_state == "comic":

        comic.draw()

        if transition is not None:
            transition.draw(screen)

    elif current_state == "gameplay":

        game.draw()

        if transition is not None:
            transition.draw(screen)


    pygame.display.flip()


pygame.quit()