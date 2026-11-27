"""Safe, concurrent ICMP reachability checks using the system ping command."""
from __future__ import annotations

import ipaddress
import platform
import re
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from typing import Iterable

_HOST_RE = re.compile(r"^(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)(?:\.(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?))*\.?$")

@dataclass(frozen=True)
class ProbeResult:
    target: str
    reachable: bool
    sent: int
    received: int
    packet_loss_percent: float
    average_latency_ms: float | None
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def validate_target(target: str) -> str:
    value = target.strip()
    if not value or any(ch.isspace() for ch in value):
        raise ValueError(f"Invalid target: {target!r}")
    try:
        ipaddress.ip_address(value)
        return value
    except ValueError:
        if not _HOST_RE.fullmatch(value):
            raise ValueError(f"Target must be an IP address or hostname: {target!r}")
        return value


def _ping_command(target: str, count: int, timeout: int) -> list[str]:
    system = platform.system().lower()
    if system == "windows":
        return ["ping", "-n", str(count), "-w", str(timeout * 1000), target]
    if system == "darwin":
        return ["ping", "-c", str(count), "-W", str(timeout * 1000), target]
    return ["ping", "-c", str(count), "-W", str(timeout), target]


def probe_host(target: str, count: int = 4, timeout: int = 2) -> ProbeResult:
    target = validate_target(target)
    if not 1 <= count <= 20:
        raise ValueError("count must be between 1 and 20")
    if not 1 <= timeout <= 10:
        raise ValueError("timeout must be between 1 and 10 seconds")
    executable = shutil.which("ping")
    if not executable:
        return ProbeResult(target, False, count, 0, 100.0, None, "The ping utility was not found on this system.")
    command = _ping_command(target, count, timeout)
    command[0] = executable
    started = time.perf_counter()
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=count * timeout + 3, check=False)
    except subprocess.TimeoutExpired:
        return ProbeResult(target, False, count, 0, 100.0, None, "Ping command timed out.")
    except OSError as exc:
        return ProbeResult(target, False, count, 0, 100.0, None, str(exc))

    output = completed.stdout + "\n" + completed.stderr
    received = len(re.findall(r"\bbytes from\b", output, re.IGNORECASE))
    # Windows uses "Reply from" rather than "bytes from".
    if platform.system().lower() == "windows":
        received = len(re.findall(r"\breply from\b", output, re.IGNORECASE))
    latency_values = [float(x) for x in re.findall(r"(?:time[=<]\s*)(\d+(?:\.\d+)?)\s*ms", output, re.IGNORECASE)]
    average = round(sum(latency_values) / len(latency_values), 2) if latency_values else None
    # Some ping implementations use a summary average when individual replies differ in format.
    if average is None:
        match = re.search(r"=\s*[\d.]+\s*/\s*([\d.]+)\s*/", output)
        if match:
            average = float(match.group(1))
    loss_match = re.search(r"(\d+(?:\.\d+)?)%\s*packet loss", output, re.IGNORECASE)
    if loss_match:
        loss = float(loss_match.group(1))
        received = max(received, round(count * (100 - loss) / 100))
    else:
        loss = round((count - received) / count * 100, 2)
    return ProbeResult(target, received > 0, count, received, loss, average,
                       None if completed.returncode == 0 or received else "No ICMP replies received.")


def probe_many(targets: Iterable[str], count: int = 4, timeout: int = 2, workers: int = 8) -> list[ProbeResult]:
    cleaned = list(dict.fromkeys(validate_target(t) for t in targets))
    if not cleaned:
        raise ValueError("Provide at least one target")
    if not 1 <= workers <= 32:
        raise ValueError("workers must be between 1 and 32")
    results: dict[str, ProbeResult] = {}
    with ThreadPoolExecutor(max_workers=min(workers, len(cleaned))) as pool:
        futures = {pool.submit(probe_host, host, count, timeout): host for host in cleaned}
        for future in as_completed(futures):
            host = futures[future]
            try:
                results[host] = future.result()
            except ValueError as exc:
                results[host] = ProbeResult(host, False, count, 0, 100.0, None, str(exc))
    return [results[host] for host in cleaned]
