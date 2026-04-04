from decimal import Decimal
import json

from django.shortcuts import render
from django.db.models import Max

from basic.models import (
    avg_qb_stats, avg_rb_stats, avg_wr_stats, avg_te_stats,
    total_qb_stats, total_rb_stats, total_wr_stats, total_te_stats,
    weekly_qb_stats, weekly_rb_stats, weekly_wr_stats, weekly_te_stats,
    weekly_defense_stats
)


def convert_numeric_values(row, exclude_keys=None):
    """
    Convert Decimal/float values to integers for cleaner display.
    """
    exclude_keys = exclude_keys or []
    converted = {}

    for key, value in row.items():
        if key not in exclude_keys and isinstance(value, (Decimal, float)):
            converted[key] = int(value)
        else:
            converted[key] = value

    return converted


def weekly_rankings_view(request):
    """
    Render weekly rankings table based on position and week.

    Handles:
    - Position filtering (QB, RB, WR, TE)
    - Week selection (default = latest available week)
    - Sorting (field + direction)
    """

    position_models = {
        "QB": weekly_qb_stats,
        "RB": weekly_rb_stats,
        "WR": weekly_wr_stats,
        "TE": weekly_te_stats
    }

    selected_position = request.GET.get('position', 'QB')
    selected_model = position_models[selected_position]

    # Default to most recent week if none selected
    max_week = weekly_qb_stats.objects.aggregate(Max('week'))['week__max']
    selected_week = int(request.GET.get('week', max_week))

    # Available weeks for dropdown
    weeks_list = sorted(
        set(weekly_qb_stats.objects.values_list('week', flat=True))
    )

    # Define columns dynamically per position
    if selected_position == 'QB':
        columns = [
            'rank', 'player', 'team', 'opp',
            'passing_yards', 'passing_touchdowns', 'interceptions',
            'rushing_yards', 'rushing_touchdowns', 'fantasy_points'
        ]
    elif selected_position == 'RB':
        columns = [
            'rank', 'player', 'team', 'opp',
            'rushing_attempts', 'rushing_yards', 'rushing_touchdowns',
            'targets', 'receptions', 'receiving_yards',
            'receiving_touchdowns', 'fantasy_points'
        ]
    else:
        columns = [
            'rank', 'player', 'team', 'opp',
            'targets', 'receptions', 'receiving_yards',
            'receiving_touchdowns', 'rushing_yards',
            'rushing_touchdowns', 'fantasy_points'
        ]

    clean_field_names = [c.replace('_', ' ').title() for c in columns]

    # Sorting logic (default: fantasy_points desc)
    sort_field = request.GET.get('sort_field', 'fantasy_points')
    sort_direction = request.GET.get('sort_direction', 'desc')
    order_prefix = '-' if sort_direction == 'desc' else ''

    queryset = (
        selected_model.objects
        .filter(week=selected_week)
        .order_by(f'{order_prefix}{sort_field}')
        .values(*columns)
    )

    # Convert values + filter out zero-point players
    records = [
        convert_numeric_values(row, exclude_keys=['fantasy_points'])
        for row in queryset
        if row.get('fantasy_points', 0) > 0
    ]

    return render(request, "weekly_rankings.html", {
        "records": records,
        "all_positions": list(position_models.keys()),
        "selected_position": selected_position,
        "weeks_list": weeks_list,
        "selected_week": selected_week,
        "fields": list(zip(columns, clean_field_names)),
        "selected_sort_field": sort_field,
        "selected_sort_direction": sort_direction
    })


def defense_weekly_stats(request):
    """
    Show how a defense performs against a given position.
    """

    team = request.GET.get("team")
    position = request.GET.get("position", 'QB')

    # Dynamically select relevant columns for chosen position
    all_columns = ['week', 'offense'] + [
        col.name for col in weekly_defense_stats._meta.concrete_fields
        if position.lower() in col.name.lower()
    ]

    def clean_column_name(col):
        """Make column names user-friendly for UI display."""
        if col == 'week':
            return col
        if col == 'offense':
            return 'Opposing Offense'

        col = col.lower()
        col = col.replace(f'opponent_{position.lower()}_', '')
        return col.replace('_', ' ').title() + f" to Opposing {position}s"

    clean_columns = [clean_column_name(c) for c in all_columns]

    queryset = (
        weekly_defense_stats.objects
        .filter(defense=team)
        .values(*all_columns)
        .order_by("week")
    )

    records = [
        convert_numeric_values(row, exclude_keys=['fantasy_points'])
        for row in queryset
    ]

    return render(request, "defense_stats.html", {
        "records": records,
        "columns": all_columns,
        "columns_to_show": clean_columns
    })


def season_rankings_view(request):
    """
    Render season-long rankings (Total or Average stats).
    """

    position_models = {
        "QB": (avg_qb_stats, total_qb_stats),
        "RB": (avg_rb_stats, total_rb_stats),
        "WR": (avg_wr_stats, total_wr_stats),
        "TE": (avg_te_stats, total_te_stats)
    }

    selected_position = request.GET.get("position", 'QB')
    selected_stat_type = request.GET.get('stat_type', 'Total')

    avg_model, total_model = position_models[selected_position]

    # Base columns
    if selected_position == 'QB':
        base_cols = [
            'rank', 'player', 'team',
            'passing_yards', 'passing_touchdowns', 'interceptions',
            'rushing_yards', 'rushing_touchdowns', 'fantasy_points'
        ]
    elif selected_position == 'RB':
        base_cols = [
            'rank', 'player', 'team',
            'rushing_attempts', 'rushing_yards', 'rushing_touchdowns',
            'targets', 'receptions', 'receiving_yards',
            'receiving_touchdowns', 'fantasy_points'
        ]
    else:
        base_cols = [
            'rank', 'player', 'team',
            'targets', 'receptions', 'receiving_yards',
            'receiving_touchdowns', 'rushing_yards',
            'rushing_touchdowns', 'fantasy_points'
        ]

    prefix = 'total_' if selected_stat_type == 'Total' else 'avg_'
    model = total_model if selected_stat_type == 'Total' else avg_model

    fields = ['rank', 'player', 'team'] + [
        f"{prefix}{c}" for c in base_cols if c not in ['rank', 'player', 'team']
    ]

    sort_field = request.GET.get(
        'sort_field',
        f"{prefix}fantasy_points"
    )

    sort_direction = request.GET.get('sort_direction', 'desc')
    order_prefix = '-' if sort_direction == 'desc' else ''

    queryset = (
        model.objects
        .order_by(f'{order_prefix}{sort_field}')
        .values(*fields)
    )

    records = [
        convert_numeric_values(row)
        for row in queryset
    ]

    clean_field_names = [f.replace('_', ' ').title() for f in fields]

    return render(request, "season_rankings.html", {
        "records": records,
        "all_positions": list(position_models.keys()),
        "selected_position": selected_position,
        "fields": list(zip(fields, clean_field_names)),
        "selected_stat_type": selected_stat_type,
        "selected_sort_field": sort_field,
        "selected_sort_direction": sort_direction
    })


def player_stats_view(request):
    """
    Display player-level weekly stats + optional chart view.
    """

    position_models = {
        "QB": weekly_qb_stats,
        "RB": weekly_rb_stats,
        "WR": weekly_wr_stats,
        "TE": weekly_te_stats
    }

    selected_position = request.GET.get('position', 'QB')
    model = position_models[selected_position]

    player_list = sorted(
        model.objects.values_list('player', flat=True).distinct()
    )

    selected_player = request.GET.get(
        'player',
        player_list[0] if player_list else None
    )

    queryset = (
        model.objects
        .filter(player=selected_player)
        .order_by('week')
    )

    # Columns per position
    if selected_position == 'QB':
        columns = [
            'week', 'passing_attempts', 'passing_yards',
            'passing_touchdowns', 'interceptions',
            'rushing_attempts', 'rushing_yards',
            'rushing_touchdowns', 'fantasy_points'
        ]
    elif selected_position == 'RB':
        columns = [
            'week', 'rushing_attempts', 'rushing_yards',
            'rushing_touchdowns', 'targets', 'receptions',
            'receiving_yards', 'receiving_touchdowns',
            'fantasy_points'
        ]
    else:
        columns = [
            'week', 'targets', 'receptions',
            'receiving_yards', 'receiving_touchdowns',
            'fantasy_points'
        ]

    records = [
        convert_numeric_values(row, exclude_keys=['fantasy_points'])
        for row in queryset.values(*columns)
    ]

    # Chart configuration
    metric_options = [c for c in columns if c != 'week']
    selected_metric = request.GET.get('metric', metric_options[0])

    chart_data = [r[selected_metric] for r in records]
    weeks = [r['week'] for r in records]

    return render(request, "player_stats.html", {
        "records": records,
        "all_view_types": ['table', 'chart'],
        "selected_view_type": request.GET.get("view", "table"),
        "all_positions": list(position_models.keys()),
        "selected_position": selected_position,
        "all_players": player_list,
        "selected_player": selected_player,
        "team": queryset.values('team')[0]['team'] if records else None,
        "weeks_list": json.dumps(weeks),
        "clean_field_names": [c.replace("_", " ").title() for c in columns],
        "chart_columns": zip(columns, [c.replace("_", " ").title() for c in columns]),
        "data": json.dumps(chart_data, default=float),
        "selected_player_chart_metric_name": selected_metric
    })