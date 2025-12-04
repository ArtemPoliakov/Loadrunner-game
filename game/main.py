import pygame
from sys import exit
from game.utils import draw_map, get_cur_tile, get_tile_at, load_level_from_strings, load_all_levels_from_file
import os

# CONSTANTS
TILE_SIZE = 24
MAP_WIDTH = 35
MAP_HEIGHT = 20

SCREEN_WIDTH = 840
GAME_HEIGHT = 480
PANEL_HEIGHT = 60
TOTAL_HEIGHT = GAME_HEIGHT + PANEL_HEIGHT

BLANK = "_"
GROUND = "#"
LADDER = "^"
COIN = "$"

FALL_SPEED = 2.0
ANIMATION_SPEED = 3.0
HOLE_DURATION = 4000.0
JUMP_HANG_TIME = 250.0
SCORES_FILE = "scores.txt"

# BEST TIME UI CONSTANTS
POPUP_WIDTH = 200
POPUP_HEIGHT = 160
POPUP_X = (SCREEN_WIDTH - POPUP_WIDTH) // 2
POPUP_Y = (GAME_HEIGHT - POPUP_HEIGHT) // 2
RECORD_TEXT_X = SCREEN_WIDTH - 210
RECORD_TEXT_Y = GAME_HEIGHT + 18

LEVEL_BLUEPRINTS = load_all_levels_from_file("levels.json")

# INIT
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, TOTAL_HEIGHT))
pygame.display.set_caption('Lode Runner')
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 20)
ui_font = pygame.font.SysFont("Consolas", 28, bold=True)
pause_font = pygame.font.SysFont("Consolas", 60, bold=True)  # Шрифт для напису PAUSED

# ASSETS
tile_images = {}


def load_tile(path, colorkey=None):
    img = pygame.image.load(path).convert_alpha()
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    if colorkey: img.set_colorkey(colorkey)
    return img


tile_images[LADDER] = load_tile('assets/ladder.gif')
tile_images[GROUND] = load_tile('assets/ground.png')
tile_images[COIN] = load_tile('assets/coin.jpg', (255, 255, 255))
tile_images[BLANK] = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
sprite_img = load_tile('assets/sprite.png')
try:
    background = pygame.transform.scale(pygame.image.load('assets/cave_bg.png').convert(), (SCREEN_WIDTH, GAME_HEIGHT))
except FileNotFoundError:
    background = pygame.Surface((SCREEN_WIDTH, GAME_HEIGHT))
    background.fill((20, 20, 40))

# GLOBAL STATE
current_level_idx = 0
current_level_data = []
sprite_x_pos = 0.0
sprite_y_pos = 0.0

target_x = 0.0
target_y = 0.0
is_animating = False
is_jumping = False
jump_peak_time = None

coins_collected = 0
total_coins = 0
start_ticks = 0
game_finished = False
win_time = 0
start_time = 0
active_holes = []

# --- Score & Pause State ---
high_scores = {}
show_scores_popup = False
is_paused = False  # Чи активна пауза зараз
pause_start_time = 0  # Коли почалась поточна пауза
total_pause_duration = 0  # Скільки часу сумарно ми простояли на паузі


# HELPER FUNCTIONS

def load_scores():
    scores = {}
    if not os.path.exists(SCORES_FILE):
        return scores

    with open(SCORES_FILE, "r") as f:
        lines = f.readlines()
        # [LIST COMPREHENSION]
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
                continue
    return scores


def save_score(level_idx, time_ms):
    if level_idx not in high_scores:
        high_scores[level_idx] = []
    high_scores[level_idx].append(time_ms)

    with open(SCORES_FILE, "a") as f:
        f.write(f"{level_idx}:{time_ms}\n")


def get_best_time(level_idx):
    if level_idx not in high_scores or not high_scores[level_idx]:
        return None
    return min(high_scores[level_idx])


def get_top_scores(level_idx):
    if level_idx not in high_scores or not high_scores[level_idx]:
        return []

    times = sorted(high_scores[level_idx])
    # [SLICES]
    return times[:3]


def is_aligned_to_grid(y_pos):
    return abs(y_pos % TILE_SIZE) < 0.1


def is_on_solid_ground(current_data, x_pos, y_pos):
    row, col = get_cur_tile(x_pos, y_pos, TILE_SIZE)
    tile_below = get_tile_at(current_data, row + 1, col)
    return is_aligned_to_grid(y_pos) and tile_below in [GROUND, LADDER]


def is_on_ladder_tile(current_data, x_pos, y_pos):
    row, col = get_cur_tile(x_pos, y_pos, TILE_SIZE)
    return get_tile_at(current_data, row, col) == LADDER


# STATE FUNCTIONS

def reset_level(level_idx):
    global start_time, total_coins
    temp_total_coins = 0

    def init_level_state():
        global current_level_data, sprite_x_pos, sprite_y_pos, target_x, target_y, is_animating, is_jumping
        global coins_collected, start_ticks, game_finished, active_holes, jump_peak_time
        global is_paused, total_pause_duration, pause_start_time

        # Безпечне завантаження
        safe_idx = level_idx if 0 <= level_idx < len(LEVEL_BLUEPRINTS) else 0
        current_level_data = load_level_from_strings(LEVEL_BLUEPRINTS[safe_idx])

        start_x = TILE_SIZE * 2
        start_y = TILE_SIZE * (MAP_HEIGHT - 2)

        sprite_x_pos = float(start_x)
        sprite_y_pos = float(start_y)
        target_x = sprite_x_pos
        target_y = sprite_y_pos

        is_animating = False
        is_jumping = False
        jump_peak_time = None

        coins_collected = 0

        # Скидання пауз
        is_paused = False
        total_pause_duration = 0
        pause_start_time = 0

        nonlocal temp_total_coins
        temp_total_coins = sum(map(lambda level_row: level_row.count(COIN), current_level_data))

        start_ticks = pygame.time.get_ticks()
        game_finished = False
        active_holes = []

    init_level_state()
    total_coins = temp_total_coins

    screen.blit(background, (0, 0))
    draw_map(screen, current_level_data, tile_images, TILE_SIZE, show_start=True)

    start_time = pygame.time.get_ticks()


# CORE LOGIC

# INIT SCORES
high_scores = load_scores()

reset_level(current_level_idx)
prev_btn_rect = pygame.Rect(20, GAME_HEIGHT + 15, 30, 30)
next_btn_rect = pygame.Rect(180, GAME_HEIGHT + 15, 30, 30)

while True:
    current_time = pygame.time.get_ticks()

    # EVENT HANDLING
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

        # --- KEYBOARD (ESC - Pause) ---
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if show_scores_popup:
                # Якщо відкрито вікно рекордів, закриваємо його і знімаємо паузу
                show_scores_popup = False
                is_paused = False
                if pause_start_time != 0:
                    total_pause_duration += current_time - pause_start_time
                    pause_start_time = 0
            else:
                # Якщо просто гра, перемикаємо паузу
                is_paused = not is_paused
                if is_paused:
                    pause_start_time = current_time
                else:
                    if pause_start_time != 0:
                        total_pause_duration += current_time - pause_start_time
                        pause_start_time = 0

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos

            # --- 1. ЛОГІКА МОДАЛЬНОГО ВІКНА (Пріоритетна) ---
            if show_scores_popup:
                close_btn_rect = pygame.Rect(POPUP_X + POPUP_WIDTH - 30, POPUP_Y + 5, 25, 25)
                if close_btn_rect.collidepoint(mouse_pos):
                    show_scores_popup = False
                    is_paused = False  # Знімаємо паузу при закритті
                    if pause_start_time != 0:
                        total_pause_duration += current_time - pause_start_time
                        pause_start_time = 0

            # --- 2. ОСНОВНА ГРА (Тільки якщо вікно закрите) ---
            else:
                # А) Перевірка кліку на текст рекорду
                record_rect = pygame.Rect(RECORD_TEXT_X, RECORD_TEXT_Y, 150, 30)

                if record_rect.collidepoint(mouse_pos):
                    show_scores_popup = True
                    # Автоматично ставимо на паузу
                    if not is_paused:
                        is_paused = True
                        pause_start_time = current_time

                # Б) Кнопки навігації
                elif prev_btn_rect.collidepoint(mouse_pos):
                    if current_level_idx > 0: current_level_idx -= 1; reset_level(current_level_idx)
                elif next_btn_rect.collidepoint(mouse_pos):
                    if current_level_idx < len(LEVEL_BLUEPRINTS) - 1: current_level_idx += 1; reset_level(
                        current_level_idx)

                # В) Логіка копання (Тільки якщо не на паузі)
                elif not is_paused and event.button == 1 and mouse_pos[1] < GAME_HEIGHT and not game_finished:
                    mx, my = mouse_pos
                    click_col, click_row = mx // TILE_SIZE, my // TILE_SIZE
                    p_row, p_col = get_cur_tile(sprite_x_pos + TILE_SIZE / 2, sprite_y_pos, TILE_SIZE)

                    if abs(click_row - p_row) <= 1 and abs(click_col - p_col) <= 1:
                        if get_tile_at(current_level_data, click_row, click_col) == GROUND:
                            current_level_data[click_row][click_col] = BLANK
                            active_holes.append({'row': click_row, 'col': click_col, 'time': current_time})

        # KEYBOARD INPUT (WASD / QE) - Тільки якщо не на паузі
        if not is_paused and not show_scores_popup:
            if event.type == pygame.KEYDOWN and not is_animating and jump_peak_time is None:
                row, col = get_cur_tile(sprite_x_pos, sprite_y_pos, TILE_SIZE)
                curr_tile = get_tile_at(current_level_data, row, col)

                dx, dy = 0, 0

                on_stable_surface = is_on_solid_ground(current_level_data, sprite_x_pos, sprite_y_pos)
                on_ladder = is_on_ladder_tile(current_level_data, sprite_x_pos, sprite_y_pos)

                # LADDER MOVEMENT (W / S)
                if curr_tile == LADDER or (
                        on_stable_surface and get_tile_at(current_level_data, row + 1, col) == LADDER):
                    if event.key == pygame.K_s:
                        tile_below = get_tile_at(current_level_data, row + 1, col)
                        if tile_below != GROUND: dy = TILE_SIZE
                    elif event.key == pygame.K_w:
                        tile_above = get_tile_at(current_level_data, row - 1, col)
                        if row > 0 and tile_above != GROUND: dy = -TILE_SIZE

                # HORIZONTAL MOVEMENT (A / D)
                if (on_stable_surface or on_ladder) and (event.key == pygame.K_a or event.key == pygame.K_d):
                    new_col = col + (-1 if event.key == pygame.K_a else 1)
                    tile_next = get_tile_at(current_level_data, row, new_col)

                    if (0 <= new_col < MAP_WIDTH) and tile_next != GROUND:
                        dx = (new_col - col) * TILE_SIZE

                # JUMP & JUMP-ROLL LOGIC
                elif on_stable_surface:
                    if event.key == pygame.K_w:
                        tile_above = get_tile_at(current_level_data, row - 1, col)
                        if tile_above != GROUND:
                            dy = -TILE_SIZE
                            is_jumping = True

                    elif event.key == pygame.K_q or event.key == pygame.K_e:
                        target_col = col + (-1 if event.key == pygame.K_q else 1)
                        tile_above = get_tile_at(current_level_data, row - 1, col)
                        tile_target = get_tile_at(current_level_data, row - 1, target_col)

                        if tile_above != GROUND and tile_target != GROUND and target_col >= 0 and target_col < MAP_WIDTH:
                            dx = (target_col - col) * TILE_SIZE
                            dy = -TILE_SIZE
                            is_jumping = True

                if dx != 0 or dy != 0:
                    target_x = sprite_x_pos + dx
                    target_y = sprite_y_pos + dy
                    is_animating = True

            elif event.type == pygame.KEYDOWN and jump_peak_time is not None and event.key == pygame.K_w:
                row, col = get_cur_tile(sprite_x_pos, sprite_y_pos, TILE_SIZE)
                tile_above = get_tile_at(current_level_data, row - 1, col)

                if tile_above == LADDER:
                    jump_peak_time = None
                    target_y -= TILE_SIZE
                    is_animating = True

    # 2. PHYSICS & UPDATES

    # [PAUSE] Виконуємо фізику тільки якщо не на паузі
    if not is_paused:

        # Hole Regen
        for hole in active_holes[:]:
            if current_time - hole['time'] > HOLE_DURATION:
                current_level_data[hole['row']][hole['col']] = GROUND
                active_holes.remove(hole)

        # Smooth Movement Logic
        if is_animating:
            if sprite_x_pos < target_x:
                sprite_x_pos = min(sprite_x_pos + ANIMATION_SPEED, target_x)
            elif sprite_x_pos > target_x:
                sprite_x_pos = max(sprite_x_pos - ANIMATION_SPEED, target_x)
            if sprite_y_pos < target_y:
                sprite_y_pos = min(sprite_y_pos + ANIMATION_SPEED, target_y)
            elif sprite_y_pos > target_y:
                sprite_y_pos = max(sprite_y_pos - ANIMATION_SPEED, target_y)

            if sprite_x_pos == target_x and sprite_y_pos == target_y:
                is_animating = False
                if is_jumping:
                    is_jumping = False
                    jump_peak_time = current_time

                    # Jump Hang Logic
        elif jump_peak_time is not None:
            if current_time - jump_peak_time > JUMP_HANG_TIME:
                jump_peak_time = None

        # Gravity
        else:
            row, col = get_cur_tile(sprite_x_pos, sprite_y_pos, TILE_SIZE)
            curr_tile = get_tile_at(current_level_data, row, col)
            tile_below = get_tile_at(current_level_data, row + 1, col)

            is_aligned = is_aligned_to_grid(sprite_y_pos)

            if is_aligned:
                should_fall = (curr_tile != LADDER) and (tile_below != GROUND) and (tile_below != LADDER)
                if should_fall:
                    sprite_y_pos += FALL_SPEED
                    target_y = sprite_y_pos
                    target_x = sprite_x_pos
            else:
                sprite_y_pos += FALL_SPEED
                target_y = sprite_y_pos
                curr_pixel_offset = sprite_y_pos % TILE_SIZE
                if curr_pixel_offset < FALL_SPEED * 2:
                    next_row = int(sprite_y_pos // TILE_SIZE)
                    row_below_tile = get_tile_at(current_level_data, next_row, int(sprite_x_pos // TILE_SIZE))
                    if row_below_tile in [GROUND, LADDER]:
                        sprite_y_pos = float(next_row * TILE_SIZE)
                        target_y = sprite_y_pos

        # Looting
        center_row, center_col = get_cur_tile(sprite_x_pos, sprite_y_pos - (TILE_SIZE / 2), TILE_SIZE)
        if get_tile_at(current_level_data, center_row, center_col) == COIN:
            current_level_data[center_row][center_col] = BLANK
            coins_collected += 1
            if coins_collected >= total_coins and not game_finished:
                game_finished = True
                # Віднімаємо час пауз
                win_time = current_time - start_ticks - total_pause_duration
                save_score(current_level_idx, win_time)

    # UI Updates

    # Розрахунок часу з урахуванням паузи
    if game_finished:
        display_time_ms = win_time
    else:
        # Якщо пауза - час "заморожено" на момент початку паузи
        if is_paused:
            display_time_ms = pause_start_time - start_ticks - total_pause_duration
        else:
            display_time_ms = current_time - start_ticks - total_pause_duration

    display_time_ms = max(0, display_time_ms)
    time_str = f"Time: {display_time_ms // 1000}s" + (" (WIN!)" if game_finished else "")

    # DRAWING
    screen.blit(background, (0, 0))
    draw_map(screen, current_level_data, tile_images, TILE_SIZE)

    sprite_rect = sprite_img.get_rect(bottomleft=(int(sprite_x_pos), int(sprite_y_pos)))
    screen.blit(sprite_img, sprite_rect)

    # UI Panel
    pygame.draw.rect(screen, (30, 30, 30), (0, GAME_HEIGHT, SCREEN_WIDTH, PANEL_HEIGHT))

    prev_color = (255, 255, 255) if current_level_idx > 0 else (100, 100, 100)
    next_color = (255, 255, 255) if current_level_idx < len(LEVEL_BLUEPRINTS) - 1 else (100, 100, 100)
    screen.blit(ui_font.render("<", True, prev_color), (prev_btn_rect.x + 5, prev_btn_rect.y))
    screen.blit(ui_font.render(f"Level {current_level_idx + 1}", True, (255, 255, 255)), (60, GAME_HEIGHT + 15))
    screen.blit(ui_font.render(">", True, next_color), (next_btn_rect.x + 5, next_btn_rect.y))
    screen.blit(font.render(f"Coins: {coins_collected}/{total_coins}", True, (255, 215, 0)),
                (SCREEN_WIDTH - 300, GAME_HEIGHT + 18))
    screen.blit(font.render(time_str, True, (200, 200, 200)), (SCREEN_WIDTH - 125, GAME_HEIGHT + 18))

    # [DISPLAY RECORD]
    best_time = get_best_time(current_level_idx)
    record_str = "Best: --"
    if best_time:
        record_str = f"Best: {best_time // 1000}s"

    score_color = (255, 255, 100) if not show_scores_popup else (100, 100, 100)
    screen.blit(font.render(record_str, True, score_color), (RECORD_TEXT_X, RECORD_TEXT_Y))

    # [PAUSE OVERLAY] Якщо пауза є, але вікна немає - малюємо "PAUSED"
    if is_paused and not show_scores_popup:
        overlay = pygame.Surface((SCREEN_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Напівпрозорий чорний
        screen.blit(overlay, (0, 0))

        pause_surf = pause_font.render("PAUSED", True, (255, 255, 255))
        pause_rect = pause_surf.get_rect(center=(SCREEN_WIDTH // 2, GAME_HEIGHT // 2))
        screen.blit(pause_surf, pause_rect)

    # [POPUP WINDOW]
    if show_scores_popup:
        pygame.draw.rect(screen, (0, 0, 0), (POPUP_X + 5, POPUP_Y + 5, POPUP_WIDTH, POPUP_HEIGHT))
        pygame.draw.rect(screen, (50, 50, 70), (POPUP_X, POPUP_Y, POPUP_WIDTH, POPUP_HEIGHT))
        pygame.draw.rect(screen, (200, 200, 200), (POPUP_X, POPUP_Y, POPUP_WIDTH, POPUP_HEIGHT), 2)

        title_surf = font.render(f"Top 3 (Lvl {current_level_idx + 1})", True, (255, 215, 0))
        screen.blit(title_surf, (POPUP_X + 20, POPUP_Y + 10))

        close_rect = pygame.Rect(POPUP_X + POPUP_WIDTH - 30, POPUP_Y + 5, 25, 25)
        pygame.draw.rect(screen, (200, 50, 50), close_rect)
        screen.blit(font.render("X", True, (255, 255, 255)), (close_rect.x + 6, close_rect.y - 2))

        top_list = get_top_scores(current_level_idx)

        if not top_list:
            screen.blit(font.render("No records yet", True, (150, 150, 150)), (POPUP_X + 30, POPUP_Y + 60))
        else:
            for i, score in enumerate(top_list):
                line = f"{i + 1}. {score // 1000}s"
                screen.blit(font.render(line, True, (255, 255, 255)), (POPUP_X + 40, POPUP_Y + 50 + i * 30))

    pygame.display.update()
    clock.tick(60)