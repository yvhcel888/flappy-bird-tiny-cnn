'''多进程数据采集（模仿学习的数据集）

和第一版相比改了四件事：
  1) 速度列表可配：真正会被玩到的五档是 3/7/10/15/20；speed=1 属于额外的一档，
     它一局要 60 秒（约 3600 帧），录 30 局就是 10 万帧，会把数据集又压偏，不需要就别放进 SPEEDS。
  2) 每局封顶分从 5 提到 12：老师能连续通过更多管子，数据集里的缝隙组合才够丰富。
  3) 不再“只留满分局”：只要过了至少 1 分就保留，失败局里那些“已经偏离中心”的状态
     恰恰是模型实战时会遇到的，对缓解累积误差有用。
  4) 执行动作时按 EXPLORE_EPS 的概率“晚跳一拍”，但训练标签仍然记老师在这一帧的
     正确动作——相当于做了一次轻量 DAgger，让数据里出现“偏了怎么救回来”的样本。

标签（动作）由 ai_helper.RuleBot 给出，是纯几何规则，不依赖模型，所以采集不需要 GPU。

注意：train_ai.py 会 glob data/train_data_speed*_bird*.npz，重新采集前请先清空 data 目录，
否则新旧数据（包括早期那些只有一两百帧的残缺文件）会混在一起。
'''
import math
import random
import multiprocessing

import numpy as np
import pygame

from bird import BlueBird, GreenBird, PinkBird, YellowBird
from pipe import Pipe
from ai_helper import FlappyAI, RuleBot

SPEEDS = [1, 3, 7, 10, 15, 20]   # UI 五个难度对应 3/7/10/15/20；1 是额外的一档，不需要就删掉
TARGET_EPISODES = 30          # 每个速度保留多少局
# speed=1 一局要 60 秒（约 3600 帧），同样录 30 局会占掉 10 万帧，所以单独少录一点
TARGET_EPISODES_BY_SPEED = {1: 8}
EPISODE_MAX_SCORE = 12        # 一局打到多少分就重开（不是“只留满分局”）
MIN_KEEP_SCORE = 1            # 低于这个分数的一局丢掉，避免开局即撞的垃圾帧
EXPLORE_EPS = 0.03            # 执行动作时“故意做错”的概率，0 表示完全听老师的


def record_process(bird_num, speed=1, target_episodes=None):
    if target_episodes is None:
        target_episodes = TARGET_EPISODES_BY_SPEED.get(speed, TARGET_EPISODES)
    print(f"[进程启动] 鸟 {bird_num} | 速度 {speed} | 目标: 采集 {target_episodes} 局（每局最多 {EPISODE_MAX_SCORE} 分）")

    pygame.init()
    pygame.display.set_mode((1, 1), pygame.HIDDEN)
    Pipe.load_base("./img/pipe/green_pipe.png")

    w, h = 1200, 600
    dt = 1.0 / 60.0

    save_file = f"train_data_speed{speed}_bird{bird_num}.npz"
    ai = FlappyAI(is_ai=False, save_file=save_file)
    rule_bot = RuleBot()

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
    pipe_list = []
    spawn_timer = 0.0
    score = 0

    kept_count = 0
    attempt_count = 0
    start_idx = 0

    while True:
        # 死亡或打满封顶分，都结算并重开
        if attempt_count == 0 or bird.game_over(pipe_list, h) or score >= EPISODE_MAX_SCORE:

            if attempt_count > 0:
                if score >= MIN_KEEP_SCORE:
                    kept_count += 1
                    print(f"[鸟{bird_num}] 第 {kept_count}/{target_episodes} 局：{score} 分，"
                          f"累计 {len(ai.recorded_frames)} 帧")
                else:
                    # 0 分对局全是开局就撞的画面，删掉
                    del ai.recorded_frames[start_idx:]
                    del ai.recorded_speeds[start_idx:]
                    del ai.recorded_actions[start_idx:]

            attempt_count += 1

            if kept_count >= target_episodes:
                print(f"[进程结束] 鸟 {bird_num} | 速度 {speed} 采集完毕，保存数据！")
                ai.save_data()
                pygame.quit()
                return

            bird = create_bird(bird_num)
            pipe_list.clear()
            spawn_timer = 0.0
            score = 0

            start_idx = len(ai.recorded_frames)

        # ================= 1. 渲染小黑图 =================
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

        # ================= 2. 取标签、记录、执行 =================
        # 标签永远是“老师在这一帧会怎么做”
        teacher_action = 1 if rule_bot.act(bird, pipe_list, speed) == 1 else 0
        ai.step(mini_screen, bird.vy, speed, teacher_action == 1)   # is_ai=False，这里只负责记录

        # 实际执行的动作偶尔故意做错，让轨迹偏离中心，模型才能见到“偏了怎么救”。
        # 只做“该跳的时候晚一拍”这种可恢复的小扰动：凭空多跳一次会让鸟窜高 67 像素，
        # 管子就在前面时根本掉不回来，录下来的就全是已经救不回来的画面，反而教坏模型。
        execute_action = teacher_action
        next_p = rule_bot._next_pipe(bird, pipe_list)
        far_from_pipe = next_p is None or (next_p.x - bird.rect.right) > 200
        if (far_from_pipe and teacher_action == 1 and EXPLORE_EPS > 0
                and random.random() < EXPLORE_EPS):
            execute_action = 0

        if execute_action == 1:
            bird.jump()

        # ================= 3. 物理更新 =================
        bird.update(dt=dt)

        dynamic_distance = 350 + (speed * 50)
        if not pipe_list or pipe_list[-1].x < w - dynamic_distance:
            p = Pipe(w, h)
            p.reset()
            pipe_list.append(p)

        for p in pipe_list:
            p.update(dt, speed * 80)

        pipe_list[:] = [p for p in pipe_list if p.active]

        for p in pipe_list:
            if p.active and not p.passed:
                if bird.x > p.x + p.WIDTH:
                    p.passed = True
                    score += 1


if __name__ == '__main__':
    print("================ 开始多进程数据采集 ================")
    print("提醒：train_ai.py 会读取 data 下所有 train_data_speed*_bird*.npz，")
    print("      旧版本留下来的数据请先删掉，否则会混进新的训练集。")

    processes = []
    for i, current_speed in enumerate(SPEEDS):
        b_num = (i % 4) + 1  # 鸟编号在 1~4 循环，避免同名文件覆盖
        print(f"启动进程: 鸟 {b_num} | 速度 {current_speed}")
        p = multiprocessing.Process(target=record_process, args=(b_num, current_speed))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()
