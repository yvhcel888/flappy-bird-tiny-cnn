'''
截图代码位置不对，导致截了几千个没有鸟和管道的背景图。。。。
AI这都给我发现问题了

'''
import pygame
import random
import time
import threading
import math
import os
from bird import BlueBird, GreenBird, PinkBird, YellowBird, Bird
from pipe import Pipe
from ai_helper import FlappyAI, RuleBot

weather_id = random.randint(1, 3)
day_t = [1, 2, 3, 4, 5, 6, 7, 8]
noon_t = [9, 10, 11, 12, 13, 14, 15, 16]
night_t = [17, 18, 19, 20, 21, 22, 23, 0]

v_time = 1
x = 0.0
size = w, h = 1200, 600
FPS = 60
pipe_list = []
spawn_timer = 0.0
PIPE_DISTANCE = 350

bg_dic = {
    "day_1": "./img/bg/day/day_sunny.jpg", "day_2": "./img/bg/day/day_raining.jpg",
    "day_3": "./img/bg/day/day_snowing.jpg",
    "night_1": "./img/bg/night/night_sunny.jpg", "night_2": "./img/bg/night/night_raining.jpg",
    "night_3": "./img/bg/night/night_snowing.jpg",
    "noon_1": "./img/bg/noon/noon_sunny.jpg", "noon_2": "./img/bg/noon/noon_raining.jpg",
    "noon_3": "./img/bg/noon/noon_snowing.jpg",
}


def set_weather():
    global weather_id
    weather_id = random.randint(1, 3)


def time_go():
    time_g = 0
    global v_time
    while True:
        time.sleep(1)
        if time_g == 10:
            set_weather()
            time_g = 0
        v_time += 1
        v_time %= 24
        time_g += 1


def load_img(path):
    img = pygame.image.load(path)
    return pygame.transform.scale(img, (1520, h))


def draw_tiled(surface, img, start_x, alpha=255):
    img.set_alpha(alpha)
    iw = 1520
    px = (start_x % iw) - iw
    while px < w:
        surface.blit(img, (px, 0))
        px += iw


def create_key(v_time, weather_id):
    key = None
    if v_time in day_t:
        key = "day"
    elif v_time in noon_t:
        key = "noon"
    elif v_time in night_t:
        key = "night"

    if weather_id == 1:
        key += "_1"
    elif weather_id == 2:
        key += "_2"
    elif weather_id == 3:
        key += "_3"
    return key


def game(speed, bird_num, is_ai, auto_record=False, max_episodes=10):
    global x
    global weather_id
    global spawn_timer

    if not pygame.get_init(): pygame.init()
    if not pygame.font.get_init(): pygame.font.init()
    if pygame.display.get_surface() is None:
        screen = pygame.display.set_mode(size)
    else:
        screen = pygame.display.get_surface()

    score = 0
    fade = 0.0
    Pipe.load_base("./img/pipe/green_pipe.png")
    pygame.display.set_caption("Flappy Bird")
    # 字体：优先用仓库自带的开源字体（站酷快乐体，OFL 1.1）；本机若还留着华文楷体就沿用它；
    # 都没有则退回系统字体。
    font = None
    for font_file in ("./font/ZCOOLKuaiLe-Regular.ttf", "./font/STKAITI.TTF"):
        if os.path.exists(font_file):
            font = pygame.font.Font(font_file, 20)
            break
    if font is None:
        font = pygame.font.SysFont("microsoftyahei,simhei,pingfangsc,arial", 20)
    clock = pygame.time.Clock()

    img_cache = {}
    for key, path in bg_dic.items():
        img_cache[key] = load_img(path)

    next_img = None
    now_sta = create_key(v_time, weather_id)
    current_img = img_cache[now_sta]

    def create_bird(b_num):
        if b_num == 1:
            return BlueBird(x=w // 3.8, y=h // 2)
        elif b_num == 2:
            return GreenBird(x=w // 3.8, y=h // 2)
        elif b_num == 3:
            return PinkBird(x=w // 3.8, y=h // 2)
        elif b_num == 4:
            return YellowBird(x=w // 3.8, y=h // 2)

    bird = create_bird(bird_num)
    save_file = f"train_data_speed{speed}_bird{bird_num}.npz"
    ai = FlappyAI(is_ai, save_file=save_file)
    rule_bot = RuleBot() if auto_record else None

    episode_count = 0
    score = 0

    while True:
        is_game_over = bird.game_over(pipe_list, h)

        # 1. 实战模式：只有撞死才结束
        if not auto_record:
            if is_game_over:  # <--- 改成这样，去掉 5 分限制
                g = pygame.transform.scale(pygame.image.load("./img/gameover/gameover.png"), (w, h))
                screen.blit(g, (0, 0))
                pygame.display.flip()
                time.sleep(1.5)
                return

        # 2. 挂机录制模式：达到 n 分就自动重置（这里不要动！）
        elif auto_record:
            if episode_count == 0 or is_game_over or score >= 10:

                episode_count += 1
                if episode_count > max_episodes:
                    ai.save_data()
                    return

                bird = create_bird(bird_num)
                pipe_list.clear()
                spawn_timer = 0.0
                score = 0
                pygame.event.clear()

        this_sta = create_key(v_time, weather_id)
        human_action = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                ai.save_data()
                return
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not is_ai and not auto_record:
                    human_action = True

        # ================= 1. 渲染给 AI 看的小黑图（当前帧） =================
        mini_screen = pygame.Surface((160, 80))
        mini_screen.fill((0, 0, 0))
        scale_x = 160 / w
        scale_y = 80 / h

        for p in pipe_list:
            if p.active:
                px = int(p.x * scale_x)
                pw = 20
                if p.top_len > 0:
                    pygame.draw.rect(mini_screen, (255, 255, 255), (px, 0, pw, int(p.top_len * scale_y)))
                if p.bot_len > 0:
                    pygame.draw.rect(mini_screen, (255, 255, 255),
                                     (px, int((p.screen_h - p.bot_len) * scale_y), pw, int(p.bot_len * scale_y)))

        pygame.draw.rect(mini_screen, (100, 100, 100), (0, int((h - 60) * scale_y), 160, 80))

        bx = int(bird.x * scale_x)
        by = int(bird.y * scale_y)
        angle_rad = math.radians(bird.angle)
        cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
        pts = [(8, 0), (-4, -4), (-4, 4)]
        rotated_pts = []
        for pt_x, pt_y in pts:
            rx = pt_x * cos_a - pt_y * sin_a
            ry = pt_x * sin_a + pt_y * cos_a
            rotated_pts.append((bx + rx, by + ry))
        pygame.draw.polygon(mini_screen, (255, 255, 255), rotated_pts)

        # ================= 2. 产生动作并进行物理更新 =================
        if auto_record:
            human_action = rule_bot.act(bird, pipe_list, speed) == 1

        action = ai.step(mini_screen, bird.vy, speed, human_action)

        # 允许跳跃
        if action == 1:
            bird.jump()

        dt = clock.tick(FPS) / 1000.0
        bird.update(dt=dt)

        dynamic_distance = 350 + (speed * 50)
        if not pipe_list or pipe_list[-1].x < w - dynamic_distance:
            p = Pipe(w, h)
            p.reset()
            pipe_list.append(p)

        for p in pipe_list:
            p.update(dt, speed * 80)

        pipe_list[:] = [p for p in pipe_list if p.active]

        # 计分
        for p in pipe_list:
            if p.active and not p.passed:
                if bird.x > p.x + p.WIDTH:
                    p.passed = True
                    score += 1

        # ================= 3. 渲染人类看到的主屏幕（物理更新后） =================
        draw_tiled(screen, current_img, x, 255)

        if now_sta != this_sta:
            now_sta = this_sta
            next_img = img_cache[now_sta]
            fade = 0.0
        if next_img is not None:
            fade += 1.0 / (1.5 * FPS)
            alpha = int(fade * 255)
            draw_tiled(screen, next_img, x, alpha)
            if fade >= 1.0:
                fade = 0.0
                current_img = next_img
                next_img = None

        for p in pipe_list:
            p.draw(screen)
        bird.draw_bird(screen)

        score_surf = font.render("当前得分" + str(score), True, (255, 0, 255))
        score_rect = score_surf.get_rect(midleft=(0, 40))
        screen.blit(score_surf, score_rect)

        pygame.display.flip()
        x -= speed * dt * 80


if __name__ == '__main__':
    threading.Thread(target=time_go, daemon=True).start()
    game(7, 1, False)
