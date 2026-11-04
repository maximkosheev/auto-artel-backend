const CSRF_TOKEN = "{{ csrf_token }}";
const AGREEMENT_URL = "{% url 'orders:agreement_order_items' order.id %}";
const ORDER_DETAIL_URL = "{% url 'orders:detail' order.id %}";
const ITEM_IDS = [{% for item in selected_items %}{{ item.id }}{% if not forloop.last %},{% endif %}{% endfor %}];

const submitAgreementBtn = document.getElementById('submitAgreementBtn');
const submitAgreementText = submitAgreementBtn.querySelector('.submit-agreement-text');
const submitAgreementSpinner = submitAgreementBtn.querySelector('.submit-agreement-spinner');
const agreementErrorModalEl = document.getElementById('agreementErrorModal');
const agreementErrorModal = new bootstrap.Modal(agreementErrorModalEl);
const agreementErrorModalText = document.getElementById('agreementErrorModalText');

function showAgreementError(message) {
  agreementErrorModalText.textContent = message || 'Не удалось отправить позиции на согласование.';
  agreementErrorModal.show();
}

submitAgreementBtn.addEventListener('click', async () => {
  submitAgreementBtn.disabled = true;
  submitAgreementText.classList.add('d-none');
  submitAgreementSpinner.classList.remove('d-none');

  try {
    const resp = await fetch(AGREEMENT_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
      body: JSON.stringify({ item_ids: ITEM_IDS }),
    });

    const data = await resp.json();

    if (!resp.ok || data.error) {
      showAgreementError(data.error);
      return;
    }

    window.location.href = ORDER_DETAIL_URL;
  } catch (err) {
    showAgreementError('Сетевая ошибка. Попробуйте снова.');
  } finally {
    submitAgreementBtn.disabled = false;
    submitAgreementText.classList.remove('d-none');
    submitAgreementSpinner.classList.add('d-none');
  }
});
