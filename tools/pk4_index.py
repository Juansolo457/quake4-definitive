"""Index the .pk4 archives of a Quake 4 install.

Writes a full file listing (CSV) and a markdown summary. The listing holds
paths, sizes and CRCs only; no game data is extracted.

    python -I tools/pk4_index.py "E:/SteamLibrary/steamapps/common/Quake 4" inventory/pc
"""

import csv
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath


def ext_of(name):
    suffix = PurePosixPath(name).suffix.lower()
    return suffix or "(none)"


def top_dir(name):
    parts = PurePosixPath(name).parts
    return parts[0] if len(parts) > 1 else "(root)"


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    install = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    pak_stats = []
    for pk4 in sorted(install.rglob("*.pk4")):
        mod = pk4.parent.name
        with zipfile.ZipFile(pk4) as zf:
            infos = [i for i in zf.infolist() if not i.is_dir()]
        pak_stats.append((mod, pk4.name, pk4.stat().st_size, len(infos)))
        for info in infos:
            rows.append({
                "mod": mod,
                "pak": pk4.name,
                "path": info.filename,
                "size": info.file_size,
                "crc32": f"{info.CRC:08x}",
            })

    with open(out_dir / "files.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["mod", "pak", "path", "size", "crc32"])
        writer.writeheader()
        writer.writerows(rows)

    # Later paks override earlier ones (id Tech 4 search order is reverse alphabetical).
    by_path = defaultdict(list)
    for row in rows:
        by_path[(row["mod"], row["path"].lower())].append(row["pak"])
    overridden = {k: v for k, v in by_path.items() if len(v) > 1}

    exts = Counter()
    ext_bytes = Counter()
    dirs = Counter()
    for row in rows:
        exts[ext_of(row["path"])] += 1
        ext_bytes[ext_of(row["path"])] += row["size"]
        dirs[(row["mod"], top_dir(row["path"]))] += 1

    lines = ["# PC data inventory", "", f"Source: `{install}`", ""]
    lines += ["## Archives", "", "| mod | pak | size (MB) | files |", "|---|---|---:|---:|"]
    for mod, name, size, count in pak_stats:
        lines.append(f"| {mod} | {name} | {size / 1e6:.1f} | {count} |")
    lines += ["", f"Total files: {len(rows)}; paths present in more than one pak: {len(overridden)}", ""]

    lines += ["## By extension", "", "| ext | files | uncompressed (MB) |", "|---|---:|---:|"]
    for ext, count in exts.most_common():
        lines.append(f"| {ext} | {count} | {ext_bytes[ext] / 1e6:.1f} |")

    lines += ["", "## By top-level directory", "", "| mod | dir | files |", "|---|---|---:|"]
    for (mod, d), count in sorted(dirs.items()):
        lines.append(f"| {mod} | {d} | {count} |")

    (out_dir / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(pak_stats)} paks, {len(rows)} files -> {out_dir}")


if __name__ == "__main__":
    main()
