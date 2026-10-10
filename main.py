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
from states.settings import Settings

from core.Save_manager import create_new_save, load_save

pygame.init()

ANCHO = 1280
ALTO = 720

screen = pygame.display.set_mode(
    (ANCHO, ALTO)
)

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


current_state = "startup"


running = True

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
        
        if current_state == "startup":

            if startup.update(dt) == "done":

                current_state = "menu"

        if current_state == "menu":

            action = menu.handle_event(
                event
            )

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

                print(
                    "Logros"
                )

            elif action == "quit":

                running = False

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

            if comic.handle_event(event) == "done":

                
                game = NewGame(
                    screen,
                    player_name,
                    save_path=current_save_path,
                    mode=current_mode
                )

                current_state = "gameplay"

        elif current_state == "gameplay":

            result = game.handle_event(
                event
            )

            if result == "menu":

                current_state = "menu"


    if current_state == "loading":

        if loading.update(dt) == "done":

            if is_continue:

                game = NewGame(
                    screen,
                    player_name,
                    save_path=current_save_path,
                    save_data=pending_save_data
                )

                current_state = "gameplay"

            else:

                comic = Comic(screen)

                current_state = "comic"
    elif current_state == "settings":

        settings_menu.update(dt)

    elif current_state == "comic":

        comic.update(dt)

    elif current_state == "gameplay":

        result = game.update(dt)

        if result == "menu":

            current_state = "menu"

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

    elif current_state == "gameplay":

        game.draw()


    pygame.display.flip()


pygame.quit()