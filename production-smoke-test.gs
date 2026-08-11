/**
 * Grow3 Assessment — 本番スモークテスト補助
 *
 * 前提:
 * - 本番GAS v3.1.1 を反映済み
 * - initAssessmentSheets() / migrateLegacyThinkingToV3() 完了済み
 * - 3診断HTMLに本番Web App URLを設定し、grow3.jpへ配置済み
 *
 * このファイルはApps Scriptへ「別ファイル」として追加して使用する。
 * 自動削除は行わない。テストデータは名前・batch_idで識別できる形で残す。
 */

const PROD_SMOKE = Object.freeze({
  PLAN_SHEET: 'PROD_SMOKE_TEST_PLAN',
  HEADERS: [
    'created_at','batch_id','case_id','diag_type',
    'token_code','token_id','participant_id',
    'expected_version','status','notes'
  ],
  EXPECTED_VERSIONS: Object.freeze({
    thinking:'thinking-v3.2.1',
    behavior:'behavior-v3.2',
    needs:'needs-v3.2',
  }),
});

function prepareProductionSmokeTestData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  assertRuntimeSheets_(ss);

  const tz = ss.getSpreadsheetTimeZone() || Session.getScriptTimeZone() || 'Asia/Tokyo';
  const stamp = Utilities.formatDate(new Date(), tz, 'yyyyMMdd-HHmmss');
  const batchId = `PROD-SMOKE-${stamp}`;

  const participant = createParticipant({
    name:`本番スモークテスト_${stamp}`,
    org:'Grow3',
    dept:'診断基盤テスト',
    external_member_id:batchId,
  });

  const specs = [
    {case_id:'SMOKE-T', type:'thinking', prefix:'TS-SMOKE'},
    {case_id:'SMOKE-B', type:'behavior', prefix:'BH-SMOKE'},
    {case_id:'SMOKE-N', type:'needs',    prefix:'ND-SMOKE'},
  ];

  const issued = specs.map((x, i) => {
    const token = issueToken(participant.participant_id, x.type, {
      batchId,
      issueNo:i + 1,
      tokenStyle:'hybrid',
      tokenPrefix:x.prefix,
      hybridSuffixLength:4,
      padWidth:3,
      issuedBy:'production-smoke-test',
    });
    return {...x, token};
  });

  const plan = ensureProductionSmokePlanSheet_(ss);
  const now = new Date();
  const rows = issued.map(x => [
    now,
    batchId,
    x.case_id,
    x.type,
    x.token.token_code,
    x.token.token_id,
    participant.participant_id,
    PROD_SMOKE.EXPECTED_VERSIONS[x.type],
    '未実施',
    '',
  ]);
  plan.getRange(plan.getLastRow()+1,1,rows.length,PROD_SMOKE.HEADERS.length).setValues(rows);
  plan.autoResizeColumns(1,PROD_SMOKE.HEADERS.length);

  const result = {
    batch_id:batchId,
    participant_id:participant.participant_id,
    tokens:issued.map(x => ({
      case_id:x.case_id,
      diag_type:x.type,
      token_code:x.token.token_code,
      expected_version:PROD_SMOKE.EXPECTED_VERSIONS[x.type],
    })),
    plan_sheet:PROD_SMOKE.PLAN_SHEET,
  };

  console.log(JSON.stringify(result, null, 2));
  try {
    SpreadsheetApp.getUi().alert([
      `本番スモーク batch: ${batchId}`,
      `participant: ${participant.participant_id}`,
      '',
      ...result.tokens.map(x => `${x.case_id} ${x.diag_type}: ${x.token_code}`),
      '',
      `詳細は「${PROD_SMOKE.PLAN_SHEET}」シートを確認してください。`,
    ].join('\n'));
  } catch (_) {}

  return result;
}

function verifyLatestProductionSmokeBatch() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  assertRuntimeSheets_(ss);

  const plan = ss.getSheetByName(PROD_SMOKE.PLAN_SHEET);
  if (!plan || plan.getLastRow() < 2) {
    throw new Error('PROD_SMOKE_TEST_PLANがありません。先にprepareProductionSmokeTestData()を実行してください。');
  }

  const width = PROD_SMOKE.HEADERS.length;
  const rows = plan.getRange(2,1,plan.getLastRow()-1,width).getValues();
  const latestBatch = cleanText_(rows[rows.length-1][1]);
  if (!latestBatch) throw new Error('最新の本番スモーク batch_idを取得できません。');

  const batchRows = rows.filter(r => cleanText_(r[1]) === latestBatch);
  const checks = batchRows.map(r => {
    const caseId = cleanText_(r[2]);
    const diagType = normalizeDiagType_(r[3]);
    const tokenCode = cleanText_(r[4]);
    const tokenId = cleanText_(r[5]);
    const expectedParticipantId = cleanText_(r[6]);
    const expectedVersion = cleanText_(r[7]);

    const token = findTokenById_(ss, tokenId);
    const result = token ? findProductionSmokeResult_(ss, diagType, token.token_id) : null;

    const messages = [];
    if (!token) messages.push('tokenが見つからない');
    if (!result) messages.push('result未記録');

    if (token && token.participant_id !== expectedParticipantId) {
      messages.push('token.participant_idが想定participantと不一致');
    }
    if (result) {
      if (result.participant_id !== expectedParticipantId) {
        messages.push('result.participant_idが想定participantと不一致');
      }
      if (token && result.participant_id !== token.participant_id) {
        messages.push('token/resultのparticipant_id不一致');
      }
      if (result.assessment_version !== expectedVersion) {
        messages.push(`assessment_version不一致（実際:${result.assessment_version || '(空欄)'} / 期待:${expectedVersion}）`);
      }
    }

    return {
      case_id:caseId,
      diag_type:diagType,
      token_code:tokenCode,
      ok:messages.length === 0,
      participant_id:result ? result.participant_id : (token ? token.participant_id : ''),
      result_id:result ? result.result_id : '',
      assessment_version:result ? result.assessment_version : '',
      expected_version:expectedVersion,
      message:messages.length ? messages.join(' / ') : 'OK',
    };
  });

  const completed = checks.filter(x => x.result_id);
  const ids = [...new Set(completed.map(x => x.participant_id))];
  const sameParticipant =
    checks.length === 3 &&
    checks.every(x => x.ok) &&
    ids.length === 1 &&
    ids[0] === cleanText_(batchRows[0][6]);

  // PLANのstatus/notes更新
  batchRows.forEach(r => {
    const caseId = cleanText_(r[2]);
    const sourceIndex = rows.findIndex(x =>
      cleanText_(x[1]) === latestBatch &&
      cleanText_(x[2]) === caseId
    );
    const check = checks.find(x => x.case_id === caseId);
    if (sourceIndex >= 0 && check) {
      plan.getRange(sourceIndex + 2, 9).setValue(check.ok ? 'PASS' : '未完了/FAIL');
      plan.getRange(sourceIndex + 2, 10).setValue(check.ok ? '' : check.message);
    }
  });

  const summary = {
    batch_id:latestBatch,
    three_diagnostics_same_participant_and_expected_versions:sameParticipant,
    participant_id:cleanText_(batchRows[0][6]),
    checks,
  };

  console.log(JSON.stringify(summary, null, 2));
  try {
    SpreadsheetApp.getUi().alert([
      `本番スモーク batch: ${latestBatch}`,
      `3診断・同一participant・期待version保存: ${sameParticipant ? 'PASS' : '未完了/FAIL'}`,
      '',
      ...checks.map(x =>
        `${x.case_id} ${x.diag_type}: ${x.ok ? `PASS (${x.assessment_version})` : x.message}`
      ),
    ].join('\n'));
  } catch (_) {}

  return summary;
}

function ensureProductionSmokePlanSheet_(ss) {
  let sheet = ss.getSheetByName(PROD_SMOKE.PLAN_SHEET);
  if (!sheet) {
    sheet = ss.insertSheet(PROD_SMOKE.PLAN_SHEET);
    sheet.getRange(1,1,1,PROD_SMOKE.HEADERS.length).setValues([PROD_SMOKE.HEADERS]);
    sheet.getRange(1,1,1,PROD_SMOKE.HEADERS.length)
      .setFontWeight('bold')
      .setBackground('#263238')
      .setFontColor('#ffffff');
    sheet.setFrozenRows(1);
    return sheet;
  }

  const actual = sheet.getRange(1,1,1,PROD_SMOKE.HEADERS.length).getValues()[0].map(String);
  const expected = PROD_SMOKE.HEADERS.map(String);
  if (actual.join('\u241f') !== expected.join('\u241f')) {
    throw new Error('既存PROD_SMOKE_TEST_PLANのヘッダーが想定と異なります。自動修正せず停止しました。');
  }
  return sheet;
}

function findProductionSmokeResult_(ss, diagType, tokenId) {
  const type = normalizeDiagType_(diagType);
  if (!type) return null;

  const sheetName = DIAGNOSTICS[type].resultSheet;
  const sheet = ss.getSheetByName(sheetName);
  if (!sheet || sheet.getLastRow() < 2) return null;

  const headers = HEADERS[sheetName];
  const idxResult = headers.indexOf('result_id');
  const idxToken = headers.indexOf('token_id');
  const idxParticipant = headers.indexOf('participant_id');
  const idxVersion = headers.indexOf('assessment_version');

  if ([idxResult,idxToken,idxParticipant,idxVersion].some(i => i < 0)) {
    throw new Error(`${sheetName}の必要ヘッダーが見つかりません。`);
  }

  const data = sheet.getRange(2,1,sheet.getLastRow()-1,headers.length).getValues();
  for (let i=0; i<data.length; i++) {
    if (cleanText_(data[i][idxToken]) === cleanText_(tokenId)) {
      return {
        row:i+2,
        result_id:cleanText_(data[i][idxResult]),
        token_id:cleanText_(data[i][idxToken]),
        participant_id:cleanText_(data[i][idxParticipant]),
        assessment_version:cleanText_(data[i][idxVersion]),
      };
    }
  }
  return null;
}
