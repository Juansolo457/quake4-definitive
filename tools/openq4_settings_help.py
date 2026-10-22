"""Add a help line under openQ4's Settings > Game Options list.

A panel below the list shows what the highlighted option does. Each row's
"<row>_hover" window sets the panel text when the mouse (or, with the menu
navigation patch, controller focus) enters the row and puts the default hint back
when it leaves. Strings go into every *_openq4.lang table in English, like the
other openQ4 strings. Safe to run again: rows that already set the panel are
skipped, and new rows get the next free string ids. Line endings are preserved.

    python -P tools/openq4_settings_help.py <openQ4 root> <help.json>

help.json:
{
  "page": "game",
  "first_id": 231309,                      # first string id to allocate
  "default": "Highlight an option ...",    # shown when no row is highlighted
  "rows": {"set_game_freelook": "Yes: the mouse looks ...", ...}
}
"""
import json
import re
import sys
from pathlib import Path

CRLF = {}


def read(path):
    raw = path.read_bytes().decode("utf-8", errors="surrogateescape")
    CRLF[path] = "\r\n" in raw
    return raw.replace("\r\n", "\n")


def write(path, text):
    if CRLF.get(path):
        text = text.replace("\n", "\r\n")
    path.write_bytes(text.encode("utf-8", errors="surrogateescape"))


def block_end(text, opening):
    """Index just past the brace that closes the one at text[opening]."""
    depth = 0
    for i in range(opening, len(text)):
        depth += (text[i] == "{") - (text[i] == "}")
        if depth == 0:
            return i + 1
    raise ValueError("unbalanced braces")


def insert_in_handler(block, handler, line):
    """Insert line at the end of handler's `if ("desktop::active" == 0)` body (or the handler's own body)."""
    m = re.search(rf"\b{handler}\s*\{{", block)
    if not m:
        raise ValueError(f"no {handler}")
    body_open = m.end() - 1
    body_close = block_end(block, body_open) - 1
    inner = re.compile(r'if\s*\(\s*"desktop::active"\s*==\s*0\s*\)\s*\{').search(block, body_open, body_close)
    if inner:
        target_close = block_end(block, inner.end() - 1) - 1
    else:
        target_close = body_close
    line_start = block.rfind("\n", 0, target_close) + 1
    indent = re.match(r"[ \t]*", block[line_start:]).group(0) + "\t"
    return block[:line_start] + indent + line + "\n" + block[line_start:]


def panel_block(panel, text_window, default_id):
    return (
        f"\t\t\t\twindowDef {panel}\n\t\t\t\t{{\n"
        f"\t\t\t\t\trect\t204,386,377,54\n\t\t\t\t\tvisible\t1\n\t\t\t\t\tnoevents\t1\n"
        f"\t\t\t\t\tbackground\t\"gfx/guis/mainmenu/b3_light\"\n"
        f"\t\t\t\t\tmatcolor\t0.545,0.588,0.294,0.25\n\n"
        f"\t\t\t\t\twindowDef {text_window}\n\t\t\t\t\t{{\n"
        f"\t\t\t\t\t\trect\t31,4,336,48\n\t\t\t\t\t\tvisible\t1\n\t\t\t\t\t\tnoevents\t1\n"
        f"\t\t\t\t\t\tforecolor\t1,1,1,0.8\n\t\t\t\t\t\ttext\t\"{default_id}\"\n"
        f"\t\t\t\t\t\ttextscale\t0.22\n\t\t\t\t\t\tfont\t\"fonts/lowpixel\"\n\t\t\t\t\t}}\n"
        f"\t\t\t\t}}\n"
    )


def main():
    root = Path(sys.argv[1])
    spec = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    page = spec["page"]
    settings = root / "content/baseoq4/pak0/guis/menu/settings"
    gui_path = settings / f"{page}.gui"
    hovers_path = settings / f"{page}_hovers.gui"
    lang_paths = sorted((root / "content/baseoq4/pak0/strings").glob("*_openq4.lang"))
    panel = f"set_{page}_help"
    text_window = f"set_{page}_help_text"
    for text in [spec["default"], *spec["rows"].values()]:
        assert '"' not in text and "\\" not in text, text

    english = read(root / "content/baseoq4/pak0/strings/english_openq4.lang")
    known = dict(re.findall(r'"(#str_\d+)"\s+"([^"]*)"', english))
    used = {int(k[5:]) for k in known}
    next_id = max([spec["first_id"] - 1] + [i for i in used if i >= spec["first_id"]]) + 1
    new_strings = []

    def string_id(text):
        nonlocal next_id
        for k, v in known.items():
            if v == text and int(k[5:]) >= spec["first_id"]:
                return k
        key = f"#str_{next_id}"
        next_id += 1
        known[key] = text
        new_strings.append((key, text))
        return key

    default_id = string_id(spec["default"])
    set_line = 'set "' + text_window + '::text" "{}" ;'

    # --- the panel, a sibling of the list below its view
    gui = read(gui_path)
    if f"windowDef {panel}\n" not in gui:
        anchor = f"\t\t\t\tsliderDef set_{page}_scroll_thumb\n"
        assert gui.count(anchor) == 1, anchor
        gui = gui.replace(anchor, panel_block(panel, text_window, default_id) + anchor, 1)
        write(gui_path, gui)

    # --- each row's hover sets and restores the text
    hovers = read(hovers_path)
    todo = []
    missing = []
    for m in re.finditer(r"windowDef\s+(\w+)_hover\s*\{", hovers):
        row = m.group(1)
        end = block_end(hovers, m.end() - 1)
        if text_window + "::text" in hovers[m.start():end]:
            continue
        if row not in spec["rows"]:
            missing.append(row)
            continue
        todo.append((m.start(), end, row, string_id(spec["rows"][row])))
    if missing:
        raise SystemExit(f"no help text for: {', '.join(missing)}")
    for start, end, row, key in reversed(todo):
        block = insert_in_handler(hovers[start:end], "onMouseEnter", set_line.format(key))
        block = insert_in_handler(block, "onMouseExit", set_line.format(default_id))
        hovers = hovers[:start] + block + hovers[end:]
    added = [row for _, _, row, _ in todo]
    write(hovers_path, hovers)

    # --- strings, English text in every openQ4 table (ids in the order rows appear)
    new_strings.sort(key=lambda kv: int(kv[0][5:]))
    for path in lang_paths:
        s = read(path).rstrip()
        assert s.endswith("}")
        present = set(re.findall(r'"(#str_\d+)"', s))
        s = s[:-1] + "".join(f'\t"{k}"\t"{v}"\n' for k, v in new_strings if k not in present) + "}\n"
        write(path, s)

    print(f"help panel {panel}; {len(added)} row(s) wired; {len(new_strings)} new string(s)"
          + (f" {new_strings[0][0]}..{new_strings[-1][0]}" if new_strings else ""))


if __name__ == "__main__":
    main()
