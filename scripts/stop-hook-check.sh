#!/usr/bin/env bash
# =============================================================
# Grow3 Stopフック用ラッパー
# 役割：セッション中に変更されたファイルへ検品を実行し、
#       FAIL時はexit 2でClaudeに差し戻す（自動差し戻しは1回まで）。
# ループ防止：stop_hook_active=true（既にフックによる再作業中）で
#       なおFAILが残る場合は、警告のみ出して停止を許可する。
#       ハードゲートはpre-commitが担う（そこでは必ず遮断される）。
# path引渡し：変更pathはNUL区切りでraw配列へ収集し、quoted配列展開で
#       checkerへ渡す（空白・引用符・glob文字・先頭ハイフンで壊さない）。
#       Stopはworking tree検査、pre-commitはindex検査の二層構造を維持する。
# =============================================================
INPUT=$(cat)
# jq非依存でstop_hook_activeを判定
if echo "$INPUT" | grep -q '"stop_hook_active"[[:space:]]*:[[:space:]]*true'; then
  ACTIVE=true
else
  ACTIVE=false
fi

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
cd "$REPO_ROOT" 2>/dev/null || exit 0

# 変更ファイル＋未追跡の新規ファイル（新規生成した成果物を漏らさない）
# NUL区切りでraw pathを配列へ収集する（改行区切り・unquoted展開に依存しない）
CHANGED=()
while IFS= read -r -d '' f; do
  # 先頭ハイフンのraw pathだけ ./ を前置し、option解釈を防ぐ（subdir配下は不要）
  case "$f" in
    -*) f="./$f" ;;
  esac
  CHANGED+=("$f")
done < <(
  {
    git -c core.quotepath=false diff --name-only -z HEAD 2>/dev/null
    git -c core.quotepath=false ls-files --others --exclude-standard -z 2>/dev/null
  } | LC_ALL=C sort -zu
)

# 設計の関門（2026-11-15追加）：登録済みの設計作業フォルダ（Dropbox含む）の
# 着手票を検査する。リポジトリに変更が無くても実行する（Dropbox直書きの仕事を拾うため）。
# pythonが無い環境では警告のみ（道具の不在で全セッションを止めない。未対応経路として扱う）。
GATE_OUTPUT=""
GATE_STATUS=0
if [ -f "$REPO_ROOT/scripts/design_gate_check.py" ]; then
  if command -v python >/dev/null 2>&1; then
    GATE_OUTPUT=$(python "$REPO_ROOT/scripts/design_gate_check.py" --hook 2>&1)
    GATE_STATUS=$?
  elif command -v py >/dev/null 2>&1; then
    GATE_OUTPUT=$(py -3 "$REPO_ROOT/scripts/design_gate_check.py" --hook 2>&1)
    GATE_STATUS=$?
  else
    echo "設計の関門：pythonが見つからないため着手票の検査を実行できませんでした。" >&2
  fi
fi
if [ "$GATE_STATUS" -ne 0 ]; then
  [ -n "$GATE_OUTPUT" ] && printf '%s\n' "$GATE_OUTPUT"
  [ -n "$GATE_OUTPUT" ] && printf '%s\n' "$GATE_OUTPUT" >&2
  if [ "$ACTIVE" = "true" ]; then
    echo "設計の関門のFAILが未解消ですが、ループ防止のため停止を許可します。" >&2
  else
    echo "設計の関門：着手票のないまま設計の仕事が進んでいます。着手票を書いてください。" >&2
    exit 2
  fi
fi

[ "${#CHANGED[@]}" -eq 0 ] && exit 0

# checkerの診断（stdout＋stderr）をまとめて取得し、実際のexit codeを保持する
CHECK_OUTPUT=$(bash "$REPO_ROOT/scripts/pre-delivery-check.sh" "${CHANGED[@]}" 2>&1)
STATUS=$?

[ -n "$CHECK_OUTPUT" ] && printf '%s\n' "$CHECK_OUTPUT"

if [ "$STATUS" -ne 0 ]; then
  # FAIL明細をstderrにも再出力し、差し戻しの実効性を上げる
  [ -n "$CHECK_OUTPUT" ] && printf '%s\n' "$CHECK_OUTPUT" >&2
  if [ "$ACTIVE" = "true" ]; then
    echo "検品FAILが未解消ですが、ループ防止のため停止を許可します。" >&2
    echo "未解消項目はコミット時にpre-commitで再度遮断されます。" >&2
    exit 0
  fi
  echo "出荷前検品でFAILが検出されました。上記のFAIL項目を解消してください。" >&2
  exit 2
fi
exit 0
