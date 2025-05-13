import duckdb

from evalscan.probes import dummy_probe

# uv run evalscan index --logs-dir /home/ubuntu/eval-scan/tests/assets/cybench-100 --db-uri cybench-100.db
# uv run evalscan scan --db-uri /home/ubuntu/eval-scan/cybench-100.db
# uvx harlequin cybench-100.db

# Probes
PROBES = [dummy_probe]


def scan(db_uri):
    # List of scanners, list of messages to scan
    # Check if the message has already been scanned
    # If not, run the scanner
    # Need a dummy scanner to be able to do this
    con = duckdb.connect(db_uri)

    # Get the messages as a dataframe
    df = con.execute("""
    SELECT *
    FROM tidy_eval_messages tem
    JOIN tidy_eval_sample_headers tesh ON tesh.raw_sample_uuid = tem.raw_sample_uuid
    JOIN tidy_eval_log_headers telh ON telh.raw_eval_log_header_uuid = tem.raw_log_uuid
    """).df()

    # Get the scores as a dataframe
    # uuid, message id, score id, score, metadata
    con.execute("""
    CREATE TABLE IF NOT EXISTS message_scores (
        uuid UUID PRIMARY KEY NOT NULL,
        message_uuid UUID NOT NULL,
        FOREIGN KEY (message_uuid) REFERENCES tidy_eval_messages(uuid),
        inserted TIMESTAMPTZ NOT NULL,
        score_name VARCHAR NOT NULL,
        score VARCHAR NOT NULL,
        input_tokens INT NOT NULL,
        output_tokens INT NOT NULL,
        metadata VARCHAR
    )
    """)

    for probe in PROBES:
        probe(df, con)  # Probe handles writing the score to the database too
