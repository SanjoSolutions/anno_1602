import time

from other.play import determine_mouse_position

while True:
    mouse_position = determine_mouse_position()
    print(mouse_position)
    time.sleep(1)
