(function () {
  'use strict';
  var root = document.documentElement, toggle = document.getElementById('themeToggle');
  function applyTheme(t) { if (t === 'dark') root.setAttribute('data-theme', 'dark'); else root.removeAttribute('data-theme'); toggle.textContent = t === 'dark' ? 'Light mode' : 'Dark mode'; toggle.setAttribute('aria-pressed', t === 'dark' ? 'true' : 'false'); }
  var saved = null; try { saved = localStorage.getItem('arc-theme'); } catch (e) {}
  applyTheme(saved || (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
  toggle.addEventListener('click', function () { var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark'; applyTheme(next); try { localStorage.setItem('arc-theme', next); } catch (e) {} });

  var osBtn = document.getElementById('osToggle');
  function applyOs(o) { if (o === 'mac') root.setAttribute('data-os', 'mac'); else root.removeAttribute('data-os'); osBtn.textContent = o === 'mac' ? 'macOS' : 'Windows'; osBtn.setAttribute('aria-label', 'Commands shown for ' + osBtn.textContent + '; click to switch'); }
  var savedOs = null; try { savedOs = localStorage.getItem('arc-os'); } catch (e) {}
  applyOs(savedOs || (/Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent) ? 'mac' : 'win'));
  osBtn.addEventListener('click', function () { var next = root.getAttribute('data-os') === 'mac' ? 'win' : 'mac'; applyOs(next); try { localStorage.setItem('arc-os', next); } catch (e) {} });

  /* icons on the boxes */
  var ICON = {
    you: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2.5" y="6" width="19" height="12" rx="2"/><path d="M6 10h.01M10 10h.01M14 10h.01M18 10h.01M8 14h8"/></svg>',
    claude: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/></svg>',
    disk: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg>',
    plain: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2a7 7 0 0 0-4 12.7V17a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-2.3A7 7 0 0 0 12 2z"/><path d="M9 21h6"/></svg>'
  };
  ['you', 'claude', 'disk'].forEach(function (k) {
    document.querySelectorAll('.box.' + k + ' > .box__bar').forEach(function (bar) { if (!bar.querySelector('svg')) bar.insertAdjacentHTML('afterbegin', ICON[k]); });
  });
  document.querySelectorAll('.plain').forEach(function (p) { if (!p.querySelector('svg')) p.insertAdjacentHTML('afterbegin', ICON.plain); });

  /* tabs */
  document.querySelectorAll('.tabs').forEach(function (tabs) {
    var host = tabs.parentElement, btns = Array.prototype.slice.call(tabs.querySelectorAll('.tab'));
    btns.forEach(function (b) { b.addEventListener('click', function () {
      btns.forEach(function (x) { x.setAttribute('aria-selected', x === b ? 'true' : 'false'); });
      Array.prototype.forEach.call(host.querySelectorAll(':scope > .pane'), function (p) { p.classList.toggle('is-on', p.id === b.getAttribute('data-pane')); });
    }); });
  });

  /* copy buttons */
  function copyText(btn, text) {
    var done = function () { var old = btn.textContent; btn.textContent = 'copied'; setTimeout(function () { btn.textContent = old; }, 1200); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, done); else done();
  }
  document.querySelectorAll('.you .copy').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var pre = Array.prototype.slice.call(btn.parentElement.querySelectorAll('pre')).filter(function (x) { return x.offsetParent !== null; })[0]; if (!pre) return;
      var clone = pre.cloneNode(true); clone.querySelectorAll('.c').forEach(function (c) { c.remove(); });
      copyText(btn, clone.textContent.replace(/\n{2,}/g, '\n').trim());
    });
  });
  document.querySelectorAll('.cmd .copy').forEach(function (btn) {
    btn.addEventListener('click', function () { var c = btn.parentElement.querySelector('code[data-copy]'); if (c) copyText(btn, c.textContent.trim()); });
  });

  /* syntax highlighting for the embedded files */
  function esc(s) { return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
  var KW = {
    java: 'package import public private protected static final class record interface enum extends implements new return if else for while do try catch finally throw throws this super void int long boolean double float char byte short var null true false instanceof switch case default break continue',
    bash: 'cd set exit echo'
  };
  function kw(list) { return new RegExp('(?:' + list.trim().split(/\s+/).join('|') + ')(?![\\w$])', 'y'); }
  function rules(lang) {
    switch (lang) {
      case 'java': return [['c', /\/\/.*/y], ['c', /\/\*[\s\S]*?\*\//y], ['s', /"(?:[^"\\\n]|\\.)*"/y], ['a', /@[A-Za-z_][\w.]*/y], ['n', /(?<![\w.])\d+(?:\.\d+)?[LlFfDd]?(?![\w])/y], ['k', kw(KW.java)]];
      case 'jsonl': case 'json': return [['k', /"(?:[^"\\]|\\.)*"(?=\s*:)/y], ['s', /"(?:[^"\\]|\\.)*"/y], ['n', /(?<![\w.])-?\d+(?:\.\d+)?(?![\w])|\b(?:true|false|null)\b/y]];
      case 'md': return [['k', /^#{1,6} .*$/my], ['s', /`[^`\n]+`/y], ['a', /\*\*[^*\n]+\*\*/y], ['c', /^\|[-:| ]+\|$/my], ['p', /\|/y]];
      case 'yaml': return [['c', /#.*/y], ['k', /^[ \t]*[\w.-]+(?=:)/my], ['s', /"(?:[^"\\\n]|\\.)*"|'(?:[^'\n])*'/y], ['n', /(?<![\w.])-?\d+(?:\.\d+)?(?![\w])|\b(?:true|false)\b/y]];
      case 'bash': return [['c', /#.*/y], ['s', /"(?:[^"\\\n]|\\.)*"/y], ['n', /\$\{[^}]*\}|\$[\w#@?]+|\$\(.*?\)/y], ['k', kw(KW.bash)]];
      case 'xml': return [['c', /<!--[\s\S]*?-->/y], ['c', /<\?[\s\S]*?\?>/y], ['t', /<\/?[\w:.-]+|\/?>/y], ['s', /"(?:[^"\\\n]|\\.)*"/y]];
      default: return [];
    }
  }
  function highlight(src, lang) {
    var R = rules(lang), out = '', i = 0, n = src.length;
    while (i < n) {
      var hit = null, cls = '';
      for (var k = 0; k < R.length; k++) { R[k][1].lastIndex = i; var m = R[k][1].exec(src); if (m && m.index === i && m[0].length) { hit = m[0]; cls = R[k][0]; break; } }
      if (hit) { out += '<span class="tok-' + cls + '">' + esc(hit) + '</span>'; i += hit.length; }
      else {
        var j = i + 1;
        if (src[i] !== '\n') {
          while (j < n && !/[\w"'`#@\/\-$*{,\n|<>]/.test(src[j])) j++;
          if (/\w/.test(src[i])) { j = i; while (j < n && /[\w$]/.test(src[j])) j++; }
        }
        out += esc(src.slice(i, j)); i = j;
      }
    }
    return out;
  }
  function highlightDiff(src, sub) {
    return src.split('\n').map(function (line, idx, arr) {
      var nl = idx < arr.length - 1 ? '\n' : '';
      if (/^(@@|---|\+\+\+)/.test(line)) return '<span class="tok-c">' + esc(line) + '</span>' + nl;
      if (line[0] === '+' || line[0] === '-') return '<span class="' + (line[0] === '+' ? 'ln-add' : 'ln-del') + '">' + esc(line[0]) + highlight(line.slice(1), sub) + '</span>';
      return highlight(line, sub) + nl;
    }).join('');
  }
  document.querySelectorAll('textarea.src').forEach(function (ta) {
    var lang = ta.getAttribute('data-lang') || '', pre = document.createElement('pre');
    pre.setAttribute('tabindex', '0');
    pre.innerHTML = lang === 'diff' ? highlightDiff(ta.value, ta.getAttribute('data-sub') || 'java') : highlight(ta.value, lang);
    if (/^(json|jsonl|md|yaml|bash|text)$/.test(lang)) ta.parentNode.classList.add('code--wrap');
    ta.parentNode.insertBefore(pre, ta.nextSibling);
  });

  /* scroll-spy: rail, progress */
  var steps = Array.prototype.slice.call(document.querySelectorAll('.step[data-step]'));
  var links = {}; document.querySelectorAll('.rl').forEach(function (a) { links[a.getAttribute('data-step')] = a; });
  var progText = document.getElementById('progText'), progBar = document.getElementById('progBar'), progPhase = document.getElementById('progPhase'), TOTAL = steps.length, current = -1;
  function setCurrent(idx) {
    if (idx === current) return; current = idx;
    steps.forEach(function (s, i) {
      var a = links[s.getAttribute('data-step')]; if (!a) return;
      a.classList.toggle('is-on', i === idx); a.classList.toggle('is-done', i < idx);
      if (i === idx) a.setAttribute('aria-current', 'step'); else a.removeAttribute('aria-current');
    });
    if (idx < 0) { progText.textContent = 'Step 0 of ' + TOTAL; progBar.style.width = '0'; progPhase.textContent = 'Start at the top'; return; }
    var s = steps[idx]; progText.textContent = 'Step ' + s.getAttribute('data-step') + ' of ' + TOTAL; progBar.style.width = ((idx + 1) / TOTAL * 100) + '%';
    var lk = links[s.getAttribute('data-step')]; progPhase.textContent = s.getAttribute('data-phase') + ' · ' + (lk ? lk.querySelector('span').textContent : '');
    var a = links[s.getAttribute('data-step')]; if (a && window.innerWidth <= 900) { var r = a.getBoundingClientRect(), p = a.parentElement.getBoundingClientRect(); if (r.left < p.left || r.right > p.right) a.scrollIntoView({ block: 'nearest', inline: 'center' }); }
  }
  function spy() {
    var line = 130, idx = -1;
    for (var i = 0; i < steps.length; i++) { if (steps[i].getBoundingClientRect().top <= line) idx = i; else break; }
    setCurrent(idx);
  }
  var ticking = false;
  window.addEventListener('scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(function () { spy(); ticking = false; }); } }, { passive: true });
  window.addEventListener('resize', spy);
  spy();
})();
