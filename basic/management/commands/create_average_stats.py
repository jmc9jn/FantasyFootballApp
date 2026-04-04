from django.core.management.base import BaseCommand
from django.db import models
from django.db.models import Avg

from basic.models import (
    weekly_qb_stats, weekly_rb_stats, weekly_wr_stats, weekly_te_stats,
    avg_qb_stats, avg_rb_stats, avg_wr_stats, avg_te_stats
)


class Command(BaseCommand):
    """
    Django management command to compute and persist
    average weekly statistics for NFL positions.

    This script:
    1. Aggregates per-player weekly stats
    2. Computes dynamic field averages
    3. Stores results in corresponding "avg_*" models
    4. Ranks players by fantasy performance
    """

    help = "Create/update average player statistics tables"

    def handle(self, *args, **kwargs):

        # Map position → (weekly model, aggregate model)
        model_map = {
            "qb": (weekly_qb_stats, avg_qb_stats),
            "rb": (weekly_rb_stats, avg_rb_stats),
            "wr": (weekly_wr_stats, avg_wr_stats),
            "te": (weekly_te_stats, avg_te_stats),
        }

        for position, (weekly_model, avg_model) in model_map.items():

            # ------------------------------------------------------------
            # Identify numeric fields to aggregate dynamically
            # ------------------------------------------------------------
            numeric_fields = [
                field.name
                for field in weekly_model._meta.fields
                if isinstance(field, (models.DecimalField, models.IntegerField))
                and field.name not in {"id", "week", "game_number", "rank"}
            ]

            # ------------------------------------------------------------
            # Aggregate per player
            # ------------------------------------------------------------
            players = weekly_model.objects.values_list("player", flat=True).distinct()

            for player in players:
                player_qs = weekly_model.objects.filter(player=player)

                if not player_qs.exists():
                    continue

                team = player_qs.first().team
                games_played = player_qs.count()

                # Dynamically build aggregation dictionary
                aggregation = {
                    f"avg_{field}": Avg(field)
                    for field in numeric_fields
                }

                avg_results = player_qs.aggregate(**aggregation)

                # Prepare model update payload
                defaults = {
                    "team": team,
                    "games_played": games_played,
                    **avg_results
                }

                avg_model.objects.update_or_create(
                    player=player,
                    defaults=defaults
                )

            # ------------------------------------------------------------
            # Ranking update (by fantasy points)
            # ------------------------------------------------------------
            sort_field = "avg_fantasy_points"

            ranked_players = avg_model.objects.all().order_by(f"-{sort_field}")

            for rank, player in enumerate(ranked_players, start=1):
                player.rank = rank
                player.save()