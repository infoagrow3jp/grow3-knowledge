#!/usr/bin/env bash
# =============================================================
# Grow3 Stopフック用ラッパー
# 役割：セッション中に変更されたファイルへ検品を実行し、
#       FAIL時はexit 2でClaudeに差し戻す（自動差し戻しは1回まで）。
# ループ防止：stop_hook_active=true（既にフックによる再作業中）で
#       なおFAILが残る場合は、警告のみ出して停止を許可する。
#       ハードゲートはpre-commitが担う（そこでは必ず遮断される）。
# =============================================================
INPUT=$(cat)
# jq非依存でstop_hook_activeを判定
if echo "$INPUT" | grep -q '"stop_hook_active"[[:space:]]*:[[:space:]]*true'; then
  ACTIVE=true
else
  ACTIVE=false
fi

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
# 変更ファイル＋未追跡の新規ファイル（新規生成した成果物を漏らさない）
CHANGED=$(
  { git -c core.quotepath=false diff --name-only HEAD 2>/dev/null
    git -c core.quotepath=false ls-files --others --exclude-standard 2>/dev/null; } | sort -u
)
[ -z "$CHANGED" ] && exit 0

# shellcheck disable=SC2086
bash "$REPO_ROOT/scripts/pre-delivery-check.sh" $CHANGED
STATUS=$?

if [ $STATUS -ne 0 ]; then
  if [ "$ACTIVE" = "true" ]; then
    echo "検品FAILが未解消ですが、ループ防止のため停止を許可します。" >&2
    echo "未解消項目はコミット時にpre-commitで再度遮断されます。" >&2
    exit 0
  fi
  echo "出荷前検品でFAILが検出されました。上記のFAIL項目を解消してください。" >&2
  exit 2
fi
exit 0
