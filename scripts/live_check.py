#!/usr/bin/env python3
"""Consistency check of ``detect`` / ``simulate`` against the recorder's raw data.

Read-only: calls only the two read-only services plus ``recorder/statistics_during_period``.
Nothing is written, and the read-only lock stays untouched.

It discovers the counters on the instance it is pointed at — no entity ids are hard-coded —
picks up to two per cycle type so every reset rule runs, and checks each preview against the
raw statistics:

* proposed sum == raw source delta − the outliers the preview says it removed
* reference delta == proposed sum (the integration's own plausibility figure)
* point count == number of hourly rows the recorder returns
* current end sum == the counter's last cumulative value
* monthly bars add up to the end sum, and none of them is negative
* the clamp warning only appears for a real gap, not for the hour grid
* **any** deviation from the raw value must be disclosed via ``source_outliers``

That last one is the point of the whole script: it is what would have caught a repair
quietly dropping several hundred kWh while reporting "0 outliers".

Usage:
    export HA_TOKEN=<long-lived access token>
    export HA_URL=ws://homeassistant.local:8123/api/websocket   # optional
    python3 scripts/live_check.py [--counters N] [--verbose]

Requires ``websockets`` (``pip install websockets``). Exits non-zero if any check fails.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

try:
    import websockets
except ImportError:  # pragma: no cover - dependency hint
    sys.exit("This script needs the 'websockets' package: pip install websockets")

DEFAULT_URL = "ws://homeassistant.local:8123/api/websocket"
TOLERANCE = 1.0  # same order as the integration's PLAUSI_TOLERANCE


class Client:
    """Minimal Home Assistant WebSocket client."""

    def __init__(self, ws, timezone_name: str = "UTC") -> None:
        self.ws = ws
        self.tz = ZoneInfo(timezone_name)
        self._id = 0

    async def call(self, message: dict) -> dict:
        self._id += 1
        message["id"] = self._id
        await self.ws.send(json.dumps(message))
        while True:
            reply = json.loads(await self.ws.recv())
            if reply.get("id") == self._id:
                return reply

    async def service(self, service: str, data: dict) -> dict:
        reply = await self.call({
            "type": "call_service", "domain": "statistics_toolset", "service": service,
            "service_data": data, "return_response": True,
        })
        if not reply.get("success"):
            raise RuntimeError(json.dumps(reply.get("error")))
        return reply["result"]["response"]

    async def statistics(self, statistic_id: str, start: str, end: str) -> list[dict]:
        reply = await self.call({
            "type": "recorder/statistics_during_period", "start_time": start,
            "end_time": end, "statistic_ids": [statistic_id], "period": "hour",
            "types": ["sum"],
        })
        rows = (reply.get("result") or {}).get(statistic_id, [])
        return [row for row in rows if row.get("sum") is not None]

    def service_time(self, utc_iso: str) -> str:
        """UTC ISO -> naive local string, which is what the services expect.

        The panel sends local time from its ``datetime-local`` field; passing UTC straight
        through shifts the range by the timezone offset and produces spurious warnings.
        """
        return datetime.fromisoformat(utc_iso).astimezone(self.tz).strftime("%Y-%m-%d %H:%M:%S")


class Report:
    def __init__(self, verbose: bool) -> None:
        self.verbose = verbose
        self.passed = 0
        self.failures: list[str] = []

    def check(self, condition: bool, label: str, detail: str = "") -> bool:
        if condition:
            self.passed += 1
            if self.verbose:
                print(f"    ok   {label}{(': ' + detail) if detail else ''}")
        else:
            self.failures.append(f"{label} — {detail}")
            print(f"    FAIL {label}: {detail}")
        return condition


async def check_range(
    ha: Client, report: Report, counter: str, detected: dict, label: str, start: str, end: str
) -> None:
    print(f"  [{label}] {start[:16]} .. {end[:16]}")
    try:
        preview = await ha.service("simulate", {
            "statistic_id": counter,
            "reference_id": detected.get("reference_id") or "",
            "cycle": detected["cycle"],
            "start": ha.service_time(start),
            "end": ha.service_time(end),
        })
    except RuntimeError as exc:
        # A refusal is fine as long as it explains itself.
        message = str(exc)
        explained = any(
            marker in message
            for marker in ("no cumulative data", "keine kumulativen", "outside", "no long-term")
        )
        report.check(explained, f"{counter} [{label}] error explains itself", message[:160])
        return

    source = detected.get("reference_id") or counter
    raw = await ha.statistics(source, start, end)
    if not raw:
        report.check(False, f"{counter} [{label}] source has data",
                     "simulate succeeded but the recorder returns nothing")
        return

    raw_delta = raw[-1]["sum"] - raw[0]["sum"]
    removed = preview.get("source_removed") or 0.0
    proposed = preview["proposed_end_sum"]

    report.check(
        abs((raw_delta - removed) - proposed) <= max(TOLERANCE, abs(proposed) * 1e-6),
        f"{counter} [{label}] sum == raw delta − removed outliers",
        f"{raw_delta:.3f} − {removed:.3f} vs. {proposed:.3f}",
    )
    report.check(abs(preview["reference_delta"] - proposed) <= TOLERANCE,
                 f"{counter} [{label}] reference delta == sum",
                 f"{preview['reference_delta']:.3f} vs. {proposed:.3f}")
    report.check(abs(preview["points"] - len(raw)) <= 1, f"{counter} [{label}] point count",
                 f"preview {preview['points']} vs. recorder {len(raw)}")

    current = await ha.statistics(counter, start, end)
    if current:
        report.check(abs(preview["current_end_sum"] - current[-1]["sum"]) <= TOLERANCE,
                     f"{counter} [{label}] current end sum",
                     f"{preview['current_end_sum']:.3f} vs. {current[-1]['sum']:.3f}")

    bars = preview.get("proposed_periods", [])
    total = sum(bar["value"] for bar in bars)
    report.check(abs(total - proposed) <= max(2.0, abs(proposed) * 0.01),
                 f"{counter} [{label}] bars add up", f"{total:.1f} vs. {proposed:.1f}")
    negative = [bar for bar in bars if bar["value"] < 0]
    report.check(not negative, f"{counter} [{label}] no negative bars", str(negative[:3]))

    for warning in preview.get("warnings", []):
        if warning.get("code") == "start_moved_up":
            moved = datetime.fromisoformat(warning["timestamp"])
            sent = datetime.strptime(ha.service_time(start), "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=ha.tz
            )
            gap = (moved - sent).total_seconds()
            report.check(gap > 3600, f"{counter} [{label}] clamp warning only for a real gap",
                         f"only {gap / 60:.0f} min — that is the hour grid, not a gap")
        if warning.get("code") == "source_outliers_removed":
            report.check(abs(warning.get("amount", 0) - removed) < 0.01,
                         f"{counter} [{label}] warning amount == source_removed",
                         f"{warning.get('amount')} vs. {removed}")

    # The important one: nothing may vanish silently.
    if abs(raw_delta - proposed) > TOLERANCE:
        report.check((preview.get("source_outliers") or 0) > 0,
                     f"{counter} [{label}] deviation from raw value is disclosed",
                     f"{raw_delta - proposed:.3f} missing, "
                     f"source_outliers={preview.get('source_outliers')}")


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--counters", type=int, default=2,
                        help="counters to check per cycle type (default 2)")
    parser.add_argument("--verbose", action="store_true", help="also print passing checks")
    args = parser.parse_args()

    token = os.environ.get("HA_TOKEN")
    if not token:
        return int(bool(sys.stderr.write("Set HA_TOKEN to a long-lived access token.\n")))
    url = os.environ.get("HA_URL", DEFAULT_URL)

    # ping_interval=None: a large simulation can occupy the connection longer than the
    # default keepalive timeout allows.
    async with websockets.connect(url, max_size=None, ping_interval=None) as ws:
        await ws.recv()
        await ws.send(json.dumps({"type": "auth", "access_token": token}))
        if json.loads(await ws.recv()).get("type") != "auth_ok":
            return int(bool(sys.stderr.write("Authentication failed.\n")))

        ha = Client(ws)
        config = await ha.call({"type": "get_config"})
        ha.tz = ZoneInfo(config["result"].get("time_zone", "UTC"))
        print(f"{url} — timezone {ha.tz}")

        report = Report(args.verbose)
        metadata = await ha.call({"type": "recorder/list_statistic_ids"})
        cumulative = sorted(
            entry["statistic_id"] for entry in metadata["result"]
            if entry.get("has_sum") and entry["statistic_id"].startswith("sensor.")
        )
        print(f"{len(cumulative)} sensors with cumulative statistics")

        by_cycle: dict[str, list[tuple[str, dict]]] = {}
        for statistic_id in cumulative:
            detected = await ha.service("detect", {"statistic_id": statistic_id})
            if detected.get("cycle_via") == "utility_meter":  # cycle known exactly
                by_cycle.setdefault(detected["cycle"], []).append((statistic_id, detected))
        print("cycles found:", {cycle: len(items) for cycle, items in sorted(by_cycle.items())})

        selection = [item for items in by_cycle.values() for item in items[: args.counters]]
        print(f"checking {len(selection)} counters\n")

        now = datetime.now(timezone.utc)
        for statistic_id, detected in selection:
            print(f"{statistic_id}  (cycle {detected['cycle']}, "
                  f"source {detected.get('reference_id') or 'self'})")
            ranges = []
            if detected.get("start"):
                ranges.append(("all", detected["start"], detected["end"]))
            ranges.append(("12 months", (now - timedelta(days=365)).isoformat(), now.isoformat()))
            ranges.append(("this year",
                           datetime(now.year, 1, 1, tzinfo=timezone.utc).isoformat(),
                           now.isoformat()))
            for label, start, end in ranges:
                await check_range(ha, report, statistic_id, detected, label, start, end)
            print()

        print("=" * 70)
        print(f"{report.passed} checks passed, {len(report.failures)} failed")
        for failure in report.failures:
            print(" -", failure)
        return 1 if report.failures else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
