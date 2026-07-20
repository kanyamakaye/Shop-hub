// Cart page: quantity +/- steppers with live subtotal recalculation (RWF, comma-formatted
// to match the server-rendered numbers). Tax/shipping/estimated totals stay as last-loaded
// values until "Update" reloads the page with authoritative server-computed numbers.
document.addEventListener('DOMContentLoaded', () => {
    const rows = document.querySelectorAll('[data-cart-row]');
    const totalEl = document.getElementById('cart-total');

    function formatRwf(amount) {
        return Math.round(amount).toLocaleString('en-US') + ' RWF';
    }

    function recalcTotal() {
        let grandTotal = 0;
        const storeSubtotals = {};

        rows.forEach((row) => {
            const price = parseFloat(row.dataset.price);
            const qty = parseInt(row.querySelector('[data-qty-input]').value, 10) || 0;
            const subtotal = price * qty;
            row.querySelector('[data-row-subtotal]').textContent = formatRwf(subtotal);

            const storeId = row.dataset.store;
            storeSubtotals[storeId] = (storeSubtotals[storeId] || 0) + subtotal;
            grandTotal += subtotal;
        });

        Object.keys(storeSubtotals).forEach((storeId) => {
            const el = document.querySelector(`[data-store-subtotal="${storeId}"]`);
            if (el) el.textContent = formatRwf(storeSubtotals[storeId]);
        });

        if (totalEl) totalEl.textContent = formatRwf(grandTotal);
    }

    rows.forEach((row) => {
        const input = row.querySelector('[data-qty-input]');
        row.querySelectorAll('.qty-btn').forEach((btn) => {
            btn.addEventListener('click', () => {
                const step = parseInt(btn.dataset.step, 10);
                const next = Math.max(1, (parseInt(input.value, 10) || 1) + step);
                input.value = next;
                recalcTotal();
            });
        });
        input.addEventListener('input', recalcTotal);
    });
});
