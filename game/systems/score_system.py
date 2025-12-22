import os
from typing import Dict, List, Optional
from game.config import SCORES_FILE


class ScoreManager:

    def __init__(self):
        self._scores: Dict[int, List[int]] = self._load_scores()

    def _load_scores(self) -> Dict[int, List[int]]:
        scores = {}
        if not os.path.exists(SCORES_FILE):
            return scores

        try:
            with open(SCORES_FILE, "r") as f:
                lines = f.readlines()
                clean_lines = [line.strip() for line in lines if line.strip()]

                for line in clean_lines:
                    try:
                        lvl_str, time_str = line.split(":")
                        lvl_idx = int(lvl_str)
                        time_ms = int(time_str)

                        if lvl_idx not in scores:
                            scores[lvl_idx] = []
                        scores[lvl_idx].append(time_ms)
                    except ValueError:
                        print(f"Skipping corrupt line: {line}")
                        continue
        except OSError as e:
            print(f"Error reading scores: {e}")

        return scores

    def save_score(self, level_idx: int, time_ms: int):
        if level_idx not in self._scores:
            self._scores[level_idx] = []
        self._scores[level_idx].append(time_ms)

        try:
            with open(SCORES_FILE, "a") as f:
                f.write(f"{level_idx}:{time_ms}\n")
        except OSError as e:
            print(f"Error saving score: {e}")

    def get_best_time(self, level_idx: int) -> Optional[int]:
        if level_idx not in self._scores or not self._scores[level_idx]:
            return None
        return min(self._scores[level_idx])

    def get_top_scores(self, level_idx: int, limit: int = 3) -> List[int]:
        if level_idx not in self._scores:
            return []
        return sorted(self._scores[level_idx])[:limit]