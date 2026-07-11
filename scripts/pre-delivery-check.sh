#!/bin/bash
# =============================================================
# Grow3 出荷前検品スクリプト（機械判定専用）
# 使い方:
#   bash scripts/pre-delivery-check.sh <ファイルまたはディレクトリ>...
#   bash scripts/pre-delivery-check.sh --staged   # git addされたファイルを検査
# 終了コード: 0 = 合格（WARNのみ含む） / 1 = FAILあり（出荷不可）
# 判定できるのは文字列レベルのみ。CPマスター準拠・視覚的なブランド適合は
# compliance-checker（裁量判定）で確認すること。
#
# 未確定表記（【要確認】/TODO/仮置き/未確定）の扱い:
#   frontmatter の status: draft|reviewed → WARN
#   status: final または frontmatterなし → FAIL
# 公開禁止事例・★★・XXX は status に関係なく常に FAIL。
# =============================================================
set -u
FAIL=0
WARN=0

# ---- 自己言及除外（検品の仕組み自身が検品に引っかかるのを防ぐ） ----
# scripts/・.claude/・.githooks/ 配下、および導入手順.md は対象外。
is_excluded() {
  case "$1" in
    scripts/*|*/scripts/*|.claude/*|*/.claude/*|.githooks/*|*/.githooks/*|導入手順.md|*/導入手順.md)
      return 0 ;;
    *)
      return 1 ;;
  esac
}

# ---- 検査対象の収集 ----
TARGETS=()
if [ "${1:-}" = "--staged" ]; then
  while IFS= read -r f; do
    [ -f "$f" ] && ! is_excluded "$f" && TARGETS+=("$f")
  done < <(git -c core.quotepath=false diff --cached --name-only --diff-filter=ACM 2>/dev/null)
else
  for a in "$@"; do
    if [ -d "$a" ]; then
      while IFS= read -r f; do
        ! is_excluded "$f" && TARGETS+=("$f")
      done < <(find "$a" -type f \( -name "*.md" -o -name "*.html" -o -name "*.htm" \
            -o -name "*.txt" -o -name "*.pptx" -o -name "*.docx" -o -name "*.xlsx" \
            -o -name "*.css" -o -name "*.js" -o -name "*.svg" \) \
            ! -path "*/node_modules/*" ! -path "*/.git/*")
    elif [ -f "$a" ]; then
      ! is_excluded "$a" && TARGETS+=("$a")
    fi
  done
fi
[ ${#TARGETS[@]} -eq 0 ] && { echo "検査対象がありません"; exit 0; }

# ---- ファイル内容の取得（OOXMLはzip展開してテキスト化） ----
get_text() {
  case "$1" in
    *.pptx|*.docx|*.xlsx)
      unzip -p "$1" "*.xml" 2>/dev/null | sed -e 's/<[^>]*>/ /g' ;;
    *) cat "$1" ;;
  esac
}

# 先頭YAML frontmatterの status 値を返す（なければ空）。
get_doc_status() {
  local first
  first=$(head -n 1 "$1" 2>/dev/null | tr -d '\r')
  [ "$first" = "---" ] || { echo ""; return; }
  awk '
    BEGIN { in_fm=0 }
    {
      line=$0
      sub(/\r$/, "", line)
    }
    NR==1 && line=="---" { in_fm=1; next }
    in_fm && line=="---" { exit }
    in_fm && line ~ /^status:[[:space:]]*/ {
      sub(/^status:[[:space:]]*/, "", line)
      sub(/[[:space:]]+$/, "", line)
      print line
      exit
    }
  ' "$1"
}

report() { # $1=LEVEL $2=file $3=message
  echo "[$1] $2 : $3"
  [ "$1" = "FAIL" ] && FAIL=$((FAIL+1)) || WARN=$((WARN+1))
}

BRAND_COLORS="0F3D96|EEF3FA|1F2937|E5E7EB|FFFFFF|000000|FFF|000"

for f in "${TARGETS[@]}"; do
  TEXT=$(get_text "$f")
  DOC_STATUS=$(get_doc_status "$f")
  if [ "$DOC_STATUS" = "draft" ] || [ "$DOC_STATUS" = "reviewed" ]; then
    UNCERTAIN_LEVEL=WARN
  else
    UNCERTAIN_LEVEL=FAIL
  fi

  # ===== FAIL（出荷不可） =====
  # 1) 公開禁止事例：介護施設の離職率改善事例（statusに関係なく常にFAIL）
  #    「介護」×「離職率」は近接共起（前後80行以内）のみFAIL。
  #    数値パターン（30%台→5%台）はファイル全体でFAILを維持。
  if echo "$TEXT" | grep -Eq "30％?台.{0,20}5％?台|30%台.{0,20}5%台"; then
    report FAIL "$f" "公開禁止事例の疑い：離職率30%台→5%台の数値パターン"
  fi
  NEAR_HIT=$(printf '%s\n' "$TEXT" | awk '
    {
      if (index($0, "介護") > 0) k[NR] = 1
      if (index($0, "離職率") > 0) r[NR] = 1
    }
    END {
      for (a in k) {
        for (b in r) {
          d = (a > b) ? a - b : b - a
          if (d <= 80) { print a "/" b; exit }
        }
      }
    }
  ')
  if [ -n "$NEAR_HIT" ]; then
    report FAIL "$f" "公開禁止事例の疑い：「介護」と「離職率」が近接共起（前後80行以内・行${NEAR_HIT}）"
  fi
  # 2) 未確定表記の残存
  #    draft/reviewed → WARN / final・frontmatterなし → FAIL
  for kw in "【要確認】" "TODO" "仮置き" "未確定"; do
    if echo "$TEXT" | grep -qF "$kw"; then
      report "$UNCERTAIN_LEVEL" "$f" "未確定表記が残存：${kw}"
    fi
  done
  # ★★ / XXX は status に関係なく FAIL
  for kw in "★★" "XXX"; do
    if echo "$TEXT" | grep -qF "$kw"; then
      report FAIL "$f" "未確定表記が残存：${kw}"
    fi
  done

  # ===== WARN（要レビュー） =====
  # 3) ブランド外カラーコード（html/css/js/svgのみ）
  case "$f" in
    *.html|*.htm|*.css|*.js|*.svg)
      OFFBRAND=$(grep -oiE "#[0-9a-f]{6}|#[0-9a-f]{3}\b" "$f" 2>/dev/null \
        | tr 'a-f' 'A-F' | sed 's/#//' | sort -u \
        | grep -vE "^(${BRAND_COLORS})$" | head -5)
      if [ -n "$OFFBRAND" ]; then
        report WARN "$f" "ブランド外カラーコード：$(echo $OFFBRAND | tr '\n' ' ')（診断ツール4象限色なら対象外・要目視）"
      fi ;;
  esac
  # 4) 改行直前の読点（md/html/txtのみ）
  case "$f" in
    *.md|*.html|*.htm|*.txt)
      LINES=$(grep -nE "、[[:space:]]*$" "$f" 2>/dev/null | cut -d: -f1 | head -10 | tr '\n' ',')
      [ -n "$LINES" ] && report WARN "$f" "改行直前の読点：行 ${LINES%,}"
      # 5) AI語候補（禁止語ではない・要レビュー）
      for w in "寄り添" "最大化" "変容を促" "本質的な価値" "唯一無二"; do
        if grep -qF "$w" "$f" 2>/dev/null; then
          report WARN "$f" "AI語候補：「${w}」（文脈上必要なら問題なし）"
        fi
      done ;;
  esac
  # 6) HTML構造タグの開閉個数不一致（補助検査・WARNのみ）
  #    個数一致でも入れ子誤りは保証できず、コメント内文字列で誤検出しうる。
  case "$f" in
    *.html|*.htm)
      for tag in div section article main; do
        open_n=$(grep -oiE "<${tag}([[:space:]/>])" "$f" 2>/dev/null | wc -l | tr -d ' ')
        close_n=$(grep -oiE "</${tag}[[:space:]]*>" "$f" 2>/dev/null | wc -l | tr -d ' ')
        if [ "${open_n:-0}" != "${close_n:-0}" ]; then
          report WARN "$f" "HTMLタグ個数不一致：<${tag}> 開${open_n} / 閉${close_n}（入れ子誤りは未検出・コメント内誤検知ありうる）"
        fi
      done ;;
  esac
done

echo "----------------------------------------"
echo "検品結果: FAIL ${FAIL}件 / WARN ${WARN}件（対象 ${#TARGETS[@]}ファイル）"
if [ $FAIL -gt 0 ]; then
  echo "判定: 出荷不可（FAILをすべて解消してください）"
  exit 1
fi
echo "判定: 合格（WARNは要レビュー）"
exit 0
