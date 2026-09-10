# 調達アラート

電子部品・原材料の相場と公開サプライチェーン統計から、**材料区分ごとの逼迫度**と
リードタイム延伸の**兆候**を一望する購買・資材管理向けモニター。

仕入先の値上げ・納期回答が相場で裏付けられるかを、交渉前に確認するための道具。
厳密な予測ではなく「過去に相場が動いた局面ではリードタイムが伸びる傾向があった」という定性的な兆候の提示。

- 公開ページ（GitHub Pages）: `https://<user>.github.io/buzai-signal/`
- スナップショット（claude.ai Artifact）: https://claude.ai/code/artifact/f9420228-267d-46dd-bb22-5672e6ed2099

## 構成

| ファイル | 役割 |
|---|---|
| `fetch.py` | `raw/` の生データ（FRED CSV / Yahoo 金銀）を最新化。APIキー不要。失敗ソースは既存を維持 |
| `build.py` | `raw/` → `data.json`（20素材＋6指標＋13区分の時系列）を組み立て |
| `news.json` | 市況・部材欠品・地政学リスクの定性レイヤー（1日2回 自動更新） |
| `template.html` | UI本体。`__DATA__` と `__NEWS__` のプレースホルダを持つ |
| `inject.py` | `template.html` + `data.json` + `news.json` → `docs/index.html` |
| `docs/index.html` | GitHub Pages が配信する生成物 |
| `ROUTINE_PROMPT.md` | 自動更新クラウドエージェント（routine）に渡すプロンプト |

## ローカルでの更新

```sh
/usr/bin/python3 fetch.py      # 生データ最新化（任意）
/usr/bin/python3 build.py      # data.json 再生成
/usr/bin/python3 inject.py     # docs/index.html 再生成
git add -A && git commit -m "refresh" && git push
```

> 注: Homebrew版 python3 が不調な環境があったため、当面 `/usr/bin/python3`（macOS標準 3.9）を使う。標準ライブラリのみ・依存なし。

## 自動更新（フェーズ2）

- **相場・統計**: 月次。FRED/IMF の一次産品価格は月次公表なので、新しい月が出たときだけ数値が動く。
- **市況・ニュース**: 1日2回（朝5時／夕方15時 JST）。クラウドの routine が Web検索で
  最新の相場水準・部材欠品・リードタイム・地政学リスクを集め、`news.json` を再生成 →
  `build.py` / `inject.py` → `docs/index.html` を commit・push → GitHub Pages が再デプロイ。
- routine のプロンプトは `ROUTINE_PROMPT.md`。管理: https://claude.ai/code/routines

## データソース

すべて無料・公開。FRED（APIキー不要のCSVエンドポイント）、Yahoo Finance chart API（金・銀）、
NY連銀 Empire State 製造業調査の「仕入先の納期」拡散指数（リードタイム逼迫の実データ）。
DRAM/NAND契約価格・WSTS売上・SEMI装置出荷額のみ暫定推計値（UI上で「暫定推計」表示）。

## 逼迫度スコアの算出

各区分 = 構成材料バスケット（重み付き）の価格モメンタム（前年比60%＋直近3ヶ月の年率換算40%、
ロジスティック正規化）58% : NY連銀 納期拡散指数（現況70%＋先行30%）42%。
半導体・電子部品区分は WSTS/SEMI モメンタムを約3割ブレンド。
しきい値 25/42/58/74 で 緩和／通常／やや逼迫／逼迫／深刻。詳細は `build.py` の `method` とページ内「算出方法」。
