import pygame
import numpy as np
import torch
import os
from ai_model import FlappyNet


class FlappyAI:
    def __init__(self, is_ai, save_file="train_data.npz"):
        self.is_ai = is_ai
        self.save_file = os.path.join("data", save_file)
        self.model = None
        self.recorded_frames = []
        self.recorded_speeds = []
        self.recorded_actions = []

        if self.is_ai:
            self.model = FlappyNet()
            try:
                model_path = "flappy_ai.pth" if os.path.exists("flappy_ai.pth") else os.path.join("data",
                                                                                                  "flappy_ai.pth")
                self.model.load_state_dict(torch.load(model_path, weights_only=True))
                self.model.eval()
                print("AI 模型加载成功！")
            except FileNotFoundError:
                print("警告：未找到 AI 模型，请先录制数据并运行 train_ai.py！")
                self.is_ai = False

    def _extract_features(self, screen, bird_vy, speed):
        # 因为传进来的 screen 已经是画好的 160x80 了，直接取像素
        pixels = pygame.surfarray.array3d(screen).transpose(1, 0, 2)
        gray = np.dot(pixels[..., :3], [0.299, 0.587, 0.114]).astype(np.uint8)

        bird_vy_norm = bird_vy / 1000.0
        pipe_speed_norm = (speed * 80) / 500.0
        return gray, [bird_vy_norm, pipe_speed_norm]

    def step(self, screen, bird_vy, speed, human_action=False):
        gray, speed_features = self._extract_features(screen, bird_vy, speed)

        if self.is_ai and self.model:
            img_tensor = torch.tensor(gray / 255.0, dtype=torch.float32).unsqueeze(0).unsqueeze(0)
            speed_tensor = torch.tensor([speed_features], dtype=torch.float32)
            with torch.no_grad():
                out = self.model(img_tensor, speed_tensor)
                action = torch.argmax(out, dim=1).item()
            return action
        else:
            self.recorded_frames.append(gray)
            self.recorded_speeds.append(speed_features)
            self.recorded_actions.append(1 if human_action else 0)
            return 1 if human_action else 0

    def save_data(self):
        if not self.is_ai and len(self.recorded_frames) > 0:
            os.makedirs("data", exist_ok=True)
            # 先写临时文件再改名：录制进程被中断时不会留下半截的 npz
            tmp = self.save_file + ".part"
            with open(tmp, "wb") as fh:
                np.savez_compressed(fh,
                                    frames=np.array(self.recorded_frames, dtype=np.uint8),
                                    speeds=np.array(self.recorded_speeds, dtype=np.float32),
                                    actions=np.array(self.recorded_actions, dtype=np.int64))
            os.replace(tmp, self.save_file)
            print(f"✅ 数据已保存到 {self.save_file}！共录制 {len(self.recorded_frames)} 帧。")


class RuleBot:
    """规则机器人：给模仿学习当“老师”。

    旧版的问题：只有管子距离 200 像素以内才开始瞄准，而且必须“正在下落”才肯拍翅。
    speed=20 时 200 像素只够走 0.125 秒，鸟最多上升 45 像素，而缝隙可能在上方 250 像素处，
    所以高难度的满分对局其实是“连续抽到低缝隙”的运气局，标签本身没有策略信息。

    这一版把两处都改掉：
      1) 不管距离多远，始终朝着“下一根管子的安全高度”靠，提前量给足；
      2) 只要低于安全高度就拍翅，允许连续拍翅快速爬升（速度上限 450 px/s）。
    于是鸟会贴着目标高度做一次跳跃幅度（约 67 像素）的锯齿运动，目标点按管型往下压
    半个跳跃高度，正好让锯齿关于缝隙中心对称，五个难度都能稳定通过。
    实测（dt=1/60）：3/7/10 档能一直玩到步数上限；15 档偶尔才撞一次；
    20 档多数对局能过几百根管子，偶尔在第几十根处撞管——这一档管间距 1350 已经超过屏幕宽度，
    下一根管子露头时只剩 0.55 秒，而一次跳跃的高度就有 67 像素，物理上确实没多少余量了。
    （旧版在 15/20 档的平均得分只有 0.9 和 1.1。）

    act() 的签名和返回值都没变，game.py 里的 auto_record 仍然可以直接用。
    """

    def __init__(self, aim_ratio=0.50, hold_y=400):
        # 锯齿运动的上冲来自一次跳跃，aim_ratio 表示把目标点往下压多少个“跳跃高度”。
        # 取 0.5 正好让锯齿的最高点和最低点关于缝隙中心对称，上下各留 34 像素余量。
        self.aim_ratio = aim_ratio
        # 前方暂时没有管子时（speed=20 的管间距 1350 比屏幕还宽）先停在这个高度等它出现；
        # 停得比屏幕中线低一点，是因为“从高处来不及掉下去”比“从低处爬上来”更容易撞。
        self.hold_y = hold_y

    @staticmethod
    def _next_pipe(bird, pipe_list):
        """找出鸟接下来要穿过的那根管子。

        注意要用鸟的“左边缘”而不是中心：管子右沿只要还压着鸟的身体，
        就说明鸟还没完全脱离这根管子，这时候把目标换成下一根会直接撞上去。
        """
        left = bird.rect.left
        for p in pipe_list:
            if p.active and p.x + p.WIDTH > left:
                return p
        return None

    def _target_y(self, bird, p):
        """算出鸟中心应该维持的 y（y 向下为正）。"""
        half_h = bird.rect.height / 2.0
        hop = (bird.jump_speed ** 2) / (2.0 * bird.gravity)  # 一次跳跃的上升高度 ≈ 67.5

        if p.n == 3:  # 上下都有管子：瞄准缝隙中心，再往下压半个跳跃高度
            return p.gap_y + hop * self.aim_ratio
        if p.n == 1:  # 只有下管：贴着管口上方飞
            return p.screen_h - p.bot_len - hop - half_h - 18
        # n == 2，只有上管：贴着管口下方飞
        return p.top_len + hop + half_h + 18

    def act(self, bird, pipe_list, speed=1):
        p = self._next_pipe(bird, pipe_list)
        target_y = self.hold_y if p is None else self._target_y(bird, p)
        # 低于目标高度（y 更大）就拍翅；高于目标就让它自由下落
        return 1 if bird.y > target_y else 0