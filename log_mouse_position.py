import pyautogui
import time

from other.play import get_window_client_area_position

while True:
    left, top = get_window_client_area_position()
    mouse_position = pyautogui.position()
    position = (
        mouse_position[0] - left,
        mouse_position[1] - top
    )
    print(position)
    time.sleep(1)
