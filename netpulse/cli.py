"""Command-line interface for NetPulse."""
import argparse
from .probe import probe_many
from .report import export_csv, export_json

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check network reachability, latency and packet loss.")
    parser.add_argument("--targets", required=True, help="Comma-separated IP addresses or hostnames")
    parser.add_argument("--count", type=int, default=4, help="Echo requests per host (1-20)")
    parser.add_argument("--timeout", type=int, default=2, help="Timeout per request in seconds (1-10)")
    parser.add_argument("--workers", type=int, default=8, help="Maximum concurrent hosts (1-32)")
    parser.add_argument("--format", choices=("table", "json", "csv"), default="table", help="Output format")
    parser.add_argument("--output", help="Write JSON/CSV report to this file")
    return parser

def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    targets = [item.strip() for item in args.targets.split(",") if item.strip()]
    try:
        results = probe_many(targets, args.count, args.timeout, args.workers)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 2
    if args.format == "json":
        import json
        rendered = json.dumps([r.to_dict() for r in results], indent=2)
    elif args.format == "csv":
        import csv, io
        from .report import FIELDS
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(r.to_dict() for r in results)
        rendered = buffer.getvalue()
    else:
        headers = ("TARGET", "STATUS", "REPLIES", "LOSS", "AVG LATENCY", "DETAIL")
        rows = [(r.target, "UP" if r.reachable else "NO REPLY", f"{r.received}/{r.sent}", f"{r.packet_loss_percent:.1f}%", f"{r.average_latency_ms:.2f} ms" if r.average_latency_ms is not None else "—", r.error or "") for r in results]
        widths = [max(len(headers[i]), *(len(row[i]) for row in rows)) for i in range(len(headers))]
        rendered = "  ".join(headers[i].ljust(widths[i]) for i in range(len(headers))) + "\n"
        rendered += "  ".join("-" * widths[i] for i in range(len(headers))) + "\n"
        rendered += "\n".join("  ".join(row[i].ljust(widths[i]) for i in range(len(headers))) for row in rows)
    if args.output:
        if args.format == "json":
            export_json(results, args.output)
        elif args.format == "csv":
            export_csv(results, args.output)
        else:
            from pathlib import Path
            Path(args.output).write_text(rendered, encoding="utf-8")
        print(f"Report saved to {args.output}")
    print(rendered)
    return 0
