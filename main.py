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
from states.achievements import AchievementsMenu
from ui.slide_transition import SlideTransition
from ui.zoom_transition import ZoomTransition

from core.Save_manager import create_new_save, load_save
from core.audio_manager import audio

pygame.init()
audio.preload()

ANCHO = 1280
ALTO = 720

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
achievements_menu = None
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

transition = None

SLIDE_ON_RESPAWN = True


current_state = "startup"


running = True


def handle_menu_action(action):

    global name_menu, continue_menu, settings_menu, achievements_menu
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

        achievements_menu = AchievementsMenu(screen)

        current_state = "achievements"

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

                game.apply_loss()

            running = False

        if current_state == "menu":

            menu.handle_event(event)

        elif current_state == "settings":

            if settings_menu.handle_event(event) == "back":

                current_state = "menu"

        elif current_state == "achievements":

            if achievements_menu.handle_event(event) == "back":

                current_state = "menu"

        elif current_state == "name_input":

            result = name_menu.handle_event(
                event
            )

            if result == "back":


                current_state = "menu"

            elif result is not None:

                player_name = result[1]

                password_menu = PasswordMenu(screen, mode="set")

                current_state = "password_set"

        elif current_state == "password_set":

            result = password_menu.handle_event(
                event
            )

            if result == "back":

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

            if transition is not None:
                continue

            if comic.handle_event(event) == "done":


                game = NewGame(
                    screen,
                    player_name,
                    save_path=current_save_path,
                    mode=current_mode
                )

                game._intro_pending = True

                transition = SlideTransition(screen.copy())

                current_state = "gameplay"

        elif current_state == "gameplay":

            if transition is not None:
                continue

            result = game.handle_event(
                event
            )

            if result == "menu":

                current_state = "menu"

                menu.play_intro()


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

                transition = ZoomTransition(screen.copy())

                current_state = "gameplay"

            else:

                comic = Comic(screen)

                transition = ZoomTransition(screen.copy())

                current_state = "comic"
    elif current_state == "settings":

        settings_menu.update(dt)

    elif current_state == "comic":

        if transition is not None:

            if transition.update(dt) == "done":
                transition = None

        else:

            comic.update(dt)

    elif current_state == "gameplay":

        if transition is not None:

            if transition.update(dt) == "done":
                transition = None

            result = None

        else:

            result = game.update(dt)

        if result == "menu":

            current_state = "menu"

            menu.play_intro()

        elif result == "respawn":

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

    elif current_state == "achievements":

        achievements_menu.draw()

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
