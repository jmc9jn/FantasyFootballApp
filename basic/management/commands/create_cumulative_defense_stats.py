from django.core.management.base import BaseCommand
from django.db.models import Sum, F, Window
from django.db.models.expressions import RowRange

from basic.models import weekly_defense_stats, total_defense_stats


# ============================================================
# Utility: Rolling cumulative sum generator
# ============================================================
def calculate_rolling_sum(field_name: str):
    """
    Creates a window function for cumulative sum by opponent over time.

    WHY:
    This enables time-series defensive accumulation metrics,
    such as total fantasy points allowed up to each week.
    """
    return Window(
        expression=Sum(F(field_name)),
        partition_by=[F("opp")],   # reset per opponent
        order_by=F("week").asc(),  # chronological accumulation
        frame=RowRange(start=None, end=0),
    )


# ============================================================
# Django Management Command
# ============================================================
class Command(BaseCommand):
    """
    Builds cumulative defensive statistics across weeks.

    This script:
    1. Computes rolling (season-to-date) defensive metrics
    2. Applies per-opponent window functions
    3. Stores results in an aggregated table for fast querying
    """

    help = "Create cumulative defense totals"

    def handle(self, *args, **kwargs):

        # --------------------------------------------------------
        # Step 1: Annotate cumulative metrics
        # --------------------------------------------------------
        qs = (
            weekly_defense_stats.objects
            .order_by("opp", "week")
            .annotate(

                # ---------------- QB allowed stats ----------------
                qb_fantasy_points=calculate_rolling_sum("opponent_qb_fantasy_points_allowed"),
                qb_passing_yards=calculate_rolling_sum("opponent_qb_passing_yards_allowed"),
                qb_rushing_yards=calculate_rolling_sum("opponent_qb_rushing_yards_allowed"),
                qb_passing_tds=calculate_rolling_sum("opponent_qb_passing_touchdowns_allowed"),

                # ---------------- RB allowed stats ----------------
                rb_fantasy_points=calculate_rolling_sum("opponent_rb_fantasy_points_allowed"),
                rb_rushing_yards=calculate_rolling_sum("opponent_rb_rushing_yards_allowed"),
                rb_receiving_yards=calculate_rolling_sum("opponent_rb_receiving_yards_allowed"),
                rb_rushing_tds=calculate_rolling_sum("opponent_rb_rushing_touchdowns_allowed"),
                rb_receiving_tds=calculate_rolling_sum("opponent_rb_receiving_touchdowns_allowed"),

                # ---------------- WR allowed stats ----------------
                wr_fantasy_points=calculate_rolling_sum("opponent_wr_fantasy_points_allowed"),
                wr_rushing_yards=calculate_rolling_sum("opponent_wr_rushing_yards_allowed"),
                wr_receiving_yards=calculate_rolling_sum("opponent_wr_receiving_yards_allowed"),
                wr_rushing_tds=calculate_rolling_sum("opponent_wr_rushing_touchdowns_allowed"),
                wr_receiving_tds=calculate_rolling_sum("opponent_wr_receiving_touchdowns_allowed"),

                # ---------------- TE allowed stats ----------------
                te_fantasy_points=calculate_rolling_sum("opponent_te_fantasy_points_allowed"),
                te_rushing_yards=calculate_rolling_sum("opponent_te_rushing_yards_allowed"),
                te_receiving_yards=calculate_rolling_sum("opponent_te_receiving_yards_allowed"),
                te_rushing_tds=calculate_rolling_sum("opponent_te_rushing_touchdowns_allowed"),
                te_receiving_tds=calculate_rolling_sum("opponent_te_receiving_touchdowns_allowed"),
            )
            .values(
                "opp", "week",

                "qb_fantasy_points",
                "qb_passing_yards",
                "qb_rushing_yards",
                "qb_passing_tds",

                "rb_fantasy_points",
                "rb_rushing_yards",
                "rb_receiving_yards",
                "rb_rushing_tds",
                "rb_receiving_tds",

                "wr_fantasy_points",
                "wr_rushing_yards",
                "wr_receiving_yards",
                "wr_rushing_tds",
                "wr_receiving_tds",

                "te_fantasy_points",
                "te_rushing_yards",
                "te_receiving_yards",
                "te_rushing_tds",
                "te_receiving_tds",
            )
        )

        # --------------------------------------------------------
        # Step 2: Convert queryset → model objects
        # --------------------------------------------------------
        objs = [total_defense_stats(**row) for row in qs]

        # --------------------------------------------------------
        # Step 3: Refresh table (ETL overwrite pattern)
        # --------------------------------------------------------
        total_defense_stats.objects.all().delete()
        total_defense_stats.objects.bulk_create(objs)