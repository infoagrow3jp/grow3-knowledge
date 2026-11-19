# gemini-usage の詳細

## 通常の呼び出し

### Gemini CLI（非対話実行）

- 非対話（ヘッドレス）になる条件は、TTYでない環境で実行するか、`-p`（`--prompt`）で指示を渡すこと［D-gemini-cli-headless］
- `-p` は非対話を強制し、標準入力があればその後ろに指示文を付ける［D-gemini-cli-reference］
- 位置引数の指示（`gemini "指示"`）はTTYでは対話モードで始まる。非対話にするには `-p` を使う［D-gemini-cli-reference］
- `-i`（`--prompt-interactive`）は指示を実行したあと対話を続けるので、自動実行には使わない［D-gemini-cli-reference］
- `-i` は標準入力をパイプで渡すときには使えない［D-gemini-cli-configuration］
- 出力形式は `--output-format`（`-o`）で `text`（既定）・`json`・`stream-json` から選ぶ［D-gemini-cli-reference］
- `json` は1つのJSONを返す。キーは `response`（最終回答の文字列）・`stats`（トークン使用量とAPIの遅延）・`error`（失敗時だけ）［D-gemini-cli-headless］
- `stream-json` は改行区切りのJSON（JSONL）で、イベントの種類は `init`・`message`・`tool_use`・`tool_result`・`error`・`result`［D-gemini-cli-headless］
- `stream-json` の `init` にセッションIDとモデル、`result` に集計した統計とモデル別のトークン使用量が入る［D-gemini-cli-headless］
- 終了コードは 0（成功）・1（一般的なエラーまたはAPIの失敗）・42（入力エラー：指示や引数が不正）・53（ターン上限超過）［D-gemini-cli-headless］
- 非対話実行は、保存済みの認証情報があればそれを使う。なければ環境変数で Gemini API キーか Vertex AI の認証を設定する［D-gemini-cli-authentication］
- Gemini API キーは環境変数 `GEMINI_API_KEY` で渡す［D-gemini-cli-configuration］
- 環境変数は `.env` からも読まれる。探す順は、作業フォルダ、親フォルダ（`.git` のあるプロジェクトルートかホームまで）、`~/.env`［D-gemini-cli-configuration］
- 設定の優先順位は、低い順に、既定値、システム既定ファイル、ユーザー設定（`~/.gemini/settings.json`）、プロジェクト設定（`.gemini/settings.json`）、システム設定ファイル、環境変数、コマンドライン引数［D-gemini-cli-configuration］
- 作業対象のフォルダを足すには `--include-directories`（カンマ区切りか複数回指定、最大5つ）［D-gemini-cli-configuration］

呼び出しの形：

```bash
gemini -p "README.md を要約して"
cat error.log | gemini -p "失敗の原因を説明して"
gemini -p "指示" --output-format json
```

### Gemini API（Google GenAI SDK）

- 公式SDKは Google GenAI SDK。Python は `pip install -U google-genai`、JavaScript は `npm install @google/genai`［D-gemini-api-get-started］
- Go は `google.golang.org/genai`、Java は `com.google.genai` の `google-genai`、C# は `Google.GenAI`［D-gemini-api-libraries］
- 新規の実装は Interactions API（`client.interactions.create`）を使う。2026年6月に一般提供になり、新規プロジェクトの推奨インターフェースになっている［D-gemini-api-interactions］
- 最小の形は `model` と `input` の2つ。SDKでは最終出力を `interaction.output_text` で読める［D-gemini-api-get-started］
- `genai.Client()` は、キーを渡さなければ環境変数 `GEMINI_API_KEY` を読む。明示するなら `genai.Client(api_key=...)`［D-gemini-api-migrate-sdk］
- REST は `https://generativelanguage.googleapis.com/v1beta/interactions` へ POST し、`x-goog-api-key` ヘッダでキーを渡す［D-gemini-api-get-started］
- REST の応答は `Interaction` リソース全体で、`steps` 配列に `thought` や `model_output` が順に入る［D-gemini-api-get-started］
- システム指示は `system_instruction`、生成の設定は `generation_config`（`thinking_level`・`max_output_tokens` など）で渡す［D-gemini-api-interactions、D-gemini-api-carbon］
- ストリーミングは `stream=True`。`step.delta` イベントで文章の断片が届く［D-gemini-api-get-started］
- Word・PowerPoint・Excel と OpenDocument のファイルを直接渡せる。ユーザーの指示と関数の応答の中で、文書・表計算・動画・音声の一部（ページ範囲・シート・セル範囲・時間区間、ページ画像・抽出テキスト・数式・動画の文字起こしなどの層）だけを選んで処理できる［G-2026-11-18-1］
- ツールの検索（Preview）：ツールが多いとき、`function` か `mcp_server` のツールに `defer_loading: true` を付け、`{"type": "tool_search"}` のツールを足すと、Gemini が必要な関数スキーマだけを取得する。`execution: "client"` にすると検索をアプリ側で行う。Interactions API（`v1beta`）で Gemini 3.6 以降のモデルが対象［G-2026-11-19-11］

呼び出しの形：

```python
from google import genai

client = genai.Client()
interaction = client.interactions.create(
    model="gemini-4-hydrogen",
    input="Explain how AI works in a few words",
)
print(interaction.output_text)
```

## モデルの選び方

### Gemini API

- 文章・コード・推論の現行の推奨は、汎用の既定が `gemini-4-hydrogen`、最上位の推論が `gemini-4-neon`・`gemini-4-carbon`・`gemini-4-argon`、大量・低コストが `gemini-3.5-flash-lite`［D-gemini-api-latest-model、G-2026-11-18-2］
- `gemini-4-neon` は2026年11月18日に一般提供（GA）になった。有料枠のみで、価格は入力100万トークンあたり $3.00・出力 $15.00［G-2026-11-18-2］
- `gemini-4-carbon` は推論の深さを優先するモデルで、1ターンあたりの思考トークンと遅延が Argon より大きい［D-gemini-api-carbon］
- `gemini-4-argon` は応答が速く1ターンあたりのトークン消費が少ない。対話的なコーディングや日常の機能開発向け［D-gemini-api-carbon］
- Gemini 4 の各モデルはコンテキストが100万トークン、出力は既定64K・ロングデコードで最大100万トークン［D-gemini-api-latest-model、G-2026-11-18-2］
- `thinking_level` の使える値は、`gemini-4-carbon` と `gemini-4-argon` が `low`・`medium`（既定）・`high`、`gemini-4-hydrogen` と `gemini-4-neon` が `low`・`medium`・`high`（既定）・`xhigh`、`gemini-3.5-flash-lite` が `minimal`（既定）・`low`・`medium`・`high`。`minimal` は Gemini 4 では使えず、指定するとエラーになる［D-gemini-api-latest-model、G-2026-11-20-5］
- `thinking_level` は3段階とも評価し、品質の基準を満たす最も低い値を選ぶ［D-gemini-api-carbon］
- `max_output_tokens` は思考と出力の合計の上限。`gemini-4-carbon` では、32K未満を指定している既存の実装は 32,768 以上に上げる［D-gemini-api-carbon］
- `gemini-4-carbon` は無料枠では使えない［D-gemini-api-carbon］
- 難しい指示は数分かかることがある。バックグラウンド実行を使うか、HTTPクライアントのタイムアウトを15分以上にする［D-gemini-api-carbon］
- モデル名の型は、安定版（例 `gemini-3.6-flash`）、プレビュー版、`latest` 別名（例 `gemini-flash-latest`。新しい版に差し替わる）、試験版の4つ。本番は特定の安定版を指定する［D-gemini-api-models］
- プレビュー版は、最短2週間前の告知で廃止される［D-gemini-api-models］
- 停止予定の表の日付は「最も早い場合の停止日」。モデルごとの推奨の置き換え先も同じ表にある［D-gemini-api-deprecations］
- 画像生成の既定は `gemini-nano-banana-2.1`、動画生成は `gemini-omni-1.2-flash`、音声読み上げは `gemini-3.8-flash-tts`、文字起こしは `gemini-3.5-transcribe`、埋め込みは `gemini-embedding-2`［D-gemini-api-latest-model］
- 分類・ルーティング・スコアリングの推奨は `gemini-decision-1`［G-2026-11-20-3］
- リアルタイムの対話型の世界生成は `models/genie-4`（2026年11月19日に一般提供。Interactions API の `v1beta`、有料枠のみ、停止日は未発表）［G-2026-11-19-12、G-2026-11-20-7、G-2026-11-20-8］
- `gemini-4-neon` を使うときは、`temperature`・`top_p`・`top_k` を外す（範囲内の値は無視され、範囲外の値は 400 エラー）［G-2026-11-20-5］
- Gemini 3.8 Flash 以前から `gemini-4-neon` へ移るときは、`thinking_level: minimal`・明示キャッシュ・低い固定の `max_output_tokens`（8,192 など。外すか 65,536 に上げる）を見直す［G-2026-11-20-5］
- Gemini 4 では、ツールを宣言せずシステム指示で生のJSONのツール呼び出しを書かせると `MALFORMED_FUNCTION_CALL` になり得る。ネイティブの関数呼び出しか構造化出力を使う［G-2026-11-20-5］

### Gemini CLI

- `--model`（`-m`）の既定は `auto`。別名は `auto`・`pro`・`flash`・`flash-lite` で、具体的なモデル名も渡せる［D-gemini-cli-reference］
- 既定のモデルは環境変数 `GEMINI_MODEL` か設定の `model.name` でも変えられる［D-gemini-cli-configuration］
- 思考の長い要求がタイムアウトするときは、設定の `model.requestTimeoutMs`（既定 60000）を上げる［D-gemini-cli-configuration］

## 指示の書き方

- 明確で具体的な指示を書く。応答の長さなどの制約と、応答の形式（表・箇条書き・一文など）を指定する［D-gemini-api-prompting］
- 例（few-shot）を常に入れることが推奨されている。例が多すぎると例に過剰に合わせた応答になる［D-gemini-api-prompting］
- 例どうしの構造と書式（XMLタグ・空白・改行・区切り）をそろえる［D-gemini-api-prompting］
- モデルが必要とする情報は、知っている前提にせず文脈として渡す［D-gemini-api-prompting］
- 複雑な指示は分ける。1指示1プロンプトにする、手順ごとにプロンプトをつなぐ、並行に処理して結果をまとめる［D-gemini-api-prompting］
- 複雑なJSONスキーマの出力は、プロンプトで形式を書くより構造化出力の機能を使う［D-gemini-api-prompting］
- 新しい事実や珍しい事実が要るときは Google 検索によるグラウンディング、計算・数え上げが要るときはコード実行ツールを有効にする［D-gemini-api-prompting］
- 次の6項目は、公式が Gemini 3 向けの原則として挙げているもの：
- 目的を明確・簡潔に述べ、不要な言い回しや過度に説得的な表現を避ける［D-gemini-api-prompting］
- XML風のタグ（`<context>`・`<task>` など）か Markdown 見出しで区切り、1つのプロンプトの中では1つの形式に統一する［D-gemini-api-prompting］
- あいまいな用語や変数は明示的に説明する［D-gemini-api-prompting］
- 既定の応答は直接的で簡潔。会話的・詳細な応答が要るときは明示して頼む［D-gemini-api-prompting］
- 重要な行動上の制約・役割・出力形式は、システム指示かユーザープロンプトの先頭に置く［D-gemini-api-prompting］
- 大量の文脈（文書・コード）は先に全部置き、具体的な指示や質問は最後に置く。資料のあとに「上の情報にもとづいて…」のようなつなぎの一文を入れる［D-gemini-api-prompting］
- 思考を内部で行うモデルでは、応答の中で手順や計画を書かせる必要は通常ない［D-gemini-api-prompting］
- エージェント用のシステム指示では、推論の深さ、計画への固執と切り替え、誤りからの回復の粘り強さ、読み取りと書き込みのリスクの区別、確認を求める条件、説明の量を指定する［D-gemini-api-prompting］

## 指示ファイル・スキル

### GEMINI.md

- 読み込む順は、全体用（`~/.gemini/GEMINI.md`）、ワークスペースのフォルダとその親フォルダ、ツールがファイルやフォルダに触れたときにその場所から信頼済みルートまでの祖先（必要時の読み込み）［D-gemini-cli-gemini-md］
- 見つかったファイルは連結され、毎回の指示と一緒にモデルへ送られる［D-gemini-cli-gemini-md］
- 別ファイルの取り込みは `@./path/file.md` の書き方（相対パス・絶対パス）［D-gemini-cli-gemini-md］
- ファイル名は設定の `context.fileName` で変えられる（例：`["AGENTS.md", "CONTEXT.md", "GEMINI.md"]`）［D-gemini-cli-gemini-md］
- 組み込みのシステムプロンプトを置き換えるには環境変数 `GEMINI_SYSTEM_MD`（`true` で `./.gemini/system.md`、それ以外の文字列はパス）［D-gemini-cli-configuration］

### スキル

- スキルはフォルダ単位で、名前と説明だけが最初にシステムプロンプトへ入り、モデルが `activate_skill` ツールを呼んだときに `SKILL.md` の本文とフォルダ構成が読み込まれる［D-gemini-cli-skills］
- 置き場所の優先順位は、低い順に、組み込み、拡張機能、ユーザー（`~/.gemini/skills/` か `~/.agents/skills/`）、ワークスペース（`.gemini/skills/` か `.agents/skills/`）［D-gemini-cli-skills］
- 同じ名前のスキルは優先順位の高い場所のものが使われる。同じ階層では `.agents/skills/` が `.gemini/skills/` より優先される［D-gemini-cli-skills］
- スキルの有効化のときは、名前・目的・アクセスするフォルダを示す確認が出る［D-gemini-cli-skills］
- 端末からの管理は `gemini skills list`・`install`・`link`・`uninstall`・`enable`・`disable`。`--scope` は `user`（既定）か `workspace`［D-gemini-cli-skills、D-gemini-cli-reference］
- `gemini skills install` の確認を省くには `--consent` を付ける［D-gemini-cli-skills］

### サブエージェント

- サブエージェントは既定で有効。無効にするには設定で `experimental.enableAgents` を false にする［D-gemini-cli-subagents］
- 定義ファイルは YAML frontmatter つきの Markdown で、プロジェクト用は `.gemini/agents/*.md`、ユーザー用は `~/.gemini/agents/*.md`。本文がシステムプロンプトになる［D-gemini-cli-subagents］
- frontmatter の必須項目は `name`（英小文字・数字・ハイフン・アンダースコア）と `description`［D-gemini-cli-subagents］
- 任意の項目は `kind`（`local` が既定、または `remote`）、`tools`、`mcpServers`、`model`（既定は `inherit`）、`temperature`、`max_turns`（既定30）、`timeout_mins`（既定10）［D-gemini-cli-subagents］
- `tools` を省くと親セッションの全ツールを引き継ぐ。ワイルドカードは `*`・`mcp_*`・`mcp_<サーバー名>_*`［D-gemini-cli-subagents］
- サブエージェントは別のサブエージェントを呼べない（`*` を与えても見えない）［D-gemini-cli-subagents］
- 特定のサブエージェントに任せるには、指示の先頭に `@<名前>` を書く［D-gemini-cli-subagents］
- 組み込みのサブエージェントに `codebase_investigator` がある［D-gemini-cli-subagents］

## 操作別の注意

### 承認モード（CLI）

- `--approval-mode` の選択肢は `default`・`auto_edit`・`yolo`・`plan`［D-gemini-cli-reference］
- `default` はツール呼び出しごとに確認する。`auto_edit` は編集ツール（`replace`・`write_file`）を自動承認し、ほかは確認する。`yolo` はすべて自動承認する［D-gemini-cli-configuration］
- `plan` は読み取り専用のモード［D-gemini-cli-policy-engine］
- 設定の `general.defaultApprovalMode` に書ける値は `default`・`auto_edit`・`plan` だけ。`yolo` はコマンドラインからしか有効にできない［D-gemini-cli-configuration］
- 設定の `security.disableYoloMode` が true のときは、フラグを付けても `yolo` にならない［D-gemini-cli-configuration］
- `--approval-mode` と `--yolo` は同時に使えない［D-gemini-cli-configuration］
- `yolo` のときは既定でサンドボックスが有効になる［D-gemini-cli-configuration］
- サンドボックスは `--sandbox`（`-s`）か環境変数 `GEMINI_SANDBOX`（`true`・`false`・`docker`・`podman`・任意のコマンド）でも有効にできる［D-gemini-cli-configuration］

### ポリシーエンジン（CLI）

- ルールの判定は `allow`・`deny`・`ask_user` の3つ。非対話モードでは `ask_user` は `deny` として扱われる［D-gemini-cli-policy-engine］
- 既定のポリシーでは、読み取り系のツール（`read_file`・`glob` など）はおおむね許可、書き込み系（`write_file`・`run_shell_command` など）は `ask_user`［D-gemini-cli-policy-engine］
- ユーザーのポリシーは `~/.gemini/policies/*.toml` に置く。フォルダ内の `.toml` はすべて読み込まれる［D-gemini-cli-policy-engine］
- ワークスペース階層（`.gemini/policies`）のポリシーは現在機能しない［D-gemini-cli-policy-engine］
- ルールの `interactive = false` で非対話モードだけに効かせられる。`modes` で承認モードを絞れる（モード名は `default`・`autoEdit`・`plan`・`yolo`）［D-gemini-cli-policy-engine］
- 優先度は 0〜999 で、数字が大きいほど優先される。階層は Admin が User より、User が既定より優先される［D-gemini-cli-policy-engine］
- シェルのコマンドは `commandPrefix` か `commandRegex` で指定する（同じルールで両方は使えない）［D-gemini-cli-policy-engine］
- リダイレクト（`>` など）やコマンド置換（`$()` など）を含むコマンドは、ルールに合っても確認になる。許すには `allowRedirection`・`allowCommandSubstitution` を true にする［D-gemini-cli-policy-engine］
- ツール引数は安定したJSON文字列にして `argsPattern` の正規表現と照合する。最上位の引数どうしは `\x00` で区切られ、ネストした値は区切られない。最上位だけに合わせるには `\x00` で始める（例 `'\x00"command":"git '`）［G-2026-11-19-4］
- `argsPattern` は RE2 構文。先読み・後読み・後方参照・`\uXXXX` は使えず（`\x{XXXX}` を使う）、繰り返しは1,000回まで。旧版はJavaScriptの正規表現として評価していたので、以前読み込めたルールが無効と報告されたら書き直す［G-2026-11-19-4］
- `commandRegex` は最上位の `command` 引数だけに合う。`ls|pwd` のような選択肢もコマンドの先頭から合わせる［G-2026-11-19-4］
- MCP のツールは `mcpName` で指定する。MCP サーバー名にアンダースコアを使うとルールが正しく効かない［D-gemini-cli-policy-engine］
- 追加のポリシーの場所は設定の `policyPaths` で指定できる［D-gemini-cli-configuration］

非対話でだけ git の実行を許すルールの形：

```toml
[[rule]]
toolName = "run_shell_command"
commandPrefix = "git"
decision = "allow"
priority = 100
interactive = false
```

### フォルダの信頼（CLI）

- フォルダの信頼の機能は既定で無効。設定の `security.folderTrust.enabled` を true にすると有効になる［D-gemini-cli-trusted-folders］
- 有効な環境で未信頼のフォルダを非対話実行すると、`FatalUntrustedWorkspaceError` で終了する［D-gemini-cli-trusted-folders］
- 回避するには `--skip-trust` を付けるか、環境変数 `GEMINI_CLI_TRUST_WORKSPACE=true` を設定する（そのセッションだけ信頼する）［D-gemini-cli-trusted-folders］
- 未信頼のフォルダでは、プロジェクトの `.gemini/settings.json` と `.env` が読まれず、MCP サーバーに接続せず、カスタムコマンドも読まれず、ツールの自動承認も効かない［D-gemini-cli-trusted-folders］

### セッション（CLI）

- `--resume`（`-r`）は `"latest"`、番号、セッションのUUIDを受ける。値を省くと `latest` になる［D-gemini-cli-configuration］
- 再開と同時に指示を渡す形は `gemini -r "latest" "指示"`、ID指定は `gemini -r "<session-id>" "指示"`［D-gemini-cli-reference］
- `--list-sessions` は現在のプロジェクトのセッションを一覧して終了する。`--delete-session` は番号かUUIDで削除する［D-gemini-cli-reference、D-gemini-cli-configuration］
- 設定の `model.maxSessionTurns` は1セッションのターン数の上限（既定 -1 で無制限）［D-gemini-cli-configuration］

### 会話の継続と保存（API）

- 会話の継続は、サーバー側で履歴を持つ方法（`previous_interaction_id`。推奨）と、クライアント側で履歴を全部送る方法の2つ［D-gemini-api-get-started］
- `previous_interaction_id` が引き継ぐのは会話の履歴（入力と出力）だけ。`tools`・`system_instruction`・`generation_config` はその回だけ有効なので、毎回指定し直す［D-gemini-api-interactions］
- 既定では Interaction が保存される（`store=true`）。保存期間は有料枠で55日、無料枠で1日［D-gemini-api-interactions］
- `store=false` はバックグラウンド実行と両立せず、以後のターンで `previous_interaction_id` を使えなくする［D-gemini-api-interactions］
- `store=false` で履歴をクライアント側で持つときは、モデルが生成したステップ（`thought` と `function_call` を含む）を受け取ったまま全部送り直す［D-gemini-api-get-started］
- `interactions.create` の応答にはモデルが生成したステップだけが入る。`interactions.get` で取る保存済みのリソースには `user_input` のステップも入る［D-gemini-api-interactions］

### 出力形式と長い処理（API）

- JSONで受けるには `response_format` に `{"type": "text", "mime_type": "application/json", "schema": <JSONスキーマ>}` を渡し、`interaction.output_text` を解析する［D-gemini-api-get-started］
- 長い処理は `background=True` で非同期にし、`interactions.get()` で `status` を見て待つ（`completed`・`failed`）［D-gemini-api-get-started］
- 同期の応答は 65,536 トークンで止まる。それを超える出力は `background=True` にして `max_output_tokens` を 65,536 より大きくする（上限は100万トークンから入力分を引いた値）［D-gemini-api-carbon］
- `background: true` で `max_output_tokens` を指定しないと、64Kトークンで止まる［D-gemini-api-carbon］
- 64Kを超える出力では `model_output` のステップが複数になるので、`interaction.steps` の `model_output` の文章をすべてつなぐ［D-gemini-api-carbon］
- バックグラウンド実行中の `status` は `in_progress` か `queued`［D-gemini-api-carbon］

## 使わないもの

- 旧ライブラリ（Python の `google-generativeai`、JavaScript の `@google/generative-ai`）は2025年11月30日付で非推奨になっており、新しい機能が使えない。Google GenAI SDK（`google-genai`・`@google/genai`）へ移る［D-gemini-api-libraries、D-gemini-api-migrate-sdk］
- `generateContent` は引き続きサポートされるがレガシー扱い。主力系列以外の新しいモデル・機能と、新しいエージェント機能・ツールは Interactions API で提供される［D-gemini-api-interactions］
- `temperature`・`top_p`・`top_k` は、Gemini 4 と Gemini 3.6 以降では値を渡しても無視され、非推奨の警告ヘッダが返る。将来は 400 エラーになる予定なので指定を外す［D-gemini-api-prompting］
- それより前の Gemini 3 のモデルでは、`temperature`・`top_p`・`top_k` を既定値のままにする［D-gemini-api-prompting］
- `gemini-2.5-pro` は非推奨。2026年12月1日から、APIの要求は `gemini-3.8-flash` へ自動で回される［D-gemini-api-deprecations］
- `gemini-2.5-flash` は非推奨。2026年12月1日から、APIの要求は `gemini-3.5-flash-lite` へ自動で回される［D-gemini-api-deprecations］
- `gemini-2.5-flash-lite` は非推奨ではないが、利用は過去に使っていた利用者に限られる。新規は Gemini 4 Hydrogen か 3.5 Flash-Lite を使う［D-gemini-api-models］
- 停止済み：`gemini-2.0-flash`・`gemini-2.0-flash-lite`（置き換え先 `gemini-3.6-flash`・`gemini-3.1-flash-lite`）、`gemini-3-pro-preview`（置き換え先 `gemini-3.1-pro-preview`）、`gemini-3.1-flash-lite-preview`（置き換え先 `gemini-3.1-flash-lite`）［D-gemini-api-deprecations］
- `gemini-3.7-flash` は `gemini-3.8-flash` へ、`gemini-3.5-flash` は `gemini-3.6-flash` へ、APIの要求が自動で回される［D-gemini-api-deprecations］
- `gemini-3-flash-preview` の推奨の置き換え先は `gemini-3.6-flash`、`gemini-3.1-flash-lite`（2027年5月7日停止予定）の置き換え先は `gemini-3.5-flash-lite`［D-gemini-api-deprecations］
- 停止済みの画像・動画モデル：`imagen-4.0-generate-001` など Imagen 系（置き換え先 `gemini-nano-banana-2.1`）、`veo-3.1-generate-preview` など Veo 系（置き換え先 `gemini-omni-1.2-flash`）［D-gemini-api-deprecations］
- 停止済みの埋め込みモデル：`text-embedding-004`・`embedding-001`（置き換え先 `gemini-embedding-2`）［D-gemini-api-deprecations］
- 2026年12月18日停止予定：`gemini-2.5-flash-preview-tts`・`gemini-2.5-pro-preview-tts`・`gemini-3.1-flash-tts-preview`（置き換え先 `gemini-3.8-flash-tts` か `gemini-3.8-flash-lite-tts`）［D-gemini-api-deprecations］
- `gemini-4-carbon` と `gemini-4-neon` は明示キャッシュ（`cachedContents`・`caches.create`）に対応しない。`cached_content` を作る・参照する呼び出しを外す。暗黙キャッシュは 4,096 トークン以上のプロンプトで既定で有効［D-gemini-api-carbon、G-2026-11-20-4］
- CLIの `--yolo`（`-y`）は非推奨。`--approval-mode=yolo` を使う［D-gemini-cli-reference］
- CLIの `--allowed-tools` は非推奨。ポリシーエンジンを使う［D-gemini-cli-reference］
- 設定の `tools.exclude` は非推奨。ツールを外すにはポリシーの `deny` ルールを使う［D-gemini-cli-policy-engine］
