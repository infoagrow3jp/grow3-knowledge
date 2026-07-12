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
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

PASS=0
FAILN=0

run_check() { # $@ = args to pre-delivery-check.sh
  env PRE_DELIVERY_UNCERTAINTY_REGISTRY="${PRE_DELIVERY_UNCERTAINTY_REGISTRY:-$REGISTRY}" \
    bash "$CHECK" "$@"
}

assert_exit0() { # $1=case name, rest=args
  local name="$1"
  shift
  local code=0
  OUT=$(run_check "$@" 2>&1) || code=$?
  if [ "$code" -ne 0 ]; then
    echo "NG: $name → 終了コード${code}（期待：0）"
    echo "$OUT" | sed 's/^/    /'
    FAILN=$((FAILN + 1))
    return
  fi
  echo "OK: $name"
  PASS=$((PASS + 1))
}

assert_exit1() { # $1=case name, rest=args
  local name="$1"
  shift
  local code=0
  OUT=$(run_check "$@" 2>&1) || code=$?
  if [ "$code" -eq 0 ]; then
    echo "NG: $name → 終了コード0（期待：1）"
    echo "$OUT" | sed 's/^/    /'
    FAILN=$((FAILN + 1))
    return
  fi
  echo "OK: $name"
  PASS=$((PASS + 1))
}

# 1. frozen + 台帳登録済み
cat > "$TMPDIR/frozen_registered.md" <<'EOF'
---
status: frozen
---
改訂履歴: v0.1（初版）→ v0.1改訂（Evidence型別項目、source_form統一、occurrence_pattern／corroborated event分離、Hypothesis状態遷移・改訂操作、verification_action、§23未確定16項目統合）→ v0.1確定（Evidence型別管理、解釈の由来管理、Hypothesis状態遷移、因果表現の制約、秘匿性継承、validatorと人間確認の役割分担、未確定16項目のschema段階への送出）
EOF
cp "$REGISTRY" "$TMPDIR/registry1.tsv"
: > "$TMPDIR/registry1_min.tsv"
echo -e "frozen_registered.md\t1\thistory\t改訂履歴: v0.1（初版）→ v0.1改訂（Evidence型別項目、source_form統一、occurrence_pattern／corroborated event分離、Hypothesis状態遷移・改訂操作、verification_action、§23未確定16項目統合）→ v0.1確定（Evidence型別管理、解釈の由来管理、Hypothesis状態遷移、因果表現の制約、秘匿性継承、validatorと人間確認の役割分担、未確定16項目のschema段階への送出）" > "$TMPDIR/registry1_min.tsv"
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/registry1_min.tsv" assert_exit0 "1. frozen+台帳登録済み" "$TMPDIR/frozen_registered.md"

# 2. draft + 未登録
cat > "$TMPDIR/draft_unregistered.md" <<'EOF'
---
status: draft
---
本文に未確定の語が残っている。
EOF
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/registry1_min.tsv" assert_exit0 "2. draft+未登録未確定" "$TMPDIR/draft_unregistered.md"

# 3. コードフェンス内
cat > "$TMPDIR/fence.md" <<'EOF'
---
status: frozen
---
```
未確定の例
```
EOF
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/registry1_min.tsv" assert_exit0 "3. コードフェンス内未確定" "$TMPDIR/fence.md"

# 4. 記録形式節内
cat > "$TMPDIR/template_section.md" <<'EOF'
# サンプル

## 記録形式

- 未確定表記の例示

## 判断ログ

### DEC-001｜確定済み
EOF
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/registry1_min.tsv" assert_exit0 "4. 記録形式節内未確定" "$TMPDIR/template_section.md"

# 5. 実ファイル3件（台帳登録済み意図的未確定）
assert_exit0 "5. 実ファイル3件" \
  "$REPO_ROOT/DECISIONS.md" \
  "$REPO_ROOT/docs/organization-diagnosis_設計メモ_v0.1.md" \
  "$REPO_ROOT/docs/organization-diagnosis_schema設計メモ_v0.1.md"

# 6. frozen + 未登録
cat > "$TMPDIR/frozen_unregistered.md" <<'EOF'
---
status: frozen
---
未登録の未確定表記です。
EOF
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/registry1_min.tsv" assert_exit1 "6. frozen+未登録未確定" "$TMPDIR/frozen_unregistered.md"

# 7. 台帳行を1文字変更
cat > "$TMPDIR/modified_line.md" <<'EOF'
---
status: frozen
---
改訂履歴: v0.1（初版）→ v0.1改訂（Evidence型別項目、source_form統一、occurrence_pattern／corroborated event分離、Hypothesis状態遷移・改訂操作、verification_action、§23未確定17項目統合）→ v0.1確定（Evidence型別管理、解釈の由来管理、Hypothesis状態遷移、因果表現の制約、秘匿性継承、validatorと人間確認の役割分担、未確定16項目のschema段階への送出）
EOF
cat > "$TMPDIR/registry7.tsv" <<'EOF'
modified_line.md	1	history	改訂履歴: v0.1（初版）→ v0.1改訂（Evidence型別項目、source_form統一、occurrence_pattern／corroborated event分離、Hypothesis状態遷移・改訂操作、verification_action、§23未確定16項目統合）→ v0.1確定（Evidence型別管理、解釈の由来管理、Hypothesis状態遷移、因果表現の制約、秘匿性継承、validatorと人間確認の役割分担、未確定16項目のschema段階への送出）
EOF
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/registry7.tsv" assert_exit1 "7. 台帳行1文字変更" "$TMPDIR/modified_line.md"

# 8. expected_count超過
cat > "$TMPDIR/duplicate.md" <<'EOF'
---
status: frozen
---
| status | 状態（語彙・遷移は§23未確定） |
| status | 状態（語彙・遷移は§23未確定） |
| status | 状態（語彙・遷移は§23未確定） |
EOF
cp "$REGISTRY" "$TMPDIR/registry8.tsv"
echo -e "duplicate.md\t2\tdeferred_v0.2\t| status | 状態（語彙・遷移は§23未確定） |" >> "$TMPDIR/registry8.tsv"
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/registry8.tsv" assert_exit1 "8. expected_count超過" "$TMPDIR/duplicate.md"

# 9. TODO in frozen
cat > "$TMPDIR/todo_frozen.md" <<'EOF'
---
status: frozen
---
TODO: 残タスク
EOF
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/registry1_min.tsv" assert_exit1 "9. frozen+TODO" "$TMPDIR/todo_frozen.md"

# 10. ★★ in draft
cat > "$TMPDIR/stars_draft.md" <<'EOF'
---
status: draft
---
★★要修正
EOF
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/registry1_min.tsv" assert_exit1 "10. draft+★★" "$TMPDIR/stars_draft.md"

# 11. 不正classification
cat > "$TMPDIR/bad_class.tsv" <<'EOF'
# bad
bad.md	1	invalid_class	未確定
EOF
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/bad_class.tsv" assert_exit1 "11. 不正classification" "$TMPDIR/frozen_unregistered.md"

# 12. expected_count=0
cat > "$TMPDIR/bad_count.tsv" <<'EOF'
bad.md	0	history	未確定
EOF
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/bad_count.tsv" assert_exit1 "12. expected_count=0" "$TMPDIR/frozen_unregistered.md"

# 13. 重複登録
cat > "$TMPDIR/dup_registry.tsv" <<'EOF'
dup.md	1	history	未確定行
dup.md	1	history	未確定行
EOF
PRE_DELIVERY_UNCERTAINTY_REGISTRY="$TMPDIR/dup_registry.tsv" assert_exit1 "13. 台帳重複登録" "$TMPDIR/frozen_unregistered.md"

echo "----------------------------------------"
echo "テスト結果: 合格 ${PASS}件 / 不合格 ${FAILN}件"
if [ $FAILN -gt 0 ]; then
  echo "判定: 回帰あり"
  exit 1
fi
echo "判定: 全ケース合格"
exit 0
