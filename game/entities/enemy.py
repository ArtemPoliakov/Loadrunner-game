import math

import pygame
import os
from collections import deque
from game.entities.entity import Entity
from game.config import *
from game.utils import load_image_asset


class Enemy(Entity):
    def __init__(self, x: float, y: float):
        super().__init__(x, y)

        sprite_path = os.path.join(ASSETS_DIR, 'enemy.png')
        original_img = load_image_asset(sprite_path, scale=(TILE_SIZE, TILE_SIZE))

        self.image_left = original_img
        self.image_right = pygame.transform.flip(original_img, True, False)
        self.image = self.image_left

        self.target_x = x
        self.target_y = y
        self.move_speed = 1.5

    def _get_grid_pos(self):
        cx = self.x + TILE_SIZE / 2
        cy = self.y + TILE_SIZE / 2
        col = int(cx // TILE_SIZE)
        row = int(cy // TILE_SIZE)
        return row, col

    def update(self, dt: float, map_obj, player_pos):
        # Movement logic
        # Move X
        # dx = self.move_speed * math.copysign(1, self.target_x - self.x)
        if self.x < self.target_x:
            self.x = min(self.x + self.move_speed, self.target_x)
            self.image = self.image_right
        elif self.x > self.target_x:
            self.x = max(self.x - self.move_speed, self.target_x)
            self.image = self.image_left

        # Move Y
        if self.y < self.target_y:
            self.y = min(self.y + self.move_speed, self.target_y)
        elif self.y > self.target_y:
            self.y = max(self.y - self.move_speed, self.target_y)

        # Decision-making
        # REFACTORED (Enemy: move: Спробувати прибрати 0.1 (замінити на 0))
        if abs(self.x - self.target_x) == 0 and abs(self.y - self.target_y) == 0:
            curr_r, curr_c = self._get_grid_pos()
            target_r, target_c = player_pos

            # Run BFS to find the next best step
            next_move = self._bfs_next_move(map_obj, (curr_r, curr_c), (target_r, target_c))

            if next_move:
                next_r, next_c = next_move
                self.target_x = float(next_c * TILE_SIZE)
                self.target_y = float(next_r * TILE_SIZE)

    def _bfs_next_move(self, map_obj, start, goal):
        q = deque([start])
        came_from = {start: None}

        found = False

        while q:
            curr = q.popleft()
            if curr == goal:
                found = True
                break

            r, c = curr
            neighbors = []

            current_tile = map_obj.get_tile(r, c)
            tile_below = map_obj.get_tile(r + 1, c)

            is_on_ground = tile_below in [GROUND, LADDER]
            is_on_ladder = current_tile == LADDER

            # Falling
            if not is_on_ground and not is_on_ladder:
                if r < map_obj.height - 1 and map_obj.get_tile(r + 1, c) != GROUND:
                    neighbors.append((r + 1, c))

            # Normal movement
            else:
                # Up
                if is_on_ladder:
                    if r > 0 and map_obj.get_tile(r - 1, c) != GROUND:
                        neighbors.append((r - 1, c))

                # Down
                if r < map_obj.height - 1:
                    t_down = map_obj.get_tile(r + 1, c)
                    if t_down != GROUND:
                        neighbors.append((r + 1, c))

                # Left
                if c > 0:
                    t_left = map_obj.get_tile(r, c - 1)
                    if t_left != GROUND:
                        neighbors.append((r, c - 1))
                # Right
                if c < map_obj.width - 1:
                    t_right = map_obj.get_tile(r, c + 1)
                    if t_right != GROUND:
                        neighbors.append((r, c + 1))

            for neighbor in neighbors:
                if neighbor not in came_from:
                    came_from[neighbor] = curr
                    q.append(neighbor)

        if not found:
            return None

        # Backtracking
        curr = goal
        while came_from[curr] != start:
            curr = came_from[curr]
            if curr is None: return None

        return curr