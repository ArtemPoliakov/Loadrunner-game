import math
import pygame
import json

BLANK = "_"
GROUND = "#"
LADDER = "^"
COIN = "$"


def draw_map(screen, map_data, surface_dict, tile_size, /, *, show_start=False):
    for i in range(len(map_data)):
        row = map_data[i]
        for j in range(len(row)):
            tile_char = row[j]
            if tile_char == BLANK or tile_char not in surface_dict:
                continue

            cell = surface_dict[tile_char]
            cell_rect = cell.get_rect(topleft=(tile_size * j, tile_size * i))
            screen.blit(cell, cell_rect)
    else:
        if show_start:
            screen_w, screen_h = screen.get_size()
            center_x, center_y = screen_w // 2, screen_h // 2

            panel_bg_color = (30, 30, 30)
            border_color = (255, 215, 0)
            text_color = (255, 255, 255)

            panel_w, panel_h = 200, 80
            panel_rect = pygame.Rect(0, 0, panel_w, panel_h)
            panel_rect.center = (center_x, center_y)

            pygame.draw.rect(screen, panel_bg_color, panel_rect)
            pygame.draw.rect(screen, border_color, panel_rect, 3)

            font = pygame.font.SysFont("Consolas", 40, bold=True)
            text_surf = font.render("START", True, text_color)
            text_rect = text_surf.get_rect(center=panel_rect.center)

            screen.blit(text_surf, text_rect)

            pygame.display.flip()
            pygame.time.delay(1000)

def get_cur_tile(x_pos, y_pos, tile_size):
    row = math.floor((y_pos - 1) / tile_size)
    col = math.floor(x_pos / tile_size)
    return row, col


def get_tile_at(map_data, row, col):
    if row < 0 or row >= len(map_data):
        return GROUND
    current_row = map_data[row]
    if not current_row or col < 0 or col >= len(current_row):
        return GROUND
    return current_row[col]


def load_level_from_strings(level_blueprint):
    level_data = []
    for row_str in level_blueprint:
        level_data.append(list(row_str))
    return level_data


def load_all_levels_from_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            blueprints = json.load(f)

        if not isinstance(blueprints, list):
            print(f"ПОМИЛКА: JSON файл має містити список рівнів, отримано {type(blueprints)}")
            return []

        return blueprints

    except FileNotFoundError:
        print(f"ПОМИЛКА: Файл рівнів '{filepath}' не знайдено!")
        return []
    except json.JSONDecodeError as e:
        print(f"ПОМИЛКА: Не вдалося розпарсити JSON: {e}")
        return []