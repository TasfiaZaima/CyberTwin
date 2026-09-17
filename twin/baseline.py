"""Persistent baseline learning for device behavioral features."""
from __future__ import annotations
import argparse
import numpy as np
from database.db import Database, utc_now
from features.extractor import FEATURE_NAMES


def train_baseline(database: Database, device_id: str) -> dict[str, dict[str, float]]:
    rows = database.feature_rows(device_id, 10000)
    if len(rows) < 2:
        raise ValueError(f"At least two feature windows are required for {device_id}")
    result = {}
    for name in FEATURE_NAMES:
        values = np.asarray([float(row[name]) for row in rows], dtype=float)
        stats = {"mean": float(values.mean()), "std_dev": float(values.std()),
                 "min_value": float(values.min()), "max_value": float(values.max()),
                 "percentile_05": float(np.percentile(values, 5)),
                 "percentile_95": float(np.percentile(values, 95))}
        database.execute("""INSERT INTO baselines (device_id,feature_name,mean,std_dev,min_value,
          max_value,percentile_05,percentile_95,sample_count,trained_at) VALUES (?,?,?,?,?,?,?,?,?,?)
          ON CONFLICT(device_id,feature_name) DO UPDATE SET mean=excluded.mean,std_dev=excluded.std_dev,
          min_value=excluded.min_value,max_value=excluded.max_value,percentile_05=excluded.percentile_05,
          percentile_95=excluded.percentile_95,sample_count=excluded.sample_count,trained_at=excluded.trained_at""",
          [device_id, name, *stats.values(), len(values), utc_now()])
        result[name] = stats
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--device", required=True)
    args = parser.parse_args(); print(train_baseline(Database(), args.device))
