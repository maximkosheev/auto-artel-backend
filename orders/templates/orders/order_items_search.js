const ASSORTMENT_SEARCH_URL      = "{% url 'orders:assortment_search_results' %}";
const FULL_SEARCH_URL = "{% url 'orders:items_full_search_results' %}";
const HAS_ORDER       = {% if order %}true{% else %}false{% endif %};
const ADD_URL         = {% if order %}"{% url 'orders:add_order_item' order.id %}"{% else %}null{% endif %};
const CSRF_TOKEN      = "{{ csrf_token }}";

/* ── Helpers ── */
function setSearchLoading(loading) {
  document.getElementById("searchBtnText").classList.toggle("d-none", loading);
  document.getElementById("searchBtnSpinner").classList.toggle("d-none", !loading);
  document.getElementById("searchBtn").disabled = loading;
}

function showError(msg) {
  const el = document.getElementById("searchError");
  el.textContent = msg;
  el.classList.remove("d-none");
}

function hideError() {
  document.getElementById("searchError").classList.add("d-none");
}

function formatPrice(price) {
  return new Intl.NumberFormat("ru-RU", {style: "currency", currency: "RUB"}).format(price);
}

function escHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function escAttr(str) {
  return String(str ?? "").replace(/'/g, "&#39;").replace(/"/g, "&quot;");
}

/* ── Assortment search (step 1) ── */
document.getElementById("searchForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  hideError();
  showAssortmentPhase();

  const articleNumber = document.getElementById("articleInput").value.trim();
  if (!articleNumber) return;

  setSearchLoading(true);

  const formData = new FormData();
  formData.append("article_number", articleNumber);
  formData.append("csrfmiddlewaretoken", CSRF_TOKEN);

  try {
    const resp = await fetch(ASSORTMENT_SEARCH_URL, {method: "POST", body: formData});
    const data = await resp.json();

    if (!resp.ok) {
      showError(data.error || "Ошибка при обращении к поставщику.");
      document.getElementById("resultsSection").classList.add("d-none");
      document.getElementById("emptyState").classList.add("d-none");
      return;
    }

    renderAssortmentResults(data.items, articleNumber);
  } catch (err) {
    showError("Сетевая ошибка. Попробуйте снова.");
  } finally {
    setSearchLoading(false);
  }
});

function renderAssortmentResults(items, articleNumber) {
  const body    = document.getElementById("resultsBody");
  const section = document.getElementById("resultsSection");
  const empty   = document.getElementById("emptyState");

  body.innerHTML = "";

  if (!items || items.length === 0) {
    section.classList.add("d-none");
    empty.classList.remove("d-none");
    return;
  }

  empty.classList.add("d-none");
  section.classList.remove("d-none");

  document.getElementById("resultCount").textContent = items.length;
  document.getElementById("searchedArticle").textContent = `Артикул: ${articleNumber}`;

  items.forEach(item => {
    const tr = document.createElement("tr");
    tr.dataset.pin   = item.article_number;
    tr.dataset.manufacture = item.manufacture;
    tr.innerHTML = `
      <td><code>${escHtml(item.article_number)}</code></td>
      <td>${escHtml(item.manufacture)}</td>
      <td>${escHtml(item.name)}</td>
    `;
    tr.addEventListener("click", handleAssortmentRowClick);
    body.appendChild(tr);
  });
}

/* ── Full search (step 2) ── */
async function handleAssortmentRowClick(e) {
  const tr    = e.currentTarget;
  const pin   = tr.dataset.pin;
  const manufacture = tr.dataset.manufacture;

  showFullResultsPhase(pin, manufacture);

  const formData = new FormData();
  formData.append("article_number", pin);
  formData.append("manufacture", manufacture);
  formData.append("csrfmiddlewaretoken", CSRF_TOKEN);

  try {
    const resp = await fetch(FULL_SEARCH_URL, {method: "POST", body: formData});
    const data = await resp.json();

    if (!resp.ok) {
      showError(data.error || "Ошибка при обращении к поставщику.");
      showAssortmentPhase();
      return;
    }

    renderFullResults(data.items, manufacture);
  } catch (err) {
    showError("Сетевая ошибка. Попробуйте снова.");
    showAssortmentPhase();
  }
}

function renderFullResults(items, manufacture) {
  const body      = document.getElementById("fullResultsBody");
  const tableWrap = document.getElementById("fullResultsTableWrap");
  const loading   = document.getElementById("fullResultsLoading");
  const empty     = document.getElementById("fullEmptyState");

  loading.classList.add("d-none");
  body.innerHTML = "";

  if (!items || items.length === 0) {
    empty.classList.remove("d-none");
    return;
  }

  document.getElementById("fullResultCount").textContent = items.length;
  tableWrap.classList.remove("d-none");

  const colSpan   = HAS_ORDER ? 8 : 7;
  const matched   = items.filter(i => i.manufacture === manufacture);
  const analogs   = items.filter(i => i.manufacture !== manufacture);

  if (matched.length > 0) {
    appendGroupHeader(body, escHtml(manufacture), colSpan);
    matched.forEach(item => appendResultRow(body, item));
  }

  if (analogs.length > 0) {
    appendGroupHeader(body, "Аналоги", colSpan);
    analogs.forEach(item => appendResultRow(body, item));
  }

  if (HAS_ORDER) {
    body.querySelectorAll(".add-to-order-btn").forEach(btn => {
      btn.addEventListener("click", handleAddToOrder);
    });
  }
}

function appendGroupHeader(tbody, label, colSpan) {
  const tr = document.createElement("tr");
  tr.innerHTML = `
    <td colspan="${colSpan}" class="fw-semibold text-secondary small px-3 py-2"
        style="background:#f8f9fa; border-top: 2px solid #dee2e6; letter-spacing:.03em;">
      ${label}
    </td>`;
  tbody.appendChild(tr);
}

function appendResultRow(tbody, item) {
  const tr    = document.createElement("tr");
  const count = parseInt(item.count) || 0;
  const addCell = HAS_ORDER ? `
    <td class="text-center">
      <button
        class="btn btn-sm btn-outline-primary add-to-order-btn"
        title="Добавить в заказ"
        data-item='${escAttr(JSON.stringify(item))}'
      >
        <i class="bi bi-cart-plus-fill"></i>
      </button>
    </td>` : "";

  tr.innerHTML = `
    <td><code>${escHtml(item.article_number)}</code></td>
    <td>${escHtml(item.manufacture)}</td>
    <td>${escHtml(item.name)}</td>
    <td class="text-end text-nowrap">${formatPrice(item.price)}</td>
    <td class="text-center">
      <span class="badge ${count > 5 ? 'bg-success' : count > 0 ? 'bg-warning text-dark' : 'bg-danger'}">
        ${count}
      </span>
    </td>
    <td>${escHtml(item.delivery_time)}</td>
    <td><small>${escHtml(item.warehouse_location)}</small></td>
    ${addCell}
  `;
  tbody.appendChild(tr);
}

/* ── Phase transitions ── */
function showAssortmentPhase() {
  document.getElementById("fullResultsSection").classList.add("d-none");
  document.getElementById("fullResultsLoading").classList.add("d-none");
  document.getElementById("fullResultsTableWrap").classList.add("d-none");
  document.getElementById("fullEmptyState").classList.add("d-none");
}

function showFullResultsPhase(pin, manufacture) {
  document.getElementById("resultsSection").classList.add("d-none");
  document.getElementById("emptyState").classList.add("d-none");

  document.getElementById("fullResultsSection").classList.remove("d-none");
  document.getElementById("fullResultsLoading").classList.remove("d-none");
  document.getElementById("fullResultsTableWrap").classList.add("d-none");
  document.getElementById("fullEmptyState").classList.add("d-none");
  document.getElementById("fullResultCount").textContent = "0";
  document.getElementById("fullSearchedInfo").textContent = `${manufacture} · ${pin}`;
}

document.getElementById("backToAssortmentBtn").addEventListener("click", () => {
  hideError();
  showAssortmentPhase();
  document.getElementById("resultsSection").classList.remove("d-none");
});

/* ── Add to order (only when HAS_ORDER) ── */
async function handleAddToOrder(e) {
  const btn  = e.currentTarget;
  const item = JSON.parse(btn.dataset.item);

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

  try {
    const resp = await fetch(ADD_URL, {
      method: "POST",
      headers: {"Content-Type": "application/json", "X-CSRFToken": CSRF_TOKEN},
      body: JSON.stringify(item),
    });

    const data = await resp.json();

    if (!resp.ok) {
      alert(data.error || "Не удалось добавить позицию.");
      btn.disabled = false;
      btn.innerHTML = '<i class="bi bi-cart-plus-fill"></i>';
      return;
    }

    btn.classList.replace("btn-outline-primary", "btn-success");
    btn.innerHTML = '<i class="bi bi-check-lg"></i>';
    appendOrderItem(data.item);
    showToast(`«${item.name}» добавлен в заказ.`);
  } catch (err) {
    alert("Сетевая ошибка.");
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-cart-plus-fill"></i>';
  }
}

/* ── Order items sidebar ── */
function appendOrderItem(item) {
  const list  = document.getElementById("orderItemsList");
  const badge = document.getElementById("orderItemCount");

  const emptyEl = document.getElementById("emptyOrderItems");
  if (emptyEl) emptyEl.remove();

  const div = document.createElement("div");
  div.className = "list-group-item list-group-item-action py-2 px-3";
  div.innerHTML = `
    <div class="d-flex justify-content-between align-items-start">
      <div>
        <div class="fw-semibold small">${escHtml(item.name)}</div>
        <div class="text-muted" style="font-size:.75rem">
          <code>${escHtml(item.article_number)}</code>
          &nbsp;·&nbsp;${escHtml(item.manufacture)}
        </div>
      </div>
      <span class="badge bg-primary ms-2 text-nowrap">${formatPrice(item.price)}</span>
    </div>
  `;
  list.appendChild(div);
  badge.textContent = parseInt(badge.textContent || "0") + 1;
}

/* ── Toast ── */
function showToast(msg) {
  document.getElementById("toastMessage").textContent = msg;
  bootstrap.Toast.getOrCreateInstance(document.getElementById("addToast"), {delay: 3000}).show();
}
