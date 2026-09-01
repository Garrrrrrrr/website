/* ============================================================================
   Site behaviour

   Header state, mobile sheet, theme toggle, scroll reveals, image skeletons,
   lightbox, and the contact form.

   Every interactive element here works with the keyboard, and nothing here is
   required for the page to be readable: with JavaScript disabled the content,
   navigation and disclosure rows all still function.
   ========================================================================= */

(function () {
  'use strict';

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)');

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(sel));
  }

  /* -- 1. Header state ---------------------------------------------------- */

  var header = $('.header');
  if (header) {
    var onScroll = function () {
      header.classList.toggle('is-scrolled', window.scrollY > 8);
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* -- 2. Focus trap ------------------------------------------------------ */

  var FOCUSABLE = [
    'a[href]', 'button:not([disabled])', 'input:not([disabled])',
    'textarea:not([disabled])', 'select:not([disabled])', '[tabindex]:not([tabindex="-1"])'
  ].join(',');

  function trapFocus(container, event) {
    var items = $$(FOCUSABLE, container).filter(function (el) {
      return el.offsetParent !== null || el === document.activeElement;
    });
    if (!items.length) return;
    var first = items[0];
    var last = items[items.length - 1];

    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  /* -- 3. Mobile sheet ---------------------------------------------------- */

  var sheet = $('#nav-sheet');
  var sheetOpen = $('[data-sheet-open]');
  var sheetClose = $('[data-sheet-close]');
  var sheetReturn = null;

  function openSheet() {
    if (!sheet) return;
    // Return focus to the trigger itself. document.activeElement is not
    // reliable here: a pointer activation may leave it on <body>.
    sheetReturn = sheetOpen || document.activeElement;
    sheet.classList.add('is-open');
    sheet.removeAttribute('hidden');
    document.body.classList.add('is-locked');
    if (sheetOpen) sheetOpen.setAttribute('aria-expanded', 'true');
    var target = $(FOCUSABLE, sheet);
    if (target) target.focus();
  }

  function closeSheet() {
    if (!sheet || !sheet.classList.contains('is-open')) return;
    sheet.classList.remove('is-open');
    sheet.setAttribute('hidden', '');
    document.body.classList.remove('is-locked');
    if (sheetOpen) sheetOpen.setAttribute('aria-expanded', 'false');
    if (sheetReturn && sheetReturn.focus) sheetReturn.focus();
    sheetReturn = null;
  }

  if (sheetOpen) sheetOpen.addEventListener('click', openSheet);
  if (sheetClose) sheetClose.addEventListener('click', closeSheet);
  if (sheet) {
    $$('.sheet__link, .sheet__actions a', sheet).forEach(function (a) {
      a.addEventListener('click', closeSheet);
    });
  }
  // The sheet only exists below 768px; if the viewport grows past it, close.
  window.matchMedia('(min-width: 768px)').addEventListener('change', function (e) {
    if (e.matches) closeSheet();
  });

  /* -- 4. Theme toggle ---------------------------------------------------- */

  function effectiveTheme() {
    var set = document.documentElement.getAttribute('data-theme');
    if (set) return set;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  $$('[data-theme-toggle]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var next = effectiveTheme() === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      try { localStorage.setItem('theme', next); } catch (e) {}
      var meta = $('meta[name="theme-color"]');
      if (meta) {
        meta.setAttribute('content', next === 'dark' ? '#101113' : '#F4F4F1');
      }
      window.dispatchEvent(new CustomEvent('themechange', { detail: next }));
    });
  });

  /* -- 5. Scroll reveals -------------------------------------------------- */

  var reveals = $$('.reveal');
  if (reveals.length && 'IntersectionObserver' in window && !reduced.matches) {
    var revealObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var group = $$('.reveal', entry.target.parentElement);
        var i = group.indexOf(entry.target);
        entry.target.style.setProperty('--reveal-delay', Math.min(i, 6) * 40 + 'ms');
        entry.target.classList.add('is-visible');
        revealObserver.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.05 });
    reveals.forEach(function (el) { revealObserver.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add('is-visible'); });
  }

  /* -- 6. Image skeletons ------------------------------------------------- */

  $$('.shot, .figure__frame').forEach(function (holder) {
    var img = $('img', holder);
    if (!img) return;
    var done = function () { holder.classList.add('is-loaded'); };
    if (img.complete && img.naturalWidth) done();
    else {
      img.addEventListener('load', done);
      img.addEventListener('error', done);
    }
  });

  /* -- 7. Lightbox -------------------------------------------------------- */

  var lightbox = $('#lightbox');
  if (lightbox) {
    var lbImg = $('.lightbox__img', lightbox);
    var lbCaption = $('.lightbox__caption', lightbox);
    var lbPrev = $('.lightbox__nav--prev', lightbox);
    var lbNext = $('.lightbox__nav--next', lightbox);
    var group = [];
    var index = 0;
    var lbReturn = null;

    function show(i) {
      index = (i + group.length) % group.length;
      var trigger = group[index];
      var img = $('img', trigger);
      lbImg.src = img.getAttribute('data-full') || img.currentSrc || img.src;
      lbImg.alt = img.alt;
      lbCaption.textContent = trigger.getAttribute('data-caption') || img.alt;
      var many = group.length > 1;
      lbPrev.hidden = !many;
      lbNext.hidden = !many;
    }

    function openLightbox(trigger) {
      var name = trigger.getAttribute('data-lightbox') || 'default';
      group = $$('[data-lightbox="' + name + '"]');
      lbReturn = trigger;
      show(group.indexOf(trigger));
      lightbox.classList.add('is-open');
      lightbox.removeAttribute('hidden');
      document.body.classList.add('is-locked');
      $('.lightbox__close', lightbox).focus();
    }

    function closeLightbox() {
      if (!lightbox.classList.contains('is-open')) return;
      lightbox.classList.remove('is-open');
      lightbox.setAttribute('hidden', '');
      document.body.classList.remove('is-locked');
      lbImg.removeAttribute('src');
      if (lbReturn && lbReturn.focus) lbReturn.focus();
      lbReturn = null;
    }

    $$('[data-lightbox]').forEach(function (trigger) {
      trigger.addEventListener('click', function (e) {
        e.preventDefault();
        openLightbox(trigger);
      });
    });

    $('.lightbox__close', lightbox).addEventListener('click', closeLightbox);
    lbPrev.addEventListener('click', function () { show(index - 1); });
    lbNext.addEventListener('click', function () { show(index + 1); });
    lightbox.addEventListener('click', function (e) {
      if (e.target === lightbox) closeLightbox();
    });

    document.addEventListener('keydown', function (e) {
      if (!lightbox.classList.contains('is-open')) return;
      if (e.key === 'Escape') closeLightbox();
      else if (e.key === 'ArrowLeft' && group.length > 1) show(index - 1);
      else if (e.key === 'ArrowRight' && group.length > 1) show(index + 1);
      else if (e.key === 'Tab') trapFocus(lightbox, e);
    });
  }

  /* Escape and Tab handling for the sheet lives alongside, but the lightbox
     sits above it, so the sheet only responds when the lightbox is closed. */
  document.addEventListener('keydown', function (e) {
    if (!sheet || !sheet.classList.contains('is-open')) return;
    if (lightbox && lightbox.classList.contains('is-open')) return;
    if (e.key === 'Escape') closeSheet();
    else if (e.key === 'Tab') trapFocus(sheet, e);
  });

  /* -- 8. Contact form ---------------------------------------------------- */

  var form = $('#contact-form');
  if (form) {
    var ENDPOINT = 'https://formspree.io/f/xqeywjbo';
    var RATE = { max: 2, windowMs: 5 * 60 * 1000, key: 'formSubmissions' };
    var submit = $('.form__submit', form);
    var status = $('#form-status');
    var submitLabel = submit.innerHTML;

    function setError(field, message) {
      var input = $('#' + field);
      var slot = $('#' + field + '-error');
      if (slot) slot.textContent = message || '';
      if (input) {
        if (message) input.setAttribute('aria-invalid', 'true');
        else input.removeAttribute('aria-invalid');
      }
      return !message;
    }

    function validate(data) {
      var ok = true;
      ok = setError('name', data.name.trim() ? '' : 'Enter your name.') && ok;
      ok = setError('email',
        /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(data.email.trim())
          ? '' : 'Enter a valid email address.') && ok;
      ok = setError('message',
        data.message.trim().length >= 10
          ? '' : 'Add a little more detail, at least 10 characters.') && ok;
      return ok;
    }

    function recentSubmissions() {
      try {
        var raw = JSON.parse(localStorage.getItem(RATE.key) || '[]');
        var cutoff = Date.now() - RATE.windowMs;
        return raw.filter(function (t) { return t > cutoff; });
      } catch (e) { return []; }
    }

    function setStatus(state, message) {
      if (!status) return;
      status.setAttribute('data-state', state);
      status.textContent = message;
    }

    function setBusy(busy) {
      submit.disabled = busy;
      submit.setAttribute('aria-busy', busy ? 'true' : 'false');
      submit.innerHTML = busy
        ? '<span class="spinner" aria-hidden="true"></span>Sending'
        : submitLabel;
    }

    form.addEventListener('submit', function (e) {
      e.preventDefault();

      // Honeypot. A real person never fills this; a bot fills everything.
      if ($('#company', form).value) return;

      var data = {
        name: $('#name', form).value,
        email: $('#email', form).value,
        message: $('#message', form).value
      };

      setStatus('', '');
      if (!validate(data)) {
        setStatus('error', 'Check the highlighted fields and try again.');
        return;
      }

      var recent = recentSubmissions();
      if (recent.length >= RATE.max) {
        var wait = Math.ceil((recent[0] + RATE.windowMs - Date.now()) / 60000);
        setStatus('error',
          'You have sent ' + RATE.max + ' messages already. Try again in ' +
          wait + ' minute' + (wait === 1 ? '' : 's') + ', or email me directly.');
        return;
      }

      setBusy(true);
      setStatus('', '');

      var body = new FormData();
      body.append('name', data.name.trim());
      body.append('email', data.email.trim());
      body.append('message', data.message.trim());

      // No 'no-cors'. Formspree returns a real JSON response, so a failure
      // is actually visible instead of being reported as success.
      fetch(ENDPOINT, {
        method: 'POST',
        body: body,
        headers: { Accept: 'application/json' }
      })
        .then(function (res) {
          return res.json().catch(function () { return {}; })
            .then(function (json) { return { ok: res.ok, json: json }; });
        })
        .then(function (result) {
          if (!result.ok) {
            var detail = result.json && result.json.errors && result.json.errors.length
              ? result.json.errors.map(function (x) { return x.message; }).join(' ')
              : 'The message did not send.';
            setStatus('error', detail + ' You can email me at g.tse8888@gmail.com instead.');
            return;
          }
          recent.push(Date.now());
          try { localStorage.setItem(RATE.key, JSON.stringify(recent)); } catch (e) {}
          form.reset();
          setStatus('ok', 'Message sent. I will reply to ' + data.email.trim() + '.');
        })
        .catch(function () {
          setStatus('error',
            'The message could not be sent. Check your connection, or email me at g.tse8888@gmail.com.');
        })
        .then(function () { setBusy(false); });
    });

    // Clear a field's error as soon as the person starts fixing it.
    ['name', 'email', 'message'].forEach(function (id) {
      var input = $('#' + id, form);
      if (input) {
        input.addEventListener('input', function () {
          if (input.getAttribute('aria-invalid')) setError(id, '');
        });
      }
    });
  }

  /* -- 9. Footer year ----------------------------------------------------- */

  $$('[data-year]').forEach(function (el) {
    el.textContent = String(new Date().getFullYear());
  });
})();
