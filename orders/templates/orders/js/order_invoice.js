(function () {
  const invoiceForm = document.getElementById('invoiceForm');
  const invoiceInput = document.getElementById('invoiceLinkInput');
  const invoiceModalEl = document.getElementById('invoiceModal');

  if (!invoiceForm || !invoiceInput ) {
    return;
  }

  function isValidHttpUrl(value) {
    let url;
    try {
      url = new URL(value);
    } catch (err) {
      return false;
    }
    return url.protocol === 'http:' || url.protocol === 'https:';
  }

  invoiceInput.addEventListener('input', () => {
    invoiceInput.classList.remove('is-invalid');
  });

  invoiceForm.addEventListener('submit', (event) => {
    const value = invoiceInput.value.trim();
    if (!isValidHttpUrl(value)) {
      event.preventDefault();
      invoiceInput.classList.add('is-invalid');
      invoiceInput.focus();
    }
  });
})();
