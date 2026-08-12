const CSRF_TOKEN = "{{ csrf_token }}";
const UPDATE_COUNT_URL_TEMPLATE = "{% url 'orders:update_order_item_count' 0 %}";
const REMOVE_ITEMS_URL = "{% url 'orders:remove_order_items' order.id %}";

function updateCountUrl(itemId) {
  return UPDATE_COUNT_URL_TEMPLATE.replace('/0/', `/${itemId}/`);
}

function formatPrice(price) {
  return new Intl.NumberFormat("ru-RU", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(price);
}

document.querySelectorAll('tr[data-item-id]').forEach((row) => {
  const input = row.querySelector('.count-input');
  const applyBtn = row.querySelector('.apply-count-btn');
  const applyText = row.querySelector('.apply-count-text');
  const applySpinner = row.querySelector('.apply-count-spinner');
  const errorEl = row.querySelector('.count-error');
  const priceCell = row.querySelector('[data-item-price]');
  const itemId = row.dataset.itemId;

  function hideError() {
    errorEl.classList.add('d-none');
    errorEl.textContent = '';
  }

  function showError(msg) {
    errorEl.textContent = msg;
    errorEl.classList.remove('d-none');
  }

  function isChanged() {
    return input.value !== input.dataset.originalCount;
  }

  function refreshApplyVisibility() {
    applyBtn.classList.toggle('d-none', !isChanged());
  }

  input.addEventListener('input', () => {
    const digitsOnly = input.value.replace(/[^0-9]/g, '');
    if (digitsOnly !== input.value) {
      input.value = digitsOnly;
    }
    hideError();
    refreshApplyVisibility();
  });

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (isChanged()) {
        applyCount();
      }
    }
  });

  applyBtn.addEventListener('click', applyCount);

  async function applyCount() {
    const value = input.value.trim();
    const count = parseInt(value, 10);

    if (!value || isNaN(count) || count < 1) {
      showError('Введите целое число не меньше 1.');
      return;
    }

    hideError();
    input.disabled = true;
    applyBtn.disabled = true;
    applyText.classList.add('d-none');
    applySpinner.classList.remove('d-none');

    try {
      const resp = await fetch(updateCountUrl(itemId), {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
        body: JSON.stringify({ count }),
      });

      const data = await resp.json();

      if (!resp.ok) {
        showError(data.error || 'Не удалось обновить количество.');
        return;
      }

      input.value = data.item.count;
      input.dataset.originalCount = String(data.item.count);
      priceCell.textContent = formatPrice(data.item.price);
      applyBtn.classList.add('d-none');
    } catch (err) {
      showError('Сетевая ошибка. Попробуйте снова.');
    } finally {
      input.disabled = false;
      applyBtn.disabled = false;
      applyText.classList.remove('d-none');
      applySpinner.classList.add('d-none');
    }
  }
});

/* ── Bulk delete selected items ── */
const removeSelectedBtn = document.getElementById('removeSelectedBtn');
const removeItemsModalEl = document.getElementById('removeItemsModal');
const removeItemsModal = new bootstrap.Modal(removeItemsModalEl);
const removeItemsModalText = document.getElementById('removeItemsModalText');
const confirmRemoveItemsBtn = document.getElementById('confirmRemoveItemsBtn');
const confirmRemoveText = confirmRemoveItemsBtn.querySelector('.confirm-remove-text');
const confirmRemoveSpinner = confirmRemoveItemsBtn.querySelector('.confirm-remove-spinner');

function getSelectedCheckboxes() {
  return Array.from(document.querySelectorAll('.item-select-checkbox:checked'));
}

function refreshRemoveSelectedVisibility() {
  removeSelectedBtn.classList.toggle('d-none', getSelectedCheckboxes().length === 0);
}

document.querySelectorAll('.item-select-checkbox').forEach((checkbox) => {
  checkbox.addEventListener('change', refreshRemoveSelectedVisibility);
});

removeSelectedBtn.addEventListener('click', () => {
  const selected = getSelectedCheckboxes();
  if (selected.length === 0) return;

  removeItemsModalText.textContent = `Вы действительно хотите удалить выбранные позиции (${selected.length})?`;
  removeItemsModal.show();
});

confirmRemoveItemsBtn.addEventListener('click', async () => {
  const selected = getSelectedCheckboxes();
  if (selected.length === 0) {
    removeItemsModal.hide();
    return;
  }

  const itemIds = selected.map((cb) => parseInt(cb.dataset.itemId, 10));

  confirmRemoveItemsBtn.disabled = true;
  confirmRemoveText.classList.add('d-none');
  confirmRemoveSpinner.classList.remove('d-none');

  try {
    const resp = await fetch(REMOVE_ITEMS_URL, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
      body: JSON.stringify({ item_ids: itemIds }),
    });

    const data = await resp.json();

    if (!resp.ok) {
      alert(data.error || 'Не удалось удалить выбранные позиции.');
      return;
    }

    selected.forEach((cb) => cb.closest('tr[data-item-id]').remove());
    removeItemsModal.hide();
    refreshRemoveSelectedVisibility();
  } catch (err) {
    alert('Сетевая ошибка. Попробуйте снова.');
  } finally {
    confirmRemoveItemsBtn.disabled = false;
    confirmRemoveText.classList.remove('d-none');
    confirmRemoveSpinner.classList.add('d-none');
  }
});
