// Generic AJAX modal system for view/edit/delete actions.
// Triggers: [data-modal-view=url], [data-modal-edit=url], [data-modal-delete=url]
// (each takes optional data-modal-title, and data-modal-message for delete).
// View/edit fetch the target URL, pull out #main-content, and inject it into the
// modal body — no extra backend endpoints needed, since Django re-renders the
// same full page on validation errors and redirects elsewhere on success.
document.addEventListener('DOMContentLoaded', () => {
    const overlay = document.getElementById('app-modal');
    if (!overlay) return;
    const body = document.getElementById('app-modal-body');
    const titleEl = document.getElementById('app-modal-title');
    let sourceUrl = null;

    function csrfToken() {
        const match = document.cookie.match(/csrftoken=([^;]+)/);
        return match ? match[1] : '';
    }

    function openModal(title) {
        titleEl.textContent = title || '';
        overlay.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');
        requestAnimationFrame(() => overlay.classList.add('modal-open'));
    }

    function closeModal() {
        overlay.classList.remove('modal-open');
        document.body.classList.remove('overflow-hidden');
        setTimeout(() => {
            overlay.classList.add('hidden');
            body.innerHTML = '';
            sourceUrl = null;
        }, 150);
    }

    function extractMain(html) {
        const doc = new DOMParser().parseFromString(html, 'text/html');
        const main = doc.getElementById('main-content');
        return main ? main.innerHTML : '<p class="p-6 text-sm text-slate-500">Nothing to show.</p>';
    }

    function ensureLocationCascade(root) {
        if (!root.querySelector('[data-level="province"]')) return;
        if (window.initLocationCascade) {
            window.initLocationCascade(root);
            return;
        }
        const script = document.createElement('script');
        script.src = '/static/js/location-cascade.js';
        script.onload = () => window.initLocationCascade(root);
        document.body.appendChild(script);
    }

    function showSpinner() {
        body.innerHTML = '<div class="flex items-center justify-center p-16"><span class="h-6 w-6 animate-spin rounded-full border-2 border-brand-blue-600 border-t-transparent"></span></div>';
    }

    function renderInto(html) {
        body.innerHTML = extractMain(html);
        bindForms();
        ensureLocationCascade(body);
    }

    function bindForms() {
        body.querySelectorAll('form').forEach((form) => {
            // A form with no explicit action="" resolves (via the DOM) against the
            // *current* page URL, not the page it was fetched from — pin it explicitly.
            if (!form.getAttribute('action') && sourceUrl) {
                form.setAttribute('action', sourceUrl);
            }
            form.addEventListener('submit', handleSubmit);
        });
    }

    async function handleSubmit(event) {
        event.preventDefault();
        const form = event.currentTarget;
        const submitBtn = form.querySelector('button[type=submit]');
        if (submitBtn) submitBtn.disabled = true;
        try {
            const response = await fetch(form.action || sourceUrl || window.location.href, {
                method: form.method || 'POST',
                body: new FormData(form),
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
            });
            if (response.redirected) {
                window.location.reload();
                return;
            }
            renderInto(await response.text());
        } catch (err) {
            body.innerHTML = '<p class="p-6 text-sm text-red-600">Something went wrong. Please try again.</p>';
        } finally {
            if (submitBtn) submitBtn.disabled = false;
        }
    }

    async function openRemoteModal(url, title) {
        sourceUrl = url;
        openModal(title);
        showSpinner();
        try {
            const response = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
            renderInto(await response.text());
            // Escape hatch: some forms have page-only JS (image preview, cascading
            // selects) that doesn't run inside a modal — let people pop out to it.
            body.insertAdjacentHTML('afterbegin', `<div class="flex justify-end border-b border-slate-100 px-6 py-2 dark:border-slate-700"><a href="${url}" target="_blank" rel="noopener" class="text-xs font-medium text-brand-blue-600 hover:underline">Open full page &#8599;</a></div>`);
        } catch (err) {
            body.innerHTML = '<p class="p-6 text-sm text-red-600">Could not load this content.</p>';
        }
    }

    function openDeleteModal(url, title, message) {
        openModal(title || 'Confirm delete');
        body.innerHTML = `
            <div class="p-6">
                <p class="text-sm text-slate-600 dark:text-slate-300">${message || 'This action cannot be undone.'}</p>
                <form method="post" action="${url}" class="mt-6 flex justify-end gap-3">
                    <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken()}">
                    <button type="button" data-modal-close class="btn-outline">Cancel</button>
                    <button type="submit" class="inline-flex items-center justify-center rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-red-700">Delete</button>
                </form>
            </div>`;
        bindForms();
    }

    document.addEventListener('click', (event) => {
        const viewTrigger = event.target.closest('[data-modal-view]');
        if (viewTrigger) {
            event.preventDefault();
            openRemoteModal(viewTrigger.getAttribute('data-modal-view'), viewTrigger.getAttribute('data-modal-title') || 'Details');
            return;
        }
        const editTrigger = event.target.closest('[data-modal-edit]');
        if (editTrigger) {
            event.preventDefault();
            openRemoteModal(editTrigger.getAttribute('data-modal-edit'), editTrigger.getAttribute('data-modal-title') || 'Edit');
            return;
        }
        const deleteTrigger = event.target.closest('[data-modal-delete]');
        if (deleteTrigger) {
            event.preventDefault();
            openDeleteModal(
                deleteTrigger.getAttribute('data-modal-delete'),
                deleteTrigger.getAttribute('data-modal-title'),
                deleteTrigger.getAttribute('data-modal-message'),
            );
            return;
        }
        if (event.target === overlay || event.target.closest('[data-modal-close]')) {
            closeModal();
        }
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && !overlay.classList.contains('hidden')) closeModal();
    });
});
