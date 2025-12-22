import pandas as pd
import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "FantasyFootballApp.settings")
django.setup()

from stats.models import *

rb = avg_rb_stats.objects.all()
wr = avg_wr_stats.objects.all()
wr = weekly_wr_stats.objects.all()
df = pd.DataFrame.from_records(rb.values())
df2 = pd.DataFrame.from_records(wr.values())
df3 = pd.DataFrame.from_records(wr.values())
print(df.loc[:,['player','rushing_yards']].sort_values(by='rushing_yards', ascending=False))
print(df2.loc[:, ['player','receiving_yards']].sort_values(by='receiving_yards', ascending=False))
print(df3.loc[df3.player.str.contains('Jaxon')])