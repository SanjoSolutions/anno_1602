from enum import IntEnum

from a import A
from mss import mss
from ctypes import *
import pyautogui
import time


class Rect(Structure):
    _fields_ = [
        ('left', c_long),
        ('top', c_long),
        ('right', c_long),
        ('bottom', c_long),
    ]


class MouseAction(IntEnum):
    Move = 0
    PrimaryClickAt = 1
    SecondaryClick = 2


class Environment:
    def __init__(self):
        self.screenshotter = mss()
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
        if type == MouseAction.Move:
            position = action[1]
            x, y = self.action_position_to_mouse_position(position)
            pyautogui.moveTo(
                x=x,
                y=y,
                duration=0.1
            )
        elif type == MouseAction.PrimaryClickAt:
            position = action[1]
            x, y = self.action_position_to_mouse_position(position)
            pyautogui.click(
                x=x,
                y=y
            )
        elif type == MouseAction.SecondaryClick:
            pyautogui.click(button='right')
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
            self.generate_mouse_move_actions() |
            self.generate_primary_mouse_click_at_actions() |
            self.generate_secondary_mouse_click_actions()
        )

    def generate_mouse_move_actions(self):
        actions = set()
        for y in range(self.window['height']):
            for x in range(self.window['width']):
                action = (MouseAction.Move, (x, y))
                actions.add(action)
        return actions

    def generate_primary_mouse_click_at_actions(self):
        actions = set()
        for y in range(self.window['height']):
            for x in range(self.window['width']):
                action = (MouseAction.PrimaryClickAt, (x, y))
                actions.add(action)
        return actions

    def generate_secondary_mouse_click_actions(self):
        actions = set()
        action = (MouseAction.SecondaryClick,)
        actions.add(action)
        return actions

    def get_state(self):
        screenshot = self.screenshotter.grab(self.window)
        pixels = tuple(screenshot.pixels)
        return pixels


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


state_to_metric_value = dict()


def determine_metric_value(state):
    return state_to_metric_value[state]


environment = Environment()
environment.get_state()
database = Database()
a = A()
a.explore(environment, database, 1000)
print('explored states: ' + str(len(database.state_to_explored_actions)))

# environment.reset()
# path_to_outcome = a.evaluate(environment, database, determine_metric_value)
# print(path_to_outcome)