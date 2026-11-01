from ui_ai import ui
from game import game

if __name__ == '__main__':
    dif, bird_num,is_ai = ui()
    speed=1
    if dif=="新手":
        speed=3
    elif dif=="简单":
        speed=7
    elif dif=="普通":
        speed=10
    elif dif=="困难":
        speed=15
    else:
        speed=20
    game(speed,bird_num,is_ai)