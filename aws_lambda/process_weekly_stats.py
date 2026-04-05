import boto3
import pandas as pd
import io

# =========================
# CONFIG
# =========================

s3 = boto3.client('s3')
BUCKET_NAME = 'uva-fantasy-football'

REQUIRED_FILES = {
    'passing_stats.xlsx',
    'advanced_passing_air_yards_stats.xlsx',
    'advanced_passing_accuracy_stats.xlsx',
    'advanced_passing_pressure_stats.xlsx',
    'rushing_stats.xlsx',
    'receiving_stats.xlsx',
    'advanced_rushing_stats.xlsx',
    'advanced_receiving_stats.xlsx',
    'fumbles.xlsx',
    'snap_stats.xlsx'
}


# =========================
# HELPERS
# =========================

def read_excel_from_s3(prefix, filename):
    obj = s3.get_object(Bucket=BUCKET_NAME, Key=prefix + filename)
    return pd.read_excel(io.BytesIO(obj['Body'].read()))


def upload_df_to_s3(df, key):
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    s3.put_object(Bucket=BUCKET_NAME, Key=key, Body=buffer.getvalue())
    print(f"Uploaded: {key}")


def calculate_fumbles(df, position):
    df = df[df['Pos.'] == position][['Player', 'Week', 'Team', 'Fmb', 'FR']]
    df['Fumbles_Lost'] = df['Fmb'] - df['FR']
    return df.drop(columns=['Fmb', 'FR'])


def get_snaps(df, position):
    return (
        df[df['Pos.'] == position][['Player', 'Week', 'Team', 'OffSnp', 'Off%']]
        .rename(columns={
            'OffSnp': 'Snaps_Played',
            'Off%': 'Snap_Percentage'
        })
    )


# =========================
# POSITION PROCESSING
# =========================

def create_qb_weekly_stats(passing, air_yards, accuracy, pressure,
                           rushing, advanced_rushing, fumbles, snaps):

    passing = passing.drop(columns=['Rk', 'Day', 'Unnamed: 9', -9999, 'Pos.'], errors='ignore')

    passing = passing.rename(columns={
        'Cmp': 'Completions',
        'Att': 'Passing_Attempts',
        'Yds': 'Passing_Yards',
        'TD': 'Passing_Touchdowns',
        'Int': 'Interceptions'
    })

    rushing = rushing[rushing['Pos.'] == 'QB'][[
        'Player', 'Week', 'Team', 'Att', 'Yds', 'TD'
    ]].rename(columns={
        'Att': 'Rushing_Attempts',
        'Yds': 'Rushing_Yards',
        'TD': 'Rushing_Touchdowns'
    })

    fumbles = calculate_fumbles(fumbles, 'QB')
    snaps = get_snaps(snaps, 'QB')

    qb_df = (
        passing
        .merge(air_yards, on=['Player', 'Week', 'Team'], how='left')
        .merge(accuracy, on=['Player', 'Week', 'Team'], how='left')
        .merge(pressure, on=['Player', 'Week', 'Team'], how='left')
        .merge(rushing, on=['Player', 'Week', 'Team'], how='left')
        .merge(advanced_rushing, on=['Player', 'Week', 'Team'], how='left')
        .merge(fumbles, on=['Player', 'Week', 'Team'], how='left')
        .merge(snaps, on=['Player', 'Week', 'Team'], how='left')
    ).fillna(0)

    qb_df['fantasy_points'] = (
        qb_df['Passing_Yards'] / 25 +
        qb_df['Passing_Touchdowns'] * 4 -
        qb_df['Interceptions'] +
        qb_df['Rushing_Yards'] / 10 +
        qb_df['Rushing_Touchdowns'] * 6 -
        qb_df['Fumbles_Lost'] * 2
    ).round(2)

    return qb_df.rename(columns=str.lower)


def create_rb_weekly_stats(rushing, receiving,
                           advanced_rushing, advanced_receiving,
                           fumbles, snaps):

    rushing = rushing[rushing['Pos.'] == 'RB'][[
        'Player', 'Week', 'Team', 'Att', 'Yds', 'TD'
    ]].rename(columns={
        'Att': 'Rushing_Attempts',
        'Yds': 'Rushing_Yards',
        'TD': 'Rushing_Touchdowns'
    })

    receiving = receiving[receiving['Pos.'] == 'RB'][[
        'Player', 'Week', 'Team', 'Tgt', 'Rec', 'Yds', 'TD'
    ]].rename(columns={
        'Tgt': 'Targets',
        'Rec': 'Receptions',
        'Yds': 'Receiving_Yards',
        'TD': 'Receiving_Touchdowns'
    })

    fumbles = calculate_fumbles(fumbles, 'RB')
    snaps = get_snaps(snaps, 'RB')

    rb_df = (
        rushing
        .merge(receiving, on=['Player', 'Week', 'Team'], how='left')
        .merge(advanced_rushing, on=['Player', 'Week', 'Team'], how='left')
        .merge(advanced_receiving, on=['Player', 'Week', 'Team'], how='left')
        .merge(fumbles, on=['Player', 'Week', 'Team'], how='left')
        .merge(snaps, on=['Player', 'Week', 'Team'], how='left')
    ).fillna(0)

    rb_df['fantasy_points'] = (
        rb_df['Rushing_Yards'] / 10 +
        rb_df['Rushing_Touchdowns'] * 6 +
        rb_df['Receptions'] * 0.5 +
        rb_df['Receiving_Yards'] / 10 +
        rb_df['Receiving_Touchdowns'] * 6 -
        rb_df['Fumbles_Lost'] * 2
    ).round(2)

    return rb_df.rename(columns=str.lower)


def create_wr_weekly_stats(receiving, advanced_receiving,
                           rushing, fumbles, snaps):

    receiving = receiving[receiving['Pos.'] == 'WR'][[
        'Player', 'Week', 'Team', 'Tgt', 'Rec', 'Yds', 'TD'
    ]].rename(columns={
        'Tgt': 'Targets',
        'Rec': 'Receptions',
        'Yds': 'Receiving_Yards',
        'TD': 'Receiving_Touchdowns'
    })

    rushing = rushing[rushing['Pos.'] == 'WR'][[
        'Player', 'Week', 'Team', 'Yds', 'TD'
    ]].rename(columns={
        'Yds': 'Rushing_Yards',
        'TD': 'Rushing_Touchdowns'
    })

    fumbles = calculate_fumbles(fumbles, 'WR')
    snaps = get_snaps(snaps, 'WR')

    wr_df = (
        receiving
        .merge(advanced_receiving, on=['Player', 'Week', 'Team'], how='left')
        .merge(rushing, on=['Player', 'Week', 'Team'], how='left')
        .merge(fumbles, on=['Player', 'Week', 'Team'], how='left')
        .merge(snaps, on=['Player', 'Week', 'Team'], how='left')
    ).fillna(0)

    wr_df['fantasy_points'] = (
        wr_df['Receptions'] * 0.5 +
        wr_df['Receiving_Yards'] / 10 +
        wr_df['Receiving_Touchdowns'] * 6 +
        wr_df['Rushing_Yards'] / 10 +
        wr_df['Rushing_Touchdowns'] * 6 -
        wr_df['Fumbles_Lost'] * 2
    ).round(2)

    return wr_df.rename(columns=str.lower)


def create_te_weekly_stats(receiving, advanced_receiving,
                           rushing, fumbles, snaps):

    receiving = receiving[receiving['Pos.'] == 'TE'][[
        'Player', 'Week', 'Team', 'Tgt', 'Rec', 'Yds', 'TD'
    ]].rename(columns={
        'Tgt': 'Targets',
        'Rec': 'Receptions',
        'Yds': 'Receiving_Yards',
        'TD': 'Receiving_Touchdowns'
    })

    rushing = rushing[rushing['Pos.'] == 'TE'][[
        'Player', 'Week', 'Team', 'Yds', 'TD'
    ]].rename(columns={
        'Yds': 'Rushing_Yards',
        'TD': 'Rushing_Touchdowns'
    })

    fumbles = calculate_fumbles(fumbles, 'TE')
    snaps = get_snaps(snaps, 'TE')

    te_df = (
        receiving
        .merge(advanced_receiving, on=['Player', 'Week', 'Team'], how='left')
        .merge(rushing, on=['Player', 'Week', 'Team'], how='left')
        .merge(fumbles, on=['Player', 'Week', 'Team'], how='left')
        .merge(snaps, on=['Player', 'Week', 'Team'], how='left')
    ).fillna(0)

    te_df['fantasy_points'] = (
        te_df['Receptions'] * 0.5 +
        te_df['Receiving_Yards'] / 10 +
        te_df['Receiving_Touchdowns'] * 6 +
        te_df['Rushing_Yards'] / 10 +
        te_df['Rushing_Touchdowns'] * 6 -
        te_df['Fumbles_Lost'] * 2
    ).round(2)

    return te_df.rename(columns=str.lower)


# =========================
# DEFENSE
# =========================

def create_weekly_defense_stats(qb, rb, wr, te):

    def aggregate(df, cols, label):
        grouped = (
            df.groupby(['team', 'opp', 'week'])[cols]
            .sum()
            .reset_index()
            .rename(columns={'team': 'offense', 'opp': 'defense'})
        )

        return grouped.rename(columns={
            col: f'opponent_{label}_{col}_allowed' for col in cols
        })

    qb_stats = aggregate(qb, ['fantasy_points', 'passing_yards'], 'qb')
    rb_stats = aggregate(rb, ['fantasy_points', 'rushing_yards'], 'rb')
    wr_stats = aggregate(wr, ['fantasy_points', 'receiving_yards'], 'wr')
    te_stats = aggregate(te, ['fantasy_points', 'receiving_yards'], 'te')

    return (
        qb_stats
        .merge(rb_stats, on=['offense', 'defense', 'week'], how='left')
        .merge(wr_stats, on=['offense', 'defense', 'week'], how='left')
        .merge(te_stats, on=['offense', 'defense', 'week'], how='left')
        .fillna(0)
        .round(2)
    )


# =========================
# LAMBDA HANDLER
# =========================

def lambda_handler(event, context):

    # Handle manual runs
    if "Records" not in event:
        return {"statusCode": 200, "body": "Manual run"}

    uploaded_key = event['Records'][0]['s3']['object']['key']

    if '/raw/' not in uploaded_key:
        return {"statusCode": 200, "body": "Skipping non-raw file"}

    prefix = '/'.join(uploaded_key.split('/')[:-1]) + '/'

    # Check files
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)
    uploaded_files = {
        obj['Key'].split('/')[-1]
        for obj in response.get('Contents', [])
    }

    if not REQUIRED_FILES.issubset(uploaded_files):
        return {"statusCode": 200, "body": "Waiting for all files"}

    # Load data
    passing = read_excel_from_s3(prefix, 'passing_stats.xlsx')
    air_yards = read_excel_from_s3(prefix, 'advanced_passing_air_yards_stats.xlsx')
    accuracy = read_excel_from_s3(prefix, 'advanced_passing_accuracy_stats.xlsx')
    pressure = read_excel_from_s3(prefix, 'advanced_passing_pressure_stats.xlsx')
    rushing = read_excel_from_s3(prefix, 'rushing_stats.xlsx')
    receiving = read_excel_from_s3(prefix, 'receiving_stats.xlsx')
    adv_rushing = read_excel_from_s3(prefix, 'advanced_rushing_stats.xlsx')
    adv_receiving = read_excel_from_s3(prefix, 'advanced_receiving_stats.xlsx')
    fumbles = read_excel_from_s3(prefix, 'fumbles.xlsx')
    snaps = read_excel_from_s3(prefix, 'snap_stats.xlsx')

    # Process
    qb = create_qb_weekly_stats(passing, air_yards, accuracy, pressure,
                               rushing, adv_rushing, fumbles, snaps)

    rb = create_rb_weekly_stats(rushing, receiving,
                               adv_rushing, adv_receiving,
                               fumbles, snaps)

    wr = create_wr_weekly_stats(receiving, adv_receiving,
                               rushing, fumbles, snaps)

    te = create_te_weekly_stats(receiving, adv_receiving,
                               rushing, fumbles, snaps)

    defense = create_weekly_defense_stats(qb, rb, wr, te)

    # Output
    processed_prefix = prefix.replace('/raw/', '/processed/')

    upload_df_to_s3(qb, processed_prefix + 'qb_weekly_stats.csv')
    upload_df_to_s3(rb, processed_prefix + 'rb_weekly_stats.csv')
    upload_df_to_s3(wr, processed_prefix + 'wr_weekly_stats.csv')
    upload_df_to_s3(te, processed_prefix + 'te_weekly_stats.csv')
    upload_df_to_s3(defense, processed_prefix + 'defense_weekly_stats.csv')

    return {
        "statusCode": 200,
        "body": f"Processed data for {prefix}"
    }
