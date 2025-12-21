import pygame
import sys
import os
from game.config import *
from game.entities import Player, GameMap
from game.core.level_manager import LevelManager
from game.systems import ScoreManager, SaveManager
from game.ui import UIRenderer
from game.ui.components import Button, Dropdown
from game.core.editor import Editor


class GameApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, TOTAL_HEIGHT))
        pygame.display.set_caption("Lode Runner OOP")

        try:
            icon = pygame.image.load(os.path.join(ASSETS_DIR, 'sprite.png'))
            pygame.display.set_icon(icon)
        except:
            pass

        self.clock = pygame.time.Clock()

        self.level_manager = LevelManager()
        self.score_manager = ScoreManager()
        self.ui = UIRenderer()
        self.save_manager = SaveManager()

        self._load_assets()

        self.is_paused = False
        self.show_popup = False
        self.game_finished = False

        self.start_ticks = 0
        self.pause_start = 0
        self.total_pause_duration = 0
        self.win_time = 0

        self.system_message = ""
        self.system_message_time = 0

        self.map: GameMap = None
        self.player: Player = None

        self.is_editor_mode = False
        self.editor = Editor(self.level_manager, self.assets)


        self.game_dropdown = Dropdown(
            60, GAME_HEIGHT + 15, 200, 30,
            options=self.level_manager.get_all_level_names(),
            callback=self._on_game_level_selected,
            direction='up'
        )
        self.game_dropdown.selected_index = self.level_manager.current_index


        self.mode_btn = Button(
            SCREEN_WIDTH - 90, GAME_HEIGHT + 15, 80, 30,
            text="EDIT",
            callback=self.toggle_mode,
            color=(100, 100, 200)
        )

        self.reset_level()


    def _on_game_level_selected(self, index):
        self.level_manager.set_level(index)
        self.reset_level()

    def toggle_mode(self):
        self.is_editor_mode = not self.is_editor_mode
        self.mode_btn.text = "PLAY" if self.is_editor_mode else "EDIT"
        self.mode_btn.base_color = (200, 100, 100) if self.is_editor_mode else (100, 100, 200)

        if not self.is_editor_mode:
            self.reset_level()
            self.game_dropdown.options = self.level_manager.get_all_level_names()
            self.game_dropdown.selected_index = self.level_manager.current_index
        else:
            self.editor._refresh_ui_data()


    def _load_assets(self):
        def load_img(filename, color_key=None):
            path = os.path.join(ASSETS_DIR, filename)
            if not os.path.exists(path):
                surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
                surf.fill((128, 0, 128))
                return surf
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
            if color_key: img.set_colorkey(color_key)
            return img

        self.assets = {
            LADDER: load_img('ladder.gif'),
            GROUND: load_img('ground.png'),
            COIN: load_img('coin.jpg', (255, 255, 255)),
        }
        pointer_path = os.path.join(ASSETS_DIR, 'pointer.png')
        if os.path.exists(pointer_path):
            self.assets['pointer'] = pygame.image.load(pointer_path).convert_alpha()
        else:
            print(f"WARNING: pointer.png not found at {pointer_path}")
            surf = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.circle(surf, (200, 200, 200), (16, 16), 14, 2)
            self.assets['pointer'] = surf
        try:
            bg_path = os.path.join(ASSETS_DIR, 'cave_bg.png')
            self.background = pygame.transform.scale(
                pygame.image.load(bg_path).convert(), (SCREEN_WIDTH, GAME_HEIGHT)
            )
        except Exception:
            self.background = pygame.Surface((SCREEN_WIDTH, GAME_HEIGHT))
            self.background.fill(COLOR_BG)

    def reset_level(self):
        lvl_data = self.level_manager.get_current_level_data()
        self.map = GameMap(lvl_data)
        start_x = TILE_SIZE * 2
        start_y = TILE_SIZE * (MAP_HEIGHT - 2)
        self.player = Player(start_x, start_y)
        self.game_finished = False
        self.is_paused = False
        self.show_popup = False
        self.start_ticks = pygame.time.get_ticks()
        self.total_pause_duration = 0
        self.win_time = 0
        self.system_message = ""
        self.game_dropdown.selected_index = self.level_manager.current_index

    def show_message(self, text):
        self.system_message = text
        self.system_message_time = pygame.time.get_ticks()

    def _get_elapsed_time(self):
        if self.game_finished: return self.win_time
        if self.is_paused: return self.pause_start - self.start_ticks - self.total_pause_duration
        return pygame.time.get_ticks() - self.start_ticks - self.total_pause_duration

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if self.mode_btn.handle_event(event): continue

            if self.is_editor_mode:
                self.editor.handle_input(event)

            else:
                if self.game_dropdown.handle_event(event): continue

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.show_popup:
                            self.show_popup = False
                            self.is_paused = False
                            self._resume_timer()
                        else:
                            self.is_paused = not self.is_paused
                            if self.is_paused:
                                self.pause_start = pygame.time.get_ticks()
                            else:
                                self._resume_timer()
                    elif event.key == pygame.K_F1 and not self.is_paused and not self.game_finished:
                        elapsed = self._get_elapsed_time()
                        data = (self.player.x, self.player.y, self.player.coins, elapsed, self.map._data,
                                self.map.holes)
                        self.save_manager.save_game(self.level_manager.current_index, data)
                        self.show_message(f"Lvl {self.level_manager.current_index + 1} Saved")
                    elif event.key == pygame.K_F2:
                        data = self.save_manager.load_game(self.level_manager.current_index)
                        if data:
                            try:
                                p_x, p_y, p_coins, saved_elapsed, saved_map_data, saved_holes = data
                                self.player.x = p_x;
                                self.player.y = p_y;
                                self.player.reset_movement();
                                self.player._coins_collected = p_coins
                                self.map._data = saved_map_data;
                                self.map.holes = []
                                current_ticks = pygame.time.get_ticks()
                                for h in saved_holes: h['time'] = current_ticks; self.map.holes.append(h)
                                self.start_ticks = pygame.time.get_ticks() - saved_elapsed
                                self.total_pause_duration = 0;
                                self.is_paused = False;
                                self.game_finished = False;
                                self.win_time = 0
                                self.show_message(f"Lvl {self.level_manager.current_index + 1} Loaded")
                            except ValueError:
                                self.show_message("Save Error!")

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    if self.show_popup:
                        if self.ui.nav_rects['close'].collidepoint((mx, my)):
                            self.show_popup = False;
                            self.is_paused = False;
                            self._resume_timer()
                    elif not self.is_paused:
                        if event.button == 1 and my < GAME_HEIGHT and not self.game_finished:
                            self._handle_digging(mx, my)
                        if my > GAME_HEIGHT:
                            if self.ui.nav_rects['prev'].collidepoint((mx, my)):
                                if self.level_manager.prev_level(): self.reset_level()
                            elif self.ui.nav_rects['next'].collidepoint((mx, my)):
                                if self.level_manager.next_level(): self.reset_level()
                            elif mx > SCREEN_WIDTH - 250 and mx < SCREEN_WIDTH - 90:
                                self.show_popup = True;
                                self.is_paused = True;
                                self.pause_start = pygame.time.get_ticks()

        if not self.is_editor_mode and not self.is_paused and not self.game_finished:
            keys = pygame.key.get_pressed()
            self.player.handle_input(keys, self.map)

    def _resume_timer(self):
        if self.pause_start != 0:
            self.total_pause_duration += pygame.time.get_ticks() - self.pause_start
            self.pause_start = 0

    def _handle_digging(self, mx, my):
        grid_c, grid_r = int(mx // TILE_SIZE), int(my // TILE_SIZE)
        player_r, player_c = self.player._get_grid_pos()
        if abs(grid_r - player_r) <= 1 and abs(grid_c - player_c) <= 1:
            self.map.dig_hole(grid_r, grid_c)

    def update(self):
        self.mode_btn.update(pygame.mouse.get_pos())
        if self.is_editor_mode:
            self.editor.update()
        else:
            self.game_dropdown.update(pygame.mouse.get_pos())
            if self.is_paused or self.game_finished: return
            dt = 0
            self.map.update_holes()
            self.player.update(dt, self.map)
            if self.player.coins >= self.map.total_coins:
                self.win_time = self._get_elapsed_time()
                self.game_finished = True
                self.score_manager.save_score(self.level_manager.current_index, self.win_time)
                print(f"Level Complete! Time: {self.win_time}ms")

    def draw(self):
        if self.is_editor_mode:
            self.screen.fill((30, 30, 30))
            self.editor.draw(self.screen)
        else:
            self.screen.blit(self.background, (0, 0))
            self.map.draw(self.screen, self.assets)
            self.player.draw(self.screen)

            display_time = self._get_elapsed_time()
            best_time = self.score_manager.get_best_time(self.level_manager.current_index)

            self.ui.draw_hud(
                self.screen,
                self.level_manager.current_index,
                self.player.coins,
                self.map.total_coins,
                display_time,
                self.game_finished,
                best_time
            )

            self.game_dropdown.draw(self.screen)

            current_time = pygame.time.get_ticks()
            if current_time - self.system_message_time < 2000 and self.system_message:
                self.ui.draw_message(self.screen, self.system_message)
            if self.is_paused: self.ui.draw_pause(self.screen)
            if self.show_popup:
                scores = self.score_manager.get_top_scores(self.level_manager.current_index)
                self.ui.draw_scores_popup(self.screen, self.level_manager.current_index, scores)

        self.mode_btn.draw(self.screen)
        pygame.display.flip()

    def run(self):
        while True:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)