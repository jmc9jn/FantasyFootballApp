# stats/management/commands/load_stats.py

import os
import boto3
import pandas as pd
from django.core.management.base import BaseCommand
from stats.models import weekly_qb_stats, weekly_rb_stats, weekly_wr_stats, weekly_te_stats, weekly_defense_stats

#Allows user to run script Django custom cli command
class Command(BaseCommand):
    help = 'Load weekly player stats from S3 into the database'

    def handle(self, *args, **kwargs):
        s3 = boto3.client('s3')
        bucket = 'uva-fantasy-football'
        base_prefix = 'data/weekly_stats/2025/'

        positions = {
            'qb': (weekly_qb_stats, 'qb_weekly_stats.csv'),
            'rb': (weekly_rb_stats, 'rb_weekly_stats.csv'),
            'wr': (weekly_wr_stats, 'wr_weekly_stats.csv'),
            'te': (weekly_te_stats, 'te_weekly_stats.csv'),
            'def': (weekly_defense_stats, 'defense_weekly_stats.csv'),
        }

        #Delete all previous data
        for model, _ in positions.values():
            model.objects.all().delete()

        # Iterate over weeks
        for week_num in range(1, 18):  # assuming 17 weeks
            prefix = f"{base_prefix}week_{week_num}/processed/"

            for pos, (model, filename) in positions.items():
                key = prefix + filename
                print(f"Processing: {key}")

                try:
                    obj = s3.get_object(Bucket=bucket, Key=key)
                    df = pd.read_csv(obj['Body'])

                    records = []
                    model_fields = [f.name for f in model._meta.fields if f.name != 'id']
                    for _, row in df.iterrows():
                        data = {field: row[field] for field in model_fields if field in row}
                        record = model(**data)
                        records.append(record)

                    #Bulk insert data into models
                    model.objects.bulk_create(records, batch_size=1000)

                    #Rank players based on number of fantasy points
                    if pos != 'def':
                        sorted_model = model.objects.filter(week = week_num).order_by('-fantasy_points')
                        for rank, player in enumerate(sorted_model, start = 1):
                            player.rank = rank
                            player.save()


                    print(f"Loaded {len(records)} {pos.upper()} records for week {week_num}")

                except s3.exceptions.NoSuchKey:
                    print(f"File not found: {key}")
                except Exception as e:
                    print(f"Error loading {key}: {e}")
