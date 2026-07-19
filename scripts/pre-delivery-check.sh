#!/bin/bash
# =============================================================
# Grow3 出荷前検品スクリプト（機械判定専用）
# 使い方:
#   bash scripts/pre-delivery-check.sh <ファイルまたはディレクトリ>...
#   bash scripts/pre-delivery-check.sh --staged   # git addされたファイルを検査
# 終了コード: 0 = 合格（WARNのみ含む） / 1 = FAILあり（出荷不可）
# =============================================================
set -u
FAIL=0
WARN=0

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 明示指定台帳（PRE_DELIVERY_UNCERTAINTY_REGISTRY）は指定パスの実ファイルを読む（index非要求）
REGISTRY_EXPLICIT=0
[ -n "${PRE_DELIVERY_UNCERTAINTY_REGISTRY:-}" ] && REGISTRY_EXPLICIT=1
REGISTRY="${PRE_DELIVERY_UNCERTAINTY_REGISTRY:-$SCRIPT_DIR/pre-delivery-intentional-uncertainty.tsv}"

# --staged: 本文・frontmatter status・既定台帳をGit indexの同一snapshotから読む
STAGED_MODE=0
[ "${1:-}" = "--staged" ] && STAGED_MODE=1

index_has_path() {
  git -C "$REPO_ROOT" cat-file -e ":$1" 2>/dev/null
}

read_index_content() {
  git -C "$REPO_ROOT" -c core.quotepath=false show ":$1" 2>/dev/null
}
VALID_CLASSIFICATIONS="history|data_state|deferred_v0.2|implementation_detail|meta_check"

declare -A REG_EXPECTED
declare -A REG_CLASS
declare -A REG_FOUND

# ---- 自己言及除外 ----
is_excluded() {
  case "$1" in
    scripts/*|*/scripts/*|.claude/*|*/.claude/*|.githooks/*|*/.githooks/*|導入手順.md|*/導入手順.md)
      return 0 ;;
    *)
      return 1 ;;
  esac
}

normalize_rel_path() {
  local p="$1" rel root_abs abs
  if git -C "$REPO_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    rel=$(git -C "$REPO_ROOT" -c core.quotepath=false ls-files --full-name -- "$p" 2>/dev/null | head -1)
    if [ -n "$rel" ]; then
      echo "$rel"
      return
    fi
  fi
  abs=$(cd "$(dirname "$p")" 2>/dev/null && pwd)
  abs="${abs//\\//}/$(basename "$p")"
  root_abs=$(cd "$REPO_ROOT" 2>/dev/null && pwd)
  root_abs="${root_abs//\\//}"
  case "$abs" in
    "$root_abs"/*)
      echo "${abs#"$root_abs"/}"
      return
      ;;
  esac
  basename "$p"
}

report() { # $1=LEVEL $2=file $3=message
  echo "[$1] $2 : $3"
  [ "$1" = "FAIL" ] && FAIL=$((FAIL+1)) || WARN=$((WARN+1))
}

registry_key() {
  printf '%s\t%s' "$1" "$2"
}

load_registry() {
  local line_no=0 registry_fail=0
  # 既定台帳のみstagedでindex読取。明示指定台帳は指定パスの実ファイルを読む
  if [ "$STAGED_MODE" -eq 1 ] && [ "$REGISTRY_EXPLICIT" -eq 0 ]; then
    local reg_rel
    reg_rel=$(normalize_rel_path "$REGISTRY")
    if ! index_has_path "$reg_rel"; then
      report FAIL "$REGISTRY" "台帳ファイルがGit indexに存在しません"
      return 1
    fi
    exec 3< <(read_index_content "$reg_rel")
  else
    [ -f "$REGISTRY" ] || { report FAIL "$REGISTRY" "台帳ファイルが存在しません"; return 1; }
    exec 3< "$REGISTRY"
  fi

  while IFS= read -r raw_line <&3 || [ -n "$raw_line" ]; do
    line_no=$((line_no + 1))
    # コメント行・空行（空白のみ）はスキップ
    [[ "$raw_line" =~ ^[[:space:]]*# ]] && continue
    [[ -z "${raw_line//[[:space:]]/}" ]] && continue

    local tab_count rel_path expected class reason exact_line rest
    tab_count=$(printf '%s' "$raw_line" | awk -F '\t' '{print NF-1}')
    if [ "${tab_count:-0}" -lt 4 ]; then
      report FAIL "$REGISTRY" "台帳エラー：列不足（行${line_no}）"
      registry_fail=1
      continue
    fi

    # 最初の4個のTABで5論理列へ分解（exact_lineは4個目以降の全体）
    rel_path="${raw_line%%$'\t'*}"
    rest="${raw_line#*$'\t'}"
    expected="${rest%%$'\t'*}"
    rest="${rest#*$'\t'}"
    class="${rest%%$'\t'*}"
    rest="${rest#*$'\t'}"
    reason="${rest%%$'\t'*}"
    exact_line="${rest#*$'\t'}"
    rel_path="${rel_path%%$'\r'}"
    expected="${expected%%$'\r'}"
    class="${class%%$'\r'}"
    reason="${reason%%$'\r'}"
    exact_line="${exact_line%%$'\r'}"

    if [ -z "$rel_path" ]; then
      report FAIL "$REGISTRY" "台帳エラー：pathが空です（行${line_no}）"
      registry_fail=1
      continue
    fi
    if [ -z "$expected" ]; then
      report FAIL "$REGISTRY" "台帳エラー：expected_countが空です（行${line_no}）"
      registry_fail=1
      continue
    fi
    if ! [[ "$expected" =~ ^[0-9]+$ ]] || [ "$expected" -le 0 ]; then
      report FAIL "$REGISTRY" "台帳エラー：expected_countが不正（行${line_no}：${expected}）"
      registry_fail=1
      continue
    fi
    if [ -z "$class" ]; then
      report FAIL "$REGISTRY" "台帳エラー：classificationが空です（行${line_no}）"
      registry_fail=1
      continue
    fi
    if ! [[ "$class" =~ ^(${VALID_CLASSIFICATIONS})$ ]]; then
      report FAIL "$REGISTRY" "台帳エラー：classificationが不正（行${line_no}：${class}）"
      registry_fail=1
      continue
    fi
    if [[ "$reason" =~ ^[[:space:]]*$ ]]; then
      report FAIL "$REGISTRY" "台帳エラー：reasonが空です（行${line_no}）"
      registry_fail=1
      continue
    fi
    if [ -z "$exact_line" ]; then
      report FAIL "$REGISTRY" "台帳エラー：exact_lineが空です（行${line_no}）"
      registry_fail=1
      continue
    fi
    if [[ "$exact_line" == *"★★"* ]] || [[ "$exact_line" == *"XXX"* ]]; then
      report FAIL "$REGISTRY" "台帳エラー：exact_lineにhard検出語が含まれます（行${line_no}）"
      registry_fail=1
      continue
    fi

    local key
    key=$(registry_key "$rel_path" "$exact_line")
    if [ -n "${REG_EXPECTED[$key]+x}" ]; then
      report FAIL "$REGISTRY" "台帳エラー：重複登録（${rel_path}）"
      registry_fail=1
      continue
    fi

    REG_EXPECTED[$key]=$expected
    REG_CLASS[$key]=$class
    REG_FOUND[$key]=0
  done
  exec 3<&-

  [ "$registry_fail" -eq 1 ] && return 1
  return 0
}

# 「記録形式」節除外はリポジトリ直下の正本 DECISIONS.md のみ。
# fenced code block は原則走査（区切り行自体はスキップ）。
apply_record_form_template_filter() {
  case "$(normalize_rel_path "$1")" in
    DECISIONS.md) echo 1 ;;
    *) echo 0 ;;
  esac
}

# 記録形式節（DECISIONSのみ）を除いた行のうち「未確定」を含む行を NR<TAB>line で出力
# fence内も検出対象（検出・exact照合・件数計数と同一フィルタ）
# stdinから本文を読む（pathはフィルタ判定にのみ使用。stagedはindex版、手動はworking tree版）
scan_mitei_prose_lines() {
  local file="$1" apply_template
  apply_template=$(apply_record_form_template_filter "$file")
  awk -v apply_template="$apply_template" '
    BEGIN { in_template = 0 }
    {
      line = $0
      sub(/\r$/, "", line)
      if (line ~ /^```/) next
      if (apply_template && line ~ /^## 記録形式[[:space:]]*$/) { in_template = 1; next }
      if (apply_template && in_template && line ~ /^## /) { in_template = 0 }
      if (apply_template && in_template) next
      if (index(line, "未確定") > 0) print NR "\t" line
    }
  '
}

# B/C群用：fenceは残し、記録形式節のみ DECISIONS.md で除外
strip_template_and_fences() {
  local apply_template="${1:-0}"
  awk -v apply_template="$apply_template" '
    BEGIN { in_template = 0 }
    {
      line = $0
      sub(/\r$/, "", line)
      if (apply_template && line ~ /^## 記録形式[[:space:]]*$/) { in_template = 1; next }
      if (apply_template && in_template && line ~ /^## /) { in_template = 0 }
      if (apply_template && in_template) next
      print line
    }
  '
}

# stdinから本文を読む（pathはフィルタ判定にのみ使用）
count_prose_exact_line() {
  local file="$1" exact="$2" apply_template
  apply_template=$(apply_record_form_template_filter "$file")
  awk -v target="$exact" -v apply_template="$apply_template" '
    BEGIN { in_template = 0; n = 0 }
    {
      line = $0
      sub(/\r$/, "", line)
      if (line ~ /^```/) next
      if (apply_template && line ~ /^## 記録形式[[:space:]]*$/) { in_template = 1; next }
      if (apply_template && in_template && line ~ /^## /) { in_template = 0 }
      if (apply_template && in_template) next
      if (line == target) n++
    }
    END { print n }
  '
}

check_mitei_lines() {
  local f="$1" rel="$2" uncertain_level="$3"
  declare -A line_hits=()

  while IFS=$'\t' read -r lineno content || [ -n "$lineno" ]; do
    [ -z "$lineno" ] && continue
    line_hits["$content"]=$((${line_hits["$content"]:-0} + 1))
    local key hit_count reg_expected reg_class
    key=$(registry_key "$rel" "$content")
    hit_count=${line_hits["$content"]}

    if [ -n "${REG_EXPECTED[$key]+x}" ]; then
      reg_expected=${REG_EXPECTED[$key]}
      reg_class=${REG_CLASS[$key]}
      REG_FOUND[$key]=$((${REG_FOUND[$key]:-0} + 1))
      if [ "$hit_count" -le "$reg_expected" ]; then
        report WARN "$f" "行${lineno} 意図的な未確定表記（${reg_class}・台帳登録済み）"
      else
        report FAIL "$f" "行${lineno} 未確定表記が台帳許可件数を超過（${hit_count}/${reg_expected}）"
      fi
    else
      report "$uncertain_level" "$f" "行${lineno} 未確定表記が残存：未確定"
    fi
  done < <(printf '%s\n' "$TEXT" | scan_mitei_prose_lines "$f")
}

check_stale_registry_entries() {
  local key rel exact found expected abs
  for key in "${!REG_EXPECTED[@]}"; do
    rel="${key%%$'\t'*}"
    exact="${key#*$'\t'}"
    expected="${REG_EXPECTED[$key]}"
    if [ "$STAGED_MODE" -eq 1 ]; then
      if ! index_has_path "$rel"; then
        report FAIL "$REGISTRY" "台帳エラー：登録先ファイルが存在しません（${rel}）"
        continue
      fi
      found=$(read_index_content "$rel" | count_prose_exact_line "$rel" "$exact")
    else
      abs="$REPO_ROOT/$rel"
      if [ ! -f "$abs" ]; then
        report FAIL "$REGISTRY" "台帳エラー：登録先ファイルが存在しません（${rel}）"
        continue
      fi
      found=$(count_prose_exact_line "$abs" "$exact" < "$abs")
    fi
    found="${found:-0}"
    if [ "$found" -eq 0 ]; then
      report FAIL "$REGISTRY" "台帳エラー：登録行が本文に存在しません（${rel}）"
    elif [ "$found" -lt "$expected" ]; then
      report FAIL "$REGISTRY" "台帳エラー：実件数がexpected_count未満です（${rel}：${found}/${expected}）"
    elif [ "$found" -gt "$expected" ]; then
      report FAIL "$REGISTRY" "台帳エラー：実件数がexpected_countを超過しています（${rel}：${found}/${expected}）"
    fi
  done
}

load_registry || exit 1

# ---- 検査対象の収集 ----
TARGETS=()
if [ "$STAGED_MODE" -eq 1 ]; then
  # indexが正。working tree上の存在は要求しない（同一snapshot契約）
  while IFS= read -r f; do
    ! is_excluded "$f" && TARGETS+=("$f")
  done < <(git -C "$REPO_ROOT" -c core.quotepath=false diff --cached --name-only --diff-filter=ACMR --find-renames 2>/dev/null)
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
if [ ${#TARGETS[@]} -eq 0 ]; then
  echo "検査対象がありません"
fi

get_text() {
  if [ "$STAGED_MODE" -eq 1 ]; then
    # Office文書はメインループで事前遮断済み（stagedのOffice index読取は別ゲート）
    read_index_content "$(normalize_rel_path "$1")"
    return
  fi
  case "$1" in
    *.pptx|*.docx|*.xlsx)
      unzip -p "$1" "*.xml" 2>/dev/null | sed -e 's/<[^>]*>/ /g' ;;
    *) cat "$1" ;;
  esac
}

# stdinから本文を読み、frontmatterのstatusを出力（本文と同一snapshotを保証）
get_doc_status() {
  awk '
    NR==1 {
      line=$0
      sub(/\r$/, "", line)
      if (line != "---") exit
      in_fm=1
      next
    }
    {
      line=$0
      sub(/\r$/, "", line)
    }
    in_fm && line=="---" { exit }
    in_fm && line ~ /^status:[[:space:]]*/ {
      sub(/^status:[[:space:]]*/, "", line)
      sub(/[[:space:]]+$/, "", line)
      print line
      exit
    }
  '
}

BRAND_COLORS="0F3D96|EEF3FA|1F2937|E5E7EB|FFFFFF|000000|FFF|000"

if [ ${#TARGETS[@]} -gt 0 ]; then
  for f in "${TARGETS[@]}"; do
    if [ "$STAGED_MODE" -eq 1 ]; then
      case "$f" in
        *.pptx|*.docx|*.xlsx)
          # stagedのOffice検査は未対応（index上のバイナリ抽出は別ゲート）。
          # working treeへのフォールバックは禁止のため、明示FAILとする
          report FAIL "$f" "stagedモードのOffice文書検査は未対応です（別ゲートで実装予定・working tree読取へのフォールバックは行いません）"
          continue
          ;;
      esac
    fi
    TEXT=$(get_text "$f")
    PROSE_TEXT=$(printf '%s\n' "$TEXT" | strip_template_and_fences "$(apply_record_form_template_filter "$f")")
    DOC_STATUS=$(printf '%s\n' "$TEXT" | get_doc_status)
    REL_PATH=$(normalize_rel_path "$f")
    if [ "$DOC_STATUS" = "draft" ] || [ "$DOC_STATUS" = "reviewed" ]; then
      UNCERTAIN_LEVEL=WARN
    else
      UNCERTAIN_LEVEL=FAIL
    fi

    # ===== FAIL（出荷不可） =====
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

    # 「未確定」：行単位＋台帳（draft/reviewedでも未登録はFAIL）
    check_mitei_lines "$f" "$REL_PATH" "$UNCERTAIN_LEVEL"

    # その他未確定語：従来どおり（台帳対象外）
    for kw in "【要確認】" "TODO" "仮置き"; do
      if echo "$PROSE_TEXT" | grep -qF "$kw"; then
        report "$UNCERTAIN_LEVEL" "$f" "未確定表記が残存：${kw}"
      fi
    done
    for kw in "★★" "XXX"; do
      if echo "$PROSE_TEXT" | grep -qF "$kw"; then
        report FAIL "$f" "未確定表記が残存：${kw}"
      fi
    done

    # ===== WARN（要レビュー） =====
    case "$f" in
      *.html|*.htm|*.css|*.js|*.svg)
        OFFBRAND=$(grep -oiE "#[0-9a-f]{6}|#[0-9a-f]{3}\b" "$f" 2>/dev/null \
          | tr 'a-f' 'A-F' | sed 's/#//' | sort -u \
          | grep -vE "^(${BRAND_COLORS})$" | head -5)
        if [ -n "$OFFBRAND" ]; then
          report WARN "$f" "ブランド外カラーコード：$(echo $OFFBRAND | tr '\n' ' ')（診断ツール4象限色なら対象外・要目視）"
        fi ;;
    esac
    case "$f" in
      *.md|*.html|*.htm|*.txt)
        LINES=$(grep -nE "、[[:space:]]*$" "$f" 2>/dev/null | cut -d: -f1 | head -10 | tr '\n' ',')
        [ -n "$LINES" ] && report WARN "$f" "改行直前の読点：行 ${LINES%,}"
        for w in "寄り添" "最大化" "変容を促" "本質的な価値" "唯一無二"; do
          if grep -qF "$w" "$f" 2>/dev/null; then
            report WARN "$f" "AI語候補：「${w}」（文脈上必要なら問題なし）"
          fi
        done ;;
    esac
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
fi

# 本文検査対象が0件でも台帳全登録の整合検査は必ず実行する
check_stale_registry_entries

echo "----------------------------------------"
echo "検品結果: FAIL ${FAIL}件 / WARN ${WARN}件（対象 ${#TARGETS[@]}ファイル）"
if [ $FAIL -gt 0 ]; then
  echo "判定: 出荷不可（FAILをすべて解消してください）"
  exit 1
fi
echo "判定: 合格（WARNは要レビュー）"
exit 0
