import pygame
import sys
from ludo import LudoGame
from ui_pygame import UI, W, H

def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Ludo — Full Rules")
    clock = pygame.time.Clock()

    game = LudoGame(players_count=2)
    ui = UI(game)

    running = True
    winner_announced = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                act = ui.click(event.pos)
                if act == "quit":
                    running = False
                elif act == "add":
                    game.add_player()
                elif act == "del":
                    game.remove_player()
                elif act == "save":
                    game.save()
                elif act == "load":
                    if not game.load():
                        print("No savefile found.")
                elif act == "roll":
                    if not game.awaiting_move:
                        dice = game.roll_dice()
                        if not game.can_move_any(game.current_player(), dice):
                            game.dice_value = None
                            game.awaiting_move = False
                            game._advance_turn()
                elif act.startswith("move:"):
                    tid = int(act.split(":")[1])
                    if game.dice_value is not None:
                        game.move_token(game.current_turn, tid)

        ui.draw(screen)
        pygame.display.flip()

        widx = game.winner_index()
        if widx is not None and not winner_announced:
            print(f"{game.players[widx].name} wins!")
            winner_announced = True

        clock.tick(30)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
