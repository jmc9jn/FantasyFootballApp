import boto3
import io
import pandas as pd

def read_from_bucket(key):
    bucket_name = 'uva-fantasy-football'
    s3 = boto3.client('s3')

    obj = s3.get_object(Bucket=bucket_name, Key=key)
    df = pd.read_csv(io.BytesIO(obj['Body'].read()))

    return df

df = read_from_bucket("data/weekly_stats/2025/week_1/processed/wr_weekly_stats.csv")
for col in df.columns:
    col_name = col.lower().replace(' ', '_')
    if pd.api.types.is_numeric_dtype(df[col]):
        print(f"    {col_name} = models.FloatField(null=True, blank=True)")
    else:
        print(f"    {col_name} = models.CharField(max_length=255, null=True, blank=True)")

