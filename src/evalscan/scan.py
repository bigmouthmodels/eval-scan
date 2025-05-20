import duckdb

from evalscan.scanners import uniform

# uv run evalscan index --logs-dir /home/ubuntu/eval-scan/tests/assets/cybench-100 --db-uri cybench-100.db
# uv run evalscan scan --db-uri /home/ubuntu/eval-scan/cybench-100.db
# uvx harlequin cybench-100.db


import asyncio

import pandas as pd
from tqdm.asyncio import tqdm_asyncio


def apply_async(df, async_fn) -> pd.Series:
    async def run_all():
        tasks = [async_fn(row) for _, row in df.iterrows()]
        return await tqdm_asyncio.gather(*tasks)

    results = asyncio.run(run_all())
    return pd.Series(results, index=df.index)


# Probes
SCANNERS = [uniform]


def scan(db_uri):
    # List of scanners, list of messages to scan
    # Check if the message has already been scanned
    # If not, run the scanner
    # Need a dummy scanner to be able to do this
    con = duckdb.connect(db_uri)

    # Get the messages as a dataframe
    messages_df = con.execute("SELECT * FROM messages").df()

    # Get the scores as a dataframe
    # uuid, message id, score id, score, metadata
    con.execute("""
    CREATE TABLE IF NOT EXISTS message_scan (
        uuid UUID PRIMARY KEY NOT NULL,
        message_id VARCHAR NOT NULL,
        FOREIGN KEY (message_id) REFERENCES messages(message_id),
        sample_id VARCHAR NOT NULL,
        FOREIGN KEY (sample_id) REFERENCES samples(sample_id),
        eval_id VARCHAR NOT NULL,
        FOREIGN KEY (eval_id) REFERENCES evals(eval_id),
        scanner VARCHAR NOT NULL,
        value VARCHAR NOT NULL,
        input_tokens INT NOT NULL,
        output_tokens INT NOT NULL,
        metadata VARCHAR
    )
    """)

    for scanner in SCANNERS:
        scanner(messages_df, con)
