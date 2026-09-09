#!/usr/bin/env python3
"""raw/ の生データを最新化する。

- FRED: fredgraph.csv?id=<ID> をダウンロード（APIキー不要）
- Yahoo: COMEX 金/銀先物の月次終値を chart API から取得

取得に失敗したソースは既存ファイルを残してスキップする（部分更新で止めない）。
FRED/IMF の相場は月次なので日次で走らせても新しい月が出た時だけ動く。
python3 fetch.py && python3 build.py で data.json を更新。
"""
import json, os, sys, urllib.request, datetime

D = os.path.dirname(os.path.abspath(__file__))
FRED = os.path.join(D, "raw", "fred")
YAHOO = os.path.join(D, "raw")

FRED_IDS = [
    "PCOPPUSDM", "PALUMUSDM", "PNICKUSDM", "PTINUSDM", "PZINCUSDM", "PLEADUSDM",
    "PIORECRUSDM", "WPU1017", "POILWTIUSDM", "MHHNGSP", "WPU066", "PCU325211325211",
    "PCU334412334412", "WPU1178", "PCU334413334413", "WPU10",
    "DTCDISA066MSFRBNY", "DTFDISA066MSFRBNY", "NOCDISA066MSFRBNY", "DGORDER",
]
YAHOO_SYMS = {"GC": "GC%3DF", "SI": "SI%3DF"}

UA = {"User-Agent": "Mozilla/5.0 (buzai-signal fetch)"}
ok, fail = [], []


def get(url, timeout=40):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


for fid in FRED_IDS:
    try:
        body = get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=" + fid)
        text = body.decode("utf-8", "replace")
        if not text.lower().startswith("observation_date"):
            raise RuntimeError("unexpected body")
        if text.count("\n") < 10:
            raise RuntimeError("too short")
        with open(os.path.join(FRED, fid + ".csv"), "w") as f:
            f.write(text)
        ok.append(fid)
    except Exception as e:  # noqa: BLE001
        fail.append("%s (%s)" % (fid, e))

for name, sym in YAHOO_SYMS.items():
    try:
        body = get("https://query1.finance.yahoo.com/v8/finance/chart/%s?range=10y&interval=1mo" % sym)
        d = json.loads(body)
        res = d["chart"]["result"][0]
        assert res["timestamp"] and res["indicators"]["quote"][0]["close"]
        with open(os.path.join(YAHOO, "yahoo_%s.json" % name), "wb") as f:
            f.write(body)
        ok.append("yahoo_" + name)
    except Exception as e:  # noqa: BLE001
        fail.append("yahoo_%s (%s)" % (name, e))

print("fetch %s : ok=%d fail=%d" % (datetime.datetime.now().isoformat(timespec="minutes"), len(ok), len(fail)))
if fail:
    print("  skipped (kept existing): " + "; ".join(fail))
# 失敗があっても既存データで build できるので exit 0
sys.exit(0)
