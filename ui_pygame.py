import pygame
from typing import Tuple, List
from ludo import RING_LEN, HOME_LEN, SAFE_GLOBAL_INDICES

# Window & layout
W, H = 900, 700
CELL = 36
GRID = 15
MARGIN_X = (W - GRID * CELL) // 2
MARGIN_Y = 20

# Colors
WHITE  = (245, 245, 245)
BLACK  = (30, 30, 30)
GRAY   = (180, 180, 180)
FADE   = (230, 230, 230)
RED    = (220, 40, 40)
GREEN  = (40, 180, 80)
YELLOW = (230, 210, 70)
BLUE   = (60, 120, 220)
PANEL  = (250, 250, 255)

SEAT_COLORS = [RED, GREEN, YELLOW, BLUE]

# Buttons
class Button:
    def __init__(self, x, y, w, h, text):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text

    def draw(self, surf, font, bg, fg):
        pygame.draw.rect(surf, bg, self.rect, border_radius=6)
        r = font.render(self.text, True, fg)
        surf.blit(r, (self.rect.x + (self.rect.w - r.get_width())//2,
                      self.rect.y + (self.rect.h - r.get_height())//2))

    def hit(self, pos):
        return self.rect.collidepoint(pos)

# Grid calculations
def _grid_point(cell_x, cell_y):
    return (MARGIN_X + cell_x * CELL + CELL//2, MARGIN_Y + cell_y * CELL + CELL//2)

# Ring squares
RING_GRID = [
    (6,0),(7,0),(8,0),(8,1),(8,2),(8,3),(8,4),(8,5),
    (9,5),(10,5),(11,5),(12,5),(13,5),(14,6),(14,7),(14,8),
    (13,8),(12,8),(11,8),(10,8),(9,8),(8,9),(8,10),(8,11),
    (8,12),(8,13),(7,14),(6,14),(5,14),(5,13),(5,12),(5,11),
    (5,10),(5,9),(4,8),(3,8),(2,8),(1,8),(0,8),(0,7),(0,6),
    (1,6),(2,6),(3,6),(4,6),(5,6),(5,5),(5,4),(5,3),(5,2),(5,1),
    (6,0)
][:52]

# Home paths
HOME_GRID = {
    0: [(6,1),(6,2),(6,3),(6,4),(6,5),(6,6)],
    1: [(13,6),(12,6),(11,6),(10,6),(9,6),(8,6)],
    2: [(8,13),(8,12),(8,11),(8,10),(8,9),(8,8)],
    3: [(1,8),(2,8),(3,8),(4,8),(5,8),(6,8)],
}

# Base definition (top-left of each 6x6 corner)
BASE_TOPLEFT = {0:(0,0), 1:(9,0), 2:(9,9), 3:(0,9)}

# Dice home centers inside each base
BASE_DICE_CENTERS = {0:(3,3), 1:(12,3), 2:(12,12), 3:(3,12)}

# Token slot offsets inside dice home
TOKEN_SLOT_OFFSETS = [(-1.0,-1.0),(0.0,-1.0),(-1.0,0.0),(0.0,0.0)]

def ring_point_global(idx: int):
    gx, gy = RING_GRID[idx % RING_LEN]
    return _grid_point(gx, gy)

def home_point_global(seat: int, idx: int):
    gx, gy = HOME_GRID[seat][idx]
    return _grid_point(gx, gy)

# UI Class
class UI:
    def __init__(self, game):
        self.game = game
        pygame.font.init()
        self.font = pygame.font.SysFont("Arial", 18)
        self.big = pygame.font.SysFont("Arial", 22, bold=True)

        bottom_y = H - 70
        self.btn_roll = Button(40, bottom_y, 120, 40, "Roll Dice")
        self.btn_add  = Button(180, bottom_y, 120, 40, "+ Player")
        self.btn_del  = Button(320, bottom_y, 120, 40, "- Player")
        self.btn_save = Button(460, bottom_y, 120, 40, "Save")
        self.btn_load = Button(600, bottom_y, 120, 40, "Load")
        self.btn_quit = Button(740, bottom_y, 120, 40, "Quit")

        self.highlight = []

    def draw(self, screen):
        screen.fill(WHITE)
        self._draw_board(screen)
        self._draw_ui_panel(screen)
        self._draw_tokens(screen)

    def _draw_board(self, screen):
        # Draw only necessary grid squares (faded background)
        for x in range(GRID):
            for y in range(GRID):
                rect = pygame.Rect(MARGIN_X + x*CELL, MARGIN_Y + y*CELL, CELL, CELL)
                pygame.draw.rect(screen, FADE, rect)
                pygame.draw.rect(screen, BLACK, rect, 1)

        # Draw player bases with grey dice home
        base_coords = [(0,0,6,6,RED), (9,0,6,6,GREEN), (9,9,6,6,YELLOW), (0,9,6,6,BLUE)]
        for bx, by, w, h, color in base_coords:
            rect = pygame.Rect(MARGIN_X + bx*CELL, MARGIN_Y + by*CELL, w*CELL, h*CELL)
            pygame.draw.rect(screen, color, rect)
            dice_size = CELL*3
            dice_rect = pygame.Rect(rect.centerx - dice_size//2,
                                    rect.centery - dice_size//2,
                                    dice_size, dice_size)
            pygame.draw.rect(screen, GRAY, dice_rect, border_radius=8)
            pygame.draw.rect(screen, BLACK, dice_rect, 2, border_radius=8)

        # Draw ring squares
        for idx, (gx, gy) in enumerate(RING_GRID):
            rect = pygame.Rect(MARGIN_X + gx*CELL, MARGIN_Y + gy*CELL, CELL, CELL)
            color = WHITE if idx not in SAFE_GLOBAL_INDICES else (210,210,255)
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, BLACK, rect, 1)

        # Draw home paths
        for seat in range(4):
            for gx, gy in HOME_GRID[seat]:
                rect = pygame.Rect(MARGIN_X + gx*CELL, MARGIN_Y + gy*CELL, CELL, CELL)
                pygame.draw.rect(screen, SEAT_COLORS[seat], rect)
                pygame.draw.rect(screen, BLACK, rect, 1)

        # Draw center star
        cx, cy = MARGIN_X + 7*CELL, MARGIN_Y + 7*CELL
        star_len = CELL*2
        pygame.draw.polygon(screen, RED,    [(cx, cy), (cx-star_len//2, cy-star_len//2), (cx+star_len//2, cy-star_len//2)])
        pygame.draw.polygon(screen, GREEN,  [(cx, cy), (cx+star_len//2, cy-star_len//2), (cx+star_len//2, cy+star_len//2)])
        pygame.draw.polygon(screen, YELLOW, [(cx, cy), (cx+star_len//2, cy+star_len//2), (cx-star_len//2, cy+star_len//2)])
        pygame.draw.polygon(screen, BLUE,   [(cx, cy), (cx-star_len//2, cy+star_len//2), (cx-star_len//2, cy+star_len//2)])

    def _draw_tokens(self, screen):
        for p_idx, p in enumerate(self.game.players):
            color = p.color
            label = self.big.render(p.name, True, color)
            screen.blit(label, (20 + p_idx*200, 8))
            for t in p.tokens:
                pos = self._token_pos_screen(p_idx, t)
                pygame.draw.circle(screen, (100,100,100), (pos[0]+2, pos[1]+2), 11)
                pygame.draw.circle(screen, color, pos, 10)

        # Highlight movable tokens
        self.highlight = []
        if self.game.dice_value is not None:
            pl = self.game.current_player()
            p_idx = self.game.players.index(pl)
            for t in pl.tokens:
                if t.is_movable_with(self.game.dice_value):
                    pos = self._token_pos_screen(p_idx, t)
                    pygame.draw.circle(screen, WHITE, pos, 14, width=3)
                    self.highlight.append((p_idx, t.id))

    def _token_pos_screen(self, p_idx, token):
        if token.state == "base":
            gx, gy = BASE_DICE_CENTERS[p_idx]
            ox, oy = TOKEN_SLOT_OFFSETS[(token.id-1) % 4]
            return _grid_point(gx + ox, gy + oy)
        if token.state == "ring":
            global_idx = (self.game.players[p_idx].entry_global + token.ring_rel) % RING_LEN
            return ring_point_global(global_idx)
        if token.state == "home":
            idx = max(0, min(HOME_LEN-1, token.home_idx))
            return home_point_global(p_idx, idx)
        if token.state == "finished":
            cx = MARGIN_X + 7*CELL
            cy = MARGIN_Y + 7*CELL
            return (cx, cy)
        return (10,10)

    def _draw_ui_panel(self, screen):
        pygame.draw.rect(screen, PANEL, (0, H-100, W, 100))
        self.btn_roll.draw(screen, self.big, BLUE, WHITE)
        self.btn_add.draw(screen, self.font, GRAY, BLACK)
        self.btn_del.draw(screen, self.font, GRAY, BLACK)
        self.btn_save.draw(screen, self.font, GRAY, BLACK)
        self.btn_load.draw(screen, self.font, GRAY, BLACK)
        self.btn_quit.draw(screen, self.font, RED, WHITE)
        status = f"Turn: {self.game.current_player().name}   Dice: {self.game.dice_value if self.game.dice_value else '-'}"
        txt = self.big.render(status, True, BLACK)
        screen.blit(txt, (20, H-140))

    def click(self, pos):
        if self.btn_roll.hit(pos): return "roll"
        if self.btn_add.hit(pos): return "add"
        if self.btn_del.hit(pos): return "del"
        if self.btn_save.hit(pos): return "save"
        if self.btn_load.hit(pos): return "load"
        if self.btn_quit.hit(pos): return "quit"
        for pidx, tid in self.highlight:
            token = next(t for t in self.game.players[pidx].tokens if t.id == tid)
            pos_t = self._token_pos_screen(pidx, token)
            dx, dy = pos[0]-pos_t[0], pos[1]-pos_t[1]
            if dx*dx + dy*dy <= (18**2): return f"move:{tid}"
        return ""
