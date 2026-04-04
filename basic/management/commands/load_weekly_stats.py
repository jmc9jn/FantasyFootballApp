import boto3
import pandas as pd

from django.core.management.base import BaseCommand

from basic.models import (
    weekly_qb_stats,
    weekly_rb_stats,
    weekly_wr_stats,
    weekly_te_stats,
    weekly_defense_stats,
)


class Command(BaseCommand):
    """
    Loads weekly fantasy football stats from S3 CSV files
    into Django database tables.

    Pipeline:
    1. Pull CSVs from S3 per week/position
    2. Convert to Django model instances
    3. Bulk insert into database
    4. Compute weekly rankings (non-defense only)
    """

    help = "Load weekly player stats from S3 into database"

    def handle(self, *args, **kwargs):

        # ------------------------------------------------------------
        # S3 Configuration
        # ------------------------------------------------------------
        s3 = boto3.client("s3")
        bucket = "uva-fantasy-football"
        base_prefix = "data/weekly_stats/2025/"

        # ------------------------------------------------------------
        # Position → Model mapping
        # ------------------------------------------------------------
        position_map = {
            "qb": (weekly_qb_stats, "qb_weekly_stats.csv"),
            "rb": (weekly_rb_stats, "rb_weekly_stats.csv"),
            "wr": (weekly_wr_stats, "wr_weekly_stats.csv"),
            "te": (weekly_te_stats, "te_weekly_stats.csv"),
            "def": (weekly_defense_stats, "defense_weekly_stats.csv"),
        }

        # ------------------------------------------------------------
        # Clear existing weekly data
        # ------------------------------------------------------------
        for model, _ in position_map.values():
            model.objects.all().delete()

        # ------------------------------------------------------------
        # Iterate over weeks
        # ------------------------------------------------------------
        for week_num in range(1, 18):  # NFL regular season weeks

            week_prefix = f"{base_prefix}week_{week_num}/processed/"

            for position, (model, filename) in position_map.items():

                s3_key = week_prefix + filename
                self.stdout.write(f"Processing: {s3_key}")

                try:
                    # ----------------------------------------------------
                    # Load CSV from S3
                    # ----------------------------------------------------
                    obj = s3.get_object(Bucket=bucket, Key=s3_key)
                    df = pd.read_csv(obj["Body"])

                    # ----------------------------------------------------
                    # Convert DataFrame → Django model instances
                    # ----------------------------------------------------
                    model_fields = [
                        f.name for f in model._meta.fields
                        if f.name != "id"
                    ]

                    records = [
                        model(**{
                            field: row[field]
                            for field in model_fields
                            if field in row
                        })
                        for _, row in df.iterrows()
                    ]

                    # ----------------------------------------------------
                    # Bulk insert into DB
                    # ----------------------------------------------------
                    model.objects.bulk_create(records, batch_size=1000)

                    # ----------------------------------------------------
                    # Compute weekly rankings (non-defense only)
                    # ----------------------------------------------------
                    if position != "def":
                        ranked_qs = (
                            model.objects
                            .filter(week=week_num)
                            .order_by("-fantasy_points")
                        )

                        for rank, player in enumerate(ranked_qs, start=1):
                            player.rank = rank
                            player.save()

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Loaded {len(records)} {position.upper()} records for week {week_num}"
                        )
                    )

                except s3.exceptions.NoSuchKey:
                    self.stdout.write(
                        self.style.WARNING(f"Missing file: {s3_key}")
                    )

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Error loading {s3_key}: {str(e)}")
                    )