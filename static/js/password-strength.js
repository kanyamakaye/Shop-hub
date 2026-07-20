(function () {
  const EYE =
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8Z"/><circle cx="12" cy="12" r="3"/></svg>';
  const EYE_OFF =
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5"><path d="M17.94 17.94A10.94 10.94 0 0 1 12 20c-7 0-11-8-11-8a21.6 21.6 0 0 1 5.06-6.06M9.9 4.24A10.4 10.4 0 0 1 12 4c7 0 11 8 11 8a21.6 21.6 0 0 1-3.22 4.55M14.12 14.12a3 3 0 1 1-4.24-4.24"/><path d="M1 1l22 22"/></svg>';

  function scorePassword(pw) {
    if (!pw) return 0;
    let score = Math.min(pw.length / 12, 1) * 40;
    if (/[a-z]/.test(pw)) score += 10;
    if (/[A-Z]/.test(pw)) score += 15;
    if (/[0-9]/.test(pw)) score += 15;
    if (/[^A-Za-z0-9]/.test(pw)) score += 20;
    if (pw.length < 8) score = Math.min(score, 35);
    return Math.max(0, Math.min(100, Math.round(score)));
  }

  function levelFor(score) {
    if (score < 35) return { label: 'Weak', bar: 'bg-red-500', text: 'text-red-600' };
    if (score < 65) return { label: 'Fair', bar: 'bg-amber-500', text: 'text-amber-600' };
    if (score < 85) return { label: 'Good', bar: 'bg-brand-blue-500', text: 'text-brand-blue-600' };
    return { label: 'Strong', bar: 'bg-brand-green-500', text: 'text-brand-green-600' };
  }

  function attachMeter(input, afterEl) {
    const meter = document.createElement('div');
    meter.className = 'mt-2';
    meter.innerHTML =
      '<div class="h-1.5 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">' +
      '<div class="h-full w-0 rounded-full transition-all duration-200"></div>' +
      '</div>' +
      '<p class="mt-1 text-xs font-medium"></p>';
    afterEl.insertAdjacentElement('afterend', meter);
    const bar = meter.querySelector('div > div');
    const label = meter.querySelector('p');

    input.addEventListener('input', function () {
      const pw = input.value;
      if (!pw) {
        bar.style.width = '0%';
        bar.className = 'h-full rounded-full transition-all duration-200';
        label.textContent = '';
        return;
      }
      const score = scorePassword(pw);
      const level = levelFor(score);
      bar.style.width = score + '%';
      bar.className = 'h-full rounded-full transition-all duration-200 ' + level.bar;
      label.className = 'mt-1 text-xs font-medium ' + level.text;
      label.textContent = 'Password strength: ' + level.label;
    });
  }

  function attachToggle(input) {
    const wrap = document.createElement('div');
    wrap.className = 'relative';
    input.parentNode.insertBefore(wrap, input);
    wrap.appendChild(input);
    input.classList.add('pr-10');

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'absolute inset-y-0 right-0 flex w-10 items-center justify-center text-slate-400 hover:text-slate-600 dark:hover:text-slate-200';
    btn.setAttribute('aria-label', 'Show password');
    btn.innerHTML = EYE;

    btn.addEventListener('click', function () {
      const showing = input.type === 'text';
      input.type = showing ? 'password' : 'text';
      btn.innerHTML = showing ? EYE : EYE_OFF;
      btn.setAttribute('aria-label', showing ? 'Show password' : 'Hide password');
    });

    wrap.appendChild(btn);
    return wrap;
  }

  document.querySelectorAll('input[type="password"]').forEach(function (input) {
    const needsMeter = input.classList.contains('js-pw-strength');
    const wrap = attachToggle(input);
    if (needsMeter) attachMeter(input, wrap);
  });
})();
