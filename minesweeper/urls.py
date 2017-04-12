from django.conf.urls import url
from minesweeper.ajax_views import AjaxProcessMove, AjaxResetGame
from minesweeper.views import MinesweeperGameView, MinesweeperNewGameView

urlpatterns = [
    url(r'^game/(?P<game_id>\d+)/$', MinesweeperGameView.as_view(), name='minesweeper'),
    url(r'^game/$', MinesweeperNewGameView.as_view(), name='minesweeper_new'),
    url(r'^ajax_move/$', AjaxProcessMove.as_view(), name='ajax_submit_move'),
    url(r'^ajax_reset/$', AjaxResetGame.as_view(), name='ajax_reset_game')
]
