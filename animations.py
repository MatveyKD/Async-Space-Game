import random
import curses
import time
import itertools
import os
import asyncio

from physics import update_speed
from tools import draw_frame
from obstacles import Obstacle, show_obstacles


SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258

COROUTINES = []
OBSTACLES = []


def read_controls(canvas):
    """Read keys pressed and returns tuple witl controls state."""

    rows_direction = columns_direction = 0
    space_pressed = False

    while True:
        pressed_key_code = canvas.getch()

        if pressed_key_code == -1:
            # https://docs.python.org/3/library/curses.html#curses.window.getch
            break

        if pressed_key_code == UP_KEY_CODE:
            rows_direction = -1

        if pressed_key_code == DOWN_KEY_CODE:
            rows_direction = 1

        if pressed_key_code == RIGHT_KEY_CODE:
            columns_direction = 1

        if pressed_key_code == LEFT_KEY_CODE:
            columns_direction = -1

        if pressed_key_code == SPACE_KEY_CODE:
            space_pressed = True

    return rows_direction, columns_direction, space_pressed


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0

    rows, columns = get_frame_size(garbage_frame)

    obstacle = Obstacle(row, column, rows, columns)
    OBSTACLES.append(obstacle)

    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed

        obstacle.row = row
    OBSTACLES.remove(obstacle)


def load_frames(dir_name):
    frames = []
    for frame_path in os.listdir(f"frames/{dir_name}"):
        with open(f"frames/{dir_name}/{frame_path}", "r") as file:
            frame = file.read()
            for _ in range(2):
                frames.append(frame)
    return frames


def get_frame_size(text):
    lines = text.splitlines()
    rows = len(lines)
    columns = max([len(line) for line in lines])
    return rows, columns


async def blink(canvas, row, column, symbol='*'):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(random.randint(5, 20))

        canvas.addstr(row, column, symbol)
        await sleep(random.randint(5, 20))

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(random.randint(5, 20))

        canvas.addstr(row, column, symbol)
        await sleep(random.randint(5, 20))


async def fill_orbit_with_garbage(canvas, height, frames):
    while True:
        column = random.randint(1, height - 1)
        frame = random.choice(frames)
        COROUTINES.append(fly_garbage(canvas, column, frame))
        await sleep(random.randint(3, 20))


def draw(canvas):
    curses.curs_set(False)
    canvas.nodelay(True)
    symbols = "+*.:'"
    width, height = canvas.getmaxyx()
    spaceship_frames = load_frames("spaceship")
    garbage_frames = load_frames("garbage")
    stars = 100
    for num in range(stars):
        row, column = random.randint(1, width-1), random.randint(1, height-1)
        COROUTINES.append(blink(canvas, row, column, random.choice(symbols)))
    COROUTINES.append(animate_spaceship(canvas, width//2, height//2, spaceship_frames))
    COROUTINES.append(fill_orbit_with_garbage(canvas, height, garbage_frames))
    COROUTINES.append(show_obstacles(canvas, OBSTACLES))

    while True:
        for coroutine in COROUTINES.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                COROUTINES.remove(coroutine)
        time.sleep(0.1)
        canvas.refresh()
        canvas.border()


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def animate_spaceship(canvas, row, column, frames):
    row_speed = column_speed = 0
    fires = []
    for frame in itertools.cycle(frames):
        draw_frame(canvas, row, column, frame)
        row_direction, column_direction, space_pressed = read_controls(canvas)
        await sleep()
        draw_frame(canvas, row, column, frame, negative=True)

        row_speed, column_speed = update_speed(row_speed, column_speed, row_direction, column_direction)
        row, column = row + row_speed, column + column_speed
        rows, columns = get_frame_size(frame)
        window_size = canvas.getmaxyx()

        row = max(0, row)
        row = min(row + rows, window_size[0]) - rows
        column = max(0, column)
        column = min(column + columns, window_size[1]) - columns

        if space_pressed:
            fires.append(fire(canvas, row, column))
        for coroutine in fires:
            try:
                coroutine.send(None)
            except StopIteration:
                fires.remove(coroutine)


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)
