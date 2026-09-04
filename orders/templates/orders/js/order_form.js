const CSRF_TOKEN = "{{ csrf_token }}";
const ORDER_PAGE_URL = "{% url 'orders:detail' order.id %}"
const CANCEL_ORDER_URL = "{% url 'orders:cancel' order.id %}";

const cancelOrderModalEl = document.getElementById('cancelOrderModal');
const cancelOrderModal = new bootstrap.Modal(cancelOrderModal);
const confirmCancelOrderBtn = document.getElementById('confirmCancelOrderBtn');

cancelOrderBtn.addEventListener('click', () => {
    cancelOrderModal.show();
});

confirmCancelOrderBtn.addEventListener('click', async () => {
    confirmCancelOrderBtn.disabled = true;
    try {
        cancelOrderModal.hide();
        window.location.href = `${ORDER_PAGE_URL}`;
    } catch (err) {
        alert('Сетевая ошибка. Попробуйте снова.');
    } finally {
        confirmCancelOrderBtn.disabled = false;
    }
});