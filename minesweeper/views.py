from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from minesweeper.forms import NewGameForm
from minesweeper.models import MinesweeperGame


class MinesweeperGameView(TemplateView):
    template_name = 'game.html'

    def new_game(self, num_mines):
        """ Starts a new game and redirects the user to the URL for that game.
        """
        game = MinesweeperGame.objects.create(num_mines=num_mines)
        game.start()
        return redirect('minesweeper', game_id=game.id)

    def get(self, request, *args, **kwargs):
        game_id = kwargs.pop('game_id', None)
        new_game_form = NewGameForm()
        context = {'new_game_form': new_game_form}

        try:
            game = MinesweeperGame.objects.get(id=game_id)
        except MinesweeperGame.DoesNotExist:
            context['message'] = 'Game matching ID {} does not exist'.format(game_id)
            game = None

        if game:
            context['game'] = game
            context['visible_array'] = game.get_visible_boardstate()

        return render(request, self.template_name, context,)

    def post(self, request, *args, **kwargs):
        new_game_form = NewGameForm(request.POST)
        return self.new_game(
            num_mines=int(new_game_form.data['num_mines'])
        )
