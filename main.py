import time
import curses
import random
import asyncio

from animations import draw


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
