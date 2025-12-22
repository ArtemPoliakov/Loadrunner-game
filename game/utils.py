import time
from functools import wraps

import pygame
import os

def log_execution(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"[LOG] {func.__name__} executed in {end - start:.4f} seconds")
        return result

    return wrapper


def load_image_asset(path, scale=None, auto_crop=True):
    if not os.path.exists(path):
        print(f"Error: Image {path} not found!")
        surf = pygame.Surface((24, 24))
        surf.fill((255, 0, 255))
        return surf

    try:
        image = pygame.image.load(path).convert_alpha()
    except pygame.error as e:
        print(f"Pygame Error loading {path}: {e}")
        return pygame.Surface((24, 24))

    color_at_00 = image.get_at((0, 0))
    if color_at_00[3] != 0:
        image.set_colorkey(color_at_00)
        final_image = pygame.Surface(image.get_size(), pygame.SRCALPHA)
        final_image.blit(image, (0, 0))
        image = final_image

    if auto_crop:
        mask = pygame.mask.from_surface(image)
        rects = mask.get_bounding_rects()
        if rects:
            bbox = rects[0].unionall(rects[1:])
            if bbox.width > 0 and bbox.height > 0:
                image = image.subsurface(bbox).copy()

    if scale:
        image = pygame.transform.scale(image, scale)

    return image