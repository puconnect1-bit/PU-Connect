/**
 * PU-Connect — Shared server-side wishlist client.
 *
 * Loaded once (see each page's <head>). It keeps the browser's localStorage
 * cache in sync with the server (the source of truth) and degrades gracefully
 * to localStorage-only when the user is offline / not authenticated.
 *
 * Public API:
 *   WishlistAPI.isAuthed()            -> bool
 *   WishlistAPI.isSaved(id)           -> bool   (live, checks server cache + localStorage)
 *   WishlistAPI.savedIds()            -> Set    (live, mutated in place)
 *   WishlistAPI.loadSavedIds()        -> Promise<Set>  (server-first; seeds cache)
 *   WishlistAPI.loadItems()           -> Promise<array> (full serialized items, for /wishlist)
 *   WishlistAPI.toggle(id)            -> Promise<true|false|null>  (null = guest/unreachable)
 *
 * CSRF is read from the csrftoken cookie (same approach as notifications.js).
 */
(function () {
  'use strict';

  var TOGGLE = '/listings/api/wishlist/toggle/';
  var LIST = '/listings/api/wishlist/';
  var IDS_KEY = 'pu-wish-ids';
  var ITEMS_KEY = 'pu-wish-items';

  var _ids = new Set();
  var _authed = (window.WISH_AUTH === true);

  function csrf() {
    try {
      var m = document.cookie.match(/csrftoken=([^;]+)/);
      return m ? m[1] : '';
    } catch (e) { return ''; }
  }

  function readIds() {
    try { return JSON.parse(localStorage.getItem(IDS_KEY) || '[]'); }
    catch (e) { return []; }
  }

  function writeIds(ids) {
    try { localStorage.setItem(IDS_KEY, JSON.stringify(ids)); }
    catch (e) { /* storage full / disabled */ }
  }

  // Always reflect the latest localStorage into the live set, then return it.
  function syncFromStorage() {
    _ids.clear();
    readIds().forEach(function (x) { _ids.add(String(x)); });
    return _ids;
  }

  // Cache full item objects (write by detail page) so other pages can read them.
  function cacheItems(items) {
    try {
      var map = {};
      var ids = [];
      (items || []).forEach(function (x) {
        var k = String(x.id);
        map[k] = x;
        ids.push(k);
      });
      localStorage.setItem(ITEMS_KEY, JSON.stringify(map));
      _ids.clear();
      ids.forEach(function (k) { _ids.add(k); });
      writeIds(ids);
    } catch (e) { /* ignore */ }
  }

  window.WishlistAPI = {
    isAuthed: function () { return _authed && window.WISH_AUTH === true; },

    // Live Set<String> of saved ids, seeded from localStorage on load.
    savedIds: function () { return syncFromStorage(); },

    isSaved: function (id) {
      syncFromStorage();
      return _ids.has(String(id));
    },

    // Server-first: fetch saved ids, seed the localStorage cache, return a Set.
    loadSavedIds: function () {
      syncFromStorage();
      if (!this.isAuthed()) { return Promise.resolve(new Set(_ids)); }
      return fetch(LIST, { credentials: 'same-origin' })
        .then(function (r) {
          if (!r.ok) { return new Set(_ids); }
          return r.json().then(function (j) {
            var ids = (j.listings || []).map(function (x) { return String(x.id); });
            _ids.clear();
            ids.forEach(function (k) { _ids.add(k); });
            writeIds(ids);
            return new Set(_ids);
          });
        })
        .catch(function () { return new Set(_ids); });
    },

    // Server-first full item list (used by the /wishlist page).
    loadItems: function () {
      if (!this.isAuthed()) {
        var m = {};
        try { m = JSON.parse(localStorage.getItem(ITEMS_KEY) || '{}'); } catch (e) {}
        return Promise.resolve(Object.keys(m).map(function (k) { return m[k]; }));
      }
      return fetch(LIST, { credentials: 'same-origin' })
        .then(function (r) {
          if (!r.ok) { return []; }
          return r.json().then(function (j) {
            cacheItems(j.listings || []);
            return (j.listings || []).map(function (x) { return x; });
          });
        })
        .catch(function () { return []; });
    },

    // Toggle the server row. Returns the resulting saved-state (true/false),
    // or null when the request could not be performed (guest/offline).
    toggle: function (id) {
      var id = String(id);
      if (!this.isAuthed()) { return Promise.resolve(null); }
      return fetch(TOGGLE, {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'X-CSRFToken': csrf(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ listing_id: id })
      })
        .then(function (r) {
          if (!r.ok) { return null; }
          return r.json().then(function (j) {
            var saved = !!j.saved;
            if (saved) { _ids.add(id); } else { _ids.delete(id); }
            writeIds(Array.from(_ids));
            return saved;
          });
        })
        .catch(function () { return null; });
    }
  };

  // Seed the live set from localStorage immediately so hearts are correct
  // before the async server fetch resolves.
  syncFromStorage();
})();
