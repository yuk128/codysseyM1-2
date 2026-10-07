const API = ((window.APP_CONFIG && window.APP_CONFIG.API_BASE_URL) || "").replace(/\/$/, "");
const $ = (selector) => document.querySelector(selector);

let currentConvId = null;
let sending = false;
let dataLimit = 20;
let editingId = null;

const EXAMPLE_QUESTIONS = [
  "가장 추웠던 날은 언제였어?",
  "가장 더웠던 날은?",
  "전체 평균 기온은 얼마야?",
  "최근 기온 추세를 알려줘",
];

// ---------- 공통 ----------
function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// AI 답변: HTML 이스케이프 후 **굵게**와 줄바꿈만 허용
function renderText(text) {
  return escapeHtml(text).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/\n/g, "<br>");
}

function formatDate(iso) {
  const d = new Date(iso);
  if (isNaN(d)) return "";
  return d.toLocaleString("ko-KR", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

let toastTimer = null;
function toast(message, type = "info") {
  const el = $("#toast");
  el.textContent = message;
  el.className = "toast" + (type === "error" ? " error" : "");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.add("hidden"), 3500);
}

function showNotice(message) { const n = $("#notice"); n.textContent = message; n.classList.remove("hidden"); }
function hideNotice() { $("#notice").classList.add("hidden"); }

function errorMessage(data, status) {
  if (data && Array.isArray(data.detail)) return data.detail.map((d) => d.msg).join(", ");
  if (data && typeof data.detail === "string") return data.detail;
  return `요청에 실패했어요 (${status})`;
}

async function api(path, options = {}) {
  const slowTimer = setTimeout(
    () => showNotice("서버를 깨우는 중일 수 있어요. 무료 서버는 첫 요청에 최대 1분 정도 걸릴 수 있습니다…"),
    4000
  );
  try {
    const res = await fetch(API + path, { headers: { "Content-Type": "application/json" }, ...options });
    let data = null;
    try { data = await res.json(); } catch (e) { /* 본문이 없는 응답 */ }
    if (!res.ok) throw new Error(errorMessage(data, res.status));
    return data;
  } catch (e) {
    if (e instanceof TypeError) {
      throw new Error("서버에 연결할 수 없어요. 서버가 켜져 있는지, config.js의 주소를 확인해 주세요.");
    }
    throw e;
  } finally {
    clearTimeout(slowTimer);
    hideNotice();
  }
}

// ---------- 데이터 요약 ----------
async function loadSummary() {
  const box = $("#summary-body");
  try {
    const s = await api("/api/data/summary");
    if (!s.count) { box.textContent = "저장된 데이터가 없어요."; return; }
    const m = s.metrics;
    box.innerHTML = `
      <dl>
        <dt>기간</dt><dd>${escapeHtml(s.period)}</dd>
        <dt>데이터 수</dt><dd>${s.count}개</dd>
        <dt>전체 평균</dt><dd>${m.average}°C</dd>
        <dt>최고</dt><dd>${m.max.value}°C <small>(${escapeHtml(m.max.date)})</small></dd>
        <dt>최저</dt><dd>${m.min.value}°C <small>(${escapeHtml(m.min.date)})</small></dd>
        <dt>최근 7일 평균</dt><dd>${m.recent_7d_average}°C</dd>
        <dt>최근 30일 평균</dt><dd>${m.recent_30d_average}°C</dd>
        <dt>트렌드</dt><dd>${escapeHtml(s.trend)}</dd>
      </dl>`;
  } catch (e) {
    box.textContent = e.message;
  }
}

// ---------- 채팅 ----------
function scrollMessages() { const m = $("#messages"); m.scrollTop = m.scrollHeight; }

function addMessage(role, text) {
  const el = document.createElement("div");
  el.className = `msg ${role}`;
  if (role === "assistant") el.innerHTML = renderText(text);
  else el.textContent = text;
  $("#messages").appendChild(el);
  scrollMessages();
  return el;
}

function addLoading() {
  const el = document.createElement("div");
  el.className = "msg loading";
  el.innerHTML = 'AI가 데이터를 살펴보는 중<span class="dots"></span>';
  $("#messages").appendChild(el);
  scrollMessages();
  return el;
}

function setSending(value) {
  sending = value;
  $("#btn-send").disabled = value;
  $("#chat-input").disabled = value;
  if (!value) $("#chat-input").focus();
}

function showWelcome() {
  const box = $("#messages");
  box.innerHTML = "";
  const welcome = document.createElement("div");
  welcome.className = "welcome";
  welcome.innerHTML = "<div>안녕하세요! 저장된 서울 기온 데이터에 대해 물어보세요.</div>";
  const chips = document.createElement("div");
  chips.className = "chips";
  for (const q of EXAMPLE_QUESTIONS) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "chip";
    b.textContent = q;
    b.addEventListener("click", () => sendMessage(q));
    chips.appendChild(b);
  }
  welcome.appendChild(chips);
  box.appendChild(welcome);
}

function newChat() {
  currentConvId = null;
  $("#chat-title").textContent = "새 대화";
  showWelcome();
  switchTab("chat");
  loadConversations();
}

async function sendMessage(text) {
  text = (text || "").trim();
  if (!text || sending) return;
  const welcome = document.querySelector(".welcome");
  if (welcome) welcome.remove();
  setSending(true);
  addMessage("user", text);
  const loading = addLoading();
  try {
    const data = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message: text, conversation_id: currentConvId }),
    });
    loading.remove();
    addMessage("assistant", data.reply);
    currentConvId = data.conversation_id;
    if (!data.saved) toast("답변은 왔지만 대화 저장에 실패했어요.", "error");
    loadConversations();
  } catch (e) {
    loading.remove();
    addMessage("error", e.message);
  } finally {
    setSending(false);
  }
}

// ---------- 대화 기록 ----------
async function loadConversations() {
  const ul = $("#conv-list");
  try {
    const items = await api("/api/conversations?limit=30");
    ul.innerHTML = "";
    if (!items.length) {
      const li = document.createElement("li");
      li.className = "empty";
      li.textContent = "저장된 대화가 없어요.";
      ul.appendChild(li);
      return;
    }
    for (const c of items) {
      if (c.id === currentConvId) $("#chat-title").textContent = c.title;
      const li = document.createElement("li");
      li.className = "conv-item" + (c.id === currentConvId ? " active" : "");
      li.innerHTML = `
        <button type="button" class="conv-open"><span class="conv-title"></span><span class="conv-meta"></span></button>
        <button type="button" class="ghost conv-del" title="삭제">🗑</button>`;
      li.querySelector(".conv-title").textContent = c.title;
      li.querySelector(".conv-meta").textContent = `${formatDate(c.created_at)} · 메시지 ${c.message_count}개`;
      li.querySelector(".conv-open").addEventListener("click", () => openConversation(c.id));
      li.querySelector(".conv-del").addEventListener("click", () => removeConversation(c.id, c.title));
      ul.appendChild(li);
    }
  } catch (e) {
    ul.innerHTML = "";
    const li = document.createElement("li");
    li.className = "empty";
    li.textContent = e.message;
    ul.appendChild(li);
  }
}

async function openConversation(id) {
  try {
    const conv = await api(`/api/conversations/${encodeURIComponent(id)}`);
    currentConvId = conv.id;
    $("#chat-title").textContent = conv.title;
    const box = $("#messages");
    box.innerHTML = "";
    for (const m of conv.messages) addMessage(m.role, m.content);
    switchTab("chat");
    loadConversations();
  } catch (e) {
    toast(e.message, "error");
    loadConversations();
  }
}

async function removeConversation(id, title) {
  if (!confirm(`'${title}' 대화를 삭제할까요?`)) return;
  try {
    await api(`/api/conversations/${encodeURIComponent(id)}`, { method: "DELETE" });
    toast("대화를 삭제했어요.");
    if (id === currentConvId) newChat();
    else loadConversations();
  } catch (e) {
    toast(e.message, "error");
  }
}

// ---------- 데이터 관리 ----------
async function loadData() {
  const body = $("#data-body");
  try {
    const items = await api(`/api/data?limit=${dataLimit}`);
    body.innerHTML = "";
    for (const item of items) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td></td><td></td><td class="memo"></td>
        <td><div class="row-actions">
          <button type="button" class="ghost btn-edit">수정</button>
          <button type="button" class="ghost btn-del">삭제</button>
        </div></td>`;
      const cells = tr.querySelectorAll("td");
      cells[0].textContent = item.date;
      cells[1].textContent = `${item.value}°C`;
      cells[2].textContent = item.memo || "";
      tr.querySelector(".btn-edit").addEventListener("click", () => openEdit(item));
      tr.querySelector(".btn-del").addEventListener("click", () => removeData(item));
      body.appendChild(tr);
    }
    $("#data-count").textContent = `최신순 ${items.length}개 표시 중`;
    $("#btn-more").classList.toggle("hidden", items.length < dataLimit || dataLimit >= 1000);
  } catch (e) {
    body.innerHTML = "";
    toast(e.message, "error");
  }
}

async function addData(event) {
  event.preventDefault();
  const payload = {
    date: $("#f-date").value,
    value: parseFloat($("#f-value").value),
    memo: $("#f-memo").value.trim(),
  };
  try {
    await api("/api/data", { method: "POST", body: JSON.stringify(payload) });
    toast("데이터를 추가했어요.");
    $("#data-form").reset();
    await Promise.all([loadData(), loadSummary()]);
  } catch (e) { 
    toast(e.message, "error");
  }
}

function openEdit(item) {
  editingId = item.id;
  $("#e-date").value = item.date;
  $("#e-value").value = item.value;
  $("#e-memo").value = item.memo || "";
  $("#edit-dialog").showModal();
}

async function saveEdit(event) {
  event.preventDefault();
  const payload = {
    date: $("#e-date").value,
    value: parseFloat($("#e-value").value),
    memo: $("#e-memo").value.trim(),
  };
  try {
    await api(`/api/data/${encodeURIComponent(editingId)}`, { method: "PUT", body: JSON.stringify(payload) });
    $("#edit-dialog").close();
    toast("데이터를 수정했어요.");
    await Promise.all([loadData(), loadSummary()]);
  } catch (e) {
    toast(e.message, "error");
  }
}

async function removeData(item) {
  if (!confirm(`${item.date} 데이터를 삭제할까요?`)) return;
  try {
    await api(`/api/data/${encodeURIComponent(item.id)}`, { method: "DELETE" });
    toast("데이터를 삭제했어요.");
    await Promise.all([loadData(), loadSummary()]);
  } catch (e) {
    toast(e.message, "error");
  }
}

// ---------- 탭 / 초기화 ----------
function switchTab(name) {
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === name));
  $("#tab-chat").classList.toggle("hidden", name !== "chat");
  $("#tab-data").classList.toggle("hidden", name !== "data");
}

document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => switchTab(t.dataset.tab)));
$("#chat-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const input = $("#chat-input");
  const text = input.value;
  input.value = "";
  sendMessage(text);
});
$("#btn-new-chat").addEventListener("click", newChat);
$("#btn-refresh-summary").addEventListener("click", loadSummary);
$("#data-form").addEventListener("submit", addData);
$("#edit-form").addEventListener("submit", saveEdit);
$("#e-cancel").addEventListener("click", () => $("#edit-dialog").close());
$("#btn-more").addEventListener("click", () => { dataLimit = Math.min(dataLimit + 20, 1000); loadData(); });

showWelcome();
loadSummary();
loadConversations();
loadData();