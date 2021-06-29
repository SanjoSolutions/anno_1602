import random
from enum import IntEnum

from mss import mss
from pymem import Pymem

from ctypes import *
import pyautogui
import time
import cv2 as cv
import numpy as np

from tensorflow.keras.layers import Dense, concatenate, Conv2D, Flatten
from tensorflow.keras.models import Model
from tensorflow.keras import Input
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.losses import MeanSquaredError
import tensorflow as tf
import os


os.environ["CUDA_VISIBLE_DEVICES"] = "-1"


FRAME_WIDTH = 160
FRAME_HEIGHT = 120
NUMBER_OF_COLOR_CHANNELS = 1


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
    Idle = 3


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
        self.actions = None

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
        elif type == ActionType.Idle:
            pass
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
        if self.actions is None:
            self.actions = (
                self.generate_3d_space_primary_mouse_click_at_actions() |
                self.generate_minimap_primary_mouse_click_at_actions() |
                self.generate_menu_actions() |
                self.generate_submenu_actions() |
                self.generate_key_press_actions() |
                {(ActionType.Idle,)}
            )
        return self.actions

    def generate_3d_space_primary_mouse_click_at_actions(self):
        return self.generate_primary_mouse_click_at_actions(
            (0, 0, 120, 115),
            (4, 4)
        )

    def generate_minimap_primary_mouse_click_at_actions(self):
        return self.generate_primary_mouse_click_at_actions(
            (125, 3, 30, 25),
            (1, 1)
        )

    def generate_menu_actions(self):
        return {
            (ActionType.PrimaryMouseClickAt, (127, 48)),  # build
            # (ActionType.PrimaryMouseClickAt, (136, 48)),  # battle
            (ActionType.PrimaryMouseClickAt, (144, 48)),  # status
        }

    def generate_submenu_actions(self):
        return (
            self.generation_status_menu_actions() |
            self.generate_build_menu_actions() |
            self.generate_ship_actions()
        )

    def generation_status_menu_actions(self):
        return {
            (ActionType.PrimaryMouseClickAt, (152, 111)),  # diplomacy
        }

    def generate_build_menu_actions(self):
        build_menu_positions = [
            (127, 103),  # 1
            (136, 103),  # 2
            (144, 103),  # 3
            (153, 103),  # 4
            (127, 113),  # 5
            (136, 113),  # 6
            (144, 113),  # 7
            (153, 113),  # 8
        ]

        build_menu_actions = set(
            [
                (ActionType.PrimaryMouseClickAt, position)
                for position
                in build_menu_positions
            ]
        )

        build_submenu_actions = set().union(
            *[
                self.generate_build_submenu_actions(position)
                for position
                in build_menu_positions
            ]
        )

        return (
            build_menu_actions |
            build_submenu_actions
        )

    def generate_build_submenu_actions(self, build_menu_item_position):
        BUILD_MENU_ITEM_WIDTH = 8
        BUILD_MENU_ITEM_HEIGHT = 10
        BUILD_SUBMENU_BETWEEN_ROW_SPACE = 2
        BUILD_SUBMENU_BETWEEN_COLUMN_SPACE = 1
        BUILD_SUBMENU_ITEM_WIDTH = 8
        BUILD_SUBMENU_ITEM_HEIGHT = 7

        build_menu_item_x, build_menu_item_y = build_menu_item_position

        NUMBER_OF_ROWS = 4
        NUMBER_OF_COLUMNS = 4

        ROW_DELTA = BUILD_SUBMENU_BETWEEN_ROW_SPACE + BUILD_SUBMENU_ITEM_HEIGHT
        COLUMN_DELTA = BUILD_SUBMENU_BETWEEN_COLUMN_SPACE + BUILD_SUBMENU_ITEM_WIDTH

        actions = set()

        for row in range(0, NUMBER_OF_ROWS, 1):
            y = build_menu_item_y - 0.5 * BUILD_MENU_ITEM_HEIGHT - BUILD_SUBMENU_BETWEEN_ROW_SPACE - 0.5 * BUILD_SUBMENU_ITEM_HEIGHT - \
                (NUMBER_OF_ROWS - 1) * ROW_DELTA + \
                row * ROW_DELTA
            for column in range(0, NUMBER_OF_COLUMNS, 1):
                x = 121 + BUILD_SUBMENU_BETWEEN_COLUMN_SPACE + 0.5 * BUILD_SUBMENU_ITEM_WIDTH + \
                    column * COLUMN_DELTA
                action = (ActionType.PrimaryMouseClickAt, (x, y))
                actions.add(action)

        return actions

    def generate_ship_actions(self):
        return self.generate_ship_status_actions()

    def generate_ship_status_actions(self):
        return {
            (ActionType.PrimaryMouseClickAt, (127, 75)),  # explore island
            (ActionType.PrimaryMouseClickAt, (130, 94)),  # build warehouse / exchange goods with warehouse
            (ActionType.PrimaryMouseClickAt, (128, 104)),
            (ActionType.PrimaryMouseClickAt, (136, 104)),
            (ActionType.PrimaryMouseClickAt, (144, 104)),
            (ActionType.PrimaryMouseClickAt, (152, 104)),
            (ActionType.PrimaryMouseClickAt, (128, 86)),
            (ActionType.PrimaryMouseClickAt, (133, 86)),
            (ActionType.PrimaryMouseClickAt, (137, 86)),
            (ActionType.PrimaryMouseClickAt, (141, 86)),
            (ActionType.PrimaryMouseClickAt, (146, 86)),
            (ActionType.PrimaryMouseClickAt, (153, 86)),
            (ActionType.PrimaryMouseClickAt, (127, 77)),
            (ActionType.PrimaryMouseClickAt, (136, 77)),
            (ActionType.PrimaryMouseClickAt, (144, 77)),
            (ActionType.PrimaryMouseClickAt, (153, 77)),
            (ActionType.PrimaryMouseClickAt, (128, 69)),
            (ActionType.PrimaryMouseClickAt, (136, 69)),
            (ActionType.PrimaryMouseClickAt, (144, 69)),
            (ActionType.PrimaryMouseClickAt, (153, 69)),
        }

    def generate_primary_mouse_click_at_actions(self, area, delta):
        actions = set()
        for y in range(area[1], area[1] + area[3], delta[1]):
            for x in range(area[0], area[0] + area[2], delta[0]):
                action = (ActionType.PrimaryMouseClickAt, (x, y))
                actions.add(action)
        return actions

    def generate_key_press_actions(self):
        # see manual, Appendix D (page 69)
        actions = {
            # (ActionType.KeyPress, 'f2'),
            # (ActionType.KeyPress, 'f3'),
            # (ActionType.KeyPress, 'f4'),
            (ActionType.KeyPress, 'f5'),
            (ActionType.KeyPress, 'f6'),
            (ActionType.KeyPress, 'f7'),
            # (ActionType.KeyPress, 'z'),
            # (ActionType.KeyPress, 'x'),
            # (ActionType.KeyPress, 'o'),
            (ActionType.KeyPress, 'd'),
            # (ActionType.KeyPress, 'l'),
            (ActionType.KeyPress, 'b'),
            # (ActionType.KeyPress, 'k'),  # can be uncommented at some point
            (ActionType.KeyPress, 'i'),
            # (ActionType.KeyPress, 'f'),
            # (ActionType.KeyPress, 'w'),  # can be uncommented at some point
            (ActionType.KeyPress, 'j'),
            (ActionType.KeyPress, 'h'),
            # (ActionType.KeyPress, 'pause'),
            # (ActionType.KeyPress, 'esc'),
            # (ActionType.KeyPress, 's'),  # can be uncommented at some point
            # (ActionType.KeyPress, 'c'),  # can be uncommented at some point
            # (ActionType.KeyPress, ('ctrl', '1')),
            # (ActionType.KeyPress, ('ctrl', '2')),
            # (ActionType.KeyPress, ('ctrl', '3')),
            # (ActionType.KeyPress, ('ctrl', '4')),
            # (ActionType.KeyPress, ('ctrl', '5')),
            # (ActionType.KeyPress, ('ctrl', '6')),
            # (ActionType.KeyPress, ('ctrl', '7')),
            # (ActionType.KeyPress, ('ctrl', '8')),
            # (ActionType.KeyPress, ('ctrl', '9')),
            # (ActionType.KeyPress, '1'),
            # (ActionType.KeyPress, '2'),
            # (ActionType.KeyPress, '3'),
            # (ActionType.KeyPress, '4'),
            # (ActionType.KeyPress, '5'),
            # (ActionType.KeyPress, '6'),
            # (ActionType.KeyPress, '7'),
            # (ActionType.KeyPress, '8'),
            # (ActionType.KeyPress, '9'),
            # (ActionType.KeyPress, 'f8'),
            # (ActionType.KeyPress, 'f9'),
            # (ActionType.KeyPress, 'f10'),
            # (ActionType.KeyPress, 'f11'),
            # (ActionType.KeyPress, 'f12'),
        }
        return actions

    def get_state(self):
        screenshot = self.screenshotter.grab(self.window)
        pixels = np.array(screenshot.pixels, dtype=np.float32)
        pixels = cv.cvtColor(pixels, cv.COLOR_RGB2GRAY)
        pixels = cv.resize(pixels, (FRAME_WIDTH, FRAME_HEIGHT))
        pixels /= 255.0
        pixels = tuple(map(tuple, pixels))

        state = pixels

        return state

    def get_score(self):
        modules = list(self.process.list_modules())
        module = next(module for module in modules if module.name == 'Dll.dll')
        module_base_address = module.lpBaseOfDll
        score_address = module_base_address + 0x1C2D4
        return self.process.read_int(score_address)


def main():
    environment = Environment()

    convolutional_model = create_convolutional_model(FRAME_WIDTH, FRAME_HEIGHT)
    state_to_action_value_models, state_to_action_values_model = create_state_to_action_value_models(
        environment,
        FRAME_WIDTH,
        FRAME_HEIGHT,
        convolutional_model
    )

    actions = list(environment.get_available_actions())

    print('Number of actions: ' + str(len(actions)))

    previous_score = environment.get_score()

    state = environment.get_state()

    while True:
        action = choose_action(environment, state_to_action_values_model, state)
        environment.do_action(actions[action])
        score = environment.get_score()
        reward = score - previous_score
        print(actions[action], score, previous_score, reward)
        after_state = environment.get_state()
        update_value_prediction_model(
            state_to_action_value_models[action],
            state_to_action_values_model,
            state,
            reward,
            after_state
        )
        previous_score = score
        state = after_state


def create_convolutional_model(frame_width, frame_height):
    image_input_layer = Input(shape=(frame_height, frame_width, NUMBER_OF_COLOR_CHANNELS))
    convolution_layer_1 = Conv2D(
        filters=32,
        kernel_size=(8, 8),
        strides=4,
        activation='relu',
    )(image_input_layer)
    convolution_layer_2 = Conv2D(
        filters=64,
        kernel_size=(4, 4),
        strides=2,
        activation='relu',
    )(convolution_layer_1)
    convolution_layer_3 = Conv2D(
        filters=64,
        kernel_size=(3, 3),
        strides=1,
        activation='relu',
    )(convolution_layer_2)
    return Model(inputs=image_input_layer, outputs=convolution_layer_3)


def create_state_to_action_value_models(environment, frame_width, frame_height, convolutional_model):
    number_of_actions = len(environment.get_available_actions())
    image_input_layer = Input(shape=(frame_height, frame_width, NUMBER_OF_COLOR_CHANNELS))
    convolutional_layers = convolutional_model(image_input_layer)
    flatten_convolution_layers = Flatten()(convolutional_layers)
    hidden_layer_1 = Dense(512, activation='relu')(flatten_convolution_layers)
    hidden_layer_2 = Dense(512, activation='relu')(hidden_layer_1)
    output_layers = [
        Dense(1)(hidden_layer_2)
        for index
        in range(number_of_actions)
    ]
    state_to_action_value_prediction_models = [
        Model(inputs=image_input_layer, outputs=output_layers[index])
        for index
        in range(number_of_actions)
    ]
    for model in state_to_action_value_prediction_models:
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss=MeanSquaredError()
        )
    action_values_layer = concatenate(output_layers)
    state_to_action_values_predication_model = Model(inputs=image_input_layer, outputs=action_values_layer)
    state_to_action_values_predication_model.compile(
        optimizer=Adam(learning_rate=0.001),
        loss=MeanSquaredError()
    )
    return state_to_action_value_prediction_models, state_to_action_values_predication_model


alpha = 0.9
gamma = 0.9
epsilon = 0.1


def choose_action(environment, state_to_action_values_model, state):
    actions = environment.get_available_actions()
    if random.random() <= epsilon:
        return random.randrange(0, len(actions))
    else:
        return determine_action(state_to_action_values_model, state)


def update_value_prediction_model(state_to_action_value_model, state_to_action_values_model, state, reward, after_state):
    states = np.array([state])
    current_prediction = state_to_action_value_model(states).numpy()[0][0]
    target = current_prediction + \
        alpha * \
            (reward + \
             gamma * determine_value_of_highest_value_action(state_to_action_values_model, after_state) - \
             current_prediction)
    y = np.array([target])
    state_to_action_value_model.fit(
        x=states,
        y=y
    )


def determine_action(state_to_action_values_model, state):
    action = int(tf.math.argmax(state_to_action_values_model(np.array([state]))[0]).numpy())
    return action


def determine_value_of_highest_value_action(state_to_action_values_model, state):
    value = float(tf.math.reduce_max(state_to_action_values_model(np.array([state]))[0]).numpy())
    return value


def action_to_embedding(environment, action):
    actions = environment.get_available_actions()
    number_of_actions = len(actions)
    embedding = [0] * number_of_actions
    embedding[action] = 1
    return tuple(embedding)


if __name__ == '__main__':
    main()
