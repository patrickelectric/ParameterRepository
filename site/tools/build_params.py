"""Flatten every <Vehicle>-<version>/apm.pdef.json into site/static/data/ for the search page."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "site/static/data"
KEYS = (("Units", "u"), ("Values", "v"), ("Bitmask", "b"))


def flatten(pdef):
    rows = []
    for group, params in pdef.items():
        if group == "json":  # format-version marker, not a group
            continue
        for name, p in params.items():
            row = {"n": name, "t": p.get("DisplayName", ""), "d": p.get("Description", "")}
            if "Range" in p:
                row["r"] = [p["Range"]["low"], p["Range"]["high"]]
            row.update({dst: p[src] for src, dst in KEYS if src in p})
            rows.append(row)
    return sorted(rows, key=lambda r: r["n"])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    index = {}
    for f in sorted(ROOT.glob("*-*/apm.pdef.json")):
        vehicle, version = f.parent.name.rsplit("-", 1)
        rows = flatten(json.loads(f.read_text()))
        (OUT / f"{vehicle}-{version}.json").write_text(json.dumps(rows, separators=(",", ":")))
        index.setdefault(vehicle, []).append(version)
    for versions in index.values():
        versions.sort(key=lambda v: [int(x) for x in v.split(".")], reverse=True)
    (OUT / "index.json").write_text(json.dumps(index))
    print(f"wrote {sum(map(len, index.values()))} files for {len(index)} vehicles")


if __name__ == "__main__":
    main()
