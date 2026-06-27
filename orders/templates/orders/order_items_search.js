{% load static %}
const ASSORTMENT_SEARCH_URL      = "{% url 'orders:assortment_search_results' %}";
const FULL_SEARCH_URL = "{% url 'orders:items_full_search_results' %}";
const HAS_ORDER       = {% if order %}true{% else %}false{% endif %};
const ADD_URL         = {% if order %}"{% url 'orders:add_order_item' order.id %}"{% else %}null{% endif %};
const CSRF_TOKEN      = "{{ csrf_token }}";
const CART_ICON_URL   = "{% static 'images/shopping_cart.svg' %}";

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
    <td class="text-center align-middle" data-add-cell>
      <div class="d-flex align-items-center gap-1 justify-content-center">
        <input type="number" class="form-control form-control-sm qty-input"
               min="1" value="1" style="width:4rem">
        <button
          class="btn btn-sm btn-primary add-to-order-btn"
          title="Добавить в заказ"
          data-item='${escAttr(JSON.stringify(item))}'
        >
          <img src="${CART_ICON_URL}" width="18" height="18" alt="Добавить в заказ">
        </button>
      </div>
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

  if (HAS_ORDER) {
    const cell = tr.querySelector("[data-add-cell]");
    tr.querySelector(".add-to-order-btn").addEventListener("click", (e) => {
      const qty = Math.max(1, parseInt(cell.querySelector(".qty-input").value) || 1);
      const itemData = JSON.parse(e.currentTarget.dataset.item);
      handleAddToOrder(itemData, qty, cell);
    });
    tr.querySelector(".qty-input").addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        const qty = Math.max(1, parseInt(e.currentTarget.value) || 1);
        handleAddToOrder(item, qty, cell);
      }
    });
  }

  tbody.appendChild(tr);
}

/* ── Add to order ── */
function renderAddCell(cell, item) {
  cell.innerHTML = `
    <div class="d-flex align-items-center gap-1 justify-content-center">
      <input type="number" class="form-control form-control-sm qty-input"
             min="1" value="1" style="width:4rem">
      <button
        class="btn btn-sm btn-primary add-to-order-btn"
        title="Добавить в заказ"
        data-item='${escAttr(JSON.stringify(item))}'
      >
        <img src="${CART_ICON_URL}" width="18" height="18" alt="Добавить в заказ">
      </button>
    </div>
  `;
  cell.querySelector(".add-to-order-btn").addEventListener("click", (e) => {
    const qty = Math.max(1, parseInt(cell.querySelector(".qty-input").value) || 1);
    const itemData = JSON.parse(e.currentTarget.dataset.item);
    handleAddToOrder(itemData, qty, cell);
  });
  cell.querySelector(".qty-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      const qty = Math.max(1, parseInt(e.currentTarget.value) || 1);
      handleAddToOrder(item, qty, cell);
    }
  });
}

async function handleAddToOrder(item, count, cell) {
  const originalHTML = cell.innerHTML;
  cell.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

  try {
    const resp = await fetch(ADD_URL, {
      method: "POST",
      headers: {"Content-Type": "application/json", "X-CSRFToken": CSRF_TOKEN},
      body: JSON.stringify({...item, count}),
    });

    const data = await resp.json();

    if (!resp.ok) {
      alert(data.error || "Не удалось добавить позицию.");
      renderAddCell(cell, item);
      return;
    }

    cell.innerHTML = `<span class="text-success fw-semibold"><i class="bi bi-check-lg"></i> ${count}&nbsp;шт.</span>`;
    setTimeout(() => renderAddCell(cell, item), 1500);
  } catch (err) {
    alert("Сетевая ошибка.");
    renderAddCell(cell, item);
  }
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

