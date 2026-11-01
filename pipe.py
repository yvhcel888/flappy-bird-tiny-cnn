import pygame
import random

class Pipe:
    WIDTH = 100
    GAP = 180
    MIN_LEN = 60
    SPEED = 180
    _base_img = None

    @classmethod
    def load_base(cls, path):
        img = pygame.image.load(path).convert_alpha()
        w, h = img.get_size()
        new_h = int(h * cls.WIDTH / w)
        cls._base_img = pygame.transform.smoothscale(img, (cls.WIDTH, new_h))

    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.x = screen_w
        self.n = 3
        self.gap_y = 0
        self.top_len = 0
        self.bot_len = 0
        self.passed = False
        self.active = False


    def reset(self, x=None):
        self.x = x if x is not None else self.screen_w
        self.n = random.randint(1, 3)#1.只有上 2.只有下 3.上下
        self.passed = False
        self.active = True

        if self.n == 3:
            self.gap_y = random.randint(
                self.GAP // 2 + self.MIN_LEN,
                self.screen_h - self.GAP // 2 - self.MIN_LEN
            )
            self.top_len = self.gap_y - self.GAP // 2
            self.bot_len = self.screen_h - (self.gap_y + self.GAP // 2)
        elif self.n == 1:
            self.bot_len = random.randint(250, 300)
            self.top_len = 0
        else:
            self.top_len = random.randint(250, 300)
            self.bot_len = 0

    def update(self, dt, speed=None):
        if not self.active:
            return
        v = speed if speed is not None else self.SPEED
        self.x -= v * dt
        if self.x + self.WIDTH < 0:
            self.active = False

    def draw(self, screen):
        if not self.active:
            return
        if self.top_len > 0:
            top = pygame.transform.smoothscale(self._base_img, (self.WIDTH, self.top_len))
            screen.blit(top, (self.x, 0))

        if self.bot_len > 0:
            bot = pygame.transform.flip(self._base_img, False, True)
            bot = pygame.transform.smoothscale(bot, (self.WIDTH, self.bot_len))
            bot_y = self.screen_h - self.bot_len
            screen.blit(bot, (self.x, bot_y))

    def collides_with(self, bird_rect):
        if not self.active:
            return False
        if self.top_len > 0:
            if bird_rect.colliderect(pygame.Rect(self.x, 0, self.WIDTH, self.top_len)):
                return True
        if self.bot_len > 0:
            bot_y = self.screen_h - self.bot_len
            if bird_rect.colliderect(pygame.Rect(self.x, bot_y, self.WIDTH, self.bot_len)):
                return True
        return False