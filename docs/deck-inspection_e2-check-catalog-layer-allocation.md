---
status: approved
version: v0
基準日: 2026-08-22
種別: evidence-record
domain: deck-inspection
確定者: 小林裕司（Phase 1・E2照合。Contract v0 EVIDENCE_PENDING-E2の解消記録）
見直し: check-catalog／Contract境界文の改訂時に再照合する
---

# E2照合記録：check-catalog 31件の層割り当て

## 判定：E2: VERIFIED（境界文への矛盾 0件）

- 照合対象：`skills/office-artifact-validation/references/check-catalog.md`（v0.1.0現物）の全31 check_id
- 照合先：`docs/deck-inspection_integration-contract_v0.md` §2 境界文
  「第1層は機械判定可能な検査のみを担い、内容の設計整合・意味判断を行わない。第2層は第1層の対象外宣言に列挙された領域と設計整合を担い、第1層と同一観点の重複判定を行わない。」
- 実装状態の根拠：check-catalog現物・validation-common Schema（`check_id_heuristic_implemented` enum）・全テスト343ケースPASS（2026-08-22）

## 分類原則（Contract v0準拠）

- invariant／heuristic／systemは第1層
- `contract.*`は第1層側の暫定予約であり、現時点では**未実装**（v0 configでは受け付けない・0.x間互換性非保証）
- `contract.*`を実際に再利用するかは**V2**（`docs/deck-inspection_v2-check-id-mapping.md`）で判定する
- `deck.*`は第2層であり、既存31件には含まれない
- preflight（`scripts/pre-delivery-check.sh`）は31件の検査層ではなく、リポジトリ投入の入口検査

## 照合表（31件）

### invariant（10件）

| check_id | check_class | 実装状態 | 所有者 | 判定対象 | 境界整合 | 矛盾 | 備考 |
|---|---|---|---|---|---|---|---|
| package.zip_open | invariant | 実装済み | 第1層runner | ZIPとして開けるか | 第1層で整合 | なし | 前提検査。失敗時は後続がprerequisite_failed |
| package.duplicate_entry | invariant | 実装済み | 第1層runner | ZIP内エントリの重複 | 第1層で整合 | なし | — |
| package.required_part_exists | invariant | 実装済み | 第1層runner | 必須パーツの存在 | 第1層で整合 | なし | — |
| ooxml.xml_parse | invariant | 実装済み | 第1層runner | 各XMLパートの解析可否 | 第1層で整合 | なし | — |
| ooxml.relationship_target_exists | invariant | 実装済み | 第1層runner | リレーション参照先の存在 | 第1層で整合 | なし | — |
| ooxml.paragraph_child_order | invariant | 実装済み | 第1層runner | 段落子要素の順序（pPr→内容→endParaRPr） | 第1層で整合 | なし | 「本文が消えた」系事故の検知元 |
| ooxml.table_cell_border_order | invariant | 実装済み | 第1層runner | 表セルの罫線群→塗りの順序 | 第1層で整合 | なし | — |
| ooxml.table_cell_border_duplicate | invariant | 実装済み | 第1層runner | 同一セルの罫線要素重複 | 第1層で整合 | なし | — |
| pdf.open | invariant | 実装済み | 第1層runner | PDFとして開けるか | 第1層で整合 | なし | — |
| pdf.page_count_nonzero | invariant | 実装済み | 第1層runner | ページ数が1以上 | 第1層で整合 | なし | — |

### heuristic（7件）

| check_id | check_class | 実装状態 | 所有者 | 判定対象 | 境界整合 | 矛盾 | 備考 |
|---|---|---|---|---|---|---|---|
| text.low_content | heuristic | 実装済み | 第1層runner | 文字数が極端に少ないページ・スライド | 第1層で整合 | なし | pptx/docx/pdf。抑制可（意図はWARN＝人の判断へ委譲するため境界侵犯なし） |
| text.truncated_line | heuristic | **未実装**（全形式 not_implemented） | 第1層runner（予約） | 語の途中で切れて見える行 | 第1層で整合 | なし | 日本語の分かち書き不在で機械判定不能のため全形式見送り。config指定不可 |
| text.orphan_line | heuristic | 実装済み（PDFのみ） | 第1層runner | 1〜2文字の孤立行 | 第1層で整合 | なし | pptx/docxはnot_applicable |
| layout.footer_overlap | heuristic | 実装済み（PPTXのみ） | 第1層runner | フッター・ヘッダー帯との干渉 | 第1層で整合 | なし | 誤検出対処済み（帯認定75%・テキスト保有図形限定） |
| layout.out_of_bounds | heuristic | 実装済み（PPTXのみ） | 第1層runner | 用紙・スライド外へのはみ出し | 第1層で整合 | なし | 1pt許容差あり |
| font.too_small | heuristic | 実装済み | 第1層runner | 小さすぎる文字（形式別閾値） | 第1層で整合 | なし | 継承未解決runは非評価（evaluated_countで明示）。deck-contract投影フォント基準（24pt/18pt）はこの検査の**閾値設定**として載る余地があるが、基準の正本はdeck-contract側（criteria工程） |
| layout.too_many_lines | heuristic | 実装済み（PDFのみ） | 第1層runner | 1ページあたりの行数過多 | 第1層で整合 | なし | OOXMLは表示行数を取得できないためPDF限定 |

### contract（9件・暫定予約）

| check_id | check_class | 実装状態 | 所有者 | 判定対象 | 境界整合 | 矛盾 | 備考 |
|---|---|---|---|---|---|---|---|
| contract.required_terms | contract | **未実装**（暫定予約） | 第1層側暫定予約 | 必須語が指定位置に存在 | 第1層（機械判定）で整合 | なし | 再利用可否はV2 |
| contract.forbidden_terms | contract | **未実装**（暫定予約） | 第1層側暫定予約 | 禁止語・残留語がない | 第1層で整合 | なし | 同上 |
| contract.token_retention | contract | **未実装**（暫定予約） | 第1層側暫定予約 | 重要トークン（時刻・金額・台詞）の残存 | 第1層で整合 | なし | 同上 |
| contract.count | contract | **未実装**（暫定予約） | 第1層側暫定予約 | 枚数・ページ数・分類数が期待どおり | 第1層で整合 | なし | 同上 |
| contract.derivation | contract | **未実装**（暫定予約） | 第1層側暫定予約 | 元ファイルと派生物の対応 | 第1層で整合 | なし | v0 configはderivationsを読まない（roadmap管理） |
| contract.reference_integrity | contract | **未実装**（暫定予約） | 第1層側暫定予約 | ID・タグの重複、未定義参照 | 第1層で整合 | なし | 再利用可否はV2 |
| contract.ordering | contract | **未実装**（暫定予約） | 第1層側暫定予約 | 時刻の逆転、範囲の重複 | 第1層で整合 | なし | 同上 |
| contract.computed_value | contract | **未実装**（暫定予約） | 第1層側暫定予約 | 数式・期待値との一致 | 第1層で整合 | なし | 同上 |
| contract.anchor | contract | **未実装**（暫定予約） | 第1層側暫定予約 | 指定範囲に指定語がある／ない | 第1層で整合 | なし | 同上 |

### system（5件）

| check_id | check_class | 実装状態 | 所有者 | 判定対象 | 境界整合 | 矛盾 | 備考 |
|---|---|---|---|---|---|---|---|
| system.config_load | system | 実装済み | 第1層runner | 設定ファイルの読込可否 | 第1層で整合 | なし | 検査基盤の異常（ERROR専用）。成果物の判定ではない |
| system.config_schema | system | 実装済み | 第1層runner | 設定構造の正しさ（未知キー等） | 第1層で整合 | なし | — |
| system.input_resolution | system | 実装済み | 第1層runner | 入力指定の一意性（CLI／YAML競合） | 第1層で整合 | なし | — |
| system.artifact_open | system | 実装済み | 第1層runner | ライブラリでの後続処理用オブジェクト構築可否 | 第1層で整合 | なし | invariant通過後の基盤異常。成果物FAILと区別 |
| runner.uncaught_exception | system | 実装済み | 第1層runner | 検査実行中の想定外例外 | 第1層で整合 | なし | 最低限のERRORレポートを必ず残す設計 |

## 照合所見

1. **31件すべてが機械判定（構造・表記・整合・基盤異常）であり、内容の設計整合・意味判断を含む検査は1件も存在しない。** 境界文の前段（第1層＝機械判定のみ）と完全に整合する。
2. **第2層が担うべき領域（設計整合・意味判断）に踏み込む check_id はない。** したがって「第1層と同一観点の重複判定を行わない」の検証は、第2層の `deck.*` 設計時（criteria工程・V2以降）に、本表を対象外宣言の基礎として参照すれば足りる。
3. 境界の半分を定義する「第1層の対象外宣言」は、check-catalog上は `—`（形式非対応＝not_applicable）と `✕`（未実装＝not_implemented）の区別、およびheuristicの形式限定として現物に存在することを確認した。
4. 例外・特記は備考欄のとおり（font.too_smallの閾値とdeck-contract投影フォント基準の関係のみ、criteria工程での設計注意として記録）。矛盾には該当しない。
