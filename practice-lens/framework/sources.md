# ソース台帳

調査エージェントは、検索の前にこの台帳を読む。台帳にあるURLは直接fetchする。
検索は、台帳で拾えないものを補うときだけ使う。

確認日の欄が空のものは未確認。未確認のURLを根拠に書かない。

---

## 0. 横断（全業種で使う）

| ソース | URL | 信頼度 | 拾う内容 | 確認日 | 備考 |
|---|---|---|---|---|---|
| 職業能力評価基準 策定業種一覧（56業種） | https://www.mhlw.go.jp/stf/newpage_04653.html | 公的 | 業種ページへの入口 | 2026-10-09 | 検索に出ない。必ずここから入る |
| 職業能力評価基準 トップ | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/jinzaikaihatsu/ability_skill/syokunou/index.html | 公的 | レベル区分の考え方（L1〜L4） | 2026-10-09 | |
| ローカルベンチマーク（経産省） | https://www.meti.go.jp/policy/economy/keiei_innovation/sangyokinyu/locaben/sheet.html | 公的 | 商流・業務フロー、4つの視点、現状→将来→ギャップ | 2026-10-09 | 「差別化ポイント」は「こだわっていること」に読み替えて使う |
| 職場のあんぜんサイト（厚労省・労働災害事例） | https://anzeninfo.mhlw.go.jp/ | 公的 | 業種別の事故事例・ヒヤリハット、原因、再発防止 | 2026-10-10 | 事例は業種別・災害別の一覧から入る（例：感電・火災 https://anzeninfo.mhlw.go.jp/hiyari/13.html ）。個別事例は各業種の節に載せる |
| 職業能力評価基準の構成（PDF） | https://www.mhlw.go.jp/content/11800000/001018939.pdf | 公的 | 職種／職務／能力ユニット／能力細目／職務遂行のための基準／必要な知識 の定義 | 2026-10-10 | 4業種の調査役が共通して参照 |

各業種ページには「全体構成」「レベル区分」「人材要件確認表」「能力ユニット（Excel/Word）」が置かれている。
拾う順は、全体構成 → 能力ユニット → レベル区分。

---

## 1. 看板・サイン（個別受注型／製作は反復生産型）

| ソース | URL | 信頼度 | 拾う内容 | 確認日 | 備考 |
|---|---|---|---|---|---|
| 職業能力評価基準 屋外広告業 | https://www.mhlw.go.jp/stf/newpage_09887.html | 公的 | 4職種（企画営業／デザイン設計／製作施工管理／製作施工）、能力ユニット、L1〜L4 | 2026-10-09 | 製作・施工管理は品質原価工程・購買外注・安全衛生の3ユニット。安全衛生は共通ユニットにも入る |
| 職業能力評価基準 広告業 | https://www.mhlw.go.jp/stf/newpage_09059.html | 公的 | 企画・営業側の工程 | 2026-10-09 | 屋外広告業で足りない営業側を補う |
| 職業能力評価基準 ディスプレイ業 | https://www.mhlw.go.jp/stf/newpage_10318.html | 公的 | 空間・展示側の製作・施工 | 2026-10-09 | 大型案件・内装寄りの観点 |
| JOB tag 看板制作 | https://shigoto.mhlw.go.jp/User/Occupation/Detail/344 | 公的 | タスク20項目と実施率、関連資格 | 2026-10-09 | 実施率は「全員やる仕事／人で分かれる仕事」の目安。数値は取得時点のもので更新される（2026-10-09時点：基礎工事68.8%） |
| JOB tag 広告営業 | https://shigoto.mhlw.go.jp/User/Occupation/Detail/61 | 公的 | 受注から回収までの進行管理 | 2026-10-09 | 職業別名に看板広告営業員 |
| JOB tag グラフィックデザイナー | https://shigoto.mhlw.go.jp/User/Occupation/Detail/334 | 公的 | デザイン側のタスク | 2026-10-09 | 職業別名にサインデザイナー |
| 屋外広告士（日広連） | https://nikkoren.or.jp/koukokushi/about-testproject.html | 業界団体 | 試験科目区分（法規・設計・施工・デザイン） | 2026-10-09 | 国が屋外広告の仕事をどう分けているかの枠 |
| 広告美術仕上げ技能士（技能検定） | https://www.mhlw.go.jp/content/11800000/001168038.pdf | 公的 | 1〜3級の学科・実技の範囲（令和2年版。平成16年版 https://www.mhlw.go.jp/file/06-Seisakujouhou-11800000-Shokugyounouryokukaihatsukyoku/118_kokokubijutsu.pdf ） | 2026-10-10 | 採点基準・配点の記載は無い。レベル軸の根拠にはなるが品質判断の線は書かれていない |
| 職業能力評価基準 屋外広告業 レベル区分 | https://www.mhlw.go.jp/content/11800000/000605219.pdf | 公的 | L1〜L4の定義、職務別の呼称、キャリア形成の例 | 2026-10-10 | |
| 屋外広告業 モデル評価シート・モデルカリキュラム（厚労省報道発表別添 2012-05） | https://www.mhlw.go.jp/stf/houdou/2r9852000002bqla-att/2r9852000002bqpo.pdf | 公的 | 4職種（5職務）の職務説明文、デザイン・設計L1の「職務遂行のための基準」、判定目安表、OJT項目 | 2026-10-10 | 屋外広告業で「基準」の原文が読める唯一の資料。p.16〜20 |
| 職業能力評価基準 ディスプレイ業 概要・レベル区分 | https://www.mhlw.go.jp/file/04-Houdouhappyou-11806001-Shokugyounouryokukaihatsukyoku-Nouryokuhyoukaka/0000087056.pdf | 公的 | 製作・施工管理職種の職務説明、「意匠図の策定」の基準（レベル区分 https://www.mhlw.go.jp/content/11800000/000610810.pdf ） | 2026-10-10 | |
| 職業能力評価基準 広告業 レベル区分 | https://www.mhlw.go.jp/content/11800000/000588582.pdf | 公的 | 営業職種のL1〜L4 | 2026-10-10 | |
| 職場のあんぜんサイト ヒヤリ・ハット「吊り看板が落下して、頭に当たりそうになった」 | https://anzeninfo.mhlw.go.jp/hiyari/hiy_0041.html | 公的 | 発生状況のみ | 2026-10-10 | 原因・対策の記載なし |

---

## 2. 電気工事（個別受注型／盤製作等は反復生産型）

| ソース | URL | 信頼度 | 拾う内容 | 確認日 | 備考 |
|---|---|---|---|---|---|
| 職業能力評価基準 電気通信工事業 | https://www.mhlw.go.jp/stf/newpage_09761.html | 公的 | 工事の工程、施工管理、安全 | 2026-10-09 | 「電気工事業」の基準は存在しない。これが最も近い |
| 職業能力評価基準 総合工事業 | https://www.mhlw.go.jp/stf/newpage_09291.html | 公的 | 施工管理、工程・品質・安全・原価、協力会社管理 | 2026-10-09 | 元請・下請の受け渡しの観点はこちらが厚い |
| JOB tag 電気工事士 | https://shigoto.mhlw.go.jp/User/Occupation/Detail/46 | 公的 | タスクと実施率 | 2026-10-09 | |
| JOB tag 電気技術者 | https://shigoto.mhlw.go.jp/User/Occupation/Detail/272 | 公的 | 設計・管理側 | 2026-10-09 | |
| 電気工事士試験（電気技術者試験センター） | https://bilumen.jp/denko2/gino/defect | 公的（転載） | 技能試験「欠陥の判断基準」の項目番号付き転載 | 2026-10-10 | **一次資料 shiken.or.jp はこの環境で取得不可。転載ページで確認。一次資料での再確認が要る（正式Library昇格前に）** |
| 職業能力評価基準 電気通信工事業 レベル区分 | https://www.mhlw.go.jp/content/11800000/001259280.pdf | 公的 | L1〜L4の職種別定義 | 2026-10-10 | 「キャリア形成の例」は本文取得できず |
| 職業能力評価基準 総合工事業 レベル区分 | https://www.mhlw.go.jp/content/11800000/000593899.pdf | 公的 | L1〜L4の総論 | 2026-10-10 | 職務別の記述は取得できず |
| 厚労省 報道発表（2009-03-02）電気通信工事業のモデル評価シート等 | https://www.mhlw.go.jp/houdou/2009/03/h0302-1.html | 公的 | 3職種4職務の整理 | 2026-10-10 | 別紙はExcelで未読 |
| JOB tag 建築施工管理技術者 | https://shigoto.mhlw.go.jp/User/Occupation/Detail/21 | 公的 | 元請側（施工管理）のタスク16項目、下請の選定・工期・工事費調整、変更時の折衝 | 2026-10-10 | 職業別名に設備系の施工管理を含む。元請→下請の境目の一次資料 |
| 国土交通省 電気通信設備工事監督技術基準（案）令和6年3月 | https://www.mlit.go.jp/tec/it/denki/gijyutukijyun/R0603denkouji_kantokugijutu.pdf | 公的 | 段階確認一覧表、「確認」と「把握」の定義、条件変更の確認・通知 | 2026-10-10 | 公共工事の電気通信設備工事の資料。電気工事一般ではない |
| 経済産業省（近畿）令和5年度電気工事業立入検査結果 | https://www.safety-kinki.meti.go.jp/electric/entry/downloadfiles/entry-denkikouji/koujigyoutachiirir5.pdf | 公的 | 電気工事業法が求める事項（主任電気工事士、検査器具、完了後検査、帳簿、無資格請負禁止）と不備10件 | 2026-10-10 | 資格・法令上の役割境界（LENS-005）の根拠 |
| 職場のあんぜんサイト 労働災害「天井裏の空調設備の配線修理中に感電し死亡」 | https://anzeninfo.mhlw.go.jp/jirei/sai_100916.html | 公的 | 発生状況・原因4点・対策4点 | 2026-10-10 | 業種は病院（施設側の電気技師） |
| 職場のあんぜんサイト ヒヤリ・ハット（分電盤・配電盤・受電設備の感電3件） | https://anzeninfo.mhlw.go.jp/hiyari/hiy_0255.html | 公的 | 原因・対策（ほか hiy_0228、hiy_0453） | 2026-10-10 | |

---

## 3. 小売（食品スーパー・菓子店／店舗運営は反復型、催事・予約は個別対応型）

| ソース | URL | 信頼度 | 拾う内容 | 確認日 | 備考 |
|---|---|---|---|---|---|
| 職業能力評価基準 スーパーマーケット業 | https://www.mhlw.go.jp/stf/newpage_08766.html | 公的 | 販売、チェッカー、ストアマネジメント、商品開発・仕入、営業企画 | 2026-10-09 | |
| 職業能力評価基準 専門店業 | https://www.mhlw.go.jp/stf/newpage_09763.html | 公的 | 店舗マネジメント（職種は1つ） | 2026-10-09 | 製造側のユニットは無い。菓子店の製造はJOB tag 和菓子・洋菓子、菓子製造技能検定で補う（各research.mdの0章に候補URL） |
| 職業能力評価基準 外食産業 | https://www.mhlw.go.jp/stf/newpage_08928.html | 公的 | 仕入、在庫・ロス、店舗管理、従業員教育 | 2026-10-09 | 飲食展開時の参照先 |
| JOB tag スーパー店員 | https://shigoto.mhlw.go.jp/User/Occupation/Detail/57 | 公的 | 検品・陳列・補充・接客のタスク | 2026-10-09 | |
| JOB tag スーパー店長 | https://shigoto.mhlw.go.jp/User/Occupation/Detail/55 | 公的 | 発注指示、人員配置、苦情対応、市場調査 | 2026-10-09 | 多店舗化で店長に渡す仕事の一覧として使える |
| JOB tag スーパーレジ係 | https://shigoto.mhlw.go.jp/User/Occupation/Detail/56 | 公的 | レジ・現金管理 | 2026-10-09 | |
| 職業能力評価基準 スーパーマーケット業 導入・活用マニュアル | https://www.mhlw.go.jp/content/11800000/000983688.pdf | 公的 | 販売L1の評価シート記入例（発注・在庫／陳列の基準文）、○△×の判定基準、目線合わせ・甘辛 | 2026-10-10 | 評価の甘辛（retail B-20 保留）の根拠はここ |
| 職業能力評価基準 専門店業 レベル区分 | https://www.mhlw.go.jp/content/11800000/000600490.pdf | 公的 | L1店長代行〜L4上級店長（守・破・離） | 2026-10-10 | |
| 職業能力評価シート 一覧（スーパーマーケット業） | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000093928.html | 公的 | 職務ごとにシートがあるレベル | 2026-10-10 | レベル区分PDF（000945570）とキャリアマップ（000974022）は機械可読テキストが無く未読 |
| JOB tag 和菓子製造、和菓子職人 | https://shigoto.mhlw.go.jp/User/Occupation/Detail/4 | 公的 | タスク15項目、属する産業に小売業 | 2026-10-10 | 専門店業に製造ユニットが無いのを補う |
| JOB tag 洋菓子製造、パティシエ | https://shigoto.mhlw.go.jp/User/Occupation/Detail/3 | 公的 | タスク21項目、生菓子は当日売り切り、繁忙期 | 2026-10-10 | 同上 |
| 菓子製造技能検定 試験科目及びその範囲並びにその細目（厚労省） | https://www.mhlw.go.jp/general/seido/syokunou/ginou/aramashi/dl/syokusyu_071.pdf | 公的 | 1級・2級の学科・実技の範囲（洋菓子／和菓子） | 2026-10-10 | 平成17年2月。採点基準の記載なし |
| 厚労省 第三次産業（小売業・飲食店・社会福祉施設）の労働災害防止資料 | https://www.mhlw.go.jp/content/11300000/001378118.pdf | 公的 | 小売業の災害事例（挽肉機械、惣菜売場の転倒）と原因・対策 | 2026-10-10 | 介護（社会福祉施設）にも使える |
| 長野県小売業SAFEだより 第2号 | https://jsite.mhlw.go.jp/nagano-roudoukyoku/content/contents/kouri-SAFEdayori_vol.2.pdf | 公的 | 転倒・切り傷の事例と原因 | 2026-10-10 | 切り傷の分析は1社の取組。会社名は書かない |
| 農林水産省 食品ロス削減推進の徹底について（R7-06） | https://www.super.or.jp/wp/wp-content/uploads/2025/06/maff20250609.pdf | 公的 | 「適正な発注」（需要予測、リードタイム） | 2026-10-10 | 業界団体サイト掲載 |
| 農林水産省 商慣習見直しに取り組む食品製造・小売事業者の公表 | https://www.maff.go.jp/j/shokusan/recycle/syoku_loss/syokansyu/torikumi2024.html | 公的 | 3分の1ルール、納品期限緩和 | 2026-10-10 | |
| スーパーマーケット白書 2025年版 | https://www.super.or.jp/wp/wp-content/uploads/2024/02/NSAJ-Supermarket-hakusho2025_Full.pdf | 業界団体 | 部門別売上構成、人員の中央値、惣菜の予約販売 | 2026-10-10 | |

---

## 4. 介護（施設は反復型、利用者対応は個別対応型）

| ソース | URL | 信頼度 | 拾う内容 | 確認日 | 備考 |
|---|---|---|---|---|---|
| 職業能力評価基準 施設介護業 | https://www.mhlw.go.jp/stf/newpage_09297.html | 公的 | 施設運営、施設介護サービス、相談援助 | 2026-10-09 | 通所介護の職種はここには無い（在宅介護業側） |
| 職業能力評価基準 在宅介護業 | https://www.mhlw.go.jp/stf/newpage_09294.html | 公的 | 訪問介護サービス、通所介護サービス、サービス提供責任者 | 2026-10-09 | 通所介護（デイサービス版行動素材表の出所）はこちら |
| JOB tag 施設介護員 | https://shigoto.mhlw.go.jp/User/Occupation/Detail/134 | 公的 | タスクと実施率 | 2026-10-09 | |
| JOB tag 訪問介護員 | https://shigoto.mhlw.go.jp/User/Occupation/Detail/133 | 公的 | 単独訪問での判断 | 2026-10-09 | 一人で判断する場面が多い＝判断の分かれ目が濃い |
| JOB tag 訪問介護のサービス提供責任者 | https://shigoto.mhlw.go.jp/User/Occupation/Detail/555 | 公的 | 計画、ヘルパー管理、家族対応 | 2026-10-09 | |
| JOB tag 施設管理者（介護施設） | https://shigoto.mhlw.go.jp/User/Occupation/Detail/410 | 公的 | 施設運営の管理側 | 2026-10-09 | |
| JOB tag 介護分野の職業一覧 | https://shigoto.mhlw.go.jp/User/OccupationsLongTermCare | 公的 | 12職種の入口 | 2026-10-09 | |
| 職業能力評価基準 施設介護業 レベル区分 | https://www.mhlw.go.jp/content/11800000/000594076.pdf | 公的 | L1〜L4、職種別の呼称 | 2026-10-10 | |
| 職業能力評価基準 在宅介護業 レベル区分・キャリアマップ | https://www.mhlw.go.jp/content/11800000/000594004.pdf | 公的 | L1〜L4、キャリア形成パターンA/B（キャリアマップ https://www.mhlw.go.jp/content/11800000/001106521.pdf ） | 2026-10-10 | |
| キャリアマップ・職業能力評価シート 導入・活用マニュアル（在宅介護業） | https://www.mhlw.go.jp/content/11800000/000973174.pdf | 公的 | 評価記号（○△×）、4つのキャリア、人材要件確認表の設問例 | 2026-10-10 | 評価シート本体は画像のため本文未読。シート一覧 https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000093927.html はExcelで未読 |
| 社保審・介護給付費分科会 第176回 資料2「訪問介護」 | https://www.mhlw.go.jp/content/12300000/000642929.pdf | 公的 | 老計10号のサービス行為区分、身体介護／生活援助の定義 | 2026-10-10 | |
| 老計10号 見守り的援助（H30改正、京都市掲載） | https://www.city.kyoto.lg.jp/hokenfukushi/cmsfiles/contents/0000220/220695/300402mimamoritekiennjo.pdf | 公的 | 1-6の定義文と具体例 | 2026-10-10 | care B-3（保留）の根拠 |
| 老振第76号 指定訪問介護事業所の事業運営の取扱等について | https://www.city.hirakata.osaka.jp/cmsfiles/contents/0000046/46318/tsuuchi_houmon_76.pdf | 公的 | 不適切な要求への対応手順、生活援助の範囲に含まれない行為 | 2026-10-10 | 枚方市掲載 |
| 札幌市 訪問介護 自己点検シート（基準条例・解釈通知の再掲） | https://www.city.sapporo.jp/kaigo/k200jigyo/documents/h25jikotennkenn-houmonnkaigo.pdf | 公的 | サ責の責務8項目、計画、記録、連携、緊急時、事故発生時 | 2026-10-10 | H25。老企第25号の再掲 |
| 千葉県 集団指導資料 訪問介護（R5） | https://www.pref.chiba.lg.jp/koufuku/kaigohoken/documents/01r5-houmonkaigo.pdf | 公的 | 訪問介護計画の作成・変更・同意、「文書等の確実な方法により伝達」 | 2026-10-10 | |
| 厚労省（2006-01）別紙7 指定基準の見直し案 | https://www.mhlw.go.jp/shingi/2006/01/dl/s0126-9d7.pdf | 公的 | サ責責務の原案、緊急時対応、事故発生防止 | 2026-10-10 | |
| 東京都 集団指導資料 指定介護老人福祉施設（R5） | https://www.fukushi.metro.tokyo.lg.jp/documents/d/fukushi/r5_tokuyou_service | 公的 | 施設サービス計画（アセスメント・同意・モニタリング）、中止時の記録、身体的拘束の3要件 | 2026-10-10 | |
| 介護保険施設等における事故の報告様式等について（老高発1129第1号 R6） | https://www.mhlw.go.jp/content/001342369.pdf | 公的 | 報告対象、第1報5日以内、原因分析（本人／職員／環境要因）・再発防止策 | 2026-10-10 | LENS-019（原因の置き場）の根拠 |
| 宮城県 事務連絡（R3-06-28）サ高住・有料老人ホームの事故報告 | https://www.pref.miyagi.jp/documents/8960/r030628.pdf | 公的 | 報告対象の例示、標準様式8項目 | 2026-10-10 | |
| 介護職員初任者研修 到達目標・評価・内容 | https://www.pref.nagano.lg.jp/kaigo-shien/kenko/fukushi/kaigo/kenshu/documents/hyo21.pdf | 公的 | 安全確保とリスクマネジメント、記録・報告・連絡・相談、観察の視点 | 2026-10-10 | 長野県掲載。カリキュラム本体 https://www.pref.miyagi.jp/documents/8807/01_bessi01.pdf |
| 愛媛労働局 社会福祉施設の労働災害が増加しています（2021-09） | https://jsite.mhlw.go.jp/ehime-roudoukyoku/roudoukyoku/gyoumu_naiyou/roudoukijun/anzen/20210908shakaifukusisisetu_saigaibokumetu.html | 公的 | 転倒が41.1%、シフト勤務で安全衛生教育が行き届かない | 2026-10-10 | |
| 居宅サービス事業所におけるICT機器・ソフトウェア導入に関する手引き（R3改訂版） | https://www.mhlw.go.jp/content/12300000/001276275.pdf | 公的 | 申し送りへの転記、「訪問指示内容の伝達漏れ」（概要版 https://www.mhlw.go.jp/content/12300000/001276276.pdf ） | 2026-10-10 | 伝達の手段（LENS-008/010）の根拠 |
| 社保審・介護給付費分科会 第149回 資料1「訪問介護の報酬・基準について」 | https://www.mhlw.go.jp/file/05-Shingikai-12601000-Seisakutoukatsukan-Sanjikanshitsu_Shakaihoshoutantou/0000183149.pdf | 公的 | 生活援助中心型の対象者 | 2026-10-10 | |

---

## 調査で判明した取得上の制約（2026-10-10）

- 厚労省の能力ユニット（Excel）・職務資料（Word）・評価シート（xls）は、この環境ではバイナリ取得が遮断される。読めるのはページ本文と、全体構成・レベル区分・導入マニュアルなどのPDFのみ。「職務遂行のための基準」の原文はPDF抜粋に依存している。ローカルで正本cloneかPDF変換が要る
- ローカルベンチマークは取得許可が下りなかった。手元のExcel（tool2018r4）を使う
- 各業種のresearch.md 0章で見つかった追加資料は 2026-10-10 に本台帳へ転記済み。以後、カードの sources[] は `tools/provenance_check.py` で台帳と突き合わせる（candidates → library 昇格時に必須）

## 使い方の注意

- 会社HPの「私たちのこだわり」は、台帳に入れない。営業文句で、判断の分かれ目が書かれていない。
- 拾うのは「判断が分かれるところ」が書いてある資料だけ。技能検定の採点基準、事故事例の原因分析、業界誌の現場インタビューはこれに当たる。
- 実案件で出た固有のこだわりは、この台帳ではなくライブラリの `field_evidence` に入る。会社名は書かない。
