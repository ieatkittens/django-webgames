from random import randint

from braces.views import AjaxResponseMixin, JSONResponseMixin
from django.views.generic import View

from minesweeper.constants import WON, LOST, SUCCESS_MESSAGES, FAILURE_MESSAGES
from minesweeper.models import MinesweeperGame


class AjaxResetGame(JSONResponseMixin, AjaxResponseMixin, View):
    """ Resets the game for the provided ID
    """

    def get_ajax(self, request, *args, **kwargs):
        context = {}
        # Get our Dossier Object
        game_id = request.GET.get('game_id', None)

        try:
            game = MinesweeperGame.objects.prefetch_related('fields').get(id=game_id)
        except MinesweeperGame.DoesNotExist:
            game = None

        if game:
            game.reset()
            json_boardstate = game.get_client_json_boardstate()
            context['json_boardstate'] = json_boardstate
            context['game_status'] = game.status
        else:
            context['message'] = 'Game with ID {} not found'.format(game_id)
            context['message_class'] = 'alert alert-danger'

        return self.render_json_response(context)


class AjaxProcessMove(JSONResponseMixin, AjaxResponseMixin, View):
    """ Accepts a User move, processes it and returns the updated boardstate.
    """

    def get_ajax(self, request, *args, **kwargs):
        context = {}
        # Get our Dossier Object
        game_id = request.GET.get('game_id', None)
        move_type = request.GET.get('move_type', 'clear')
        x = request.GET.get('x', None)
        y = request.GET.get('y', None)

        try:
            game = MinesweeperGame.objects.prefetch_related('fields').get(id=game_id)
        except MinesweeperGame.DoesNotExist:
            game = None

        if game and x and y:
            game.user_move(int(x), int(y), move_type)
            json_boardstate = game.get_client_json_boardstate()
            context['json_boardstate'] = json_boardstate
            if game.status == WON:
                context['message'] = SUCCESS_MESSAGES[randint(0, len(SUCCESS_MESSAGES) - 1)]
            elif game.status == LOST:
                context['message'] = FAILURE_MESSAGES[randint(0, len(FAILURE_MESSAGES) - 1)]
            context['game_status'] = game.status
        else:
            context['message'] = 'Game with ID {} not found'.format(game_id)

        return self.render_json_response(context)
