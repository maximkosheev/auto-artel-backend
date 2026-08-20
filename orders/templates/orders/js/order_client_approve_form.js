const selectAllCheckbox = document.getElementById('selectAllCheckbox');
const itemCheckboxes = Array.from(document.querySelectorAll('.item-checkbox'));
const submitBtn = document.getElementById('submitApproveBtn');
const submitBtnText = submitBtn.querySelector('.submit-text');
const selectedSummary = document.getElementById('selectedSummary');
const totalItems = itemCheckboxes.length;
const itemPrices = itemCheckboxes.map((checkbox) => parseFloat(checkbox.dataset.price) || 0);

function formatMoney(value) {
    return new Intl.NumberFormat('ru-RU').format(Math.round(value));
}

function countChecked() {
    return itemCheckboxes.filter((checkbox) => checkbox.checked).length;
}

function updateSelectAllState() {
    const checkedCount = countChecked();
    selectAllCheckbox.checked = totalItems > 0 && checkedCount === totalItems;
    selectAllCheckbox.indeterminate = checkedCount > 0 && checkedCount < totalItems;
}

function updateSubmitState() {
    let checkedCount = 0;
    let selectedCost = 0;
    itemCheckboxes.forEach((checkbox, index) => {
        if (checkbox.checked) {
            checkedCount += 1;
            selectedCost += itemPrices[index];
        }
    });

    submitBtn.classList.remove('submit--all', 'submit--partial', 'submit--none');

    if (checkedCount === 0) {
        submitBtn.classList.add('submit--none');
        submitBtnText.textContent = 'Не согласовано';
    } else if (checkedCount === totalItems) {
        submitBtn.classList.add('submit--all');
        submitBtnText.textContent = 'Согласовать все';
    } else {
        submitBtn.classList.add('submit--partial');
        submitBtnText.textContent = 'Согласовать частично';
    }

    if (selectedSummary) {
        selectedSummary.textContent = `Выбрано позиций: ${checkedCount} из ${totalItems} на сумму ${formatMoney(selectedCost)} ₽`;
    }
}

if (selectAllCheckbox) {
    selectAllCheckbox.addEventListener('change', () => {
        itemCheckboxes.forEach((checkbox) => {
            checkbox.checked = selectAllCheckbox.checked;
        });
        selectAllCheckbox.indeterminate = false;
        updateSubmitState();
    });
}

itemCheckboxes.forEach((checkbox) => {
    checkbox.addEventListener('change', () => {
        updateSelectAllState();
        updateSubmitState();
    });
});

updateSelectAllState();
updateSubmitState();
