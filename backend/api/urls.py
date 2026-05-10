from django.urls import path
from . import views

urlpatterns = [
    path('live-scoreboard/',                         views.live_scoreboard,   name='live_scoreboard'),
    path('predictions/game/<str:game_id>/',          views.game_prediction,   name='game_prediction'),
    path('predictions/player-props/<str:game_id>/',  views.player_props,      name='player_props'),
    path('odds/',                                    views.todays_odds,        name='todays_odds'),
    path('stats/team/<int:team_id>/',                views.team_stats,         name='team_stats'),
    path('stats/player/<int:player_id>/',            views.player_stats,       name='player_stats'),
    path('players/search/',                          views.player_search,      name='player_search'),
    path('leaders/',                                 views.league_leaders,     name='league_leaders'),
]
