"""
Click left mouse button to create start (blue), end (orange) and barriers (black)
Click right mouse button to reset any node
Click enter to find the path
Click backspace to clear
"""

import math
import time
from _thread import *
import pygame
from tkinter import messagebox
from tkinter import *

pygame.init()

WIDTH = HEIGHT = 1000
ROWS = COLS = 50
SQUARE_SIZE = WIDTH / COLS
MOVE_STRAIGHT = 10
MOVE_DIAGONALLY = 14
DELAY = 0.01
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
ORANGE = (255, 153, 51)
BLUE = (51, 153, 255)
GREEN = (51, 255, 51)
RED = (255, 51, 51)
YELLOW = (255, 255, 51)

class Map:
    def __init__(self, win, rows, cols, width, height, square_size, black, white, orange, blue, yellow, green, red):
        self.win = win
        self.rows = rows
        self.cols = cols
        self.width = width
        self.height = height
        self.square_size = square_size
        self.black = black
        self.white = white
        self.orange = orange
        self.blue = blue
        self.yellow = yellow
        self.green = green
        self.red = red
        self.map = self.create_map()

    def create_map(self):
        map = []
        for row in range(self.rows):
            map.append([])
            for col in range(self.cols):
                node = Node(row, col)
                map[row].append(node)

        return map

    def get_node(self, row, col):
        return self.map[row][col]

    def draw_grid(self):
        for row in range(self.rows):
            pygame.draw.line(self.win, self.black, (0, row * self.square_size), (self.width, row * self.square_size))
            for col in range(self.cols):
                pygame.draw.line(self.win, self.black, (col * self.square_size, 0), (col * self.square_size, self.height))

    def draw_nodes(self):
        for row in range(self.rows):
            for col in range(self.cols):
                node = self.get_node(row, col)
                if node.path:
                    pygame.draw.rect(self.win, self.yellow, pygame.Rect(col * self.square_size, row * self.square_size,
                                                                   self.square_size, self.square_size))
                elif node.start:
                    pygame.draw.rect(self.win, self.blue, pygame.Rect(col * self.square_size, row * self.square_size,
                                                                   self.square_size, self.square_size))
                elif node.end:
                    pygame.draw.rect(self.win, self.orange, pygame.Rect(col * self.square_size, row * self.square_size,
                                                                   self.square_size, self.square_size))
                elif node.in_closed:
                    pygame.draw.rect(self.win, self.red, pygame.Rect(col * self.square_size, row * self.square_size,
                                                                   self.square_size, self.square_size))
                elif node.in_open:
                    pygame.draw.rect(self.win, self.green, pygame.Rect(col * self.square_size, row * self.square_size,
                                                                   self.square_size, self.square_size))
                elif node.open:
                    pygame.draw.rect(self.win, self.white, pygame.Rect(col * self.square_size, row * self.square_size,
                                                                  self.square_size, self.square_size))
                else: # Node is not open
                    pygame.draw.rect(self.win, self.black, pygame.Rect(col * self.square_size, row * self.square_size,
                                                                  self.square_size, self.square_size))

    def get_start(self):
        for row in range(self.rows):
            for col in range(self.cols):
                if self.map[row][col].start:
                    return self.map[row][col]

        return False

    def get_end(self):
        for row in range(self.rows):
            for col in range(self.cols):
                if self.map[row][col].end:
                    return self.map[row][col]

        return False

    def change_node_state(self, node):
        if not self.get_start():
            node.start = True
        else:
            if not self.get_end():
                node.end = True
            elif not node.start and not node.end:
                node.open = False

    def reset_all(self):
        for row in range(self.rows):
            for col in range(self.cols):
                self.get_node(row, col).reset()

        global available, available_to_restart
        available = True
        available_to_restart = True

    def draw_path(self, path):
        global available_to_restart
        pathfinder(self, True)

        for node in path:
            if node != self.get_start() and node != self.get_end():
                time.sleep(DELAY)
                node.path = True

        available_to_restart = True

    def reset_scores(self):
        for row in range(self.rows):
            for col in range(self.cols):
                node = self.get_node(row, col)
                node.came_from = None
                node.g = math.inf
                node.h = None
                node.f = None

    def is_barrier(self):
        for row in range(self.rows):
            for col in range(self.cols):
                if not self.get_node(row, col).open:
                    return True

        return False

class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.reset()

    def reset(self):
        self.start = False
        self.end = False
        self.open = True
        self.path = False
        self.in_open = False
        self.in_closed = False
        self.came_from = None
        self.g = math.inf
        self.h = None
        self.f = None

# Distance between two nodes
def calc_dist(node1, node2):
    # abs() returns absolute value
    x_dist = abs(node1.x - node2.x)
    y_dist = abs(node1.y - node2.y)
    remaining = abs(x_dist - y_dist)
    return MOVE_DIAGONALLY * min(x_dist, y_dist) + (MOVE_STRAIGHT * remaining)

# Neighbours of a node
def get_neighbours(map, node, closed):
    neighbours = []

    for r in [-1, 0, 1]:
        for c in [-1, 0, 1]:
            row, col = node.x + r, node.y + c
            if 0 <= row < ROWS and 0 <= col < COLS:
                if map.get_node(row, col) not in closed and map.get_node(row, col).open:
                    neighbours.append(map.get_node(row, col))

    return neighbours

# Reconstructing the path
def get_path(end):
    path = [end]
    current = end

    while current.came_from:
        path.append(current.came_from)
        current = current.came_from

    path.reverse()
    return path

def pathfinder(map, show):
    open = []
    closed = []

    try:
        # Create the start node and assign g, h, and f value
        start = map.get_start()
        start.g = 0
        start.h = calc_dist(start, map.get_end())
        start.f = start.g + start.h

        # Append start node to the open list
        open.append(start)

        while len(open) != 0:
            if show:
                time.sleep(DELAY)
                for node_to_draw in open:
                    if not node_to_draw.start and not node_to_draw.end:
                        node_to_draw.in_open = True

                for node_to_draw in closed:
                    if not node_to_draw.start and not node_to_draw.end:
                        node_to_draw.in_closed = True

            # Get node with the lowest f score in the open list
            current = open[0]
            for i in range(len(open)):
                node = open[i]
                if node.f < current.f:
                    current = node

            # Remove current from open list
            open.remove(current)

            # Add current to closed
            closed.append(current)

            # Check if current is the end node
            if current.end:
                return get_path(current)

            # Get neighbours list of the current node
            neighbours = get_neighbours(map, current, closed)

            # For each neighbour of the current node
            for neighbour in neighbours:
                tentative_g = current.g + calc_dist(current, neighbour)
                if tentative_g < neighbour.g:
                    neighbour.came_from = current
                    neighbour.g = tentative_g
                    neighbour.h = calc_dist(neighbour, map.get_end())
                    neighbour.f = neighbour.g + neighbour.h

                    if neighbour not in open:
                        open.append(neighbour)
    except:
        pass

    return False

def get_mouse_pos(pos):
    return math.floor(pos[1] / SQUARE_SIZE), math.floor(pos[0] / SQUARE_SIZE)

win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pathfinder algorithm")
icon = pygame.image.load("icon.png")
pygame.display.set_icon(icon)

map = Map(win, ROWS, COLS, WIDTH, HEIGHT, SQUARE_SIZE, BLACK, WHITE, ORANGE, BLUE, YELLOW, GREEN, RED)
available = True
available_to_restart = True

clock = pygame.time.Clock()

running = True
while running:
    clock.tick(60)

    win.fill(WHITE)

    for event in pygame.event.get():
        try:
            if event.type == pygame.QUIT:
                running = False
                break

            if available_to_restart:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        map.reset_all()

            if available:
                if not map.get_start() or not map.get_end() or not map.is_barrier():
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1: # Left mouse click
                            row, col = get_mouse_pos(event.pos)
                            map.change_node_state(map.get_node(row, col))
                        elif event.button == 3: # Right mouse click
                            row, col = get_mouse_pos(event.pos)
                            map.get_node(row, col).reset()
                else:
                    mouse_presses = pygame.mouse.get_pressed()
                    if mouse_presses[0]: # Left mouse click
                        row, col = get_mouse_pos(event.pos)
                        map.change_node_state(map.get_node(row, col))
                    elif mouse_presses[2]: # Right mouse click
                        row, col = get_mouse_pos(event.pos)
                        map.get_node(row, col).reset()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        available = False
                        available_to_restart = False
                        path = pathfinder(map, False)
                        map.reset_scores()
                        if path:
                            start_new_thread(map.draw_path, (path, ))
                        else:
                            root = Tk()
                            root.withdraw()

                            if not map.get_start():
                                messagebox.showerror("Error", "No start point provided\nMake one and try again")
                            elif not map.get_end():
                                messagebox.showerror("Error", "No end point provided\nMake one and try again")
                            else:
                                messagebox.showerror("Error", "There is no path for this state\nChange it and try again")
                            available = True
                            available_to_restart = True
        except:
            pass

    map.draw_nodes()
    map.draw_grid()

    pygame.display.flip()