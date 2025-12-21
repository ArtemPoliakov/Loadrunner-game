import pygame
from abc import ABC, abstractmethod


class Entity(ABC, pygame.sprite.Sprite):

    def __init__(self, x: float, y: float, image_path: str = None):
        super().__init__()
        self._x = x
        self._y = y

        if image_path:
            self.image = pygame.image.load(image_path).convert_alpha()
        else:
            self.image = pygame.Surface((24, 24))
            self.image.fill((255, 0, 0))

        self.rect = self.image.get_rect(topleft=(x, y))

    @property
    def x(self) -> float:
        return self._x

    @x.setter
    def x(self, value: float):
        self._x = value
        self.rect.x = int(value)

    @property
    def y(self) -> float:
        return self._y

    @y.setter
    def y(self, value: float):
        self._y = value
        self.rect.y = int(value)

    @abstractmethod
    def update(self, dt: float, map_obj):
        pass

    def draw(self, screen: pygame.Surface):
        screen.blit(self.image, self.rect)