#!/bin/bash
# =============================================================
# pre-delivery-check.sh の回帰テスト
# 使い方：bash scripts/test-pre-delivery-check.sh
# =============================================================
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CHECK="$SCRIPT_DIR/pre-delivery-check.sh"
REGISTRY="$SCRIPT_DIR/pre-delivery-intentional-uncertainty.tsv"
# 台帳整合は REPO_ROOT 相対pathを見るため、fixtureはgitignore済み_tmp_配下へ置く
FIXDIR="$REPO_ROOT/_tmp_pdc_test"
rm -rf "$FIXDIR"
mkdir -p "$FIXDIR"
TMPDIR=$(mktemp -d)
DEC_E24_BACKUP=""
REG_E45_BACKUP=""
trap '[ -n "$DEC_E24_BACKUP" ] && [ -f "$DEC_E24_BACKUP" ] && cp "$DEC_E24_BACKUP" "$REPO_ROOT/DECISIONS.md"; [ -n "$REG_E45_BACKUP" ] && [ -f "$REG_E45_BACKUP" ] && cp "$REG_E45_BACKUP" "$REGISTRY"; rm -rf "$TMPDIR" "$FIXDIR"' EXIT

PASS=0
FAILN=0

run_check() {
  env PRE_DELIVERY_UNCERTAINTY_REGISTRY="${PRE_DELIVERY_UNCERTAINTY_REGISTRY:-$REGISTRY}" \
    bash "$CHECK" "$@"
}

# $1=name $2=expected_code $3=must_regex $4=must_not_regex ; rest=args
assert_diag() {
  local name="$1" expect_code="$2" must="$3" must_not="$4"
  shift 4
  local code=0
  OUT=$(run_check "$@" 2>&1) || code=$?
  if [ "$code" -ne "$expect_code" ]; then
    echo "NG: $name → 終了コード${code}（期待：${expect_code}）"
    echo "$OUT" | sed 's/^/    /'
    FAILN=$((FAILN + 1))
    return
  fi
  if [ -n "$must" ] && ! printf '%s\n' "$OUT" | grep -Eq -- "$must"; then
    echo "NG: $name → 必須診断なし（期待マッチ：${must}）"
    echo "$OUT" | sed 's/^/    /'
    FAILN=$((FAILN + 1))
    return
  fi
  if [ -n "$must_not" ] && printf '%s\n' "$OUT" | grep -Eq -- "$must_not"; then
    echo "NG: $name → 禁止診断あり（禁止マッチ：${must_not}）"
    echo "$OUT" | sed 's/^/    /'
    FAILN=$((FAILN + 1))
    return
  fi
  echo "OK: $name"
  PASS=$((PASS + 1))
}

assert_exit0() {
  local name="$1"
  shift
  assert_diag "$name" 0 "" "" "$@"
}

assert_exit1() {
  local name="$1"
  shift
  assert_diag "$name" 1 "" "" "$@"
}

LINE_EXACT='改訂履歴: v0.1（初版）→ v0.1改訂（Evidence型別項目、source_form統一、occurrence_pattern／corroborated event分離、Hypothesis状態遷移・改訂操作、verification_action、§23未確定16項目統合）→ v0.1確定（Evidence型別管理、解釈の由来管理、Hypothesis状態遷移、因果表現の制約、秘匿性継承、validatorと人間確認の役割分担、未確定16項目のschema段階への送出）'
REL_PREFIX="_tmp_pdc_test"

# 1. frozen + 台帳登録済み
cat > "$FIXDIR/frozen_registered.md" <<EOF
---
status: frozen
---
${LINE_EXACT}
EOF
printf '%s\n' "${REL_PREFIX}/frozen_registered.md	1	history	改訂履歴の意図的保留を台帳登録するため	${LINE_EXACT}" > "$TMPDIR/registry1_min.tsv"
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/registry1_min.tsv" assert_exit0 "1. frozen+台帳登録済み" "$FIXDIR/frozen_registered.md"

# 2. draft + 未登録
cat > "$FIXDIR/draft_unregistered.md" <<'EOF'
---
status: draft
---
本文に未確定の語が残っている。
EOF
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/registry1_min.tsv" assert_exit0 "2. draft+未登録未確定" "$FIXDIR/draft_unregistered.md"

# 3 / E15. fence内A群・frozen → 検出FAIL（旧除外期待の反転）
cat > "$FIXDIR/fence.md" <<'EOF'
---
status: frozen
---
```
未確定の例
```
EOF
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/registry1_min.tsv" \
  assert_diag "3. E15 fence内A群・frozen→FAIL" 1 \
  "未確定表記が残存：未確定" \
  "意図的な未確定表記" \
  "$FIXDIR/fence.md"

# 4 / E23. 一般文書の記録形式節内soft・frozen → 検出FAIL
cat > "$FIXDIR/template_section.md" <<'EOF'
# サンプル

## 記録形式

- 未確定表記の例示

## 判断ログ

### DEC-001｜確定済み
EOF
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/registry1_min.tsv" \
  assert_diag "4. E23 一般文書の記録形式節内→FAIL" 1 \
  "未確定表記が残存：未確定" \
  "意図的な未確定表記" \
  "$FIXDIR/template_section.md"

# 4b / E24. 正本 DECISIONS.md の記録形式節内は除外（陽性回帰）
# path完全一致 DECISIONS.md だけが対象のため、正本へ一時的に soft を挿入して検証する
DEC_FILE="$REPO_ROOT/DECISIONS.md"
DEC_E24_BACKUP="$TMPDIR/DECISIONS.md.e24.bak"
cp "$DEC_FILE" "$DEC_E24_BACKUP"
awk '
  /^## 記録形式[[:space:]]*$/ { print; print ""; print "- 未確定表記の例示"; next }
  { print }
' "$DEC_E24_BACKUP" > "$DEC_FILE"
assert_diag "4b. E24 DECISIONS記録形式節内は除外" 0 \
  "" \
  "未確定表記が残存：未確定" \
  "$DEC_FILE"
cp "$DEC_E24_BACKUP" "$DEC_FILE"
DEC_E24_BACKUP=""

# 4b2 / E24-subdir. サブディレクトリ上の DECISIONS.md は記録形式節を除外しない
mkdir -p "$FIXDIR/subdir"
cat > "$FIXDIR/subdir/DECISIONS.md" <<'EOF'
# 派生 DECISIONS（除外対象外）

## 記録形式

- 未確定表記の例示

## 判断ログ

### DEC-001｜確定済み
- 本文に検出語なし
EOF
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/registry1_min.tsv" \
  assert_diag "4b2. E24-subdir サブdirのDECISIONSは記録形式除外しない" 1 \
  "未確定表記が残存：未確定" \
  "意図的な未確定表記" \
  "$FIXDIR/subdir/DECISIONS.md"
rm -rf "$FIXDIR/subdir"

# 4c / E16. fence内B群・draft → WARN（exit 0）
cat > "$FIXDIR/fence_b_draft.md" <<'EOF'
---
status: draft
---
```
TODO: fence内
```
EOF
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/registry1_min.tsv" \
  assert_diag "4c. E16 fence内B群・draft→WARN" 0 \
  "未確定表記が残存：TODO" \
  "未確定表記が残存：未確定" \
  "$FIXDIR/fence_b_draft.md"

# 4d / E17. fence内B群・frozen → FAIL
cat > "$FIXDIR/fence_b_frozen.md" <<'EOF'
---
status: frozen
---
```
TODO: fence内
```
EOF
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/registry1_min.tsv" \
  assert_diag "4d. E17 fence内B群・frozen→FAIL" 1 \
  "未確定表記が残存：TODO" \
  "reasonが空" \
  "$FIXDIR/fence_b_frozen.md"

# 4e / E18. fence内C群 → 常時FAIL
cat > "$FIXDIR/fence_c.md" <<'EOF'
---
status: draft
---
```
★★要修正
```
EOF
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/registry1_min.tsv" \
  assert_diag "4e. E18 fence内C群→FAIL" 1 \
  "未確定表記が残存：★★" \
  "reasonが空" \
  "$FIXDIR/fence_c.md"

# 5. 実ファイル3件
assert_exit0 "5. 実ファイル3件" \
  "$REPO_ROOT/DECISIONS.md" \
  "$REPO_ROOT/docs/organization-diagnosis_設計メモ_v0.1.md" \
  "$REPO_ROOT/docs/organization-diagnosis_schema設計メモ_v0.1.md"

# 6. frozen + 未登録
cat > "$FIXDIR/frozen_unregistered.md" <<'EOF'
---
status: frozen
---
未登録の未確定表記です。
EOF
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/registry1_min.tsv" assert_exit1 "6. frozen+未登録未確定" "$FIXDIR/frozen_unregistered.md"

# 7. 台帳行1文字変更 → 陳腐化FAIL
cat > "$FIXDIR/modified_line.md" <<'EOF'
---
status: frozen
---
改訂履歴: v0.1（初版）→ v0.1改訂（Evidence型別項目、source_form統一、occurrence_pattern／corroborated event分離、Hypothesis状態遷移・改訂操作、verification_action、§23未確定17項目統合）→ v0.1確定（Evidence型別管理、解釈の由来管理、Hypothesis状態遷移、因果表現の制約、秘匿性継承、validatorと人間確認の役割分担、未確定16項目のschema段階への送出）
EOF
printf '%s\n' "${REL_PREFIX}/modified_line.md	1	history	照合用の台帳行	${LINE_EXACT}" > "$TMPDIR/registry7.tsv"
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/registry7.tsv" \
  assert_diag "7. 台帳行1文字変更→陳腐化" 1 \
  "登録行が本文に存在しません" \
  "reasonが空" \
  "$FIXDIR/modified_line.md"

# 8. expected_count超過
cat > "$FIXDIR/duplicate.md" <<'EOF'
---
status: frozen
---
| status | 状態（語彙・遷移は§23未確定） |
| status | 状態（語彙・遷移は§23未確定） |
| status | 状態（語彙・遷移は§23未確定） |
EOF
cp "$REGISTRY" "$TMPDIR/registry8.tsv"
printf '%s\n' "${REL_PREFIX}/duplicate.md	2	deferred_v0.2	超過検出用の一時登録	| status | 状態（語彙・遷移は§23未確定） |" >> "$TMPDIR/registry8.tsv"
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/registry8.tsv" \
  assert_diag "8. expected_count超過" 1 \
  "expected_countを超過|台帳許可件数を超過" \
  "reasonが空" \
  "$FIXDIR/duplicate.md"

# 9. TODO in frozen
cat > "$FIXDIR/todo_frozen.md" <<'EOF'
---
status: frozen
---
TODO: 残タスク
EOF
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/registry1_min.tsv" assert_exit1 "9. frozen+TODO" "$FIXDIR/todo_frozen.md"

# 10. ★★ in draft
cat > "$FIXDIR/stars_draft.md" <<'EOF'
---
status: draft
---
★★要修正
EOF
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/registry1_min.tsv" assert_exit1 "10. draft+★★" "$FIXDIR/stars_draft.md"

# 11. 不正classification
cat > "$TMPDIR/bad_class.tsv" <<'EOF'
# bad
bad.md	1	invalid_class	理由あり	未確定
EOF
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/bad_class.tsv" \
  assert_diag "11. 不正classification" 1 \
  "classificationが不正" \
  "列不足" \
  "$FIXDIR/frozen_unregistered.md"

# 12. expected_count=0
cat > "$TMPDIR/bad_count.tsv" <<'EOF'
bad.md	0	history	理由あり	未確定
EOF
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/bad_count.tsv" \
  assert_diag "12. expected_count=0" 1 \
  "expected_countが不正" \
  "classificationが不正" \
  "$FIXDIR/frozen_unregistered.md"

# 13. 重複登録
cat > "$TMPDIR/dup_registry.tsv" <<'EOF'
dup.md	1	history	理由A	未確定行
dup.md	1	history	理由B	未確定行
EOF
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/dup_registry.tsv" \
  assert_diag "13. 台帳重複登録" 1 \
  "重複登録" \
  "reasonが空" \
  "$FIXDIR/frozen_unregistered.md"

# 14. 正常5列読込
cat > "$FIXDIR/ok.md" <<'EOF'
---
status: frozen
---
未確定の行
EOF
printf '%s\n' "${REL_PREFIX}/ok.md	1	history	正常な理由	未確定の行" > "$TMPDIR/ok5.tsv"
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/ok5.tsv" \
  assert_diag "14. 正常5列読込" 0 \
  "意図的な未確定表記" \
  "台帳エラー" \
  "$FIXDIR/ok.md"

# 15. TABが4個未満
printf '%s\n' "bad.md	1	history	未確定" > "$TMPDIR/cols_short.tsv"
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/cols_short.tsv" \
  assert_diag "15. TAB4個未満→列不足" 1 \
  "列不足" \
  "reasonが空" \
  "$FIXDIR/frozen_unregistered.md"

# 16. reason空
printf '%s\n' "bad.md	1	history		未確定" > "$TMPDIR/reason_empty.tsv"
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/reason_empty.tsv" \
  assert_diag "16. reason空" 1 \
  "reasonが空" \
  "列不足" \
  "$FIXDIR/frozen_unregistered.md"

# 17. reason空白のみ
printf '%s\n' "bad.md	1	history	   		未確定" > "$TMPDIR/reason_blank.tsv"
# 4 tabs: path, exp, class, spaces-only reason, exact — need exactly spaces between 3rd and 4th tab
printf 'bad.md\t1\thistory\t   \t未確定\n' > "$TMPDIR/reason_blank.tsv"
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/reason_blank.tsv" \
  assert_diag "17. reason空白のみ" 1 \
  "reasonが空" \
  "列不足" \
  "$FIXDIR/frozen_unregistered.md"

# 18. exact_line空
printf 'bad.md\t1\thistory\t理由あり\t\n' > "$TMPDIR/exact_empty.tsv"
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/exact_empty.tsv" \
  assert_diag "18. exact_line空" 1 \
  "exact_lineが空" \
  "reasonが空" \
  "$FIXDIR/frozen_unregistered.md"

# 19. expected_count非数値
printf '%s\n' "bad.md	x	history	理由あり	未確定" > "$TMPDIR/count_nonnum.tsv"
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/count_nonnum.tsv" \
  assert_diag "19. expected_count非数値" 1 \
  "expected_countが不正" \
  "classificationが不正" \
  "$FIXDIR/frozen_unregistered.md"

# 20. expected_count負数
printf '%s\n' "bad.md	-1	history	理由あり	未確定" > "$TMPDIR/count_neg.tsv"
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/count_neg.tsv" \
  assert_diag "20. expected_count負数" 1 \
  "expected_countが不正" \
  "classificationが不正" \
  "$FIXDIR/frozen_unregistered.md"

# 21. hard patternを含むexact_line
printf '%s\n' "bad.md	1	history	理由あり	本文に★★を含む行" > "$TMPDIR/hard_exact.tsv"
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/hard_exact.tsv" \
  assert_diag "21. hardをexact_lineへ登録" 1 \
  "hard検出語" \
  "重複登録" \
  "$FIXDIR/frozen_unregistered.md"

# 22. 登録先ファイル不在（本文対象0件でも整合）
printf '%s\n' "missing-file-does-not-exist.md	1	history	欠落検知用	未確定の行" > "$TMPDIR/missing_path.tsv"
OUT=$(env PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/missing_path.tsv" bash "$CHECK" 2>&1) || code=$?
code=${code:-0}
if [ "$code" -ne 1 ] \
  || ! printf '%s\n' "$OUT" | grep -Eq "登録先ファイルが存在しません" \
  || ! printf '%s\n' "$OUT" | grep -q "検査対象がありません"; then
  echo "NG: 22. 登録先不在（本文0件でも整合）"
  echo "$OUT" | sed 's/^/    /'
  FAILN=$((FAILN + 1))
else
  echo "OK: 22. 登録先不在（本文0件でも整合）"
  PASS=$((PASS + 1))
fi
code=0

# 23. exact_line実件数0（陳腐化）
cat > "$FIXDIR/stale.md" <<'EOF'
---
status: frozen
---
別の未確定表記
EOF
printf '%s\n' "${REL_PREFIX}/stale.md	1	history	陳腐化検知用	存在しない未確定行XYZ" > "$TMPDIR/stale.tsv"
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/stale.tsv" \
  assert_diag "23. exact_line実件数0→陳腐化" 1 \
  "登録行が本文に存在しません" \
  "reasonが空" \
  "$FIXDIR/stale.md"

# 24. 実件数不足
cat > "$FIXDIR/under.md" <<'EOF'
---
status: frozen
---
| status | 状態（語彙・遷移は§23未確定） |
EOF
printf '%s\n' "${REL_PREFIX}/under.md	2	history	件数不足検知用	| status | 状態（語彙・遷移は§23未確定） |" > "$TMPDIR/under.tsv"
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/under.tsv" \
  assert_diag "24. 実件数不足" 1 \
  "実件数がexpected_count未満" \
  "実件数がexpected_countを超過" \
  "$FIXDIR/under.md"

# 25. exact_lineにTAB
cat > "$FIXDIR/tab_doc.md" <<'EOF'
---
status: frozen
---
EOF
printf 'col1\twith\ttabs 未確定\n' >> "$FIXDIR/tab_doc.md"
printf '%s\t1\thistory\tTAB含む行の登録\tcol1\twith\ttabs 未確定\n' "${REL_PREFIX}/tab_doc.md" > "$TMPDIR/tab_reg.tsv"
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/tab_reg.tsv" \
  assert_diag "25. exact_lineにTAB→正常照合" 0 \
  "意図的な未確定表記" \
  "台帳エラー" \
  "$FIXDIR/tab_doc.md"

# 26. reason内TABによる列ずれ → 陳腐化
printf '%s\t1\thistory\t前半\tずれ理由\t未確定の行\n' "${REL_PREFIX}/shift.md" > "$TMPDIR/reason_tab.tsv"
cat > "$FIXDIR/shift.md" <<'EOF'
---
status: frozen
---
未確定の行
EOF
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/reason_tab.tsv" \
  assert_diag "26. reason内TAB→陳腐化FAIL" 1 \
  "登録行が本文に存在しません" \
  "reasonが空" \
  "$FIXDIR/shift.md"

# 27 / E54. fence外1+fence内1、expected=2 → 登録済みWARN（件数2）
cat > "$FIXDIR/fence_count.md" <<'EOF'
---
status: frozen
---
件数確認用の未確定行
```
件数確認用の未確定行
```
EOF
printf '%s\n' "${REL_PREFIX}/fence_count.md	2	history	fence内外の件数統一確認	件数確認用の未確定行" > "$TMPDIR/fence_count2.tsv"
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/fence_count2.tsv" \
  assert_diag "27. E54 fence内外expected=2→OK" 0 \
  "意図的な未確定表記" \
  "台帳許可件数を超過|実件数がexpected_countを超過" \
  "$FIXDIR/fence_count.md"

# 28 / E55. 同条件 expected=1 → 超過FAIL
printf '%s\n' "${REL_PREFIX}/fence_count.md	1	history	fence内外の件数超過確認	件数確認用の未確定行" > "$TMPDIR/fence_count1.tsv"
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/fence_count1.tsv" \
  assert_diag "28. E55 fence内外expected=1→超過FAIL" 1 \
  "台帳許可件数を超過|実件数がexpected_countを超過" \
  "登録行が本文に存在しません" \
  "$FIXDIR/fence_count.md"

# =============================================================
# staged / index snapshot 系（E41〜E47・E51〜E53・S04）
# 実indexは一切変更しない。GIT_INDEX_FILEによる一時indexを
# read-tree HEADで初期化し、全staged fixtureとchecker実行を
# その一時index上で行う。
# =============================================================
TEST_INDEX="$TMPDIR/pdc-test-index"

git_tmp() {
  GIT_INDEX_FILE="$TEST_INDEX" git -C "$REPO_ROOT" -c core.quotepath=false "$@"
}

reset_test_index() {
  rm -f "$TEST_INDEX"
  git_tmp read-tree HEAD
}

# $1=name $2=expected_code $3=must $4=must_not $5=registry_mode(explicit|default)
# $6=optional 実行profile:
#   renames_false … checkerプロセスにだけ diff.renames=false を注入（E48〜E50）
#   office_tmp    … checkerプロセスにだけ suite専用TMPDIRを注入（E56〜E59）
assert_staged() {
  local name="$1" expect_code="$2" must="$3" must_not="$4" regmode="$5"
  local profile="${6:-}"
  local code=0
  local -a run_env=( "GIT_INDEX_FILE=$TEST_INDEX" )
  if [ "$profile" = "renames_false" ]; then
    run_env+=(
      "GIT_CONFIG_COUNT=1"
      "GIT_CONFIG_KEY_0=diff.renames"
      "GIT_CONFIG_VALUE_0=false"
    )
  fi
  if [ "$profile" = "office_tmp" ]; then
    run_env+=( "TMPDIR=$OFFICE_TEST_TMPROOT" )
  fi
  if [ "$regmode" = "default" ]; then
    OUT=$(env -u PRE_DELIVERY_UNCERTAINTY_REGISTRY "${run_env[@]}" \
      bash "$CHECK" --staged 2>&1) || code=$?
  else
    OUT=$(env "${run_env[@]}" \
      PRE_DELIVERY_UNCERTAINTY_REGISTRY="${STAGED_REGISTRY:-$REGISTRY}" \
      bash "$CHECK" --staged 2>&1) || code=$?
  fi
  if [ "$code" -ne "$expect_code" ]; then
    echo "NG: $name → 終了コード${code}（期待：${expect_code}）"
    echo "$OUT" | sed 's/^/    /'
    FAILN=$((FAILN + 1))
    return
  fi
  if [ -n "$must" ] && ! printf '%s\n' "$OUT" | grep -Eq -- "$must"; then
    echo "NG: $name → 必須診断なし（期待マッチ：${must}）"
    echo "$OUT" | sed 's/^/    /'
    FAILN=$((FAILN + 1))
    return
  fi
  if [ -n "$must_not" ] && printf '%s\n' "$OUT" | grep -Eq -- "$must_not"; then
    echo "NG: $name → 禁止診断あり（禁止マッチ：${must_not}）"
    echo "$OUT" | sed 's/^/    /'
    FAILN=$((FAILN + 1))
    return
  fi
  echo "OK: $name"
  PASS=$((PASS + 1))
}

# HEAD上の .gitignore を一時index上で new_rel へ rename（必要なら new_blob に差替え）
# working tree には新pathを作らない。一時index内の新規A→移動は使わない。
stage_gitignore_rename() {
  local new_rel="$1" new_blob="${2:-}"
  local line mode sha
  reset_test_index
  line=$(git_tmp ls-files --stage -- .gitignore | head -1)
  mode=$(printf '%s\n' "$line" | awk '{print $1}')
  sha=$(printf '%s\n' "$line" | awk '{print $2}')
  [ -n "$mode" ] && [ -n "$sha" ] || {
    echo "NG: stage_gitignore_rename → .gitignore が一時indexにありません"
    FAILN=$((FAILN + 1))
    return 1
  }
  if [ -n "$new_blob" ]; then
    sha="$new_blob"
  fi
  git_tmp update-index --force-remove -- .gitignore
  git_tmp update-index --add --cacheinfo "${mode},${sha},${new_rel}"
}

# rename が R として見えることの補助確認（checker合格の代替にはしない）
assert_rename_name_status() {
  local name="$1" old_path="$2" new_path="$3"
  local ns
  ns=$(GIT_INDEX_FILE="$TEST_INDEX" git -C "$REPO_ROOT" \
    -c core.quotepath=false -c diff.renames=false \
    diff --cached --name-status --diff-filter=ACMR --find-renames 2>/dev/null || true)
  if ! printf '%s\n' "$ns" | grep -Eq "^R[0-9]*[[:space:]]+${old_path}[[:space:]]+${new_path}$"; then
    echo "NG: $name → rename name-status 補助確認失敗"
    echo "$ns" | sed 's/^/    /'
    FAILN=$((FAILN + 1))
    return 1
  fi
  return 0
}

# 実index非破壊の事前スナップショット（末尾検査で照合）
# mode・blob SHA・stage番号・pathを含むindex実体をハッシュ化して比較する
real_index_hash() {
  git -C "$REPO_ROOT" ls-files --stage -z | git hash-object --stdin
}
REAL_INDEX_BEFORE=$(real_index_hash)

# 29 / E41. staged版は正常／working tree版は違反 → exit 0（index本文が正）
reset_test_index
cat > "$FIXDIR/e41.md" <<'EOF'
---
status: frozen
---
確定済みの本文
EOF
git_tmp add -f "$FIXDIR/e41.md"
cat > "$FIXDIR/e41.md" <<'EOF'
---
status: frozen
---
この行は未確定
EOF
assert_staged "29. E41 index正常/WT違反→exit0" 0 \
  "" \
  "未確定表記が残存" \
  explicit

# 30 / E42. staged版は違反／working tree版は正常 → FAIL
reset_test_index
cat > "$FIXDIR/e42.md" <<'EOF'
---
status: frozen
---
この行は未確定
EOF
git_tmp add -f "$FIXDIR/e42.md"
cat > "$FIXDIR/e42.md" <<'EOF'
---
status: frozen
---
確定済みの本文
EOF
assert_staged "30. E42 index違反/WT正常→FAIL" 1 \
  "\[FAIL\].*未確定表記が残存" \
  "" \
  explicit

# 31 / E43. staged本文違反＋staged status frozen、WTは本文・status変更済み → soft FAIL
reset_test_index
cat > "$FIXDIR/e43.md" <<'EOF'
---
status: frozen
---
この行は未確定
EOF
git_tmp add -f "$FIXDIR/e43.md"
cat > "$FIXDIR/e43.md" <<'EOF'
---
status: draft
---
確定済みの本文
EOF
assert_staged "31. E43 index本文+index statusでsoft FAIL" 1 \
  "\[FAIL\].*未確定表記が残存" \
  "\[WARN\].*未確定表記が残存" \
  explicit

# 32 / E44. staged本文正常＋staged status frozen、WTだけdraft＋違反本文 → exit 0
reset_test_index
cat > "$FIXDIR/e44.md" <<'EOF'
---
status: frozen
---
確定済みの本文
EOF
git_tmp add -f "$FIXDIR/e44.md"
cat > "$FIXDIR/e44.md" <<'EOF'
---
status: draft
---
この行は未確定
EOF
assert_staged "32. E44 index本文+index statusで違反なし" 0 \
  "" \
  "未確定表記が残存" \
  explicit

# 33 / E45. staged既定台帳は正常／WT既定台帳は不正 → index台帳で読込成功
reset_test_index
REG_E45_BACKUP="$TMPDIR/registry-e45-backup.tsv"
cp "$REGISTRY" "$REG_E45_BACKUP"
printf 'broken registry without tabs\n' > "$REGISTRY"
assert_staged "33. E45 index既定台帳正常/WT不正→exit0" 0 \
  "" \
  "台帳エラー|台帳ファイルが存在しません" \
  default
cp "$REG_E45_BACKUP" "$REGISTRY"
REG_E45_BACKUP=""

# 34 / E46. staged既定台帳は不正／WT既定台帳は正常 → index台帳に基づく読込FAIL
reset_test_index
E46_BLOB=$(printf 'broken registry without tabs\n' | git -C "$REPO_ROOT" hash-object -w --stdin)
git_tmp update-index --cacheinfo "100644,$E46_BLOB,scripts/pre-delivery-intentional-uncertainty.tsv"
assert_staged "34. E46 index既定台帳不正/WT正常→FAIL" 1 \
  "台帳エラー：列不足" \
  "" \
  default

# 35 / E47. 明示指定台帳（不正classification）はstagedでも実ファイルを読む
reset_test_index
STAGED_REGISTRY="$TMPDIR/e47.tsv"
printf '%s\n' "${REL_PREFIX}/e47.md	1	bad_class	明示指定テスト	なにかの行" > "$STAGED_REGISTRY"
assert_staged "35. E47 staged明示指定=実ファイル読込" 1 \
  "classificationが不正" \
  "Git indexに存在しません|台帳ファイルが存在しません" \
  explicit
unset STAGED_REGISTRY

# 36 / E51. 登録対象ファイルだけindexから削除（本文対象0件） → 登録先不在FAIL
reset_test_index
REG_FIRST_PATH=$(grep -v '^[[:space:]]*#' "$REGISTRY" | grep -v '^[[:space:]]*$' | head -1 | cut -f1)
git_tmp update-index --force-remove -- "$REG_FIRST_PATH"
assert_staged "36. E51 登録先をindex削除→0件でも不在FAIL" 1 \
  "登録先ファイルが存在しません（${REG_FIRST_PATH}）" \
  "" \
  default

# 37 / E52. 台帳ファイルだけをstage（登録先不在の行を追加） → 0件でも台帳整合FAIL
reset_test_index
{ git_tmp show ":scripts/pre-delivery-intentional-uncertainty.tsv"; \
  printf '%s\n' "_tmp_pdc_test/ghost.md	1	history	index snapshotテスト用	この行は存在しない"; } > "$TMPDIR/e52.tsv"
E52_BLOB=$(git -C "$REPO_ROOT" hash-object -w --stdin < "$TMPDIR/e52.tsv")
git_tmp update-index --cacheinfo "100644,$E52_BLOB,scripts/pre-delivery-intentional-uncertainty.tsv"
assert_staged "37. E52 台帳のみstage→0件でも整合FAIL" 1 \
  "登録先ファイルが存在しません（_tmp_pdc_test/ghost.md）" \
  "" \
  default

# 38 / E53. staged対象がすべて除外対象 → 除外だけを理由に整合をスキップしない
reset_test_index
E53_DUMMY_BLOB=$(printf 'dummy excluded content\n' | git -C "$REPO_ROOT" hash-object -w --stdin)
git_tmp update-index --add --cacheinfo "100644,$E53_DUMMY_BLOB,scripts/_pdc_test_dummy.md"
git_tmp update-index --cacheinfo "100644,$E52_BLOB,scripts/pre-delivery-intentional-uncertainty.tsv"
assert_staged "38. E53 staged全件除外でも台帳整合FAIL" 1 \
  "登録先ファイルが存在しません（_tmp_pdc_test/ghost.md）" \
  "" \
  default

# 39 / S04. 静的契約：既定台帳のみindex読取・明示指定は実ファイルの分岐が存在
if grep -q 'REGISTRY_EXPLICIT=1' "$CHECK" \
   && grep -q 'REGISTRY_EXPLICIT" -eq 0' "$CHECK"; then
  echo "OK: 39. S04 既定台帳index/明示指定実ファイルの分岐存在"
  PASS=$((PASS + 1))
else
  echo "NG: 39. S04 分岐が見つかりません"
  FAILN=$((FAILN + 1))
fi

# =============================================================
# ACMR / rename 系（E48〜E50）
# 旧pathは HEAD の .gitignore。一時indexのみ操作し WT/実index は触らない。
# checker 実行時のみ GIT_CONFIG_* で diff.renames=false を注入する。
# =============================================================

# 40 / E48. リネームのみ（違反なし）→ 新pathを走査し exit 0（vacuous禁止）
stage_gitignore_rename "_tmp_pdc_test/e48_renamed.md"
assert_rename_name_status "40. E48 補助name-status" ".gitignore" "_tmp_pdc_test/e48_renamed.md" || true
assert_staged "40. E48 リネームのみ・違反なし→exit0" 0 \
  "対象 [1-9][0-9]*ファイル" \
  "検査対象がありません|\\[FAIL\\]" \
  default \
  renames_false

# 41 / E49. リネーム＋hard（★★）最小編集 → 新path index 本文で FAIL
E49_BLOB=$(
  { git -C "$REPO_ROOT" show HEAD:.gitignore; printf '%s\n' '★★'; } \
    | git -C "$REPO_ROOT" hash-object -w --stdin
)
stage_gitignore_rename "_tmp_pdc_test/e49_renamed.md" "$E49_BLOB"
assert_rename_name_status "41. E49 補助name-status" ".gitignore" "_tmp_pdc_test/e49_renamed.md" || true
assert_staged "41. E49 リネーム＋★★→新path hard FAIL" 1 \
  "_tmp_pdc_test/e49_renamed.md.*未確定表記が残存：★★|未確定表記が残存：★★" \
  "検査対象がありません" \
  default \
  renames_false

# 42 / E50. 未登録frozen相当のリネーム＋soft → 本文 soft FAIL（台帳不在だけ禁止）
E50_BLOB=$(
  { git -C "$REPO_ROOT" show HEAD:.gitignore; printf '%s\n' '未確定'; } \
    | git -C "$REPO_ROOT" hash-object -w --stdin
)
stage_gitignore_rename "_tmp_pdc_test/e50_renamed.md" "$E50_BLOB"
assert_rename_name_status "42. E50 補助name-status" ".gitignore" "_tmp_pdc_test/e50_renamed.md" || true
assert_staged "42. E50 未登録リネーム＋未確定→本文 soft FAIL" 1 \
  "_tmp_pdc_test/e50_renamed.md.*未確定表記が残存：未確定|未確定表記が残存：未確定" \
  "未確定表記が残存：★★" \
  default \
  renames_false

# 43 / ACMR／find-renames／NUL契約：staged収集コマンド行に
# --name-only -z・--diff-filter=ACMR・--find-renames がすべて明示されていること
# （コメント行は除外し、diff --cached 収集行だけを見る）
if awk '
  /^[[:space:]]*#/ { next }
  /diff --cached/ && /--name-only -z/ && /--diff-filter=ACMR/ && /--find-renames/ { found=1 }
  END { exit found ? 0 : 1 }
' "$CHECK"; then
  echo "OK: 43. ACMR／find-renames／-z契約（staged収集コマンド）"
  PASS=$((PASS + 1))
else
  echo "NG: 43. ACMR／find-renames／-z契約（staged収集にACMR+find-renames+-zなし）"
  FAILN=$((FAILN + 1))
fi

# =============================================================
# staged Office index検査系（E56〜E60）
# fixtureは固定base64リテラルから復元した最小ZIP（zip/Python等の追加依存なし）。
# checker子processにはsuite専用TMPDIRを渡し、E60で一時dir残骸0件を確認する。
# 一時indexのみ操作し、working tree側fixtureは_tmp_pdc_test配下だけを使う。
# =============================================================
OFFICE_TEST_TMPROOT="$TMPDIR/checker-office-tmp"
mkdir -p "$OFFICE_TEST_TMPROOT"

# 正常ZIP fixture（member: content.xml / 内容: <doc><t>office fixture clean</t></doc>）
OFFICE_CLEAN_ZIP_B64='UEsDBBQAAAAIANCx81wTT2tsKAAAACgAAAALAAAAY29udGVudC54bWyzSclPtrMpsctPS8tMTlVIy6woKS1KVUjOSU3Ms9EvsbPRByng5QIAUEsBAhQAFAAAAAgA0LHzXBNPa2woAAAAKAAAAAsAAAAAAAAAAAAAAAAAAAAAAGNvbnRlbnQueG1sUEsFBgAAAAABAAEAOQAAAFEAAAAAAA=='
# hard違反ZIP fixture（member: content.xml / 内容: <doc><t>★★</t></doc>）
OFFICE_HARD_ZIP_B64='UEsDBBQAAAAIANCx81yNi7CsGgAAABoAAAALAAAAY29udGVudC54bWyzSclPtrMpsXs0o/XRjFYb/RI7G32QEC8XAFBLAQIUABQAAAAIANCx81yNi7CsGgAAABoAAAALAAAAAAAAAAAAAAAAAAAAAABjb250ZW50LnhtbFBLBQYAAAAAAQABADkAAABDAAAAAAA='

# $1=rel_path $2=base64 → 一時indexへOffice blobを登録（実index・WTの正本は触らない）
stage_office_blob() {
  local rel="$1" b64="$2" blob
  reset_test_index
  blob=$(printf '%s' "$b64" | base64 -d | git -C "$REPO_ROOT" hash-object -w --stdin)
  git_tmp update-index --add --cacheinfo "100644,${blob},${rel}"
}

# 44 / E56. index正常ZIP／WTは★★入り有効ZIP → indexだけを検査し exit 0
stage_office_blob "_tmp_pdc_test/e56.pptx" "$OFFICE_CLEAN_ZIP_B64"
printf '%s' "$OFFICE_HARD_ZIP_B64" | base64 -d > "$FIXDIR/e56.pptx"
assert_staged "44. E56 staged Office index正常/WT違反→exit0" 0 \
  "対象 1ファイル" \
  "stagedモードのOffice文書検査は未対応|stagedのOffice文書からXMLを抽出できません|未確定表記が残存：★★|検査対象がありません" \
  default \
  office_tmp

# 45 / E57. index★★入りZIP／WTは正常ZIP → index側本文のhard FAIL
stage_office_blob "_tmp_pdc_test/e57.docx" "$OFFICE_HARD_ZIP_B64"
printf '%s' "$OFFICE_CLEAN_ZIP_B64" | base64 -d > "$FIXDIR/e57.docx"
assert_staged "45. E57 staged Office index違反/WT正常→hard FAIL" 1 \
  "_tmp_pdc_test/e57.docx.*未確定表記が残存：★★" \
  "stagedモードのOffice文書検査は未対応|stagedのOffice文書からXMLを抽出できません|検査対象がありません" \
  default \
  office_tmp

# 46 / E58. index正常ZIP／WT同名ファイル不在 → WTなしでも検査成立 exit 0
stage_office_blob "_tmp_pdc_test/e58.xlsx" "$OFFICE_CLEAN_ZIP_B64"
rm -f "$FIXDIR/e58.xlsx"
assert_staged "46. E58 staged Office WT不在でも検査→exit0" 0 \
  "対象 1ファイル" \
  "stagedモードのOffice文書検査は未対応|stagedのOffice文書からXMLを抽出できません|検査対象がありません|未確定表記が残存" \
  default \
  office_tmp

# 47 / E59. indexが非ZIP blob → 抽出失敗の明示FAIL（診断に実際の非0 rcを含む）
reset_test_index
E59_BLOB=$(printf 'this is not a zip file\n' | git -C "$REPO_ROOT" hash-object -w --stdin)
git_tmp update-index --add --cacheinfo "100644,${E59_BLOB},_tmp_pdc_test/e59.pptx"
rm -f "$FIXDIR/e59.pptx"
assert_staged "47. E59 staged Office 非ZIP→抽出失敗FAIL" 1 \
  "_tmp_pdc_test/e59.pptx.*stagedのOffice文書からXMLを抽出できません（unzip rc=[1-9][0-9]*）" \
  "stagedモードのOffice文書検査は未対応|検査対象がありません|未確定表記が残存：★★" \
  default \
  office_tmp

# 48 / E60. E56〜E59（exit 0経路とexit 1経路の両方）後に一時dir残骸が0件
OFFICE_TMP_LEFT=$(find "$OFFICE_TEST_TMPROOT" -mindepth 1 -maxdepth 1 -name 'pdc-office-*' 2>/dev/null | wc -l | tr -d ' ')
if [ "${OFFICE_TMP_LEFT:-0}" -eq 0 ]; then
  echo "OK: 48. E60 Office一時dir残骸なし（正常・FAIL両経路後）"
  PASS=$((PASS + 1))
else
  echo "NG: 48. E60 Office一時dirが残存（${OFFICE_TMP_LEFT}件）"
  find "$OFFICE_TEST_TMPROOT" -mindepth 1 -maxdepth 1 | sed 's/^/    /'
  FAILN=$((FAILN + 1))
fi

# =============================================================
# staged path transport / NUL-safe 系（E61〜E68）
# 特殊pathはGIT_INDEX_FILEの一時indexだけへ登録する（実index・正本WT不変）。
# core.protectNTFS=false はfixture登録時のみ使用（checker本体では不使用）。
# 特殊path診断の確認はregexに依存せず固定文字列（grep -F）と行完全一致で行う。
# =============================================================

# 特殊path fixture登録：raw pathをNUL終端したindex-infoで一時indexへ登録
stage_special_path_blob() { # $1=raw_path $2=blob_sha
  printf '100644 %s 0\t%s\0' "$2" "$1" \
    | GIT_INDEX_FILE="$TEST_INDEX" git -C "$REPO_ROOT" \
        -c core.quotepath=false -c core.protectNTFS=false \
        update-index -z --index-info
}

# staged実行helper（既定台帳・結果をOUT／CODEへ格納。固定文字列検査用）
run_staged_default() { # $1=optional profile（renames_false|office_tmp）
  local profile="${1:-}"
  local -a run_env=( "GIT_INDEX_FILE=$TEST_INDEX" )
  if [ "$profile" = "renames_false" ]; then
    run_env+=(
      "GIT_CONFIG_COUNT=1"
      "GIT_CONFIG_KEY_0=diff.renames"
      "GIT_CONFIG_VALUE_0=false"
    )
  fi
  if [ "$profile" = "office_tmp" ]; then
    run_env+=( "TMPDIR=$OFFICE_TEST_TMPROOT" )
  fi
  CODE=0
  OUT=$(env -u PRE_DELIVERY_UNCERTAINTY_REGISTRY "${run_env[@]}" \
    bash "$CHECK" --staged 2>&1) || CODE=$?
}

run_staged_explicit() { # $1=明示指定台帳（実ファイル）
  CODE=0
  OUT=$(env "GIT_INDEX_FILE=$TEST_INDEX" \
    PRE_DELIVERY_UNCERTAINTY_REGISTRY="$1" \
    bash "$CHECK" --staged 2>&1) || CODE=$?
}

# rename補助確認（NUL安全版）：--name-status -zをread -d ''で解析しraw値で比較する。
# 既存assert_rename_name_status（E48〜E50用）は変更しない。
assert_rename_z() { # $1=name $2=old_raw_path $3=new_raw_path
  local name="$1" old="$2" new="$3" x
  local -a rec=()
  while IFS= read -r -d '' x; do rec+=("$x"); done < <(GIT_INDEX_FILE="$TEST_INDEX" \
    git -C "$REPO_ROOT" -c core.quotepath=false -c diff.renames=false \
    diff --cached --name-status -z --diff-filter=ACMR --find-renames 2>/dev/null)
  if [ "${#rec[@]}" -eq 3 ] && [[ "${rec[0]}" == R* ]] \
     && [ "${rec[1]}" = "$old" ] && [ "${rec[2]}" = "$new" ]; then
    return 0
  fi
  echo "NG: $name → rename -z補助確認失敗（record数=${#rec[@]}）"
  FAILN=$((FAILN + 1))
  return 1
}

# 特殊path用の共通blob（frozen＋A群soft／frozen＋C群hard）
SPECIAL_MITEI_BLOB=$(printf -- '---\nstatus: frozen\n---\nこの行は未確定\n' | git -C "$REPO_ROOT" hash-object -w --stdin)
SPECIAL_HARD_BLOB=$(printf -- '---\nstatus: frozen\n---\n★★\n' | git -C "$REPO_ROOT" hash-object -w --stdin)

# 50 / E61. 空白を含むstaged path → raw pathのまま検査・未確定FAIL
reset_test_index
stage_special_path_blob '_tmp_pdc_test/sp ace.md' "$SPECIAL_MITEI_BLOB"
assert_staged "50. E61 空白を含むstaged path→未確定FAIL" 1 \
  "\[FAIL\] _tmp_pdc_test/sp ace\.md : 行4 未確定表記が残存：未確定" \
  "検査対象がありません" \
  default

# 51 / E62. 日本語＋空白path → octal・quote表記にならずraw表示で検査
reset_test_index
stage_special_path_blob '_tmp_pdc_test/日本語 メモ.md' "$SPECIAL_MITEI_BLOB"
assert_staged "51. E62 日本語＋空白staged path→未確定FAIL" 1 \
  "\[FAIL\] _tmp_pdc_test/日本語 メモ\.md : 行4 未確定表記が残存：未確定" \
  "検査対象がありません" \
  default

# 52 / E63. 先頭ハイフン＋single quote＋double quote＋backslash複合path（固定文字列検査）
# raw path： -dash'quo"te\slash.md ／ 表示期待： -dash'quo"te\\slash.md
E63_PATH="-dash'quo\"te\\slash.md"
E63_EXPECT="[FAIL] -dash'quo\"te\\\\slash.md : 未確定表記が残存：★★"
reset_test_index
stage_special_path_blob "$E63_PATH" "$SPECIAL_HARD_BLOB"
run_staged_default ""
if [ "$CODE" -eq 1 ] \
  && printf '%s\n' "$OUT" | grep -qF "$E63_EXPECT" \
  && ! printf '%s\n' "$OUT" | grep -qF "Git indexから読み出せません" \
  && ! printf '%s\n' "$OUT" | grep -qF "検査対象がありません"; then
  echo "OK: 52. E63 hyphen・quotes・backslash複合path→hard FAIL"
  PASS=$((PASS + 1))
else
  echo "NG: 52. E63 hyphen・quotes・backslash複合path（code=$CODE）"
  printf '%s\n' "$OUT" | sed 's/^/    /'
  FAILN=$((FAILN + 1))
fi

# 53 / E64. TAB pathとregistry_keyのTAB連結キー衝突（path単位の固定文字列検査）
# 通常path「collision.md」のexact_line「tail<TAB>未確定」登録キーと、
# 特殊path「collision.md<TAB>tail」＋本文「未確定」のキーが旧実装では同一になる。
# 新実装は制御文字pathの台帳照合をスキップし、常に未登録FAILへ倒す。
E64_NORMAL='_tmp_pdc_test/collision.md'
E64_SPECIAL=$'_tmp_pdc_test/collision.md\ttail'
E64_NORMAL_BLOB=$(printf -- '---\nstatus: frozen\n---\ntail\t未確定\n' | git -C "$REPO_ROOT" hash-object -w --stdin)
E64_SPECIAL_BLOB=$(printf -- '---\nstatus: frozen\n---\n未確定\n' | git -C "$REPO_ROOT" hash-object -w --stdin)
reset_test_index
stage_special_path_blob "$E64_NORMAL" "$E64_NORMAL_BLOB"
stage_special_path_blob "$E64_SPECIAL" "$E64_SPECIAL_BLOB"
printf '%s\t1\thistory\t衝突確認用の一時登録\ttail\t未確定\n' "$E64_NORMAL" > "$TMPDIR/e64.tsv"
run_staged_explicit "$TMPDIR/e64.tsv"
E64_WARN_LINE='[WARN] _tmp_pdc_test/collision.md : 行4 意図的な未確定表記（history・台帳登録済み）'
E64_FAIL_LINE='[FAIL] _tmp_pdc_test/collision.md\ttail : 行4 未確定表記が残存：未確定'
E64_BAD_FRAG='collision.md\ttail : 行4 意図的な未確定表記'
if [ "$CODE" -eq 1 ] \
  && printf '%s\n' "$OUT" | grep -qF "$E64_WARN_LINE" \
  && printf '%s\n' "$OUT" | grep -qF "$E64_FAIL_LINE" \
  && ! printf '%s\n' "$OUT" | grep -qF "$E64_BAD_FRAG"; then
  echo "OK: 53. E64 TAB path台帳キー衝突→照合スキップで未登録FAIL"
  PASS=$((PASS + 1))
else
  echo "NG: 53. E64 TAB path台帳キー衝突（code=$CODE）"
  printf '%s\n' "$OUT" | sed 's/^/    /'
  FAILN=$((FAILN + 1))
fi

# 54 / E65. CR＋LFを含むpath → 診断はline\r\npath.mdの1行表示（OUTはE68用に保全）
E65_PATH=$'_tmp_pdc_test/line\r\npath.md'
E65_LINE='[FAIL] _tmp_pdc_test/line\r\npath.md : 未確定表記が残存：★★'
reset_test_index
stage_special_path_blob "$E65_PATH" "$SPECIAL_HARD_BLOB"
run_staged_default ""
E65_OUT="$OUT"
if [ "$CODE" -eq 1 ] \
  && printf '%s\n' "$E65_OUT" | grep -qF "$E65_LINE" \
  && ! printf '%s\n' "$E65_OUT" | grep -qF "検査対象がありません"; then
  echo "OK: 54. E65 CR+LF path→escape表示でhard FAIL"
  PASS=$((PASS + 1))
else
  echo "NG: 54. E65 CR+LF path（code=$CODE）"
  printf '%s\n' "$E65_OUT" | sed 's/^/    /'
  FAILN=$((FAILN + 1))
fi

# 55 / E66. 特殊path（TAB入り）へのrename → -z補助確認＋新raw path本文のhard FAIL
reset_test_index
E66_NEW=$'_tmp_pdc_test/ren\tamed.md'
E66_LINE='[FAIL] _tmp_pdc_test/ren\tamed.md : 未確定表記が残存：★★'
E66_BLOB=$(
  { git -C "$REPO_ROOT" show HEAD:.gitignore; printf '%s\n' '★★'; } \
    | git -C "$REPO_ROOT" hash-object -w --stdin
)
git_tmp update-index --force-remove -- .gitignore
stage_special_path_blob "$E66_NEW" "$E66_BLOB"
assert_rename_z "55. E66 -z補助確認" ".gitignore" "$E66_NEW" || true
run_staged_default "renames_false"
if [ "$CODE" -eq 1 ] \
  && printf '%s\n' "$OUT" | grep -qF "$E66_LINE" \
  && ! printf '%s\n' "$OUT" | grep -qF "検査対象がありません"; then
  echo "OK: 55. E66 rename→特殊path・新path検査でhard FAIL"
  PASS=$((PASS + 1))
else
  echo "NG: 55. E66 rename→特殊path（code=$CODE）"
  printf '%s\n' "$OUT" | sed 's/^/    /'
  FAILN=$((FAILN + 1))
fi

# 56 / E67. 特殊path（TAB入り）のOffice → raw suffixでOffice分岐・index抽出成功
reset_test_index
E67_PATH=$'_tmp_pdc_test/off\tice.pptx'
E67_LINE='[FAIL] _tmp_pdc_test/off\tice.pptx : 未確定表記が残存：★★'
E67_BLOB=$(printf '%s' "$OFFICE_HARD_ZIP_B64" | base64 -d | git -C "$REPO_ROOT" hash-object -w --stdin)
stage_special_path_blob "$E67_PATH" "$E67_BLOB"
run_staged_default "office_tmp"
if [ "$CODE" -eq 1 ] \
  && printf '%s\n' "$OUT" | grep -qF "$E67_LINE" \
  && ! printf '%s\n' "$OUT" | grep -qF "XMLを抽出できません" \
  && ! printf '%s\n' "$OUT" | grep -qF "Git indexから読み出せません" \
  && ! printf '%s\n' "$OUT" | grep -qF "検査対象がありません"; then
  echo "OK: 56. E67 特殊pathのOffice→index抽出でhard FAIL"
  PASS=$((PASS + 1))
else
  echo "NG: 56. E67 特殊pathのOffice（code=$CODE）"
  printf '%s\n' "$OUT" | sed 's/^/    /'
  FAILN=$((FAILN + 1))
fi

# 57 / E68. 診断1行性（E65のOUTを行完全一致・件数で検査。summary行は含めない）
E68_FULL_LINE='[FAIL] _tmp_pdc_test/line\r\npath.md : 未確定表記が残存：★★'
E68_FAIL_COUNT=$(printf '%s\n' "$E65_OUT" | grep -cF '[FAIL]')
E68_EXACT_COUNT=$(printf '%s\n' "$E65_OUT" | grep -cFx "$E68_FULL_LINE")
E68_ORPHAN_COUNT=$(printf '%s\n' "$E65_OUT" | grep -cE '^path\.md')
if [ "${E68_FAIL_COUNT:-0}" -eq 1 ] \
  && [ "${E68_EXACT_COUNT:-0}" -eq 1 ] \
  && [ "${E68_ORPHAN_COUNT:-0}" -eq 0 ]; then
  echo "OK: 57. E68 特殊path診断の1物理行性（[FAIL]=1行・完全一致・孤立行なし）"
  PASS=$((PASS + 1))
else
  echo "NG: 57. E68 診断1行性（FAIL行=${E68_FAIL_COUNT} 完全一致=${E68_EXACT_COUNT} 孤立行=${E68_ORPHAN_COUNT}）"
  printf '%s\n' "$E65_OUT" | sed 's/^/    /'
  FAILN=$((FAILN + 1))
fi

# 58 / 実index非破壊確認：staged系test（E48〜E68含む）前後で実indexが不変
REAL_INDEX_AFTER=$(real_index_hash)
if [ "$REAL_INDEX_BEFORE" = "$REAL_INDEX_AFTER" ]; then
  echo "OK: 58. 実index非破壊（staged系test前後で不変）"
  PASS=$((PASS + 1))
else
  echo "NG: 58. 実indexが変更されています"
  FAILN=$((FAILN + 1))
fi

echo "----------------------------------------"
echo "テスト結果: 合格 ${PASS}件 / 不合格 ${FAILN}件"
if [ $FAILN -gt 0 ]; then
  echo "判定: 回帰あり"
  exit 1
fi
echo "判定: 全ケース合格"
exit 0
