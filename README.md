# Grow3 3診断 実装正本

## 位置づけ

このディレクトリは、Grow3が運用する3診断の**実装上の正本**を管理する。

対象は次の3つ。

- 思考特性
- 行動特性
- 欲求プロフィール

概念・理論の説明は `grow3-frameworks.md` を参照する。
HTML/GAS、画面文言、assessment_version、保存スキーマ、デプロイ運用についてはこのディレクトリを正本とする。

> 2026-08-11時点で `grow3-frameworks.md` には旧運用語（例：行動スタイル、柔軟性）が一部残っている。
> 実装上の正式名称は本READMEの定義を優先し、概念正本側の文言同期は `docs/diagnostics-framework-sync_20260811.md` に従って行う。

---

## 正式名称とversion

| 種別 | 正式名称 | assessment_version |
|---|---|---|
| thinking | 思考特性 | `thinking-v3.2.1` |
| behavior | 行動特性 | `behavior-v3.2` |
| needs | 欲求プロフィール | `needs-v3.2` |

結果見出し：

- 思考特性の結果
- 行動特性の結果
- 欲求プロフィールの結果

### 行動特性 第3軸

旧称「柔軟性」は使用しない。

正式表示：**一貫・順応**

- 一貫寄り：自分の基準・決めた方針を保ちやすい
- 順応寄り：状況・相手・新情報に合わせて組み替えやすい

能力の高低ではなく、行動の出方の傾向として扱う。

---

## 本番公開URL

- 思考特性: `https://grow3.jp/diagnosis/thinking.html`
- 行動特性: `https://grow3.jp/diagnosis/behavior.html`
- 欲求プロフィール: `https://grow3.jp/diagnosis/needs.html`

本番GAS Web App:

`https://script.google.com/macros/s/AKfycbxN6MZZmZet7ltH98CyB5fz14qfqlUXxrJ6WLhb4oEMgP0ef6WicYFp4wNolmrG8CoNRQ/exec`

XServerでは `grow3.jp/public_html/diagnosis/` に3HTMLを配置する。

---

## 正本ファイル

```text
diagnostics/
├─ README.md
├─ backend/
│  ├─ assessment-backend-v3.1.1.gs
│  └─ production-smoke-test.gs
└─ web/
   ├─ thinking.html
   ├─ behavior.html
   └─ needs.html
```

`web/` の3ファイルは、2026-08-11の本番hotfix後にXServerへ配置した内容を正本とする。

---

## データモデル

### participants

```text
participant_id
name
birthdate
org
dept
external_member_id
created_at
updated_at
```

### assessment_tokens

```text
token_id
token_code
batch_id
issue_no
diag_type
participant_id
issued_at
expires_at
revoked_at
assigned_at
issued_by
```

`used` フラグは持たない。結果シートへの記録有無から使用済みを判定する。

### thinking_results

```text
result_id token_id participant_id diag_date name org dept
score_A score_B score_C score_D type_label
assessment_version answers_json completed_at
```

### behavior_results

```text
result_id token_id participant_id diag_date name org dept
score_s1 score_s2 score_s3
assessment_version answers_json completed_at
```

### needs_results

```text
result_id token_id participant_id diag_date name org dept
score_ai score_ch score_ji score_ta score_se
assessment_version answers_json completed_at
```

---

## 3診断の設計境界

3つを独立した箱として過度に分離しない。
同じ人物を見る3つのレンズとして扱う。

- 思考特性：どこに注意が向きやすく、どう解釈・判断しやすいか
- 行動特性：外から観察できる行動の出方
- 欲求プロフィール：何を相対的に優先しやすいか

概念上の重なりは許容する。
重複そのものを理由に設問を排除しない。

---

## UI・受験者向け表示の原則

- 運営者都合の内部情報を受験者へ見せない
- Spreadsheet、GAS、token_id、participant_id、assessment_version等を画面へ出さない
- 正常保存は無言で行う
- 保存失敗だけ受験者へ知らせる
- 「現在地」のような抽象的な比喩をタイトルに使わない
- 3診断の上帯はGrow3共通デザインで揃える
- 診断固有の可視化（4象限、3軸、5欲求）はそれぞれ残す

保存失敗時の表示：

> 結果の保存に失敗しました。画面を閉じず、担当者にお知らせください。

---

## 連打対策

2026-08-11の本番スモークで、欲求プロフィールを高速連打すると20問中1問が未回答のまま結果画面へ進める競合を発見した。

対応済み。

- `needs.html`: 画面遷移中は再入力を受け付けない
- `needs.html`: 結果表示前に20問全回答を再確認
- `behavior.html`: 同じ遷移実装だったため同時に対策
- `behavior.html`: 結果表示前に27問全回答を再確認
- 欲求プロフィールの二択に表示していた `A` / `B` ラベルを削除

---

## GASの重要ルール

### doPostは診断バックエンドだけが持つ

2026-08-11の本番移行時、同一Apps Scriptプロジェクト内に
LINE Producer Botの `doPost(e)` と診断GASの `doPost(e)` が共存していたため、
診断のPOSTがLINE Bot側で処理される競合が発生した。

症状：

```json
{"status":"ok"}
```

が返り、診断validateのJSONがブラウザへ返らなかった。

現在の本番Apps Scriptでは、LINE Bot側を一時的に `lineBotDoPost(e)` へ改名し、
診断用 `doPost(e)` のみを有効にしている。

**恒久方針：LINE Producer Botは別Apps Scriptプロジェクトへ分離する。**

診断GASプロジェクトへ、診断以外の `doPost` を追加しない。

---

## セットアップ保護

`initAssessmentSheets()` と `migrateLegacyThinkingToV3()` は、
スクリプトプロパティ

`V3_SETUP_ALLOWED_SPREADSHEET_ID`

が現在のスプレッドシートIDと一致する場合だけ実行可能。

移行時のみ一時設定し、完了後は削除する。

---

## 本番移行履歴（2026-08-11）

実施済み。

1. 本番スプレッドシートをコピーして退避
2. GAS v3.1.1反映
3. v3用5シート初期化
4. 旧思考診断データをv3へ移行
5. 件数確認＋旧新データのスポットチェック
6. 本番Web Appデプロイ
7. XServer `diagnosis/` へ3HTML配置
8. 本番スモークテスト
9. doPost競合修正
10. 連打対策・表示文言hotfix
11. 再スモーク確認

### 最終本番スモーク

batch: `PROD-SMOKE-20260811-094632`

- thinking: PASS / `thinking-v3.2.1`
- behavior: PASS / `behavior-v3.2`
- needs: PASS / `needs-v3.2`
- 3診断とも同一 `participant_id`
- `three_diagnostics_same_participant_and_expected_versions = true`

---

## 旧データ

旧 `tokens` / `results` は本番移行時に削除していない。
移行前バックアップも保持する。

旧受験者の自動名寄せは行わない。
人物同定は人間が判断する。

---

## 次フェーズ

本番移行の安定後に扱う。

- 3診断統合プロフィール
- `member-profile.html` の3診断対応
- `score-to-pdf.html` の3診断対応

統合プロフィールは `participant_id` を軸に派生生成し、正本データそのものにはしない。
