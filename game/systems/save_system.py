import pickle
import os
from typing import Any, Optional
from game.config import SAVES_DIR


class SaveManager:

    @staticmethod
    def ensure_save_dir():
        if not os.path.exists(SAVES_DIR):
            os.makedirs(SAVES_DIR)

    @staticmethod
    def save_game(level_idx: int, data: Any):
        SaveManager.ensure_save_dir()
        filename = os.path.join(SAVES_DIR, f"quicksave_{level_idx}.dat")

        try:
            with open(filename, "wb") as f:
                pickle.dump(data, f)
            print(f"Game saved to {filename}")
        except (OSError, pickle.PicklingError) as e:
            print(f"Save failed: {e}")

    @staticmethod
    def load_game(level_idx: int) -> Optional[Any]:
        filename = os.path.join(SAVES_DIR, f"quicksave_{level_idx}.dat")

        if not os.path.exists(filename):
            return None

        try:
            with open(filename, "rb") as f:
                data = pickle.load(f)
            return data
        except (OSError, pickle.UnpicklingError, EOFError) as e:
            print(f"Load failed: {e}")
            return None