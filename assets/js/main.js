/* ═══════════════════════════════════════════════════════════
   BASTE TRAVELS — main.js
═══════════════════════════════════════════════════════════ */

(function() {
  'use strict';

  // ─── Analytics (GA4) ───
  // Set GA4_ID to the property's Measurement ID (G-XXXXXXXXXX) to start sending data.
  // Until then events are only pushed to window.dataLayer, so nothing breaks.
  const GA4_ID = '';
  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }
  if (GA4_ID) {
    const s = document.createElement('script');
    s.async = true;
    s.src = `https://www.googletagmanager.com/gtag/js?id=${GA4_ID}`;
    document.head.appendChild(s);
    gtag('js', new Date());
    gtag('config', GA4_ID);
  }
  const track = (name, params = {}) => {
    gtag('event', name, Object.assign({ page_title: document.title, page_path: location.pathname }, params));
  };
  const ctaLocation = (el) => {
    const zone = el.closest('header, .mobile-drawer, .hero, .page-hero, .route-hero, .assure, .sticky-bar, .float-cta, .cta-section, footer, form');
    if (!zone) return 'body';
    return zone.id || zone.className.split(' ')[0] || zone.tagName.toLowerCase();
  };
  document.addEventListener('click', (e) => {
    const a = e.target.closest('a[href]');
    if (!a) return;
    const href = a.getAttribute('href');
    if (/wa\.me|api\.whatsapp\.com/.test(href)) track('whatsapp_click', { cta_location: ctaLocation(a) });
    else if (href.startsWith('tel:')) track('call_click', { cta_location: ctaLocation(a) });
    else if (/(^|\/)pay\.html|razorpay\.me/.test(href)) track('pay_click', { cta_location: ctaLocation(a) });
  });
  document.addEventListener('submit', (e) => {
    const form = e.target;
    const val = (id) => (form.querySelector(`#${id}`) || {}).value || '';
    if (form.id === 'quickBookForm') track('quote_form_submit', { trip_type: val('qb-type'), from: val('qb-from'), to: val('qb-to') });
    else track('quote_form_submit', { form_name: form.id || form.dataset.waForm || 'form' });
  }, true);

  // ─── Sticky header shadow ───
  const header = document.querySelector('header');
  if (header) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 10) header.classList.add('scrolled');
      else header.classList.remove('scrolled');
    }, { passive: true });
  }

  // ─── Mobile drawer ───
  const hamburger = document.querySelector('.hamburger');
  const drawer = document.querySelector('.mobile-drawer');
  const drawerClose = document.querySelector('.mobile-drawer-close');
  if (hamburger && drawer) {
    hamburger.addEventListener('click', () => drawer.classList.add('open'));
  }
  if (drawerClose && drawer) {
    drawerClose.addEventListener('click', () => drawer.classList.remove('open'));
  }
  if (drawer) {
    drawer.addEventListener('click', (e) => {
      if (e.target === drawer) drawer.classList.remove('open');
    });
  }

  // ─── Fare calculator ───
  const kmInput = document.getElementById('kmInput');
  const fareOut = document.getElementById('fareOut');
  const RATE = 12;
  const MIN_KM = 300;
  const fmt = (n) => '₹' + n.toLocaleString('en-IN');

  if (kmInput && fareOut) {
    const update = () => {
      const km = Math.max(parseFloat(kmInput.value) || 0, MIN_KM);
      fareOut.textContent = fmt(Math.round(km * RATE));
      fareOut.style.transform = 'scale(1.05)';
      setTimeout(() => { fareOut.style.transform = 'scale(1)'; }, 140);
    };
    kmInput.addEventListener('input', update);
  }

  // ─── Quick booking form → WhatsApp ───
  const qbForm = document.getElementById('quickBookForm');
  if (qbForm) {
    qbForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const name = (document.getElementById('qb-name') || {}).value || '';
      const phone = (document.getElementById('qb-phone') || {}).value || '';
      const from = (document.getElementById('qb-from') || {}).value || '';
      const to = (document.getElementById('qb-to') || {}).value || '';
      const date = (document.getElementById('qb-date') || {}).value || '';
      const type = (document.getElementById('qb-type') || {}).value || '';

      const msg = `Hi Baste Travels, I'd like to book a cab.%0A%0A` +
                  `Name: ${encodeURIComponent(name)}%0A` +
                  `Phone: ${encodeURIComponent(phone)}%0A` +
                  `Trip: ${encodeURIComponent(type)}%0A` +
                  `From: ${encodeURIComponent(from)}%0A` +
                  `To: ${encodeURIComponent(to)}%0A` +
                  `Date: ${encodeURIComponent(date)}`;

      window.open(`https://wa.me/917507958364?text=${msg}`, '_blank');
    });
  }

  // ─── Contact form → WhatsApp ───
  const contactForm = document.getElementById('contactForm');
  if (contactForm) {
    contactForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const name = (document.getElementById('cf-name') || {}).value || '';
      const phone = (document.getElementById('cf-phone') || {}).value || '';
      const email = (document.getElementById('cf-email') || {}).value || '';
      const msg = (document.getElementById('cf-msg') || {}).value || '';

      const text = `Hi Baste Travels,%0A%0A` +
                   `Name: ${encodeURIComponent(name)}%0A` +
                   `Phone: ${encodeURIComponent(phone)}%0A` +
                   `Email: ${encodeURIComponent(email)}%0A%0A` +
                   `Message: ${encodeURIComponent(msg)}`;
      window.open(`https://wa.me/917507958364?text=${text}`, '_blank');
    });
  }

  // ─── Page-aware WhatsApp links: tag generic inquiries with the page they came from ───
  const GENERIC_WA_TEXT = 'Hi%20Baste%20Travels%2C%20I%20want%20to%20book%20a%20cab';
  const pageH1 = document.querySelector('h1');
  const pageTopic = pageH1 ? pageH1.textContent.replace(/\s+/g, ' ').trim() : '';
  if (pageTopic && !document.body.dataset.waGeneric) {
    document.querySelectorAll(`a[href$="text=${GENERIC_WA_TEXT}"]`).forEach((a) => {
      a.href += encodeURIComponent(` (${pageTopic})`);
    });
  }

  // ─── Generic form → WhatsApp (form[data-wa-form], fields with data-wa-label) ───
  document.querySelectorAll('form[data-wa-form]').forEach((form) => {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const lines = [`Hi Baste Travels, ${form.dataset.waForm}`, ''];
      form.querySelectorAll('[data-wa-label]').forEach((field) => {
        if (field.value) lines.push(`${field.dataset.waLabel}: ${field.value}`);
      });
      window.open(`https://wa.me/917507958364?text=${encodeURIComponent(lines.join('\n'))}`, '_blank');
    });
  });

  // ─── Reveal on scroll ───
  const io = new IntersectionObserver((entries) => {
    entries.forEach((el) => {
      if (el.isIntersecting) {
        el.target.classList.add('visible');
        io.unobserve(el.target);
      }
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -50px 0px' });

  document.querySelectorAll('.reveal').forEach((el) => io.observe(el));

  // ─── Set min date to today for date inputs ───
  const today = new Date().toISOString().split('T')[0];
  document.querySelectorAll('input[type="date"]').forEach((i) => i.setAttribute('min', today));

  // ─── Service Worker registration ───
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('service-worker.js').catch(() => {});
    });
  }

  // ─── Pay page: auto-open Razorpay payment link ───
  // Link + delay live on #payBox (data-pay-url, data-auto-open seconds); ?auto=0 disables.
  const payBox = document.getElementById('payBox');
  if (payBox && payBox.dataset.payUrl) {
    const payUrl = payBox.dataset.payUrl;
    const delay = parseInt(payBox.dataset.autoOpen, 10);
    const autoOff = new URLSearchParams(location.search).get('auto') === '0';
    const countdown = document.getElementById('payCountdown');
    const secEl = document.getElementById('payCountdownSec');
    const cancelBtn = document.getElementById('payCancelBtn');
    const payNowBtn = document.getElementById('payNowBtn');
    if (payNowBtn) payNowBtn.href = payUrl;

    if (!autoOff && delay > 0 && countdown) {
      let left = delay;
      if (secEl) secEl.textContent = left;
      countdown.hidden = false;
      const timer = setInterval(() => {
        left -= 1;
        if (secEl) secEl.textContent = left;
        if (left <= 0) {
          clearInterval(timer);
          window.location.assign(payUrl);
        }
      }, 1000);
      if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
          clearInterval(timer);
          countdown.hidden = true;
        });
      }
    }
  }

  // ─── Razorpay checkout integration for booking page ───
  const paymentApiBase = window.PAYMENT_API_BASE || '/api';
  const razorpayPayBtn = document.getElementById('razorpayPayBtn');
  const paymentAmountInput = document.getElementById('paymentAmount');
  const paymentStatus = document.getElementById('paymentStatus');

  const setPaymentStatus = (message, type = 'info') => {
    if (!paymentStatus) return;
    paymentStatus.style.display = 'block';
    paymentStatus.style.color = type === 'error' ? '#b00020' : type === 'success' ? '#047857' : '#1b4f8f';
    paymentStatus.textContent = message;
  };

  const updatePayButtonLabel = () => {
    if (!razorpayPayBtn || !paymentAmountInput) return;
    const amount = parseFloat(paymentAmountInput.value) || 3600;
    razorpayPayBtn.textContent = `Pay ₹${amount.toLocaleString('en-IN')}`;
  };

  const parseJsonOrText = async (resp) => {
    const text = await resp.text();
    if (!text) return null;
    try {
      return JSON.parse(text);
    } catch (_err) {
      return { error: text.trim() || 'Unexpected server response.' };
    }
  };

  const fetchRazorpayKey = async () => {
    const resp = await fetch(`${paymentApiBase}/config`);
    if (!resp.ok) {
      const errorData = await parseJsonOrText(resp);
      throw new Error(errorData?.error || 'Unable to load payment configuration.');
    }
    const data = await parseJsonOrText(resp);
    if (!data || !data.razorpay_key_id) {
      throw new Error('Razorpay public key is unavailable.');
    }
    return data.razorpay_key_id;
  };

  const createOrder = async (amountPaise) => {
    const resp = await fetch(`${paymentApiBase}/create-order`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount: amountPaise, currency: 'INR' }),
    });

    if (!resp.ok) {
      const errorData = await parseJsonOrText(resp);
      throw new Error(errorData?.error || `Unable to create payment order. (${resp.status})`);
    }

    const data = await parseJsonOrText(resp);
    if (!data || !data.order_id) {
      throw new Error('Invalid response from payment server.');
    }
    return data;
  };

  const verifyPayment = async (payload) => {
    const resp = await fetch(`${paymentApiBase}/verify-payment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!resp.ok) {
      const errorData = await parseJsonOrText(resp);
      throw new Error(errorData?.error || `Payment verification failed. (${resp.status})`);
    }

    return await parseJsonOrText(resp);
  };

  const openRazorpayCheckout = async (order) => {
    const keyId = await fetchRazorpayKey();
    if (typeof window.Razorpay !== 'function') {
      throw new Error('Razorpay checkout script failed to load.');
    }

    const options = {
      key: keyId,
      amount: order.amount,
      currency: order.currency,
      name: 'Baste Travels',
      description: 'Cab booking payment',
      order_id: order.order_id,
      handler: async function (response) {
        try {
          setPaymentStatus('Verifying payment…');
          const result = await verifyPayment(response);
          if (result.success) {
            setPaymentStatus('Payment successful. Thank you!', 'success');
            track('payment_success', { value: order.amount / 100, currency: order.currency });
          } else {
            setPaymentStatus(result.error || 'Payment verification failed.', 'error');
          }
        } catch (error) {
          setPaymentStatus(error.message || 'Verification failed.', 'error');
        }
      },
      modal: {
        ondismiss: () => {
          setPaymentStatus('Payment modal closed. No payment was completed.', 'error');
        },
      },
      prefill: {
        name: document.getElementById('qb-name')?.value || '',
        contact: document.getElementById('qb-phone')?.value || '',
      },
    };

    const rzp = new Razorpay(options);
    rzp.on('payment.failed', function (response) {
      setPaymentStatus(response.error?.description || 'Payment failed. Please try again.', 'error');
    });
    rzp.open();
  };

  if (paymentAmountInput) {
    paymentAmountInput.addEventListener('input', updatePayButtonLabel);
    updatePayButtonLabel();
  }

  if (razorpayPayBtn) {
    razorpayPayBtn.addEventListener('click', async (event) => {
      event.preventDefault();
      if (!paymentAmountInput) return;

      const amountRupees = parseFloat(paymentAmountInput.value);
      if (Number.isNaN(amountRupees) || amountRupees <= 0) {
        setPaymentStatus('Enter a valid payment amount.', 'error');
        return;
      }

      const amountPaise = Math.round(amountRupees * 100);
      if (amountPaise < 100) {
        setPaymentStatus('Amount must be at least ₹1.00.', 'error');
        return;
      }

      try {
        setPaymentStatus('Creating payment order…');
        const order = await createOrder(amountPaise);
        await openRazorpayCheckout(order);
      } catch (error) {
        setPaymentStatus(error.message || 'Unable to start payment.', 'error');
      }
    });
  }
})();
