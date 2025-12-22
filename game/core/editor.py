import pygame
import random
from game.config import *
from game.ui.components import Button, InputField, Dropdown

CURSOR_TOOL = "CURSOR"


class Editor:
    def __init__(self, level_manager, assets):
        self.lvl_mgr = level_manager
        self.assets = assets

        self.selected_tile = CURSOR_TOOL
        self.show_grid = True

        self.dragging_player = False

        self.name_input = InputField(250, 10, 300, 30, text="")

        self.fb_label_font = pygame.font.SysFont("Arial", 14)
        self.fb_input = InputField(630, 10, 50, 30, text="5")

        self.level_dropdown = Dropdown(
            10, 10, 200, 30,
            options=self.lvl_mgr.get_all_level_names(),
            callback=self._on_level_selected
        )

        btn_y = GAME_HEIGHT + 10
        btn_size = 40
        self.buttons = []

        def make_tool_btn(x, tool_id, text, icon_key=None):
            btn = Button(x, btn_y, btn_size, btn_size, text=text, callback=lambda: self._set_tool(tool_id))
            if icon_key and icon_key in self.assets:
                btn.set_icon(self.assets[icon_key])
            return btn

        # Tools
        # Cursor
        self.cursor_btn = Button(20, btn_y, btn_size, btn_size, text="",
                                 callback=lambda: self._set_tool(CURSOR_TOOL))
        if 'pointer' in self.assets:
            self.cursor_btn.set_icon(self.assets['pointer'])
        self.buttons.append(self.cursor_btn)

        # Tiles
        self.buttons.append(make_tool_btn(70, GROUND, GROUND, GROUND))
        self.buttons.append(make_tool_btn(120, LADDER, LADDER, LADDER))
        self.buttons.append(make_tool_btn(170, COIN, COIN, COIN))

        # Enemy Tool
        self.buttons.append(make_tool_btn(220, TOOL_ENEMY, "E", 'enemy'))

        # Functional buttons
        # New Level
        self.new_lvl_btn = Button(300, btn_y, 80, btn_size, text="New", callback=self._create_level)

        # Gen RND
        self.gen_rnd_btn = Button(390, btn_y, 80, btn_size, text="Gen RND", callback=self._generate_random_level,
                                  color=(100, 100, 180))

        # Delete
        self.del_lvl_btn = Button(480, btn_y, 80, btn_size, text="Delete", callback=self._delete_level,
                                  color=(150, 50, 50))

        # SAVE
        self.save_btn = Button(570, btn_y, 80, btn_size, text="SAVE", callback=self._save_all,
                               color=(50, 150, 50))

        self.buttons.extend([self.new_lvl_btn, self.gen_rnd_btn, self.del_lvl_btn, self.save_btn])

        self._refresh_ui_data()

    def _refresh_ui_data(self):
        self.name_input.text = self.lvl_mgr.get_current_level_name()
        fb_count = self.lvl_mgr.get_current_level_fireballs()
        self.fb_input.text = str(fb_count)
        self.level_dropdown.options = self.lvl_mgr.get_all_level_names()
        self.level_dropdown.selected_index = self.lvl_mgr.current_index

    def _set_tool(self, tile):
        self.selected_tile = tile

    def _on_level_selected(self, index):
        self.lvl_mgr.set_level(index)
        self._refresh_ui_data()

    def _create_level(self):
        self.lvl_mgr.create_new_level()
        self.lvl_mgr.set_player_start(1, 1)
        self._refresh_ui_data()

    def _generate_random_level(self):
        rows = MAP_HEIGHT
        cols = MAP_WIDTH

        grid = [[GROUND for _ in range(cols)] for _ in range(rows)]

        start_c = random.randint(2, cols - 3)
        start_r = random.randint(2, rows - 3)

        floor_points = [(start_r, start_c)]

        grid[start_r][start_c] = BLANK
        # Player start
        self.lvl_mgr.set_player_start(start_r, start_c)

        max_segments = 60
        curr_r, curr_c = start_r, start_c

        for _ in range(max_segments):
            # Weights: 70% Horizontal, 30% Vertical
            move_type = random.choices(['horiz', 'vert'], weights=[70, 30], k=1)[0]

            if move_type == 'horiz':
                direction = random.choice([1, 3])
                length = random.randint(3, 8)
                tile_to_place = BLANK
            else:
                direction = random.choice([0, 2])
                length = random.randint(2, 5)
                tile_to_place = LADDER

            for _ in range(length):
                next_r, next_c = curr_r, curr_c
                if direction == 0:
                    next_r -= 1
                elif direction == 1:
                    next_c += 1
                elif direction == 2:
                    next_r += 1
                elif direction == 3:
                    next_c -= 1

                if 1 <= next_r < rows - 1 and 1 <= next_c < cols - 1:
                    curr_r, curr_c = next_r, next_c

                    if grid[curr_r][curr_c] != LADDER:
                        grid[curr_r][curr_c] = tile_to_place

                    if tile_to_place == LADDER:
                        grid[curr_r][curr_c] = LADDER

                    if grid[curr_r][curr_c] in [BLANK, LADDER]:
                        floor_points.append((curr_r, curr_c))

                    if tile_to_place == BLANK and random.random() < 0.05:
                        if (curr_r, curr_c) != (start_r, start_c):
                            grid[curr_r][curr_c] = COIN
                else:
                    break

            # Branching
            if random.random() < 0.3 or curr_c <= 1 or curr_c >= cols - 2:
                if floor_points:
                    bg_point = random.choice(floor_points)
                    curr_r, curr_c = bg_point

        new_layout = ["".join(row) for row in grid]

        # Enemies
        self.lvl_mgr.get_current_level_enemies().clear()
        enemies_placed = 0
        attempts = 0
        while enemies_placed < 4 and attempts < 200:
            er = random.randint(1, rows - 2)
            ec = random.randint(1, cols - 2)
            tile = new_layout[er][ec]
            dist = abs(er - start_r) + abs(ec - start_c)
            if tile == BLANK and dist > 6:
                if er + 1 < rows and new_layout[er + 1][ec] in [GROUND, LADDER]:
                    self.lvl_mgr.add_enemy(er, ec)
                    enemies_placed += 1
            attempts += 1

        fb_val = 5
        try:
            fb_val = int(self.fb_input.text)
        except:
            pass

        self.lvl_mgr.update_current_level(self.name_input.text, new_layout, fb_val)

    def _delete_level(self):
        if self.lvl_mgr.delete_current_level():
            self._refresh_ui_data()

    def _save_all(self):
        current_layout = self.lvl_mgr.get_current_level_data()
        try:
            fb_val = int(self.fb_input.text)
        except ValueError:
            fb_val = 5
        self.lvl_mgr.update_current_level(self.name_input.text, current_layout, fb_val)
        self.lvl_mgr.save_levels()

    def handle_input(self, event):
        if self.level_dropdown.handle_event(event): return
        if self.name_input.handle_event(event): return
        if self.fb_input.handle_event(event): return

        for btn in self.buttons:
            if btn.handle_event(event): return

        mx, my = pygame.mouse.get_pos()
        col = mx // TILE_SIZE
        row = my // TILE_SIZE

        # Mouse Logic
        p_start = self.lvl_mgr.get_player_start()
        if p_start is None: p_start = {'r': 1, 'c': 1}

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if my < GAME_HEIGHT:
                    # Drag-and-Drop
                    if self.selected_tile == CURSOR_TOOL:
                        if p_start['c'] == col and p_start['r'] == row:
                            self.dragging_player = True
                            return

                    # Other tools
                    if self.selected_tile == TOOL_ENEMY:
                        layout = self.lvl_mgr.get_current_level_data()
                        if 0 <= row < len(layout) and 0 <= col < len(layout[0]):
                            if layout[row][col] == BLANK:
                                self.lvl_mgr.add_enemy(row, col)
                    elif self.selected_tile != CURSOR_TOOL:
                        self._paint_tile(mx, my, self.selected_tile)

            elif event.button == 3:  # Right click
                if my < GAME_HEIGHT:
                    if self.selected_tile == TOOL_ENEMY:
                        self.lvl_mgr.remove_enemy(row, col)
                    else:
                        self._paint_tile(mx, my, BLANK)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging_player = False

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging_player:
                if 0 <= col < MAP_WIDTH and 0 <= row < MAP_HEIGHT:
                    self.lvl_mgr.set_player_start(row, col)

            elif pygame.mouse.get_pressed()[0]:
                if my < GAME_HEIGHT and self.selected_tile not in [CURSOR_TOOL, TOOL_ENEMY]:
                    self._paint_tile(mx, my, self.selected_tile)
                elif my < GAME_HEIGHT and self.selected_tile == BLANK:
                    self._paint_tile(mx, my, BLANK)

            elif pygame.mouse.get_pressed()[2]:
                if my < GAME_HEIGHT and self.selected_tile != TOOL_ENEMY:
                    self._paint_tile(mx, my, BLANK)

    def _paint_tile(self, mx, my, tile_char):
        col = mx // TILE_SIZE
        row = my // TILE_SIZE

        if 0 <= col < MAP_WIDTH and 0 <= row < MAP_HEIGHT:
            p_start = self.lvl_mgr.get_player_start()
            if p_start is None: p_start = {'r': 1, 'c': 1}

            if p_start['c'] == col and p_start['r'] == row:
                return

            layout = self.lvl_mgr.get_current_level_data()
            row_chars = list(layout[row])
            if row_chars[col] == tile_char:
                return
            row_chars[col] = tile_char
            layout[row] = "".join(row_chars)

            if tile_char != BLANK:
                self.lvl_mgr.remove_enemy(row, col)

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons:
            btn.update(mouse_pos)
        self.level_dropdown.update(mouse_pos)
        self.name_input.update(mouse_pos)
        self.fb_input.update(mouse_pos)

    def draw(self, screen):
        # Map
        layout = self.lvl_mgr.get_current_level_data()
        for r, row_str in enumerate(layout):
            for c, char in enumerate(row_str):
                x, y = c * TILE_SIZE, r * TILE_SIZE
                if char in self.assets:
                    screen.blit(self.assets[char], (x, y))

        # Enemies
        enemies = self.lvl_mgr.get_current_level_enemies()
        if enemies and 'enemy' in self.assets:
            enemy_img = self.assets['enemy']
            for e in enemies:
                ex, ey = e['c'] * TILE_SIZE, e['r'] * TILE_SIZE
                screen.blit(enemy_img, (ex, ey))

        # Player start position
        p_start = self.lvl_mgr.get_player_start()
        if p_start is None:
            p_start = {'r': 1, 'c': 1}
        px, py = p_start['c'] * TILE_SIZE, p_start['r'] * TILE_SIZE
        if 'player' in self.assets:
            screen.blit(self.assets['player'], (px, py))
        else:
            pygame.draw.rect(screen, (0, 255, 0), (px, py, TILE_SIZE, TILE_SIZE))
            pygame.draw.rect(screen, (0, 0, 0), (px + 8, py + 8, 4, 4))
            pygame.draw.rect(screen, (0, 0, 0), (px + 20, py + 8, 4, 4))

        # Lighting for dragging
        if self.dragging_player:
            pygame.draw.rect(screen, (0, 255, 0), (px, py, TILE_SIZE, TILE_SIZE), 3)

        # Grid
        if self.show_grid:
            for x in range(0, SCREEN_WIDTH, TILE_SIZE):
                pygame.draw.line(screen, (50, 50, 50), (x, 0), (x, GAME_HEIGHT))
            for y in range(0, GAME_HEIGHT, TILE_SIZE):
                pygame.draw.line(screen, (50, 50, 50), (0, y), (SCREEN_WIDTH, y))

        # UI panel
        pygame.draw.rect(screen, COLOR_PANEL, (0, GAME_HEIGHT, SCREEN_WIDTH, PANEL_HEIGHT))
        self.name_input.draw(screen)
        self.fb_input.draw(screen)

        lbl = self.fb_label_font.render("Ammo:", True, (200, 200, 200))
        screen.blit(lbl, (580, 15))

        for btn in self.buttons:
            is_active = False
            if self.selected_tile == TOOL_ENEMY and getattr(btn, 'text', '') == "E":
                is_active = True
            elif self.selected_tile == getattr(btn, 'text', ''):
                is_active = True
            elif self.selected_tile == CURSOR_TOOL and getattr(btn, 'text', '') == "":
                is_active = True

            if is_active:
                pygame.draw.rect(screen, (200, 200, 0), btn.rect, 3)

            btn.draw(screen)

        self.level_dropdown.draw(screen)