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
trap 'rm -rf "$TMPDIR" "$FIXDIR"' EXIT

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

# 3. コードフェンス内（現行は除外のまま）
cat > "$FIXDIR/fence.md" <<'EOF'
---
status: frozen
---
```
未確定の例
```
EOF
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/registry1_min.tsv" assert_exit0 "3. コードフェンス内未確定" "$FIXDIR/fence.md"

# 4. 記録形式節内（現行は全ファイル除外のまま）
cat > "$FIXDIR/template_section.md" <<'EOF'
# サンプル

## 記録形式

- 未確定表記の例示

## 判断ログ

### DEC-001｜確定済み
EOF
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/registry1_min.tsv" assert_exit0 "4. 記録形式節内未確定" "$FIXDIR/template_section.md"

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

echo "----------------------------------------"
echo "テスト結果: 合格 ${PASS}件 / 不合格 ${FAILN}件"
if [ $FAILN -gt 0 ]; then
  echo "判定: 回帰あり"
  exit 1
fi
echo "判定: 全ケース合格"
exit 0
