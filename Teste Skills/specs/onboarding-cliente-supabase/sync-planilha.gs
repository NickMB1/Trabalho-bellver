// Google Apps Script — busca periodicamente os checklists do Supabase (tabela
// checklists) via REST API e espelha cada um numa linha da planilha. Uma
// edição atualiza a linha existente (chave = id do checklist) em vez de criar
// uma linha nova. Cada checklist vai para a aba da planilha correspondente ao
// seu tipo de processo (campo dados.tipo_processo) — ver TIPO_SHEET_MAP.
//
// Como instalar: veja SYNC-PLANILHA.md nesta mesma pasta.

var SUPABASE_URL = 'https://mzbnyeeojtjxyvsxzllb.supabase.co';
var SUPABASE_ANON_KEY = 'sb_publishable_lh8NeKUzcgg8MANMc6hL7A_kUeA0adC';

// Uma aba por tipo de processo.
var TIPO_SHEET_MAP = {
  'Novo cliente': 'Novas empresas',
  'Abertura': 'Aberturas',
  'Alteração': 'Alterações',
  'Transformação': 'Transformação'
};
// Checklists sem tipo de processo definido (fichas antigas, criadas antes
// desse campo existir) caem aqui em vez de serem perdidos.
var SHEET_FALLBACK = 'Sem tipo definido';

// A coluna 'id' fica em A mas oculta (ver getSheet_) — só existe para a
// sincronização achar a linha certa e atualizar em vez de duplicar; não é
// pensada para leitura pelas pessoas que usam a planilha.
var COLUMNS = [
  'id', 'nome_cliente', 'cnpj', 'tipo_processo', 'situacao_processo',
  'criado_por', 'atualizado_por',
  'data_abertura', 'data_liberacao_junta_comercial', 'competencia_inicial',
  'socio_nome', 'socio_cpf', 'socio_telefone', 'socio_email',
  'funcionarios_possui', 'funcionarios_qtd', 'anexos',
  'created_at', 'updated_at'
];

// Roda a cada X minutos (ver criarGatilho). Busca todos os checklists e
// atualiza/insere uma linha por checklist na aba da planilha correspondente
// ao tipo de processo de cada um.
function syncFromSupabase() {
  var url = SUPABASE_URL + '/rest/v1/checklists?select=*&order=updated_at.asc';
  var res = UrlFetchApp.fetch(url, {
    method: 'get',
    headers: {
      apikey: SUPABASE_ANON_KEY,
      Authorization: 'Bearer ' + SUPABASE_ANON_KEY
    },
    muteHttpExceptions: true
  });

  if (res.getResponseCode() !== 200) {
    throw new Error('Supabase respondeu ' + res.getResponseCode() + ': ' + res.getContentText());
  }

  var records = JSON.parse(res.getContentText());

  records.forEach(function (record) {
    var dados = record.dados || {};
    var sheetName = TIPO_SHEET_MAP[dados.tipo_processo] || SHEET_FALLBACK;
    var sheet = getSheet_(sheetName);
    var rowValues = buildRow_(record);
    var rowIndex = findRowById_(sheet, record.id);
    if (rowIndex > 0) {
      sheet.getRange(rowIndex, 1, 1, COLUMNS.length).setValues([rowValues]);
    } else {
      sheet.appendRow(rowValues);
    }
  });
}

// Rode esta função UMA VEZ manualmente (Executar > criarGatilho) para
// instalar o gatilho automático de tempo. Já cuida de não duplicar o
// gatilho se você rodar de novo.
function criarGatilho() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'syncFromSupabase') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('syncFromSupabase')
    .timeBased()
    .everyMinutes(1)
    .create();
}

function getSheet_(sheetName) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(sheetName);
  if (!sheet) {
    sheet = ss.insertSheet(sheetName);
  }
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(COLUMNS);
    sheet.setFrozenRows(1);
    sheet.hideColumns(1);
  }
  return sheet;
}

function findRowById_(sheet, id) {
  var lastRow = sheet.getLastRow();
  if (lastRow < 2) return -1;
  var ids = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
  for (var i = 0; i < ids.length; i++) {
    if (ids[i][0] === id) return i + 2;
  }
  return -1;
}

function buildRow_(record) {
  var dados = record.dados || {};
  var socio = dados.socio || {};
  var func = dados.funcionarios || {};

  return [
    record.id || '',
    record.nome_cliente || '',
    record.cnpj || '',
    dados.tipo_processo || '',
    dados.situacao_processo || '',
    record.criado_por || '',
    record.atualizado_por || '',
    dados.data_abertura || '',
    dados.data_liberacao_junta_comercial || '',
    dados.competencia_inicial || '',
    socio.nome || '',
    socio.cpf || '',
    socio.telefone || '',
    socio.email || '',
    func.possui ? 'Sim' : 'Não',
    func.quantidade || '',
    (dados.anexos || []).join(', '),
    record.created_at || '',
    record.updated_at || ''
  ];
}
