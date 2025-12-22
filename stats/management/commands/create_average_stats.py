from django.core.management.base import BaseCommand
from stats.models import weekly_qb_stats, weekly_rb_stats, weekly_wr_stats, weekly_te_stats, avg_qb_stats, avg_rb_stats, avg_wr_stats, avg_te_stats
from django.db.models import Avg
from django.db import models

class Command(BaseCommand):
    help = 'create a table of average stats'
    def handle(self, *args, **kwargs):

        initial_data = {'qb':[weekly_qb_stats, avg_qb_stats], 'rb':[weekly_rb_stats, avg_rb_stats],
                        'wr':[weekly_wr_stats,avg_wr_stats], 'te':[weekly_te_stats,avg_te_stats]}
        for pos, data in initial_data.items():
            weekly_model = data[0]
            average_model = data[1]

            # Get numeric field names (excluding player, week, team, etc.)
            numeric_fields = [
                field.name for field in weekly_model._meta.fields
                if (isinstance(field, models.FloatField) or isinstance(field, models.IntegerField))
                and field.name not in ('id', 'week','game_number','rank')
            ]

            # Group by player/team
            players = weekly_model.objects.values_list('player', flat=True).distinct()

            for player in players:
                player_qs = weekly_model.objects.filter(player=player)
                if not player_qs.exists():
                    continue
                team = player_qs.first().team
                games_played = player_qs.count()

                # Dynamically build aggregation
                aggregation_kwargs = {f'avg_{field}': Avg(field) for field in numeric_fields}

                avg_results = player_qs.aggregate(**aggregation_kwargs)

                # Prepare defaults dict for SeasonQBStats
                defaults = {'team': team,
                            'games_played': games_played
                            }
                defaults.update(avg_results)
                # Save or update
                average_model.objects.update_or_create(
                    player=player,
                    defaults=defaults
                )

            sort_field = 'avg_fantasy_points'
            player_table = average_model.objects.all().order_by(f'-{sort_field}')
            for rank, player in enumerate(player_table, start=1):
                player.rank = rank
                player.save()

