(function () {
  const invoiceForm = document.getElementById('invoiceForm');
  const invoiceInput = document.getElementById('invoiceLinkInput');
  const submitInvoiceBtn = document.getElementById('submitInvoiceBtn');
  const skipInvoiceBtn = document.getElementById('skipInvoiceBtn');

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

    const submitButton = event.submitter;

    if (submitButton === skipInvoiceBtn) {
        // Clear invoice URL if it has already been filled, and submit
        invoiceInput.value = '';
    } else if (submitButton === submitInvoiceBtn) {
        // Validate invoice link and submit
        const value = invoiceInput.value.trim();
        if (!isValidHttpUrl(value)) {
          event.preventDefault();
          invoiceInput.classList.add('is-invalid');
          invoiceInput.focus();
        }
    }
  });
})();
