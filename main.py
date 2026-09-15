import pygame

from states.main_menu import MainMenu

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


running = True

while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:

            running = False

        action = menu.handle_event(
            event
        )

        if action == "new_game":

            print(
                "Nueva partida"
            )

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


    menu.draw()

    pygame.display.flip()

    clock.tick(60)


pygame.quit()