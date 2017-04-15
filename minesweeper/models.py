# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import copy
import itertools
import json
import operator

from django.db.models import F, Q
from django.utils import timezone
from random import randint

from django.contrib.postgres.fields import ArrayField
from django.db import models

from minesweeper.constants import IN_PROGRESS, WON, LOST
from basegame.models import BaseGame


class MinesweeperGame(BaseGame):
    """ A model to store game information
    """
    started = models.DateTimeField(null=True)
    board_size = models.IntegerField(default=10)
    num_mines = models.IntegerField(default=10)
    board = ArrayField(ArrayField(models.IntegerField()), null=True)
    visibility = ArrayField(ArrayField(models.BooleanField()), null=True)
    flagged = ArrayField(ArrayField(models.BooleanField()), null=True)
    status = models.IntegerField(default=IN_PROGRESS)

    def check_for_win(self):
        """ Checks if the player has won the game, and if they have, triggers the game_won
            function.  The game is won if all squares that do not contain mines are visible.
        """
        if all(self.fields.filter(mined=False).values_list('visible', flat=True)):
            self.game_won()

    def contains_mine(self, x, y):
        """ Accepts the x and y coordinates of a location in our array and returns True
            if that space contains a mine or False if it does not.
        """
        return self.fields.get(x_location=x, y_location=y).mined

    def flag_count(self):
        """ Returns an integer representing the total number of flagged fields
        """
        return self.fields.filter(flagged=True).count()

    def game_lost(self):
        """ Changes conditions to reflect that the user has lost the game.
        """
        self.status = LOST
        self.save()
        self.fields.all().update(visible=True)

    def game_won(self):
        """ Changes conditions to reflect that the user has won the game.
        """
        self.status = WON
        self.save()
        self.fields.all().update(visible=True)

    def reset(self):
        """ Resets the board
        """
        self.fields.all().update(
            visible=False,
            flagged=False
        )
        self.status = IN_PROGRESS
        self.save()

    def generate_board(self):
        """ Generates our Field objects
        """
        for x, y in itertools.product(range(0, self.board_size), range(0, self.board_size)):
            Field.objects.get_or_create(game=self, x_location=x, y_location=y)

    def generate_mines(self, mines=10, size=10):
        """ Generates the initial board state.  Accepts an integer indicating the number
            of mines that should be placed and an integer representing the size
            (horizontal and vertical) of the board array.
        """
        for num in range(self.num_mines):
            self.place_mine()
        # Generate empty board
        for mined_field in self.fields.filter(mined=True):
            mined_field.increment_adjacent_squares()

    def place_mine(self):
        """ Generates a tuple to represent the location of a mine in our array.  If the
            tuple found is already present in our array, recurs itself to generate a new
            tuple.
        """
        x, y = randint(0, self.board_size - 1), randint(0, self.board_size - 1)
        field = self.fields.get(x_location=x, y_location=y)
        if not field.mined:
            field.mined = True
            field.save()
        else:
            self.place_mine()

    def get_client_json_boardstate(self):
        """ Returns the current public boardstate in JSON format - only visible squares
            and flagged squares.
        """
        visible_array = self.get_visible_boardstate()
        json_array = json.dumps(visible_array)

        return json_array

    def get_last_turn(self):
        """ Fetches the last turn that hasn't been undone if it exists.  Returns None if it does not.
        """
        last_turn = Turn.objects.filter(game=self, undone=False)
        return last_turn.latest('number') if last_turn.exists() else None

    def get_visible_boardstate(self):
        """ Returns a 2D array with all publicly available information.
        """
        array = [[0 for i in range(self.board_size)] for i in range(self.board_size)]
        fields = self.fields.all().order_by('x_location', 'y_location')
        for field in fields:
            array[field.x_location][field.y_location] = field.visible_value()

        return array

    def start(self):
        """ Starts the game by generating an empty board, generating the mines and setting
            the started timestamp
        """
        self.generate_board()
        self.generate_mines()
        self.started = timezone.now()
        self.status = IN_PROGRESS
        self.save()

    def undo_last_turn(self):
        """ Resets any actions that were taken on the last turn.  If there is no last
            turn, does nothing.
        """
        last_turn = self.get_last_turn()
        if last_turn:
            last_turn.undo()

    def user_move(self, x=None, y=None, move_type='clear'):
        """ Accepts the x and y coordinates of a move submitted by the player, updates our
            board and determines if the game has been won or lost.
        """
        if move_type == 'undo':
            return self.undo_last_turn()

        field = self.fields.get(x_location=x, y_location=y)
        if field.visible:
            return

        last_turn = self.get_last_turn()
        current_turn, created = Turn.objects.get_or_create(
            game=self,
            number=(last_turn.number + 1) if last_turn else 1,
            selected_field=field,
            move_type=move_type,
            hidden_fields=list(self.fields.filter(visible=False).values_list('id', flat=True)),
            flagged_fields=list(self.fields.filter(flagged=True).values_list('id', flat=True)),
            game_status=self.status
        )

        if move_type == 'clear':
            if field.mined:
                self.game_lost()
            else:
                field.make_visible()

        elif move_type == 'flag' and self.flag_count() < self.num_mines:
            field.flagged = False if field.flagged else True
            field.save()

        self.check_for_win()
        current_turn.save()


class Field(models.Model):
    """ A model to store the details of a Field.  A field is a single square on our board.
        It has x and y coordinates representative of where it lives in our board and
        boolean flags to determine it's various states.
    """
    game = models.ForeignKey(MinesweeperGame, related_name='fields')
    x_location = models.IntegerField(default=0)
    y_location = models.IntegerField(default=0)
    flagged = models.BooleanField(default=False)
    mined = models.BooleanField(default=False)
    value = models.IntegerField(default=0)
    visible = models.BooleanField(default=False)

    def adjacent_fields(self):
        """ Returns a queryset of fields that are adjacent to this field
        """
        offset_filters = []
        for x_offset, y_offset in itertools.product(range(-1, 2), range(-1, 2)):
            offset_filters.append(
                Q(x_location=self.x_location + x_offset) &
                Q(y_location=self.y_location + y_offset)
            )
        query = Q(game=self.game)
        query.add(reduce(operator.or_, offset_filters), Q.AND)

        return Field.objects.filter(query)

    def increment(self):
        """ Increments the fields value by 1;  indicates the number of adjacent fields
            that are mined.
        """
        self.value += 1
        self.save()

    def increment_adjacent_squares(self):
        """ Increments the value of each adjacent Field by 1.
        """
        self.adjacent_fields().update(value=F('value') + 1)

    def make_visible(self):
        """ Sets the visible value of the field to True.  If the value of the field is 0,
            also triggers adjacent fields to clear.
        """
        self.visible = True
        self.save()
        if self.value == 0:
            self.recursive_make_visible_adjacent_squares()

    def recursive_make_visible_adjacent_squares(self):
        """ Marks adjancent squares as visible if the are neither visible nor mined. If
            those squares have a value of 0, runs this function on those fields as well.
        """
        adjacent_fields = self.adjacent_fields().filter(visible=False, mined=False)
        copy.copy(adjacent_fields).update(visible=True, flagged=False)

        for adjacent_field in adjacent_fields:
            if adjacent_field.value == 0:
                adjacent_field.recursive_make_visible_adjacent_squares()

    def visible_value(self):
        """ Returns the value we want to provide for this cell for the user.  Should
            be as follows:  If it's visible, we should return 'mined' if it is mined,
            otherwise it's value.  If it's not visible, we should return 'flagged' if
            it's flagged, and otherwise None.
        """
        if self.visible:
            if self.mined:
                return 'mined'
            elif self.flagged:
                return 'flagged'
            else:
                return self.value
        else:
            return 'flagged' if self.flagged else None


class Turn(models.Model):
        """ A model to store the details of what happened in a given turn.
        """
        game = models.ForeignKey(MinesweeperGame)
        selected_field = models.ForeignKey(Field)
        number = models.IntegerField(default=0)
        move_type = models.CharField(max_length=10, default='')
        undone = models.BooleanField(default=False)
        hidden_fields = ArrayField(models.IntegerField(), null=True)
        flagged_fields = ArrayField(models.IntegerField(), null=True)
        game_status = models.IntegerField(default=0)

        def undo(self):
            """ Reverses whatever actions were taken on the previous turn
            """
            if self.move_type == 'clear':
                self.game.fields.filter(id__in=self.hidden_fields).update(visible=False)
                self.game.fields.filter(id__in=self.flagged_fields).update(flagged=True)
            elif self.move_type == 'flag':
                self.selected_field.flagged = False
                self.selected_field.save()
            self.game.status = self.game_status
            self.game.save()
            self.undone = True
            self.save()
