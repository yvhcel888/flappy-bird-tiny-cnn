'''
训练太慢，AI给出的把数据搬到GPU，
但还是很慢，如果从20s减少到19s算快的话，
或许可以减少卷积核？
但是模型质量会下降
'''
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from ai_model import FlappyNet
import glob
import time

BATCH_SIZE = 1024  # 显存够大，直接拉满
EPOCHS = 30
LEARNING_RATE = 1e-3
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_data_to_gpu():
    files = glob.glob("data/train_data_speed*_bird*.npz")
    if not files:
        raise FileNotFoundError("未找到数据文件")

    all_frames, all_speeds, all_actions = [], [], []
    for f in files:
        data = np.load(f)
        all_frames.append(data['frames'])
        all_speeds.append(data['speeds'])
        all_actions.append(data['actions'])

    frames_raw = np.concatenate(all_frames, axis=0)
    speeds_raw = np.concatenate(all_speeds, axis=0)
    actions_raw = np.concatenate(all_actions, axis=0)

    print("正在将数据加载并预处理到 GPU 显存...")

    # === 核心优化 1：预先全部转为 float16 并除以 255，直接吃掉 4.3G 显存 ===
    # 这样训练时切片出来直接就能用，不需要再做任何转换
    frames_gpu = torch.tensor(frames_raw, dtype=torch.float16, device=DEVICE).unsqueeze(1) / 255.0
    speeds_gpu = torch.tensor(speeds_raw, dtype=torch.float16, device=DEVICE)
    actions_gpu = torch.tensor(actions_raw, dtype=torch.long, device=DEVICE)

    total = len(actions_gpu)
    jumps = actions_gpu.sum().item()
    no_jumps = total - jumps

    weight_no_jump = total / (2.0 * no_jumps) if no_jumps > 0 else 1.0
    weight_jump = total / (2.0 * jumps) if jumps > 0 else 1.0
    class_weights = torch.tensor([weight_no_jump, weight_jump], dtype=torch.float32).to(DEVICE)

    return frames_gpu, speeds_gpu, actions_gpu, class_weights


def train():
    frames_gpu, speeds_gpu, actions_gpu, class_weights = load_data_to_gpu()
    num_samples = len(actions_gpu)
    print(f"数据集大小: {num_samples} 帧，Batch Size: {BATCH_SIZE}")

    model = FlappyNet().to(DEVICE)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scaler = torch.cuda.amp.GradScaler()

    for epoch in range(EPOCHS):
        model.train()

        # === 核心优化 2：将统计变量放在 GPU 上，避免 CPU-GPU 频繁同步 ===
        total_loss_gpu = torch.tensor(0.0, device=DEVICE)
        correct_gpu = torch.tensor(0, device=DEVICE)

        start_time = time.time()
        indices = torch.randperm(num_samples, device=DEVICE)

        for i in range(0, num_samples, BATCH_SIZE):
            batch_idx = indices[i:i + BATCH_SIZE]

            # 直接切片，不需要 .float() 或者除以 255
            img = frames_gpu[batch_idx]
            spd = speeds_gpu[batch_idx]
            act = actions_gpu[batch_idx]

            optimizer.zero_grad()

            with torch.cuda.amp.autocast():
                out = model(img, spd)
                loss = criterion(out, act)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            # 累加依然在 GPU 上进行，没有 .item() 打断
            total_loss_gpu += loss.detach()
            correct_gpu += (torch.argmax(out, dim=1) == act).sum()

        # === 核心优化 3：所有循环结束后，只同步一次数据到 CPU ===
        acc = correct_gpu.item() / num_samples * 100
        avg_loss = total_loss_gpu.item() / (num_samples // BATCH_SIZE + 1)

        print(
            f"Epoch [{epoch + 1}/{EPOCHS}] Loss: {avg_loss:.4f}, Acc: {acc:.2f}%, Time: {time.time() - start_time:.1f}s")

    torch.save(model.state_dict(), "flappy_ai.pth")
    print("训练完成！仅权重已保存至 flappy_ai.pth。")


if __name__ == '__main__':
    train()