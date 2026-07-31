#!/usr/bin/env python3
"""Clone a real counter into test statistics, then bend them into known-bad shapes.

Why clone instead of generating: synthetic ramps do not behave like a real meter — they have
no gaps, no daylight-saving jumps, no odd first hour. Cloning keeps that realism while every
written id carries ``test`` in its name, so fixing and restoring can be exercised without
going anywhere near the original data.

Safety rails:
* the source counter is only ever **read**
* every target id must contain ``test`` — the script refuses otherwise
* targets are plain statistic ids without an entity behind them, so no automation reacts
* combine with ``WRITE_ALLOWLIST`` in ``const.py`` to make the integration itself refuse
  everything but these ids

Usage:
    export HA_TOKEN=<long-lived access token>
    export HA_URL=ws://homeassistant.local:8123/api/websocket   # optional
    python3 scripts/make_test_sensors.py --source sensor.your_counter [--prefix …] [--dry-run]

Scenarios written (suffix after the prefix):
    clean   1:1 clone — a repair must leave this unchanged
    spike   one implausible jump inserted — outlier handling and disclosure
    gap     a week of points removed — clamping and range detection
    short   only the last 30 days — a counter younger than its source
    frozen  values stop increasing halfway — a stuck meter
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timedelta, timezone

try:
    import websockets
except ImportError:  # pragma: no cover
    sys.exit("This script needs the 'websockets' package: pip install websockets")

DEFAULT_URL = "ws://homeassistant.local:8123/api/websocket"
DEFAULT_PREFIX = "sensor.stat_toolset_test"
CHUNK = 5000  # points per import message, to stay well inside the WS message limit


class Client:
    def __init__(self, ws) -> None:
        self.ws = ws
        self._id = 0

    async def call(self, message: dict) -> dict:
        self._id += 1
        message["id"] = self._id
        await self.ws.send(json.dumps(message))
        while True:
            reply = json.loads(await self.ws.recv())
            if reply.get("id") == self._id:
                return reply

    async def read_history(self, statistic_id: str) -> list[dict]:
        reply = await self.call({
            "type": "recorder/statistics_during_period",
            "start_time": datetime(2015, 1, 1, tzinfo=timezone.utc).isoformat(),
            "statistic_ids": [statistic_id], "period": "hour", "types": ["state", "sum"],
        })
        rows = (reply.get("result") or {}).get(statistic_id, [])
        return [row for row in rows if row.get("sum") is not None]

    async def read_metadata(self, statistic_id: str) -> dict | None:
        reply = await self.call({"type": "recorder/list_statistic_ids"})
        for entry in reply.get("result", []):
            if entry["statistic_id"] == statistic_id:
                return entry
        return None

    async def count_points(self, statistic_id: str) -> tuple[int, float | None]:
        rows = await self.read_history(statistic_id)
        return len(rows), (rows[-1]["sum"] if rows else None)

    async def import_statistics(self, statistic_id: str, unit: str, rows: list[dict]) -> None:
        metadata = {
            "has_mean": False, "has_sum": True, "name": f"TEST {statistic_id}",
            "source": "recorder", "statistic_id": statistic_id,
            "unit_of_measurement": unit,
        }
        for offset in range(0, len(rows), CHUNK):
            chunk = rows[offset : offset + CHUNK]
            reply = await self.call({
                "type": "recorder/import_statistics", "metadata": metadata,
                "stats": [
                    {
                        "start": datetime.fromtimestamp(row["start"] / 1000, timezone.utc).isoformat(),
                        "state": row["state"] if row.get("state") is not None else row["sum"],
                        "sum": row["sum"],
                    }
                    for row in chunk
                ],
            })
            if not reply.get("success"):
                raise RuntimeError(json.dumps(reply.get("error")))


def scenario_clean(rows: list[dict]) -> list[dict]:
    return [dict(row) for row in rows]


def scenario_spike(rows: list[dict]) -> list[dict]:
    """Add an implausible jump in the middle and keep it in every later value.

    That is how a real corruption looks: the phantom amount stays in the cumulative sum
    instead of appearing as a single odd hour.
    """
    out = [dict(row) for row in rows]
    if len(out) < 10:
        return out
    middle = len(out) // 2
    jump = 250_000.0
    for row in out[middle:]:
        row["sum"] += jump
        if row.get("state") is not None:
            row["state"] += jump
    return out


def scenario_gap(rows: list[dict]) -> list[dict]:
    """Remove a week in the middle — the series continues afterwards, just without those hours."""
    if len(rows) < 400:
        return [dict(row) for row in rows]
    middle = len(rows) // 2
    return [dict(row) for i, row in enumerate(rows) if not middle <= i < middle + 168]


def scenario_short(rows: list[dict]) -> list[dict]:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).timestamp() * 1000
    return [dict(row) for row in rows if row["start"] >= cutoff]


def scenario_frozen(rows: list[dict]) -> list[dict]:
    """Values stop moving halfway through — a meter that died without saying so."""
    out = [dict(row) for row in rows]
    if len(out) < 10:
        return out
    middle = len(out) // 2
    frozen_sum = out[middle]["sum"]
    frozen_state = out[middle].get("state")
    for row in out[middle:]:
        row["sum"] = frozen_sum
        if frozen_state is not None:
            row["state"] = frozen_state
    return out


SCENARIOS = {
    "clean": scenario_clean,
    "spike": scenario_spike,
    "gap": scenario_gap,
    "short": scenario_short,
    "frozen": scenario_frozen,
}


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="counter to clone (read-only)")
    parser.add_argument("--prefix", default=DEFAULT_PREFIX,
                        help=f"target id prefix, must contain 'test' (default {DEFAULT_PREFIX})")
    parser.add_argument("--only", nargs="*", choices=sorted(SCENARIOS),
                        help="write only these scenarios")
    parser.add_argument("--dry-run", action="store_true", help="show what would be written")
    args = parser.parse_args()

    if "test" not in args.prefix.lower():
        return int(bool(sys.stderr.write("Refusing to run: --prefix must contain 'test'.\n")))
    token = os.environ.get("HA_TOKEN")
    if not token:
        return int(bool(sys.stderr.write("Set HA_TOKEN to a long-lived access token.\n")))

    async with websockets.connect(
        os.environ.get("HA_URL", DEFAULT_URL), max_size=None, ping_interval=None
    ) as ws:
        await ws.recv()
        await ws.send(json.dumps({"type": "auth", "access_token": token}))
        if json.loads(await ws.recv()).get("type") != "auth_ok":
            return int(bool(sys.stderr.write("Authentication failed.\n")))
        ha = Client(ws)

        meta = await ha.read_metadata(args.source)
        if not meta:
            return int(bool(sys.stderr.write(f"{args.source} has no statistics.\n")))
        unit = meta.get("display_unit_of_measurement") or meta.get("unit_of_measurement") or ""
        rows = await ha.read_history(args.source)
        if not rows:
            return int(bool(sys.stderr.write(f"{args.source} returned no rows.\n")))
        first = datetime.fromtimestamp(rows[0]["start"] / 1000, timezone.utc)
        last = datetime.fromtimestamp(rows[-1]["start"] / 1000, timezone.utc)
        print(f"source {args.source}: {len(rows)} points, {first:%Y-%m-%d} .. {last:%Y-%m-%d}, "
              f"unit {unit!r}")

        incomplete: list[str] = []
        wanted = args.only or sorted(SCENARIOS)
        for name in wanted:
            target = f"{args.prefix}_{name}"
            if "test" not in target.lower():  # belt and braces
                print(f"  skipping {target}: name does not contain 'test'")
                continue
            shaped = SCENARIOS[name](rows)
            if not shaped:
                print(f"  {name}: nothing to write (source too short)")
                continue
            span_first = datetime.fromtimestamp(shaped[0]["start"] / 1000, timezone.utc)
            print(f"  {target}: {len(shaped)} points from {span_first:%Y-%m-%d}, "
                  f"end sum {shaped[-1]['sum']:.1f}")
            if not args.dry_run:
                await ha.import_statistics(target, unit, shaped)
                # The WS command only acknowledges receipt; the recorder writes afterwards.
                # Without checking, an interrupted run (a restart, say) looks successful.
                written, end_sum = 0, None
                for _attempt in range(30):
                    await asyncio.sleep(1)
                    written, end_sum = await ha.count_points(target)
                    if written >= len(shaped):
                        break
                if written < len(shaped):
                    print(f"    INCOMPLETE: {written}/{len(shaped)} points arrived — "
                          f"run the script again for this scenario")
                    incomplete.append(target)
                else:
                    print(f"    verified: {written} points, end sum {end_sum:.1f}")

        if args.dry_run:
            print("\ndry run — nothing was written")
            return 0
        if incomplete:
            print(f"\n{len(incomplete)} scenario(s) incomplete: {', '.join(incomplete)}")
            return 1
        print("\nAll scenarios written and verified. Remove them later via "
              "Developer tools -> Statistics, where orphaned statistic ids can be deleted.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
