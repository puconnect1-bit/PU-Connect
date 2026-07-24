/* ============================================================
   THEME MANAGEMENT
   ============================================================ */
(function () {
  const _H = document.documentElement;
  const _TB = document.getElementById('thbtn');
  let _dark = localStorage.getItem('pu-theme') !== 'light';

  function applyTheme(d) {
    _H.setAttribute('data-theme', d ? 'dark' : 'light');
    if (_TB) {
      _TB.innerHTML = d
        ? '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>'
        : '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
    }
    _dark = d;
    localStorage.setItem('pu-theme', d ? 'dark' : 'light');
    const m = document.getElementById('themeColorMeta');
    if (m) m.setAttribute('content', d ? '#0d0e11' : '#f0ede8');
  }

  applyTheme(_dark);
  if (_TB) _TB.addEventListener('click', function () { applyTheme(!_dark); });

  // Expose for inline use if needed
  window._applyTheme = applyTheme;
})();