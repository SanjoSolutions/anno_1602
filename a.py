import os
import pickle
import sys
from enum import IntEnum

from mss import mss
from pymem import Pymem

from a import A
from ctypes import *
import pyautogui
import time
import cv2 as cv
import numpy as np


class Rect(Structure):
    _fields_ = [
        ('left', c_long),
        ('top', c_long),
        ('right', c_long),
        ('bottom', c_long),
    ]


class ActionType(IntEnum):
    PrimaryMouseClickAt = 1
    KeyPress = 2


class Environment:
    def __init__(self):
        self.screenshotter = mss()
        self.process = Pymem('1602.exe')
        self.hwnd = cdll.user32.FindWindowW(None, 'Anno 1602')
        rect = Rect()
        succeeded = cdll.user32.GetWindowRect(self.hwnd, pointer(rect))
        title_bar_height = 32
        padding_left = 8
        padding_right = 8
        padding_bottom = 9
        self.window = {
            'left': rect.left + padding_left,
            'top': rect.top + title_bar_height,
            'width': rect.right - rect.left - padding_left - padding_right,
            'height': rect.bottom - rect.top - title_bar_height - padding_bottom,
        }

    def do_action(self, action):
        if self.is_done():
            raise AssertionError(
                '"do_action" was called when environment was done. ' +
                'Please make sure to reset the environment first.'
            )
        while windll.user32.GetForegroundWindow() != self.hwnd:
            time.sleep(1)
        type = action[0]
        if type == ActionType.PrimaryMouseClickAt:
            position = action[1]
            x, y = self.action_position_to_mouse_position(position)
            pyautogui.click(
                x=x,
                y=y
            )
        elif type == ActionType.KeyPress:
            keys = action[1]
            if isinstance(keys, str):
                keys = (keys,)
            pyautogui.hotkey(*keys)
        else:
            raise ValueError('Unexpected action type: ' + str(type))

    def action_position_to_mouse_position(self, action_position):
        x, y = action_position
        mouse_position = (
            self.window['left'] + x,
            self.window['top'] + y
        )
        return mouse_position

    def reset(self):
        pass

    def is_done(self):
        return False

    def get_available_actions(self):
        return (
            self.generate_primary_mouse_click_at_actions() |
            self.generate_key_press_actions()
        )

    def generate_primary_mouse_click_at_actions(self):
        actions = set()
        for y in range(0, self.window['height'], 10):
            for x in range(0, self.window['width'], 10):
                action = (ActionType.PrimaryMouseClickAt, (x, y))
                actions.add(action)
        return actions

    def generate_key_press_actions(self):
        # see manual, Appendix D (page 69)
        actions = {
            (ActionType.KeyPress, 'f2'),
            (ActionType.KeyPress, 'f3'),
            (ActionType.KeyPress, 'f4'),
            (ActionType.KeyPress, 'f5'),
            (ActionType.KeyPress, 'f6'),
            (ActionType.KeyPress, 'f7'),
            (ActionType.KeyPress, 'z'),
            (ActionType.KeyPress, 'x'),
            (ActionType.KeyPress, 'o'),
            (ActionType.KeyPress, 'd'),
            (ActionType.KeyPress, 'l'),
            (ActionType.KeyPress, 'b'),
            (ActionType.KeyPress, 'k'),
            (ActionType.KeyPress, 'i'),
            (ActionType.KeyPress, 'f'),
            (ActionType.KeyPress, 'w'),
            (ActionType.KeyPress, 'j'),
            (ActionType.KeyPress, 'h'),
            (ActionType.KeyPress, 'pause'),
            (ActionType.KeyPress, 'esc'),
            (ActionType.KeyPress, 's'),
            (ActionType.KeyPress, 'c'),
            (ActionType.KeyPress, ('ctrl', '1')),
            (ActionType.KeyPress, ('ctrl', '2')),
            (ActionType.KeyPress, ('ctrl', '3')),
            (ActionType.KeyPress, ('ctrl', '4')),
            (ActionType.KeyPress, ('ctrl', '5')),
            (ActionType.KeyPress, ('ctrl', '6')),
            (ActionType.KeyPress, ('ctrl', '7')),
            (ActionType.KeyPress, ('ctrl', '8')),
            (ActionType.KeyPress, ('ctrl', '9')),
            (ActionType.KeyPress, '1'),
            (ActionType.KeyPress, '2'),
            (ActionType.KeyPress, '3'),
            (ActionType.KeyPress, '4'),
            (ActionType.KeyPress, '5'),
            (ActionType.KeyPress, '6'),
            (ActionType.KeyPress, '7'),
            (ActionType.KeyPress, '8'),
            (ActionType.KeyPress, '9'),
            (ActionType.KeyPress, 'f8'),
            (ActionType.KeyPress, 'f9'),
            (ActionType.KeyPress, 'f10'),
            (ActionType.KeyPress, 'f11'),
            (ActionType.KeyPress, 'f12'),
        }
        return actions

    def get_state(self):
        screenshot = self.screenshotter.grab(self.window)
        pixels = np.array(screenshot.pixels, dtype=np.float32)
        pixels = cv.cvtColor(pixels, cv.COLOR_RGB2GRAY)
        pixels = cv.resize(pixels, (80, 60))
        pixels /= 255.0
        pixels = tuple(map(tuple, pixels))

        gold = self.process.read_int(0x005B7684)
        values = (gold,)

        state = pixels + (values,)

        return state


class Database:
    def __init__(self):
        self.state_to_explored_actions = dict()
        self.state_and_action_to_state = dict()
        self.state_to_state_and_action_pairs_that_lead_to_it = dict()
        self.state_to_unexplored_actions_count = dict()

    def store(self, state_before_action, action, state_after_action):
        state_before_action = tuple(state_before_action)
        state_after_action = tuple(state_after_action)
        if state_before_action not in self.state_to_explored_actions:
            self.state_to_explored_actions[state_before_action] = set()
        self.state_to_explored_actions[state_before_action].add(action)

        self.state_and_action_to_state[(state_before_action, action)] = \
            state_after_action

        if state_after_action not in self.state_to_state_and_action_pairs_that_lead_to_it:
            self.state_to_state_and_action_pairs_that_lead_to_it[state_after_action] = set()
        self.state_to_state_and_action_pairs_that_lead_to_it[state_after_action].add(
            (state_before_action, action)
        )

    def query_explored_actions(self, state):
        state = tuple(state)
        return self.state_to_explored_actions[state] if state in self.state_to_explored_actions else set()

    def query_action_that_lead_to_state_with_highest_metric_value(self, state, determine_metric_value):
        state = tuple(state)
        explored_actions = self.state_to_explored_actions[state]
        return max(
            determine_metric_value(self.state_and_action_to_state[(state, action)])
            for action
            in explored_actions
        )

    def query_state_with_highest_metric_value(self, determine_metric_value):
        return max(self.state_and_action_to_state.values(), key=lambda state: determine_metric_value(state))

    def query_state_and_action_pairs_which_lead_to_state(self, state):
        state = tuple(state)
        return (
            self.state_to_state_and_action_pairs_that_lead_to_it[state]
            if state in self.state_to_state_and_action_pairs_that_lead_to_it
            else set()
        )

    def store_unexplored_actions_count(self, state, unexplored_actions_count):
        state = tuple(state)
        self.state_to_unexplored_actions_count[state] = unexplored_actions_count

    def query_total_known_unexplored_actions_count(self, state):
        visited_states = set()
        state = tuple(state)
        count = 0
        states = [state]
        while len(states) >= 1:
            next_states = []
            for state in states:
                if state not in visited_states:
                    unexplored_actions_count = self.query_unexplored_actions_count(state)
                    if unexplored_actions_count is not None:
                        count += unexplored_actions_count
                    if state in self.state_to_explored_actions:
                        actions = self.state_to_explored_actions[state]
                        next_states += [self.state_and_action_to_state[(state, action)] for action in actions]
                    visited_states.add(state)
            states = next_states
        return count

    def query_unexplored_actions_count(self, state):
        return (
            self.state_to_unexplored_actions_count[state]
            if state in self.state_to_unexplored_actions_count
            else None
        )

    def query_state(self, state, action):
        state = tuple(state)
        state_and_action_pair = (state, action)
        return (
            self.state_and_action_to_state[state_and_action_pair]
            if state_and_action_pair in self.state_and_action_to_state
            else None
        )


def determine_metric_value(state):
    return state[-1][0]


def save_database(database):
    with open('database.pickle', 'wb') as file:
        pickle.dump(database, file, pickle.HIGHEST_PROTOCOL)


if __name__ == '__main__':
    environment = Environment()
    environment.get_state()
    database = Database()
    a = A()
    try:
        a.explore(environment, database, 10000)
        print('explored states: ' + str(len(database.state_to_explored_actions)))

        # environment.reset()
        path_to_outcome = a.evaluate(environment, database, determine_metric_value)
        print(path_to_outcome)
    except KeyboardInterrupt:
        print('Interrupted')

        save_database(database)

        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
