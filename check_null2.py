import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

URL = "https://null2.nexus/api/v1/products/stocks?date=2026-10-31"
TIMES = ["14:30:00", "14:50:00", "15:10:00", "15:30:00"]

request = Request(
    URL,
    headers={
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json,text/plain,*/*",
        "Referer": "https://null2.nexus/order",
    },
)

with urlopen(request, timeout=30) as response:
    data = json.load(response)

if isinstance(data, dict):
    slots = data.get("stocks", data.get("data", []))
else:
    slots = data

by_time = {
    str(slot.get("start_time")): slot
    for slot in slots
    if isinstance(slot, dict)
}

results = []

for target_time in TIMES:
    slot = by_time.get(target_time, {})

    try:
        available = int(slot.get("available"))
    except (TypeError, ValueError):
        available = None

    results.append({
        "time": target_time[:5],
        "available": available,
        "status": slot.get("status", "not_found"),
        "two_seats_available":
            available is not None and available >= 2,
    })

jst = timezone(timedelta(hours=9))
checked_at = datetime.now(jst).isoformat(timespec="seconds")

output = {
    "event_date": "2026-10-31",
    "party_size": 2,
    "checked_at_jst": checked_at,
    "any_two_seats_available":
        any(x["two_seats_available"] for x in results),
    "slots": results,
}

Path("docs").mkdir(exist_ok=True)

Path("docs/status.json").write_text(
    json.dumps(output, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

rows = "".join(
    f"""
    <tr>
      <td>{x["time"]}</td>
      <td>{"—" if x["available"] is None else x["available"]}</td>
      <td>{x["status"]}</td>
      <td>{"空きあり" if x["two_seats_available"] else "2名分なし"}</td>
    </tr>
    """
    for x in results
)

message = (
    "希望時間に2名分の空きあり"
    if output["any_two_seats_available"]
    else "現在、希望時間に2名分の空きなし"
)

html = f"""
<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NULL² 空席監視</title>
</head>

<body>
<h1>NULL² 10/31 空席監視</h1>

<p>最終確認：{checked_at}（JST）</p>
<p>2名 / 14:30・14:50・15:10・15:30</p>

<table border="1" cellpadding="8">
<tr>
<th>時間</th>
<th>available</th>
<th>status</th>
<th>判定</th>
</tr>

{rows}

</table>

<p><strong>{message}</strong></p>

</body>
</html>
"""

Path("docs/index.html").write_text(
    html,
    encoding="utf-8",
)

print(json.dumps(output, ensure_ascii=False, indent=2))
