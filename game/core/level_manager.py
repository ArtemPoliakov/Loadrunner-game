import json
import os
from typing import List, Dict, Any
from game.config import LEVELS_FILE
from game.utils import log_execution


class LevelManager:
    def __init__(self):
        self.levels: List[Dict[str, Any]] = self._load_levels()
        self.current_index = 0

    @log_execution
    def _load_levels(self) -> List[Dict[str, Any]]:
        if not os.path.exists(LEVELS_FILE):
            print("Level file not found! Creating default.")
            return self._create_default_file()

        try:
            with open(LEVELS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data and isinstance(data[0], list):
                    print("Detected old level format. Converting...")
                    new_data = []
                    for i, layout in enumerate(data):
                        new_data.append({
                            "id": i,
                            "name": f"Level {i + 1}",
                            "layout": layout
                        })
                    return new_data
                return data
        except json.JSONDecodeError:
            print("Error decoding levels JSON")
            return []

    def _create_default_file(self):
        return []

    def save_levels(self):
        try:
            with open(LEVELS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.levels, f, indent=2)
            print("Levels saved successfully.")
        except IOError as e:
            print(f"Error saving levels: {e}")


    def get_current_level_data(self) -> List[str]:
        if 0 <= self.current_index < len(self.levels):
            return self.levels[self.current_index]["layout"]
        return []

    def get_current_level_name(self) -> str:
        if 0 <= self.current_index < len(self.levels):
            return self.levels[self.current_index].get("name", f"Level {self.current_index + 1}")
        return "Unknown Level"

    def get_all_level_names(self) -> List[str]:
        return [lvl.get("name", f"Level {i + 1}") for i, lvl in enumerate(self.levels)]


    def create_new_level(self):
        from game.config import MAP_WIDTH, MAP_HEIGHT, GROUND, BLANK
        layout = []
        for r in range(MAP_HEIGHT):
            if r == 0 or r == MAP_HEIGHT - 1:
                row = GROUND * MAP_WIDTH
            else:
                row = GROUND + (BLANK * (MAP_WIDTH - 2)) + GROUND
            layout.append(row)

        new_level = {
            "id": len(self.levels),
            "name": "New Level",
            "layout": layout
        }
        self.levels.append(new_level)
        self.current_index = len(self.levels) - 1

    def update_current_level(self, name: str, layout: List[str]):
        if 0 <= self.current_index < len(self.levels):
            self.levels[self.current_index]["name"] = name
            self.levels[self.current_index]["layout"] = layout
            self.save_levels()

    def delete_current_level(self):
        if 0 <= self.current_index < len(self.levels) and len(self.levels) > 1:
            self.levels.pop(self.current_index)
            if self.current_index >= len(self.levels):
                self.current_index = len(self.levels) - 1
            self.save_levels()
            return True
        return False


    def next_level(self):
        if self.current_index < len(self.levels) - 1:
            self.current_index += 1
            return True
        return False

    def prev_level(self):
        if self.current_index > 0:
            self.current_index -= 1
            return True
        return False

    def set_level(self, index: int):
        if 0 <= index < len(self.levels):
            self.current_index = index