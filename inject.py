#!/usr/bin/env python3
"""template.html に data.json と news.json を埋め込んで docs/index.html を書き出す。

docs/ は GitHub Pages の公開ディレクトリ。
python3 inject.py
"""
import json, os

D = os.path.dirname(os.path.abspath(__file__))

tpl = open(os.path.join(D, "template.html")).read()
data = open(os.path.join(D, "data.json")).read().strip()
news_path = os.path.join(D, "news.json")
news = open(news_path).read().strip() if os.path.exists(news_path) else "null"
# minify news json
news = json.dumps(json.loads(news), ensure_ascii=False, separators=(",", ":"))

assert "__DATA__" in tpl and "__NEWS__" in tpl, "template.html にプレースホルダがありません"
out = tpl.replace("__DATA__", data).replace("__NEWS__", news)

os.makedirs(os.path.join(D, "docs"), exist_ok=True)
with open(os.path.join(D, "docs", "index.html"), "w") as f:
    f.write(out)
print("docs/index.html %d bytes (data %d, news %d)" % (len(out), len(data), len(news)))
