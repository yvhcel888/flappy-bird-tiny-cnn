import pygame
import os
import glob
class Bird:
    def __init__(self, path, x, y):
        self.path = path
        self.x = x
        self.y = y
        self.frame=self.load_img()
        self.counter=0
        self.index = 0
        self.vy = 0.0
        self.gravity = 1500.0
        self.jump_speed = -450.0
        self.angle = 0.0
        self.rect = pygame.Rect(0, 0, 34, 24)
        self.rect.center = (x, y)

    def update(self, dt, per_frame=6):
        self.counter += 1
        if self.counter >= per_frame:
            self.counter = 0
            self.index = (self.index + 1) % len(self.frame)

        self.vy += self.gravity * dt
        self.y += self.vy * dt
        if self.y < 0:
            self.y = 0
            self.vy = 0
        self.angle = max(-25, min(60, -self.vy * 0.1))
        self.rect.center = (self.x, self.y)

        if self.y < 0:
            self.y = 0
            self.vy = 0

    def load_img(self):
        path=os.path.join(self.path, "*.png")
        files = glob.glob(path)
        files.sort()
        img=[]
        for img_path in files:
            img.append(pygame.transform.scale(pygame.image.load(img_path), (34, 24)))
        return img

    def draw_bird(self, screen):
        img = self.frame[self.index]
        img = pygame.transform.rotate(img, self.angle)
        rect = img.get_rect(center=(self.x, self.y))
        screen.blit(img, rect)

    #AI建议删掉原来我自己的fall函数，只要这个jump？？然后把物理逻辑全部写入了update。。。似乎是好一点？？
    def jump(self):
        self.vy = self.jump_speed

    def game_over(self, pipe_list, h):
        if self.rect.bottom >= h:
            return True
        for p in pipe_list:
            if p.collides_with(self.rect):
                return True
        return False


class BlueBird(Bird):
    def __init__(self, x, y):
        super().__init__(r".\img\bird\Transparent\Blue Bird\PNG",x,y)

class GreenBird(Bird):
    def __init__(self, x, y):
        super().__init__(r".\img\bird\Transparent\Green Bird\PNG",x,y)

class PinkBird(Bird):
    def __init__(self, x, y):
        super().__init__(r".\img\bird\Transparent\Pink Bird\PNG",x,y)

class YellowBird(Bird):
    def __init__(self, x, y):
        super().__init__(r".\img\bird\Transparent\Yellow Bird\PNG",x,y)
