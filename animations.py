import random
import curses
import time
import itertools
import os
import asyncio


SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258

COROUTINES = []


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

    return rows_direction, columns_direction


def draw_frame(canvas, start_row, start_column, text, negative=False):
    rows_number, columns_number = canvas.getmaxyx()

    for row, line in enumerate(text.splitlines(), round(start_row)):
        if row < 0:
            continue

        if row >= rows_number:
            break

        for column, symbol in enumerate(line, round(start_column)):
            if column < 0:
                continue

            if column >= columns_number:
                break

            if symbol == ' ':
                continue

            if row == rows_number - 1 and column == columns_number - 1:
                continue

            symbol = symbol if not negative else ' '
            canvas.addch(row, column, symbol)


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0

    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed


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
        for _ in range(random.randint(5, 20)):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(random.randint(5, 20)):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(random.randint(5, 20)):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(random.randint(5, 20)):
            await asyncio.sleep(0)


async def fill_orbit_with_garbage(canvas, height, frames):
    while True:
        column = random.randint(1, height - 1)
        frame = random.choice(frames)
        COROUTINES.append(fly_garbage(canvas, column, frame))
        for _ in range(random.randint(3, 20)):
            await asyncio.sleep(0)


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

    while True:
        for coroutine in COROUTINES.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                COROUTINES.remove(coroutine)
        time.sleep(0.1)
        canvas.refresh()
        canvas.border()


async def animate_spaceship(canvas, row, column, frames, speed=1):
    for frame in itertools.cycle(frames):
        draw_frame(canvas, row, column, frame)
        row_direction, column_direction = read_controls(canvas)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, frame, negative=True)

        row += row_direction * speed
        column += column_direction * speed
        rows, columns = get_frame_size(frame)
        window_size = canvas.getmaxyx()

        row = max(0, row)
        row = min(row + rows, window_size[0]) - rows
        column = max(0, column)
        column = min(column + columns, window_size[1]) - columns
