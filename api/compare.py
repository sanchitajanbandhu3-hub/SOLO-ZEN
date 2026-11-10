"""Compares a current bill with previous bills: finds duplicate charges, price jumps and new charges.
Plain Python, no AI, so the numbers are always exact."""
from http.server import BaseHTTPRequestHandler
from collections import Counter
import difflib
import json
import re

LINE = re.compile(r"^\s*(.+?)\s*(?:[:\-\t]|\s{2,})\s*(?:rs\.?|inr|\u20b9)?\s*([\d,]+(?:\.\d+)?)\s*$", re.I)
TOTAL_WORDS = ("total", "payable", "amount due", "net amount")
SKIP = ("subtotal", "sub total", "previous", "paid", "received", "balance", "units", "reading", "advance")
JUMP_PCT = 15.0


def norm(name):
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", name.lower()).split())


def parse(text):
    items, total = {}, None
    for raw in text.splitlines():
        m = LINE.match(raw)
        if not m:
            continue
        name, amount = m.group(1).strip(), float(m.group(2).replace(",", ""))
        low = name.lower()
        if any(k in low for k in SKIP):
            continue
        if any(k in low for k in TOTAL_WORDS):
            total = amount
            continue
        item = items.setdefault(norm(name), {"name": name, "amts": []})
        item["amts"].append(amount)
    return items, total


def find_match(key, prev_items):
    if key in prev_items:
        return prev_items[key]
    close = difflib.get_close_matches(key, list(prev_items), n=1, cutoff=0.85)
    return prev_items[close[0]] if close else None


def money(x):
    return f"{x:,.2f}"


def compare(current_text, previous_texts):
    cur, cur_total = parse(current_text)
    prevs = [parse(t) for t in previous_texts]
    findings, unchanged = [], 0

    for key, item in cur.items():
        name, amts = item["name"], item["amts"]
        for amt, n in Counter(amts).items():
            if n > 1:
                findings.append({"type": "duplicate", "severity": "high", "name": name,
                                 "message": f"{name} appears {n} times at {money(amt)} each ({money(amt * n)} in total). Ask for the extra {n - 1} to be removed."})
        unit = max(amts)
        before = [m["amts"] for m in (find_match(key, p[0]) for p in prevs) if m]
        before_units = [max(a) for a in before]
        if not before_units:
            findings.append({"type": "new_charge", "severity": "medium", "name": name,
                             "message": f"{name} ({money(unit)}) was not on your previous bill{'s' if len(prevs) > 1 else ''}. Ask what it is for."})
            continue
        avg = sum(before_units) / len(before_units)
        pct = (unit - avg) / avg * 100 if avg > 0 else 0
        basis = "your previous bill" if len(before_units) == 1 else f"the average of {len(before_units)} previous bills"
        if pct >= JUMP_PCT and unit - avg >= 1:
            findings.append({"type": "price_jump", "severity": "high" if pct >= 50 else "medium", "name": name,
                             "message": f"{name} is {money(unit)}, up {pct:.0f}% from {money(avg)} on {basis}. Check whether your usage went up, or ask what changed."})
        elif pct <= -JUMP_PCT and avg - unit >= 1:
            findings.append({"type": "decrease", "severity": "low", "name": name,
                             "message": f"{name} went down {abs(pct):.0f}% ({money(unit)} from {money(avg)} on {basis})."})
        else:
            unchanged += 1

    if prevs:
        for key, item in prevs[0][0].items():
            if not find_match(key, cur):
                findings.append({"type": "dropped", "severity": "low", "name": item["name"],
                                 "message": f"{item['name']} ({money(max(item['amts']))}) was on your last bill but is not on this one."})

    order = {"high": 0, "medium": 1, "low": 2}
    findings.sort(key=lambda f: order[f["severity"]])
    to_total = cur_total if cur_total is not None else round(sum(sum(i["amts"]) for i in cur.values()), 2)
    last = prevs[0] if prevs else ({}, None)
    from_total = last[1] if last[1] is not None else round(sum(sum(i["amts"]) for i in last[0].values()), 2)
    change = round((to_total - from_total) / from_total * 100, 1) if from_total else None
    return {"charges_found": len(cur), "previous_bills": len(prevs), "total_from": from_total, "total_to": to_total,
            "total_change_pct": change, "unchanged": unchanged, "findings": findings}


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            size = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(size) or b"{}")
            cur = str(body.get("current", ""))[:6000]
            prev = [str(p)[:6000] for p in (body.get("previous") or [])[:3] if str(p).strip()]
            if len(cur.strip()) < 20 or not prev:
                raise ValueError("need current and previous")
            out, code = compare(cur, prev), 200
        except Exception:
            out, code = {"error": "Paste your current bill and at least one previous bill."}, 400
        data = json.dumps(out).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
