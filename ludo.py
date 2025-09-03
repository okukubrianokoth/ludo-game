# ludo.py
import random
import json
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Tuple

# Constants
TOKENS_PER_PLAYER = 4
RING_LEN = 52
HOME_LEN = 6
# Safe squares (global ring indices) — classic pattern
SAFE_GLOBAL_INDICES = {0, 8, 13, 21, 26, 34, 39, 47}

# Player seat definitions: (name, color RGB, entry global index)
SEATS = [
    ("Red",    (220, 40, 40),   0),
    ("Green",  (40, 180, 80),  13),
    ("Yellow", (230, 210, 70), 26),
    ("Blue",   (60, 120, 220), 39),
]

@dataclass
class Token:
    id: int
    state: str = "base"    # base, ring, home, finished
    ring_rel: int = -1     # 0..51 relative to player's entry when on ring
    home_idx: int = -1     # 0..5 when in home path

    def is_movable_with(self, dice: int) -> bool:
        if self.state == "finished":
            return False
        if self.state == "base":
            return dice == 6
        if self.state == "ring":
            # If stays on ring
            if self.ring_rel + dice < RING_LEN:
                return True
            # would enter home
            steps_into_home = self.ring_rel + dice - (RING_LEN - 1) - 1
            return steps_into_home <= (HOME_LEN - 1)
        if self.state == "home":
            return (self.home_idx + dice) <= (HOME_LEN - 1)
        return False

@dataclass
class Player:
    name: str
    color: Tuple[int,int,int]
    entry_global: int
    tokens: List[Token] = field(default_factory=list)

    def all_finished(self) -> bool:
        return all(t.state == "finished" for t in self.tokens)

    def to_dict(self):
        return {
            "name": self.name,
            "color": self.color,
            "entry_global": self.entry_global,
            "tokens": [asdict(t) for t in self.tokens],
        }

    @staticmethod
    def from_dict(d):
        p = Player(d["name"], tuple(d["color"]), d["entry_global"])
        p.tokens = [Token(**tok) for tok in d["tokens"]]
        return p

class LudoGame:
    def __init__(self, players_count: int = 2):
        self.players: List[Player] = []
        self.current_turn: int = 0
        self.dice_value: Optional[int] = None
        self.awaiting_move: bool = False
        self.reset_players(players_count)

    # ----------------- Player/Token CRUD -----------------
    def reset_players(self, count: int):
        self.players.clear()
        count = max(2, min(4, count))
        for i in range(count):
            name, color, entry = SEATS[i]
            p = Player(name, color, entry)
            p.tokens = [Token(id=j+1) for j in range(TOKENS_PER_PLAYER)]
            self.players.append(p)
        self.current_turn = 0
        self.dice_value = None
        self.awaiting_move = False

    def add_player(self) -> bool:
        if len(self.players) >= 4:
            return False
        idx = len(self.players)
        name, color, entry = SEATS[idx]
        p = Player(name, color, entry)
        p.tokens = [Token(id=j+1) for j in range(TOKENS_PER_PLAYER)]
        self.players.append(p)
        return True

    def remove_player(self) -> bool:
        if len(self.players) <= 2:
            return False
        self.players.pop()
        self.current_turn %= len(self.players)
        return True

    def save(self, path="savegame.json"):
        data = {
            "current_turn": self.current_turn,
            "dice_value": self.dice_value,
            "players": [p.to_dict() for p in self.players],
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self, path="savegame.json") -> bool:
        try:
            with open(path, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            return False
        self.current_turn = data.get("current_turn", 0)
        self.dice_value = data.get("dice_value", None)
        self.players = [Player.from_dict(pd) for pd in data["players"]]
        if len(self.players) < 2:
            self.reset_players(2)
        self.awaiting_move = self.dice_value is not None
        return True

    # ----------------- Gameplay -----------------
    def roll_dice(self) -> int:
        self.dice_value = random.randint(1, 6)
        self.awaiting_move = True
        return self.dice_value

    def current_player(self) -> Player:
        return self.players[self.current_turn]

    def global_index_of(self, player: Player, token: Token) -> Optional[int]:
        if token.state != "ring":
            return None
        return (player.entry_global + token.ring_rel) % RING_LEN

    def can_move_any(self, player: Player, dice: int) -> bool:
        return any(t.is_movable_with(dice) for t in player.tokens)

    def move_token(self, player_idx: int, token_id: int) -> bool:
        """Apply current dice_value to the token of player `player_idx` with id token_id.
           Returns True if moved, False otherwise.
        """
        if self.dice_value is None:
            return False
        player = self.players[player_idx]
        token = next((t for t in player.tokens if t.id == token_id), None)
        if token is None or not token.is_movable_with(self.dice_value):
            return False

        dice = self.dice_value

        # Perform movement
        if token.state == "base":
            token.state = "ring"
            token.ring_rel = 0
        elif token.state == "ring":
            new_rel = token.ring_rel + dice
            if new_rel < RING_LEN:
                token.ring_rel = new_rel
            else:
                # enter home
                steps_into_home = new_rel - (RING_LEN - 1) - 1
                token.state = "home"
                token.ring_rel = -1
                token.home_idx = steps_into_home
        elif token.state == "home":
            token.home_idx += dice

        # check finish (exact on last home index)
        if token.state == "home" and token.home_idx == (HOME_LEN - 1):
            token.state = "finished"
            token.home_idx = -1

        # handle capture if on ring and not safe
        self._handle_capture(player_idx, token)

        extra_turn = (dice == 6)
        self.dice_value = None
        self.awaiting_move = False

        if not extra_turn:
            self._advance_turn()
        # else keep same current_turn

        return True

    def _handle_capture(self, mover_idx: int, moved_token: Token):
        if moved_token.state != "ring":
            return
        mover = self.players[mover_idx]
        dest_global = self.global_index_of(mover, moved_token)
        if dest_global in SAFE_GLOBAL_INDICES:
            return
        for idx, p in enumerate(self.players):
            if idx == mover_idx:
                continue
            for t in p.tokens:
                if t.state == "ring" and self.global_index_of(p, t) == dest_global:
                    # capture
                    t.state = "base"
                    t.ring_rel = -1
                    t.home_idx = -1

    def _advance_turn(self):
        self.current_turn = (self.current_turn + 1) % len(self.players)

    def winner_index(self) -> Optional[int]:
        for i, p in enumerate(self.players):
            if p.all_finished():
                return i
        return None
