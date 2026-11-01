'''
AI完成，帮我把训练和使用分开了，
并且分离了主函数内AI部分代码，
使得游戏和AI分离的开一点
'''
import torch
import torch.nn as nn
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
class FlappyNet(nn.Module):
    def __init__(self):
        super().__init__()
        # 图像特征提取 (输入 1 通道灰度图)
        self.cnn = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Flatten()
        )
        # 速度特征提取
        self.fc_speed = nn.Sequential(
            nn.Linear(2, 16), nn.ReLU()
        )
        # 融合层 (6400是图像展平后的维度，16是速度维度)
        # 融合层 (12800是图像展平后的维度，16是速度维度)
        self.fusion = nn.Sequential(
            nn.Linear(12800 + 16, 128), nn.ReLU(),
            nn.Linear(128, 2)
        )

    def forward(self, img, speed):
        feat_img = self.cnn(img)
        feat_speed = self.fc_speed(speed)
        combined = torch.cat((feat_img, feat_speed), dim=1)
        return self.fusion(combined)