"""Insert rows into openQ4's Settings > Game Options page (classic settings GUI).

Rows are laid out by absolute position, so this also moves every row and hover
below the insertion point, grows the scrolling content, and keeps the section jump
list, the engine's scroll table (Session_menu.cpp), the settings registry and the
settings_menu_coverage.py expectations in step.  Line endings are preserved.

    python -P tools/openq4_settings_rows.py <openQ4 root> <spec.json>

spec.json:
{
  "after": "set_game_scopesensitivity",          # existing row window to insert below
  "section": "Gameplay And View",               # registry section name of that row
  "rows": [
    {"window": "set_game_fov", "id": "game.view.fov", "label_id": "#str_231306", "label": "Field of View",
     "kind": "slider", "cvar": "g_fov", "low": "70", "high": "130", "step": "1", "maxchars": 3,
     "default": "90", "cvar_low": "1", "cvar_high": "179", "range_intent": "..."},
    {"window": "...", "kind": "choice", "choices_id": "#str_...", "choices": "A;B;C",  # new choices string
     "values": "0;1;2", "default": "0", ...}
  ]
}
"""
import json
import re
import sys
from pathlib import Path

ROW = 24
CONTENT_TOP = 47        # y of the first row; scroll steps are rows of 24 from here
CRLF = {}


def read(path):
    raw = path.read_bytes().decode("utf-8", errors="surrogateescape")
    CRLF[path] = "\r\n" in raw
    return raw.replace("\r\n", "\n")


def write(path, text):
    if CRLF.get(path):
        text = text.replace("\n", "\r\n")
    path.write_bytes(text.encode("utf-8", errors="surrogateescape"))


def content_children(lines, container="set_game_content"):
    """(line index of the first rect, y, window name) for each direct child of container."""
    out = []
    depth = 0
    container_depth = None
    entered = False
    pending = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if container_depth is None and re.match(rf"windowDef\s+{container}\b", stripped):
            container_depth = depth
        elif entered and depth == container_depth + 1:
            m = re.match(r"(windowDef|choiceDef|sliderDef|editDef|bindDef|listDef)\s+(\w+)", stripped)
            if m:
                pending = m.group(2)
        if pending and depth == container_depth + 2 and stripped.startswith("rect"):
            m = re.match(r"\s*rect\s+(-?\d+),(-?\d+),", line)
            if m:
                out.append((i, int(m.group(2)), pending))
            pending = None
        depth += line.count("{") - line.count("}")
        if container_depth is not None:
            if depth > container_depth:
                entered = True
            elif entered:
                break
    return out


def set_rect_y(line, y):
    return re.sub(r"(rect\s+-?\d+,)(-?\d+)(,)", lambda m: f"{m.group(1)}{y}{m.group(3)}", line, count=1)


def row_block(row, y):
    w = row["window"]
    head = (
        f"\t//==============================================================//\n"
        f"\t// Settings->Game Options->{row['label']}\n"
        f"\t//==============================================================//\n\n"
        f"\t\t\t\twindowDef {w}\n\t\t\t\t{{\n"
        f"\t\t\t\t\trect\t228,{y},377,25\n\t\t\t\t\tvisible\t1\n\n"
        f"\t\t\t\t\twindowDef {w}_background\n\t\t\t\t\t{{\n"
        f"\t\t\t\t\t\trect\t0,0,377,25\n\t\t\t\t\t\tvisible\t1\n"
        f"\t\t\t\t\t\tbackground\t\"gfx/guis/mainmenu/b3_light\"\n"
        f"\t\t\t\t\t\tmatcolor\t0.545,0.588,0.294,0.4\n\t\t\t\t\t}}\n"
        f"\t\t\t\t\twindowDef {w}_description\n\t\t\t\t\t{{\n"
        f"\t\t\t\t\t\trect\t31,3,210,18\n\t\t\t\t\t\tvisible\t1\n"
        f"\t\t\t\t\t\tforecolor\t1,1,1,0.8\n\t\t\t\t\t\ttext\t\"{row['label_id']}\"\n"
        f"\t\t\t\t\t\ttextscale\t0.24\n\t\t\t\t\t\tfont\t\"fonts/lowpixel\"\n\t\t\t\t\t}}\n"
    )
    if row["kind"] == "choice":
        values = f"\t\t\t\t\t\tvalues\t\"{row['values']}\"\n\t\t\t\t\t\tchoiceType\t1\n" if "values" in row else "\t\t\t\t\t\tchoiceType\t0\n"
        body = (
            f"\t\t\t\t\tchoiceDef {w}_value\n\t\t\t\t\t{{\n"
            f"\t\t\t\t\t\trect\t240,3,162,18\n\t\t\t\t\t\tvisible\t1\n"
            f"\t\t\t\t\t\tforecolor\t1,0.745,0.137,0.8\n\t\t\t\t\t\tcvar\t{row['cvar']}\n"
            f"\t\t\t\t\t\ttextscale\t0.24\n\t\t\t\t\t\tfont\t\"fonts/lowpixel\"\n"
            f"\t\t\t\t\t\tchoices\t\"{row['choices_id']}\"\n{values}\n"
            f"\t\t\t\t\t\tonAction {{\n\t\t\t\t\t\t\tset \"cmd\" \"play main_menu_selection\" ;\n\t\t\t\t\t\t}}\n"
            f"\t\t\t\t\t}}\n"
        )
    else:
        body = (
            f"\t\t\t\t\twindowDef {w}_slider_bg\n\t\t\t\t\t{{\n"
            f"\t\t\t\t\t\trect\t244,8,128,16\n\t\t\t\t\t\tbackground\t\"gfx/guis/mainmenu/slider_bg\"\n"
            f"\t\t\t\t\t\tmatcolor\t1,0.745,0.137,0.8\n\t\t\t\t\t\tnoevents\t1\n\t\t\t\t\t\tvisible\t1\n\t\t\t\t\t}}\n"
            f"\t\t\t\t\tsliderDef {w}_slider_bar\n\t\t\t\t\t{{\n"
            f"\t\t\t\t\t\trect\t244,9,71,8\n\t\t\t\t\t\tforecolor\t1,0.745,0.137,0.8\n"
            f"\t\t\t\t\t\tmatcolor\t1,0.745,0.137,0.8\n\t\t\t\t\t\tlow\t{row['low']}\n"
            f"\t\t\t\t\t\thigh\t{row['high']}\n\t\t\t\t\t\tstep\t{row['step']}\n"
            f"\t\t\t\t\t\tthumbShader\t\"gfx/guis/mainmenu/slider_bar\"\n"
            f"\t\t\t\t\t\tcvar\t{row['cvar']}\n\t\t\t\t\t\tvisible\t1\n\t\t\t\t\t}}\n"
            f"\t\t\t\t\teditDef {w}_value\n\t\t\t\t\t{{\n"
            f"\t\t\t\t\t\trect\t322,4,100,18\n\t\t\t\t\t\tvisible\t1\n\t\t\t\t\t\tcvar\t{row['cvar']}\n"
            f"\t\t\t\t\t\ttextscale\t0.24\n\t\t\t\t\t\tmaxchars\t{row['maxchars']}\n\t\t\t\t\t\tnumeric\t1\n"
            f"\t\t\t\t\t\tforecolor\t1,0.745,0.137,0.8\n\t\t\t\t\t\tfont\t\"fonts/lowpixel\"\n\n"
            f"\t\t\t\t\t\tonEnter {{\n\t\t\t\t\t\t\tsetfocus \"set_b_back\" ;\n\t\t\t\t\t\t}}\n\n"
            f"\t\t\t\t\t\tonAction {{\n\t\t\t\t\t\t\tset \"cmd\" \"play main_menu_selection\" ;\n\t\t\t\t\t\t}}\n"
            f"\t\t\t\t\t}}\n"
        )
    return head + body + "\t\t\t\t}\n\t//==============================================================//\n\n"


def hover_block(row, y):
    w = row["window"]
    return (
        f"\t\twindowDef {w}_hover\n\t\t{{\n\t\t\trect\t245,{y},361,20\n\t\t\tvisible\t0\n\n"
        f"\t\t\tonMouseEnter {{\n\t\t\t\tif (\"desktop::active\" == 0) {{\n"
        f"\t\t\t\t\tstoptransitions \"{w}_background\" ;\n"
        f"\t\t\t\t\tset \"{w}_background::matcolor_w\" \"1\" ;\n"
        f"\t\t\t\t\tset \"cmd\" \"play main_menu_mouseover\" ;\n\t\t\t\t}}\n\t\t\t}}\n\n"
        f"\t\t\tonMouseExit {{\n\t\t\t\tif (\"desktop::active\" == 0) {{\n"
        f"\t\t\t\t\ttransition \"{w}_background::matcolor_w\" \"1\" \"0.4\" \"300\" ;\n\t\t\t\t}}\n\t\t\t}}\n\t\t}}\n"
    )


def registry_entry(row, section):
    w = row["window"]
    entry = {"id": row["id"], "pane": "Game Options", "section": section,
             "path": f"Settings > Game Options > {section} > {row['label']}", "source": "game", "container": w}
    if row["kind"] == "choice":
        entry.update({"widgets": [f"{w}_value"], "widget_type": "choice", "label_key": row["label_id"],
                      "choices_key": row["choices_id"], "target_type": "cvar", "target": row["cvar"],
                      "default": row["default"], "restart_required": False,
                      "accessibility": "Standard focusable choiceDef row."})
        if "values" in row:
            entry["values"] = row["values"].split(";")
    else:
        entry.update({"widgets": [f"{w}_slider_bar", f"{w}_value"],
                      "edit_fields": [{"name": f"{w}_value", "maxchars": row["maxchars"], "numeric": True}],
                      "widget_type": "slider_edit", "label_key": row["label_id"], "target_type": "cvar",
                      "target": row["cvar"], "default": row["default"],
                      "ui_range": {"low": row["low"], "high": row["high"], "step": row["step"]},
                      "cvar_range": {"low": row["cvar_low"], "high": row["cvar_high"]},
                      "restart_required": False, "accessibility": "Slider with paired edit field."})
    if "range_intent" in row:
        entry["range_intent"] = row["range_intent"]
    return entry


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    root = Path(sys.argv[1])
    spec = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    rows = spec["rows"]
    n = len(rows)
    shift = ROW * n

    game_path = root / "content/baseoq4/pak0/guis/menu/settings/game.gui"
    hover_path = root / "content/baseoq4/pak0/guis/menu/settings/game_hovers.gui"
    session_path = root / "src/framework/Session_menu.cpp"
    registry_path = root / "docs/dev/settings-menu-registry.json"
    test_path = root / "tools/tests/settings_menu_coverage.py"

    # --- game.gui
    game = read(game_path)
    lines = game.split("\n")
    children = content_children(lines)
    anchor = next(c for c in children if c[2] == spec["after"])
    insert_y = anchor[1] + ROW
    for index, y, _ in children:
        if y >= insert_y:
            lines[index] = set_rect_y(lines[index], y + shift)
    game = "\n".join(lines)

    old_height = int(re.search(r"rect\t-24,-41,640,(\d+)", game).group(1))
    game = game.replace(f"rect\t-24,-41,640,{old_height}", f"rect\t-24,-41,640,{old_height + shift}", 1)
    old_max = int(re.search(r"high\t(\d+)\n(?:[^\n]*\n){0,6}?\t*cvar\tgui_set_game_scroll", game).group(1))
    game = re.sub(r"high\t\d+(\n(?:[^\n]*\n){0,6}?\t*cvar\tgui_set_game_scroll)", rf"high\t{old_max + n}\1", game, count=1)

    jumps = [int(v) for v in re.findall(r'set "gui::gui_set_game_scroll" "(\d+)" ;', game)]
    anchor_row = (anchor[1] - CONTENT_TOP) // ROW
    section_index = max(k for k, start in enumerate(jumps) if start <= anchor_row)
    moved = [v for k, v in enumerate(jumps) if k > section_index]
    for v in sorted(moved, reverse=True):
        game = game.replace(f'set "gui::gui_set_game_scroll" "{v}" ;', f'set "gui::gui_set_game_scroll" "{v + n}" ;', 1)

    # insert after the anchor's block: just before the next row's header comment
    anchor_line = anchor[0]
    marker = game.split("\n")
    insert_at = None
    for i in range(anchor_line, len(marker)):
        if marker[i].startswith("\t//==") and i + 1 < len(marker) and marker[i + 1].startswith("\t// Settings->"):
            insert_at = i
            break
        if re.match(r"\t\t\t\twindowDef \w+", marker[i]) and i > anchor_line + 2:
            insert_at = i
            break
    assert insert_at is not None, "no insertion point after the anchor row"
    blocks = "".join(row_block(r, insert_y + ROW * k) for k, r in enumerate(rows))
    marker[insert_at:insert_at] = blocks.rstrip("\n").split("\n") + [""]
    write(game_path, "\n".join(marker))

    # --- hovers: top-level windows in the include, positioned at row y + 2
    hovers = read(hover_path)
    hl = hovers.split("\n")
    anchor_hover = None
    for i, line in enumerate(hl):
        if re.match(r"\s*windowDef\s+(\w+)_hover\s*$", line):
            name = re.match(r"\s*windowDef\s+(\w+)_hover", line).group(1)
            for j in range(i + 1, min(i + 4, len(hl))):
                m = re.match(r"(\s*rect\s+\d+,)(\d+)(,.*)$", hl[j])
                if m:
                    y = int(m.group(2))
                    if y >= insert_y + 2:
                        hl[j] = f"{m.group(1)}{y + shift}{m.group(3)}"
                    if name == spec["after"]:
                        anchor_hover = i
                    break
    assert anchor_hover is not None, "anchor row has no hover"
    end = anchor_hover + 1
    depth = 0
    while True:
        depth += hl[end].count("{") - hl[end].count("}")
        end += 1
        if depth == 0 and "}" in hl[end - 1]:
            break
    new_hovers = "".join(hover_block(r, insert_y + 2 + ROW * k) for k, r in enumerate(rows)).rstrip("\n").split("\n")
    hl[end:end] = new_hovers
    write(hover_path, "\n".join(hl))

    # --- Session_menu.cpp: scroll cvar range, page table, section thresholds
    src = read(session_path)
    src = src.replace(f'"game menu scroll step", 0, {old_max} )', f'"game menu scroll step", 0, {old_max + n} )', 1)
    page = re.search(r'"game_section_choice",\n\t\t(\d+),\n\t\t0,\n\t\t(\d+),\n\t\t-24,\n\t\t-41,\n\t\t(\d+),', src)
    assert page and int(page.group(2)) == old_max and int(page.group(3)) == old_height
    src = src[:page.start()] + page.group(0).replace(f"\n\t\t{old_max},", f"\n\t\t{old_max + n},").replace(f"\n\t\t{old_height},", f"\n\t\t{old_height + shift},") + src[page.end():]
    start = src.index('if ( idStr::Icmp( page.name, "game" ) == 0 ) {')
    stop = src.index('if ( idStr::Icmp( page.name, "system" ) == 0 ) {', start)
    block = src[start:stop]
    for v in sorted(moved, reverse=True):
        block = block.replace(f"scrollValue < {v} )", f"scrollValue < {v + n} )", 1)
    src = src[:start] + block + src[stop:]
    write(session_path, src)

    # --- strings, English text in every openQ4 table
    texts = []
    for r in rows:
        texts.append((r["label_id"], r["label"]))
        if r["kind"] == "choice" and "choices" in r:
            texts.append((r["choices_id"], r["choices"]))
    for path in sorted((root / "content/baseoq4/pak0/strings").glob("*_openq4.lang")):
        s = read(path).rstrip()
        assert s.endswith("}")
        s = s[:-1] + "".join(f'\t"{k}"\t"{v}"\n' for k, v in texts) + "}\n"
        write(path, s)

    # --- registry
    raw = registry_path.read_bytes().decode("utf-8")
    registry = json.loads(raw)
    settings = registry["settings"]
    at = next(i for i, s in enumerate(settings) if s.get("container") == spec["after"]) + 1
    settings[at:at] = [registry_entry(r, spec["section"]) for r in rows]
    out = json.dumps(registry, indent=2, ensure_ascii=False) + "\n"
    registry_path.write_bytes((out.replace("\n", "\r\n") if "\r\n" in raw else out).encode("utf-8"))

    # --- coverage test expectations
    test = read(test_path)
    test = test.replace(f'"rect\\t-24,-41,640,{old_height}",', f'"rect\\t-24,-41,640,{old_height + shift}",', 1)
    test = test.replace(f'"640,{old_height}",', f'"640,{old_height + shift}",', 1)
    test = test.replace(f'"high\\t{old_max}",', f'"high\\t{old_max + n}",', 1)
    test = test.replace(f'"game menu scroll step", 0, {old_max} )', f'"game menu scroll step", 0, {old_max + n} )', 1)
    for v in sorted(moved, reverse=True):
        test = test.replace(f"'set \"gui::gui_set_game_scroll\" \"{v}\"',", f"'set \"gui::gui_set_game_scroll\" \"{v + n}\"',", 1)
    anchor_numeric = '            "set_game_controller_look_sensitivity_value",\n'
    sliders = "".join(f'            "{r["window"]}_value",\n' for r in rows if r["kind"] == "slider")
    if sliders:
        test = test.replace(anchor_numeric, anchor_numeric + sliders, 1)
    write(test_path, test)

    print(f"inserted {n} row(s) after {spec['after']} at y={insert_y}; section {section_index}; "
          f"height {old_height}->{old_height + shift}; scroll max {old_max}->{old_max + n}; moved jumps {moved}")


if __name__ == "__main__":
    main()
