import pygame
from game.config import *


class UIRenderer:
    def __init__(self):
        self.font = pygame.font.SysFont("Arial", 20)
        self.ui_font = pygame.font.SysFont("Consolas", 28, bold=True)
        self.pause_font = pygame.font.SysFont("Consolas", 60, bold=True)
        self.msg_font = pygame.font.SysFont("Consolas", 20, bold=True)

        self.nav_rects = {
            'prev': pygame.Rect(0, 0, 0, 0),
            'next': pygame.Rect(0, 0, 0, 0),
            'close': pygame.Rect(0, 0, 0, 0),
            'restart': pygame.Rect(0, 0, 0, 0),
            'next_lvl': pygame.Rect(0, 0, 0, 0)
        }

    def _truncate_text(self, text: str, font: pygame.font.Font, max_width: int) -> str:
        if font.size(text)[0] <= max_width: return text
        ellipsis = "..."
        for i in range(len(text), 0, -1):
            candidate = text[:i] + ellipsis
            if font.size(candidate)[0] <= max_width: return candidate
        return ellipsis

    def draw_hud(self, screen: pygame.Surface, level_idx: int, coins: int, total_coins: int, time_ms: int,
                 is_finished: bool, best_time: int, fireballs: int, fireball_icon: pygame.Surface):
        pygame.draw.rect(screen, COLOR_PANEL, (0, GAME_HEIGHT, SCREEN_WIDTH, PANEL_HEIGHT))

        prev_color = COLOR_TEXT if level_idx > 0 else (100, 100, 100)
        next_color = COLOR_TEXT

        prev_surf = self.ui_font.render("<", True, prev_color)
        next_surf = self.ui_font.render(">", True, next_color)

        self.nav_rects['prev'] = screen.blit(prev_surf, (25, GAME_HEIGHT + 15))
        self.nav_rects['next'] = screen.blit(next_surf, (270, GAME_HEIGHT + 15))

        base_y = GAME_HEIGHT + 18
        center_y = base_y + 10

        if fireball_icon:
            w, h = fireball_icon.get_size()
            scaled_icon = pygame.transform.scale(fireball_icon, (w * 5, h * 5))
            icon_rect = scaled_icon.get_rect(centery=center_y, x=310)
            screen.blit(scaled_icon, icon_rect)
            count_text = f"x {fireballs}"
            text_surf = self.font.render(count_text, True, (255, 100, 100))
            text_rect = text_surf.get_rect(centery=center_y, left=icon_rect.right + 5)
            screen.blit(text_surf, text_rect)


        coin_text = f"Coins: {coins}/{total_coins}"
        coin_surf = self.font.render(coin_text, True, COLOR_GOLD)
        coin_rect = coin_surf.get_rect(centery=center_y, left=SCREEN_WIDTH - 430)
        screen.blit(coin_surf, coin_rect)

        seconds = time_ms // 1000
        time_text = f"Time: {seconds}s"
        time_surf = self.font.render(time_text, True, (200, 200, 200))
        time_rect = time_surf.get_rect(centery=center_y, left=SCREEN_WIDTH - 290)
        screen.blit(time_surf, time_rect)

        record_str = "Best: --"
        if best_time is not None:
            record_str = f"Best: {best_time // 1000}s"

        best_surf = self.font.render(record_str, True, (255, 255, 100))
        best_rect = best_surf.get_rect(centery=center_y, left=SCREEN_WIDTH - 170)
        screen.blit(best_surf, best_rect)

    def draw_message(self, screen: pygame.Surface, text: str):
        msg_surf = self.msg_font.render(text, True, (0, 255, 0))
        msg_rect = msg_surf.get_rect(topright=(SCREEN_WIDTH - 10, 10))
        screen.blit(msg_surf, msg_rect)

    def draw_pause(self, screen: pygame.Surface):
        overlay = pygame.Surface((SCREEN_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))
        pause_surf = self.pause_font.render("PAUSED", True, COLOR_TEXT)
        pause_rect = pause_surf.get_rect(center=(SCREEN_WIDTH // 2, GAME_HEIGHT // 2))
        screen.blit(pause_surf, pause_rect)

    def draw_scores_popup(self, screen: pygame.Surface, level_idx: int, top_scores: list):
        POPUP_W, POPUP_H = 200, 160
        POPUP_X = (SCREEN_WIDTH - POPUP_W) // 2
        POPUP_Y = (GAME_HEIGHT - POPUP_H) // 2
        pygame.draw.rect(screen, (50, 50, 70), (POPUP_X, POPUP_Y, POPUP_W, POPUP_H))
        pygame.draw.rect(screen, (200, 200, 200), (POPUP_X, POPUP_Y, POPUP_W, POPUP_H), 2)
        title = self.font.render(f"Top 3 (Lvl {level_idx + 1})", True, COLOR_GOLD)
        screen.blit(title, (POPUP_X + 20, POPUP_Y + 10))
        self.nav_rects['close'] = pygame.Rect(POPUP_X + POPUP_W - 30, POPUP_Y + 5, 25, 25)
        pygame.draw.rect(screen, (200, 50, 50), self.nav_rects['close'])
        screen.blit(self.font.render("X", True, COLOR_TEXT),
                    (self.nav_rects['close'].x + 6, self.nav_rects['close'].y - 2))
        if not top_scores:
            screen.blit(self.font.render("No records", True, (150, 150, 150)), (POPUP_X + 30, POPUP_Y + 60))
        else:
            for i, score in enumerate(top_scores):
                line = f"{i + 1}. {score // 1000}s"
                screen.blit(self.font.render(line, True, COLOR_TEXT), (POPUP_X + 40, POPUP_Y + 50 + i * 30))

    def draw_summary_panel(self, screen: pygame.Surface, is_win: bool, time_ms: int):
        overlay = pygame.Surface((SCREEN_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        W, H = 300, 200
        X = (SCREEN_WIDTH - W) // 2
        Y = (GAME_HEIGHT - H) // 2

        border_col = (50, 200, 50) if is_win else (200, 50, 50)
        pygame.draw.rect(screen, (30, 30, 40), (X, Y, W, H))
        pygame.draw.rect(screen, border_col, (X, Y, W, H), 3)

        title_text = "VICTORY!" if is_win else "GAME OVER"
        title_col = (100, 255, 100) if is_win else (255, 100, 100)
        title_surf = self.ui_font.render(title_text, True, title_col)
        screen.blit(title_surf, title_surf.get_rect(center=(X + W // 2, Y + 40)))

        res_text = f"Time: {time_ms // 1000}s" if is_win else "Try Again!"
        res_surf = self.font.render(res_text, True, (255, 255, 255))
        screen.blit(res_surf, res_surf.get_rect(center=(X + W // 2, Y + 80)))

        btn_w, btn_h = 100, 35
        restart_rect = pygame.Rect(X + 20, Y + H - 50, btn_w, btn_h)
        pygame.draw.rect(screen, (100, 100, 200), restart_rect)
        pygame.draw.rect(screen, (200, 200, 255), restart_rect, 2)
        rest_surf = self.font.render("Restart", True, (255, 255, 255))
        screen.blit(rest_surf, rest_surf.get_rect(center=restart_rect.center))
        self.nav_rects['restart'] = restart_rect

        if is_win:
            next_rect = pygame.Rect(X + W - 20 - btn_w, Y + H - 50, btn_w, btn_h)
            pygame.draw.rect(screen, (50, 150, 50), next_rect)
            pygame.draw.rect(screen, (150, 255, 150), next_rect, 2)
            next_surf = self.font.render("Next Lvl", True, (255, 255, 255))
            screen.blit(next_surf, next_surf.get_rect(center=next_rect.center))
            self.nav_rects['next_lvl'] = next_rect
        else:
            self.nav_rects['next_lvl'] = pygame.Rect(0, 0, 0, 0)