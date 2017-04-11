# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils import timezone
from random import randint

from django.contrib.postgres.fields import ArrayField
from django.db import models

from minesweeper.constants import MINE


class MinesweeperGame(models.Model):
    """ A model to store game information
    """
    created = models.DateTimeField(auto_now_add=True)
    started = models.DateTimeField(null=True)
    board_size = models.IntegerField(default=10)
    num_mines = models.IntegerField(default=10)
    board = ArrayField(ArrayField(models.IntegerField()), null=True)
    visibility = ArrayField(ArrayField(models.BooleanField()), null=True)
    flagged = ArrayField(ArrayField(models.BooleanField()), null=True)
    status = models.IntegerField(default=0)

    def start(self):
        self.generate_empty_board()
        self.generate_mines()
        self.started = timezone.now()
        self.save()

    def generate_empty_board(self):
        """ Generates a blank (and fully hidden) board.
        """
        self.board = [[0] * self.board_size for _ in xrange(self.board_size)]
        self.visibility = [[False] * self.board_size for _ in xrange(self.board_size)]
        self.flagged = [[False] * self.board_size for _ in xrange(self.board_size)]

    def generate_mines(self, mines=10, size=10):
        """ Generates the initial board state.  Accepts an integer indicating the number
            of mines that should be placed and an integer representing the size
            (horizontal and vertical) of the board array.
        """
        self.mine_locations = []
        for num in range(self.num_mines):
            self.place_mine()
        # Generate empty board

        for mine_location in self.mine_locations:
            self.board[mine_location[0]][mine_location[1]] = MINE
            self.increment_adjacent_squares(mine_location)

    def increment_adjacent_squares(self, mine_location):
        """ Accepts a tuple indicating the location of a mine in our array and increments
            all adjacent squares that do not contain a mine by 1.
        """
        x, y = mine_location

        for x_offset in range(-1, 2):
            for y_offset in range(-1, 2):
                self.increment_square(x + x_offset, y + y_offset)

    def increment_square(self, x, y):
        """ Increments a square if it is inside the bounds of our board and does not
            contain a mine.
        """
        if self.inside_board(x, y) and not self.contains_mine(x, y):
            self.board[x][y] += 1

    def contains_mine(self, x, y):
        """ Accepts the x and y coordinates of a location in our array and returns True
            if that space contains a mine or False if it does not.
        """
        return True if self.board[x][y] == MINE else False

    def place_mine(self):
        """ Generates a tuple to represent the location of a mine in our array.  If the
            tuple found is already present in our array, recurs itself to generate a new
            tuple.
        """
        mine_location = (randint(0, self.board_size - 1), randint(0, self.board_size - 1))
        if mine_location not in self.mine_locations:
            self.mine_locations.append(mine_location)
        else:
            self.place_mine()

    def inside_board(self, x, y):
        """ Accepts the x and y coordinates of a location and returns True if it is inside
            the bounds of our board and False if it is not.
        """
        return (x >= 0 and x < self.board_size and y >= 0 and y < self.board_size)

    def process_move(self, x, y):
        """ Accepts the x and y coordinates of a move submitted by the player, updates our
            board and determines if the game has been won or lost.
        """
        self.make_visible(x, y)
        if self.board[x][y] == 0:
            self.make_visible_adjacent_squares(x, y)
        elif self.contains_mine(x, y):
            self.game_lost()

        self.save()

    def make_visible_adjacent_squares(self, x, y):
        """ Accepts the x and y coordinates of a location in our array and sets all
            adjacent squares to visible.
        """
        for x_offset in range(-1, 2):
            offset_x = x + x_offset
            for y_offset in range(-1, 2):
                offset_y = y + y_offset
                if self.inside_board(x, y) and not self.is_visible(offset_x, offset_y):
                    self.make_visible(offset_x, offset_y)
                    if self.board[offset_x][offset_y] == 0:
                        self.make_visible_adjacent_squares(offset_x, offset_y)

    def make_visible(self, x, y):
        """ Accepts the x and y coordinates of a location in our array and marks it as
            visible.
        """
        self.visibility[x][y] = True

    def is_visible(self, x, y):
        """ Accepts the x and y coordinates of a location in our array and returns True
            if it is visible or false if it is not.
        """
        return self.visibility[x][y]
