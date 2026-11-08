"""Exact math checks on a bill. No AI here: plain Python, so the numbers are always right."""
from http.server import BaseHTTPRequestHandler
import json
import re

LINE = re.compile(r"^\s*(.+?)\s*[:\-]\s*(?:rs\.?|inr|\u20b9)?\s*([\d,]+(?:\.\d+)?)\s*$", re.I)
SKIP = ("total", "payable", "amount due", "previous", "paid", "received", "balance", "units", "reading")
LATE = ("late", "penalty", "surcharge", "delay")
VAGUE = ("misc", "other", "sundry")


def money(x):
    return float(x.replace(",", ""))


def check_bill(text):
    charges, total = [], None
    for raw in text.splitlines():
        m = LINE.match(raw)
        if not m:
            continue
        name, amount = m.group(1).strip(), money(m.group(2))
        low = name.lower()
        if "total" in low or "payable" in low or "amount due" in low:
            total = amount
        elif not any(k in low for k in SKIP):
            charges.append((name, amount))

    seen, dups = {}, []
    for name, amount in charges:
        seen[(name.lower(), amount)] = seen.get((name.lower(), amount), 0) + 1
    for (name, amount), n in seen.items():
        if n > 1:
            dups.append({"name": name.title(), "amount": amount, "times": n})

    added = round(sum(a for _, a in charges), 2)
    result = {
        "charges_found": len(charges),
        "sum_of_charges": added,
        "total_on_bill": total,
        "total_matches": None if total is None or not charges else abs(added - total) < 1,
        "difference": None if total is None else round(total - added, 2),
        "duplicates": dups,
        "late_fee_lines": [n for n, _ in charges if any(k in n.lower() for k in LATE)],
        "vague_lines": [n for n, _ in charges if any(k in n.lower() for k in VAGUE)],
    }
    return result


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            size = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(size) or b"{}")
            out, code = check_bill(str(body.get("bill", ""))[:6000]), 200
        except Exception:
            out, code = {"error": "bad request"}, 400
        data = json.dumps(out).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
