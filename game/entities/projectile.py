import pygame
import math
from game.config import *
from game.entities.entity import Entity
from game.entities.map import GameMap


class Explosion(Entity):
    def __init__(self, x: float, y: float, image: pygame.Surface):
        super().__init__(x, y)
        self.image = image
        self.rect = self.image.get_rect(center=(int(x), int(y)))
        self._x = self.rect.x
        self._y = self.rect.y
        self.frame_index = 0
        self.is_finished = False

    def update(self, dt: float, map_obj, enemies: list):
        step = dt if dt > 0 else 16.6
        self.frame_index += step

        if self.frame_index > EXPLOSION_DURATION:
            self.is_finished = True
            return

        kill_radius_px = EXPLOSION_RADIUS_TILES * TILE_SIZE
        cx, cy = self.rect.center

        for enemy in enemies[:]:
            ex = enemy.x + TILE_SIZE / 2
            ey = enemy.y + TILE_SIZE / 2
            dist = math.hypot(ex - cx, ey - cy)

            if dist <= kill_radius_px:
                if enemy in enemies:
                    enemies.remove(enemy)
                    print("Enemy destroyed by explosion!")

    def draw(self, screen: pygame.Surface):
        screen.blit(self.image, self.rect)


class Fireball(Entity):
    def __init__(self, x: float, y: float, direction: int, image: pygame.Surface, explosion_img: pygame.Surface):
        adjusted_y = y + (TILE_SIZE * 0.6) - (image.get_height() / 2)

        super().__init__(x, adjusted_y)
        self.direction = direction
        self.image = image
        if direction < 0:
            self.image = pygame.transform.flip(image, True, False)

        self.rect = self.image.get_rect(topleft=(self.x, self.y))

        self.explosion_img = explosion_img
        self.should_explode = False
        self.explosion_instance = None

    def update(self, dt: float, map_obj: GameMap, enemies: list):
        self.x += FIREBALL_SPEED * self.direction

        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

        if self.x < 0 or self.x > SCREEN_WIDTH:
            self.should_explode = True

        cx = self.x + self.rect.width / 2
        cy = self.y + self.rect.height / 2
        row, col = map_obj.get_grid_pos(cx, cy)
        tile = map_obj.get_tile(row, col)
        if tile == GROUND:
            self.should_explode = True

        for enemy in enemies:
            if self.rect.colliderect(enemy.rect):
                self.should_explode = True
                break

        if self.should_explode:
            center_x = self.x + self.rect.width / 2
            center_y = self.y + self.rect.height / 2
            self.explosion_instance = Explosion(center_x, center_y, self.explosion_img)

    def draw(self, screen: pygame.Surface):
        screen.blit(self.image, self.rect)