import os
import mss
import cv2
import win32api
import win32gui
import win32con
import numpy as np
from time import time
from time import sleep
from enum import Enum

sct = mss.mss()

# Constants
fps_time = time()
nox_window = None

# Threshold
DEFAULT_THRESHOLD = .80
AUTO_THRESHOLD = .90

# Box Drawing
BOX_COLOR = (0, 255, 0)
BOX_BORDER_WIDTH = 2

# Target Images
chat_btn = cv2.imread('assets/chat_btn.png')
go_btn = cv2.imread('assets/go_btn.png')
auto_battle_off_btn = cv2.imread('assets/auto_battle_off_btn.png')
back_btn = cv2.imread('assets/back_btn.png')
battle_btn = cv2.imread('assets/battle_btn.png')
challenge_btn = cv2.imread('assets/challenge_btn.png')
confirm_btn = cv2.imread('assets/confirm_btn.png')
leave_btn = cv2.imread('assets/leave_btn.png')
retry_btn = cv2.imread('assets/retry_btn.png')
not_now_btn = cv2.imread('assets/not_now_btn.png')
unread_btn = cv2.imread('assets/unread_btn.png')
tap_to_continue_btn = cv2.imread('assets/tap_to_continue_btn.png')
ripple_dimension_dhalia_btn = cv2.imread(
    'assets/ripple_dimension_dhalia_btn.png')
ripple_dimension_dhalia_alt_btn = cv2.imread(
    'assets/ripple_dimension_dhalia_alt_btn.png')
ripple_dimension_ye_suhua_btn = cv2.imread(
    'assets/ripple_dimension_ye_suhua_btn.png')
ripple_dimension_ye_suhua_alt_btn = cv2.imread(
    'assets/ripple_dimension_ye_suhua_alt_btn.png')

# Game state

esper_name = ''


class RIPPLE_DIMENSION_STATE(Enum):
    FIND_RIPPLE_DIMENSION = {'name': 'FIND_RIPPLE_DIMENSION', 'buttons': [
        {'img': ripple_dimension_dhalia_btn, 'name': 'Ripple Dimension Dhalia',
            'threshold': DEFAULT_THRESHOLD, 'next': 'RIPPLE_DIMENSION_FOUND', 'esper': 'Dhalia', 'delay': None},
        {'img': ripple_dimension_dhalia_alt_btn, 'name': 'Ripple Dimension Dhalia Share',
            'threshold': DEFAULT_THRESHOLD, 'next': 'RIPPLE_DIMENSION_FOUND', 'esper': 'Dhalia', 'delay': None},
        {'img': ripple_dimension_ye_suhua_btn, 'name': 'Ripple Dimension Ye Suhua',
            'threshold': DEFAULT_THRESHOLD, 'next': 'RIPPLE_DIMENSION_FOUND', 'esper': 'Ye Suhua', 'delay': None},
        {'img': ripple_dimension_ye_suhua_alt_btn, 'name': 'Ripple Dimension Ye Suhua Share',
            'threshold': DEFAULT_THRESHOLD, 'next': 'RIPPLE_DIMENSION_FOUND', 'esper': 'Ye Suhua', 'delay': None},
        {'img': unread_btn, 'name': 'Unread Button',
            'threshold': DEFAULT_THRESHOLD, 'next': None, 'esper': 'Ye Suhua', 'delay': None}
    ]}
    RIPPLE_DIMENSION_FOUND = {'name': 'RIPPLE_DIMENSION_FOUND', 'buttons': [
        {'img': go_btn, 'name': 'Go Button', 'threshold': DEFAULT_THRESHOLD,
            'next': 'CHALLENGE_RIPPLE_DIMENSION', 'delay': None},
        {'img': leave_btn, 'name': 'Leave Button', 'threshold': DEFAULT_THRESHOLD,
            'next': 'FIND_RIPPLE_DIMENSION', 'delay': None},
    ]}
    CHALLENGE_RIPPLE_DIMENSION = {'name': 'CHALLENGE_RIPPLE_DIMENSION', 'buttons': [
        {'img': challenge_btn, 'name': 'Challenge Button', 'threshold': DEFAULT_THRESHOLD,
            'next': 'BATTLE_RIPPLE_DIMENSION', 'delay': None}
    ]}
    BATTLE_RIPPLE_DIMENSION = {'name': 'BATTLE_RIPPLE_DIMENSION', 'buttons': [
        {'img': battle_btn, 'name': 'Battle Button',
            'threshold': DEFAULT_THRESHOLD, 'next': 'BATTLING', 'delay': None}
    ]}
    BATTLING = {'name': 'BATTLING', 'buttons': [
        {'img': auto_battle_off_btn, 'name': 'Activate Auto',
            'threshold': AUTO_THRESHOLD, 'next': None, 'delay': None},
        {'img': retry_btn, 'name': 'Retry Button',
            'threshold': DEFAULT_THRESHOLD, 'next': None, 'delay': None},
        {'img': confirm_btn, 'name': 'Confirm Button',
         'threshold': DEFAULT_THRESHOLD, 'next': 'BACK', 'delay': None}
    ]}
    BACK = {'name': 'BACK', 'buttons': [
        {'img': back_btn, 'name': 'Back Button',
            'threshold': DEFAULT_THRESHOLD, 'next': 'CHAT', 'delay': 2}
    ]}
    # BACK_AGAIN = {'name': 'BACK', 'buttons': [
    #     {'img': back_btn, 'name': 'Back Button',
    #      'threshold': DEFAULT_THRESHOLD, 'next': 'CHAT', 'delay': 2}
    # ]}
    CHAT = {'name': 'CHAT', 'buttons': [
        {'img': chat_btn, 'name': 'Chat Button', 'threshold': DEFAULT_THRESHOLD,
            'next': 'FIND_RIPPLE_DIMENSION', 'delay': None}
    ]}


game_state = None
nox_player_img = None


# Get Window by name


def get_window(window_name):
    global nox_window
    nox_window = win32gui.FindWindow(None, window_name)

# Get window dimensions


def get_window_dimensions(window):
    rect = win32gui.GetWindowRect(window)
    return [rect[0], rect[1], (rect[2] - rect[0]), (rect[3] - rect[1])]

# Match and image with another


def match_image(compare_img, target_img):
    """Return the min max value and location of the matched image.

    @param compare_img Image where the search is running. It must be 8-bit or 32-bit floating-point..
    @param target_img Searched image. It must be not greater than the source image.

    @returns [min_val, max_val, min_loc, max_loc]
    """
    match = cv2.matchTemplate(compare_img, target_img, cv2.TM_CCOEFF_NORMED)
    return cv2.minMaxLoc(match)

# Get image dimensions (width and height)


def get_img_dimension(image):
    """Return given image x and y dimensions.

    @param image The image.

    @returns Tuple with x and y dimensions ([x, y]).
    """
    return [image.shape[1], image.shape[0]]

# Check if accuracy is above threshold


def is_accuracy_above_threshold(accuracy, threshold):
    """Check if the accuracy is above or equal the given threshold.

    @param accuracy The accuracy to test.
    @param threshold The threshold to test.

    @returns True if accuracy above or equal threshold and False if not.
    """
    return accuracy >= threshold

# Print a portion of the monitor


def get_monitor_segment_img(dimensions):
    """Return the image of a portion of the screen

    @param dimensions The dimensions of the portion of the screen.

    @returns The image with the portion of the screen.
    """
    img = np.array(sct.grab(dimensions))
    img = img[:, :, :3]
    return img.copy()

# Open a windows with the image


def open_image(title, image):
    """Open a window with the given title with the given image.

    @param title Window title.
    @param image The image.
    """
    cv2.imshow(title, image)
    cv2.waitKey(1)

# Draw rectangle in image


def draw_rect(image, start_vertex, end_vertex, rect_color, rect_border_width):
    """Drawn a rectangle on the image on a specific location.

    @param image The image.
    @param start_vertex Initial vertex of the rectangle.
    @param end_vertex Ending vertex of the rectangle.
    @param color The color in (0, 255, 255) format.
    @param rect_border_width Size of the rect border in pixels.
    """
    cv2.rectangle(image, start_vertex, end_vertex,
                  rect_color, rect_border_width)

# Click the image found on scree


def click_img_on_window(img, img_loc):
    """Click on the image found on window

    @param img The image to click.
    @param img_loc Tuple with image x and y location.
    """
    w, h = get_img_dimension(img)
    draw_rect(nox_player_img, img_loc,
              (img_loc[0] + w, img_loc[1] + h), BOX_COLOR, BOX_BORDER_WIDTH)

    x = img_loc[0] + (w//2)
    y = img_loc[1] + (h//2)

    lParam = win32api.MAKELONG(x, y)
    win32gui.SendMessage(nox_window, win32con.WM_LBUTTONDOWN,
                         win32con.MK_LBUTTON, lParam)
    win32gui.SendMessage(nox_window, win32con.WM_LBUTTONUP, None, lParam)

# Find image on the specific game state


def find_and_click_img(state):
    """Find image on the specific game state.

    @param state The game state with the image to find and threshold.
    """
    img = state['img']
    threshold = state['threshold']
    button_name = state['name']
    _, max_val, _, max_loc = match_image(nox_player_img, img)

    print_accuracy_image(max_val, button_name)

    if is_accuracy_above_threshold(max_val, threshold):
        click_img_on_window(img, max_loc)
        update_state(state)
        # open_image('Dislyte', nox_player_img)

# Update game state


def update_state(state):
    global game_state

    if state['delay'] is not None:
        sleep(state['delay'])

    if state['next'] is not None:
        game_state = RIPPLE_DIMENSION_STATE[state['next']]

# Print FPS


def print_fps():
    """Print FPS on console
    """
    global fps_time
    os.system('clear')
    try:
        print('FPS: %.0f' % (1 / (time() - fps_time)))
    except:
        None
    fps_time = time()

# Print game state


def print_game_state():
    """Print game state on console
    """
    print("Game State:", game_state.name)

# Print accuracy of image


def print_accuracy_image(accuracy, button_name):
    """Print accuracy of image
    """
    print("Accuracy of", button_name, ": %.2f%%" % (accuracy*100))

# Get Bluestacks windows image


def get_nox_player_window_img():
    global nox_player_img

    x, y, w, h = get_window_dimensions(nox_window)
    dimensions = {'left': x, 'top': y, 'width': w, 'height': h}
    nox_player_img = get_monitor_segment_img(dimensions)


# Execute actual state automation


def execute_state(state):
    for button in state.value['buttons']:
        find_and_click_img(button)

# Find Ripple Dimension


def automate_ripple_dimension():
    global game_state
    game_state = RIPPLE_DIMENSION_STATE.FIND_RIPPLE_DIMENSION
    while True:
        print_fps()
        print_game_state()
        get_nox_player_window_img()

        execute_state(game_state)


# Script Start
get_window("NoxPlayer")

automate_ripple_dimension()
