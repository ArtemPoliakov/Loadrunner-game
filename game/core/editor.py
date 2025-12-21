import pygame
from game.config import *
from game.ui.components import Button, InputField, Dropdown

CURSOR_TOOL = "CURSOR"


class Editor:
    def __init__(self, level_manager, assets):
        self.lvl_mgr = level_manager
        self.assets = assets

        self.selected_tile = CURSOR_TOOL
        self.show_grid = True

        self.name_input = InputField(250, 10, 300, 30, text="")

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

        self.cursor_btn = Button(20, btn_y, btn_size, btn_size, text="",
                                 callback=lambda: self._set_tool(CURSOR_TOOL))
        if 'pointer' in self.assets:
            self.cursor_btn.set_icon(self.assets['pointer'])
        self.buttons.append(self.cursor_btn)

        self.buttons.append(make_tool_btn(70, GROUND, GROUND, GROUND))
        self.buttons.append(make_tool_btn(120, LADDER, LADDER, LADDER))
        self.buttons.append(make_tool_btn(170, COIN, COIN, COIN))

        self.new_lvl_btn = Button(300, btn_y, 100, btn_size, text="New Level", callback=self._create_level)
        self.del_lvl_btn = Button(410, btn_y, 100, btn_size, text="Delete Lvl", callback=self._delete_level,
                                  color=(150, 50, 50))
        self.save_btn = Button(SCREEN_WIDTH - 200, btn_y, 100, btn_size, text="SAVE", callback=self._save_all,
                               color=(50, 150, 50))

        self.buttons.extend([self.new_lvl_btn, self.del_lvl_btn, self.save_btn])

        self._refresh_ui_data()

    def _refresh_ui_data(self):
        self.name_input.text = self.lvl_mgr.get_current_level_name()
        self.level_dropdown.options = self.lvl_mgr.get_all_level_names()
        self.level_dropdown.selected_index = self.lvl_mgr.current_index

    def _set_tool(self, tile):
        self.selected_tile = tile

    def _on_level_selected(self, index):
        self.lvl_mgr.set_level(index)
        self._refresh_ui_data()

    def _create_level(self):
        self.lvl_mgr.create_new_level()
        self._refresh_ui_data()

    def _delete_level(self):
        if self.lvl_mgr.delete_current_level():
            self._refresh_ui_data()

    def _save_all(self):
        current_layout = self.lvl_mgr.get_current_level_data()
        self.lvl_mgr.update_current_level(self.name_input.text, current_layout)
        self.lvl_mgr.save_levels()

    def handle_input(self, event):
        if self.level_dropdown.handle_event(event): return
        if self.name_input.handle_event(event): return
        for btn in self.buttons:
            if btn.handle_event(event): return

        mx, my = pygame.mouse.get_pos()
        mouse_buttons = pygame.mouse.get_pressed()

        if mouse_buttons[0] and my < GAME_HEIGHT:
            if self.selected_tile != CURSOR_TOOL:
                self._paint_tile(mx, my, self.selected_tile)

        if mouse_buttons[2] and my < GAME_HEIGHT:
            if self.selected_tile != CURSOR_TOOL:
                self._paint_tile(mx, my, BLANK)

    def _paint_tile(self, mx, my, tile_char):
        col = mx // TILE_SIZE
        row = my // TILE_SIZE

        if 0 <= col < MAP_WIDTH and 0 <= row < MAP_HEIGHT:
            layout = self.lvl_mgr.get_current_level_data()
            row_chars = list(layout[row])
            if row_chars[col] == tile_char:
                return
            row_chars[col] = tile_char
            layout[row] = "".join(row_chars)

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons:
            btn.update(mouse_pos)
        self.level_dropdown.update(mouse_pos)
        self.name_input.update(mouse_pos)

    def draw(self, screen):
        layout = self.lvl_mgr.get_current_level_data()
        for r, row_str in enumerate(layout):
            for c, char in enumerate(row_str):
                x, y = c * TILE_SIZE, r * TILE_SIZE
                if char in self.assets:
                    screen.blit(self.assets[char], (x, y))

        if self.show_grid:
            for x in range(0, SCREEN_WIDTH, TILE_SIZE):
                pygame.draw.line(screen, (50, 50, 50), (x, 0), (x, GAME_HEIGHT))
            for y in range(0, GAME_HEIGHT, TILE_SIZE):
                pygame.draw.line(screen, (50, 50, 50), (0, y), (SCREEN_WIDTH, y))

        pygame.draw.rect(screen, COLOR_PANEL, (0, GAME_HEIGHT, SCREEN_WIDTH, PANEL_HEIGHT))
        self.name_input.draw(screen)

        for btn in self.buttons:
            if btn.text == "Mouse" and self.selected_tile == CURSOR_TOOL:
                pygame.draw.rect(screen, (200, 200, 0), btn.rect, 3)
            elif btn.text == self.selected_tile:
                pygame.draw.rect(screen, (200, 200, 0), btn.rect, 3)
            btn.draw(screen)

        self.level_dropdown.draw(screen)