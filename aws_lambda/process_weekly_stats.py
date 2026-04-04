import boto3
import pandas as pd
import io

# -----------------------------
# AWS CONFIG
# -----------------------------
s3 = boto3.client("s3")
BUCKET_NAME = "uva-fantasy-football"

# Required input files before processing starts
REQUIRED_FILES = {
    "passing_stats.xlsx",
    "advanced_passing_air_yards_stats.xlsx",
    "advanced_passing_accuracy_stats.xlsx",
    "advanced_passing_pressure_stats.xlsx",
    "rushing_stats.xlsx",
    "receiving_stats.xlsx",
    "advanced_rushing_stats.xlsx",
    "advanced_receiving_stats.xlsx",
    "fumbles.xlsx",
    "snap_stats.xlsx",
}


# -----------------------------
# S3 HELPERS
# -----------------------------
def read_excel_from_s3(key: str, prefix: str) -> pd.DataFrame:
    """Load an Excel file from S3 into a pandas DataFrame."""
    obj = s3.get_object(Bucket=BUCKET_NAME, Key=prefix + key)
    return pd.read_excel(io.BytesIO(obj["Body"].read()))


def list_uploaded_files(prefix: str):
    """Return set of filenames currently uploaded under a prefix."""
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)
    contents = response.get("Contents", [])
    return {
        obj["Key"].split("/")[-1]
        for obj in contents
        if obj.get("Key")
    }


# -----------------------------
# LAMBDA ENTRY POINT
# -----------------------------
def lambda_handler(event, context):

    # Allow manual invocation (no S3 trigger)
    if "Records" not in event:
        return {
            "statusCode": 200,
            "body": "Manual invocation — no processing required.",
        }

    uploaded_key = event["Records"][0]["s3"]["object"]["key"]

    # Only process raw uploads
    if "/raw/" not in uploaded_key:
        return {
            "statusCode": 200,
            "body": "Ignored: not a raw upload.",
        }

    # Determine folder prefix
    prefix = "/".join(uploaded_key.split("/")[:-1]) + "/"

    # Check uploaded files in batch
    uploaded_files = list_uploaded_files(prefix)
    print(f"Detected files: {uploaded_files}")

    # Wait until all required inputs are present
    if not REQUIRED_FILES.issubset(uploaded_files):
        missing = REQUIRED_FILES - uploaded_files
        print(f"Waiting for files. Missing: {missing}")
        return {
            "statusCode": 200,
            "body": "Waiting for full dataset.",
        }

    # -----------------------------
    # LOAD INPUT DATA
    # -----------------------------
    passing = read_excel_from_s3("passing_stats.xlsx", prefix)
    air_yards = read_excel_from_s3("advanced_passing_air_yards_stats.xlsx", prefix)
    accuracy = read_excel_from_s3("advanced_passing_accuracy_stats.xlsx", prefix)
    pressure = read_excel_from_s3("advanced_passing_pressure_stats.xlsx", prefix)
    rushing = read_excel_from_s3("rushing_stats.xlsx", prefix)
    receiving = read_excel_from_s3("receiving_stats.xlsx", prefix)
    adv_rushing = read_excel_from_s3("advanced_rushing_stats.xlsx", prefix)
    adv_receiving = read_excel_from_s3("advanced_receiving_stats.xlsx", prefix)
    fumbles = read_excel_from_s3("fumbles.xlsx", prefix)
    snaps = read_excel_from_s3("snap_stats.xlsx", prefix)

    # -----------------------------
    # PROCESS DATA (your existing logic)
    # -----------------------------
    qb = create_qb_weekly_stats(passing, air_yards, accuracy, pressure, rushing, adv_rushing, fumbles, snaps)
    rb = create_rb_weekly_stats(rushing, receiving, adv_rushing, adv_receiving, fumbles, snaps)
    wr = create_wr_weekly_stats(receiving, adv_receiving, rushing, fumbles, snaps)
    te = create_te_weekly_stats(receiving, adv_receiving, rushing, fumbles, snaps)
    defense = create_weekly_defense_stats(qb, rb, wr, te)

    # -----------------------------
    # OUTPUT TO S3
    # -----------------------------
    processed_prefix = prefix.replace("/raw/", "/processed/")

    outputs = [
        ("qb", qb),
        ("rb", rb),
        ("wr", wr),
        ("te", te),
        ("defense", defense),
    ]

    for name, df in outputs:
        output_key = f"{processed_prefix}{name}_weekly_stats.csv"

        buffer = io.StringIO()
        df.to_csv(buffer, index=False)

        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=output_key,
            Body=buffer.getvalue(),
        )

        print(f"Uploaded: {output_key}")

    return {
        "statusCode": 200,
        "body": f"Processed dataset for {prefix}",
    }