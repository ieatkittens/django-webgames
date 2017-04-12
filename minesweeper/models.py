# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.utils import timezone
from random import randint

from django.contrib.postgres.fields import ArrayField
from django.db import models

from minesweeper.constants import MINE, IN_PROGRESS, WON, LOST


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
    status = models.IntegerField(default=IN_PROGRESS)

    def start(self):
        """ Starts the game by generating an empty board, generating the mines and setting
            the started timestamp
        """
        self.generate_empty_board()
        self.generate_mines()
        self.started = timezone.now()
        self.status = IN_PROGRESS
        self.save()

    def game_lost(self):
        """ Changes conditions to reflect that the user has lost the game.
        """
        self.status = LOST
        self.set_board_visibility(True)
        self.save()

    def game_won(self):
        """ Changes conditions to reflect that the user has won the game.
        """
        self.status = WON
        self.set_board_visibility(True)
        self.save()

    def set_board_visibility(self, state):
        """ Sets visibility for all locations on the board to state value
        """
        self.visibility = [[state] * self.board_size for _ in xrange(self.board_size)]
        self.save()

    def generate_empty_board(self):
        """ Generates a blank (and fully hidden) board.
        """
        self.board = [[0] * self.board_size for _ in xrange(self.board_size)]
        self.set_board_visibility(False)
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

    def user_move(self, x, y, move_type='clear'):
        """ Accepts the x and y coordinates of a move submitted by the player, updates our
            board and determines if the game has been won or lost.
        """
        if move_type == 'clear' and not self.is_flagged(x, y):

            # Make the location visible
            self.make_visible(x, y)

            # If there are no adjacent mines, cascade out and clear adjacent squares as well
            if self.board[x][y] == 0:
                self.make_visible_adjacent_squares(x, y)

            # If there is a mine in the square, trigger a game loss.
            elif self.contains_mine(x, y):
                self.game_lost()

        elif move_type == 'flag' and self.inside_board(x, y) and not self.is_visible(x, y):
            self.toggle_flag(x, y)

        self.check_for_win()

        self.save()

    def check_for_win(self):
        """ Checks if the player has won the game, and if they have, triggers the game_won
            function.  The game is won if all squares that do not contain mines are visible.
        """
        # Get the total number of spaces minus the number of 'visible' spaces
        total_non_visible_squares = self.board_size ** 2 - len([value for row in self.visibility for value in row if value is True])
        # If total number of 'non_visible' spaces is equal to the number of mines, you win!
        all_non_mines_visible = True if total_non_visible_squares == self.num_mines else False
        if all_non_mines_visible:
            self.game_won()

    def toggle_flag(self, x, y):
        """ Accepts the x and y coordinates of a move submitted by the player and toggles
            the flagged value for that location if it is inside our board and that
            location is currently not visible
        """
        self.flagged[x][y] = not self.flagged[x][y]
        self.save()

    def is_flagged(self, x, y):
        """ Accepts the x and y coordinates of a location in our array and returns True
            if it is flagged or False if it is not.
        """
        return self.flagged[x][y]

    def remove_flag(self, x, y):
        """ Accepts the x and y coordinates of a move submitted by the player adds a flag
            to that location if it is not currently visible and it is inside the bound of
            our board
        """

    def make_visible_adjacent_squares(self, x, y):
        """ Accepts the x and y coordinates of a location in our array and sets all
            adjacent squares to visible.
        """
        for x_offset in range(-1, 2):
            offset_x = x + x_offset
            for y_offset in range(-1, 2):
                offset_y = y + y_offset
                if self.inside_board(offset_x, offset_y) and not self.is_visible(offset_x, offset_y):
                    self.make_visible(offset_x, offset_y)
                    if self.is_flagged(offset_x, offset_y):
                        self.toggle_flag(offset_x, offset_y)
                    if self.board[offset_x][offset_y] == 0:
                        self.make_visible_adjacent_squares(offset_x, offset_y)

    def make_visible(self, x, y):
        """ Accepts the x and y coordinates of a location in our array and marks it as
            visible.
        """
        self.visibility[x][y] = True

    def is_visible(self, x, y):
        """ Accepts the x and y coordinates of a location in our array and returns True
            if it is visible or False if it is not.
        """
        return self.visibility[x][y]

    def get_visible_boardstate(self):
        """ Returns a 2D array with all publicly available information.
        """
        visible_array = self.visibility
        for x, row in enumerate(visible_array):
            for y, col in enumerate(row):
                # First reveal visible squares
                visible_array[x][y] = self.board[x][y] if col else 'not_visible'
                # Then reveal flagged squares
                visible_array[x][y] = 'flagged' if self.flagged[x][y] else visible_array[x][y]

        return visible_array

    def client_json_boardstate(self):
        """ Returns the current public boardstate in JSON format - only visible squares
            and flagged squares.
        """
        visible_array = self.get_visible_boardstate()
        json_array = json.dumps(visible_array)

        return json_array
