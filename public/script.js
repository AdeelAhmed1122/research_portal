const API = "/api/opportunities";
const $ = (id) => document.getElementById(id);
const FIELDS = ["title", "description", "research_area", "faculty_name",
                "department", "required_skills", "positions", "deadline", "status"];
let items = [];

// ---------- helpers ----------
const esc = (s) => { const d = document.createElement("div"); d.textContent = s ?? ""; return d.innerHTML; };
const fmtDate = (d) => { if (!d) return ""; const [y, m, day] = d.slice(0, 10).split("-").map(Number);
  return new Date(y, m - 1, day).toLocaleDateString(undefined, { dateStyle: "medium" }); };
const today = () => { const t = new Date(); return new Date(t.getFullYear(), t.getMonth(), t.getDate()); };

let toastTimer;
function toast(text, ok = true) {
  const t = $("msg");
  t.textContent = text; t.className = "toast " + (ok ? "ok" : "bad"); t.hidden = false;
  clearTimeout(toastTimer); toastTimer = setTimeout(() => (t.hidden = true), 5000);
}

async function api(url, method = "GET", body) {
  let res;
  try {
    res = await fetch(url, { method, headers: body ? { "Content-Type": "application/json" } : {},
                             body: body ? JSON.stringify(body) : undefined });
  } catch { throw new Error("Cannot reach the server. Is the backend running?"); }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status}).`);
  return data;
}

// ---------- 1. display all ----------
async function load() {
  try { items = await api(API); render(); }
  catch (e) { toast("Could not load opportunities: " + e.message, false); }
}

const skillChips = (t) => (t || "").split(",").map(x => x.trim()).filter(Boolean).map(x => `<span class="chip">${esc(x)}</span>`).join("");
function deadlineBadge(o) {
  const [y, m, d] = o.deadline.slice(0, 10).split("-").map(Number);
  const days = Math.round((new Date(y, m - 1, d) - today()) / 864e5);
  if (o.status === "Closed") return `<span class="dl">Deadline ${fmtDate(o.deadline)}</span>`;
  if (days < 0) return `<span class="dl late">Deadline passed</span>`;
  if (days <= 7) return `<span class="dl soon">⏰ ${days === 0 ? "Closes today" : days + " day" + (days === 1 ? "" : "s") + " left"}</span>`;
  return `<span class="dl">Deadline ${fmtDate(o.deadline)}</span>`;
}
function updateStats() {
  const open = items.filter(o => o.status === "Open");
  $("stTotal").textContent = items.length; $("stOpen").textContent = open.length;
  $("stPos").textContent = open.reduce((n, o) => n + o.positions, 0);
}
function render() {
  updateStats();
  const q = $("search").value.trim().toLowerCase(), st = $("statusFilter").value;
  const view = items.filter(o => (!st || o.status === st) &&
    (!q || [o.title, o.research_area, o.faculty_name, o.department, o.required_skills].join(" ").toLowerCase().includes(q)));
  $("count").textContent = `Showing ${view.length} of ${items.length}`;
  $("list").innerHTML = view.length ? view.map(o => `
    <div class="card ${o.status}">
      <div class="card-head"><h3>${esc(o.title)}</h3><span class="pill ${o.status}">${o.status}</span></div>
      <div class="who">👤 <b>${esc(o.faculty_name)}</b> · ${esc(o.department)}</div>
      <div class="chips"><span class="chip area">🔬 ${esc(o.research_area)}</span>${skillChips(o.required_skills)}</div>
      <p class="desc">${esc(o.description)}</p>
      <div class="foot-row"><span>🎓 ${o.positions} position${o.positions === 1 ? "" : "s"}</span>${deadlineBadge(o)}</div>
      <div class="card-actions">
        <button class="btn primary sm" data-act="view" data-id="${o.id}">Details</button>
        <button class="btn ghost sm" data-act="edit" data-id="${o.id}">Edit</button>
        <button class="btn ghost sm" data-act="toggle" data-id="${o.id}">${o.status === "Open" ? "Mark Closed" : "Reopen"}</button>
        <button class="btn danger sm" data-act="delete" data-id="${o.id}">Delete</button>
      </div>
    </div>`).join("")
    : `<div class="empty"><h3>${items.length ? "No matching opportunities" : "No research opportunities yet"}</h3><p>${items.length ? "Try a different search or filter." : "Click “Post Opportunity” to add the first one."}</p></div>`;
}

// ---------- 2. details ----------
async function showDetails(id) {
  try {
    const o = await api(`${API}/${id}`);
    $("detailBody").innerHTML = `
      <div class="d-head"><h2>${esc(o.title)}</h2><span class="pill ${o.status}">${o.status}</span></div>
      <dl>
        <dt>ID</dt><dd>${o.id}</dd>
        <dt>Description</dt><dd>${esc(o.description)}</dd>
        <dt>Research area</dt><dd>${esc(o.research_area)}</dd>
        <dt>Faculty member</dt><dd>${esc(o.faculty_name)}</dd>
        <dt>Department</dt><dd>${esc(o.department)}</dd>
        <dt>Required skills</dt><dd><div class="chips">${skillChips(o.required_skills)}</div></dd>
        <dt>Positions</dt><dd>${o.positions}</dd>
        <dt>Deadline</dt><dd>${fmtDate(o.deadline)}</dd>
      </dl>
      <div class="actions"><button class="btn primary" id="closeDetail">Close</button></div>`;
    $("closeDetail").onclick = () => $("detailDlg").close();
    $("detailDlg").showModal();
  } catch (e) { toast(e.message, false); load(); }
}

// ---------- 3 & 4. create / update form ----------
function clearErrors() {
  document.querySelectorAll(".err").forEach(e => (e.textContent = ""));
  document.querySelectorAll(".invalid").forEach(e => e.classList.remove("invalid"));
}
function openForm(o) {
  $("oppForm").reset(); clearErrors();
  $("formTitle").textContent = o ? "Edit Opportunity" : "New Opportunity";
  $("oppId").value = o ? o.id : "";
  if (o) FIELDS.forEach(f => ($(f).value = o[f]));
  $("formDlg").showModal();
}

// ---------- 8. validation ----------
function validate(isNew) {
  clearErrors();
  const req = (label) => (v) => (v ? "" : `${label} is required.`);
  const rules = {
    title: (v) => !v ? "Research title is required." : v.length < 5 ? "Title must be at least 5 characters." : "",
    description: (v) => !v ? "Research description is required." : v.length < 20 ? "Description must be at least 20 characters." : "",
    research_area: req("Research area"),
    faculty_name: req("Faculty member's name"),
    department: req("Department"),
    required_skills: req("Required skills"),
    positions: (v) => !v ? "Number of positions is required."
      : !/^\d+$/.test(v) || +v < 1 || +v > 1000 ? "Enter a whole number between 1 and 1000." : "",
    deadline: (v) => !v ? "Application deadline is required."
      : isNew && $("status").value === "Open" && new Date(v + "T00:00:00") < today() ? "Deadline cannot be in the past." : "",
  };
  let ok = true;
  for (const [id, check] of Object.entries(rules)) {
    const msg = check($(id).value.trim());
    if (msg) { ok = false; $(id).classList.add("invalid"); document.querySelector(`[data-for=${id}]`).textContent = msg; }
  }
  return ok;
}

$("oppForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = $("oppId").value;
  if (!validate(!id)) return;
  const body = {};
  FIELDS.forEach(f => (body[f] = $(f).value.trim()));
  body.positions = parseInt(body.positions, 10);
  try {
    const r = await api(id ? `${API}/${id}` : API, id ? "PUT" : "POST", body);
    $("formDlg").close(); toast(r.message); load();
  } catch (err) { toast(err.message, false); }
});

// ---------- 5. open/closed, 6. delete ----------
async function toggleStatus(id) {
  const o = items.find(x => x.id === id);
  const next = o.status === "Open" ? "Closed" : "Open";
  try { const r = await api(`${API}/${id}`, "PUT", { status: next });
        toast(`Status changed to ${next}.`); load(); }
  catch (e) { toast(e.message, false); load(); }
}
async function remove(id) {
  const o = items.find(x => x.id === id);
  if (!confirm(`Delete "${o.title}"? This cannot be undone.`)) return;
  try { const r = await api(`${API}/${id}`, "DELETE"); toast(r.message); load(); }
  catch (e) { toast(e.message, false); load(); }
}

// ---------- events ----------
$("list").addEventListener("click", (e) => {
  const b = e.target.closest("button[data-act]"); if (!b) return;
  const id = +b.dataset.id, o = items.find(x => x.id === id);
  ({ view: () => showDetails(id), edit: () => openForm(o),
     toggle: () => toggleStatus(id), delete: () => remove(id) })[b.dataset.act]();
});
$("newBtn").onclick = () => openForm(null);
$("cancelBtn").onclick = () => $("formDlg").close();
$("search").addEventListener("input", render);
$("statusFilter").onchange = render;
load();
