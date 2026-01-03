import pygame
import sys
import os

from game.config import *
from game.entities import Player, GameMap, Enemy
from game.core.level_manager import LevelManager
from game.systems import ScoreManager, SaveManager
from game.ui import UIRenderer
from game.ui.components import Button, Dropdown
from game.core.editor import Editor
from game.entities.projectile import Fireball, Explosion


class GameApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, TOTAL_HEIGHT))
        pygame.display.set_caption("Lode Runner")

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
        self.game_over = False

        self.start_ticks = 0
        self.pause_start = 0
        self.total_pause_duration = 0
        self.win_time = 0
        self.system_message = ""
        self.system_message_time = 0

        self.map: GameMap = None
        self.player: Player = None
        self.enemies = []

        self.projectiles = []
        self.explosions = []
        self.fireballs_left = 0

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

    def _on_game_level_selected(self, index):
        self.level_manager.set_level(index)
        self.reset_level()

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
            'enemy': load_img('enemy.png'),
            'player': load_img('sprite.png'),
        }

        # Fireball
        fb_size = int(TILE_SIZE / 3)
        self.assets['fireball'] = load_img(FIREBALL_IMG)
        self.assets['fireball'] = pygame.transform.scale(self.assets['fireball'], (fb_size, fb_size))

        # Explosion
        exp_size = int(TILE_SIZE * 1.2)
        self.assets['explosion'] = load_img(EXPLOSION_IMG)
        self.assets['explosion'] = pygame.transform.scale(self.assets['explosion'], (exp_size, exp_size))

        # Pointer
        pointer_path = os.path.join(ASSETS_DIR, 'pointer.png')
        if os.path.exists(pointer_path):
            self.assets['pointer'] = pygame.image.load(pointer_path).convert_alpha()

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

        start_pos = self.level_manager.get_player_start()
        if start_pos is None:
            start_pos = {'r': MAP_HEIGHT - 3, 'c': 2}

        start_x = start_pos['c'] * TILE_SIZE
        start_y = start_pos['r'] * TILE_SIZE
        self.player = Player(start_x, start_y)

        self.enemies = []
        self.projectiles = []
        self.explosions = []
        self.fireballs_left = self.level_manager.get_current_level_fireballs()

        enemy_data = self.level_manager.get_current_level_enemies()
        for e_pos in enemy_data:
            ex = e_pos['c'] * TILE_SIZE
            ey = e_pos['r'] * TILE_SIZE
            self.enemies.append(Enemy(ex, ey))

        self.game_finished = False
        self.game_over = False
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
        if self.game_finished:
            return self.win_time
        if self.is_paused or self.game_over:
            return self.pause_start - self.start_ticks - self.total_pause_duration
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
                # Обробка Summary Panel (Win/Lose)
                if self.game_finished or self.game_over:
                    if self.game_dropdown.handle_event(event): continue

                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mx, my = event.pos
                        # Restart
                        if self.ui.nav_rects['restart'].collidepoint((mx, my)):
                            self.reset_level()
                        # Next Level (Only Win)
                        elif self.game_finished and self.ui.nav_rects['next_lvl'].collidepoint((mx, my)):
                            if self.level_manager.next_level():
                                self.reset_level()
                    continue

                if self.game_dropdown.handle_event(event): continue

                if event.type == pygame.KEYDOWN:
                    # PAUSE (ESC)
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

                    # QUICKSAVE (F1)
                    elif event.key == pygame.K_F1 and not self.is_paused:
                        elapsed = self._get_elapsed_time()
                        enemies_data = [(e.x, e.y, e.target_x, e.target_y) for e in self.enemies]

                        proj_data = []
                        for p in self.projectiles:
                            proj_data.append({
                                'x': p.rect.x,
                                'y': p.rect.y,
                                'direction': p.direction
                            })

                        expl_data = []
                        for e in self.explosions:
                            expl_data.append({
                                'x': e.rect.x,
                                'y': e.rect.y,
                                'frame_index': e.frame_index
                            })

                        data = (
                            self.player.x, self.player.y, self.player.coins,
                            elapsed,
                            self.map._data, self.map.holes,
                            enemies_data,
                            self.fireballs_left,
                            proj_data,
                            expl_data
                        )
                        self.save_manager.save_game(self.level_manager.current_index, data)
                        self.show_message(f"Lvl {self.level_manager.current_index + 1} Saved")

                    # QUICKLOAD (F2)
                    elif event.key == pygame.K_F2:
                        data = self.save_manager.load_game(self.level_manager.current_index)
                        if data:
                            try:
                                (p_x, p_y, p_coins, saved_elapsed, saved_map_data, saved_holes, saved_enemies,
                                 saved_ammo, saved_proj_data, saved_expl_data) = data

                                self.player.x = p_x
                                self.player.y = p_y
                                self.player.reset_movement()
                                self.player._coins_collected = p_coins

                                self.map._data = saved_map_data
                                self.map.holes = []
                                current_ticks = pygame.time.get_ticks()
                                for h in saved_holes:
                                    h['time'] = current_ticks
                                    self.map.holes.append(h)

                                self.enemies = []
                                for e_data in saved_enemies:
                                    ex, ey, tx, ty = e_data
                                    enemy = Enemy(ex, ey)
                                    enemy.target_x = tx
                                    enemy.target_y = ty
                                    self.enemies.append(enemy)

                                self.fireballs_left = saved_ammo

                                self.projectiles = []
                                for p_dat in saved_proj_data:
                                    fb = Fireball(
                                        p_dat['x'], p_dat['y'], p_dat['direction'],
                                        self.assets['fireball'], self.assets['explosion']
                                    )
                                    self.projectiles.append(fb)

                                self.explosions = []
                                for e_dat in saved_expl_data:
                                    exp = Explosion(
                                        e_dat['x'], e_dat['y'],
                                        self.assets['explosion']
                                    )
                                    exp.frame_index = e_dat['frame_index']
                                    self.explosions.append(exp)

                                self.start_ticks = pygame.time.get_ticks() - saved_elapsed
                                self.total_pause_duration = 0
                                self.is_paused = False
                                self.game_finished = False
                                self.game_over = False
                                self.win_time = 0
                                self.show_message(f"Lvl {self.level_manager.current_index + 1} Loaded")
                            except ValueError:
                                self.show_message("Save Format Error!")
                            except Exception as e:
                                print(f"Load Error: {e}")
                                self.show_message("Load Failed!")

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    if event.button == 2 and not self.is_paused and not self.game_finished:
                        self._spawn_fireball()
                    if self.show_popup:
                        if self.ui.nav_rects['close'].collidepoint((mx, my)):
                            self.show_popup = False
                            self.is_paused = False
                            self._resume_timer()
                    elif not self.is_paused:
                        if event.button == 1 and my < GAME_HEIGHT:
                            self._handle_digging(mx, my)
                        if my > GAME_HEIGHT:
                            if self.ui.nav_rects['prev'].collidepoint((mx, my)):
                                if self.level_manager.prev_level(): self.reset_level()
                            elif self.ui.nav_rects['next'].collidepoint((mx, my)):
                                if self.level_manager.next_level(): self.reset_level()
                            elif SCREEN_WIDTH - 250 < mx < SCREEN_WIDTH - 90:
                                self.show_popup = True
                                self.is_paused = True
                                self.pause_start = pygame.time.get_ticks()

        if not self.is_editor_mode and not self.is_paused and not self.game_finished and not self.game_over:
            keys = pygame.key.get_pressed()
            self.player.handle_input(keys, self.map)

    def _spawn_fireball(self):
        if self.fireballs_left > 0:
            direction = 1 if self.player.facing_right else -1
            start_x = self.player.x + (TILE_SIZE if direction == 1 else 0)
            start_y = self.player.y

            fireball = Fireball(
                start_x,
                start_y,
                direction,
                self.assets['fireball'],
                self.assets['explosion']
            )
            self.projectiles.append(fireball)

            self.fireballs_left -= 1
        else:
            print("No fireballs left!")

    def _resume_timer(self):
        if self.pause_start != 0:
            self.total_pause_duration += pygame.time.get_ticks() - self.pause_start
            self.pause_start = 0

    def _handle_digging(self, mx, my):
        grid_c, grid_r = int(mx // TILE_SIZE), int(my // TILE_SIZE)
        player_r, player_c = self.player.row, self.player.col
        if abs(grid_r - player_r) <= 1 and abs(grid_c - player_c) <= 1:
            self.map.dig_hole(grid_r, grid_c)

    def update(self):
        self.mode_btn.update(pygame.mouse.get_pos())
        if self.is_editor_mode:
            self.editor.update()
        else:
            self.game_dropdown.update(pygame.mouse.get_pos())
            if self.is_paused or self.game_finished or self.game_over:
                return

            dt = 0
            self.map.update_holes()
            self.player.update(dt, self.map)

            for proj in self.projectiles[:]:
                proj.update(dt, self.map, self.enemies)

                if proj.explosion_instance:
                    self.explosions.append(proj.explosion_instance)
                    self.projectiles.remove(proj)
                elif proj.should_explode:
                    self.projectiles.remove(proj)

            for exp in self.explosions[:]:
                exp.update(dt, self.map, self.enemies)
                if exp.is_finished:
                    self.explosions.remove(exp)

            player_grid_pos = self.player.row, self.player.col
            for enemy in self.enemies:
                enemy.update(dt, self.map, player_grid_pos)

                hitbox = enemy.rect.inflate(-10, -10)
                if self.player.rect.colliderect(hitbox):
                    self.game_over = True
                    self.pause_start = pygame.time.get_ticks()
                    print("GAME OVER")
                    return

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
            for enemy in self.enemies: enemy.draw(self.screen)
            for proj in self.projectiles:
                proj.draw(self.screen)
            for exp in self.explosions:
                exp.draw(self.screen)

            display_time = self._get_elapsed_time()
            best_time = self.score_manager.get_best_time(self.level_manager.current_index)

            self.ui.draw_hud(
                self.screen, self.level_manager.current_index,
                self.player.coins, self.map.total_coins,
                display_time, self.game_finished, best_time,
                self.fireballs_left,
                self.assets['fireball']
            )
            self.game_dropdown.draw(self.screen)

            # Draw summary panel
            if self.game_finished or self.game_over:
                self.ui.draw_summary_panel(self.screen, self.game_finished, self.win_time)

            elif self.is_paused:
                self.ui.draw_pause(self.screen)

            # Messages
            current_time = pygame.time.get_ticks()
            if current_time - self.system_message_time < 2000 and self.system_message:
                self.ui.draw_message(self.screen, self.system_message)

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