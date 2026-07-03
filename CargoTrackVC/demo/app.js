const $ = (selector) => document.querySelector(selector);
const apiInput = $("#apiUrl");

const sampleOrder = {
  numero_ordem: "OT-2026-0001",
  chave_ordem: "SHIP-2026-0001",
  embarcador: "Agro Origem Ltda",
  cnpj_embarcador: "12345678000195",
  transportadora: "TransLog Brasil",
  cnpj_transportadora: "22345678000190",
  motorista_nome: "Ana Motorista",
  cpf_motorista: "12345678901",
  placa: "ABC1D23",
  recebedor: "CD Santos",
  cnpj_recebedor: "32345678000191",
  origem: "Rondonopolis/MT",
  destino: "Santos/SP",
  descricao_carga: "Carga paletizada de alimentos",
  quantidade: 18000,
  unidade: "kg",
  valor_frete: 9500,
  data_coleta_prevista: new Date().toISOString()
};

const steps = [
  {
    title: "Embarcador cria a ordem",
    lead: "A operacao nasce como uma ordem de transporte com carga, rota, transportadora, motorista e recebedor.",
    behind: "POST /ordens grava a ordem, aplica idempotencia por chave_ordem e registra auditoria.",
    status: "Ordem criada pelo embarcador",
    action: createOrder
  },
  {
    title: "Transportadora aceita a carga",
    lead: "Ao aceitar, a transportadora transforma a ordem em um documento digital para o motorista.",
    behind: "POST /ordens/{id}/aceite emite VC-OrdemTransporte e VC-EventoLogistico.",
    status: "Documento digital emitido",
    action: acceptOrder
  },
  {
    title: "Motorista recebe a wallet",
    lead: "O motorista consulta pelo CPF e baixa as credenciais da viagem.",
    behind: "GET /ordens?cpf=... e GET /ordens/{id}/documento?cpf=... retornam JSON-LD assinado.",
    status: "Wallet carregada",
    action: downloadDocument
  },
  {
    title: "Recebedor assina a entrega",
    lead: "No destino, o recebedor confirma nome, documento, localizacao e observacao.",
    behind: "POST /ordens/{id}/entrega muda o status para entregue e emite VC-ComprovanteEntrega.",
    status: "Comprovante emitido",
    action: signDelivery
  },
  {
    title: "Comprovante verificavel",
    lead: "O comprovante final pode ser exibido como QR Code e validado por outro sistema.",
    behind: "A verificacao usa o documento JSON-LD, a assinatura e o cache de chaves publicas.",
    status: "Entrega verificavel",
    action: renderProof
  }
];

const state = {
  step: 0,
  ordemId: null,
  documento: [],
  comprovante: null,
  online: false
};

function api(path, options = {}) {
  return fetch(`${apiInput.value}${path}`, {
    headers: {"Content-Type": "application/json"},
    ...options
  }).then(async (response) => {
    const text = await response.text();
    const data = text ? JSON.parse(text) : {};
    if (!response.ok) throw new Error(data.detail?.message || data.detail?.message || response.statusText);
    return data;
  });
}

async function createOrder() {
  const data = await api("/ordens", {method: "POST", body: JSON.stringify(sampleOrder)});
  state.ordemId = data.ordem_id;
  toast("Ordem criada");
}

async function acceptOrder() {
  if (!state.ordemId) await createOrder();
  await api(`/ordens/${state.ordemId}/aceite`, {method: "POST"});
  toast("Transportadora aceitou a carga");
}

async function downloadDocument() {
  if (!state.ordemId) await acceptOrder();
  const list = await api(`/ordens?cpf=${sampleOrder.cpf_motorista}`);
  const doc = await api(`/ordens/${state.ordemId}/documento?cpf=${sampleOrder.cpf_motorista}`);
  state.documento = doc.verifiableCredential || [];
  toast(`${list.length || 1} ordem encontrada na wallet`);
}

async function signDelivery() {
  if (!state.ordemId) await downloadDocument();
  const data = await api(`/ordens/${state.ordemId}/entrega`, {
    method: "POST",
    body: JSON.stringify({
      recebedor_nome: "Bruno Recebedor",
      documento_recebedor: "1234567",
      latitude: -23.9608,
      longitude: -46.3336,
      observacao: "Carga recebida sem avarias."
    })
  });
  state.comprovante = data.verifiableCredential?.[0];
  toast("Entrega assinada");
}

function renderProof() {
  if (!state.comprovante && state.documento.length) state.comprovante = state.documento.at(-1);
  render();
  toast("Comprovante pronto para verificacao");
}

function render() {
  const current = steps[state.step];
  $("#guideTitle").textContent = current.title;
  $("#guideLead").textContent = current.lead;
  $("#behind").textContent = current.behind;
  $("#stageStatus").textContent = current.status;
  $("#eventTitle").textContent = current.title;
  $("#eventText").textContent = current.lead;
  $("#eventAction").textContent = state.step === steps.length - 1 ? "Gerar comprovante" : "Executar";

  $("#steps").innerHTML = steps.map((step, index) => `
    <li class="${index === state.step ? "active" : ""} ${index < state.step ? "done" : ""}">
      <span>${index + 1}</span>
      <p>${step.title}</p>
    </li>
  `).join("");

  $("#driver").innerHTML = `
    <div class="appbar"><b>Wallet motorista</b><span>${sampleOrder.placa}</span></div>
    <div class="card">
      <small>Ordem</small>
      <h3>${sampleOrder.numero_ordem}</h3>
      <p>${sampleOrder.origem} → ${sampleOrder.destino}</p>
    </div>
    <div class="list">
      <div><b>Carga</b><span>${sampleOrder.descricao_carga}</span></div>
      <div><b>Status</b><span>${state.comprovante ? "Entregue" : state.documento.length ? "Documento baixado" : state.ordemId ? "Criada" : "Aguardando"}</span></div>
      <div><b>Credenciais</b><span>${state.documento.length}</span></div>
    </div>
  `;

  const proofPayload = JSON.stringify(state.comprovante || {ordem: state.ordemId, status: "aguardando"}, null, 2);
  $("#inspector").innerHTML = `
    <div class="appbar"><b>Recebedor</b><span>Proof of delivery</span></div>
    <div class="card success">
      <small>Comprovante</small>
      <h3>${state.comprovante ? "VALIDO" : "Pendente"}</h3>
      <p>${state.comprovante ? "VC-ComprovanteEntrega emitida" : "Aguardando assinatura"}</p>
    </div>
    <div id="qr" class="qr"></div>
    <pre>${proofPayload.slice(0, 360)}</pre>
  `;
  const qr = $("#qr");
  qr.innerHTML = "";
  if (window.qrcode && state.comprovante) {
    const code = qrcode(0, "M");
    code.addData(JSON.stringify({id: state.comprovante.id, type: state.comprovante.type}));
    code.make();
    qr.innerHTML = code.createSvgTag({cellSize: 3, margin: 1});
  } else {
    qr.textContent = "QR";
  }
}

async function runCurrent() {
  const button = $("#next");
  button.disabled = true;
  try {
    await steps[state.step].action();
    if (state.step < steps.length - 1) state.step += 1;
  } catch (error) {
    toast(error.message || "Falha ao executar etapa");
  } finally {
    button.disabled = false;
    render();
  }
}

function toast(message) {
  $("#toast").textContent = message;
  $("#toast").classList.add("show");
  setTimeout(() => $("#toast").classList.remove("show"), 2200);
}

$("#next").addEventListener("click", runCurrent);
$("#eventAction").addEventListener("click", runCurrent);
$("#prev").addEventListener("click", () => {
  state.step = Math.max(0, state.step - 1);
  render();
});
$("#reset").addEventListener("click", () => {
  Object.assign(state, {step: 0, ordemId: null, documento: [], comprovante: null});
  render();
});
$("#testApi").addEventListener("click", async () => {
  try {
    await api("/health");
    $("#apiState span").textContent = "API conectada";
    $("#apiState").classList.add("ok");
  } catch {
    $("#apiState span").textContent = "API indisponivel";
    $("#apiState").classList.remove("ok");
  }
});

document.querySelectorAll(".tabs button").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".tabs button").forEach((item) => item.classList.remove("active"));
    document.querySelectorAll(".actor").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    document.querySelector(`[data-panel="${button.dataset.tab}"]`)?.classList.add("active");
  });
});

render();

