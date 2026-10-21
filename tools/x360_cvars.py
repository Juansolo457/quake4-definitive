"""Recover the idCVar table (name, default, flags, min/max, description) from a
decrypted Xbox 360 image (xexdump output).

On the 360 build static idCVars are initialized data in .data:
    +0  vtable   +4  name   +8  default   +12 description   +16 flags
    +20 valueMin (float)   +24 valueMax (float)
The vtable is found from the object whose name is "com_showFPS" (falls back to the
most common word preceding a cvar-like name pointer).

    python -P tools/x360_cvars.py game/xex/default > game/xex/cvars.tsv
"""

import collections
import re
import struct
import sys

BASE = 0x82000000
FLAG_NAMES = [
    (0x1, "BOOL"), (0x2, "INTEGER"), (0x4, "FLOAT"), (0x8, "SYSTEM"), (0x10, "RENDERER"),
    (0x20, "SOUND"), (0x40, "GUI"), (0x80, "GAME"), (0x100, "TOOL"), (0x200, "USERINFO"),
    (0x400, "SERVERINFO"), (0x800, "NETWORKSYNC"), (0x1000, "STATIC"), (0x2000, "CHEAT"),
    (0x4000, "NOCHEAT"), (0x8000, "INIT"), (0x10000, "ROM"), (0x20000, "ARCHIVE"),
]
NAME_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9]{0,9}_[A-Za-z0-9_]+")


def load(prefix):
    data = open(prefix + ".bin", "rb").read()
    sections = {}
    for line in open(prefix + ".sections.txt"):
        name, base, size = line.split()[:3]
        sections[name] = (int(base, 16), int(size, 16))
    return data, sections


def c_string(data, address):
    off = address - BASE
    if off < 0 or off >= len(data):
        return None
    end = data.find(b"\0", off, off + 2048)
    if end < 0:
        return None
    raw = data[off:end]
    if not all(0x20 <= b < 0x7F or b in (9, 10, 13) for b in raw):
        return None
    return raw.decode("latin1")


def flag_text(flags):
    return "|".join(n for bit, n in FLAG_NAMES if flags & bit)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    data, sections = load(sys.argv[1])
    data_base, data_size = sections[".data"]
    start = data_base - BASE
    words = struct.unpack_from(f">{data_size // 4}I", data, start)

    # vtable: the word before name pointers that look like cvar names
    candidates = collections.Counter()
    for i in range(1, len(words)):
        name = c_string(data, words[i])
        if name and NAME_RE.fullmatch(name):
            candidates[words[i - 1]] += 1
    vtable = candidates.most_common(1)[0][0]

    rows = []
    for i in range(len(words) - 7):
        if words[i] != vtable:
            continue
        name = c_string(data, words[i + 1])
        value = c_string(data, words[i + 2])
        desc = c_string(data, words[i + 3])
        if not name or value is None:
            continue
        flags = words[i + 4]
        vmin, vmax = struct.unpack_from(">ff", data, start + (i + 5) * 4)
        rows.append((name, value, flags, vmin, vmax, (desc or "").strip().replace("\n", " "), data_base + i * 4))

    print("name\tdefault\tflags\tmin\tmax\tdescription\tobject")
    for name, value, flags, vmin, vmax, desc, obj in sorted(rows, key=lambda r: r[0].lower()):
        rng = ("", "") if vmin > vmax else (f"{vmin:g}", f"{vmax:g}")
        print(f"{name}\t{value}\t{flag_text(flags)}\t{rng[0]}\t{rng[1]}\t{desc}\t0x{obj:08X}")
    print(f"vtable 0x{vtable:08X}: {len(rows)} cvars", file=sys.stderr)


if __name__ == "__main__":
    main()
