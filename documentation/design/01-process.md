# 01 字型設計流程與工具鏈

> 本文件是專案立項時（r1）寫的流程規劃，保留作為設計過程紀錄。實際的建置方式以根目錄的 README 為準：`scripts/build_glyphs.py` 產生輪廓，`scripts/export_fonts.py` 用 fontTools 直接輸出 OTF／TTF／WOFF2／UFO。

蒐集日期 2026-11-12。出處見文末。

## 1. 業界通用流程

多數教學與字型公司的說法一致，可以收斂成七步。順序不能跳，跳了後面要還債。

| 步 | 做什麼 | 產出 | 常見錯誤 |
| --- | --- | --- | --- |
| 1 定義 | 用途、氣質、字集、字重數 | 設計簡報 | 沒定用途就開始畫 |
| 2 控制字 | 先畫少數能代表整套的字（n、o、H、O 等） | DNA 與度量 | 一次畫完 26 個再回頭改 |
| 3 擴張 | 從控制字推導其餘字形，共用零件 | 完整字集 | 每個字各畫各的，筆畫粗細不一 |
| 4 字距 | 先設每個字左右的字腔（spacing） | 均勻的文字灰度 | 用字偶調整去補救爛字腔 |
| 5 字偶 | 只處理字腔解決不了的組合（kerning） | 字偶表 | 對數太多，維護不了 |
| 6 工程 | OpenType 功能、垂直度量、命名、hinting | 可安裝字型 | 各平台行高不一致 |
| 7 測試 | 真實文字、各字級、各軟體；回頭修 | 修訂清單 | 只看單字不看段落 |

三個要點：

- 字腔是規則，字偶是例外。先把字腔做對，字偶只是收尾。
- 判斷均勻要靠眼睛，數字只是起點。
- 字距、字偶、測試花的時間比畫字多。排程要留給後段。

常用測試字：`hamburgevons`、`adhesion`（直畫、曲線、接合、斜線都有）。本專案是哥德系，另加 `minimum`（全是直畫，專門測柵欄節奏）。

## 2. 本專案採用的流程

本專案有兩個特殊條件：字形全是直線，而且由兩個 AI 協作。所以把「手繪後描圖」換成「規範後產生」。

```
規範（03-spec.md）──► 產生器（Python）──► glyphs.json ──► UFO ──► fontmake ──► TTF／OTF
      ▲                                    │
      └────────── 樣張審稿 ◄───────────────┘
```

| 階段 | 內容 | 主責 | 完成條件 |
| --- | --- | --- | --- |
| P0 立項 | 主軸、規範、文字架構、42 個控制字 | Claude | 已完成（r1） |
| P1 定調 | FOX 看 r1，回覆待決事項；修控制字 | FOX、Claude | 控制字鎖定，規範升 1.0 |
| P2 補齊 | ASCII 95 字全部畫完 | Claude（判斷型）、Codex（推導型） | 95 字全部 approved |
| P3 字距 | 字腔分組、字偶、等寬數字 | Claude 定規則、Codex 做工具與初稿 | 測試文字灰度均勻 |
| P4 工程 | UFO 原始檔、fontmake 管線、OpenType 功能、檢查 | Codex | 一行指令產出可安裝字型 |
| P5 擴充 | Latin-1 附加字元、更多符號、風格集、第二字重 | 待定 | 待定 |

中文字不在目前範圍內。一套繁體中文字至少數千字，是另一個量級的專案。

## 3. 工具鏈

| 用途 | 選用 | 理由 |
| --- | --- | --- |
| 原始檔格式 | UFO（Unified Font Object） | 純文字、開放格式、可比對差異，任何主流字型編輯器都能開 |
| 產生輪廓 | Python + shapely | 字形是多邊形的聯集與差集，程式能保證格點與角度 |
| 編譯 | fontmake（底層是 fontTools） | 開源，UFO／designspace 直接編成 TTF／OTF |
| 手動微調 | FontForge（免費，Windows 可用）或 Fontra（開源，瀏覽器介面） | 需要用眼睛修的時候才開。Glyphs 只有 macOS 版，不適用 |
| 檢查 | 自寫的規範自檢，之後可加 fontbakery | 格點、角度、度量由程式把關 |

r1 為了先看到東西，暫時跳過 UFO，直接用 fontTools 產 TTF。P4 由 Codex 補上正式管線。

## 4. 出處

- TYPE01，字型設計工作流程（專案設定、一致性、原型階段）：https://type-01.com/?p=25661
- Made Good Designs，Type Design: How Typefaces Are Made（五階段流程、字腔與字偶的關係）：https://madegooddesigns.com/?p=5348
- Made Good Designs，How to Make a Font（測試字 hamburgevons／adhesion、時間分配）：https://madegooddesigns.com/?p=5351
- TypeType，Creating a font from scratch：https://typetype.org/blog/creating-a-font-from-scratch-a-detailed-guide-and-tips-for-choosing-software/
- Underscore Type，From idea to typeface：https://medium.com/underscore-type-foundry/from-idea-to-typeface-how-are-fonts-designed-649d365d3d1b
- fontmake：https://pypi.org/project/fontmake/3.5.1
- Simon Cozens，What happens when you compile a variable font（fontmake 內部流程）：https://simoncozens.github.io/compiling-variable-fonts
