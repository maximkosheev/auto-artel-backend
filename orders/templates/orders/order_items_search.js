const SEARCH_URL = "{% url 'orders:items_search_results' %}";
const ADD_URL    = "{% url 'orders:add_order_item' order.id %}";
const CSRF_TOKEN = "{{ csrf_token }}";

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

/* ── Search ── */
document.getElementById("searchForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  hideError();

  const articleNumber = document.getElementById("articleInput").value.trim();
  if (!articleNumber) return;

  setSearchLoading(true);

  const formData = new FormData();
  formData.append("article_number", articleNumber);
  formData.append("csrfmiddlewaretoken", CSRF_TOKEN);

  try {
    const resp = await fetch(SEARCH_URL, {method: "POST", body: formData});
    const data = await resp.json();

    if (!resp.ok) {
      showError(data.error || "Ошибка при обращении к поставщику.");
      document.getElementById("resultsSection").classList.add("d-none");
      document.getElementById("emptyState").classList.add("d-none");
      return;
    }

    renderResults(data.items, articleNumber);
  } catch (err) {
    showError("Сетевая ошибка. Попробуйте снова.");
  } finally {
    setSearchLoading(false);
  }
});

function renderResults(items, articleNumber) {
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

  document.getElementById("resultCount").textContent  = items.length;
  document.getElementById("searchedArticle").textContent = `Артикул: ${articleNumber}`;

  items.forEach(item => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><code>${escHtml(item.article_number)}</code></td>
      <td>${escHtml(item.manufacture)}</td>
      <td>${escHtml(item.name)}</td>
      <td class="text-end text-nowrap">${formatPrice(item.price)}</td>
      <td class="text-center">
        <span class="badge ${item.count > 5 ? 'bg-success' : item.count > 0 ? 'bg-warning text-dark' : 'bg-danger'}">
          ${item.count}
        </span>
      </td>
      <td>${escHtml(item.delivery_time)}</td>
      <td><small>${escHtml(item.warehouse_location)}</small></td>
      <td class="text-center">
        <button
          class="btn btn-sm btn-outline-primary add-to-order-btn"
          title="Добавить в заказ"
          data-item='${escAttr(JSON.stringify(item))}'
        >
          <i class="bi bi-cart-plus-fill"></i>
        </button>
      </td>
    `;
    body.appendChild(tr);
  });

  /* Attach listeners to new buttons */
  body.querySelectorAll(".add-to-order-btn").forEach(btn => {
    btn.addEventListener("click", handleAddToOrder);
  });
}

/* ── Add to order ── */
async function handleAddToOrder(e) {
  const btn  = e.currentTarget;
  const item = JSON.parse(btn.dataset.item);

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

  try {
    const resp = await fetch(ADD_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": CSRF_TOKEN,
      },
      body: JSON.stringify(item),
    });

    const data = await resp.json();

    if (!resp.ok) {
      alert(data.error || "Не удалось добавить позицию.");
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

  /* Remove "empty" placeholder if present */
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
  const toastEl = document.getElementById("addToast");
  bootstrap.Toast.getOrCreateInstance(toastEl, {delay: 3000}).show();
}

/* ── XSS helpers ── */
function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
function escAttr(str) {
  return String(str).replace(/'/g, "&#39;").replace(/"/g, "&quot;");
}