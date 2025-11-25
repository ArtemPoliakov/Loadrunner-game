import pygame
from sys import exit
from game.utils import draw_map, get_cur_tile, get_tile_at, load_level_from_strings

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

# LEVEL BLUEPRINTS
LEVEL_1 = [
    "___________________________________",
    "___________________________________",
    "___________________________________",
    "_______$___________________$_______",
    "######^####_____________####^######",
    "______^_____________________^______",
    "______^_______$_____$_______^______",
    "______^____#######^#######__^______",
    "______^___________^_________^______",
    "______#########___^___#########____",
    "__________________^________________",
    "__$_______________^______________$_",
    "#####^############^############^###",
    "_____^____________^____________^___",
    "_____^____$_______^_______$____^___",
    "_____^__#####_____^_____#####__^___",
    "_____^____________^____________^___",
    "_____^____________^____________^___",
    "##################^################",
    "###################################"
]
LEVEL_2 = [
    "___________________________________",
    "_________________$_________________",
    "__###^######___#####___######^###__",
    "_____^_____#_____^_____#_____^_____",
    "_____^_____#___________#_____^_____",
    "__$__^__$__#____$_$____#__$__^__$__",
    "#####^####_#_#########_#_####^#####",
    "_____^_____#_____^_____#_____^_____",
    "___^_^___________^___________^_____",
    "###^#####________^________#########",
    "________#________^________#________",
    "________#___$____^____$___#________",
    "__#######_#####__^__#####_#######__",
    "__#______________^______________#__",
    "__#______________^______________#__",
    "__#___$__________^__________$___#__",
    "__#######________^________#######__",
    "________#________^________#________",
    "#################^#################",
    "###################################"
]
LEVEL_3 = [
    "___________________________________",
    "___$___________________________$___",
    "#######_____________________#######",
    "______#_____________________#______",
    "______#______$_______$______#______",
    "______#____#####___#####____#______",
    "______#____#___________#____#______",
    "______#____#___$___$___#____#______",
    "______######___#####___######______",
    "___________#___#___#___#___________",
    "___________#___#___#___#___________",
    "___________#####_^_#####___________",
    "_________________^_________________",
    "__$______________^______________$__",
    "#####____________^____________#####",
    "____#____________^____________#____",
    "____#_____$______^______$_____#____",
    "____###########__^__###########____",
    "_________________^_________________",
    "###################################"
]

LEVEL_TEST = ["___________________________________",
              "___________________________________",
              "#######_____________________#######",
              "______#_____________________#______",
              "______#_____________________#______",
              "______#____#####___#####____#______",
              "______#____#___________#____#______",
              "______#____#___________#____#______",
              "______######___#####___######______",
              "___________#___#___#___#___________",
              "___________#___#___#___#___________",
              "___________#####_^_#####___________",
              "_________________^_________________",
              "_________________^_________________",
              "#####____________^____________#####",
              "____#____________^____________#____",
              "____#____________^____________#____",
              "____###########__^__###########____",
              "_________________$_________________",
              "###################################"]
LEVEL_BLUEPRINTS = [LEVEL_1, LEVEL_2, LEVEL_3, LEVEL_TEST]

# INIT
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, TOTAL_HEIGHT))
pygame.display.set_caption('Lode Runner')
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 20)
ui_font = pygame.font.SysFont("Consolas", 28, bold=True)

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
background = pygame.transform.scale(pygame.image.load('assets/cave_bg.png').convert(), (SCREEN_WIDTH, GAME_HEIGHT))

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


# HELPER FUNCTIONS

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
    # For example
    temp_total_coins = 0

    def init_level_state():
        global current_level_data, sprite_x_pos, sprite_y_pos, target_x, target_y, is_animating, is_jumping
        global coins_collected, start_ticks, game_finished, active_holes, jump_peak_time

        current_level_data = load_level_from_strings(LEVEL_BLUEPRINTS[level_idx])

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

        # For example
        nonlocal temp_total_coins
        temp_total_coins = sum(map(lambda level_row: level_row.count(COIN), current_level_data))

        start_ticks = pygame.time.get_ticks()
        game_finished = False
        active_holes = []

    init_level_state()

    # For example
    total_coins = temp_total_coins

    # SHOW START SCREEN
    screen.blit(background, (0, 0))
    draw_map(screen, current_level_data, tile_images, TILE_SIZE, show_start=True)

    start_time = pygame.time.get_ticks()


# CORE LOGIC

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

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos

            # UI Logic
            if prev_btn_rect.collidepoint(mouse_pos):
                if current_level_idx > 0: current_level_idx -= 1; reset_level(current_level_idx)
            elif next_btn_rect.collidepoint(mouse_pos):
                if current_level_idx < len(LEVEL_BLUEPRINTS) - 1: current_level_idx += 1; reset_level(current_level_idx)

            # Digging Logic
            elif event.button == 1 and mouse_pos[1] < GAME_HEIGHT and not game_finished:
                mx, my = mouse_pos
                click_col, click_row = mx // TILE_SIZE, my // TILE_SIZE
                p_row, p_col = get_cur_tile(sprite_x_pos + TILE_SIZE / 2, sprite_y_pos, TILE_SIZE)

                if abs(click_row - p_row) <= 1 and abs(click_col - p_col) <= 1:
                    if get_tile_at(current_level_data, click_row, click_col) == GROUND:
                        current_level_data[click_row][click_col] = BLANK
                        active_holes.append({'row': click_row, 'col': click_col, 'time': current_time})

        # KEYBOARD INPUT (WASD / QE)

        # Рух дозволений, якщо ми НЕ рухаємось і не висимо
        if event.type == pygame.KEYDOWN and not is_animating and jump_peak_time is None:
            row, col = get_cur_tile(sprite_x_pos, sprite_y_pos, TILE_SIZE)
            curr_tile = get_tile_at(current_level_data, row, col)

            dx, dy = 0, 0

            # Прапорець для визначення, чи гравець стоїть на стабільній поверхні, щоб стрибати
            on_stable_surface = is_on_solid_ground(current_level_data, sprite_x_pos, sprite_y_pos)
            on_ladder = is_on_ladder_tile(current_level_data, sprite_x_pos, sprite_y_pos)

            # LADDER MOVEMENT (W / S)
            # Якщо ми на клітинці драбини або під нами драбина, можемо рухатися вертикально.
            if curr_tile == LADDER or (on_stable_surface and get_tile_at(current_level_data, row + 1, col) == LADDER):
                if event.key == pygame.K_s:
                    tile_below = get_tile_at(current_level_data, row + 1, col)
                    if tile_below != GROUND: dy = TILE_SIZE
                elif event.key == pygame.K_w:
                    tile_above = get_tile_at(current_level_data, row - 1, col)
                    if row > 0 and tile_above != GROUND: dy = -TILE_SIZE

            # HORIZONTAL MOVEMENT (A / D)
            # Дозволено, якщо на опорі (on_stable_surface) АБО на драбині (on_ladder)
            if (on_stable_surface or on_ladder) and (event.key == pygame.K_a or event.key == pygame.K_d):

                new_col = col + (-1 if event.key == pygame.K_a else 1)
                tile_next = get_tile_at(current_level_data, row, new_col)

                # Перевірка на стіну та межі
                if  (0 <= new_col < MAP_WIDTH) and tile_next != GROUND:
                    dx = (new_col - col) * TILE_SIZE

            # JUMP & JUMP-ROLL LOGIC
            # Ці рухи вимагають опори під ногами
            elif on_stable_surface:

                # Vertical Jump (W)
                if event.key == pygame.K_w:
                    tile_above = get_tile_at(current_level_data, row - 1, col)
                    if tile_above != GROUND:
                        dy = -TILE_SIZE
                        is_jumping = True

                # Jump-Roll (Q / E)
                elif event.key == pygame.K_q or event.key == pygame.K_e:
                    target_col = col + (-1 if event.key == pygame.K_q else 1)
                    tile_above = get_tile_at(current_level_data, row - 1, col)
                    tile_target = get_tile_at(current_level_data, row - 1, target_col)

                    if tile_above != GROUND and tile_target != GROUND and target_col >= 0 and target_col < MAP_WIDTH:
                        dx = (target_col - col) * TILE_SIZE
                        dy = -TILE_SIZE
                        is_jumping = True

            # Start Animation
            if dx != 0 or dy != 0:
                target_x = sprite_x_pos + dx
                target_y = sprite_y_pos + dy
                is_animating = True

        # LADDER GRAB LOGIC (during Jump Hang Time)
        elif event.type == pygame.KEYDOWN and jump_peak_time is not None and event.key == pygame.K_w:
            row, col = get_cur_tile(sprite_x_pos, sprite_y_pos, TILE_SIZE)
            tile_above = get_tile_at(current_level_data, row - 1, col)

            if tile_above == LADDER:
                jump_peak_time = None
                target_y -= TILE_SIZE
                is_animating = True

    # 2. PHYSICS & UPDATES

    # Hole Regen
    for hole in active_holes[:]:
        if current_time - hole['time'] > HOLE_DURATION:
            current_level_data[hole['row']][hole['col']] = GROUND
            active_holes.remove(hole)

    # Smooth Movement Logic
    if is_animating:
        # Move X
        if sprite_x_pos < target_x:
            sprite_x_pos = min(sprite_x_pos + ANIMATION_SPEED, target_x)
        elif sprite_x_pos > target_x:
            sprite_x_pos = max(sprite_x_pos - ANIMATION_SPEED, target_x)
        # Move Y
        if sprite_y_pos < target_y:
            sprite_y_pos = min(sprite_y_pos + ANIMATION_SPEED, target_y)
        elif sprite_y_pos > target_y:
            sprite_y_pos = max(sprite_y_pos - ANIMATION_SPEED, target_y)

        if sprite_x_pos == target_x and sprite_y_pos == target_y:
            is_animating = False
            if is_jumping:
                is_jumping = False
                jump_peak_time = current_time  # Start hang time

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
            # Freefall alignment
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
        if coins_collected >= total_coins: game_finished = True; win_time = current_time - start_time

    # UI Updates
    time_str = f"Time: {str(win_time // 1000) + "s" + " (WIN!)" if game_finished else(current_time - start_ticks) // 1000}"

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
    screen.blit(font.render(time_str, True, (200, 200, 200)), (SCREEN_WIDTH - 140, GAME_HEIGHT + 18))

    pygame.display.update()
    clock.tick(60)