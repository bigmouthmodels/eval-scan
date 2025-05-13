from pathlib import Path


from evalscan.index import index
from evalscan.scan import scan
from evalscan.report import report


def test_index(tmp_path):
    index(
        logs_dir=str(Path(__file__).parent / "assets" / "cybench-100"),
        db_uri=str(tmp_path / "cybench-100.db"),
    )


def test_scan(tmp_path):
    index(
        logs_dir=str(Path(__file__).parent / "assets" / "cybench-100"),
        db_uri=str(tmp_path / "cybench-100.db"),
    )
    scan(db_uri=str(tmp_path / "cybench-100.db"))


def test_report(tmp_path):
    index(
        logs_dir=str(Path(__file__).parent / "assets" / "cybench-100"),
        db_uri=str(tmp_path / "cybench-100.db"),
    )
    scan(db_uri=str(tmp_path / "cybench-100.db"))
    report(db_uri=str(tmp_path / "cybench-100.db"))
