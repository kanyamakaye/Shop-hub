// Homepage-only interactions: animated stat counters, FAQ accordion, smooth anchor scroll, scroll-reveal.
document.addEventListener('DOMContentLoaded', () => {
    // Fade-in-up reveal for sections as they scroll into view. Content is visible by
    // default in CSS; this only *adds* the hidden-until-revealed behavior, and only
    // once we're sure we can also reveal it again — so a JS error never leaves
    // the page permanently blank. A timeout is a final safety net regardless.
    try {
        const revealEls = document.querySelectorAll('.reveal');
        if ('IntersectionObserver' in window && revealEls.length) {
            document.documentElement.classList.add('js-reveal-ready');
            const revealObserver = new IntersectionObserver((entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('is-visible');
                        revealObserver.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.15 });
            revealEls.forEach((el) => revealObserver.observe(el));
            setTimeout(() => revealEls.forEach((el) => el.classList.add('is-visible')), 4000);
        }
    } catch (error) {
        document.documentElement.classList.remove('js-reveal-ready');
    }

    // Smooth scroll for in-page anchor links (#features, #pricing, etc.)
    document.querySelectorAll('a[href^="#"]').forEach((link) => {
        link.addEventListener('click', (event) => {
            const target = document.querySelector(link.getAttribute('href'));
            if (target) {
                event.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    // Animated counters for the statistics section.
    const counters = document.querySelectorAll('[data-counter]');
    const animateCounter = (el) => {
        const target = parseInt(el.dataset.counter, 10) || 0;
        const duration = 1200;
        const start = performance.now();
        function tick(now) {
            const progress = Math.min((now - start) / duration, 1);
            el.textContent = Math.round(progress * target).toLocaleString();
            if (progress < 1) requestAnimationFrame(tick);
            else el.textContent = target.toLocaleString();
        }
        requestAnimationFrame(tick);
    };
    if ('IntersectionObserver' in window && counters.length) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    animateCounter(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });
        counters.forEach((el) => observer.observe(el));
    } else {
        counters.forEach(animateCounter);
    }

    // Hero dashboard mockup: grow the revenue bar once it scrolls into view.
    const mockupBar = document.querySelector('[data-mockup-bar]');
    if (mockupBar) {
        const growBar = () => { mockupBar.style.width = '78%'; };
        if ('IntersectionObserver' in window) {
            const barObserver = new IntersectionObserver((entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        growBar();
                        barObserver.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.5 });
            barObserver.observe(mockupBar);
        } else {
            growBar();
        }
    }

    // FAQ accordion.
    document.querySelectorAll('[data-faq-trigger]').forEach((trigger) => {
        trigger.addEventListener('click', () => {
            const panel = trigger.nextElementSibling;
            const isOpen = !panel.classList.contains('hidden');
            document.querySelectorAll('[data-faq-panel]').forEach((p) => p.classList.add('hidden'));
            document.querySelectorAll('[data-faq-icon]').forEach((icon) => icon.classList.remove('rotate-180'));
            if (!isOpen) {
                panel.classList.remove('hidden');
                trigger.querySelector('[data-faq-icon]').classList.add('rotate-180');
            }
        });
    });

    // FAQ category filter pills.
    const faqFilters = document.querySelectorAll('#faq-category-filters .category-pill');
    const faqGroups = document.querySelectorAll('[data-faq-group]');
    faqFilters.forEach((pill) => {
        pill.addEventListener('click', () => {
            faqFilters.forEach((p) => p.classList.remove('category-pill-active'));
            pill.classList.add('category-pill-active');
            const filter = pill.dataset.faqFilter;
            faqGroups.forEach((group) => {
                const show = filter === 'all' || group.dataset.faqGroup === filter;
                group.classList.toggle('hidden', !show);
            });
        });
    });

    // Simple client-side email validation for the newsletter form.
    document.querySelectorAll('[data-newsletter-form]').forEach((form) => {
        form.addEventListener('submit', (event) => {
            const input = form.querySelector('input[type="email"]');
            const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!re.test(input.value)) {
                event.preventDefault();
                input.classList.add('ring-2', 'ring-red-500');
            } else {
                input.classList.remove('ring-2', 'ring-red-500');
            }
        });
    });

    // Featured product category pill filters.
    const filters = document.querySelectorAll('#category-filters .category-pill');
    const productCards = document.querySelectorAll('.product-card');
    filters.forEach((pill) => {
        pill.addEventListener('click', () => {
            filters.forEach((p) => p.classList.remove('category-pill-active'));
            pill.classList.add('category-pill-active');
            const filter = pill.dataset.filter;
            productCards.forEach((card) => {
                const show = filter === 'all' || card.dataset.category === filter;
                card.classList.toggle('hidden', !show);
            });
        });
    });

    // Product carousel arrow navigation.
    const carousel = document.getElementById('product-carousel');
    const prevBtn = document.getElementById('carousel-prev');
    const nextBtn = document.getElementById('carousel-next');
    if (carousel && prevBtn && nextBtn) {
        const scrollAmount = () => carousel.clientWidth * 0.8;
        prevBtn.addEventListener('click', () => carousel.scrollBy({ left: -scrollAmount(), behavior: 'smooth' }));
        nextBtn.addEventListener('click', () => carousel.scrollBy({ left: scrollAmount(), behavior: 'smooth' }));
    }

    // Pricing billing toggle (monthly <-> annually).
    const billingToggle = document.getElementById('billing-toggle');
    const billingKnob = document.getElementById('billing-toggle-knob');
    const monthlyLabel = document.getElementById('billing-monthly-label');
    const yearlyLabel = document.getElementById('billing-yearly-label');
    if (billingToggle) {
        billingToggle.addEventListener('click', () => {
            const isYearly = billingToggle.getAttribute('aria-checked') !== 'true';
            billingToggle.setAttribute('aria-checked', String(isYearly));
            billingToggle.classList.toggle('bg-brand-blue-600', isYearly);
            billingToggle.classList.toggle('bg-slate-300', !isYearly);
            billingKnob.style.transform = isYearly ? 'translateX(1.25rem)' : 'translateX(0)';
            monthlyLabel.classList.toggle('text-slate-400', isYearly);
            monthlyLabel.classList.toggle('text-slate-900', !isYearly);
            monthlyLabel.classList.toggle('dark:text-white', !isYearly);
            yearlyLabel.classList.toggle('text-slate-400', !isYearly);
            yearlyLabel.classList.toggle('text-slate-900', isYearly);
            yearlyLabel.classList.toggle('dark:text-white', isYearly);

            document.querySelectorAll('[data-price]').forEach((el) => {
                const value = isYearly ? el.dataset.yearly : el.dataset.monthly;
                el.textContent = Number(value).toLocaleString('en-US');
            });
            document.querySelectorAll('[data-period]').forEach((el) => {
                el.textContent = isYearly ? ' RWF/yr' : ' RWF/mo';
            });
        });
    }
});
