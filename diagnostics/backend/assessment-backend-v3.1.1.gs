/**
 * ============================================================
 * Grow3 3診断 共通受験基盤 — Google Apps Script v3
 * thinking / behavior / needs
 *
 * 確定方針:
 * - 人 = participants
 * - 1回の受験機会 = assessment_tokens
 * - 診断した事実 = 診断別 results
 * - token の used 状態は保存せず、result の存在から導出する
 * - validate は案内。record が本当の認証処理
 * - record は LockService 内で再検証し、1 token_id = 最大1 result を保証する
 * - participant_id はブラウザから受け取らず、token からサーバー側で確定する
 * - 未割当 token は participant_id = 空欄で保持し、初回 record 時に人物を作成・割当する
 * - validate レスポンスでは participant のPIIを返さない（連番token運用時の列挙漏えい対策）
 * - diag_date は入力値を YYYY-MM-DD に正規化、completed_at はサーバー生成
 * - 本番シートを善意で壊さない。init/migration は明示した複製先でしか動かさない
 * ============================================================
 */

const V3 = Object.freeze({
  SHEETS: Object.freeze({
    PARTICIPANTS: 'participants',
    TOKENS: 'assessment_tokens',
    THINKING: 'thinking_results',
    BEHAVIOR: 'behavior_results',
    NEEDS: 'needs_results',
    LEGACY_TOKENS: 'tokens',
    LEGACY_THINKING: 'results',
  }),
  SETUP_ALLOWED_ID_PROPERTY: 'V3_SETUP_ALLOWED_SPREADSHEET_ID',
  MAX_ANSWERS_JSON_LENGTH: 50000,
});

const DIAGNOSTICS = Object.freeze({
  thinking: Object.freeze({ prefix: 'TS', resultSheet: V3.SHEETS.THINKING }),
  behavior: Object.freeze({ prefix: 'BH', resultSheet: V3.SHEETS.BEHAVIOR }),
  needs: Object.freeze({ prefix: 'ND', resultSheet: V3.SHEETS.NEEDS }),
});

const HEADERS = Object.freeze({
  participants: [
    'participant_id','name','birthdate','org','dept','external_member_id','created_at','updated_at'
  ],
  assessment_tokens: [
    'token_id','token_code','batch_id','issue_no','diag_type','participant_id',
    'issued_at','expires_at','revoked_at','assigned_at','issued_by'
  ],
  thinking_results: [
    'result_id','token_id','participant_id','diag_date','name','org','dept',
    'score_A','score_B','score_C','score_D','type_label',
    'assessment_version','answers_json','completed_at'
  ],
  behavior_results: [
    'result_id','token_id','participant_id','diag_date','name','org','dept',
    'score_s1','score_s2','score_s3','assessment_version','answers_json','completed_at'
  ],
  needs_results: [
    'result_id','token_id','participant_id','diag_date','name','org','dept',
    'score_ai','score_ch','score_ji','score_ta','score_se',
    'assessment_version','answers_json','completed_at'
  ],
});

// ============================================================
// Public Web API
// 公開 action は validate / record の2つだけ。
// ============================================================

function doPost(e) {
  try {
    const params = parsePostJson_(e);
    const action = String(params.action || '').trim().toLowerCase();

    if (action === 'validate') {
      return respond_(validateToken(params.token_code || params.token, params.diag_type));
    }
    if (action === 'record') {
      return respond_(recordResult(params));
    }
    return respond_({ ok:false, code:'unknown_action', message:'不明なアクションです。' });
  } catch (err) {
    console.error(err && err.stack ? err.stack : err);
    return respond_({ ok:false, code:'server_error', message:'サーバーエラーが発生しました。' });
  }
}

function doGet() {
  return respond_({ ok:true, message:'Grow3 assessment GAS v3 is running.' });
}

function respond_(data) {
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}

function parsePostJson_(e) {
  if (!e || !e.postData || typeof e.postData.contents !== 'string') return {};
  const raw = e.postData.contents.trim();
  if (!raw) return {};
  return JSON.parse(raw);
}

// ============================================================
// Public logic: validate
// ============================================================

/**
 * token を消費しない。
 * PIIは返さない。token がどの participant に紐づくかはサーバー内部だけで扱う。
 */
function validateToken(tokenCode, expectedDiagType) {
  const token = normalizeTokenCode_(tokenCode);
  const diagType = normalizeDiagType_(expectedDiagType);

  if (!token) return { ok:false, code:'missing_token', message:'トークンを入力してください。' };
  if (!diagType) return { ok:false, code:'invalid_diag_type', message:'診断種別が不正です。' };

  const ss = SpreadsheetApp.getActiveSpreadsheet();
  assertRuntimeSheets_(ss);

  const tokenRow = findTokenByCode_(ss, token);
  if (!tokenRow) {
    return { ok:false, code:'invalid_token', message:'トークンが見つかりません。正しく入力されているか確認してください。' };
  }

  const status = evaluateToken_(ss, tokenRow, diagType);
  if (!status.ok) return status;

  return {
    ok:true,
    code:'available',
    message:'認証成功',
    diag_type:tokenRow.diag_type,
    assigned:Boolean(tokenRow.participant_id),
  };
}

// ============================================================
// Public logic: record
// ============================================================

/**
 * record が本当の認証処理。
 * Lock 内で token を再検証し、二重送信は既存resultを返す冪等処理にする。
 */
function recordResult(params) {
  const lock = LockService.getScriptLock();
  lock.waitLock(15000);

  try {
    const tokenCode = normalizeTokenCode_(params.token_code || params.token);
    const diagType = normalizeDiagType_(params.diag_type);

    if (!tokenCode) return { ok:false, code:'missing_token', message:'トークンがありません。' };
    if (!diagType) return { ok:false, code:'invalid_diag_type', message:'診断種別が不正です。' };

    const ss = SpreadsheetApp.getActiveSpreadsheet();
    assertRuntimeSheets_(ss);

    const tokenRow = findTokenByCode_(ss, tokenCode);
    if (!tokenRow) {
      return { ok:false, code:'invalid_token', message:'トークンが見つかりません。' };
    }

    // 冪等再送を成功扱いにする前に、少なくとも「この診断用tokenか」は必ず確認する。
    if (tokenRow.diag_type !== diagType) {
      return { ok:false, code:'wrong_diagnosis', message:'このトークンは別の診断用です。' };
    }
    if (!isTokenPrefixConsistent_(tokenRow.token_code, tokenRow.diag_type)) {
      return { ok:false, code:'token_config_error', message:'トークン設定に不整合があります。管理者に連絡してください。' };
    }

    // token_id単位で既に結果がある場合は、ネットワーク再送等を想定して成功扱いにする。
    const existing = findResultByTokenId_(ss, tokenRow.diag_type, tokenRow.token_id);
    if (existing) {
      return {
        ok:true,
        code:'already_recorded',
        message:'結果はすでに記録されています。',
        diag_type:tokenRow.diag_type,
        result_id:existing.result_id,
        already_recorded:true,
      };
    }

    const status = evaluateToken_(ss, tokenRow, diagType);
    if (!status.ok) return status;

    const validation = validateResultPayload_(diagType, params, ss);
    if (!validation.ok) return validation;

    // participant_idはブラウザから受け取らない。tokenを正とする。
    const resolved = resolveParticipantForRecord_(ss, tokenRow, params);
    if (!resolved.ok) return resolved;

    const participant = resolved.participant;
    const snapshot = buildParticipantSnapshot_(participant, params);
    const now = new Date();
    const resultId = generateUniqueId_(ss, 'R', 'result');

    const base = {
      result_id:resultId,
      token_id:tokenRow.token_id,
      participant_id:participant.participant_id,
      diag_date:validation.diag_date,
      name:snapshot.name,
      org:snapshot.org,
      dept:snapshot.dept,
      assessment_version:String(params.assessment_version || '').trim(),
      answers_json:validation.answers_json,
      completed_at:now,
    };

    appendResult_(ss, diagType, base, params);

    return {
      ok:true,
      code:'recorded',
      message:'結果を記録しました。',
      diag_type:diagType,
      result_id:resultId,
      participant_created:resolved.created,
      already_recorded:false,
    };
  } finally {
    lock.releaseLock();
  }
}

function evaluateToken_(ss, tokenRow, expectedDiagType) {
  if (tokenRow.diag_type !== expectedDiagType) {
    return { ok:false, code:'wrong_diagnosis', message:'このトークンは別の診断用です。' };
  }

  if (!isTokenPrefixConsistent_(tokenRow.token_code, tokenRow.diag_type)) {
    return { ok:false, code:'token_config_error', message:'トークン設定に不整合があります。管理者に連絡してください。' };
  }

  if (hasValue_(tokenRow.revoked_at)) {
    return { ok:false, code:'revoked', message:'このトークンは無効化されています。' };
  }

  const expiry = asDate_(tokenRow.expires_at);
  if (expiry && new Date().getTime() > expiry.getTime()) {
    return { ok:false, code:'expired', message:'このトークンの有効期限は終了しています。' };
  }

  const existing = findResultByTokenId_(ss, tokenRow.diag_type, tokenRow.token_id);
  if (existing) {
    return { ok:false, code:'used', message:'このトークンはすでに使用済みです。' };
  }

  if (tokenRow.participant_id && !findParticipantById_(ss, tokenRow.participant_id)) {
    return { ok:false, code:'participant_config_error', message:'受験者情報の設定に不整合があります。管理者に連絡してください。' };
  }

  return { ok:true };
}

// ============================================================
// Participant resolution / result snapshots
// ============================================================

function resolveParticipantForRecord_(ss, tokenRow, params) {
  if (tokenRow.participant_id) {
    const participant = findParticipantById_(ss, tokenRow.participant_id);
    if (!participant) {
      return { ok:false, code:'participant_config_error', message:'受験者情報が見つかりません。管理者に連絡してください。' };
    }
    return { ok:true, participant, created:false };
  }

  // 未割当tokenはrecord時に初めてparticipantを作る。
  // 自動名寄せはしない。同姓同名等の誤統合を避けるため、必ず新規participant_idを発行する。
  const infoValidation = validateNewParticipantInfo_(params);
  if (!infoValidation.ok) return infoValidation;

  const participant = createParticipantInternal_(ss, {
    name:params.name,
    birthdate:params.birthdate,
    org:params.org,
    dept:params.dept,
    external_member_id:'',
  });

  const tokenSheet = ss.getSheetByName(V3.SHEETS.TOKENS);
  tokenSheet.getRange(tokenRow.row, 6).setValue(participant.participant_id); // participant_id
  tokenSheet.getRange(tokenRow.row, 10).setValue(new Date());               // assigned_at

  return { ok:true, participant, created:true };
}

function buildParticipantSnapshot_(participant, params) {
  // participant_idの決定には使わないが、受験時点の組織・部署等は入力値を優先して履歴に残せる。
  // 空欄の場合はparticipantsの現在値にfallbackする。
  return {
    name:cleanText_(params.name) || participant.name,
    org:cleanText_(params.org) || participant.org,
    dept:cleanText_(params.dept) || participant.dept,
  };
}

function validateNewParticipantInfo_(params) {
  const name = cleanText_(params.name);
  if (!name) {
    return { ok:false, code:'participant_name_required', message:'未割当トークンのため、氏名を入力してください。' };
  }

  const birth = normalizeOptionalDate_(params.birthdate);
  if (!birth.ok) {
    return { ok:false, code:'invalid_birthdate', message:'生年月日の形式が不正です。' };
  }
  return { ok:true };
}

// ============================================================
// Result validation / append
// ============================================================

function validateResultPayload_(diagType, p, ss) {
  const diagDate = normalizeRequiredDiagDate_(p.diag_date, ss);
  if (!diagDate.ok) return diagDate;

  const version = String(p.assessment_version || '').trim();
  if (!version) {
    return { ok:false, code:'missing_assessment_version', message:'診断バージョンがありません。' };
  }

  const answers = normalizeAnswersJson_(p.answers_json);
  if (!answers.ok) return answers;

  if (diagType === 'thinking') {
    const vals = [p.score_A,p.score_B,p.score_C,p.score_D].map(Number);
    if (vals.some(v => !Number.isFinite(v) || v < 0 || v > 200)) {
      return { ok:false, code:'invalid_score', message:'思考特性スコアが不正です。' };
    }
    const total = vals.reduce((a,b)=>a+b,0);
    if (Math.abs(total - 200) > 0.001) {
      return { ok:false, code:'invalid_score_total', message:'思考特性スコアの合計が200点ではありません。' };
    }
  }

  if (diagType === 'behavior') {
    const vals = [p.score_s1,p.score_s2,p.score_s3].map(Number);
    // 各軸9問×±1のため、正常値は -9,-7,-5,-3,-1,1,3,5,7,9 のいずれか。
    if (vals.some(v => !Number.isInteger(v) || v < -9 || v > 9 || Math.abs(v) % 2 !== 1)) {
      return { ok:false, code:'invalid_score', message:'行動特性スコアが不正です。' };
    }
  }

  if (diagType === 'needs') {
    const vals = [p.score_ai,p.score_ch,p.score_ji,p.score_ta,p.score_se].map(Number);
    if (vals.some(v => !Number.isInteger(v) || v < 0 || v > 8)) {
      return { ok:false, code:'invalid_score', message:'欲求プロフィールのスコアが不正です。' };
    }
    const total = vals.reduce((a,b)=>a+b,0);
    if (total !== 20) {
      return { ok:false, code:'invalid_score_total', message:'欲求プロフィールの回答数が不正です。' };
    }
  }

  return { ok:true, diag_date:diagDate.value, answers_json:answers.value };
}

function appendResult_(ss, diagType, base, p) {
  const sheet = ss.getSheetByName(DIAGNOSTICS[diagType].resultSheet);
  if (!sheet) throw new Error(`「${DIAGNOSTICS[diagType].resultSheet}」シートが見つかりません。`);

  let row;
  if (diagType === 'thinking') {
    row = [
      base.result_id,base.token_id,base.participant_id,base.diag_date,base.name,base.org,base.dept,
      Number(p.score_A),Number(p.score_B),Number(p.score_C),Number(p.score_D),String(p.type_label || ''),
      base.assessment_version,base.answers_json,base.completed_at,
    ];
  } else if (diagType === 'behavior') {
    row = [
      base.result_id,base.token_id,base.participant_id,base.diag_date,base.name,base.org,base.dept,
      Number(p.score_s1),Number(p.score_s2),Number(p.score_s3),
      base.assessment_version,base.answers_json,base.completed_at,
    ];
  } else if (diagType === 'needs') {
    row = [
      base.result_id,base.token_id,base.participant_id,base.diag_date,base.name,base.org,base.dept,
      Number(p.score_ai),Number(p.score_ch),Number(p.score_ji),Number(p.score_ta),Number(p.score_se),
      base.assessment_version,base.answers_json,base.completed_at,
    ];
  } else {
    throw new Error('未対応の診断種別です。');
  }
  sheet.appendRow(row);
}

// ============================================================
// Admin functions (Apps Script editor / spreadsheet custom menu only)
// Public doPostからは呼ばない。
// ============================================================

function createParticipant(info) {
  const lock = LockService.getScriptLock();
  lock.waitLock(15000);
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    assertRuntimeSheets_(ss);
    return createParticipantInternal_(ss, info || {});
  } finally {
    lock.releaseLock();
  }
}

function createParticipantInternal_(ss, info) {
  const name = cleanText_(info.name);
  if (!name) throw new Error('name（氏名）は必須です。');

  const birth = normalizeOptionalDate_(info.birthdate);
  if (!birth.ok) throw new Error('birthdate（生年月日）の形式が不正です。');

  const now = new Date();
  const participantId = generateUniqueId_(ss, 'P', 'participant');
  const row = [
    participantId,
    name,
    birth.value,
    cleanText_(info.org),
    cleanText_(info.dept),
    cleanText_(info.external_member_id),
    now,
    now,
  ];

  ss.getSheetByName(V3.SHEETS.PARTICIPANTS).appendRow(row);
  return rowToParticipant_(row, -1);
}

function updateParticipant(participantId, patch) {
  const lock = LockService.getScriptLock();
  lock.waitLock(15000);
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    assertRuntimeSheets_(ss);
    const existing = findParticipantById_(ss, participantId);
    if (!existing) throw new Error('participant_idが見つかりません。');

    patch = patch || {};
    const next = {
      name:Object.prototype.hasOwnProperty.call(patch,'name') ? cleanText_(patch.name) : existing.name,
      birthdate:existing.birthdate,
      org:Object.prototype.hasOwnProperty.call(patch,'org') ? cleanText_(patch.org) : existing.org,
      dept:Object.prototype.hasOwnProperty.call(patch,'dept') ? cleanText_(patch.dept) : existing.dept,
      external_member_id:Object.prototype.hasOwnProperty.call(patch,'external_member_id') ? cleanText_(patch.external_member_id) : existing.external_member_id,
    };
    if (!next.name) throw new Error('name（氏名）は空欄にできません。');

    if (Object.prototype.hasOwnProperty.call(patch,'birthdate')) {
      const birth = normalizeOptionalDate_(patch.birthdate);
      if (!birth.ok) throw new Error('birthdate（生年月日）の形式が不正です。');
      next.birthdate = birth.value;
    }

    const sheet = ss.getSheetByName(V3.SHEETS.PARTICIPANTS);
    sheet.getRange(existing.row, 2, 1, 7).setValues([[
      next.name,next.birthdate,next.org,next.dept,next.external_member_id,existing.created_at,new Date()
    ]]);
    return findParticipantById_(ss, participantId);
  } finally {
    lock.releaseLock();
  }
}

/**
 * participantId は空欄/null可（未割当token）。
 * options例:
 * {
 *   batchId:'20260903_A社', issueNo:14,
 *   tokenStyle:'hybrid', // sequential | random | hybrid
 *   tokenPrefix:'BH-A2609',
 *   randomLength:8, hybridSuffixLength:4, padWidth:3,
 *   expiresAt:'2026-09-30', issuedBy:'小林'
 * }
 */
function issueToken(participantId, diagType, options) {
  const lock = LockService.getScriptLock();
  lock.waitLock(15000);
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    assertRuntimeSheets_(ss);
    return issueTokenInternal_(ss, participantId, diagType, options || {});
  } finally {
    lock.releaseLock();
  }
}

function issueBatchTokens(diagType, count, options) {
  const lock = LockService.getScriptLock();
  lock.waitLock(15000);
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    assertRuntimeSheets_(ss);

    options = options || {};
    const type = normalizeDiagType_(diagType);
    if (!type) throw new Error('diagTypeが不正です。');

    const participantIds = Array.isArray(options.participantIds) ? options.participantIds : null;
    const n = participantIds ? participantIds.length : Number(count || 0);
    if (!Number.isInteger(n) || n <= 0) throw new Error('countは1以上の整数にしてください。');

    // ① 書き込む前に、受験者・附番・prefix・期限などを全件分検証する
    const pids = [];
    for (let i=0; i<n; i++) {
      const pid = participantIds ? cleanText_(participantIds[i]) : '';
      if (pid && !findParticipantById_(ss, pid)) {
        throw new Error(`participantIds[${i}] のparticipant_idが見つかりません。`);
      }
      pids.push(pid);
    }

    const batchId = cleanText_(options.batchId);
    const style = String(options.tokenStyle || 'hybrid').trim().toLowerCase();
    if (!['sequential','random','hybrid'].includes(style)) throw new Error('tokenStyleが不正です。');

    const basePrefix = DIAGNOSTICS[type].prefix;
    const tokenPrefix = normalizeTokenPrefix_(options.tokenPrefix || basePrefix);
    if (tokenPrefix.split('-')[0] !== basePrefix) {
      throw new Error(`tokenPrefixは「${basePrefix}」で始めてください。`);
    }

    const padWidth = Number(options.padWidth || 3);
    const randomLength = Math.max(4, Number(options.randomLength) || 8);
    const hybridSuffixLength = Math.max(3, Number(options.hybridSuffixLength) || 4);
    if (!Number.isInteger(padWidth) || padWidth <= 0) throw new Error('padWidthは1以上の整数にしてください。');

    const firstIssueNo = options.startIssueNo != null && options.startIssueNo !== ''
      ? Number(options.startIssueNo)
      : nextIssueNo_(ss, batchId, type);
    if (!Number.isInteger(firstIssueNo) || firstIssueNo <= 0) {
      throw new Error('startIssueNoは1以上の整数にしてください。');
    }

    const expiresAt = parseExpiry_(options.expiresAt);
    const issuedBy = cleanText_(options.issuedBy) || getActiveUserLabel_();
    const now = new Date();

    const sheet = ss.getSheetByName(V3.SHEETS.TOKENS);
    const width = HEADERS.assessment_tokens.length;
    const existing = sheet.getLastRow() >= 2
      ? sheet.getRange(2,1,sheet.getLastRow()-1,width).getValues()
      : [];

    const usedIds = new Set();
    const usedCodes = new Set();
    const usedIssueNos = new Set();
    existing.forEach(r => {
      const id = cleanText_(r[0]);
      const code = normalizeTokenCode_(r[1]);
      if (id) usedIds.add(id);
      if (code) usedCodes.add(code);
      if (cleanText_(r[2]) === batchId && normalizeDiagType_(r[4]) === type) {
        const no = Number(r[3] || 0);
        if (Number.isInteger(no) && no > 0) usedIssueNos.add(no);
      }
    });

    const rows = [];
    for (let i=0; i<n; i++) {
      const issueNo = firstIssueNo + i;
      if (usedIssueNos.has(issueNo)) {
        throw new Error(`batch「${batchId || '(空欄)'}」の${type}でissue_no「${issueNo}」は既に存在します。`);
      }

      let tokenId = '';
      for (let tries=0; tries<30; tries++) {
        const candidate = `T_${uuidToSafe_(Utilities.getUuid()).slice(0,16)}`;
        if (!usedIds.has(candidate)) {
          tokenId = candidate;
          usedIds.add(candidate);
          break;
        }
      }
      if (!tokenId) throw new Error('一意なtoken_idの生成に失敗しました。');

      const issue = String(issueNo).padStart(padWidth,'0');
      let tokenCode = '';
      if (style === 'sequential') {
        tokenCode = normalizeTokenCode_(`${tokenPrefix}-${issue}`);
        if (usedCodes.has(tokenCode)) {
          throw new Error(`token_code「${tokenCode}」は既に存在します。batchごとにtokenPrefixを変えるか、hybrid/random方式を使用してください。`);
        }
      } else {
        for (let tries=0; tries<30; tries++) {
          const candidate = style === 'random'
            ? normalizeTokenCode_(`${tokenPrefix}-${safeRandom_(randomLength)}`)
            : normalizeTokenCode_(`${tokenPrefix}-${issue}-${safeRandom_(hybridSuffixLength)}`);
          if (!usedCodes.has(candidate)) {
            tokenCode = candidate;
            break;
          }
        }
        if (!tokenCode) throw new Error('一意なtoken_codeの生成に失敗しました。');
      }

      usedCodes.add(tokenCode);
      usedIssueNos.add(issueNo);
      const pid = pids[i];
      rows.push([
        tokenId,tokenCode,batchId,issueNo,type,pid,now,expiresAt,'',pid ? now : '',issuedBy
      ]);
    }

    // ② 全件のpreflightが成功した場合だけ、1回のsetValues()でまとめて書き込む
    const startRow = sheet.getLastRow() + 1;
    sheet.getRange(startRow,1,rows.length,width).setValues(rows);
    return rows.map((row,i)=>rowToToken_(row,startRow+i));
  } finally {
    lock.releaseLock();
  }
}

function issueTokenInternal_(ss, participantId, diagType, options) {
  const type = normalizeDiagType_(diagType);
  if (!type) throw new Error('diagTypeが不正です。');

  const pid = cleanText_(participantId);
  if (pid && !findParticipantById_(ss, pid)) {
    throw new Error('指定されたparticipant_idが見つかりません。');
  }

  const batchId = cleanText_(options.batchId);
  const issueNo = options.issueNo != null && options.issueNo !== ''
    ? Number(options.issueNo)
    : nextIssueNo_(ss, batchId, type);
  if (!Number.isInteger(issueNo) || issueNo <= 0) throw new Error('issueNoは1以上の整数にしてください。');
  if (issueNoExists_(ss, batchId, type, issueNo)) {
    throw new Error(`batch「${batchId || '(空欄)'}」の${type}でissue_no「${issueNo}」は既に存在します。`);
  }

  const style = String(options.tokenStyle || 'hybrid').trim().toLowerCase();
  if (!['sequential','random','hybrid'].includes(style)) throw new Error('tokenStyleが不正です。');

  const basePrefix = DIAGNOSTICS[type].prefix;
  const tokenPrefix = normalizeTokenPrefix_(options.tokenPrefix || basePrefix);
  if (tokenPrefix.split('-')[0] !== basePrefix) {
    throw new Error(`tokenPrefixは「${basePrefix}」で始めてください。`);
  }

  const tokenId = generateUniqueId_(ss, 'T', 'token');
  const tokenCode = generateUniqueTokenCode_(ss, {
    style,
    prefix:tokenPrefix,
    issueNo,
    padWidth:Number(options.padWidth || 3),
    randomLength:Number(options.randomLength || 8),
    hybridSuffixLength:Number(options.hybridSuffixLength || 4),
  });

  const now = new Date();
  const expiresAt = parseExpiry_(options.expiresAt);
  const issuedBy = cleanText_(options.issuedBy) || getActiveUserLabel_();

  const row = [
    tokenId,tokenCode,batchId,issueNo,type,pid,now,expiresAt,'',pid ? now : '',issuedBy
  ];
  ss.getSheetByName(V3.SHEETS.TOKENS).appendRow(row);
  return rowToToken_(row, -1);
}

function revokeToken(tokenCodeOrId) {
  const lock = LockService.getScriptLock();
  lock.waitLock(15000);
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    assertRuntimeSheets_(ss);
    const token = findTokenByCodeOrId_(ss, tokenCodeOrId);
    if (!token) throw new Error('トークンが見つかりません。');
    if (findResultByTokenId_(ss, token.diag_type, token.token_id)) {
      throw new Error('すでに結果が記録されているトークンは無効化できません。');
    }
    ss.getSheetByName(V3.SHEETS.TOKENS).getRange(token.row, 9).setValue(new Date());
    return findTokenById_(ss, token.token_id);
  } finally {
    lock.releaseLock();
  }
}

function assignTokenToParticipant(tokenCodeOrId, participantId) {
  const lock = LockService.getScriptLock();
  lock.waitLock(15000);
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    assertRuntimeSheets_(ss);
    const token = findTokenByCodeOrId_(ss, tokenCodeOrId);
    if (!token) throw new Error('トークンが見つかりません。');
    const participant = findParticipantById_(ss, participantId);
    if (!participant) throw new Error('participant_idが見つかりません。');
    if (findResultByTokenId_(ss, token.diag_type, token.token_id)) {
      throw new Error('すでに使用済みのトークンは割当変更できません。');
    }
    if (token.participant_id && token.participant_id !== participant.participant_id) {
      throw new Error('このトークンは別の受験者に割当済みです。自動で再割当はしません。');
    }

    const sheet = ss.getSheetByName(V3.SHEETS.TOKENS);
    sheet.getRange(token.row, 6).setValue(participant.participant_id);
    if (!token.assigned_at) sheet.getRange(token.row, 10).setValue(new Date());
    return findTokenById_(ss, token.token_id);
  } finally {
    lock.releaseLock();
  }
}

/**
 * 管理者の候補提示用。自動統合には使わない。
 * query: {name, org, dept, external_member_id} または文字列
 */
function findParticipantCandidates(query) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  assertRuntimeSheets_(ss);
  const sheet = ss.getSheetByName(V3.SHEETS.PARTICIPANTS);
  if (sheet.getLastRow() < 2) return [];

  let q;
  if (typeof query === 'string') {
    q = { any:normalizeSearchText_(query) };
  } else {
    query = query || {};
    q = {
      name:normalizeSearchText_(query.name),
      org:normalizeSearchText_(query.org),
      dept:normalizeSearchText_(query.dept),
      external_member_id:normalizeSearchText_(query.external_member_id),
    };
  }

  const data = sheet.getRange(2,1,sheet.getLastRow()-1,HEADERS.participants.length).getValues();
  return data.map((r,i)=>rowToParticipant_(r,i+2)).filter(p => {
    if (q.any) {
      return [p.name,p.org,p.dept,p.external_member_id]
        .some(v => normalizeSearchText_(v).includes(q.any));
    }
    if (q.name && !normalizeSearchText_(p.name).includes(q.name)) return false;
    if (q.org && !normalizeSearchText_(p.org).includes(q.org)) return false;
    if (q.dept && !normalizeSearchText_(p.dept).includes(q.dept)) return false;
    if (q.external_member_id && normalizeSearchText_(p.external_member_id) !== q.external_member_id) return false;
    return Boolean(q.name || q.org || q.dept || q.external_member_id);
  }).slice(0,50);
}

// ============================================================
// Safe setup / migration for a duplicated spreadsheet only
// ============================================================

/**
 * 読み取り専用。複製したスプレッドシートのID確認用。
 * このIDを Apps Script > プロジェクトの設定 > スクリプト プロパティに
 * V3_SETUP_ALLOWED_SPREADSHEET_ID として手動登録してから init/migration を実行する。
 */
function showActiveSpreadsheetId() {
  const id = SpreadsheetApp.getActiveSpreadsheet().getId();
  console.log(id);
  try { SpreadsheetApp.getUi().alert(`Active spreadsheet ID:\n${id}`); } catch (_) {}
  return id;
}

/**
 * 既存シートをclear/rename/deleteしない。
 * v3用5シートがなければ作り、存在する場合はヘッダー順序を厳密確認する。
 */
function initAssessmentSheets() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  assertSetupTarget_(ss);

  ensureExactSheet_(ss, V3.SHEETS.PARTICIPANTS, HEADERS.participants);
  ensureExactSheet_(ss, V3.SHEETS.TOKENS, HEADERS.assessment_tokens);
  ensureExactSheet_(ss, V3.SHEETS.THINKING, HEADERS.thinking_results);
  ensureExactSheet_(ss, V3.SHEETS.BEHAVIOR, HEADERS.behavior_results);
  ensureExactSheet_(ss, V3.SHEETS.NEEDS, HEADERS.needs_results);

  try {
    SpreadsheetApp.getUi().alert('v3用シートの初期化・検証が完了しました。既存シート／既存データは変更していません。');
  } catch (_) {}
  return true;
}

/**
 * 旧 tokens / results をv3へ「コピー」する移行。
 * 元シートは一切変更しない。
 * - 同一旧tokenに複数resultsがある場合も全件保存する。
 * - 1 token_id = 1 result を守るため、2件目以降は履歴用の内部tokenを追加する。
 * - 同一人物らしい複数tokenの自動名寄せは行わない（旧tokenごとにparticipantを作る）。
 * - 冪等性: 同じ legacy token_code が assessment_tokens に存在する場合、そのtokenはスキップする。
 */
function migrateLegacyThinkingToV3() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  assertSetupTarget_(ss);
  initAssessmentSheets();

  const legacyTokenSheet = ss.getSheetByName(V3.SHEETS.LEGACY_TOKENS);
  const legacyResultSheet = ss.getSheetByName(V3.SHEETS.LEGACY_THINKING);
  if (!legacyTokenSheet && !legacyResultSheet) {
    throw new Error('旧「tokens」「results」シートが見つかりません。');
  }

  const resultGroups = readLegacyThinkingGroups_(legacyResultSheet);
  const legacyTokens = readLegacyTokens_(legacyTokenSheet);

  // resultsにしか存在しないtokenも移行対象に含める。
  Object.keys(resultGroups).forEach(code => {
    if (!legacyTokens[code]) legacyTokens[code] = { token_code:code, legacy_row:null };
  });

  const summary = {
    tokens_seen:0,
    tokens_migrated:0,
    participants_created:0,
    results_migrated:0,
    skipped_existing:0,
    results_skipped_existing:0,
    history_tokens_created:0,
  };

  Object.keys(legacyTokens).forEach(code => {
    summary.tokens_seen++;
    const legacyToken = legacyTokens[code];
    const results = resultGroups[code] || [];
    const info = mergeLegacyParticipantInfo_(legacyToken, results);
    const migrationBatchId = `legacy-thinking:${code}`;

    let primaryToken = findTokenByCode_(ss, code);
    let participant = null;

    if (primaryToken) {
      // 同じtoken_codeが別用途で既にv3に存在する場合は、自動で上書き・統合しない。
      if (primaryToken.diag_type !== 'thinking' || primaryToken.batch_id !== migrationBatchId) {
        throw new Error(`legacy token「${code}」と既存assessment_tokensが衝突しています。自動移行せず停止しました。`);
      }
      summary.skipped_existing++;
      if (primaryToken.participant_id) participant = findParticipantById_(ss, primaryToken.participant_id);
    } else {
      if (info.name || info.birthdate || info.org || info.dept || results.length) {
        participant = createLegacyParticipant_(ss, info);
        summary.participants_created++;
      }
      primaryToken = appendLegacyToken_(ss, {
        token_code:code,
        batch_id:migrationBatchId,
        participant_id:participant ? participant.participant_id : '',
        issue_no:1,
        issued_by:'legacy-migration',
      });
      summary.tokens_migrated++;
    }

    // 途中失敗から再実行できるよう、participantが不足していればここで補完する。
    if (!participant && (info.name || info.birthdate || info.org || info.dept || results.length)) {
      participant = createLegacyParticipant_(ss, info);
      summary.participants_created++;
      const tokenSheet = ss.getSheetByName(V3.SHEETS.TOKENS);
      tokenSheet.getRange(primaryToken.row, 6).setValue(participant.participant_id);
      primaryToken.participant_id = participant.participant_id;
    }

    results.forEach((legacyResult, i) => {
      const attemptNo = i + 1;
      let tokenForResult = attemptNo === 1
        ? primaryToken
        : findTokenByBatchIssue_(ss, migrationBatchId, 'thinking', attemptNo);

      if (!tokenForResult) {
        tokenForResult = appendLegacyHistoryToken_(
          ss,
          migrationBatchId,
          participant ? participant.participant_id : '',
          attemptNo
        );
        summary.history_tokens_created++;
      }

      if (!participant) {
        participant = createLegacyParticipant_(ss, info);
        summary.participants_created++;
      }

      if (!tokenForResult.participant_id) {
        const tokenSheet = ss.getSheetByName(V3.SHEETS.TOKENS);
        tokenSheet.getRange(tokenForResult.row, 6).setValue(participant.participant_id);
        tokenForResult.participant_id = participant.participant_id;
      } else if (tokenForResult.participant_id !== participant.participant_id) {
        throw new Error(`legacy token「${code}」の履歴tokenが別participantに紐づいています。自動修正せず停止しました。`);
      }

      if (findResultByTokenId_(ss, 'thinking', tokenForResult.token_id)) {
        summary.results_skipped_existing++;
        return;
      }

      appendLegacyThinkingResult_(ss, tokenForResult, participant, legacyResult);
      summary.results_migrated++;
    });
  });

  console.log(JSON.stringify(summary));
  try { SpreadsheetApp.getUi().alert(`v3移行コピー完了\n${JSON.stringify(summary, null, 2)}\n\n旧tokens/resultsは変更していません。`); } catch (_) {}
  return summary;
}

function assertSetupTarget_(ss) {
  const allowed = PropertiesService.getScriptProperties().getProperty(V3.SETUP_ALLOWED_ID_PROPERTY);
  const actual = ss.getId();
  if (!allowed || allowed !== actual) {
    throw new Error(
      `安全装置により停止しました。複製したスプレッドシートのIDをスクリプトプロパティ「${V3.SETUP_ALLOWED_ID_PROPERTY}」に設定してください。\n` +
      `現在のID: ${actual}`
    );
  }
}

function ensureExactSheet_(ss, name, headers) {
  let sheet = ss.getSheetByName(name);
  if (!sheet) {
    sheet = ss.insertSheet(name);
    sheet.getRange(1,1,1,headers.length).setValues([headers]);
    sheet.setFrozenRows(1);
    return sheet;
  }

  if (sheet.getLastRow() === 0) {
    sheet.getRange(1,1,1,headers.length).setValues([headers]);
    sheet.setFrozenRows(1);
    return sheet;
  }

  if (sheet.getLastColumn() < headers.length) {
    throw new Error(`「${name}」シートの列数がv3定義より少ないため、自動変更せず停止しました。`);
  }
  const actual = sheet.getRange(1,1,1,headers.length).getValues()[0].map(String);
  const mismatch = headers.findIndex((h,i)=>actual[i] !== h);
  if (mismatch >= 0) {
    throw new Error(`「${name}」シートの${mismatch+1}列目がv3定義と一致しません（期待: ${headers[mismatch]} / 実際: ${actual[mismatch]}）。自動修正せず停止しました。`);
  }
  return sheet;
}

// ============================================================
// Legacy migration helpers
// ============================================================

function readLegacyTokens_(sheet) {
  const out = {};
  if (!sheet || sheet.getLastRow() < 2) return out;
  const cols = Math.max(9, sheet.getLastColumn());
  const data = sheet.getRange(2,1,sheet.getLastRow()-1,cols).getValues();
  data.forEach((r,i)=>{
    const code = normalizeTokenCode_(r[0]);
    if (!code || out[code]) return;
    out[code] = {
      token_code:code,
      legacy_row:i+2,
      name:cleanText_(r[5] || r[1]),
      birthdate:normalizeLegacyDateValue_(r[6]),
      org:cleanText_(r[7]),
      dept:cleanText_(r[8]),
    };
  });
  return out;
}

function readLegacyThinkingGroups_(sheet) {
  const out = {};
  if (!sheet || sheet.getLastRow() < 2) return out;
  const width = Math.max(12, sheet.getLastColumn());
  const data = sheet.getRange(2,1,sheet.getLastRow()-1,width).getValues();
  data.forEach((r,i)=>{
    const code = normalizeTokenCode_(r[1]);
    if (!code) return;
    if (!out[code]) out[code] = [];
    out[code].push({
      legacy_row:i+2,
      timestamp:r[0],
      token_code:code,
      diag_date:r[2],
      name:cleanText_(r[3]),
      birthdate:normalizeLegacyDateValue_(r[4]),
      org:cleanText_(r[5]),
      dept:cleanText_(r[6]),
      score_A:Number(r[7] || 0),
      score_B:Number(r[8] || 0),
      score_C:Number(r[9] || 0),
      score_D:Number(r[10] || 0),
      type_label:cleanText_(r[11]),
    });
  });
  return out;
}

function mergeLegacyParticipantInfo_(legacyToken, results) {
  const latest = results.length ? results[results.length-1] : {};
  return {
    name:cleanText_((legacyToken && legacyToken.name) || latest.name),
    birthdate:cleanText_((legacyToken && legacyToken.birthdate) || latest.birthdate),
    org:cleanText_((legacyToken && legacyToken.org) || latest.org),
    dept:cleanText_((legacyToken && legacyToken.dept) || latest.dept),
  };
}

function createLegacyParticipant_(ss, info) {
  const now = new Date();
  const participantId = generateUniqueId_(ss, 'P', 'participant');
  const row = [participantId,info.name || '',info.birthdate || '',info.org || '',info.dept || '','',now,now];
  ss.getSheetByName(V3.SHEETS.PARTICIPANTS).appendRow(row);
  return rowToParticipant_(row, -1);
}

function appendLegacyToken_(ss, x) {
  const tokenId = generateUniqueId_(ss, 'T', 'token');
  const row = [tokenId,x.token_code,x.batch_id,x.issue_no,'thinking',x.participant_id || '','','','','',x.issued_by || 'legacy-migration'];
  const sheet = ss.getSheetByName(V3.SHEETS.TOKENS);
  sheet.appendRow(row);
  return rowToToken_(row, sheet.getLastRow());
}

function appendLegacyHistoryToken_(ss, batchId, participantId, attemptNo) {
  const tokenId = generateUniqueId_(ss, 'T', 'token');
  const code = generateUniqueTokenCode_(ss, {
    style:'hybrid',prefix:'TS-LEGACY',issueNo:attemptNo,
    padWidth:3,randomLength:8,hybridSuffixLength:5,
  });
  const row = [
    tokenId,
    code,
    batchId,
    attemptNo,
    'thinking',
    participantId || '',
    '', // issued_at unknown
    '', // expires_at
    '', // revoked_at
    '', // assigned_at unknown
    'legacy-migration',
  ];
  const sheet = ss.getSheetByName(V3.SHEETS.TOKENS);
  sheet.appendRow(row);
  return rowToToken_(row, sheet.getLastRow());
}

function findTokenByBatchIssue_(ss, batchId, diagType, issueNo) {
  const sheet = ss.getSheetByName(V3.SHEETS.TOKENS);
  if (!sheet || sheet.getLastRow() < 2) return null;
  const data = sheet.getRange(2,1,sheet.getLastRow()-1,HEADERS.assessment_tokens.length).getValues();
  for (let i=0;i<data.length;i++) {
    if (cleanText_(data[i][2]) !== cleanText_(batchId)) continue;
    if (normalizeDiagType_(data[i][4]) !== normalizeDiagType_(diagType)) continue;
    if (Number(data[i][3] || 0) !== Number(issueNo)) continue;
    return rowToToken_(data[i], i+2);
  }
  return null;
}

function appendLegacyThinkingResult_(ss, token, participant, legacy) {
  const resultId = generateUniqueId_(ss, 'R', 'result');
  const diagDate = normalizeLegacyDiagDate_(legacy.diag_date);
  const completedAt = asDate_(legacy.timestamp) || legacy.timestamp || '';
  const row = [
    resultId,token.token_id,participant.participant_id,diagDate,
    legacy.name || participant.name,legacy.org || participant.org,legacy.dept || participant.dept,
    legacy.score_A,legacy.score_B,legacy.score_C,legacy.score_D,legacy.type_label,
    'thinking-legacy-v1','',completedAt,
  ];
  ss.getSheetByName(V3.SHEETS.THINKING).appendRow(row);
}

// ============================================================
// Sheet lookup helpers
// ============================================================

function assertRuntimeSheets_(ss) {
  const required = [V3.SHEETS.PARTICIPANTS,V3.SHEETS.TOKENS,V3.SHEETS.THINKING,V3.SHEETS.BEHAVIOR,V3.SHEETS.NEEDS];
  const missing = required.filter(n=>!ss.getSheetByName(n));
  if (missing.length) throw new Error(`v3シートが不足しています: ${missing.join(', ')}`);
}

function findParticipantById_(ss, participantId) {
  const id = cleanText_(participantId);
  if (!id) return null;
  const sheet = ss.getSheetByName(V3.SHEETS.PARTICIPANTS);
  if (!sheet || sheet.getLastRow() < 2) return null;
  const data = sheet.getRange(2,1,sheet.getLastRow()-1,HEADERS.participants.length).getValues();
  for (let i=0;i<data.length;i++) {
    if (cleanText_(data[i][0]) === id) return rowToParticipant_(data[i], i+2);
  }
  return null;
}

function findTokenByCode_(ss, tokenCode) {
  const code = normalizeTokenCode_(tokenCode);
  if (!code) return null;
  const sheet = ss.getSheetByName(V3.SHEETS.TOKENS);
  if (!sheet || sheet.getLastRow() < 2) return null;
  const data = sheet.getRange(2,1,sheet.getLastRow()-1,HEADERS.assessment_tokens.length).getValues();
  for (let i=0;i<data.length;i++) {
    if (normalizeTokenCode_(data[i][1]) === code) return rowToToken_(data[i], i+2);
  }
  return null;
}

function findTokenById_(ss, tokenId) {
  const id = cleanText_(tokenId);
  if (!id) return null;
  const sheet = ss.getSheetByName(V3.SHEETS.TOKENS);
  if (!sheet || sheet.getLastRow() < 2) return null;
  const data = sheet.getRange(2,1,sheet.getLastRow()-1,HEADERS.assessment_tokens.length).getValues();
  for (let i=0;i<data.length;i++) {
    if (cleanText_(data[i][0]) === id) return rowToToken_(data[i], i+2);
  }
  return null;
}

function findTokenByCodeOrId_(ss, value) {
  return findTokenById_(ss, value) || findTokenByCode_(ss, value);
}

function findResultByTokenId_(ss, diagType, tokenId) {
  const type = normalizeDiagType_(diagType);
  if (!type) return null;
  const sheet = ss.getSheetByName(DIAGNOSTICS[type].resultSheet);
  if (!sheet || sheet.getLastRow() < 2) return null;
  const width = HEADERS[DIAGNOSTICS[type].resultSheet].length;
  const data = sheet.getRange(2,1,sheet.getLastRow()-1,width).getValues();
  for (let i=0;i<data.length;i++) {
    if (cleanText_(data[i][1]) === tokenId) {
      return {
        row:i+2,
        result_id:cleanText_(data[i][0]),
        token_id:cleanText_(data[i][1]),
        participant_id:cleanText_(data[i][2]),
      };
    }
  }
  return null;
}

function rowToParticipant_(r, row) {
  return {
    row,
    participant_id:cleanText_(r[0]),
    name:cleanText_(r[1]),
    birthdate:normalizeLegacyDateValue_(r[2]),
    org:cleanText_(r[3]),
    dept:cleanText_(r[4]),
    external_member_id:cleanText_(r[5]),
    created_at:r[6] || '',
    updated_at:r[7] || '',
  };
}

function rowToToken_(r, row) {
  return {
    row,
    token_id:cleanText_(r[0]),
    token_code:normalizeTokenCode_(r[1]),
    batch_id:cleanText_(r[2]),
    issue_no:Number(r[3] || 0),
    diag_type:normalizeDiagType_(r[4]),
    participant_id:cleanText_(r[5]),
    issued_at:r[6] || '',
    expires_at:r[7] || '',
    revoked_at:r[8] || '',
    assigned_at:r[9] || '',
    issued_by:cleanText_(r[10]),
  };
}

// ============================================================
// ID / token generation
// ============================================================

function generateUniqueId_(ss, prefix, kind) {
  for (let i=0;i<20;i++) {
    const id = `${prefix}_${uuidToSafe_(Utilities.getUuid()).slice(0,16)}`;
    if (kind === 'participant' && !findParticipantById_(ss, id)) return id;
    if (kind === 'token' && !findTokenById_(ss, id)) return id;
    if (kind === 'result' && !resultIdExists_(ss, id)) return id;
  }
  throw new Error('一意IDの生成に失敗しました。');
}

function resultIdExists_(ss, resultId) {
  return Object.keys(DIAGNOSTICS).some(type => {
    const sheet = ss.getSheetByName(DIAGNOSTICS[type].resultSheet);
    if (!sheet || sheet.getLastRow() < 2) return false;
    const vals = sheet.getRange(2,1,sheet.getLastRow()-1,1).getValues();
    return vals.some(r=>cleanText_(r[0]) === resultId);
  });
}

function generateUniqueTokenCode_(ss, x) {
  const padWidth = Number.isInteger(x.padWidth) && x.padWidth > 0 ? x.padWidth : 3;
  const issue = String(x.issueNo).padStart(padWidth,'0');

  if (x.style === 'sequential') {
    const code = `${x.prefix}-${issue}`;
    if (findTokenByCode_(ss, code)) {
      throw new Error(`token_code「${code}」は既に存在します。batchごとにtokenPrefixを変えるか、hybrid/random方式を使用してください。`);
    }
    return code;
  }

  for (let i=0;i<30;i++) {
    let code;
    if (x.style === 'random') {
      code = `${x.prefix}-${safeRandom_(Math.max(4, Number(x.randomLength) || 8))}`;
    } else {
      code = `${x.prefix}-${issue}-${safeRandom_(Math.max(3, Number(x.hybridSuffixLength) || 4))}`;
    }
    if (!findTokenByCode_(ss, code)) return code;
  }
  throw new Error('一意なtoken_codeの生成に失敗しました。');
}

function issueNoExists_(ss, batchId, diagType, issueNo) {
  const sheet = ss.getSheetByName(V3.SHEETS.TOKENS);
  if (!sheet || sheet.getLastRow() < 2) return false;
  const data = sheet.getRange(2,1,sheet.getLastRow()-1,HEADERS.assessment_tokens.length).getValues();
  return data.some(r =>
    cleanText_(r[2]) === cleanText_(batchId) &&
    normalizeDiagType_(r[4]) === diagType &&
    Number(r[3] || 0) === Number(issueNo)
  );
}

function nextIssueNo_(ss, batchId, diagType) {
  const sheet = ss.getSheetByName(V3.SHEETS.TOKENS);
  if (!sheet || sheet.getLastRow() < 2) return 1;
  const data = sheet.getRange(2,1,sheet.getLastRow()-1,HEADERS.assessment_tokens.length).getValues();
  let max = 0;
  data.forEach(r=>{
    if (cleanText_(r[2]) !== cleanText_(batchId)) return;
    if (normalizeDiagType_(r[4]) !== diagType) return;
    const n = Number(r[3] || 0);
    if (Number.isInteger(n) && n > max) max = n;
  });
  return max + 1;
}

function safeRandom_(length) {
  let out = '';
  while (out.length < length) out += uuidToSafe_(Utilities.getUuid());
  return out.slice(0,length);
}

function uuidToSafe_(uuid) {
  // 0/O, 1/I/l を避ける16文字。UUIDの各hex nibbleを1対1で写像する。
  const alphabet = '23456789ABCDEFGH';
  return String(uuid || '').replace(/-/g,'').toLowerCase().split('').map(ch=>{
    const n = parseInt(ch,16);
    return Number.isFinite(n) ? alphabet[n] : '';
  }).join('');
}

// ============================================================
// Normalization helpers
// ============================================================

function normalizeTokenCode_(v) {
  return String(v || '').trim().toUpperCase().replace(/\s+/g,'');
}

function normalizeTokenPrefix_(v) {
  return normalizeTokenCode_(v).replace(/^-+|-+$/g,'');
}

function normalizeDiagType_(v) {
  const s = String(v || '').trim().toLowerCase();
  return Object.prototype.hasOwnProperty.call(DIAGNOSTICS, s) ? s : '';
}

function isTokenPrefixConsistent_(tokenCode, diagType) {
  const expected = DIAGNOSTICS[diagType] && DIAGNOSTICS[diagType].prefix;
  if (!expected) return false;
  return normalizeTokenCode_(tokenCode).split('-')[0] === expected;
}

function cleanText_(v) {
  return String(v == null ? '' : v).trim();
}

function normalizeSearchText_(v) {
  return cleanText_(v).toLowerCase().replace(/[\s　]+/g,'');
}

function hasValue_(v) {
  return !(v == null || v === '');
}

function normalizeAnswersJson_(v) {
  if (v == null || v === '') {
    return { ok:false, code:'missing_answers', message:'回答データがありません。' };
  }

  let json;
  try {
    json = typeof v === 'string' ? JSON.stringify(JSON.parse(v)) : JSON.stringify(v);
  } catch (_) {
    return { ok:false, code:'invalid_answers_json', message:'回答データの形式が不正です。' };
  }

  if (json.length > V3.MAX_ANSWERS_JSON_LENGTH) {
    return { ok:false, code:'answers_too_large', message:'回答データが大きすぎます。' };
  }
  return { ok:true, value:json };
}

function normalizeRequiredDiagDate_(v, ss) {
  let raw = cleanText_(v);
  if (!raw) {
    const tz = ss.getSpreadsheetTimeZone() || Session.getScriptTimeZone() || 'Asia/Tokyo';
    raw = Utilities.formatDate(new Date(), tz, 'yyyy-MM-dd');
  }
  const parsed = parseYmd_(raw);
  if (!parsed) {
    return { ok:false, code:'invalid_diag_date', message:'診断日は YYYY-MM-DD 形式で入力してください。' };
  }
  return { ok:true, value:parsed };
}

function normalizeOptionalDate_(v) {
  const raw = cleanText_(v);
  if (!raw) return { ok:true, value:'' };
  const parsed = parseYmd_(raw);
  return parsed ? { ok:true, value:parsed } : { ok:false, value:'' };
}

function parseYmd_(v) {
  if (v instanceof Date && !isNaN(v)) {
    const tz = Session.getScriptTimeZone() || 'Asia/Tokyo';
    return Utilities.formatDate(v, tz, 'yyyy-MM-dd');
  }
  const s = cleanText_(v).replace(/[\.\/]/g,'-');
  const m = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
  if (!m) return '';
  const y = Number(m[1]), mo = Number(m[2]), d = Number(m[3]);
  const date = new Date(y, mo-1, d);
  if (date.getFullYear() !== y || date.getMonth() !== mo-1 || date.getDate() !== d) return '';
  return `${String(y).padStart(4,'0')}-${String(mo).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
}

function parseExpiry_(v) {
  if (v == null || v === '') return '';
  if (v instanceof Date && !isNaN(v)) return v;
  const s = cleanText_(v);
  const ymd = parseYmd_(s);
  if (ymd) {
    const parts = ymd.split('-').map(Number);
    return new Date(parts[0],parts[1]-1,parts[2],23,59,59,999);
  }
  const dt = new Date(s);
  if (!isNaN(dt)) return dt;
  throw new Error('expiresAtの形式が不正です。DateまたはYYYY-MM-DDを指定してください。');
}

function asDate_(v) {
  if (v instanceof Date && !isNaN(v)) return v;
  if (v == null || v === '') return null;
  const d = new Date(v);
  return isNaN(d) ? null : d;
}

function normalizeLegacyDateValue_(v) {
  if (v instanceof Date && !isNaN(v)) {
    const tz = Session.getScriptTimeZone() || 'Asia/Tokyo';
    return Utilities.formatDate(v, tz, 'yyyy-MM-dd');
  }
  const parsed = parseYmd_(v);
  return parsed || cleanText_(v);
}

function normalizeLegacyDiagDate_(v) {
  const parsed = parseYmd_(v);
  return parsed || cleanText_(v);
}

function getActiveUserLabel_() {
  try {
    return Session.getActiveUser().getEmail() || 'manual';
  } catch (_) {
    return 'manual';
  }
}
