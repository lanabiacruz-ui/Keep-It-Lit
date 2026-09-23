import pygame

from states.main_menu import MainMenu
from states.new_game import NewGame

pygame.init()

ANCHO = 1280
ALTO = 720

screen = pygame.display.set_mode(
    (ANCHO, ALTO)
)

pygame.display.set_caption(
    "Soulmon"
)

clock = pygame.time.Clock()

menu = MainMenu(screen)

# El estado de gameplay se crea recién cuando se
# elige "Nueva partida" (todavía no existe al arrancar)
game = None

# "menu" o "gameplay"
current_state = "menu"


running = True

while running:

    dt = clock.tick(60) / 1000

    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            running = False

        if current_state == "menu":

            action = menu.handle_event(
                event
            )

            if action == "new_game":

                # Arranca una partida nueva y cambia de pantalla
                game = NewGame(screen)

                current_state = "gameplay"

            elif action == "continue_game":

                print(
                    "Continuar partida"
                )

            elif action == "settings":

                print(
                    "Configuraciones"
                )

            elif action == "achievements":

                print(
                    "Logros"
                )

            elif action == "quit":

                running = False

        elif current_state == "gameplay":

            result = game.handle_event(
                event
            )

            if result == "menu":

                # ESC durante el juego vuelve al menú
                current_state = "menu"


    if current_state == "gameplay":

        game.update(dt)


    screen.fill((0, 0, 0))

    if current_state == "menu":

        menu.draw()

    elif current_state == "gameplay":

        game.draw()


    pygame.display.flip()


pygame.quit()
