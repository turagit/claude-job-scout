(function () {
  'use strict';

  if (window.__REPORT_INTERACTIVE_LOADED__) return;
  window.__REPORT_INTERACTIVE_LOADED__ = true;

  // Sort handlers
  document.querySelectorAll('.toolbar [data-sort]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var key = btn.dataset.sort;
      var toolbar = btn.closest('.toolbar');
      var list = toolbar && toolbar.nextElementSibling;
      if (!list) return;
      var items = Array.prototype.slice.call(list.children).filter(function (el) {
        return el.dataset && el.dataset['sort_' + key] !== undefined;
      });
      items.sort(function (a, b) {
        var av = a.dataset['sort_' + key] || '';
        var bv = b.dataset['sort_' + key] || '';
        if (key === 'score') {
          return (parseInt(bv, 10) || 0) - (parseInt(av, 10) || 0);
        }
        if (key === 'date') {
          return (new Date(bv)).getTime() - (new Date(av)).getTime();
        }
        return av.localeCompare(bv);
      });
      items.forEach(function (item) { list.appendChild(item); });
      toolbar.querySelectorAll('[data-sort]').forEach(function (b) { b.classList.remove('active'); });
      btn.classList.add('active');
    });
  });

  // Filter handlers (tier-based and unread-based)
  document.querySelectorAll('.toolbar [data-filter]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var filter = btn.dataset.filter;
      var attr = btn.dataset.filterAttr || 'tier';
      var toolbar = btn.closest('.toolbar');
      var list = toolbar && toolbar.nextElementSibling;
      if (!list) return;
      list.querySelectorAll('[data-' + attr + ']').forEach(function (item) {
        if (filter === 'all' || item.dataset[attr] === filter) {
          item.style.display = '';
        } else {
          item.style.display = 'none';
        }
      });
      toolbar.querySelectorAll('[data-filter][data-filter-attr="' + attr + '"], [data-filter]:not([data-filter-attr])').forEach(function (b) {
        if ((b.dataset.filterAttr || 'tier') === attr) b.classList.remove('active');
      });
      btn.classList.add('active');
    });
  });

  // Fold expand/collapse
  document.querySelectorAll('.fold .fold-header').forEach(function (header) {
    header.addEventListener('click', function () {
      header.parentElement.classList.toggle('open');
    });
  });

  // Mark-as-read (visual only — does not persist)
  document.querySelectorAll('[data-mark-read]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var targetId = btn.dataset.markRead;
      var target = document.getElementById(targetId);
      if (!target) return;
      target.classList.toggle('read');
    });
  });

  // Copy-to-clipboard
  document.querySelectorAll('.copy-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var targetId = btn.dataset.copyTarget;
      var target = document.getElementById(targetId);
      if (!target || !navigator.clipboard) return;
      var text = target.innerText || target.textContent || '';
      navigator.clipboard.writeText(text.trim()).then(function () {
        var orig = btn.textContent;
        btn.classList.add('copied');
        btn.textContent = 'Copied!';
        setTimeout(function () {
          btn.classList.remove('copied');
          btn.textContent = orig;
        }, 1500);
      }).catch(function () {
        btn.textContent = 'Copy failed';
        setTimeout(function () { btn.textContent = 'Copy'; }, 1500);
      });
    });
  });

  // Expose embedded data for any inline view-specific scripts
  var dataEl = document.getElementById('report-data');
  if (dataEl) {
    try {
      window.__REPORT_DATA__ = JSON.parse(dataEl.textContent);
    } catch (e) {
      window.__REPORT_DATA__ = null;
      if (window.console && console.warn) {
        console.warn('interactive.js: failed to parse #report-data JSON', e);
      }
    }
  }
})();
