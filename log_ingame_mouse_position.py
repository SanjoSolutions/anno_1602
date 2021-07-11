import time
from other.main import Anno1602


anno1602 = Anno1602()

while True:
    mouse_position = anno1602.determine_mouse_position()
    print(mouse_position)
    time.sleep(1)
