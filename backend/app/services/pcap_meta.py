from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple

import dpkt


def _open_reader(f):
    """
    dpkt поддерживает pcap.Reader и pcapng.Reader.
    Требование у тебя pcap, но на всякий случай пытаемся оба.
    """
    try:
        return dpkt.pcap.Reader(f), "pcap"
    except (ValueError, dpkt.dpkt.NeedData):
        f.seek(0)
        return dpkt.pcapng.Reader(f), "pcapng"


def analyze_capture(path: str | Path) -> tuple[datetime | None, datetime | None, int, str]:
    """
    Возвращает (t_min, t_max, packets_count, fmt)
    Время в UTC.
    """
    path = Path(path)
    count = 0
    t_min = None
    t_max = None

    with path.open("rb") as f:
        reader, fmt = _open_reader(f)
        for ts, _buf in reader:
            count += 1
            if t_min is None:
                t_min = ts
            t_max = ts

    dt_min = datetime.fromtimestamp(t_min, tz=timezone.utc) if t_min is not None else None
    dt_max = datetime.fromtimestamp(t_max, tz=timezone.utc) if t_max is not None else None
    return dt_min, dt_max, count, fmt


def export_pcap_segment(
    in_path: str | Path,
    out_path: str | Path,
    t_from: datetime,
    t_to: datetime,
) -> int:
    """
    Создает новый pcap с пакетами в диапазоне [t_from, t_to].
    Возвращает количество записанных пакетов.
    """
    in_path = Path(in_path)
    out_path = Path(out_path)

    # dt -> float timestamp (UTC)
    if t_from.tzinfo is None:
        t_from = t_from.replace(tzinfo=timezone.utc)
    if t_to.tzinfo is None:
        t_to = t_to.replace(tzinfo=timezone.utc)
    ts_from = t_from.timestamp()
    ts_to = t_to.timestamp()

    written = 0
    with in_path.open("rb") as fin:
        reader, fmt = _open_reader(fin)
        if fmt != "pcap":
            # V1: экспортируем только pcap (по требованиям); pcapng можно добавить позже
            raise ValueError("Only pcap export is supported in V1")

        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("wb") as fout:
            writer = dpkt.pcap.Writer(fout)
            for ts, buf in reader:
                if ts < ts_from:
                    continue
                if ts > ts_to:
                    break
                writer.writepkt(buf, ts=ts)
                written += 1

    return written