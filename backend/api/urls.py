from django.urls import path
from . import views, v2, gm

urlpatterns = [
    path('live-scoreboard/',                         views.live_scoreboard,   name='live_scoreboard'),
    path('predictions/game/<str:game_id>/',          views.game_prediction,   name='game_prediction'),
    path('predictions/player-props/<str:game_id>/',  views.player_props,      name='player_props'),
    path('odds/',                                    views.todays_odds,        name='todays_odds'),
    path('stats/team/<int:team_id>/',                views.team_stats,         name='team_stats'),
    path('stats/player/<int:player_id>/',            views.player_stats,       name='player_stats'),
    path('players/search/',                          views.player_search,      name='player_search'),
    path('leaders/',                                 views.league_leaders,     name='league_leaders'),
    # v2: direct-SQL endpoints used by the redesigned frontend
    path('v2/scoreboard/',            v2.scoreboard,            name='v2_scoreboard'),
    path('v2/predictions/upcoming/',  v2.upcoming_predictions,  name='v2_predictions'),
    path('v2/awards/',                v2.awards,                name='v2_awards'),
    path('v2/title-odds/',            v2.title_odds,            name='v2_title_odds'),
    path('v2/odds/',                  v2.odds,                  name='v2_odds'),
    path('v2/players/search/',        v2.player_search,         name='v2_player_search'),
    path('v2/players/<int:player_id>/', v2.player_detail,       name='v2_player'),
    path('v2/leaders/',               v2.leaders,               name='v2_leaders'),
    path('v2/teams/',                 v2.teams_list,            name='v2_teams'),
    path('v2/teams/<int:team_id>/',   v2.team_detail,           name='v2_team'),
    path('v2/gm/league/',             gm.league,                name='gm_league'),
    path('v2/gm/roster/<int:team_id>/', gm.roster,              name='gm_roster'),
    path('v2/gm/trade/',              gm.evaluate_trade,        name='gm_trade'),
    path('v2/gm/simulate/',           gm.simulate_season,       name='gm_simulate'),
    path('v2/ask/',                   v2.ask_view,              name='v2_ask'),
]
