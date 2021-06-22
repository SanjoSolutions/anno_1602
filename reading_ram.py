from pymem import Pymem
import time

process = Pymem('1602.exe')

from_address = 0x400000
to_address = 0x72e000
length = to_address - from_address


def read_memory():
    bytes = process.read_bytes(from_address, length)
    return bytes

start_time = time.time_ns()
bytes = read_memory()
end_time = time.time_ns()
duration = end_time - start_time
print('duration:', duration)
