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
            'close': pygame.Rect(0, 0, 0, 0)
        }

    def _truncate_text(self, text: str, font: pygame.font.Font, max_width: int) -> str:
        if font.size(text)[0] <= max_width:
            return text

        ellipsis = "..."
        for i in range(len(text), 0, -1):
            candidate = text[:i] + ellipsis
            if font.size(candidate)[0] <= max_width:
                return candidate
        return ellipsis

    def draw_hud(self, screen: pygame.Surface, level_idx: int, coins: int, total_coins: int, time_ms: int,
                 is_finished: bool, best_time: int = None):
        pygame.draw.rect(screen, COLOR_PANEL, (0, GAME_HEIGHT, SCREEN_WIDTH, PANEL_HEIGHT))

        prev_color = COLOR_TEXT if level_idx > 0 else (100, 100, 100)
        next_color = COLOR_TEXT

        prev_surf = self.ui_font.render("<", True, prev_color)
        next_surf = self.ui_font.render(">", True, next_color)


        self.nav_rects['prev'] = screen.blit(prev_surf, (25, GAME_HEIGHT + 15))
        self.nav_rects['next'] = screen.blit(next_surf, (270, GAME_HEIGHT + 15))


        base_y = GAME_HEIGHT + 18

        coin_text = f"Coins: {coins}/{total_coins}"
        screen.blit(self.font.render(coin_text, True, COLOR_GOLD), (SCREEN_WIDTH - 460, base_y))

        seconds = time_ms // 1000
        time_suffix = " (WIN!)" if is_finished else ""
        time_text = f"Time: {seconds}s{time_suffix}"
        screen.blit(self.font.render(time_text, True, (200, 200, 200)), (SCREEN_WIDTH - 320, base_y))

        record_str = "Best: --"
        if best_time is not None:
            record_str = f"Best: {best_time // 1000}s"
        screen.blit(self.font.render(record_str, True, (255, 255, 100)), (SCREEN_WIDTH - 180, base_y))

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