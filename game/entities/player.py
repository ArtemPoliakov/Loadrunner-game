import pygame
import os
from typing import Optional
from game.entities.entity import Entity
from game.config import *
from game.entities.map import GameMap
from game.utils import load_image_asset
from game.enums import Direction, DIR_OFFSETS

class Player(Entity):
    def __init__(self, x: float, y: float):
        super().__init__(x, y)

        sprite_path = os.path.join(ASSETS_DIR, 'sprite.png')
        original_img = load_image_asset(sprite_path, scale=(TILE_SIZE, TILE_SIZE))

        self.image_right = original_img
        self.image_left = pygame.transform.flip(original_img, True, False)

        self.image = self.image_right
        self.facing_right = True

        self.target_x = x
        self.target_y = y
        self.is_animating = False
        self.is_jumping = False
        self.jump_peak_time: Optional[int] = None

        self._coins_collected = 0

    @property
    def coins(self) -> int:
        return self._coins_collected

    # REFACTORED (property для row, col)
    @property
    def row(self) -> int:
        return int((self.y + TILE_SIZE / 2) // TILE_SIZE)

    @property
    def col(self) -> int:
        return int((self.x + TILE_SIZE / 2) // TILE_SIZE)

    def add_coin(self):
        self._coins_collected += 1

    def reset_movement(self):
        self.target_x = self.x
        self.target_y = self.y
        self.is_animating = False
        self.is_jumping = False
        self.jump_peak_time = None

    def _is_aligned_y(self) -> bool:
        return abs(self.y % TILE_SIZE) < 0.1

    # REFACTORED (property для row, col)

    def _on_solid_ground(self, map_obj: GameMap) -> bool:
        row, col = self.row, self.col
        tile_below = map_obj.get_tile(row + 1, col)
        return self._is_aligned_y() and tile_below in [GROUND, LADDER]

    def _on_ladder(self, map_obj: GameMap) -> bool:
        row, col = self.row, self.col
        current_tile = map_obj.get_tile(row, col)
        return current_tile == LADDER


    # REFACTORED (Player.handleinput → dict, dict, dx, dy (rewrite))
    def handle_input(self, keys, map_obj: GameMap):
        if self.is_animating or self.jump_peak_time is not None:
            return

        move_dir = None
        row, col = self.row, self.col

        curr_tile = map_obj.get_tile(row, col)
        tile_below = map_obj.get_tile(row + 1, col)
        tile_above = map_obj.get_tile(row - 1, col)

        on_stable = self._on_solid_ground(map_obj)
        on_ladder = self._on_ladder(map_obj)

        if keys[pygame.K_a] or keys[pygame.K_q]:
            if self.facing_right:
                self.facing_right = False
                self.image = self.image_left
        elif keys[pygame.K_d] or keys[pygame.K_e]:
            if not self.facing_right:
                self.facing_right = True
                self.image = self.image_right

        can_climb = (curr_tile == LADDER) or (on_stable and tile_below == LADDER)

        if can_climb:
            if keys[pygame.K_s]:
                if tile_below != GROUND:
                    move_dir = Direction.DOWN
            elif keys[pygame.K_w]:
                if row > 0 and tile_above != GROUND:
                    move_dir = Direction.UP

        if (on_stable or on_ladder) and (keys[pygame.K_a] or keys[pygame.K_d]):
            try_dir = Direction.LEFT if keys[pygame.K_a] else Direction.RIGHT
            dr, dc = DIR_OFFSETS[try_dir]
            new_col = col + dc
            tile_next = map_obj.get_tile(row, new_col)

            if 0 <= new_col < map_obj.width and tile_next != GROUND:
                if move_dir is None:
                    move_dir = try_dir

        elif on_stable and move_dir is None:
            if keys[pygame.K_w] and tile_above != GROUND:
                move_dir = Direction.UP
                self.is_jumping = True

            elif keys[pygame.K_q] or keys[pygame.K_e]:
                try_dir = Direction.UP_LEFT if keys[pygame.K_q] else Direction.UP_RIGHT
                dr, dc = DIR_OFFSETS[try_dir]
                target_c = col + dc
                tile_targ = map_obj.get_tile(row - 1, target_c)

                if tile_above != GROUND and tile_targ != GROUND and 0 <= target_c < map_obj.width:
                    move_dir = try_dir
                    self.is_jumping = True

        if move_dir is not None:
            dr, dc = DIR_OFFSETS[move_dir]
            self.target_x = self.x + dc * TILE_SIZE
            self.target_y = self.y + dr * TILE_SIZE
            self.is_animating = True

    def update(self, dt: float, map_obj: GameMap):
        current_time = pygame.time.get_ticks()

        if self.is_animating:
            if self.x < self.target_x:
                self.x = min(self.x + ANIMATION_SPEED, self.target_x)
            elif self.x > self.target_x:
                self.x = max(self.x - ANIMATION_SPEED, self.target_x)

            if self.y < self.target_y:
                self.y = min(self.y + ANIMATION_SPEED, self.target_y)
            elif self.y > self.target_y:
                self.y = max(self.y - ANIMATION_SPEED, self.target_y)

            if self.x == self.target_x and self.y == self.target_y:
                self.is_animating = False
                if self.is_jumping:
                    self.is_jumping = False
                    self.jump_peak_time = current_time

        elif self.jump_peak_time is not None:
            if current_time - self.jump_peak_time > JUMP_HANG_TIME:
                self.jump_peak_time = None
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w]:
                row, col = self.row, self.col
                if map_obj.get_tile(row - 1, col) == LADDER:
                    self.jump_peak_time = None
                    self.target_y -= TILE_SIZE
                    self.is_animating = True

        else:
            if self._is_aligned_y():
                row, col = self.row, self.col
                curr_tile = map_obj.get_tile(row, col)
                tile_below = map_obj.get_tile(row + 1, col)

                should_fall = (curr_tile != LADDER) and \
                              (tile_below != GROUND) and \
                              (tile_below != LADDER)

                if should_fall:
                    self.y += FALL_SPEED
                    self.target_y = self.y
                    self.target_x = self.x
            else:
                self.y += FALL_SPEED
                self.target_y = self.y

                if (self.y % TILE_SIZE) < FALL_SPEED * 2:
                    next_row = int(self.y // TILE_SIZE)
                    col = int(self.x // TILE_SIZE)
                    tile_below = map_obj.get_tile(next_row, col)

                    if tile_below in [GROUND, LADDER]:
                        self.y = float(next_row * TILE_SIZE)
                        self.target_y = self.y

        cx, cy = self.x + TILE_SIZE / 2, self.y + TILE_SIZE / 2
        row, col = int((cy - TILE_SIZE / 2) // TILE_SIZE), int(cx // TILE_SIZE)

        if map_obj.get_tile(row, col) == COIN:
            map_obj.set_tile(row, col, BLANK)
            self.add_coin()