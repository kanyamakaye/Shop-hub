// Cart page: quantity +/- steppers with live subtotal and total recalculation.
document.addEventListener('DOMContentLoaded', () => {
    const rows = document.querySelectorAll('[data-cart-row]');
    const totalEl = document.getElementById('cart-total');

    function recalcTotal() {
        let total = 0;
        rows.forEach((row) => {
            const price = parseFloat(row.dataset.price);
            const qty = parseInt(row.querySelector('[data-qty-input]').value, 10) || 0;
            const subtotal = price * qty;
            row.querySelector('[data-row-subtotal]').textContent = `$${subtotal.toFixed(2)}`;
            total += subtotal;
        });
        if (totalEl) totalEl.textContent = `$${total.toFixed(2)}`;
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
