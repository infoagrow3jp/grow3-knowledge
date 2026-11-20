# gpt-usage の詳細

## 通常の呼び出し

### Codex CLI の非対話実行

- 非対話実行は `codex exec "指示"`（短縮形 `codex e`）を使う。［D-codex-non-interactive、D-codex-cli-reference］
- 実行中の経過は stderr に流れ、stdout には最終メッセージだけが出るので、そのままパイプやリダイレクトで受け取れる。［D-codex-non-interactive］
- 既定のサンドボックスは読み取り専用で、編集を許すなら `--sandbox workspace-write`、さらに広げるなら `--sandbox danger-full-access` を付ける。［D-codex-non-interactive］
- `danger-full-access` は隔離された CI ランナーやコンテナなど、管理された環境でだけ使う。［D-codex-non-interactive］
- Git リポジトリの中で実行することが求められ、外で実行するなら `--skip-git-repo-check` で確認を外す。［D-codex-non-interactive］
- 指示の引数を省くと stdin から指示を読む。明示するなら `codex exec -` と書く。［D-codex-non-interactive］
- 指示の引数と stdin のパイプを両方渡すと、引数が指示、パイプの内容が追加の文脈として扱われる。［D-codex-non-interactive］
- 認証は保存済みの CLI 認証を使い回す。1回の実行だけ別の API キーを使うなら `CODEX_API_KEY=<api-key> codex exec …` と実行単位で渡す。［D-codex-non-interactive］
- `OPENAI_API_KEY`・`CODEX_API_KEY` を、リポジトリ側のコードを実行するジョブ全体の環境変数に置かない。［D-codex-non-interactive］
- GitHub Actions では CLI を自分で入れずに Codex GitHub Action（`openai/codex-action`）を使う。［D-codex-non-interactive］
- 必須（`required = true`）の MCP サーバーが初期化に失敗すると、`codex exec` はエラーで終了する。［D-codex-non-interactive］
- 既存の app server 上で非対話セッションを開始・再開するには `codex exec --remote <ADDR>`〔v0.171.0以降〕。［O-2026-11-20-7］

`codex exec` の主なオプション（公式のオプション表にあるもの）：

- `--model, -m`：この実行で使うモデルを指定する。［D-codex-cli-reference］
- `--sandbox, -s`：`read-only`・`workspace-write`・`danger-full-access` のいずれか。［D-codex-cli-reference］
- `--cd, -C`：作業の起点にするフォルダを指定する。［D-codex-cli-reference］
- `--profile, -p`：`$CODEX_HOME/<名前>.config.toml` をユーザー設定に重ねる。［D-codex-cli-reference］
- `--config, -c key=value`：設定値をその実行だけ上書きする（繰り返し可。値は TOML として解釈され、できなければ文字列になる）。［D-codex-cli-reference］
- `--image, -i`：最初のメッセージに画像を添付する。［D-codex-cli-reference］
- `--json`：整形テキストの代わりに JSON Lines のイベントを出す。［D-codex-cli-reference］
- `--output-last-message, -o <パス>`：最終メッセージをファイルに書く。［D-codex-cli-reference］
- `--output-schema <パス>`：最終応答の JSON Schema を指定する。［D-codex-cli-reference］
- `--ephemeral`：セッションの記録ファイルをディスクに残さない。［D-codex-cli-reference］
- `--skip-git-repo-check`：Git リポジトリの外での実行を許す。［D-codex-cli-reference］
- `--trust`：このプロジェクトへの信頼を保存する（`--ignore-user-config` とは併用できない）。［D-codex-cli-reference］
- `--ignore-user-config`：`$CODEX_HOME/config.toml` を読まない（認証は `CODEX_HOME` を使う）。［D-codex-cli-reference］
- `--ignore-rules`：ユーザーとプロジェクトの `.rules` ファイルを読まない。［D-codex-cli-reference］
- `--worktree`：新しい実行を管理された Git worktree で行う（`resume`・`--ephemeral`・`--ignore-user-config` とは併用できない）。［D-codex-cli-reference］
- `--approve-for-me`：`on-request` の承認を自動審査に回し、`workspace-write` で動かす（`--sandbox`・`--yolo` とは併用できない）。［D-codex-cli-reference］
- `--dangerously-bypass-approvals-and-sandbox, --yolo`：承認もサンドボックスも外す。隔離されたランナーの中でだけ使う。［D-codex-cli-reference］
- `codex exec` のオプション表に `--ask-for-approval` は載っていない（`codex` 本体の全体オプションには `--ask-for-approval, -a` が `on-request | never` で載っている）。［D-codex-cli-reference］

### OpenAI API（Responses API・SDK）

- 新規の実装には Responses API が推奨されている（Chat Completions はサポートが続いている）。［D-api-migrate-responses］
- 最新のモデルは Responses API と公式 SDK から使える。［D-api-models］
- SDK の導入は `npm install openai` または `pip install openai`。［D-api-quickstart］
- 各 SDK は環境変数 `OPENAI_API_KEY` から API キーを自動で読む。［D-api-quickstart］
- エンドポイントは `POST /responses`（curl の例では `https://api.openai.com/v1/responses` に `Content-Type: application/json` と `Authorization: Bearer $OPENAI_API_KEY` を付ける）。［D-api-responses-create、D-api-text］
- 最小の形は `model` と `input` の2つで、生成された文章は SDK の `output_text` で受け取る。［O-2026-11-19-15］

Python の最小の形（公式の例。モデルIDは用途に合わせて選ぶ）：

```python
from openai import OpenAI
client = OpenAI()
response = client.responses.create(
    model="gpt-6.2-astra",
    input="Write a one-sentence bedtime story about a unicorn.",
)
print(response.output_text)
```

- `output` 配列には文章のほかにツール呼び出しや推論の項目が入ることがあり、文章が `output[0].content[0].text` にあると決めてかかるのは安全でない。［D-api-text］
- 推論・ツール・マルチモーダルの出力を扱う流れでは、`response.output` を順に見て、項目ごとに `type` で処理を分ける。［D-api-migrate-responses］
- 応答は既定で保存される（`store` の既定は true）。保存しないなら `store: false` を指定する。［D-api-responses-create、D-api-migrate-responses］

## モデルの選び方

- API で迷ったら `gpt-6.2-astra`（複雑な推論とコーディング向けの旗艦）、知能とコストの釣り合いなら `gpt-6.2-sol`、コスト重視の大量処理なら `gpt-6-luna` が案内されている。［O-2026-11-19-16］
- `gpt-6.2-astra` は最も難しい仕事を最初から最後まで、`gpt-6.2-sol` は日常の作業からエージェントの大規模運用までを担うモデルとして案内されている。両方とも Responses API と Chat Completions に対応するが、ツール呼び出しには Responses API が要る。［O-2026-11-17-73］
- `gpt-6.1-terra` は視覚的な推論・コンピューター操作・自然な文章向けの、速く効率的なモデル。［O-2026-11-19-16］
- `gpt-6.1-sol`（Astra に近い性能を低コストで）と `gpt-6-sol` は、モデル一覧の全カタログに載っている。［O-2026-11-19-16］
- Codex での案内：最難度の一連の作業は GPT-6.2 Astra（または GPT-6 Astra）、日常のコーディング・文章・複数資料にまたがる作業は GPT-6.2 Sol、日常の文章と視覚的な作業は GPT-6.1 Terra、良い結果の形が分かっている定型・大量の作業は Luna。［O-2026-11-19-14］
- Codex CLI では起動時に `--model`（`-m`）で指定し、非対話実行でも `codex exec -m gpt-6.2-sol "…"` のように同じ指定が使える。［O-2026-11-19-14］
- GPT-6.2 Astra・GPT-6.2 Sol は Codex でコンテキストウィンドウを最大 100 万トークンまで使える（`config.toml` の `model_context_window` で設定する）。［O-2026-11-19-14］
- Responses API の公開ベータで、バックグラウンド完了の猶予を2時間か8時間から選べる。対象は `gpt-6.2-astra`・`gpt-6.2-sol`・`gpt-6.1-terra`・`gpt-6-luna` で、トークン単価は Standard より2時間枠で 30%、8時間枠で 40% 低い。［O-2026-11-17-72］
- `gpt-6.2-astra`・`gpt-6.2-sol` は Flex（`service_tier: flex`）に対応しない。［O-2026-11-19-3］
- `gpt-6.2-astra`・`gpt-6.2-sol` は Ultrafast に対応する（公開時点）。データ所在地の指定は、US・EU が Standard・Fast・Batch、Ultrafast は US のみ。［O-2026-11-19-5、O-2026-11-19-3］
- `gpt-6.2-astra`・`gpt-6.2-sol` は Chat Completions でも使えるが、ツール呼び出しには Responses API が要る。［O-2026-11-19-3］
- `gpt-6.1-terra` を Codex CLI で使うには 0.159.0 以降が要る。［D-codex-models］
- Codex CLI 0.171.0 で、GPT-6.2 Sol・Astra がモデルカタログに加わり、Sol がカタログの既定の選択になった。［O-2026-11-20-7］
- 既定のモデルは `config.toml` の `model` で決まり、指定がなければ推奨モデルが使われる。［D-codex-models］
- API キーで認証した Codex では、使えるモデルは API の組織とプロジェクトに従う。［D-codex-models］
- 独自のモデルプロバイダーやゲートウェイを使うなら、Responses API 互換のエンドポイントにする（`wire_api` で使える値は `responses` だけ）。［D-codex-models、D-codex-config-reference］
- 本番のアプリでは、挙動をそろえるためにモデルのスナップショットに固定し、プロンプトの挙動を測るテストを用意することが勧められている。［D-api-text］

推論の強さ：

- API では `reasoning.effort`（Responses）で指定する。値はモデルごとに異なり、`none`・`minimal`・`low`・`medium`・`high`・`xhigh`・`max` がありうる。［D-api-reasoning］
- `gpt-6.2-astra`・`gpt-6.2-sol` は `reasoning.effort`（Responses）・`reasoning_effort`（Chat Completions）が `none` のリクエストを拒否する。［O-2026-11-19-20］
- `gpt-6-astra` は `none` に対応せず、`none` を指定すると HTTP 400 になる。［D-api-reasoning］
- `gpt-6.1-sol` は `none` と `minimal` に対応せず、既定は `medium`。［D-api-reasoning］
- `gpt-6.1-terra`・`gpt-6-sol`・`gpt-6-luna` は `none` に対応する。［D-api-gpt6-guide］
- `gpt-6.1-sol`・`gpt-6-sol`・`gpt-6-luna` は、`reasoning.effort` を省くと `medium` になる。［D-api-reasoning］
- 既存のリクエストが `minimal` を使っているなら、`low` から始めて代表的なタスクで比べる。［D-api-gpt6-guide］
- `gpt-6.2-astra`・`gpt-6.2-sol` を新規に使うなら `medium` から始める。`none` か `minimal` を使っていた呼び出しは `low` にする。［O-2026-11-19-3］
- `gpt-6.2-astra`・`gpt-6.2-sol` では、Chat Completions でも `temperature`・`top_p`・`logprobs`・`top_logprobs` を省く（Responses では `temperature`・`top_p`・`top_logprobs` を省き、`include` から `message.output_text.logprobs` を外す）。［O-2026-11-19-3］
- 推論の強さが `none` 以外のときは `temperature`・`top_p`・`top_logprobs` を外す（Responses では `include` から `message.output_text.logprobs` も外す）。［D-api-gpt6-guide］
- `reasoning.mode` は `standard`（既定）と `pro` があり、推論の強さとは独立している。［D-api-reasoning］
- `reasoning.effort` は品質を取り戻す主な手段ではなく、調整のつまみとして扱う。［D-api-reasoning］
- Codex では `config.toml` の `model_reasoning_effort` で指定する。値は `low`・`medium`・`high`・`xhigh`・`max`・`ultra` などで、使える段階はモデルとクライアントによる。［D-codex-config-reference］
- Codex での出発点は、GPT-6.2 Astra・GPT-6.2 Sol ならクライアントが選ぶ強さ、Luna なら `high`、GPT-6 Astra なら `low`。［O-2026-11-19-14、D-codex-subagents］
- 推論の強さの段階は、モデルの世代をまたいでそのまま対応するわけではない。慣れたタスクを低めの設定で試して調整する。［D-codex-models］
- GPT-6 Luna は Max までで、Ultra には対応しない。［D-codex-models］

## 指示の書き方

### Codex への指示

- 大きめの作業では、目的（何をするか）・文脈（どの情報が役立つか）・出力（形式・長さ・細かさ）・境界（変えてはいけないもの、避けること、実行前に確認すること）のうち、効くものだけを書く。［D-codex-prompting］
- 手順の細かな一覧ではなく、ほしい結果から書く。手順そのものが大事なときだけ手順を書く。［D-codex-prompting］
- 境界は、間違うと結果が使えなくなる1〜2点に絞る。［D-codex-prompting］
- Codex への良い指示は、求める挙動を名指しし、関係するコードや再現手順を示し、大事な制約を守らせ、変更の確かめ方を伝える。［D-codex-prompting］
- IDE 拡張は開いているファイルを自動で文脈に入れるが、CLI ではパスを明示する。［D-codex-prompting］
- 大事な作業では、最後の確認（たとえば全項目に担当と期限があるか）を指示に含める。［D-codex-prompting］

GPT-6.2 を Codex で使うときの公式の書き方：

- 同僚に頼む調子で書き、成果をレビューするときに何を見るかを伝える。［O-2026-11-19-6］
- 推論の強さは作業の深さに合わせる：簡単な調査は Medium、1つの原因を複数のシステムにわたって追うなら High、複数の原因が絡むなら Extra High。［O-2026-11-19-6］
- 完了条件と、網羅してほしい箇所を伝える。［O-2026-11-19-6］
- 並列にしたい作業には「必要に応じてサブエージェントを使う」と書く。繰り返し使う指示は、適用条件とともにスキルか `AGENTS.md` に書く。Ultra では Codex が自分でサブエージェントを投入するかを判断する。［O-2026-11-19-6］
- `AGENTS.md` は簡潔にし、コードやドキュメントから推測できないプロジェクトの要件・規約・必須の流れだけを書く。［O-2026-11-19-6］
- 複数のエージェントが同じマシンを使うときは、ビルドとテストの同時実行数に配慮させ、終わるときにバックグラウンドのジョブと一時ファイルを片付けさせる。［O-2026-11-19-6］
- API では、既定の出力がより簡潔・直接的になるので、既存の「簡潔に」系の指示を見直す。意図が不明だと次の一手を提案して確認待ちになることがあるので、長い作業では妥当で後から戻せる仮定を置いて進め、その仮定を述べるよう書く。［O-2026-11-19-3］

### API のプロンプト

- `instructions` は、口調・目的・正しい応答の例など、その応答での振る舞いへの指示を渡すもので、`input` の内容より優先される。［O-2026-11-19-19］
- 複数のターンで使い回す指示は、`input` の最初の `developer` メッセージに置く。その回だけの指示は `instructions` に置く。［O-2026-11-19-19、O-2026-11-19-18］
- `developer` メッセージは規則と業務ロジック、`user` メッセージはそれに適用される入力、という分担で考える。［O-2026-11-19-19］
- 推論モデルには、課題・制約・ほしい出力形式を渡し、途中の手順を一つひとつ指定しない。［D-api-reasoning］
- エージェント的な作業や調査の多い作業では、何をもって完了とするかと、モデルが自分の作業をどう確かめるかを定める。［D-api-reasoning］
- 本番のプロンプトはアプリのコードの中に置き、生成した `instructions` と `input` を Responses API に直接渡す。［D-api-text］

### GPT-6 Astra の傾向と対処

- 追加の入力で結果が大きく変わりうるときに質問を返しやすく、利用者が「妥当な仮定を置いて進めてほしい」場面で止まることがある。意図と範囲を文脈から推し量り、完了まで進めるよう指示する。［D-api-gpt6-guide］
- 確認を求めるのは、具体的で見直せる結果を用意した後にするよう指示すると、作業の前で止まるのを避けられる。［D-api-gpt6-guide］
- 指示への追従が強く、スキルや `AGENTS.md` などのファイルに含まれる指示に敏感。モデルが読めるスキルやファイルの指示を点検することが強く勧められている。［D-api-gpt6-guide］
- スキルの中のあいまいな記述や矛盾する記述で、早い段階で止まることがある。利用者の指示がスキルの指針より優先することを明示する。［D-api-gpt6-guide］
- 一覧・表・Markdown を多用する傾向がある。文章中心の出力がほしいなら、文体と構成を指定する。［D-api-gpt6-guide］
- サブエージェントへの委任が期待より少ないことがある。いつ、どの程度並列に委任するかを指定する。［D-api-gpt6-guide］
- コーディングでは完了前のテストが手厚くなりがちで、小さな変更では必要以上に広がる。変更に見合うテストの範囲を指定する。［D-api-gpt6-guide］

## 指示ファイル・スキル

### AGENTS.md

- Codex は作業の前に `AGENTS.md` を読む。指示の連なりは実行ごとに1回組み立てられる。［D-codex-agents-md］
- まず Codex のホーム（既定は `~/.codex`、`CODEX_HOME` で変更可）で `AGENTS.override.md`、なければ `AGENTS.md` を読む。［D-codex-agents-md］
- 次にプロジェクトのルート（通常は Git のルート）から現在のフォルダまでを順にたどり、各フォルダで `AGENTS.override.md`、`AGENTS.md`、`project_doc_fallback_filenames` の名前の順に探して、1フォルダにつき1ファイルまで取り込む。［D-codex-agents-md］
- ファイルはルート側から順に連結され、現在のフォルダに近いものが後ろに来るので優先される。［D-codex-agents-md］
- 空のファイルは飛ばされ、合計が `project_doc_max_bytes`（既定 32 KiB）に達するとそれ以上は追加されない。上限を上げるか、下位のフォルダに分けて置く。［D-codex-agents-md］
- 探索は現在のフォルダで止まるので、上書きの指示は対象の作業に近い場所に置く。［D-codex-agents-md］
- 指示が古く見えるときは、対象のフォルダで Codex を起動し直す（実行ごとに組み立て直すので、消すべきキャッシュはない）。［D-codex-agents-md］

### 設定ファイル（config.toml）

- ユーザー設定は `~/.codex/config.toml`、プロジェクトごとの上書きは `.codex/config.toml`。プロジェクト側は、そのプロジェクトを信頼したときだけ読まれる。［D-codex-config-basic］
- 優先順位は高い順に、CLI のフラグと `--config` の上書き、プロジェクトの設定（現在のフォルダに近いほうが優先）、`--profile` で選んだプロファイル、ユーザー設定、クラウド管理の既定、システム設定、組み込みの既定。［D-codex-config-basic］
- 信頼していないプロジェクトでは、プロジェクトの `.codex/` の層（設定・フック・ルール）が飛ばされる。ユーザーとシステムの設定は読まれる。［D-codex-config-basic］
- `codex exec` と `codex review` は、書き込み可能なサンドボックスでも、信頼済みのプロジェクトでだけプロジェクトの設定とプロジェクト定義の MCP サーバーを読む。`--trust` で信頼を保存できる。［D-codex-non-interactive］
- プロジェクト側の `.codex/config.toml` に書いても無視されるキーがある（`model_provider`・`model_providers`・`profile`・`notify`・`otel` など）。これらはユーザー設定に置く。［D-codex-config-reference］
- よく変える項目は `model`、`approval_policy`、`sandbox_mode`、`web_search`、`model_reasoning_effort`。［D-codex-config-basic］
- `--strict-config` を付けると、`config.toml` の未知のキーがエラーになる。付けなければ無視される。［O-2026-11-20-1］
- 有効なモデル・承認方針・トークン使用量は `/status`、設定の層の優先順は `/debug-config` で確かめられる。［O-2026-11-20-1］
- ChatGPT Work のチャットは管理された環境で動き、手元の Codex の設定ファイルを読まない。［O-2026-11-20-1］
- 管理された端末では、組織が `requirements.toml` で制約をかけていることがある（たとえば `approval_policy = "never"` や `sandbox_mode = "danger-full-access"` の禁止）。［D-codex-config-basic］

### スキル

- スキルは `SKILL.md` を持つフォルダで、`SKILL.md` には `name` と `description` が必須。［D-codex-skills］
- Codex は最初に各スキルの名前・説明・ファイルパスだけを読み、使うと決めたときに `SKILL.md` の全文を読む。［D-codex-skills］
- 最初の一覧に使う量は、既定でコンテキストウィンドウの 2% まで。スキルが多いと説明文が先に短くされ、一部が一覧から省かれることがある。［D-codex-skills］
- 暗黙の起動は `description` との一致で決まるので、主な用途とトリガー語を説明文の先頭に置く。［D-codex-skills］
- 明示的に呼ぶには、Codex CLI では `/skills` を実行するか、`$` でスキルを名指しする。［D-codex-skills］
- リポジトリのスキルは、現在のフォルダからリポジトリのルートまでの各フォルダの `.agents/skills` から読まれる。利用者個人のものは `$HOME/.agents/skills`、管理者のものは `/etc/codex/skills`。［D-codex-skills］
- スキルの変更は自動で検知される。反映されないときは Codex を起動し直す。［D-codex-skills］
- スキルを消さずに止めるには、`~/.codex/config.toml` に `[[skills.config]]` を書いて `enabled = false` にする。［D-codex-skills］
- `agents/openai.yaml` で `allow_implicit_invocation: false` にすると暗黙には起動されず、`$skill` の明示的な呼び出しだけが効く。［D-codex-skills］

### サブエージェント

- 現行の Codex ではサブエージェントの仕組みが既定で有効。起動するのは、直接頼んだときか、該当する `AGENTS.md` やスキルの指示が委任を求めているとき。［D-codex-subagents］
- 良い指示は、作業の分け方、全員の完了を待つかどうか、返してほしい要約や出力を説明する。［D-codex-subagents］
- サブエージェントはそれぞれモデルとツールを使うので、単独の実行よりトークンを多く使う。［D-codex-subagents］
- 並列化は、探索・テスト・切り分け・要約のような読み取り中心の作業から始める。書き込み中心の並列作業は衝突しやすいので慎重に扱う。［D-codex-subagents］
- サブエージェントは親のサンドボックスと承認の設定を引き継ぐ。カスタムエージェントのファイルではこれを置き換えられない。［D-codex-subagents］
- 非対話の流れなど、新しい承認を表示できない実行では、新たな承認が要る操作は失敗し、エラーが親に返る。［D-codex-subagents］
- モデルや推論の強さを指定しなければ、親のものを引き継ぐ。［D-codex-subagents］
- 組み込みのエージェントは `default`・`worker`・`explorer`。［D-codex-subagents］
- カスタムエージェントは `~/.codex/agents/`（個人用）か `.codex/agents/`（プロジェクト用）に TOML ファイルを1つずつ置き、`name`・`description`・`developer_instructions` を必ず定義する。［D-codex-subagents］
- 全体の設定は `config.toml` の `[agents]`（`agents.enabled`、`agents.max_concurrent_threads_per_session`、`agents.default_subagent_model`、`agents.default_subagent_reasoning_effort`）。［D-codex-subagents］

## 操作別の注意

### セッションの再開（Codex）

- 前の実行の続きは `codex exec resume --last "指示"`、セッションを指定するなら `codex exec resume <SESSION_ID>`。［D-codex-non-interactive］
- `--last` は現在の作業フォルダの直近のセッションを選ぶ。ほかのフォルダのセッションも対象にするなら `--all` を足す。［D-codex-cli-reference］
- `codex exec fork <SESSION_ID> [PROMPT]` は保存済みのセッションを新しいセッションに複製する。指示なしだと、ターンを始めずに複製だけ作る。［D-codex-cli-reference］
- 画像、`--output-schema`、`--output-last-message`、`--ephemeral` を使うときは指示が必須。［D-codex-cli-reference］

### 承認とサンドボックス（Codex）

- サンドボックスは技術的にできること（書ける場所、ネットワーク）を決め、承認方針は実行前に止まって確認する場面を決める。2つは別の仕組み。［D-codex-approvals］
- サンドボックスのモードは `read-only`・`workspace-write`・`danger-full-access` の3つ。［D-codex-config-reference］
- 承認方針（`approval_policy`）は `on-request`・`never`・`granular` の指定。対話的な実行には `on-request`、非対話の実行には `never` を使う。［D-codex-config-reference］
- 設定キーは `-c key=value` で実行ごとに上書きできるので、承認方針も `approval_policy` のキーで渡せる。［D-codex-cli-reference、D-codex-config-reference］
- 承認の確認を出さない指定は、どのサンドボックスのモードとも組み合わせられる。Codex は与えられた制約の中でできる範囲を行う。［D-codex-approvals］
- 非対話の実行には `codex exec --sandbox workspace-write` を使う。［D-codex-approvals］
- `workspace-write` では、設定で有効にしない限りネットワークは切れている。有効にするには `[sandbox_workspace_write]` の `network_access = true`、1回だけなら `-c 'sandbox_workspace_write.network_access=true'`。［D-codex-approvals］
- `workspace-write` でも、書き込み可能な場所の中の `.git`、`.agents`、`.codex`、`.aws` は読み取り専用で守られ、その配下もすべて読み取り専用。［D-codex-approvals］
- 作業フォルダには、現在のフォルダと `/tmp` のような一時フォルダが含まれる。［D-codex-approvals］
- 書き込み先を増やしたいときは、`--sandbox danger-full-access` にするより `--add-dir` を使う。［D-codex-cli-reference］
- 承認を自動審査に回すには `approvals_reviewer = "auto_review"`。審査されるのは承認が要る操作だけで、サンドボックスの境界は変わらない。［D-codex-approvals］
- `--dangerously-bypass-approvals-and-sandbox`（別名 `--yolo`）はサンドボックスも承認もなくす指定で、推奨されていない。［D-codex-approvals］
- Web 検索は既定でキャッシュ（`web_search = "cached"`）から返る。最新のページを取りに行くなら `--search`（`web_search = "live"`）。［D-codex-config-basic、D-codex-cli-reference］
- WSL2 では Linux のサンドボックス実装が使われる。WSL1 は 0.115 以降で非対応。［D-codex-approvals］

### 出力形式（Codex）

- `--json` を付けると stdout が JSON Lines になり、`thread.started`・`turn.started`・`turn.completed`・`turn.failed`・`item.*`・`error` のイベントが流れる。［D-codex-non-interactive］
- 最終メッセージだけが要るなら `-o <パス>`（`--output-last-message`）。ファイルに書きつつ stdout にも出る。［D-codex-non-interactive］
- 後続の処理で決まった項目が要るなら `--output-schema <schema.json>` で、最終応答を JSON Schema に従わせる。［D-codex-non-interactive］
- CI では `--json` と `--output-last-message` を組み合わせると、機械可読の経過と最終の要約の両方が取れる。［D-codex-cli-reference］

### 会話の継続と状態（API）

- 前の応答の続きは `previous_response_id` で指定する。前の応答の `instructions` は引き継がれない。連なり全体の指示は、最初のリクエストの `input` の先頭の `developer` メッセージに置くと、後続の応答に引き継がれる。［O-2026-11-19-17、O-2026-11-19-18］
- GPT-6.2 以降は、推論の項目より前の内容を挿入・編集する（例：過去のツール結果を書き換える）と、その推論の項目が捨てられる（`prefix_mismatch`）。項目を丸ごと削除するだけ、または推論の項目より後ろに追記するだけでは、この理由では捨てられない。［O-2026-11-19-20］
- GPT-6.2 以降は、Responses API の `tools`・`text.format` を途中で変えても、その後ろの推論の項目が捨てられる。変更は追記で行う：ツールの追加は `additional_tools` の項目、出力の形や推論の強さの変更は `configuration_update` の項目を `input` の末尾に足し、リクエスト単位の設定は元のまま保つ。ツールを絞るなら `tool_choice` と `allowed_tools`。［O-2026-11-19-2］
- GPT-6.2 より前のモデルでは `instructions` を変えると先頭が変わり、キャッシュが切れる。過去の `input` の項目の編集、ツール結果や古いターンの縮小・要約への置き換えも同様。縮める必要があるなら compaction を使うか、最初に送る前に縮める。［O-2026-11-19-2］
- OpenAI の compaction（`/responses/compact`、`context_management`）では後続の推論の項目が残る。`/responses/compact` を呼ぶときは `instructions` を省き、返った内容を元の順序で次のリクエストに渡す。独自の compaction では、圧縮した項目を直近のターンの前ではなく文脈の末尾に置く。［O-2026-11-19-2］
- 先頭の変更によるキャッシュ切れは `prompt_cache_options.comparison_response_id`（Prompt Cache Diagnostics）で調べられる。［O-2026-11-19-2］
- GPT-6.2 以降は、推論の項目を作ったリクエストと再利用するリクエストで `safety_identifier` が違うと、その項目が捨てられる（`end_user_mismatch`）。片方にだけ付けた場合も含む。両方に同じ値を付けるか、両方とも付けなければ通る。［O-2026-11-19-20］
- 推論の項目が意図せず捨てられたかは、応答の `input_transformations` で確かめられる。ほかの理由は `model_mismatch`・`organization_mismatch`・`turn_boundary`。［O-2026-11-19-20］
- `previous_response_id` は `conversation` と一緒には使えない。［D-api-responses-create］
- `previous_response_id` を使っても、連なりの中のそれまでの入力トークンは入力として課金される。［D-api-migrate-responses］
- 状態を持たせない（`store: false`、または Zero Data Retention の組織）ときは、返ってきた推論の項目をすべて保持して次のリクエストで送り返す。推論の項目には既定で `encrypted_content` が含まれる。［D-api-migrate-responses、D-api-reasoning］
- 文脈を自分で引き回すときに、推論・関数呼び出し・関数呼び出し結果の項目を落とさない。関数の結果には対応する `call_id` を付ける。［D-api-migrate-responses］
- 推論の強さを途中で変えるときは `configuration_update` の入力項目を使い、リクエスト単位の `reasoning.effort` は変えない（プロンプトの先頭部分のキャッシュを保つため）。［D-api-gpt6-guide］

### 出力の長さと形式（API）

- `max_output_tokens` は、見える出力と推論トークンを合わせた上限。［D-api-responses-create］
- 上限やコンテキストウィンドウに達すると `status` が `incomplete`、`incomplete_details` の `reason` が `max_output_tokens` の応答が返る。見える出力が1つも出ないうちに起きることがある。［D-api-reasoning］
- 試し始めの段階では、推論と出力のために少なくとも 25,000 トークンを確保することが勧められている。［D-api-reasoning］
- 構造化出力は、Responses では `response_format` ではなく `text.format` で指定する。［D-api-migrate-responses］
- Responses では関数定義の `strict` を省くと strict モードが試みられる。非 strict の挙動を保つなら `strict: false` を明示する。［D-api-migrate-responses］
- ストリーミングは、Chat Completions のチャンク処理を使い回さず、型のついた Responses のイベントを処理する。［D-api-migrate-responses］
- ツール呼び出しは Responses API で行う。`gpt-6-astra`・`gpt-6.1-sol`・`gpt-6.1-terra` は Chat Completions にも対応するが、ツール呼び出しには Responses が要る。［D-api-gpt6-guide］

## 使わないもの

### Codex

- 使わない：`codex exec --full-auto`（サポート終了。代わりに `--sandbox workspace-write`、自動審査つきなら `--approve-for-me`）。［D-codex-non-interactive］
- 使わない：`approval_policy = "untrusted"`（非対応で、残っているとクライアントが起動できないことがある。代わりに `on-request` か `never`。厳しい承認を保つならユーザー設定の `[projects."<パス>"]` に `trust_level = "untrusted"`）。［D-codex-approvals］
- 使わない：`approval_policy = "on-failure"`（非推奨。代わりに `on-request` か `never`）。［D-codex-config-reference］
- 使わない：`wire_api = "chat"` と Chat Completions 専用のエンドポイント（現行の Codex は非対応。代わりに Responses API 互換のエンドポイント）。［D-codex-models］
- 使わない：ChatGPT サインインの Codex での `gpt-5.5`（代わりに `gpt-6.1-sol`、Free・Go プランは `gpt-6-luna`）。［D-codex-models］
- 使わない：ChatGPT サインインの Codex での `gpt-5.4`・`gpt-5.4-mini`（代わりに `gpt-6-sol`・`gpt-6-luna`）。［D-codex-models］
- 使わない：`gpt-5.3-codex-spark`（提供終了。代わりに現行の推奨モデル）。［D-codex-models］
- 使わない：ChatGPT サインインの Codex での `gpt-5.2`・`gpt-5.3-codex`（非推奨。代わりに現行の推奨モデル）。［D-codex-models］
- 使わない：`[features]` の `web_search`・`web_search_cached`・`web_search_request`（非推奨。代わりに最上位の `web_search` 設定）。［D-codex-config-basic］
- 使わない：`personality` の `friendly`・`pragmatic` と `/personality` コマンド（効かない。組み込みの性格指示を外すなら `personality = "none"`）。［D-codex-config-basic］

### API

- 使わない：新規実装での Chat Completions（代わりに Responses API。サポート自体は続いている）。［D-api-migrate-responses］
- 使わない：Assistants API（2026-08-26 に停止。代わりに Responses API と Conversations API）。［D-api-deprecations］
- 使わない：`/v1/prompts` と再利用プロンプトオブジェクト（2026-11-30 に停止予定。代わりにプロンプトをアプリのコードに置く）。［D-api-deprecations］
- 使わない：Agent Builder（2026-11-30 に停止予定。代わりに Agents SDK か ChatGPT Workspace Agents）。［D-api-deprecations］
- 使わない：`prompt_cache_retention`（GPT-5.5 以前からの移行時。代わりに `prompt_cache_options.ttl`）。［D-api-gpt6-guide］
- 使わない：`gpt-5`・`o3`（2026-12-11 に停止予定。代わりに `gpt-6.1-sol`）。［D-api-deprecations］
- 使わない：`gpt-5-mini`（2026-12-11 に停止予定。代わりに `gpt-6.1-terra`）。［D-api-deprecations］
- 使わない：`gpt-5-nano`（2026-12-11 に停止予定。代わりに `gpt-6-luna`）。［D-api-deprecations］
- 使わない：`gpt-5-pro`・`o3-pro`（2026-12-11 に停止予定。代わりに Responses API で `gpt-6.1-sol` に `reasoning.mode: pro`）。［D-api-deprecations］
- 使わない：GPT-4o・GPT-4o mini・GPT-4.1・GPT-4.1 mini の各スナップショット（2027-01-14 に停止予定。代わりに `gpt-6-luna`）。［D-api-deprecations］
- 使わない：`gpt-5.1`・`gpt-5.3-codex`（2027-04-01 に停止予定。代わりに `gpt-6-sol`）。［D-api-deprecations］
- 使わない：`gpt-5.4-nano`（2027-04-01 に停止予定。代わりに `gpt-6-luna`）。［D-api-deprecations］
- 使わない：EU のデータ所在地で `service_tier: fast`・`priority` を付けた `gpt-5.2`・`gpt-5.4`・`gpt-5.4-mini`（2027-01-11 に非推奨。代わりに同じモデルを EU のデータ所在地・Standard（`service_tier: default`）で使うか、GPT-6.2 系）。［O-2026-11-20-3］
- 使わない：停止済みの `gpt-4`・`gpt-4-turbo`・`o1`・`o3-mini`・`gpt-5-codex`・`gpt-5.1-codex`・`gpt-5.2-codex`（一覧上の置き換え先は `gpt-5.6-sol`）。［D-api-deprecations］
- 使わない：停止済みの `gpt-3.5-turbo`・`o4-mini`（一覧上の置き換え先は `gpt-5.6-terra`）。［D-api-deprecations］
