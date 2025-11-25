import pygame
from sys import exit

pygame.init()
screen = pygame.display.set_mode((800, 400))
pygame.display.set_caption('Lode Runner')
clock = pygame.time.Clock()

tile_images = []

ground_surf = pygame.Surface((32, 32))
ground_surf.fill('brown')
ground_rect = ground_surf.get_rect(topleft=(0, 0))


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit()
    screen.blit(ground_surf, ground_rect, )
    pygame.display.update()
    clock.tick(60)