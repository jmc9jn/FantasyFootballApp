#Import necessary libraries
from django.shortcuts import render
from stats.models import (avg_qb_stats, avg_rb_stats, avg_wr_stats, avg_te_stats,
                     total_qb_stats, total_rb_stats, total_wr_stats, total_te_stats,
                     weekly_qb_stats, weekly_rb_stats, weekly_wr_stats, weekly_te_stats)
from django.db.models import Max
import json

def weekly_rankings_view(request):
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
    # If no position is selected, default to QB
    selected_position = request.GET.get('position', 'QB')

    #Retrieve the week selected by the user
    #If no week is selected yet, take the most recent week
    max_week = weekly_qb_stats.objects.aggregate(Max('week'))['week__max']
    selected_week = int(request.GET.get('week', max_week))

    #Get a list of the weeks
    weeks_list = sorted(list(weekly_qb_stats.objects.values_list('week',flat=True).distinct()), reverse = False)
    weeks_list = [int(week) for week in weeks_list]

    #Initialize a list to store the records
    records = []

    #Get fields for each specific position
    if selected_position == 'QB':
        columns = ['rank','player','team','opp','passing_yards','passing_touchdowns', 'interceptions',
                  'rushing_yards','rushing_touchdowns','fantasy_points']

    elif selected_position == 'RB':
        columns = ['rank','player','team','opp','rushing_attempts','rushing_yards',
                  'rushing_touchdowns', 'targets',
                  'receptions','receiving_yards','receiving_touchdowns','fantasy_points']

    else:
        columns = ['rank','player','team','opp','targets', 'receptions','receiving_yards','receiving_touchdowns',
                  'rushing_yards', 'rushing_touchdowns',
                  'fantasy_points']

    #Get the original fields name and the cleaned version to display
    clean_field_names = [r.replace('_', ' ').title() for r in columns]

    #Get the field you want to sort on and what direction
    selected_sort_field = request.GET.get('sort_field', 'fantasy_points')
    selected_sort_direction = request.GET.get('sort_direction', 'desc')
    order_prefix = '-' if selected_sort_direction == 'desc' else ''

    #Get the appropriate model based on user selection
    #Filter based on selected week and order by fantasy points
    weekly_model = (position_models[selected_position]
                    .objects.all()
                    .filter(week = selected_week)
                    .order_by(f'{order_prefix}{selected_sort_field}')
                    .values(*columns)
                    )

    records = []
    for row in weekly_model:
        converted_row = {}
        for key, value in row.items():
            if key != 'fantasy_points' and isinstance(value, float):
                converted_row[key] = int(value)
            else: converted_row[key] = value

        records.append(converted_row)

    records = [record for record in records if record.get('fantasy_points') > 0]

    return render(request, "weekly_rankings.html", {
        "records": records,

        "all_positions": position_list,
        "selected_position": selected_position,

        "weeks_list": weeks_list,
        "selected_week": selected_week,

        "fields":  list(zip(columns, clean_field_names)),
        "selected_sort_field": selected_sort_field,
        "selected_sort_direction": selected_sort_direction
    })


def season_rankings_view(request):
    # Map position to corresponding average and total stat tables
    position_models = {
        "QB": [avg_qb_stats, total_qb_stats],
        "RB": [avg_rb_stats, total_rb_stats],
        "WR": [avg_wr_stats, total_wr_stats],
        "TE": [avg_te_stats, total_te_stats]
    }
    #Get a list of the positions
    position_list = list(position_models.keys())

    #Retrieve the position selected by the user
    #If no position is selected, default to QB
    selected_position = request.GET.get("position", 'QB')

    #Get fields for each specific position
    if selected_position == 'QB':
        columns = ['rank','player','team','passing_yards','passing_touchdowns', 'interceptions',
                  'rushing_yards','rushing_touchdowns','fantasy_points']

    elif selected_position == 'RB':
        columns = ['rank','player','team','rushing_attempts','rushing_yards',
                  'rushing_touchdowns', 'targets',
                  'receptions','receiving_yards','receiving_touchdowns','fantasy_points']

    else:
        columns = ['rank','player','team','targets', 'receptions','receiving_yards','receiving_touchdowns',
                  'rushing_yards', 'rushing_touchdowns',
                  'fantasy_points']

    #Get the original fields name and the cleaned version to display
    clean_field_names = [f.replace('_', ' ').title() for f in columns]

    #Get the stat type (either total or averages)
    selected_stat_type = request.GET.get('stat_type', 'Total')

    #Get the direction to sort
    selected_sort_direction = request.GET.get('sort_direction', 'desc')
    order_prefix = '-' if selected_sort_direction == 'desc' else ''

    if selected_stat_type == 'Total':
        selected_sort_field = request.GET.get('sort_field', 'total_fantasy_points')
        fields = ['rank','player','team'] + ['total_' + column for column in columns if column not in ['rank','player','team']]
        data = position_models[selected_position][1]

    else:
        selected_sort_field = request.GET.get('sort_field', 'avg_fantasy_points')
        fields = ['rank','player','team'] + ['avg_' + column for column in columns if column not in ['rank','player','team']]
        data = position_models[selected_position][0]

    #Get the data based on user selected criteria
    model = (data
             .objects.all()
             .order_by(f'{order_prefix}{selected_sort_field}')
             .values(*fields)
             )

    #Create a list of dictionaries out of the data
    records = []

    #Convert float to integers (more aesthetic)
    for row in model:
        converted_row = {}
        for key, value in row.items():
            if 'fantasy_points' not in key and isinstance(value, (float, Decimal)):
                converted_row[key] = int(value)
            else:
                converted_row[key] = value
        records.append(converted_row)

    return render(request, "season_rankings.html", {
        "records": records,

        "all_positions": position_list,
        "selected_position": selected_position,

        "fields":  list(zip(fields, clean_field_names)),
        "selected_stat_type": selected_stat_type,
        "selected_sort_field": selected_sort_field,
        "selected_sort_direction": selected_sort_direction
    })

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








