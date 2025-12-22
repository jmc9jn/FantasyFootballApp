#Import necessary libraries
from django.shortcuts import render
from stats.models import (avg_qb_stats, avg_rb_stats, avg_wr_stats, avg_te_stats,
                     total_qb_stats, total_rb_stats, total_wr_stats, total_te_stats,
                     weekly_qb_stats, weekly_rb_stats, weekly_wr_stats, weekly_te_stats)
from django.db.models import Max
import json

#This view is responsible for receiving requests from the player stats template
#and returning the necessary response
def player_stats_view(request):
    #Map position to corresponding weekly tables
    position_models = {
        "QB": weekly_qb_stats,
        "RB": weekly_rb_stats,
        "WR": weekly_wr_stats,
        "TE": weekly_te_stats
    }
    # Get a list of the positions
    position_list = list(position_models.keys())

    # Retrieve the position selected by the user
    # if no position is selected, default to QB. This narrows down which players to show
    # in the player dropdown
    selected_position = request.GET.get('position', 'QB')
    selected_model = position_models[selected_position]

    #Retrieve the player selected by the user
    #If no player is selected, default to first player of selected position
    selected_player = request.GET.get('player', selected_model.objects.first().player)

    #Get all players that fall under the selected position
    player_list = sorted(selected_model.objects.values_list('player', flat=True).distinct())

    #Initialize a list to store player records
    records = []

    #Get the appropriate data based on the position and player name selected by the user
    weekly_model = (position_models[selected_position]
                    .objects
                    .all()
                    .filter(player = selected_player)
                    .order_by('week')
                    )

    #Get the appropriate fields based on the position selected by the user
    if selected_position == 'QB':
        columns = ['week','passing_attempts','passing_yards','passing_touchdowns','interceptions',
                              'rushing_attempts','rushing_yards','rushing_touchdowns', 'fantasy_points']

    elif selected_position == 'RB':
        columns = ['week','rushing_attempts','rushing_yards','rushing_touchdowns',
                                'targets', 'receptions','receiving_yards','receiving_touchdowns', 'fantasy_points']

    else:
        columns = ['week','targets','receptions','receiving_yards','receiving_touchdowns', 'fantasy_points']


    player_table = weekly_model.values(*columns)

    #Convert the fields to stat fields to integers (more aesthetic than using decimals)
    for row in player_table:
        converted_row = {}
        for key, value in row.items():
            if key != 'fantasy_points' and isinstance(value, float):
                converted_row[key] = int(value)
            else:
                converted_row[key] = value

        records.append(converted_row)

    #Get the selected view type (either table or chart)
    selected_view_type = request.GET.get("view", "table")

    #Get the list of fields names to render
    clean_field_names = [r.replace("_"," ").title() for r in columns]

    #Get the list of fields to choose from for the chart view
    #Set default field as the first field from the set of columns for the given position
    metric_field_list = [i for i in columns if i != 'week']
    default_metric = metric_field_list[0]
    selected_chart_y_axis = request.GET.get('metric', default_metric)

    #Actual values for the selected metric
    chart_metric = [r[selected_chart_y_axis] for r in records]

    #Get a list of weeks for the player
    weeks_list = [r['week'] for r in records]

    return render(request, "player_stats.html", {
        "records": records,

        "all_view_types": ['table', 'chart'],
        "selected_view_type": selected_view_type,

        "all_positions": position_list,
        "selected_position": selected_position,

        "all_players": player_list,
        'selected_player': selected_player,

        "team": weekly_model.values('team')[0]['team'],

        "weeks_list": json.dumps(weeks_list),
        "clean_field_names": clean_field_names,

        "data": json.dumps(chart_metric, default = float),
        "selected_player_chart_metric_name" : selected_chart_y_axis
    })








