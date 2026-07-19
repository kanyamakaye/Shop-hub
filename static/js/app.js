// Shared site-wide JS: confirm-before-delete dialogs and dark mode toggle.
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-confirm]').forEach((el) => {
        el.addEventListener('submit', (event) => {
            const message = el.getAttribute('data-confirm') || 'Are you sure?';
            if (!window.confirm(message)) {
                event.preventDefault();
            }
        });
    });

    const toggle = document.getElementById('theme-toggle');
    const lightIcon = document.getElementById('theme-icon-light');
    const darkIcon = document.getElementById('theme-icon-dark');
    function syncIcons() {
        const isDark = document.documentElement.classList.contains('dark');
        lightIcon.classList.toggle('hidden', isDark);
        darkIcon.classList.toggle('hidden', !isDark);
    }
    if (toggle) {
        syncIcons();
        toggle.addEventListener('click', () => {
            document.documentElement.classList.toggle('dark');
            localStorage.setItem('theme', document.documentElement.classList.contains('dark') ? 'dark' : 'light');
            syncIcons();
        });
    }

    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    const mobileMenu = document.getElementById('mobile-menu');
    if (mobileMenuToggle && mobileMenu) {
        mobileMenuToggle.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }

    // Debounced auto-submit for the navbar search box (present on every page).
    const navbarSearch = document.getElementById('navbar-search');
    if (navbarSearch) {
        let searchTimer;
        navbarSearch.addEventListener('input', () => {
            clearTimeout(searchTimer);
            searchTimer = setTimeout(() => navbarSearch.form.requestSubmit(), 500);
        });
    }

    // Feedback on plain (non-modal) POST form submits: disable the submit button
    // and show a "Saving..." state so the page doesn't feel unresponsive while it
    // navigates. Modal forms already get this from modal.js, so they're skipped.
    document.addEventListener('submit', (event) => {
        if (event.defaultPrevented) return; // e.g. a data-confirm dialog was cancelled
        const form = event.target;
        if (form.method && form.method.toLowerCase() !== 'post') return;
        if (form.closest('#app-modal-body')) return;
        if (form.hasAttribute('data-no-loading')) return;
        const submitBtn = form.querySelector('button[type=submit]');
        if (!submitBtn || submitBtn.disabled) return;
        submitBtn.dataset.originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Please wait…';
    });

    // Flash messages (success/error/warning/info) show immediately, then
    // auto-dismiss a few seconds later — same behavior for every action site-wide.
    document.querySelectorAll('.js-toast').forEach((toast) => {
        const dismiss = () => {
            toast.classList.remove('toast-enter');
            toast.classList.add('toast-exit');
            toast.addEventListener('animationend', () => toast.remove(), { once: true });
        };
        const timer = setTimeout(dismiss, 4000);
        const closeBtn = toast.querySelector('[data-toast-close]');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                clearTimeout(timer);
                dismiss();
            });
        }
    });
});
