#!/bin/bash
# =============================================================
# pre-delivery-check.sh の回帰テスト（テンプレート／例示ブロック除外の検証）
# 使い方：bash scripts/test-pre-delivery-check.sh
# 終了コード：0 = 全ケース合格 / 1 = いずれか不合格
#
# 目的：2026-07-12にDECISIONS.mdの「## 記録形式」節にあるテンプレート例示
# （### DEC-XXX｜判断タイトル）が、本文の未確定表記と誤って同一視されFAILに
# なった問題を修正した際の回帰防止テスト。以下の両方向を検証する：
#   1. テンプレート／例示ブロック内のプレースホルダはFAILしない（偽陽性の解消）
#   2. 本文（テンプレート範囲外）に実際に残った未確定表記はFAILする（見逃し防止）
# =============================================================
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHECK="$SCRIPT_DIR/pre-delivery-check.sh"
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

PASS=0
FAILN=0

assert_no_fail() { # $1=fixture file $2=case name
  OUT=$(bash "$CHECK" "$1" 2>&1)
  if echo "$OUT" | grep -qE "^\[FAIL\]"; then
    echo "NG: $2 → FAILが検出された（期待：FAILなし）"
    echo "$OUT" | sed 's/^/    /'
    FAILN=$((FAILN+1))
  else
    echo "OK: $2"
    PASS=$((PASS+1))
  fi
}

assert_fail() { # $1=fixture file $2=case name
  OUT=$(bash "$CHECK" "$1" 2>&1)
  if echo "$OUT" | grep -qE "^\[FAIL\]"; then
    echo "OK: $2"
    PASS=$((PASS+1))
  else
    echo "NG: $2 → FAILが検出されなかった（期待：FAILあり＝見逃し）"
    echo "$OUT" | sed 's/^/    /'
    FAILN=$((FAILN+1))
  fi
}

# ---- ケース1：記録形式節のテンプレート例示はFAILしない ----
cat > "$TMPDIR/case1_template.md" <<'EOF'
# 判断ログ（サンプル）

## 記録形式

### DEC-XXX｜判断タイトル
- 日付：
- 状態：確定／保留／廃止

## 判断ログ

### DEC-001｜サンプル判断
- 日付：2026-01-01
- 状態：確定
- 決定：サンプル
EOF
assert_no_fail "$TMPDIR/case1_template.md" "記録形式節内のDEC-XXXはFAILしない"

# ---- ケース2：記録形式節の外に残った未確定表記（DEC-XXX）はFAILする ----
cat > "$TMPDIR/case2_residual.md" <<'EOF'
# 判断ログ（サンプル）

## 記録形式

### DEC-XXX｜判断タイトル
- 日付：

## 判断ログ

### DEC-XXX｜まだ確定していない項目
- 日付：2026-01-01
- 状態：保留
EOF
assert_fail "$TMPDIR/case2_residual.md" "判断ログ節に残ったDEC-XXXはFAILする（見逃し防止）"

# ---- ケース3：コードフェンス内のTODO/XXXはFAILしない ----
cat > "$TMPDIR/case3_fence.md" <<'EOF'
# サンプル文書

以下はコード例です。

```
TODO: この部分は後で直す XXX
```

本文はここまで。
EOF
assert_no_fail "$TMPDIR/case3_fence.md" "コードフェンス内のTODO/XXXはFAILしない"

# ---- ケース4：コードフェンス外に実際に残ったTODOはFAILする ----
cat > "$TMPDIR/case4_real_todo.md" <<'EOF'
# サンプル文書

この項目はTODOのまま残っている。
EOF
assert_fail "$TMPDIR/case4_real_todo.md" "コードフェンス外の実際のTODOはFAILする（見逃し防止）"

echo "----------------------------------------"
echo "テスト結果: 合格 ${PASS}件 / 不合格 ${FAILN}件"
if [ $FAILN -gt 0 ]; then
  echo "判定: 回帰あり"
  exit 1
fi
echo "判定: 全ケース合格"
exit 0
