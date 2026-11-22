# claude-usage の詳細

## 通常の呼び出し

### Claude Code CLI（非対話実行）

- 基本形は `claude -p "指示"`（`--print` も同じ）。標準入力も読むので `cat file | claude -p "指示"` の形で渡せる［D-claude-code-headless、D-claude-code-cli-reference］
- 成功は終了コード0、失敗は0以外。不正なフラグは実行前に標準エラーへ、実行中の失敗（認証なし等）は結果として標準出力へ出る［D-claude-code-headless］
- 標準入力は10MBまで。超えるとエラーで終了するので、内容をファイルに書いてパスを指示に書く［D-claude-code-headless］
- `-p` と併用できないフラグがある。`--bg` は拒否される［D-claude-code-headless、D-claude-code-cli-reference］
- `--output-format` は `text`（既定）・`json`・`stream-json` の3つ［D-claude-code-headless］
- `json` は結果本文が `result`、セッションIDが `session_id`、概算費用が `total_cost_usd` に入る［D-claude-code-headless］
- `stream-json` で逐次受け取るときは `--verbose` と `--include-partial-messages` を付ける。最後の行が `result` メッセージ［D-claude-code-headless］
- `--bare` は、フック・スキル・カスタムコマンド・サブエージェント・プラグイン・MCPサーバー・自動メモリ・CLAUDE.md の自動読み込みを省く［D-claude-code-headless、D-claude-code-cli-reference］
- `--bare` は OAuth 資格情報とキーチェーンを読まない。認証は環境変数 `ANTHROPIC_API_KEY` か、`--settings` で渡す `apiKeyHelper`［D-claude-code-headless］
- `--bare` で使えるツールは Bash・ファイル読み取り・ファイル編集。必要な文脈は `--append-system-prompt`・`--settings`・`--mcp-config`・`--agents`・`--plugin-dir` で渡す［D-claude-code-headless］
- `--bare` ではフックが動かない（`--settings` で渡しても動かない）。フックが要る実行には使わない［D-claude-code-headless、D-claude-code-best-practices］
- `--bare` はスクリプトとSDKからの呼び出しで推奨されるモード［D-claude-code-headless］
- `--bare` でも設定ファイルとその権限ルールは読まれる。`~/.claude/settings.json` のフックと、プロジェクトの `.mcp.json` のMCPサーバーは動かない［A-2026-11-20-8］
- `--bare` なしの `-p` は、信頼確認のダイアログを出さずに、作業フォルダの `.claude/settings.json` のフックと `.mcp.json` のサーバーを読み込む［D-claude-code-headless］
- 止めどころは `--max-turns <回数>` と `--max-budget-usd <金額>`（どちらも `-p` 専用）。金額は概算で、上限を超えることがある［D-claude-code-cli-reference、D-claude-code-best-practices］
- `-p` では、指示文に `/スキル名` を入れるとスキルが展開される。`/login` など端末専用の組み込みコマンドは使えない［D-claude-code-headless］
- バックグラウンド作業が残っていると、`-p` は終了せず待つ。既定では連続10分の待機で残りを止める（`CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS` で変更）［D-claude-code-headless］
- SIGTERM で止めると終了コード143で、進行中のターンは未完のまま残る。ターンを終わらせたいときは SIGINT を先に送る［D-claude-code-headless］
- セッションを保存しないときは `--no-session-persistence`（`-p` 専用。再開できなくなる）［D-claude-code-cli-reference］
- `claude auth status` はJSONで認証状態を返し、ログインしていれば終了コード0、していなければ1。`loginExpiresAt` は保存済みログインの有効期限の見込み日か `null`〔v2.1.318以降〕［A-2026-11-20-9］
- 無人実行の前に決めること：完了の条件、自分で確認する手段、触ってよい範囲、止める条件、結果の行き先と承認者［D-claude-code-best-practices］

### Claude API（Messages API）

- 最小のリクエストは `/v1/messages` へのPOSTで、本文に `model`・`max_tokens`・`messages`（`role` と `content` の配列）を送る［D-platform-working-with-messages］
- ヘッダーは `x-api-key`・`anthropic-version`・`content-type: application/json`［D-platform-working-with-messages］
- `anthropic-version` ヘッダーは必須。SDK は自動で付ける。最新は `2026-10-21` で、最新版の利用が推奨されている［D-platform-api-versioning］
- APIバージョンの履歴は `2026-10-21`・`2023-06-01`・`2023-01-01`［D-platform-api-versioning］
- `2026-10-21` では、assistant メッセージ直下の `document` ブロック、user メッセージの `text` ブロックに付けた空でない `citations`、`temperature`・`top_p`・`top_k` が400になる［D-platform-api-versioning］
- Messages API は状態を持たない。毎回、会話履歴の全体を送る［D-platform-working-with-messages］
- システムプロンプトは最上位の `system` に書く。会話の途中で足す指示は、user ターンの直後に `"role": "system"` のメッセージとして入れる（先頭には置けない。対応モデルは Fable 5.2・Opus 5.5・Sonnet 5.5・Haiku 5.5 など）［D-platform-working-with-messages］
- 応答の終わり方は `stop_reason` で判定する（`end_turn`・`max_tokens`・`refusal` など）。`refusal` には `stop_details` が付く［D-platform-working-with-messages］

## モデルの選び方

### 現行モデル（API）

- `claude-fable-5-2`：難しい推論と長時間のエージェント作業向け。思考は常時オン（adaptive）、effort の既定は `high`［D-platform-models-overview］
- `claude-opus-5-5`：長時間のエージェント型コーディングと知識労働向け。思考は常時オン（adaptive）、effort の既定は `medium`［D-platform-models-overview］
- `claude-sonnet-5-5`：速さと賢さの釣り合いがよい。思考は adaptive、effort の既定は `high`［D-platform-models-overview］
- `claude-haiku-5-5`：分類・抽出・振り分けなど大量で低遅延の処理向け。思考は adaptive、effort の既定は `medium`［D-platform-models-overview］
- 4モデルとも入力上限は100万トークン、出力上限は12.8万トークン［D-platform-models-overview］
- モデルIDはすべて固定の版（4.6世代以降の日付なしIDも同じ）。新しい版は新しいIDで出る［D-platform-models-overview］
- `claude-mythos-5-2` は、Anthropic の検証プログラムで認められた組織だけが使える［D-platform-choosing-a-model、D-platform-fable-5-2-migration］
- 選び方は2通り。安く速く始めるなら `claude-haiku-5-5` から試して不足があれば上げる。能力優先なら `claude-opus-5-5` から始め、`xhigh`・`max` でも足りなければ `claude-fable-5-2` へ移る［D-platform-choosing-a-model］
- effort の調整は、モデルを替えるより効くことが多い［D-platform-choosing-a-model］
- 利用できる各モデルの上限や機能は Models API で取得できる［D-platform-models-overview］

### Claude Code でのモデルと effort

- `--model` には別名かモデルIDを渡す。別名は `fable`・`opus`・`sonnet`・`haiku`・`best`（`opus` と同じ）・`opusplan`（計画は `opus`、実行は `sonnet`）・`default`（上書きを消す）［D-claude-code-model-config］
- 別名は推奨版を指し、時間とともに変わる。接続先（プロバイダー）によって古い版に解決されることがある。固定するときはモデルID（例：`claude-opus-5-5`）を渡す［D-claude-code-model-config］
- `opus`・`sonnet` が100万トークンの窓を既定で持たない環境で両方に窓を求めるときは、モデルを `opusplan[1m]` にする［A-2026-11-20-6］
- モデル指定の優先順は、セッション中の `/model`、起動時の `--model`、環境変数 `ANTHROPIC_MODEL`、設定ファイルの `model`、`ANTHROPIC_DEFAULT_MODEL` の順［D-claude-code-model-config］
- `--model` と `ANTHROPIC_MODEL` は、起動したそのセッションだけに効く［D-claude-code-model-config］
- 必要バージョン：Sonnet 5.5 は v2.1.284 以降、Opus 5.5 は v2.1.280 以降、Haiku 5.5 は v2.1.293 以降［D-claude-code-model-config］
- `--effort` は `low`・`medium`・`high`・`xhigh`・`max`・`ultracode`。使える段階はモデルによる。対応しない段階を指定すると、それ以下で対応する最高の段階になる［D-claude-code-cli-reference、D-claude-code-model-config］
- `--effort ultracode` は `xhigh` に加えてワークフローの自動編成をオンにする〔v2.1.203以降〕［D-claude-code-model-config］
- Claude Code での effort の既定は、Fable 5.2・Opus 5.5・Sonnet 5.5・Haiku 5.5 が `medium`（APIの既定とは別）［D-claude-code-model-config］
- effort の決まり方は、環境変数 `CLAUDE_CODE_EFFORT_LEVEL`、セッション中の指定（`/effort` など）、`--effort`、設定ファイル、モデルの既定の順［D-claude-code-model-config］
- 設定ファイルの `effortLevel` に書けるのは `low`・`medium`・`high`・`xhigh`（`max` は書けない）［D-claude-code-model-config］
- 段階の目安：`low` は結果を毎回見る軽い作業、`medium` は範囲が明確な日常の開発、`high` は検証や境界条件が効く作業、`max` は任せきりの難問（考えすぎることがあるので試してから使う）［D-claude-code-model-config］
- 圧縮の窓の大きさ（`CLAUDE_CODE_AUTO_COMPACT_WINDOW`）は100K トークン以上の数で指定する（例：`200000`）。値を引用した警告が出たら、そのセッションは指定どおりの値を使っていないので、数を指定し直す。`200k`・`1M` の書き方は v2.1.304 以降［A-2026-11-19-14］
- `--fallback-model sonnet,haiku` のように渡すと、主モデルが混雑・利用不可のときに順に切り替える［D-claude-code-cli-reference］
- `API Error: 400 Invalid effort level` が出たら v2.1.314 以降へ更新して再起動する。直らなければ `CLAUDE_CODE_EXTRA_BODY` から `output_config.effort` のキーを消す［A-2026-11-20-15］
- フォーク・フォークしたスキル・チームメイト以外のサブエージェントの effort は、`CLAUDE_CODE_EFFORT_LEVEL`、起動元サブエージェントの `effort` かそのターンだけの指定（スキルの `effort` など）、`CLAUDE_CODE_SUBAGENT_EFFORT` のうち最初に当たるものになる。どれもなければ、主会話と同じモデルではセッションの指定に従い、別のモデルではその指定は効かない［A-2026-11-20-14、A-2026-11-20-15］
- サブエージェントのモデルは、呼び出し時の `model` 指定、定義の `model`、環境変数 `CLAUDE_CODE_SUBAGENT_MODEL`、親のモデルの順で決まる［D-claude-code-sub-agents］

### モデルを替えるとき

- 替える前に、モデル別の移行ガイドで破壊的変更を確かめる［D-platform-choosing-a-model、D-platform-fable-5-2-migration］
- Opus 4.8 以前から `claude-fable-5-2` へ移ると、`thinking` を指定しないリクエストでも思考が走る。`max_tokens` を見直し、思考を減らしたいところは effort を下げる［D-platform-fable-5-2-migration］
- 別のモデルへ会話を移すと、移行先が読めない `thinking` ブロックはAPIが落とす（リクエストは成功する）［D-platform-fable-5-2-migration］
- 提供終了日を過ぎたモデルへのリクエストは失敗する。提供終了の60日以上前に通知がある［D-platform-model-deprecations］

## 指示の書き方

- Claude は、背景を知らない優秀な新人だと考えて書く。背景の少ない同僚が読んで迷う指示は、Claude も迷う［D-platform-prompting-best-practices］
- 出力の形式と制約を具体的に書く。順番や網羅が大事な手順は番号付きで書く［D-platform-prompting-best-practices］
- 求める以上のことをしてほしいときは、推測に任せず明示して頼む［D-platform-prompting-best-practices］
- 指示には理由や背景を添える（例：「読み上げソフトで読むので省略記号を使わない」）。理由から一般化して動く［D-platform-prompting-best-practices］
- 「〜するな」より「〜する」と書く（例：「マークダウンを使うな」ではなく「流れる文章の段落で書く」）［D-platform-prompting-best-practices］
- 例は3〜5個、実際の用途に近く、偏らないものを `<example>` タグで囲んで渡す［D-platform-prompting-best-practices］
- 指示・文脈・例・入力が混ざるときは、種類ごとにXMLタグ（`<instructions>`・`<context>`・`<input>` など）で分ける［D-platform-prompting-best-practices］
- 2万トークンを超える資料は冒頭に置き、質問を末尾に置く。複数の資料は `<document>` タグで包み、`<source>` と `<document_content>` を分ける［D-platform-prompting-best-practices］
- 役割はシステムプロンプトに書く。1文でも効く［D-platform-prompting-best-practices］
- 「迷ったら〜のツールを使え」「必ず徹底的に」のような念押しは外す。現行モデルでは使いすぎ・やりすぎの原因になる［D-platform-prompting-best-practices］
- サブエージェントを使いすぎるときは、使う場面（並列・文脈の分離・独立した作業）と使わない場面を指示に書く［D-platform-prompting-best-practices］
- 思考を切っているときの段階的な推論は、答えの前に考えさせ、最終回答を `<answer>` タグに入れさせれば取り出せる。推論を `<thinking>` タグなどで書かせる指示は、モデルによっては拒否される。その場合は思考に任せ、費用や遅延が気になるときは effort を下げる［A-2026-11-22-7］
- モデル別のプロンプトの手引きがある。使うモデルの手引きを先に読む［D-platform-prompting-best-practices］
- `claude-fable-5-2` は、effort が `medium` 以上のとき「考えずに直接答えて」と書いても思考を止めない。その行を消して effort を下げる［D-platform-fable-5-2-migration］
- Claude Code には、リポジトリを読んでも分からないこと（会議で決めたこと、頭の中にしかない手順、必要な環境変数）だけを書く［D-claude-code-best-practices］
- 手元にある材料は説明せずに渡す（ファイルは `@パス`、コマンド出力はパイプ）［D-claude-code-best-practices］
- `think hard`・`be thorough` は普通の文として扱われ、effort を上げるキーワードではない。考える深さは effort で指定する［D-claude-code-best-practices］
- 最小限でなく作り込んだものがほしいときは、範囲（空の状態・エラー時・保存の流れなど）を具体的に書く［D-claude-code-best-practices］
- 確認手段は、テスト・ビルドの終了コード・リンター・出力の差分比較など、Claude が結果を読めるものにする。「全部通った」だけでなく、実行したコマンドと出力を報告させる［D-claude-code-best-practices］
- 構成やファイル配置の説明は書かない。リポジトリから読み取れる［D-claude-code-best-practices］

## 指示ファイル・スキル

### CLAUDE.md

- 置き場所と範囲：`~/.claude/CLAUDE.md`（個人・全プロジェクト）、`./CLAUDE.md` か `./.claude/CLAUDE.md`（プロジェクト共有）、`./CLAUDE.local.md`（個人・そのプロジェクトだけ）［D-claude-code-memory］
- 作業フォルダとその上位のフォルダにある CLAUDE.md・CLAUDE.local.md は起動時にすべて読まれ、上書きではなく連結される。下位フォルダのものは、そのフォルダのファイルを読み書きしたときに読まれる［D-claude-code-memory］
- CLAUDE.md はシステムプロンプトではなく、その後の user メッセージとして渡される。厳密に守られる保証はない［D-claude-code-memory］
- 1ファイル200行未満を目安にする。長いと文脈を使い、守られにくくなる。4MiBを超えるファイルは読み飛ばされる［D-claude-code-memory］
- 書くのは毎回必要な事実（ビルド・テストのコマンド、決まり、「必ずXする」）。複数手順の作業はスキルへ、一部のフォルダだけの決まりは `.claude/rules/` のパス指定ルールへ移す［D-claude-code-memory、D-claude-code-best-practices］
- 2つの指示が矛盾すると、どちらが採られるかは決まらない。古い指示・矛盾する指示は消す［D-claude-code-memory］
- `@パス` で他のファイルを取り込める（最大4段）。取り込んだファイルも一緒に読まれるので、文脈の量は減らない［D-claude-code-memory］
- 特定の時点で必ず実行させたいこと（コミット前、編集後など）はフックにする［D-claude-code-memory、D-claude-code-best-practices］
- 確実に強制するフックは `command`・`http`・`mcp_tool` の種類にする。`prompt`・`agent` のフックは別のモデルが判断するので確定的でない［A-2026-11-20-7］
- フック自体が失敗・タイムアウトしたときも操作を止めたいときは `onFailure: "block"` を足す。`mcp_tool` のフックでの指定は v2.1.328 以降［A-2026-11-20-7、A-2026-11-18-1］
- システムプロンプトの水準で効かせたい指示は `--append-system-prompt` で渡す［D-claude-code-memory］
- プロジェクト直下の CLAUDE.md は、圧縮（compact）の後に読み直される。会話の中だけで伝えた指示は残らない［D-claude-code-memory］
- `--add-dir` で足したフォルダの CLAUDE.md は、既定では読まれない（`CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` で読む）［D-claude-code-memory］
- `AGENTS.md` は、作業フォルダとその上位に CLAUDE.md・`.claude/CLAUDE.md`・CLAUDE.local.md が1つもないときだけ読まれる〔v2.1.277以降〕［D-claude-code-memory］
- 指示ファイルの古い内容・矛盾の点検は `/doctor prompt-audit`〔v2.1.283以降〕［D-claude-code-memory］
- 読み込まれたかどうかは、セッション内の `/context all` の「Memory files」で確かめる［D-claude-code-memory］

### スキル

- 置き場所：`~/.claude/skills/<名前>/SKILL.md`（個人）、`.claude/skills/<名前>/SKILL.md`（プロジェクト）。下位フォルダの `.claude/skills/` は、そのフォルダのファイルを読み書きしたときに読まれる［D-claude-code-skills］
- 通常のセッションでは、説明（`description`）だけが文脈に入り、本文は呼び出されたときに読まれる［D-claude-code-skills］
- frontmatter のフィールドはすべて任意で、`description` が推奨。`name` を省くとフォルダ名がコマンド名になる［D-claude-code-skills］
- `description` と `when_to_use` は、一覧では合わせて1,536字で切られる。主な用途を先頭に書く［D-claude-code-skills］
- frontmatter は、ファイルの1行目が `---` のときだけ読まれる。YAMLが壊れていると、本文だけが読まれ、説明での自動起動が効かない［D-claude-code-skills］
- フィールド名は表のとおりに書く（ハイフン区切り、`when_to_use` だけ下線）。未知のフィールドはエラーなしで無視される［D-claude-code-skills］
- 起動の制御：`disable-model-invocation: true` は人が `/名前` で呼ぶ専用、`user-invocable: false` は Claude だけが呼ぶ［D-claude-code-skills］
- `allowed-tools` は、スキルを呼んだターンの間だけ許可する（次のメッセージで消える）［D-claude-code-skills］
- `context: fork` を付けると、スキルを別のサブエージェントの文脈で実行する［D-claude-code-skills］
- 呼び出された本文は会話に残り続け、後のターンで読み直されない。作業全体に効かせたい指示は「編集のたびに〜する」のように書く［D-claude-code-skills］
- `paths` は、スキルを自動で起動させるファイルのglob（カンマ区切りかYAMLの配列）。基準は作業ディレクトリで、その外のファイルには当たらない。主会話では、同じGit worktree内のサブディレクトリへ `cd` しても、主たる作業ディレクトリが基準のまま［A-2026-11-20-13］
- 新しいスキルが一覧に出ないときは `/reload-skills` を実行する［A-2026-11-20-13］
- 圧縮の後は、各スキルの先頭5,000トークンだけが残る（合計25,000トークンまで）。大事な指示を SKILL.md の上のほうに置く［D-claude-code-skills］
- 本文は短くする。長い資料は同じフォルダの別ファイルに置き、SKILL.md から参照する［D-claude-code-skills］
- スキルが多いと、一覧の説明が削られる（一覧の予算は文脈の1%）。起動しないときは、説明に利用者が言いそうな語が入っているかを確かめる［D-claude-code-skills］
- frontmatter が読めないファイルは `claude plugin validate .claude/skills` で探せる〔v2.1.233以降〕［D-claude-code-skills］
- フォルダ名 `synced` と `anthropic-skills` は予約されていて、その名前のスキルは読み込まれない［D-claude-code-skills］

### サブエージェント

- 置き場所と優先順：`--agents` で渡すJSON（そのセッションだけ）、`.claude/agents/`（プロジェクト）、`~/.claude/agents/`（個人）の順。同名は優先度の高いものが使われる［D-claude-code-sub-agents］
- 定義ファイルは、YAML の frontmatter と、システムプロンプトになる本文（Markdown）でできている［D-claude-code-sub-agents］
- 必須は `name` と `description`。`name` がない、`description` がない、1行目が `---` でない、YAMLが壊れている、のどれかがあると、読み飛ばされる［A-2026-11-20-5］
- 複数語のフィールド名は camelCase（`maxTurns`・`disallowedTools`・`permissionMode`）。未知のフィールドはエラーなしで無視される［D-claude-code-sub-agents］
- 主なフィールド：`tools`（省くと全ツールを継承）、`disallowedTools`、`model`、`permissionMode`、`maxTurns`、`skills`（本文ごと先に読ませる）、`effort`、`isolation: worktree`［D-claude-code-sub-agents］
- `model` には `sonnet`・`opus`・`haiku`・`fable`、モデルID、`inherit` が書ける。省くと、呼び出した会話と同じモデルで動く［D-claude-code-sub-agents］
- `autoCompactWindow` は100000以上の整数で書く。frontmatter では `200k` は200と読まれ、下限未満として無視される〔v2.1.296以降〕。`CLAUDE_CODE_AUTO_COMPACT_WINDOW` も設定したときは、`autoCompactWindow`・モデルの文脈窓・その変数の窓のうち最小のものが使われる〔v2.1.312以降〕［A-2026-11-19-13］
- サブエージェントは、新しい独立した文脈で始まる。会話履歴・呼び出し済みのスキル・読み込み済みのファイルは見えない［D-claude-code-sub-agents］
- サブエージェントのシステムプロンプトは、定義の本文と環境情報だけで、Claude Code 本体のシステムプロンプトは入らない［D-claude-code-sub-agents］
- CLAUDE.md の階層は、サブエージェントにも読み込まれる（組み込みの Explore と Plan は読まない。`omitClaudeMd: true` で外せる〔v2.1.271以降〕）［D-claude-code-sub-agents］
- 非対話実行では、`--append-subagent-system-prompt` ですべてのサブエージェントのシステムプロンプトに文を足せる〔v2.1.205以降〕［D-claude-code-sub-agents、D-claude-code-cli-reference］
- `claude -p` とSDKでは、サブエージェントが起こしたサブエージェントのうち、待つのは前景のものだけ。背景のものは、起こした側より長引けば主会話へ報告する［A-2026-11-20-5］
- 同じ作業をサブエージェントに渡しても、答えは良くならない。使いどころは、並列の作業、出力の多い作業の切り離し、経緯を見ていない目でのレビュー［D-claude-code-best-practices］

### 設定ファイル

- 設定ファイルは `~/.claude/settings.json`（個人）、`.claude/settings.json`（プロジェクト共有）、`.claude/settings.local.json`（個人・そのプロジェクトだけ）と、組織の管理設定［D-claude-code-settings］
- 優先順は高い順に、管理設定、コマンドライン（`--settings`）、`.claude/settings.local.json`、`.claude/settings.json`、`~/.claude/settings.json`［D-claude-code-settings］
- `permissions.allow` のようなリストは、上書きではなく各ファイルの分が合わさる［D-claude-code-settings］
- 1回の実行だけ設定を変えるときは `--settings <ファイルかJSON>`。渡したキーだけが上書きされる。`Managed`・`Global config` のキーと、`prependPlugins` など一部のユーザー設定のキーは `--settings` では設定できない［A-2026-11-23-2、D-claude-code-cli-reference］
- 読み込む設定の範囲は `--setting-sources user,project,local` で絞れる［D-claude-code-cli-reference］
- 環境変数は、この優先順の段には入らない。設定キーとどちらが勝つかは、組み合わせごとに決まっている［D-claude-code-settings］

## 操作別の注意

### セッションの再開

- `--continue`（`-c`）は直近の会話を続ける。`claude -p --continue` は、`-p` やSDKで作ったセッションも対象にする［D-claude-code-headless、D-claude-code-cli-reference］
- `--resume` には、セッションID・セッション名・セッションの `.jsonl` ファイルの絶対パスを渡せる。IDなら別のフォルダからでも再開できる［D-claude-code-headless、D-claude-code-cli-reference］
- セッションIDは `claude -p "..." --output-format json` の `session_id` から取る［D-claude-code-headless］
- 再開時に新しいIDで枝分かれさせるときは `--fork-session`。IDを自分で決めるときは `--session-id <UUID>`［D-claude-code-cli-reference］
- システムプロンプトは、会話の最初のリクエストで記録され、`--resume`・`--continue` の後もそれが使われる。再開のたびに作り直すときは `--system-prompt-snapshot off`〔v2.1.257以降〕［D-claude-code-cli-reference］
- `--bare` では、この記録は既定でオフ（`--system-prompt-snapshot on` でオン）［D-claude-code-cli-reference］
- 再開した実行の `total_cost_usd` は、それまでの実行分を含む合計になる［D-claude-code-headless］

### 権限モードと承認

- `--permission-mode` の値は `default`（表示名は Manual。`manual` も可）・`acceptEdits`・`plan`・`auto`・`dontAsk`・`bypassPermissions`［D-claude-code-cli-reference、D-claude-code-permission-modes］
- 承認なしで動く範囲：`default` は作業フォルダ内のファイル読み取りとサブエージェントの起動など承認の要らない操作だけ（編集・シェルコマンド・ネットワーク要求の多くは承認を求める）、`acceptEdits` は読み取り・ファイル編集・`mkdir` などのファイル操作、`auto` は分類器の確認つきで全部、`dontAsk` は読み取りと、許可ルールかフックが承認したほとんどの呼び出しだけ、`bypassPermissions` は全部［A-2026-11-20-10、A-2026-11-20-11、A-2026-11-23-1］
- 作業フォルダ外の最初の読み取りで出る確認は、`-p`・Agent SDK・バックグラウンドセッション・VS Code のチャットパネル・デスクトップアプリでは出ず、読み取りはそのまま実行される［A-2026-11-20-2］
- `--allow-dangerously-skip-permissions` は `bypassPermissions` を `Shift+Tab` の切り替えに足すだけで、そのモードでは始めない。対話端末のセッションで切り替えに入っている間は、plan モードでも、計画を承認する前にほとんどの編集とコマンドが承認なしで動く［A-2026-11-20-9］
- 開始時のモードは、`--permission-mode`（または `--dangerously-skip-permissions`）、設定ファイルの `permissions.defaultMode`、組み込みの既定の順で決まる［D-claude-code-permission-modes］
- `claude -p` とSDKの組み込みの既定は `default`（Manual）〔v2.1.302以降〕。承認が要る呼び出しは、許可ルール・フック・`--permission-prompt-tool` が承認しない限り拒否される［D-claude-code-permission-modes、D-claude-code-headless］
- プロジェクトの `.claude/settings.json` と `.claude/settings.local.json` に書いた `defaultMode` の `auto` と `bypassPermissions` は効かない［D-claude-code-permission-modes］
- `--allowedTools` に入れたツールは承認なしで動く。入れていないツールも、承認の要らない呼び出しは動く［D-claude-code-headless］
- auto モードで始めた実行では、中身のない `Bash` の許可は外され、コマンドごとに分類器が判断する［D-claude-code-headless］
- `-p` の auto モードでは、分類器が止めた操作だけが拒否され、実行は続く［D-claude-code-best-practices］
- `dontAsk` は、確認が要る呼び出しをすべて拒否する。明示の ask ルールに当たるものと `AskUserQuestion` は、許可ルールがあっても拒否される［D-claude-code-permission-modes、D-claude-code-headless］
- `--permission-prompts none` は、承認できる人がいない実行で使う〔v2.1.259以降〕。確認が要る要求は拒否され、Claude には再試行しないよう伝わり、`AskUserQuestion` のような人の回答が要るツールは外される［D-claude-code-headless］
- `--permission-prompts none` は1回の実行だけに効く。以後の実行でも効かせるときは、設定の `permissions.denyInsteadOfPrompting` を `true` にする［D-claude-code-headless］
- 拒否された呼び出しは、`stream-json` では `permission_denied` のメッセージと、最後の結果の `permission_denials` に出る［D-claude-code-headless］
- 承認を外部のツールに任せるときは `--permission-prompt-tool mcp__<サーバー>__<ツール>`［D-claude-code-cli-reference］
- `bypassPermissions`（`--dangerously-skip-permissions`）は、隔離したコンテナ・VMの中だけで使う。Linux と macOS では、root や `sudo` での起動は拒否される［D-claude-code-permission-modes］
- `bypassPermissions` でも deny ルールは効く。allow ルールは効果がない［D-claude-code-permission-modes］
- `--restricted` を付けた起動では `bypassPermissions` が拒否され、`Error: bypassPermissions not supported in restricted mode` になる。`--dangerously-skip-permissions` など有効にしている指定を外すか、`--restricted` なしで起動する〔v2.1.248以降〕［A-2026-11-19-10］
- auto モードでは、サーバー側の分類器の審査のもとで、作業ツリーがきれいな状態の `git reset --hard` が止められることがある。止められた後は分類器がきれいな状態を見て、Claude の再試行を許可できる［A-2026-11-19-10］
- auto モードの分類器は、Agent ツールで起こしたサブエージェントの作業を3か所で確認する。エージェントチームのチームメイト以外のサブエージェントが終わると、親が読む前にその作業と最終報告を審査する。指摘や審査の拒否があっても報告は警告つきで届き、分類器が使えないときは確認を促す注記つきで届く［A-2026-11-22-1］
- `web-fetch` サブエージェントは、`WebFetch(domain:...)` の許可ルールか事前承認ドメインがタスク内の全URLを覆うとき、最初の2つの確認を省けることがある。その場合は `dontAsk` モードで始まり、承認が要る別の取得は拒否される。3つ目の確認は残る［A-2026-11-22-1］
- どのモードでも自動承認されないもの：明示の ask ルールに当たるツール、`AskUserQuestion`、重要なパスへの `rm`・`rmdir`［D-claude-code-permission-modes］
- 権限ルールは Claude Code が強制する。指示文や CLAUDE.md に書いても、許可・禁止は変わらない［D-claude-code-permissions］

### 権限ルールの書き方

- 形は `Tool` か `Tool(指定)`。例：`Bash(npm run build)`（完全一致）、`Read(./.env)`、`WebFetch(domain:example.com)`［D-claude-code-permissions］
- 評価の順は deny、ask、allow。先に当たったものが結果になる。狭い allow で、広い deny や ask に例外を作ることはできない［D-claude-code-permissions］
- Bash のルールの `*` は、空白を含む任意の文字列に当たる。`*` はサブコマンドの後に置く（`Bash(git log *)`。`Bash(git *)` は git の全コマンドを許す）［D-claude-code-permissions］
- `Bash(git diff *)` のように `*` の前に空白を入れる。空白がない `Bash(git diff*)` は `git diff-index` にも当たる［D-claude-code-headless］
- deny にツール名だけを書くと、そのツール自体が Claude から見えなくなる。`Bash(rm *)` のように指定を付けると、当たる呼び出しだけが止まる［D-claude-code-permissions］
- Read・Edit の deny ルールは、組み込みのファイルツールと、Claude Code が解析できるBashコマンドのリダイレクト先・`cat`・`head`・`tail`・`sed`・`tee` などに効く。ファイル名を書かずに読むコマンド（フォルダで `grep -r pattern .`）や、スクリプトが自分でファイルを開く場合には効かない。シェルコマンドをOSの水準で縛るにはサンドボックスを有効にし、サンドボックス外での再試行を止める［A-2026-11-20-3］
- ルールには正式なツール名を使う。画面上の表示名（例：`Stop Task`）では当たらない［D-claude-code-permissions］

### ツールの制限

- `--allowedTools`：承認なしで動かすツール（権限ルールの書き方で書く）［D-claude-code-cli-reference］
- `--tools`：使える組み込みツールそのものを絞る（`""` で全部オフ、`"Bash,Edit,Read"` のように列挙）。MCPツールには効かない［D-claude-code-cli-reference］
- `--disallowedTools`：deny ルール。`"mcp__*"` で全MCPツールを外す［D-claude-code-cli-reference］
- MCPサーバーを渡したものだけにするときは `--strict-mcp-config --mcp-config <ファイル>`［D-claude-code-cli-reference］
- `-p` に `--mcp-config` を付けると、最初のターンの前にサーバーの接続を待つ（既定で最大30秒）。検証に落ちた項目は飛ばされ、実行は続く。`stream-json` の `system/init` の `mcp_servers` と `mcp_server_errors` で確かめる［D-claude-code-headless］

### 出力形式

- スキーマに合うJSONは、`--output-format json` と `--json-schema '<JSON Schema>'` を併せて指定する。結果は `structured_output` に入る［D-claude-code-headless］
- スキーマが不正だと `Error: --json-schema is not a valid JSON Schema` で終了する。`format` キーワードは検証されない［D-claude-code-headless］
- 拒否などで有効な構造化出力が出なかったときは `structured_output` がない。使う前に有無を確かめる［D-claude-code-headless］
- `stream-json` の最初のイベント `system/init` に、モデル・ツール・MCPサーバー・読み込んだプラグインが出る。プラグインの読み込み失敗は `plugin_errors` に出る［D-claude-code-headless］
- APIの再試行は `system/api_retry` イベントで分かる（`attempt`・`max_retries`・`error` など）［D-claude-code-headless］
- サブエージェントの本文と思考も流すときは `--forward-subagent-text`（`-p` と `--output-format stream-json` が必要）〔v2.1.211以降〕［D-claude-code-cli-reference、D-claude-code-headless］

### システムプロンプト

- `--append-system-prompt`・`--append-system-prompt-file` は既定のプロンプトに足す。`--system-prompt`・`--system-prompt-file` は既定のプロンプトを丸ごと置き換える［D-claude-code-cli-reference］
- 置き換えると、ツールの使い方・安全上の指示・コーディングの決まりもすべて消える。Claude Code と役割が違うエージェントにするときだけ使う［D-claude-code-cli-reference］
- 足す系と置き換える系は併用できる［D-claude-code-cli-reference］

### 自分で書いていないリポジトリでの実行

- `-p` は信頼確認のダイアログを出さない。設定ファイルのフック、`env`、`apiKeyHelper` などのヘルパー、プロジェクトのスキルのフックと `allowed-tools` は、信頼していないフォルダでも使われる［D-claude-code-permissions］
- `.mcp.json` のサーバーは、`-p` では確認なしで接続される［D-claude-code-permissions］
- `.claude/settings.json` の `permissions.allow` は、信頼していないフォルダでは使われず、標準エラーに警告が出る［D-claude-code-permissions］
- 対策：`--setting-sources user`（プロジェクトの設定と `.mcp.json` を読まない）、`--bare`、`--settings '{"disableAllHooks": true}'`（フックを止める）［D-claude-code-permissions］

### 作業フォルダの追加

- `--add-dir` はファイルへのアクセスを足すだけで、そのフォルダの `.claude/` の設定の大半は読まれない（スキルなどは読まれる）［D-claude-code-cli-reference、D-claude-code-skills］

### API での注意

- `thinking` を指定しなくても思考が走るモデルでは、応答の `text` ブロックの前に `thinking` ブロックが入る。`content[0].text` と決め打ちせず、`type` でブロックを選ぶ［D-platform-fable-5-2-migration］
- ツールを使うループでは、`thinking` ブロックを（空のものも含めて）変えずにツール結果と一緒に送り返す［D-platform-fable-5-2-migration］
- 思考のトークンは出力トークンとして数えられ、`max_tokens` は思考と本文の合計にかかる。小さいと、本文が出る前に `stop_reason: "max_tokens"` で止まる。`max_tokens` を増やすか effort を下げる［D-platform-fable-5-2-migration］
- 履歴は追記だけにする。assistant のターンは、APIが返したとおりに（`thinking` ブロックごと）足す［D-platform-prompting-best-practices］
- `claude-fable-5-2` では、会話の途中で `system`・`tools`・過去のメッセージを変えてから `thinking` ブロックを送り返すと400になる。同じ本文の再送では直らない［D-platform-fable-5-2-migration］
- 途中で指示を変えたいときは、`system` を書き換えずに、途中の `role: "system"` メッセージで足す［D-platform-prompting-best-practices、D-platform-working-with-messages］
- effort は `output_config` の `effort` で指定する（例：`output_config={"effort": "high"}`）［D-platform-prompting-best-practices］
- `claude-fable-5-2` と `claude-mythos-5-2` の `tool_choice` は `{type: "auto"}`（既定）と `{type: "none"}` だけが使える［D-platform-fable-5-2-migration］
- `claude-fable-5-2` では、コンピューター操作のツール `computer_20251124` は400になる（Amazon Bedrock を除く）。`computer_toolset_20260801` を宣言する［D-platform-fable-5-2-migration］
- 出力の形を固定したいときは、構造化出力を使うか、形を指示して従わせる。分類は、ラベルを enum にしたツールか構造化出力を使う［D-platform-prompting-best-practices］

## 使わないもの

- 使わない：`temperature`・`top_p`・`top_k`（代わりに指示文で調整する）。APIバージョン `2026-10-21` では、どのモデルでも400。それより前のAPIバージョンでも、4.7以降のモデルは既定以外の値で400［D-platform-api-versioning、D-platform-model-deprecations、D-platform-working-with-messages］
- 使わない：assistant メッセージ末尾のプリフィル（代わりに構造化出力かシステムプロンプトの指示）。4.6以降のモデルで400。会話の途中に assistant メッセージを入れることは影響を受けない［D-platform-working-with-messages、D-platform-prompting-best-practices］
- 使わない：`thinking` の `budget_tokens`（代わりに effort。上限は `max_tokens` で切る）。4.7以降のモデルで400、Opus 4.6 と Sonnet 4.6 では非推奨［D-platform-prompting-best-practices、D-platform-models-overview］
- 使わない：`claude-fable-5-2`・`claude-mythos-5-2` での `thinking: {type: "disabled"}`（代わりに effort を下げる）。400［D-platform-fable-5-2-migration］
- 使わない：`claude-fable-5-2`・`claude-mythos-5-2` での `tool_choice` の `{type: "any"}`・`{type: "tool", name: "..."}`（代わりに `{type: "auto"}`）。400［D-platform-fable-5-2-migration］
- 使わない：`claude-sonnet-4-5-20250929`（代わりに `claude-sonnet-5-5`）。非推奨で、提供終了は2026年11月30日［D-platform-model-deprecations］
- 使わない：日付なしの `claude-sonnet-4-5`（代わりに `claude-sonnet-5-5`）。日付つきIDと同じ2026年11月30日に提供終了。提供終了後、Claude Code は `There's an issue with the selected model` で始まるエラーを出す。フォールバックのモデル列を設定していれば次のモデルへ切り替わる［A-2026-11-19-16］
- 使わない：`claude-mythos-preview`（非推奨。提供終了日は未発表）［D-platform-model-deprecations］
- 使わない：提供終了のモデル。`claude-opus-4-1-20250805`・`claude-opus-4-20250514`（代わりに `claude-opus-4-8`）、`claude-sonnet-4-20250514`・`claude-3-7-sonnet-20250219`（代わりに `claude-sonnet-5-5`）、`claude-3-5-haiku-20241022`・`claude-3-haiku-20240307`（代わりに `claude-haiku-4-5-20251001`）［D-platform-model-deprecations］
- 使わない：`--enable-auto-mode`（代わりに `--permission-mode auto`）。v2.1.111 で削除［D-claude-code-cli-reference］
- 使わない：`--remote`（代わりに `--cloud`）。非推奨の別名［D-claude-code-cli-reference］
- 使わない：`.claude/commands/` への新規作成（代わりにスキル）。古い形式で、既存のファイルは動き続ける［D-claude-code-skills］
- 使わない：指示文での大文字・IMPORTANT の強調、「最後までやれ」「怠けるな」の念押し（代わりに、曲げられない決まりはフックか deny ルール、完了は確認手段で担保する）［D-claude-code-best-practices］
