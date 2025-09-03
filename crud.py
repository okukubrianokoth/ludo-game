# crud.py
import json, os

SAVE_FILE = "savegame.json"
VALID_COLORS = ["red", "green", "yellow", "blue"]  # map to seats 0..3 in this order

def _empty():
    return {"players": []}

def _load():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            try:
                return json.load(f)
            except Exception:
                return _empty()
    return _empty()

def _save(data):
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def read_players():
    return _load().get("players", [])

def reset_players():
    _save(_empty())

def create_player(name: str, color: str):
    color = color.lower().strip()
    data = _load()
    players = data.get("players", [])
    if len(players) >= 4:
        raise ValueError("Maximum of 4 players reached.")
    if color not in VALID_COLORS:
        raise ValueError(f"Color must be one of {VALID_COLORS}")
    if any(p["color"] == color for p in players):
        raise ValueError(f"Color '{color}' is already taken.")
    players.append({"name": name.strip() or color.title(), "color": color})
    data["players"] = players
    _save(data)

def update_player(name: str, *, new_name: str = None, new_color: str = None):
    data = _load()
    players = data.get("players", [])
    idx = next((i for i,p in enumerate(players) if p["name"] == name), None)
    if idx is None:
        raise ValueError("Player not found.")
    if new_color:
        new_color = new_color.lower().strip()
        if new_color not in VALID_COLORS:
            raise ValueError(f"Color must be one of {VALID_COLORS}")
        if any(p["color"] == new_color for i,p in enumerate(players) if i != idx):
            raise ValueError(f"Color '{new_color}' is already taken.")
        players[idx]["color"] = new_color
    if new_name:
        players[idx]["name"] = new_name.strip()
    data["players"] = players
    _save(data)

def delete_player(name: str):
    data = _load()
    before = len(data.get("players", []))
    data["players"] = [p for p in data.get("players", []) if p["name"] != name]
    if len(data["players"]) == before:
        raise ValueError("Player not found.")
    _save(data)
