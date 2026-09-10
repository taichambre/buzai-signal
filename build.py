#!/usr/bin/env python3
"""raw/ の生データ (FRED CSV / Yahoo JSON) から data.json を組み立てる。

依存なし。python3 build.py で data.json を上書きする。
数値系列は月次。個別素材の追加は MAT に1行足すだけ。
"""
import json, csv, os, datetime

D = os.path.dirname(os.path.abspath(__file__))
FRED = os.path.join(D, "raw", "fred")
YAHOO = os.path.join(D, "raw")
START = "2018-01"


def load_fred(fid, scale=1.0):
    path = os.path.join(FRED, fid + ".csv")
    with open(path) as f:
        head = f.readline().strip()
        if not head.lower().startswith("observation_date"):
            raise RuntimeError("bad FRED file %s: %s" % (fid, head[:40]))
        out = []
        for row in csv.reader(f):
            if len(row) < 2:
                continue
            d, v = row[0][:7], row[1]
            if d < START or v in ("", ".", "NaN"):
                continue
            out.append({"date": d, "value": round(float(v) * scale, 3)})
    if not out:
        raise RuntimeError("empty FRED series %s" % fid)
    return out


def load_yahoo(name):
    d = json.load(open(os.path.join(YAHOO, "yahoo_%s.json" % name)))
    r = d["chart"]["result"][0]
    ts, cl = r["timestamp"], r["indicators"]["quote"][0]["close"]
    seen = {}
    for t, v in zip(ts, cl):
        if v is None:
            continue
        m = datetime.date.fromtimestamp(t).strftime("%Y-%m")
        if m >= START:
            seen[m] = round(v, 2)
    return [{"date": k, "value": seen[k]} for k in sorted(seen)]


# key: (label, group, unit, fred_id | ("yahoo", name), source, url, provisional)
MAT = {
  "copper":   ("銅", "ベースメタル", "USD/トン", "PCOPPUSDM", "FRED / IMF Primary Commodity Prices", "https://fred.stlouisfed.org/series/PCOPPUSDM", False),
  "aluminum": ("アルミ", "ベースメタル", "USD/トン", "PALUMUSDM", "FRED / IMF Primary Commodity Prices", "https://fred.stlouisfed.org/series/PALUMUSDM", False),
  "nickel":   ("ニッケル", "ベースメタル", "USD/トン", "PNICKUSDM", "FRED / IMF Primary Commodity Prices", "https://fred.stlouisfed.org/series/PNICKUSDM", False),
  "tin":      ("すず（はんだ）", "ベースメタル", "USD/トン", "PTINUSDM", "FRED / IMF Primary Commodity Prices", "https://fred.stlouisfed.org/series/PTINUSDM", False),
  "zinc":     ("亜鉛（メッキ）", "ベースメタル", "USD/トン", "PZINCUSDM", "FRED / IMF Primary Commodity Prices", "https://fred.stlouisfed.org/series/PZINCUSDM", False),
  "lead":     ("鉛", "ベースメタル", "USD/トン", "PLEADUSDM", "FRED / IMF Primary Commodity Prices", "https://fred.stlouisfed.org/series/PLEADUSDM", False),
  "gold":     ("金", "貴金属", "USD/oz", ("yahoo", "GC"), "Yahoo Finance（COMEX金先物 GC=F・月末値）", "https://finance.yahoo.com/quote/GC=F", False),
  "silver":   ("銀", "貴金属", "USD/oz", ("yahoo", "SI"), "Yahoo Finance（COMEX銀先物 SI=F・月末値）", "https://finance.yahoo.com/quote/SI=F", False),
  "ironore":  ("鉄鉱石", "鉄鋼原料", "USD/トン", "PIORECRUSDM", "FRED / IMF Primary Commodity Prices", "https://fred.stlouisfed.org/series/PIORECRUSDM", False),
  "steel":    ("鋼材（鉄鋼製品 PPI）", "鉄鋼原料", "指数", "WPU1017", "FRED / U.S. BLS（Steel Mill Products PPI）", "https://fred.stlouisfed.org/series/WPU1017", False),
  "crude":    ("原油 WTI", "エネルギー・化学", "USD/バレル", "POILWTIUSDM", "FRED / IMF Primary Commodity Prices", "https://fred.stlouisfed.org/series/POILWTIUSDM", False),
  "natgas":   ("天然ガス（Henry Hub）", "エネルギー・化学", "USD/MMBtu", "MHHNGSP", "FRED / U.S. EIA", "https://fred.stlouisfed.org/series/MHHNGSP", False),
  "resin":    ("プラスチック樹脂（PPI）", "エネルギー・化学", "指数", "WPU066", "FRED / U.S. BLS（Plastic Resins & Materials PPI）", "https://fred.stlouisfed.org/series/WPU066", False),
  "resinmfg": ("樹脂製造（PPI）", "エネルギー・化学", "指数", "PCU325211325211", "FRED / U.S. BLS（Plastics Material & Resin Mfg PPI）", "https://fred.stlouisfed.org/series/PCU325211325211", False),
  "pcb":      ("プリント基板（ベア基板 PPI）", "電子部品・半導体", "指数", "PCU334412334412", "FRED / U.S. BLS（Bare PCB Mfg PPI）", "https://fred.stlouisfed.org/series/PCU334412334412", False),
  "eleccomp": ("電子部品（PPI）", "電子部品・半導体", "指数", "WPU1178", "FRED / U.S. BLS（Electronic Components & Accessories PPI）", "https://fred.stlouisfed.org/series/WPU1178", False),
  "semippi":  ("半導体（PPI）", "電子部品・半導体", "指数", "PCU334413334413", "FRED / U.S. BLS（Semiconductor & Related Device Mfg PPI）", "https://fred.stlouisfed.org/series/PCU334413334413", False),
  "metals":   ("金属・金属製品（PPI）", "鉄鋼原料", "指数", "WPU10", "FRED / U.S. BLS（Metals & Metal Products PPI）", "https://fred.stlouisfed.org/series/WPU10", False),
}


def interp(anchor, months):
    keys = sorted(anchor)
    out = []
    for m in months:
        if m <= keys[0]:
            out.append((m, anchor[keys[0]])); continue
        if m >= keys[-1]:
            out.append((m, anchor[keys[-1]])); continue
        prev = [k for k in keys if k <= m][-1]
        nxt = [k for k in keys if k >= m][0]
        if prev == nxt:
            out.append((m, anchor[prev])); continue
        di = (datetime.date.fromisoformat(m + "-01") - datetime.date.fromisoformat(prev + "-01")).days
        dt = (datetime.date.fromisoformat(nxt + "-01") - datetime.date.fromisoformat(prev + "-01")).days
        out.append((m, round(anchor[prev] + (anchor[nxt] - anchor[prev]) * di / dt, 2)))
    return [{"date": d, "value": v} for d, v in out]


copper_pts = load_fred("PCOPPUSDM")
MONTHS = [p["date"] for p in copper_pts]

# 暫定推計値（TrendForce 月次プレスリリースの前月比を基にした形状。実値取得までのプレースホルダ）
DRAM_A = {"2018-01":100,"2018-07":103,"2018-10":95,"2019-01":78,"2019-07":52,"2019-10":47,"2020-01":49,"2020-07":58,"2020-10":52,"2021-01":55,"2021-07":74,"2021-10":70,"2022-01":66,"2022-07":55,"2022-10":44,"2023-01":34,"2023-07":26,"2023-10":30,"2024-01":40,"2024-07":54,"2024-10":56,"2025-01":55,"2025-07":66,"2025-10":82,"2026-01":98,"2026-04":112,"2026-07":121}
NAND_A = {"2018-01":100,"2018-07":92,"2019-01":72,"2019-07":58,"2020-01":60,"2020-07":63,"2021-01":66,"2021-07":78,"2022-01":74,"2022-07":62,"2023-01":45,"2023-07":38,"2024-01":52,"2024-07":63,"2025-01":60,"2025-07":70,"2026-01":86,"2026-07":95}
WSTS_A = {"2018-01":37.6,"2018-07":39.6,"2019-01":35.5,"2019-07":33.4,"2020-01":36.0,"2020-07":35.2,"2021-01":40.0,"2021-07":45.4,"2022-01":50.7,"2022-07":49.0,"2023-01":41.3,"2023-07":43.2,"2024-01":47.6,"2024-07":51.3,"2025-01":56.5,"2025-07":62.1,"2026-01":68.0,"2026-06":73.5}
SEMIBILL_A = {"2018-01":2.36,"2018-07":2.55,"2019-01":1.94,"2019-07":1.94,"2020-01":2.37,"2020-07":2.65,"2021-01":3.04,"2021-07":3.47,"2022-01":3.35,"2022-07":3.13,"2023-01":2.50,"2023-07":2.53,"2024-01":2.84,"2024-07":2.90,"2025-01":3.44,"2025-07":3.65,"2026-01":4.05,"2026-06":4.30}

materials = {}
for k, (label, group, unit, src, source, url, prov) in MAT.items():
    pts = load_yahoo(src[1]) if isinstance(src, tuple) else load_fred(src)
    materials[k] = {"label": label, "group": group, "unit": unit, "source": source,
                    "sourceUrl": url, "provisional": prov, "points": pts}

materials["dram"] = {"label": "DRAM DDR4 契約価格（指数）", "group": "電子部品・半導体", "unit": "指数(2018年1月=100)",
    "source": "TrendForce 月次プレスリリースを基にした暫定推計値", "sourceUrl": "https://www.trendforce.com/presscenter",
    "provisional": True, "points": interp(DRAM_A, MONTHS)}
materials["nand"] = {"label": "NAND 128Gb 契約価格（指数）", "group": "電子部品・半導体", "unit": "指数(2018年1月=100)",
    "source": "TrendForce 月次プレスリリースを基にした暫定推計値", "sourceUrl": "https://www.trendforce.com/presscenter",
    "provisional": True, "points": interp(NAND_A, MONTHS)}

indicators = {
  "deliveryNY": {"label": "納期長期化 拡散指数（NY連銀・現況）", "unit": "DI", "invert": False,
    "source": "FRED / NY連銀 Empire State 製造業調査「Delivery Time（現況）」", "sourceUrl": "https://fred.stlouisfed.org/series/DTCDISA066MSFRBNY",
    "provisional": False, "points": load_fred("DTCDISA066MSFRBNY"),
    "note": "0超＝回答企業の多数が「仕入先の納期が長期化している」と回答。サプライチェーン逼迫の代表的な実データ。"},
  "deliveryFutNY": {"label": "納期長期化 拡散指数（NY連銀・6ヶ月先）", "unit": "DI", "invert": False,
    "source": "FRED / NY連銀 Empire State 製造業調査「Delivery Time（先行き）」", "sourceUrl": "https://fred.stlouisfed.org/series/DTFDISA066MSFRBNY",
    "provisional": False, "points": load_fred("DTFDISA066MSFRBNY")},
  "ordersNY": {"label": "新規受注 拡散指数（NY連銀）", "unit": "DI", "invert": False,
    "source": "FRED / NY連銀 Empire State 製造業調査「New Orders」", "sourceUrl": "https://fred.stlouisfed.org/series/NOCDISA066MSFRBNY",
    "provisional": False, "points": load_fred("NOCDISA066MSFRBNY")},
  "durables": {"label": "米 耐久財 新規受注", "unit": "百万USD", "invert": False,
    "source": "FRED / U.S. Census（Durable Goods New Orders）", "sourceUrl": "https://fred.stlouisfed.org/series/DGORDER",
    "provisional": False, "points": load_fred("DGORDER")},
  "wsts": {"label": "世界半導体売上（3ヶ月移動平均）", "unit": "10億USD", "invert": False,
    "source": "WSTS Historical Billings Report を基にした暫定推計値", "sourceUrl": "https://www.wsts.org/67/Historical-Billings-Report",
    "provisional": True, "points": interp(WSTS_A, MONTHS)},
  "semiBill": {"label": "北米 半導体製造装置 出荷額", "unit": "10億USD", "invert": False,
    "source": "SEMI Billings Report を基にした暫定推計値", "sourceUrl": "https://www.semi.org/en/products-services/market-data/equipment/billings-report",
    "provisional": True, "points": interp(SEMIBILL_A, MONTHS)},
}

categories = [
  {"id":"conductor","name":"銅・導体系","desc":"コネクタ・圧着端子・バスバー・FPC/基板配線","examples":"角型コネクタ, 端子台, バスバー, フレキ基板",
   "basket":[["copper",0.70],["tin",0.15],["zinc",0.15]],"sector":None,"confidence":"高"},
  {"id":"solder","name":"はんだ・実装材料","desc":"はんだ・ソルダーペースト・めっき","examples":"鉛フリーはんだ, ソルダーペースト, プリフォーム",
   "basket":[["tin",0.60],["silver",0.25],["lead",0.15]],"sector":None,"confidence":"高"},
  {"id":"aluminum","name":"アルミ・放熱系","desc":"筐体・ヒートシンク・電解コンデンサ箔","examples":"押出ヒートシンク, ダイカスト筐体, アルミ電解コン",
   "basket":[["aluminum",0.80],["crude",0.20]],"sector":None,"confidence":"高"},
  {"id":"precious","name":"貴金属・電極系","desc":"MLCC電極・接点・ボンディングワイヤ・導電ペースト","examples":"MLCC, リレー接点, 金/銀ボンディングワイヤ, Agペースト",
   "basket":[["silver",0.40],["gold",0.40],["copper",0.20]],"sector":"semi","confidence":"中"},
  {"id":"resin_gp","name":"汎用樹脂","desc":"コネクタハウジング・筐体（PP / PA / PBT / PC）","examples":"コネクタハウジング, 樹脂筐体, ボビン, ケーブルグロメット",
   "basket":[["resin",0.55],["crude",0.25],["natgas",0.20]],"sector":None,"confidence":"中"},
  {"id":"resin_thermoset","name":"熱硬化・高機能樹脂","desc":"半導体封止材・注型・接着（エポキシ / フェノール）","examples":"モールド封止材, ポッティング材, 構造用接着剤",
   "basket":[["resinmfg",0.50],["crude",0.30],["natgas",0.20]],"sector":None,"confidence":"中"},
  {"id":"substrate","name":"基材・積層板","desc":"CCL / FR-4 / プリプレグ / ビルドアップ基板","examples":"銅張積層板, プリプレグ, ビルドアップ基板, BT基板",
   "basket":[["pcb",0.45],["copper",0.30],["resinmfg",0.25]],"sector":"semi","confidence":"中"},
  {"id":"pcb_assy","name":"プリント基板（実装前）","desc":"ベアボードの調達コスト","examples":"両面基板, 多層基板, 高多層基板",
   "basket":[["pcb",0.70],["copper",0.30]],"sector":"semi","confidence":"中"},
  {"id":"sheetmetal","name":"鋼材・板金","desc":"シャーシ・ブラケット・シールドケース","examples":"板金シャーシ, 取付ブラケット, シールドカバー",
   "basket":[["steel",0.70],["ironore",0.30]],"sector":None,"confidence":"高"},
  {"id":"harness","name":"ケーブル・ワイヤーハーネス","desc":"電線・被覆・コネクタ付き組電線","examples":"UL電線, 同軸ケーブル, ワイヤーハーネス, FFC",
   "basket":[["copper",0.60],["resin",0.25],["tin",0.15]],"sector":None,"confidence":"高"},
  {"id":"memory","name":"メモリ（DRAM / NAND）","desc":"DRAM・NAND・eMMC・SSD","examples":"DDR4/DDR5, eMMC, NAND, SSD",
   "basket":[["dram",0.55],["nand",0.35],["semippi",0.10]],"sector":"semi","confidence":"低（契約価格は暫定推計）"},
  {"id":"logic","name":"ロジック / MCU / アナログ半導体","desc":"MCU・電源IC・アナログ・FPGA・ドライバ","examples":"MCU, LDO/DC-DC, オペアンプ, ゲートドライバ, FPGA",
   "basket":[["semippi",0.55],["eleccomp",0.45]],"sector":"semi","confidence":"中"},
  {"id":"passive","name":"受動部品（コンデンサ・インダクタ）","desc":"MLCC・電解コン・インダクタ・フィルタ","examples":"MLCC, アルミ電解コン, パワーインダクタ, フェライトビーズ, EMIフィルタ",
   "basket":[["eleccomp",0.45],["silver",0.20],["nickel",0.20],["copper",0.15]],"sector":"semi","confidence":"中"},
  {"id":"resistor","name":"抵抗器","desc":"チップ抵抗・シャント・可変抵抗","examples":"チップ抵抗, 厚膜/薄膜抵抗, 電流検出シャント, 抵抗ネットワーク, ボリューム",
   "basket":[["eleccomp",0.50],["silver",0.20],["nickel",0.18],["copper",0.12]],"sector":"semi","confidence":"中"},
  {"id":"diode_sig","name":"ダイオード（小信号・ツェナー）","desc":"整流・定電圧・保護用の個別ダイオード","examples":"ツェナーダイオード, ショットキー, スイッチングダイオード, TVS/ESD, ブリッジダイオード",
   "basket":[["semippi",0.60],["eleccomp",0.30],["copper",0.10]],"sector":"semi","confidence":"中"},
  {"id":"transistor","name":"トランジスタ・MOSFET","desc":"小信号・スイッチング・電源用の個別トランジスタ","examples":"小信号トランジスタ, デジタルトランジスタ, MOSFET, IGBT",
   "basket":[["semippi",0.58],["eleccomp",0.30],["copper",0.12]],"sector":"semi","confidence":"中"},
  {"id":"led","name":"LED（チップLED・表示用）","desc":"表示・照光・バックライト用のLED","examples":"チップLED, 砲弾型LED, RGB LED, 赤外/紫外LED, LEDバックライト",
   "basket":[["semippi",0.40],["gold",0.22],["silver",0.20],["eleccomp",0.18]],"sector":"semi","confidence":"低"},
  {"id":"optocoupler","name":"フォトカプラ・光デバイス","desc":"絶縁伝送・位置検出用の光結合部品","examples":"フォトカプラ, フォトIC, フォトインタラプタ, フォトリレー",
   "basket":[["semippi",0.45],["eleccomp",0.30],["gold",0.15],["resinmfg",0.10]],"sector":"semi","confidence":"低"},
]

data = {
  "meta": {"generated": datetime.date.today().isoformat(), "rangeStart": MONTHS[0], "rangeEnd": MONTHS[-1], "months": MONTHS},
  "groups": ["ベースメタル", "貴金属", "鉄鋼原料", "エネルギー・化学", "電子部品・半導体"],
  "materials": materials,
  "indicators": indicators,
  "categories": categories,
  "annotations": [
    {"start":"2018-01","end":"2018-10","title":"DRAMスーパーサイクル","label":"2018年のDRAM高騰","note":"DRAM契約価格が高止まり。メモリのリードタイムが大幅に長期化。"},
    {"start":"2021-02","end":"2022-09","title":"コロナ後の全面的な供給逼迫","label":"2021〜22年の全面逼迫","note":"銅・すず・樹脂が同時に急騰し、半導体・受動部品も逼迫。NY連銀の納期指数は過去最悪水準。コネクタ・電源・MCUのリードタイムが52週超に。"},
    {"start":"2023-04","end":"2024-03","title":"メモリ・一部部材の市況の底","label":"2023〜24年の市況の底","note":"DRAM/NANDが記録的安値。多くの部材でリードタイムが正常化。"},
    {"start":"2024-10","end":"2026-07","title":"AI需要による再逼迫","label":"足元のAI再逼迫（2025年〜）","note":"HBM優先の生産配分で汎用DRAM・DDR4が逼迫。銅・金も並行して急騰し、複数の材料区分で同時に値上げ圧力。"},
  ],
  "method": "各材料区分の逼迫度スコア（0〜100）は、(1) 構成材料バスケットの価格モメンタム（前年比60%＋直近3ヶ月の年率換算40%）をロジスティック関数で0〜100に正規化した値と、(2) NY連銀 製造業調査の「仕入先の納期」拡散指数（現況70%＋先行き30%）を0〜100に換算した値を、おおよそ 58:42 で加重して算出。半導体・電子部品の区分はこれに WSTS売上・SEMI装置出荷のモメンタムを約3割ブレンドする。厳密な予測モデルではなく、相場と公開統計から逼迫の“兆候”を示す目安であり、数値そのものよりレベルの変化と方向感を見るための道具。バスケットの重みとしきい値は、実際の値上げ・納期事例と突き合わせて較正していく前提。",
}

with open(os.path.join(D, "data.json"), "w") as f:
    json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

print("materials %d / indicators %d / categories %d" % (len(materials), len(indicators), len(categories)))
print("months %s .. %s (%d)" % (MONTHS[0], MONTHS[-1], len(MONTHS)))
for k, v in list(materials.items()) + [("IND:" + a, b) for a, b in indicators.items()]:
    p = v["points"]
    print("  %-14s %s..%s  last=%s" % (k, p[0]["date"], p[-1]["date"], p[-1]["value"]))
