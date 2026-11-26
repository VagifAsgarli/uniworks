"""Lists every feedback loop of a CLD description (the JSON read by ../../tools/cld_draw.py) and its type.

A loop with an even number of "-" links is reinforced (R); with an odd number it is balanced (B).

    python check_cld.py cyberflow_cld.json
"""
import json
import sys


def loops(spec):
    out = {}
    for link in spec["links"]:
        out.setdefault(link[0], []).append((link[1], link[2]))
    found = {}

    def walk(start, node, path, signs):
        for nxt, sign in out.get(node, []):
            if nxt == start:
                cyc = path[:]
                k = cyc.index(min(cyc))                      # the same loop is found from each of its nodes
                key = tuple(cyc[k:] + cyc[:k])
                found[key] = (signs + [sign])[k:] + (signs + [sign])[:k]
            elif nxt not in path:
                walk(start, nxt, path + [nxt], signs + [sign])

    for n in spec["nodes"]:
        walk(n, n, [n], [])
    return found


def main():
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    name = {k: v[2].lstrip("~").replace("\n", " ") for k, v in spec["nodes"].items()}
    result = loops(spec)
    for cyc, signs in sorted(result.items(), key=lambda kv: len(kv[0])):
        minus = signs.count("-")
        kind = "balanced (B)" if minus % 2 else "reinforced (R)"
        chain = "".join(f"{name[n]} --({s})--> " for n, s in zip(cyc, signs)) + name[cyc[0]]
        print(f"{kind:15s} {minus} minus link(s): {chain}")
    print(f"{len(result)} loops; {len(spec.get('loops', []))} markers drawn: "
          + ", ".join(m[0] for m in spec.get("loops", [])))


if __name__ == "__main__":
    main()
