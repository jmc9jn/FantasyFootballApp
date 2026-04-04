from django.core.management.base import BaseCommand
from django.db import models
from django.db.models import Sum

from basic.models import (
    weekly_qb_stats, weekly_rb_stats, weekly_wr_stats, weekly_te_stats,
    total_qb_stats, total_rb_stats, total_wr_stats, total_te_stats
)


class Command(BaseCommand):
    """
    Management command to compute cumulative season totals
    for fantasy football player statistics.

    This process:
    1. Aggregates weekly stats into season totals per player
    2. Stores results in total_* models
    3. Ranks players by total fantasy points
    """

    help = "Create/update total (season aggregate) player statistics"

    def handle(self, *args, **kwargs):

        # ------------------------------------------------------------
        # Map position → (weekly model, total model)
        # ------------------------------------------------------------
        model_map = {
            "qb": (weekly_qb_stats, total_qb_stats),
            "rb": (weekly_rb_stats, total_rb_stats),
            "wr": (weekly_wr_stats, total_wr_stats),
            "te": (weekly_te_stats, total_te_stats),
        }

        for position, (weekly_model, total_model) in model_map.items():

            # ------------------------------------------------------------
            # Identify numeric fields dynamically
            # ------------------------------------------------------------
            numeric_fields = [
                field.name
                for field in weekly_model._meta.fields
                if isinstance(field, (models.DecimalField, models.IntegerField))
                and field.name not in {"id", "week", "game_number", "rank"}
            ]

            # ------------------------------------------------------------
            # Aggregate totals per player
            # ------------------------------------------------------------
            players = weekly_model.objects.values_list("player", flat=True).distinct()

            for player in players:
                player_qs = weekly_model.objects.filter(player=player)

                if not player_qs.exists():
                    continue

                team = player_qs.first().team
                games_played = player_qs.count()

                # Build dynamic SUM aggregation
                aggregation = {
                    f"total_{field}": Sum(field)
                    for field in numeric_fields
                }

                total_results = player_qs.aggregate(**aggregation)

                # Prepare model update payload
                defaults = {
                    "team": team,
                    "games_played": games_played,
                    **total_results
                }

                total_model.objects.update_or_create(
                    player=player,
                    defaults=defaults
                )

            # ------------------------------------------------------------
            # Rank players by fantasy performance
            # ------------------------------------------------------------
            ranked_players = total_model.objects.all().order_by("-total_fantasy_points")

            for rank, player in enumerate(ranked_players, start=1):
                player.rank = rank
                player.save()

        self.stdout.write(self.style.SUCCESS("Successfully computed total stats and rankings."))