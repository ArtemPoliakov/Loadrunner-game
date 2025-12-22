import pygame
from typing import List, Tuple, Generator
from game.config import *


class GameMap:
    def __init__(self, layout: List[str]):
        self._data = [list(row) for row in layout]
        self.holes = []
        self._initial_coins = sum(row.count(COIN) for row in self._data)

    @property
    def width(self) -> int:
        return len(self._data[0]) if self._data else 0

    @property
    def height(self) -> int:
        return len(self._data)

    @property
    def total_coins(self) -> int:
        return self._initial_coins

    def __getitem__(self, index: int) -> List[str]:
        return self._data[index]


    def get_tile(self, row: int, col: int) -> str:
        if 0 <= row < self.height and 0 <= col < self.width:
            return self._data[row][col]
        return GROUND

    def set_tile(self, row: int, col: int, value: str):
        if 0 <= row < self.height and 0 <= col < self.width:
            self._data[row][col] = value

    def iter_tiles(self, tile_type: str) -> Generator[Tuple[int, int], None, None]:
        for r in range(self.height):
            for c in range(self.width):
                if self._data[r][c] == tile_type:
                    yield r, c

    def dig_hole(self, row: int, col: int):
        if self.get_tile(row, col) == GROUND:
            self.set_tile(row, col, BLANK)
            self.holes.append({'r': row, 'c': col, 'time': pygame.time.get_ticks()})

    def update_holes(self):
        current_time = pygame.time.get_ticks()
        for hole in self.holes[:]:
            if current_time - hole['time'] > HOLE_DURATION:
                self.set_tile(hole['r'], hole['c'], GROUND)
                self.holes.remove(hole)

    def draw(self, screen: pygame.Surface, asset_dict: dict):
        for r in range(self.height):
            for c in range(self.width):
                tile_char = self._data[r][c]
                if tile_char != BLANK and tile_char in asset_dict:
                    img = asset_dict[tile_char]
                    screen.blit(img, (c * TILE_SIZE, r * TILE_SIZE))

    @staticmethod
    def get_grid_pos(x: float, y: float) -> Tuple[int, int]:
        col = int(x // TILE_SIZE)
        row = int((y - 1) // TILE_SIZE)
        return row, col