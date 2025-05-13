from pathlib import Path


from evalscan.cli import index, scan, report


def test_index(tmp_path):
    index(
        logs_dir=Path(__file__).parent / "assets" / "cybench-100",
        db_uri=tmp_path / "cybench-100.db",
    )


def test_scan(tmp_path):
    index(
        logs_dir=Path(__file__).parent / "assets" / "cybench-100",
        db_uri=tmp_path / "cybench-100.db",
    )
    scan(db_uri=tmp_path / "cybench-100.db")


def test_report(tmp_path):
    index(
        logs_dir=Path(__file__).parent / "assets" / "cybench-100",
        db_uri=tmp_path / "cybench-100.db",
    )
    scan(db_uri=tmp_path / "cybench-100.db")
    report(db_uri=tmp_path / "cybench-100.db")
