"""Report formatting and export helpers."""
import csv
import json
from pathlib import Path
from typing import Iterable
from .probe import ProbeResult

FIELDS = ["target", "reachable", "sent", "received", "packet_loss_percent", "average_latency_ms", "error"]

def export_json(results: Iterable[ProbeResult], destination: str | Path) -> None:
    Path(destination).write_text(json.dumps([r.to_dict() for r in results], indent=2), encoding="utf-8")

def export_csv(results: Iterable[ProbeResult], destination: str | Path) -> None:
    with Path(destination).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(r.to_dict() for r in results)
