#!/bin/bash
# =============================================================
# Grow3 コミットヘルパー（Git Bash 用）
# 使い方:
#   bash scripts/commit-helper.sh "コミットメッセージ" <ファイル>...
# 例:
#   bash scripts/commit-helper.sh "出荷前検品の除外を追加" scripts/pre-delivery-check.sh
# 動作:
#   指定ファイルのみ git add → git commit → git log -1
#   （--no-verify は付けない。pre-commit 検品を通す）
# =============================================================
set -euo pipefail

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "エラー: git リポジトリ内で実行してください" >&2
  exit 1
}
cd "$REPO_ROOT"

if [ $# -lt 2 ]; then
  echo "使い方: bash scripts/commit-helper.sh \"コミットメッセージ\" <ファイル>..." >&2
  exit 1
fi

MSG="$1"
shift

if [ -z "$MSG" ]; then
  echo "エラー: コミットメッセージが空です" >&2
  exit 1
fi

FILES=("$@")
for f in "${FILES[@]}"; do
  if [ ! -e "$f" ]; then
    # 削除済みの追跡ファイルは add 可。未追跡かつ不存在はエラー。
    if ! git ls-files --error-unmatch -- "$f" >/dev/null 2>&1; then
      echo "エラー: ファイルが存在しません: $f" >&2
      exit 1
    fi
  fi
done

git add -- "${FILES[@]}"
git commit -m "$MSG"
git log -1 --oneline
