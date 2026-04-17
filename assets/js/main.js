/* ═══════════════════════════════════════════════════════════
   BASTE TRAVELS — main.js
═══════════════════════════════════════════════════════════ */

(function() {
  'use strict';

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
})();
