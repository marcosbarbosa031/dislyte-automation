import os
import mss
import cv2
import win32api
import win32gui
import win32con
import numpy as np
from time import time
from enum import Enum

sct = mss.mss()

# Constants
fps_time = time()
nox_window = None

# Threshold
AUTO_THRESHOLD = .80
OK_THRESHOLD = .75
CONTINUE_THRESHOLD = .80
RETRY_THRESHOLD = .80
SKIP_THRESHOLD = .80
UPDATE_LIST_THRESHOLD = .99

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
ripple_dimension_dhalia_btn = cv2.imread(
    'assets/ripple_dimension_dhalia_btn.png')
ripple_dimension_ye_suhua_btn = cv2.imread(
    'assets/ripple_dimension_ye_suhua_btn.png')
ripple_dimension_ye_suhua_alt_btn = cv2.imread(
    'assets/ripple_dimension_ye_suhua_alt_btn.png')

# Game state


class GAME_STATES(Enum):
    BOT_STARTED = None
    FIND_RIPPLE_DIMENSION = {'name': 'Finding Ripple Dimension', 'buttons': [
        {'img': ripple_dimension_dhalia_btn, 'threshold': AUTO_THRESHOLD},
        {'img': ripple_dimension_ye_suhua_btn, 'threshold': AUTO_THRESHOLD}
    ]}
    # CLICKED_OK = {'name': 'Ok Button',
    #               'img': ok_btn_img, 'threshold': OK_THRESHOLD}
    # CLICKED_CONTINUE = {'name': 'Continue Button',
    #                     'img': continue_btn_img, 'threshold': CONTINUE_THRESHOLD}
    # CLICKED_RETRY = {'name': 'Retry Button',
    #                  'img': retry_btn_img, 'threshold': RETRY_THRESHOLD}
    # CLICKED_SKIP = { 'name': 'Skip Button', 'img': skip_btn_img, 'threshold': SKIP_THRESHOLD }
    # CLICKED_UPDATE_LIST = { 'name': 'Update List Button', 'img': update_list_btn_img, 'threshold': UPDATE_LIST_THRESHOLD }


game_state = GAME_STATES.BOT_STARTED


# Get Window by name
def get_window(window_name):
    global nox_window
    hWnd = win32gui.FindWindow(None, window_name)
    # The playable Nox window is the third child of the main window
    nox_window = win32gui.FindWindowEx(hWnd, win32gui.FindWindowEx(
        hWnd, win32gui.FindWindowEx(hWnd, None, None, None), None, None), None, None)

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

    img = state.value['img']
    threshold = state.value['threshold']
    button_name = state.value['name']
    _, max_val, _, max_loc = match_image(nox_player_img, img)

    print_accuracy_image(max_val, button_name)

    if is_accuracy_above_threshold(max_val, threshold):
        click_img_on_window(img, max_loc)
        update_state(state)
        # open_image('Dislyte', nox_player_img)

# Update game state


def update_state(state):
    global game_state
    game_state = state

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
    x, y, w, h = get_window_dimensions(nox_window)
    dimensions = {'left': x, 'top': y, 'width': w, 'height': h}
    return get_monitor_segment_img(dimensions)


# Script Start
get_window("NoxPlayer")


def callback(hwnd, extra):
    rect = win32gui.GetWindowRect(hwnd)
    x = rect[0]
    y = rect[1]
    w = rect[2] - x
    h = rect[3] - y
    print("Window %s:" % win32gui.GetWindowText(hwnd))
    print("\tLocation: (%d, %d)" % (x, y))
    print("\t    Size: (%d, %d)" % (w, h))


# win32gui.EnumWindows(callback, None)

class GAME_STATES_TEST(Enum):
    BOT_STARTED = None
    RIPPLE_DIMENSION_DHALIA = {
        'name': 'Dhalia', 'img': ripple_dimension_dhalia_btn, 'threshold': OK_THRESHOLD}
    RIPPLE_DIMENSION_SUHUA = {
        'name': 'Ye Suhua', 'img': ripple_dimension_ye_suhua_btn, 'threshold': OK_THRESHOLD}
    RIPPLE_DIMENSION_SUHUA_CHAT = {
        'name': 'Ye Suhua Chat', 'img': ripple_dimension_ye_suhua_alt_btn, 'threshold': OK_THRESHOLD}
    RETRY_BATTLE = {'name': 'Retry Battle',
                    'img': retry_btn, 'threshold': OK_THRESHOLD}


while True:
    print_fps()
    print_game_state()

    nox_player_img = get_nox_player_window_img()

    for state in GAME_STATES_TEST:
        if state.value is not None:
            find_and_click_img(state)

    # open_image('Dislyte', nox_player_img)

    # if keyboard.is_pressed('c'):
    #     break
