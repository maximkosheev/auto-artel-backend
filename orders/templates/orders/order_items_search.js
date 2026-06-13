const ASSORTMENT_SEARCH_URL      = "{% url 'orders:assortment_search_results' %}";
const FULL_SEARCH_URL = "{% url 'orders:items_full_search_results' %}";
const HAS_ORDER       = {% if order %}true{% else %}false{% endif %};
const ADD_URL         = {% if order %}"{% url 'orders:add_order_item' order.id %}"{% else %}null{% endif %};
const REMOVE_URL      = {% if order %}(id) => `/orders/items/${id}/remove`{% else %}null{% endif %};
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

  if (HAS_ORDER) {
    tr.querySelector(".add-to-order-btn").addEventListener("click", (e) => {
      const cell = e.currentTarget.closest("td");
      const itemData = JSON.parse(e.currentTarget.dataset.item);
      showQtySelector(cell, itemData);
    });
  }

  tbody.appendChild(tr);
}

/* ── Quantity selector ── */
function showQtySelector(cell, item) {
  cell.innerHTML = `
    <div class="d-flex align-items-center gap-1 justify-content-center">
      <input type="number" class="form-control form-control-sm qty-input"
             min="1" value="1" style="width:4rem">
      <button class="btn btn-sm btn-success qty-confirm-btn" title="Добавить">
        <i class="bi bi-check-lg"></i>
      </button>
      <button class="btn btn-sm btn-outline-secondary qty-cancel-btn" title="Отмена">
        <i class="bi bi-x-lg"></i>
      </button>
    </div>
  `;

  const input = cell.querySelector(".qty-input");
  input.focus();
  input.select();

  cell.querySelector(".qty-confirm-btn").addEventListener("click", () => {
    const qty = Math.max(1, parseInt(input.value) || 1);
    handleAddToOrder(item, qty, cell);
  });

  cell.querySelector(".qty-cancel-btn").addEventListener("click", () => {
    restoreCartButton(cell, item);
  });

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      const qty = Math.max(1, parseInt(input.value) || 1);
      handleAddToOrder(item, qty, cell);
    } else if (e.key === "Escape") {
      restoreCartButton(cell, item);
    }
  });
}

function restoreCartButton(cell, item) {
  cell.innerHTML = `
    <button
      class="btn btn-sm btn-outline-primary add-to-order-btn"
      title="Добавить в заказ"
      data-item='${escAttr(JSON.stringify(item))}'
    >
      <i class="bi bi-cart-plus-fill"></i>
    </button>
  `;
  cell.querySelector(".add-to-order-btn").addEventListener("click", (e) => {
    const itemData = JSON.parse(e.currentTarget.dataset.item);
    showQtySelector(cell, itemData);
  });
}

/* ── Add to order ── */
async function handleAddToOrder(item, count, cell) {
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
      restoreCartButton(cell, item);
      return;
    }

    cell.innerHTML = `<span class="text-success fw-semibold"><i class="bi bi-check-lg"></i> ${count}&nbsp;шт.</span>`;
    appendOrderItem(data.item);
    showToast(`«${item.name}» добавлен в заказ.`);
  } catch (err) {
    alert("Сетевая ошибка.");
    restoreCartButton(cell, item);
  }
}

/* ── Order items sidebar ── */
function appendOrderItem(item) {
  const list  = document.getElementById("orderItemsList");
  const badge = document.getElementById("orderItemCount");

  const emptyEl = document.getElementById("emptyOrderItems");
  if (emptyEl) emptyEl.remove();

  const div = document.createElement("div");
  div.className = "list-group-item py-2 px-3";
  div.dataset.itemId = item.id;

  const countHtml = item.count > 1
    ? `&nbsp;·&nbsp;${item.count}&nbsp;шт.`
    : "";

  div.innerHTML = `
    <div class="d-flex justify-content-between align-items-start gap-2">
      <div class="flex-grow-1 overflow-hidden">
        <div class="fw-semibold small text-truncate">${escHtml(item.name)}</div>
        <div class="text-muted" style="font-size:.75rem">
          <code>${escHtml(item.article_number)}</code>
          &nbsp;·&nbsp;${escHtml(item.manufacture)}${countHtml}
        </div>
      </div>
      <div class="d-flex align-items-center gap-1 flex-shrink-0">
        <span class="badge bg-primary text-nowrap">${formatPrice(item.price)}</span>
        <button class="btn btn-sm btn-outline-danger remove-order-item-btn p-1 lh-1"
                title="Удалить" data-item-id="${item.id}" style="line-height:1">
          <i class="bi bi-x-lg" style="font-size:.7rem"></i>
        </button>
      </div>
    </div>
  `;

  list.appendChild(div);
  badge.textContent = parseInt(badge.textContent || "0") + 1;
}

/* ── Remove order item ── */
async function handleRemoveOrderItem(itemId, rowEl) {
  const btn = rowEl.querySelector(".remove-order-item-btn");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
  }

  try {
    const resp = await fetch(REMOVE_URL(itemId), {
      method: "DELETE",
      headers: {"X-CSRFToken": CSRF_TOKEN},
    });

    if (!resp.ok) {
      const data = await resp.json().catch(() => ({}));
      alert(data.error || "Не удалось удалить позицию.");
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-x-lg" style="font-size:.7rem"></i>';
      }
      return;
    }

    rowEl.remove();
    const badge = document.getElementById("orderItemCount");
    const newCount = Math.max(0, parseInt(badge.textContent || "0") - 1);
    badge.textContent = newCount;

    if (newCount === 0) {
      const list = document.getElementById("orderItemsList");
      const empty = document.createElement("p");
      empty.id = "emptyOrderItems";
      empty.className = "text-muted small px-3 py-2 mb-0";
      empty.textContent = "Нет позиций";
      list.appendChild(empty);
    }
  } catch (err) {
    alert("Сетевая ошибка.");
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<i class="bi bi-x-lg" style="font-size:.7rem"></i>';
    }
  }
}

/* Event delegation for remove buttons (handles server-rendered and JS-added items) */
if (HAS_ORDER) {
  document.getElementById("orderItemsList").addEventListener("click", (e) => {
    const btn = e.target.closest(".remove-order-item-btn");
    if (!btn) return;
    const rowEl = btn.closest(".list-group-item");
    const itemId = btn.dataset.itemId;
    if (itemId && rowEl) handleRemoveOrderItem(itemId, rowEl);
  });
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

/* ── Toast ── */
function showToast(msg) {
  document.getElementById("toastMessage").textContent = msg;
  bootstrap.Toast.getOrCreateInstance(document.getElementById("addToast"), {delay: 3000}).show();
}
