import numpy as np
import os
from PIL import Image


def export_frames(npz_path, num_frames=10):
    if not os.path.exists(npz_path):
        print(f"找不到文件: {npz_path}")
        return

    # 读取数据
    data = np.load(npz_path)
    frames = data['frames']
    actions = data['actions']

    # 创建一个文件夹来存图片
    save_dir = "data/view_images"
    os.makedirs(save_dir, exist_ok=True)

    print(f"总共有 {len(frames)} 帧，正在导出前 {num_frames} 帧到 {save_dir} ...")

    # 导出图片
    for i in range(min(num_frames, len(frames))):
        # frames[i] 的 shape 是 (80, 160)
        img_array = frames[i]

        # 如果是 uint8 灰度图，直接用 PIL 存
        # 如果之前没加 astype(uint8)，可能这里会因为数据格式报错
        if img_array.dtype != np.uint8:
            img_array = img_array.astype(np.uint8)

        img = Image.fromarray(img_array, mode='L')  # 'L' 代表灰度图

        # 保存，文件名带上动作标签，方便你分析
        action_str = "Jump" if actions[i] == 1 else "NoJump"
        img_name = f"{save_dir}/frame_{i:03d}_{action_str}.png"
        img.save(img_name)


if __name__ == '__main__':
    # 替换成你的 npz 文件路径
    npz_file = "data/train_data_speed1_bird1.npz"
    export_frames(npz_file, num_frames=2000)