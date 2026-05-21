from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = PROJECT_ROOT / "data" / "dataset.joblib"
MAX_CLIENT_NAMES = 100
MAX_NON_NUMERIC_SAMPLES = 30


def get_client_name(record: Any) -> str | None:
    if isinstance(record, dict):
        value = record.get("client_name")
    else:
        value = getattr(record, "client_name", None)
    if value is None:
        return None
    return str(value)


def main() -> None:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    records = joblib.load(DATASET_PATH)
    client_names = [get_client_name(record) for record in records]
    present_client_names = [name for name in client_names if name is not None]
    numeric_names = [name for name in present_client_names if name.isdigit()]
    non_numeric_names = [name for name in present_client_names if not name.isdigit()]

    print("Account identity inspection")
    print(f"dataset_path: {DATASET_PATH}")
    print(f"total_records: {len(records)}")
    print(f"records_with_client_name: {len(present_client_names)}")
    print(f"numeric_only_client_name_count: {len(numeric_names)}")
    print(f"non_numeric_client_name_count: {len(non_numeric_names)}")

    print(f"\nfirst_{min(MAX_CLIENT_NAMES, len(present_client_names))}_client_name_values:")
    for name in present_client_names[:MAX_CLIENT_NAMES]:
        print(f"- {name}")

    if non_numeric_names:
        print(
            f"\nsample_non_numeric_client_name_values_"
            f"{min(MAX_NON_NUMERIC_SAMPLES, len(non_numeric_names))}:"
        )
        for name in non_numeric_names[:MAX_NON_NUMERIC_SAMPLES]:
            print(f"- {name}")
    else:
        print("\nsample_non_numeric_client_name_values: none")


if __name__ == "__main__":
    main()
