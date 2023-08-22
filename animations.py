import random
import curses
import time
import itertools
import os
import asyncio

from physics import update_speed
from tools import draw_frame, get_frame_size
from obstacles import Obstacle
from explosion import explode


SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258

coroutines = []
obstacles = []
obstacles_in_last_collisions = []

PHRASES = {
    1957: "First Sputnik",
    1961: "Gagarin flew!",
    1969: "Armstrong got on the moon!",
    1971: "First orbital space station Salute-1",
    1977: "Voyager-1 and Voyager-2 flew",
    1981: "Flight of the Shuttle Columbia",
    1998: 'ISS start building',
    2011: 'Voyager-1 has left the Solar System',
    2020: "Take the plasma gun! Shoot the garbage!",
}

GAMEOVER_TEXT = """
   _____                         ____                 
  / ____|                       / __ \                
 | |  __  __ _ _ __ ___   ___  | |  | |_   _____ _ __ 
 | | |_ |/ _` | '_ ` _ \ / _ \ | |  | \ \ / / _ \ '__|
 | |__| | (_| | | | | | |  __/ | |__| |\ V /  __/ |   
  \_____|\__,_|_| |_| |_|\___|  \____/  \_/ \___|_|   
                                                      
                                                      
"""

year = 1957
cur_phrase = None


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
    obstacles.append(obstacle)

    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed
        obstacle.row = row
        if obstacle in obstacles_in_last_collisions:
            obstacles_in_last_collisions.remove(obstacle)
            obstacles.remove(obstacle)
            await explode(canvas, row+(rows/2), column+(columns/2))
            return
    obstacles.remove(obstacle)


def get_garbage_delay_tics(year):
    if year < 1961:
        return None
    elif year < 1969:
        return 20
    elif year < 1981:
        return 14
    elif year < 1995:
        return 10
    elif year < 2010:
        return 8
    elif year < 2020:
        return 6
    else:
        return 2


def update_cur_phrase():
    global cur_phrase
    phrase = PHRASES.get(int(year))
    print(phrase)
    cur_phrase = phrase if phrase else cur_phrase


def load_frames(dir_name):
    frames = []
    for frame_path in os.listdir(f"frames/{dir_name}"):
        with open(f"frames/{dir_name}/{frame_path}", "r") as file:
            frame = file.read()
            for _ in range(2):
                frames.append(frame)
    return frames


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


async def show_gameover(canvas):
    rows, columns = canvas.getmaxyx()
    while True:
        draw_frame(canvas, rows/2, columns/2, GAMEOVER_TEXT)
        await sleep()


async def fill_orbit_with_garbage(canvas, height, frames):
    while True:
        garbage_delay_tics = get_garbage_delay_tics(year)
        if garbage_delay_tics:
            column = random.randint(1, height - 1)
            frame = random.choice(frames)
            coroutines.append(fly_garbage(canvas, column, frame))
            await sleep(garbage_delay_tics)
        await sleep()


def draw(canvas):
    global year
    curses.curs_set(False)
    canvas.nodelay(True)
    symbols = "+*.:'"
    width, height = canvas.getmaxyx()
    year_row, year_column = width-3, height-10
    phrase_row, phrase_column = width-6, height-40
    update_cur_phrase()
    spaceship_frames = load_frames("spaceship")
    garbage_frames = load_frames("garbage")
    stars = 100
    for num in range(stars):
        row, column = random.randint(1, width-1), random.randint(1, height-1)
        coroutines.append(blink(canvas, row, column, random.choice(symbols)))
    coroutines.append(animate_spaceship(canvas, width//2, height//2, spaceship_frames))
    coroutines.append(fill_orbit_with_garbage(canvas, height, garbage_frames))

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        time.sleep(0.1)
        canvas.addstr(year_row, year_column, str(int(year)))
        draw_frame(canvas, phrase_row, phrase_column, cur_phrase, negative=True)
        update_cur_phrase()
        draw_frame(canvas, phrase_row, phrase_column, cur_phrase)
        canvas.refresh()
        canvas.border()
        year += 0.1


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

        for obstacle in obstacles:
            if obstacle.has_collision(row, column):
                obstacles_in_last_collisions.append(obstacle)
                return


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

        if year >= 2020:
            if space_pressed:
                fires.append(fire(canvas, row, column))
            for coroutine in fires:
                try:
                    coroutine.send(None)
                except StopIteration:
                    fires.remove(coroutine)

        for obstacle in obstacles:
            if obstacle.has_collision(row, column):
                obstacles_in_last_collisions.append(obstacle)
                await show_gameover(canvas)
                return


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)
