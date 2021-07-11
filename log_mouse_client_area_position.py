import pyautogui
import time

from other.main import Anno1602

anno1602 = Anno1602()

while True:
    left, top = anno1602.get_window_client_area_position()
    mouse_position = pyautogui.position()
    position = (
        mouse_position[0] - left,
        mouse_position[1] - top
    )
    print(position)
    time.sleep(1)
