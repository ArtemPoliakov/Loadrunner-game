import pygame
from game.config import *

UI_BG = (50, 50, 50)
UI_BORDER = (200, 200, 200)
UI_HOVER = (70, 70, 70)
UI_ACTIVE = (100, 100, 150)
UI_TEXT = (255, 255, 255)


class UIElement:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.is_hovered = False

    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)


class Button(UIElement):
    def __init__(self, x, y, w, h, text, callback, color=UI_BG):
        super().__init__(x, y, w, h)
        self.text = text
        self.callback = callback
        self.base_color = color
        self.font = pygame.font.SysFont("Arial", 16, bold=True)
        self.icon = None

    def set_icon(self, surface):
        self.icon = pygame.transform.scale(surface, (self.rect.width - 4, self.rect.height - 4))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered and self.callback:
                self.callback()
                return True
        return False

    def draw(self, screen):
        color = UI_HOVER if self.is_hovered else self.base_color
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, UI_BORDER, self.rect, 2)

        if self.icon:
            icon_rect = self.icon.get_rect(center=self.rect.center)
            screen.blit(self.icon, icon_rect)
        elif self.text:
            text_surf = self.font.render(self.text, True, UI_TEXT)
            text_rect = text_surf.get_rect(center=self.rect.center)
            screen.blit(text_surf, text_rect)


class InputField(UIElement):
    def __init__(self, x, y, w, h, text=""):
        super().__init__(x, y, w, h)
        self.text = text
        self.active = False
        self.font = pygame.font.SysFont("Consolas", 18)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                self.active = True
            else:
                self.active = False
            return False

        if self.active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.active = False
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                if len(self.text) < 20:
                    self.text += event.unicode
            return True
        return False

    def draw(self, screen):
        color = UI_ACTIVE if self.active else UI_BG
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, UI_BORDER, self.rect, 2)

        text_surf = self.font.render(self.text, True, UI_TEXT)
        screen.blit(text_surf, (self.rect.x + 5, self.rect.centery - text_surf.get_height() // 2))


class Dropdown(UIElement):
    def __init__(self, x, y, w, h, options, callback, direction='down'):
        super().__init__(x, y, w, h)
        self.options = options
        self.callback = callback
        self.direction = direction
        self.is_open = False
        self.selected_index = 0
        self.font = pygame.font.SysFont("Arial", 14)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_open:
                for i in range(len(self.options)):
                    if self.direction == 'up':
                        y_pos = self.rect.top - (len(self.options) - i) * self.rect.height
                    else:
                        y_pos = self.rect.bottom + i * self.rect.height

                    opt_rect = pygame.Rect(self.rect.x, y_pos, self.rect.width, self.rect.height)

                    if opt_rect.collidepoint(event.pos):
                        self.selected_index = i
                        self.is_open = False
                        if self.callback:
                            self.callback(i)
                        return True

                self.is_open = False
                if self.rect.collidepoint(event.pos):
                    return True

            else:
                if self.rect.collidepoint(event.pos):
                    self.is_open = not self.is_open
                    return True
        return False

    def draw(self, screen):
        pygame.draw.rect(screen, UI_BG, self.rect)
        pygame.draw.rect(screen, UI_BORDER, self.rect, 2)

        current_text = self.options[self.selected_index] if self.options else "Empty"
        if len(current_text) > 18: current_text = current_text[:15] + "..."

        text_surf = self.font.render(current_text, True, UI_TEXT)
        screen.blit(text_surf, (self.rect.x + 5, self.rect.centery - text_surf.get_height() // 2))

        arrow_y = self.rect.centery - 2 if self.direction == 'down' else self.rect.centery + 2
        pygame.draw.polygon(screen, UI_TEXT, [
            (self.rect.right - 15, arrow_y),
            (self.rect.right - 5, arrow_y),
            (self.rect.right - 10, arrow_y + (5 if self.direction == 'down' else -5))
        ])

        if self.is_open:
            for i, option in enumerate(self.options):
                if self.direction == 'up':
                    y_pos = self.rect.top - (len(self.options) - i) * self.rect.height
                else:
                    y_pos = self.rect.bottom + i * self.rect.height

                opt_rect = pygame.Rect(self.rect.x, y_pos, self.rect.width, self.rect.height)

                mouse_pos = pygame.mouse.get_pos()
                color = UI_ACTIVE if opt_rect.collidepoint(mouse_pos) else UI_HOVER

                pygame.draw.rect(screen, color, opt_rect)
                pygame.draw.rect(screen, UI_BORDER, opt_rect, 1)

                opt_surf = self.font.render(option, True, UI_TEXT)
                screen.blit(opt_surf, (opt_rect.x + 5, opt_rect.centery - opt_surf.get_height() // 2))