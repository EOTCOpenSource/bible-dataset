/* Bible Dataset Reader — reads translations.json, books.json,
   apocrypha_books.json and data/<translation>/<Book>.json directly. */
(() => {
  'use strict';

  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const wait = (ms) => new Promise((r) => setTimeout(r, reduceMotion.matches ? 0 : ms));

  /* ---------------------------------------------------------------- i18n */

  const I18N = {
    am: {
      books: 'መጻሕፍት', translation: 'ትርጉም', ot: 'ብሉይ ኪዳን', nt: 'አዲስ ኪዳን', deutero: 'ሊቃውንት',
      chapter: 'ምዕራፍ', chapters: 'ምዕራፎች', filter: 'መጽሐፍ ፈልግ', back: 'ወደ መጻሕፍት',
      search: 'ፍለጋ', searchPh: 'ቃል ወይም ሐረግ ይጻፉ', scopeBook: 'በዚህ መጽሐፍ', scopeAll: 'በሙሉ ትርጉሙ',
      searching: (a, b) => `${a} ከ${b} መጻሕፍት ተፈልጓል`, results: (n) => `${n} ውጤቶች`, more: (n) => `የመጀመሪያዎቹ ${n} ውጤቶች ብቻ ይታያሉ`,
      noResults: 'ምንም አልተገኘም። ሌላ ቃል ይሞክሩ።', searchHint: 'ቢያንስ ሁለት ፊደላት ይጻፉ።',
      settings: 'የንባብ ምርጫዎች', theme: 'ገጽታ', themes: { auto: 'ራስ-ሰር', light: 'ብርሃን', dusk: 'ምሽት', night: 'ሌሊት' },
      size: 'የፊደል መጠን', leading: 'የመስመር ክፍተት', numerals: 'የግዕዝ ቁጥሮች', numeralsHint: '፩ ፪ ፫ በ 1 2 3 ፋንታ',
      lines: 'አንድ ቁጥር በአንድ መስመር', holy: 'ቅዱሳት ስሞች በቀይ', holyHint: 'እንደ ብራና መጻሕፍት እግዚአብሔር፣ ኢየሱስ፣ ማርያም በቀይ ይጻፋሉ',
      verseNums: 'የቁጥር ምልክቶች', parallel: 'ትይዩ ንባብ', parallelPick: 'ለትይዩ ንባብ ሁለተኛ ትርጉም ይምረጡ', parallelOff: 'ትይዩ ንባብን አጥፋ',
      copy: 'ቅዳ', copied: 'ተቀድቷል', share: 'አጋራ', link: 'አገናኝ ቅዳ', linkCopied: 'አገናኙ ተቀድቷል', clear: 'ምርጫ አጽዳ', highlight: 'አድምቅ',
      next: 'ቀጣይ', prev: 'ያለፈው', continue: 'ንባብ ቀጥል', missing: 'ይህ መጽሐፍ በዚህ ትርጉም ውስጥ የለም።',
      missingB: 'በሁለተኛው ትርጉም የለም', loadFail: 'ዳታውን መጫን አልተቻለም።', loadFailHint: 'ገጹን በድር አገልጋይ ይክፈቱ፤ ለምሳሌ python -m http.server',
      preview: 'በመጀመሪያ ቃል ነበረ፥ ቃልም በእግዚአብሔር ዘንድ ነበረ።', count: (n) => `${n} መጻሕፍት`,
    },
    ti: {
      books: 'መጻሕፍቲ', translation: 'ትርጉም', ot: 'ብሉይ ኪዳን', nt: 'ሓድሽ ኪዳን', deutero: 'ካልኣይ ቀኖና',
      chapter: 'ምዕራፍ', chapters: 'ምዕራፋት', filter: 'መጽሓፍ ድለ', back: 'ናብ መጻሕፍቲ',
      search: 'ድለያ', searchPh: 'ቃል ወይ ሓረግ ጽሓፉ', scopeBook: 'ኣብዚ መጽሓፍ', scopeAll: 'ኣብ ምሉእ ትርጉም',
      noResults: 'ዝተረኽበ የለን። ካልእ ቃል ፈትኑ።', next: 'ዝቕጽል', prev: 'ዝሓለፈ', continue: 'ንባብ ቀጽል',
      missing: 'እዚ መጽሓፍ ኣብዚ ትርጉም የለን።', copy: 'ቅዳሕ', copied: 'ተቐዲሑ', share: 'ኣካፍል',
      preview: 'ኣብ መጀመርታ ቃል ነበረ፡ እቲ ቓል ድማ ምስ ኣምላኽ ነበረ።',
    },
    om: {
      books: 'Kitaabota', translation: 'Hiika', ot: 'Kakuu Moofaa', nt: 'Kakuu Haaraa', deutero: 'Deuterokanoonii',
      chapter: 'Boqonnaa', chapters: 'Boqonnaalee', filter: 'Kitaaba barbaadi', back: 'Gara kitaabotaatti',
      search: 'Barbaacha', searchPh: 'Jecha ykn gaalee barreessi', scopeBook: 'Kitaaba kana keessa', scopeAll: 'Hiika guutuu keessa',
      noResults: 'Homtuu hin argamne. Jecha biraa yaali.', next: 'Itti aanu', prev: 'Duraa', continue: 'Dubbisuu itti fufi',
      missing: 'Kitaabni kun hiika kana keessa hin jiru.', copy: 'Garagalchi', copied: 'Garagalfameera', share: 'Qoodi',
      preview: 'Jalqabatti Dubbichi ture; Dubbichis Waaqa biras ture.',
    },
    en: {
      books: 'Books', translation: 'Translation', ot: 'Old Testament', nt: 'New Testament', deutero: 'Deuterocanon',
      chapter: 'Chapter', chapters: 'Chapters', filter: 'Find a book', back: 'Back to books',
      search: 'Search', searchPh: 'Type a word or phrase', scopeBook: 'This book', scopeAll: 'Whole translation',
      searching: (a, b) => `Searched ${a} of ${b} books`, results: (n) => `${n} results`, more: (n) => `Showing the first ${n} results`,
      noResults: 'Nothing found. Try a different word.', searchHint: 'Type at least two letters.',
      settings: 'Reading settings', theme: 'Theme', themes: { auto: 'Auto', light: 'Light', dusk: 'Dusk', night: 'Night' },
      size: 'Text size', leading: 'Line spacing', numerals: 'Ge\u2019ez numerals', numeralsHint: '፩ ፪ ፫ instead of 1 2 3',
      lines: 'One verse per line', holy: 'Holy names in red', holyHint: 'As in Ge\u2019ez manuscripts, God, Jesus and Mary are written in red',
      verseNums: 'Verse numbers', parallel: 'Parallel reading', parallelPick: 'Pick a second translation to read alongside', parallelOff: 'Turn off parallel reading',
      copy: 'Copy', copied: 'Copied', share: 'Share', link: 'Copy link', linkCopied: 'Link copied', clear: 'Clear selection', highlight: 'Highlight',
      next: 'Next', prev: 'Previous', continue: 'Keep reading', missing: 'This book is not in this translation.',
      missingB: 'Not in the second translation', loadFail: 'The reader could not load its data.', loadFailHint: 'Open it through a web server, for example python -m http.server',
      preview: 'In the beginning was the Word, and the Word was with God.', count: (n) => `${n} books`,
    },
  };
  const UI_LANG = { amh: 'am', gez: 'am', tir: 'ti', orm: 'om' };
  const FALLBACK = { ti: 'am', om: 'en', am: 'en', en: 'en' };
  function tr(key, ...args) {
    let lang = UI_LANG[state.t?.language_code] || 'en';
    for (let i = 0; i < 3; i++) {
      const v = I18N[lang]?.[key];
      if (v !== undefined) return typeof v === 'function' ? v(...args) : v;
      lang = FALLBACK[lang];
    }
    const v = I18N.en[key];
    return typeof v === 'function' ? v(...args) : (v ?? key);
  }

  /* --------------------------------------------------------------- state */

  const state = {
    translations: [], books: [], apocrypha: [],
    t: null, t2: null,
    book: null, doc: null, doc2: null,
    chapter: 1, verse: null,
    available: new Set(),
    sel: new Set(),
    tab: 'old',
  };
  const prefs = {
    theme: 'auto', size: 21, leading: 1.95, geez: true, lines: false, holy: true, vn: true, parallel: null, side: true,
  };
  const store = {
    get(k) { try { return JSON.parse(localStorage.getItem('bd.' + k)); } catch { return null; } },
    set(k, v) { try { localStorage.setItem('bd.' + k, JSON.stringify(v)); } catch { /* private mode */ } },
  };
  let highlights = store.get('hl') || {};
  const cache = new Map();

  /* ------------------------------------------------------------- helpers */

  const SCRIPT_CODE = { Ethiopic: 'Ethi', Latin: 'Latn', Greek: 'Grek', Hebrew: 'Hebr', Coptic: 'Copt' };
  const FONT_FOR = {
    Ethi: 'var(--font-ethi)', Latn: 'var(--font-latn)', Grek: 'var(--font-latn)',
    Hebr: '"Noto Serif Hebrew", var(--font-latn)', Copt: '"Noto Sans Coptic", var(--font-latn)',
  };
  const scriptOf = (t) => SCRIPT_CODE[t?.script] || 'Latn';
  const isEthi = (t = state.t) => scriptOf(t) === 'Ethi';

  function geez(n) {
    const ones = ['', '፩', '፪', '፫', '፬', '፭', '፮', '፯', '፰', '፱'];
    const tens = ['', '፲', '፳', '፴', '፵', '፶', '፷', '፸', '፹', '፺'];
    const two = (x) => tens[Math.floor(x / 10)] + ones[x % 10];
    const h = Math.floor(n / 100), r = n % 100;
    return h ? (h > 1 ? two(h) : '') + '፻' + two(r) : two(r);
  }
  const num = (n, t = state.t) => (prefs.geez && isEthi(t) && /^\d+$/.test(String(n))) ? geez(Number(n)) : String(n);

  const bookName = (b, t = state.t) => (isEthi(t) && b.amharic_name) ? b.amharic_name : b.name;
  const allBooks = () => [...state.books.filter((b) => b.testament === 'old'), ...state.apocrypha, ...state.books.filter((b) => b.testament === 'new')];
  const readingOrder = (avail = state.available) => allBooks().filter((b) => avail.has(b.id));
  const booksInTab = (tab) => tab === 'deutero' ? state.apocrypha : state.books.filter((b) => b.testament === tab);
  const availableIn = (t) => new Set([...(t.books || []), ...(t.apocrypha_books || [])]);
  const tabOf = (b) => b.deutero ? 'deutero' : b.testament;
  const pathOf = (t, b) => (b.deutero ? `data/apocrypha/${t.id}/` : `data/${t.id}/`) + `${b.id}.json`;
  const verseKeys = (ch) => Object.keys(ch.verses).sort((a, b) => parseInt(a, 10) - parseInt(b, 10));

  async function getJSON(url) {
    if (cache.has(url)) return cache.get(url);
    const p = fetch(url).then((r) => { if (!r.ok) throw new Error(`${r.status} ${url}`); return r.json(); });
    cache.set(url, p);
    p.catch(() => cache.delete(url));
    return p;
  }

  function el(tag, attrs = {}, ...kids) {
    const n = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (v === null || v === undefined || v === false) continue;
      if (k === 'class') n.className = v;
      else if (k === 'text') n.textContent = v;
      else if (k.startsWith('on')) n.addEventListener(k.slice(2), v);
      else n.setAttribute(k, v === true ? '' : v);
    }
    for (const k of kids.flat()) if (k !== null && k !== undefined) n.append(k);
    return n;
  }

  /* Holy names are rubricated (written in red) in Ethiopic manuscripts. */
  const HOLY = ['እግዚአብሔር', 'እግዚአብሄር', 'እግዚኣብሄር', 'እግዚአብሔርን', 'ኢየሱስ', 'ኢየሱስን', 'ክርስቶስ', 'ማርያም', 'እግዚእ'];
  const BREAK = '\\s፡።፣፤፥፦፧፨,.;:!?"\'“”‘’()\\[\\]«»';
  const HOLY_RE = new RegExp(`[^${BREAK}]*(?:${HOLY.join('|')})[^${BREAK}]*`, 'gu');

  function textNodes(text, t) {
    if (!(prefs.holy && isEthi(t))) return [document.createTextNode(text)];
    const out = [];
    let last = 0;
    for (const m of text.matchAll(HOLY_RE)) {
      if (m.index > last) out.push(document.createTextNode(text.slice(last, m.index)));
      out.push(el('span', { class: 'holy', text: m[0] }));
      last = m.index + m[0].length;
    }
    if (last < text.length) out.push(document.createTextNode(text.slice(last)));
    return out;
  }

  /* Ḥaräg — the interlace band that decorates Ethiopic manuscript headings.
     Two strands braid around each other; gilt knots sit inside each loop. */
  function harag(width = 312, period = 36, small = false) {
    const h = 34, c = 17, a = 8;
    const strand = (sign) => {
      let d = `M0 ${c}`;
      for (let x = 0, s = sign; x < width; x += period / 2, s = -s) {
        d += ` Q${x + period / 4} ${c - 2 * a * s} ${x + period / 2} ${c}`;
      }
      return d;
    };
    const mid = width / 2;
    const knots = [];
    for (let x = period / 4, i = 0; x < width; x += period / 2, i++) {
      if (!small && Math.abs(x - mid) < 20) continue;
      knots.push(`<rect class="knot" style="--i:${i}" x="${x - 2.5}" y="${c - 2.5}" width="5" height="5" transform="rotate(45 ${x} ${c})"/>`);
    }
    // A small cross medallion interrupts the band at its centre.
    const r = 13;
    const cross = small ? '' : `<g class="medallion">
        <circle cx="${mid}" cy="${c}" r="${r}"/>
        <path d="M${mid} ${c - 8.5}v17M${mid - 8.5} ${c}h17"/>
        <path class="tips" d="M${mid} ${c - 10.5}l2 2-2 2-2-2zM${mid} ${c + 10.5}l2-2-2-2-2 2zM${mid - 10.5} ${c}l2-2 2 2-2 2zM${mid + 10.5} ${c}l-2-2-2 2 2 2z"/>
      </g>`;
    return `<svg class="harag${small ? ' small' : ''}" viewBox="0 0 ${width} ${h}" style="--len:1" aria-hidden="true" focusable="false">
      <path class="strand a" pathLength="1" d="${strand(1)}"/>
      <path class="strand b" pathLength="1" d="${strand(-1)}"/>
      ${knots.join('')}
      ${cross}
    </svg>`;
  }

  /* ---------------------------------------------------------- rendering */

  const page = $('#page');

  function applyPrefs() {
    const root = document.documentElement;
    if (prefs.theme === 'auto') delete root.dataset.theme;
    else root.dataset.theme = prefs.theme;
    root.style.setProperty('--size', prefs.size + 'px');
    root.style.setProperty('--leading', String(prefs.leading));
    const bg = getComputedStyle(document.body).backgroundColor;
    $('meta[name="theme-color"]').setAttribute('content', bg || '#611b1d');
    store.set('prefs', prefs);
  }

  /* Side menu: testament tabs, book list and chapter column (wide screens). */
  let sideTab = null, sideBookId = null;
  function renderSide() {
    if (!state.t) return;
    if (state.book && sideBookId !== state.book.id) { sideTab = tabOf(state.book); }
    if (!sideTab) sideTab = 'old';
    const tabs = [
      { value: 'old', label: tr('ot') },
      { value: 'deutero', label: tr('deutero') },
      { value: 'new', label: tr('nt') },
    ].map((x) => ({ ...x, disabled: !booksInTab(x.value).some((b) => state.available.has(b.id)) }));
    segmented($('#side-tabs'), tabs, sideTab, (v) => { sideTab = v; renderSide(); $('#side-books').scrollTop = 0; });

    const list = $('#side-books');
    list.replaceChildren(...booksInTab(sideTab).map((b) => el('li', {}, el('button', {
      class: 'row', disabled: !state.available.has(b.id), 'aria-current': state.book?.id === b.id ? 'true' : null,
      onclick: () => go(b, 1),
    }, el('span', { class: 'name', text: bookName(b) }), el('span', { class: 'meta', text: num(b.chapters_count) })))));

    const box = $('#side-chapters');
    const bookChanged = sideBookId !== state.book?.id;
    box.replaceChildren();
    box.classList.remove('pop');
    if (state.doc) {
      state.doc.chapters.forEach((c, i) => box.append(el('button', {
        style: `--i:${i}`, 'aria-current': c.chapter === state.chapter ? 'true' : null,
        'aria-label': `${tr('chapter')} ${c.chapter}`, text: num(c.chapter),
        onclick: () => { if (c.chapter !== state.chapter) go(state.book, c.chapter, null, c.chapter > state.chapter ? 'next' : 'prev'); },
      })));
      if (bookChanged) { void box.offsetWidth; box.classList.add('pop'); }
    }
    sideBookId = state.book?.id || null;
    requestAnimationFrame(() => {
      const keep = (container, item) => {
        if (!item) return;
        const top = item.offsetTop - container.offsetTop, bottom = top + item.offsetHeight;
        if (top < container.scrollTop || bottom > container.scrollTop + container.clientHeight) {
          container.scrollTo({ top: top - container.clientHeight / 2 + item.offsetHeight / 2, behavior: bookChanged ? 'auto' : 'smooth' });
        }
      };
      keep(list, list.querySelector('[aria-current="true"]'));
      keep(box, box.querySelector('[aria-current="true"]'));
    });
  }

  function applySide() {
    document.body.classList.toggle('side-on', !!prefs.side);
    $('#side-btn').setAttribute('aria-pressed', String(!!prefs.side));
  }

  function applyChrome() {
    const root = document.documentElement;
    root.dataset.script = scriptOf(state.t);
    root.lang = { amh: 'am', gez: 'gez', tir: 'ti', orm: 'om', som: 'so', heb: 'he', grc: 'grc', cop: 'cop' }[state.t.language_code] || 'en';
    $('#tr-label').textContent = state.t.native_name || state.t.name;
    const ref = state.book ? `${bookName(state.book)} ${num(state.chapter)}` : tr('books');
    $('#ref-label').textContent = ref;
    $('#dock-ref').textContent = ref;
    $('#parallel-btn').setAttribute('aria-pressed', String(!!state.t2));
    $('#parallel-btn').title = tr('parallel');
    $('#search-btn').title = tr('search');
    $('#settings-btn').title = tr('settings');
    const [prev, next] = neighbours();
    for (const b of $$('.js-prev')) { b.disabled = !prev; b.title = tr('prev'); }
    for (const b of $$('.js-next')) { b.disabled = !next; b.title = tr('next'); }
    document.title = state.book ? `${ref} — ${state.t.name}` : 'Bible Dataset Reader';
  }

  function verseEl(chKey, v, text, t, cls = '') {
    const key = `${t.id}/${state.book.id}/${chKey}/${v}`;
    const node = el('span', { class: `v ${cls}`.trim(), 'data-v': v, id: cls.includes('b') ? null : `v${v}` });
    const hl = highlights[key];
    if (hl) node.classList.add(`hl-${hl}`);
    node.append(el('sup', { class: 'vn', text: num(v, t) }), el('span', { class: 't' }, textNodes(text, t)), ' ');
    return node;
  }

  function buildChapter() {
    const frag = document.createDocumentFragment();
    if (!state.doc) {
      frag.append(el('div', { class: 'empty' }, el('strong', { text: state.book ? bookName(state.book) : '' }), tr('missing')));
      return frag;
    }
    const ch = state.doc.chapters.find((c) => c.chapter === state.chapter);
    const head = el('header', { class: 'chapter-head' });
    head.innerHTML = harag();
    head.firstElementChild.classList.add('draw');
    head.append(
      el('div', { class: 'chapter-num rise', 'aria-hidden': 'true', text: num(state.chapter) }),
      el('h1', { class: 'chapter-book' }, bookName(state.book), el('span', { class: 'sr-only', text: ` ${tr('chapter')} ${state.chapter}` })),
      el('div', { class: 'chapter-sub', text: state.t2 ? `${state.t.name} / ${state.t2.name}` : state.t.name }),
    );
    frag.append(head);

    const keys = verseKeys(ch);
    const text = el('div', { class: 'text', dir: state.t.direction === 'rtl' ? 'rtl' : 'ltr' });
    text.classList.toggle('lines', prefs.lines);
    text.classList.toggle('hide-vn', !prefs.vn);

    if (state.t2) {
      const ch2 = state.doc2?.chapters.find((c) => c.chapter === state.chapter);
      text.classList.add('pv');
      text.removeAttribute('dir');
      text.style.setProperty('--font-b', FONT_FOR[scriptOf(state.t2)]);
      const pvHead = el('div', { class: 'pv-head' },
        el('span', { text: state.t.native_name || state.t.name }),
        el('button', { text: state.t2.native_name || state.t2.name, onclick: () => openTranslations('parallel') }));
      frag.append(pvHead);
      const keys2 = ch2 ? verseKeys(ch2) : [];
      const all = [...new Set([...keys, ...keys2])].sort((a, b) => parseInt(a, 10) - parseInt(b, 10));
      for (const v of all) {
        const a = ch.verses[v] !== undefined ? verseEl(ch.chapter, v, ch.verses[v], state.t, 'a') : el('span', { class: 'v a' });
        if (state.t.direction === 'rtl') a.dir = 'rtl';
        const b = ch2 && ch2.verses[v] !== undefined ? verseEl(ch2.chapter, v, ch2.verses[v], state.t2, 'b') : el('span', { class: 'v b', text: v === all[0] && !ch2 ? tr('missingB') : '' });
        if (state.t2.direction === 'rtl') b.dir = 'rtl';
        text.append(a, b);
      }
    } else {
      for (const v of keys) text.append(verseEl(ch.chapter, v, ch.verses[v], state.t));
    }
    const first = text.querySelector('.v.a, .v:not(.b)');
    if (first) first.classList.add('first');
    frag.append(text);

    const [, next] = neighbours();
    const end = el('footer', { class: 'chapter-end' });
    end.innerHTML = harag(144, 36, true);
    if (next) {
      end.append(el('button', { class: 'continue', onclick: () => go(next.book, next.chapter, null, 'next') },
        el('small', { text: tr('continue') }),
        el('span', { text: `${bookName(next.book)} ${num(next.chapter)}` })));
    }
    frag.append(end);
    frag.append(el('p', { class: 'foot-note' },
      'Text from ', el('a', { href: 'https://github.com/Beblia/Holy-Bible-XML-Format', target: '_blank', rel: 'noopener', text: 'Beblia' }),
      '. Each translation remains the copyright of its publisher.'));
    return frag;
  }

  let turning = Promise.resolve();
  function renderChapter(dir) {
    turning = turning.then(async () => {
      const rtl = state.t.direction === 'rtl';
      if (dir && !reduceMotion.matches) {
        page.className = `page turn-out-${dir === 'next' ? (rtl ? 'prev' : 'next') : (rtl ? 'next' : 'prev')}`;
        await wait(150);
      }
      page.replaceChildren(buildChapter());
      page.className = 'page' + (state.t2 ? ' parallel' : '');
      void page.offsetWidth;
      page.classList.add(dir ? `turn-in-${dir === 'next' ? (rtl ? 'prev' : 'next') : (rtl ? 'next' : 'prev')}` : 'turn-in');
      clearSelection(true);
      applyChrome();
      renderSide();
      quietUntil = performance.now() + 500; // keep the bars visible after a jump
      const target = state.verse && $(`#v${CSS.escape(String(state.verse))}`);
      if (target) {
        target.scrollIntoView({ block: 'center' });
        target.classList.add('flash');
      } else {
        window.scrollTo({ top: 0 });
      }
      showBars();
      onScroll();
    });
    return turning;
  }

  function skeleton() {
    page.className = 'page';
    page.replaceChildren(el('div', { class: 'chapter-head' }), el('div', { class: 'skeleton' }, ...Array.from({ length: 9 }, () => el('i'))));
  }

  /* --------------------------------------------------------- navigation */

  function neighbours() {
    if (!state.doc) return [null, null];
    const chs = state.doc.chapters.map((c) => c.chapter);
    const i = chs.indexOf(state.chapter);
    const order = readingOrder();
    const bi = order.findIndex((b) => b.id === state.book.id);
    const prev = i > 0 ? { book: state.book, chapter: chs[i - 1] }
      : bi > 0 ? { book: order[bi - 1], chapter: 'last' } : null;
    const next = i < chs.length - 1 ? { book: state.book, chapter: chs[i + 1] }
      : bi >= 0 && bi < order.length - 1 ? { book: order[bi + 1], chapter: 1 } : null;
    return [prev, next];
  }

  function updateHash() {
    const parts = [state.t.id];
    if (state.book) parts.push(state.book.id, state.chapter);
    if (state.book && state.verse) parts.push(state.verse);
    history.replaceState(null, '', '#' + parts.map(encodeURIComponent).join('/'));
    store.set('pos', parts);
  }

  async function loadDocs() {
    state.doc = null;
    state.doc2 = null;
    const jobs = [getJSON(pathOf(state.t, state.book)).then((d) => { state.doc = d; }).catch(() => { })];
    if (state.t2 && availableIn(state.t2).has(state.book.id)) {
      jobs.push(getJSON(pathOf(state.t2, state.book)).then((d) => { state.doc2 = d; }).catch(() => { }));
    }
    await Promise.all(jobs);
  }

  async function go(book, chapter = 1, verse = null, dir = null) {
    const sameBook = state.book && state.book.id === book.id && state.doc;
    state.book = book;
    state.tab = tabOf(book);
    if (!sameBook) {
      if (!dir) skeleton();
      await loadDocs();
    }
    if (state.doc) {
      const chs = state.doc.chapters.map((c) => c.chapter);
      state.chapter = chapter === 'last' ? chs[chs.length - 1] : (chs.includes(Number(chapter)) ? Number(chapter) : chs[0]);
    }
    state.verse = verse;
    updateHash();
    await renderChapter(dir);
  }

  function step(delta) {
    const [prev, next] = neighbours();
    const target = delta < 0 ? prev : next;
    if (target) go(target.book, target.chapter, null, delta < 0 ? 'prev' : 'next');
  }

  async function setTranslation(id, bookId, chapter, verse) {
    const t = state.translations.find((x) => x.id === id) || state.translations.find((x) => x.id === 'am2000') || state.translations[0];
    state.t = t;
    state.available = availableIn(t);
    if (state.t2 && state.t2.id === t.id) state.t2 = null;
    const all = allBooks();
    let book = all.find((b) => b.id === bookId && state.available.has(b.id))
      || (state.book && all.find((b) => b.id === state.book.id && state.available.has(b.id)))
      || readingOrder()[0];
    state.book = null;
    state.doc = null;
    applyChrome();
    if (book) await go(book, chapter || state.chapter || 1, verse);
  }

  /* ---------------------------------------------------------- selection */

  const actions = $('#actions');

  function refLabel() {
    const vs = [...state.sel].map(Number).sort((a, b) => a - b);
    const ranges = [];
    for (const v of vs) {
      const last = ranges[ranges.length - 1];
      if (last && v === last[1] + 1) last[1] = v; else ranges.push([v, v]);
    }
    const r = ranges.map(([a, b]) => a === b ? `${a}` : `${a}–${b}`).join(', ');
    return `${bookName(state.book)} ${state.chapter}:${r}`;
  }

  function onVerseTap(e) {
    const v = e.target.closest('.v[data-v]');
    if (!v || String(window.getSelection())) return;
    const key = v.dataset.v;
    if (state.sel.has(key)) state.sel.delete(key); else state.sel.add(key);
    $$(`.v[data-v="${CSS.escape(key)}"]`, page).forEach((n) => n.classList.toggle('sel', state.sel.has(key)));
    syncActions();
  }

  function syncActions() {
    const on = state.sel.size > 0;
    actions.classList.toggle('on', on);
    actions.setAttribute('aria-hidden', String(!on));
    if (on) $('.ref', actions).textContent = refLabel();
  }

  function clearSelection(silent) {
    state.sel.clear();
    $$('.v.sel', page).forEach((n) => n.classList.remove('sel'));
    if (!silent || actions.classList.contains('on')) syncActions();
  }

  function selectedText() {
    const ch = state.doc.chapters.find((c) => c.chapter === state.chapter);
    const vs = [...state.sel].sort((a, b) => parseInt(a, 10) - parseInt(b, 10));
    const body = vs.map((v) => (vs.length > 1 ? `${v} ` : '') + (ch.verses[v] || '')).join(' ');
    return `${body}\n— ${refLabel()} (${state.t.name})`;
  }

  function linkFor() {
    const vs = [...state.sel].sort((a, b) => parseInt(a, 10) - parseInt(b, 10));
    return `${location.origin}${location.pathname}#${[state.t.id, state.book.id, state.chapter, vs[0]].map(encodeURIComponent).join('/')}`;
  }

  async function copy(text, msg) {
    try { await navigator.clipboard.writeText(text); } catch {
      const ta = el('textarea', { style: 'position:fixed;opacity:0' });
      ta.value = text; document.body.append(ta); ta.select(); document.execCommand('copy'); ta.remove();
    }
    toast(msg);
  }

  let toastTimer;
  function toast(msg) {
    const t = $('#toast');
    t.textContent = msg;
    t.classList.add('on');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove('on'), 1800);
  }

  function setHighlight(color) {
    for (const v of state.sel) {
      for (const node of $$(`.v[data-v="${CSS.escape(v)}"]`, page)) {
        const t = node.classList.contains('b') ? state.t2 : state.t;
        const key = `${t.id}/${state.book.id}/${state.chapter}/${v}`;
        node.classList.remove('hl-ochre', 'hl-red', 'hl-green', 'hl-blue');
        if (color === 'none') delete highlights[key];
        else { highlights[key] = color; node.classList.add(`hl-${color}`); }
      }
    }
    store.set('hl', highlights);
    clearSelection();
  }

  /* -------------------------------------------------------------- sheets */

  let openSheetEl = null, lastFocus = null;

  function openSheet(id) {
    if (openSheetEl && openSheetEl.id !== id) closeSheet(true);
    const sheet = $('#' + id);
    lastFocus = document.activeElement;
    openSheetEl = sheet;
    sheet.classList.add('on');
    sheet.setAttribute('aria-hidden', 'false');
    $('#scrim').classList.add('on');
    document.body.style.overflow = 'hidden';
    requestAnimationFrame(() => (sheet.querySelector('[autofocus]') || sheet.querySelector('.sheet-head button'))?.focus({ preventScroll: true }));
  }

  function closeSheet(keepScrim) {
    if (!openSheetEl) return;
    openSheetEl.classList.remove('on');
    openSheetEl.style.transform = '';
    openSheetEl.setAttribute('aria-hidden', 'true');
    openSheetEl = null;
    if (!keepScrim) {
      $('#scrim').classList.remove('on');
      document.body.style.overflow = '';
      lastFocus?.focus?.({ preventScroll: true });
    }
  }

  function segmented(container, items, current, onPick) {
    container.replaceChildren();
    const pill = el('span', { class: 'pill', 'aria-hidden': 'true' });
    container.append(pill);
    for (const it of items) {
      container.append(el('button', {
        role: 'tab', 'aria-selected': String(it.value === current), disabled: it.disabled,
        text: it.label, onclick: () => onPick(it.value),
      }));
    }
    requestAnimationFrame(() => {
      const on = container.querySelector('[aria-selected="true"]');
      if (on) { pill.style.left = on.offsetLeft + 'px'; pill.style.width = on.offsetWidth + 'px'; }
    });
  }

  /* books */
  let booksTab = 'old';
  function renderBooksList() {
    const q = $('#book-filter').value.trim().toLowerCase();
    const list = $('#book-list');
    list.replaceChildren();
    const books = q ? allBooks().filter((b) => `${b.name} ${b.amharic_name || ''} ${b.usfm}`.toLowerCase().includes(q)) : booksInTab(booksTab);
    for (const b of books) {
      const has = state.available.has(b.id);
      list.append(el('li', {}, el('button', {
        class: 'row', disabled: !has, 'aria-current': state.book?.id === b.id ? 'true' : null,
        onclick: () => showChapters(b),
      }, el('span', { class: 'name', text: bookName(b) }), el('span', { class: 'meta', text: num(b.chapters_count) }))));
    }
    segmented($('#book-tabs'), [
      { value: 'old', label: tr('ot'), disabled: !booksInTab('old').some((b) => state.available.has(b.id)) },
      { value: 'deutero', label: tr('deutero'), disabled: !booksInTab('deutero').some((b) => state.available.has(b.id)) },
      { value: 'new', label: tr('nt'), disabled: !booksInTab('new').some((b) => state.available.has(b.id)) },
    ], q ? null : booksTab, (v) => { booksTab = v; $('#book-filter').value = ''; renderBooksList(); $('#book-list').parentElement.scrollTop = 0; });
  }

  async function showChapters(b) {
    const grid = $('#chapter-grid');
    $('#chapters-title').textContent = bookName(b);
    grid.replaceChildren();
    grid.classList.remove('pop');
    $('#books-slider').classList.add('second');
    let chapters;
    try { chapters = (await getJSON(pathOf(state.t, b))).chapters.map((c) => c.chapter); }
    catch { chapters = Array.from({ length: b.chapters_count }, (_, i) => i + 1); }
    chapters.forEach((c, i) => grid.append(el('button', {
      style: `--i:${i}`, 'aria-current': state.book?.id === b.id && state.chapter === c ? 'true' : null,
      'aria-label': `${tr('chapter')} ${c}`, text: num(c), onclick: () => { closeSheet(); go(b, c); },
    })));
    void grid.offsetWidth;
    grid.classList.add('pop');
    $('#chapters-back').focus({ preventScroll: true });
  }

  function openBooks() {
    booksTab = state.book ? tabOf(state.book) : 'old';
    $('#books-title').textContent = tr('books');
    $('#book-filter').placeholder = tr('filter');
    $('#chapters-back').setAttribute('aria-label', tr('back'));
    $('#book-filter').value = '';
    renderBooksList();
    if (state.book) showChapters(state.book); else $('#books-slider').classList.remove('second');
    openSheet('sheet-books');
    requestAnimationFrame(() => $('#book-list [aria-current="true"]')?.scrollIntoView({ block: 'center' }));
  }

  /* translations */
  let trMode = 'primary';
  function openTranslations(mode = 'primary') {
    trMode = mode;
    $('#tr-title').textContent = mode === 'parallel' ? tr('parallel') : tr('translation');
    const body = $('#tr-list');
    body.replaceChildren();
    if (mode === 'parallel') {
      body.append(el('p', { class: 'group', text: tr('parallelPick') }));
      if (state.t2) body.append(el('button', { class: 'row', onclick: () => { setParallel(null); closeSheet(); } }, el('span', { class: 'name', text: tr('parallelOff') })));
    }
    const groups = new Map();
    for (const t of state.translations) {
      if (!groups.has(t.language_name)) groups.set(t.language_name, []);
      groups.get(t.language_name).push(t);
    }
    for (const [lang, ts] of groups) {
      body.append(el('div', { class: 'group', text: lang }));
      for (const t of ts) {
        const current = mode === 'parallel' ? state.t2?.id === t.id : state.t.id === t.id;
        body.append(el('button', {
          class: 'row', 'aria-current': current ? 'true' : null,
          disabled: mode === 'parallel' && t.id === state.t.id,
          onclick: () => { closeSheet(); mode === 'parallel' ? setParallel(t.id) : setTranslation(t.id); },
        },
        el('span', { class: 'name', style: `font-family:${FONT_FOR[scriptOf(t)]}`, text: t.native_name || t.name }),
        el('span', { class: 'meta', text: String(t.books_count + (t.apocrypha_books_count || 0)) })));
      }
    }
    openSheet('sheet-tr');
    requestAnimationFrame(() => body.querySelector('[aria-current="true"]')?.scrollIntoView({ block: 'center' }));
  }

  async function setParallel(id) {
    prefs.parallel = id;
    state.t2 = id ? state.translations.find((t) => t.id === id) : null;
    applyPrefs();
    if (state.book) { await loadDocs(); await renderChapter(); }
  }

  /* settings */
  function openSettings() {
    const body = $('#settings-body');
    $('#settings-title').textContent = tr('settings');
    body.replaceChildren();
    const themes = el('div', { class: 'themes', role: 'group', 'aria-label': tr('theme') });
    for (const v of ['auto', 'light', 'dusk', 'night']) {
      themes.append(el('button', {
        class: 'theme', 'data-v': v, 'aria-pressed': String(prefs.theme === v),
        onclick: (e) => { prefs.theme = v; applyPrefs(); $$('.theme', themes).forEach((b) => b.setAttribute('aria-pressed', String(b === e.currentTarget))); },
      }, el('i', { text: 'ሀ' }), tr('themes')[v]));
    }
    body.append(el('div', { class: 'setting' }, el('div', { class: 'label', text: tr('theme') }), themes));

    const preview = el('p', { class: 'preview-line', text: tr('preview') });
    const sizeOut = el('span', { class: 'meta', text: `${prefs.size}` });
    body.append(el('div', { class: 'setting' },
      el('label', { for: 'size-range' }, tr('size'), sizeOut),
      el('input', {
        type: 'range', id: 'size-range', min: 15, max: 34, step: 1, value: prefs.size,
        oninput: (e) => { prefs.size = Number(e.target.value); sizeOut.textContent = prefs.size; preview.style.fontSize = prefs.size + 'px'; applyPrefs(); },
      }), preview));
    preview.style.fontSize = prefs.size + 'px';
    preview.style.lineHeight = prefs.leading;

    body.append(el('div', { class: 'setting' },
      el('label', { for: 'leading-range' }, tr('leading')),
      el('input', {
        type: 'range', id: 'leading-range', min: 1.5, max: 2.5, step: 0.05, value: prefs.leading,
        oninput: (e) => { prefs.leading = Number(e.target.value); preview.style.lineHeight = prefs.leading; applyPrefs(); },
      })));

    const toggle = (key, label, hint, show = true) => {
      if (!show) return;
      const id = `opt-${key}`;
      body.append(el('div', { class: 'setting' },
        el('label', { for: id }, el('span', {}, label, hint ? el('div', { class: 'hint', text: hint }) : null),
          el('span', { class: 'switch' },
            el('input', { type: 'checkbox', id, role: 'switch', checked: prefs[key], onchange: (e) => { prefs[key] = e.target.checked; applyPrefs(); renderChapter(); } }),
            el('span')))));
    };
    toggle('geez', tr('numerals'), tr('numeralsHint'), isEthi() || (state.t2 && isEthi(state.t2)));
    toggle('holy', tr('holy'), tr('holyHint'), isEthi() || (state.t2 && isEthi(state.t2)));
    toggle('lines', tr('lines'));
    toggle('vn', tr('verseNums'));
    openSheet('sheet-settings');
  }

  /* search */
  let searchRun = 0, searchScope = 'book';
  function openSearch() {
    $('#search-title').textContent = tr('search');
    const input = $('#search-input');
    input.placeholder = tr('searchPh');
    renderScope();
    openSheet('sheet-search');
    setTimeout(() => input.focus(), 60);
  }
  function renderScope() {
    segmented($('#search-scope'), [
      { value: 'book', label: tr('scopeBook') },
      { value: 'all', label: tr('scopeAll') },
    ], searchScope, (v) => { searchScope = v; renderScope(); runSearch(); });
  }

  function searchRegex(q) {
    const chars = [...q.normalize('NFD').replace(/\p{M}/gu, '')].map((c) => /\s/.test(c) ? '\\s+' : c.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
    return new RegExp(chars.join('\\p{M}*'), 'giu');
  }

  async function runSearch() {
    const run = ++searchRun;
    const q = $('#search-input').value.trim();
    const list = $('#search-results');
    const status = $('#search-status');
    list.replaceChildren();
    if ([...q].length < 2) { status.replaceChildren(q ? tr('searchHint') : ''); return; }
    const re = searchRegex(q);
    const books = searchScope === 'book' && state.book ? [state.book] : readingOrder();
    const hits = [];
    const LIMIT = 300;
    let done = 0;
    const fill = el('div', { class: 'bar-fill' });
    const label = el('span');
    status.replaceChildren(label, el('div', { class: 'bar-track' }, fill));

    const paint = () => {
      if (run !== searchRun) return;
      label.textContent = done < books.length ? tr('searching', done, books.length) : (hits.length ? tr('results', hits.length >= LIMIT ? `${LIMIT}+` : hits.length) : tr('noResults'));
      fill.style.width = `${(done / books.length) * 100}%`;
      if (done === books.length) fill.parentElement.hidden = true;
      const order = new Map(books.map((b, i) => [b.id, i]));
      hits.sort((a, b) => order.get(a.book.id) - order.get(b.book.id) || a.ch - b.ch || parseInt(a.v, 10) - parseInt(b.v, 10));
      list.replaceChildren(...hits.slice(0, LIMIT).map(hitEl));
    };

    const hitEl = (h) => {
      const text = h.text.normalize('NFD');
      const span = el('span');
      let last = 0;
      re.lastIndex = 0;
      for (const m of text.matchAll(re)) {
        span.append(text.slice(last, m.index), el('mark', { text: m[0] }));
        last = m.index + m[0].length;
      }
      span.append(text.slice(last));
      if (state.t.direction === 'rtl') span.dir = 'rtl';
      return el('button', { class: 'hit', onclick: () => { closeSheet(); go(h.book, h.ch, h.v); } },
        el('b', { text: `${bookName(h.book)} ${num(h.ch)}:${num(h.v)}` }), span);
    };

    let painted = 0;
    const queue = [...books];
    const worker = async () => {
      while (queue.length && run === searchRun) {
        const b = queue.shift();
        try {
          const doc = await getJSON(pathOf(state.t, b));
          for (const c of doc.chapters) {
            for (const v of verseKeys(c)) {
              re.lastIndex = 0;
              if (hits.length < LIMIT && re.test(c.verses[v].normalize('NFD'))) hits.push({ book: b, ch: c.chapter, v, text: c.verses[v] });
            }
          }
        } catch { /* missing file */ }
        done++;
        if (performance.now() - painted > 120 || done === books.length) { painted = performance.now(); paint(); }
      }
    };
    await Promise.all(Array.from({ length: 6 }, worker));
  }

  /* --------------------------------------------- bars, scroll, gestures */

  const bar = $('#bar'), dock = $('#dock'), progress = $('#progress');
  let lastY = 0, quietUntil = 0;
  function showBars() { bar.classList.remove('away'); dock.classList.remove('away'); document.body.classList.remove('bars-away'); }
  function hideBars() { bar.classList.add('away'); dock.classList.add('away'); document.body.classList.add('bars-away'); }
  function onScroll() {
    const y = window.scrollY;
    const max = document.documentElement.scrollHeight - innerHeight;
    progress.style.transform = `scaleX(${max > 0 ? Math.min(1, y / max) : 0})`;
    bar.classList.toggle('scrolled', y > 4);
    if (state.sel.size || openSheetEl || performance.now() < quietUntil) { lastY = y; return; }
    if (y > lastY + 6 && y > 140) hideBars();
    else if (y < lastY - 6 || y >= max - 4) showBars();
    lastY = y;
  }

  function bindSwipe() {
    let x0 = 0, y0 = 0, t0 = 0, tracking = false;
    page.addEventListener('touchstart', (e) => {
      if (e.touches.length !== 1) return;
      tracking = true; x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; t0 = Date.now();
    }, { passive: true });
    page.addEventListener('touchend', (e) => {
      if (!tracking) return;
      tracking = false;
      const dx = e.changedTouches[0].clientX - x0, dy = e.changedTouches[0].clientY - y0;
      if (Math.abs(dx) > 70 && Math.abs(dy) < 50 && Date.now() - t0 < 600 && !String(window.getSelection())) {
        const forward = dx < 0;
        step((state.t.direction === 'rtl' ? !forward : forward) ? 1 : -1);
      }
    }, { passive: true });
  }

  function bindSheetDrag() {
    for (const sheet of $$('.sheet')) {
      const handle = $('.sheet-head', sheet);
      let y0 = null, dy = 0;
      const start = (e) => { if (innerWidth > 760) return; y0 = e.touches[0].clientY; dy = 0; sheet.style.transition = 'none'; };
      const move = (e) => { if (y0 === null) return; dy = Math.max(0, e.touches[0].clientY - y0); sheet.style.transform = `translateY(${dy}px)`; };
      const end = () => {
        if (y0 === null) return;
        y0 = null; sheet.style.transition = '';
        if (dy > 110) closeSheet(); else sheet.style.transform = '';
      };
      for (const h of [handle, $('.sheet-grip', sheet)]) {
        h.addEventListener('touchstart', start, { passive: true });
        h.addEventListener('touchmove', move, { passive: true });
        h.addEventListener('touchend', end);
      }
    }
  }

  function bindControls() {
    $('#ref-btn').onclick = openBooks;
    $('#side-btn').onclick = () => { prefs.side = !prefs.side; applyPrefs(); applySide(); };
    $('#dock-ref-btn').onclick = openBooks;
    $('#tr-btn').onclick = () => openTranslations('primary');
    $('#parallel-btn').onclick = () => openTranslations('parallel');
    $('#settings-btn').onclick = openSettings;
    $('#search-btn').onclick = openSearch;
    $$('.js-prev').forEach((b) => { b.onclick = () => step(-1); });
    $$('.js-next').forEach((b) => { b.onclick = () => step(1); });
    $('#scrim').onclick = () => closeSheet();
    $$('.js-close').forEach((b) => { b.onclick = () => closeSheet(); });
    $('#chapters-back').onclick = () => { $('#books-slider').classList.remove('second'); $('#book-filter').focus({ preventScroll: true }); };
    $('#book-filter').oninput = () => { $('#books-slider').classList.remove('second'); renderBooksList(); };
    let deb;
    $('#search-input').oninput = () => { clearTimeout(deb); deb = setTimeout(runSearch, 280); };
    $('#search-input').onkeydown = (e) => { if (e.key === 'Enter') { clearTimeout(deb); runSearch(); } };

    page.addEventListener('click', onVerseTap);
    $('#act-copy').onclick = () => copy(selectedText(), tr('copied'));
    $('#act-link').onclick = () => copy(linkFor(), tr('linkCopied'));
    $('#act-share').onclick = async () => {
      if (navigator.share) { try { await navigator.share({ title: refLabel(), text: selectedText(), url: linkFor() }); } catch { /* cancelled */ } }
      else copy(`${selectedText()}\n${linkFor()}`, tr('copied'));
    };
    $('#act-close').onclick = () => clearSelection();
    $$('.swatch', actions).forEach((s) => { s.onclick = () => setHighlight(s.dataset.c); });

    addEventListener('scroll', onScroll, { passive: true });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') { if (openSheetEl) closeSheet(); else clearSelection(); return; }
      if (openSheetEl || /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName) || e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.key === 'ArrowLeft') step(state.t.direction === 'rtl' ? 1 : -1);
      else if (e.key === 'ArrowRight') step(state.t.direction === 'rtl' ? -1 : 1);
      else if (e.key === '/') { e.preventDefault(); openSearch(); }
      else if (e.key === 'b') openBooks();
    });
    addEventListener('hashchange', () => {
      if (!state.translations.length) return;
      const [id, book, ch, v] = location.hash.slice(1).split('/').map(decodeURIComponent);
      if (id !== state.t?.id) setTranslation(id, book, Number(ch) || 1, v);
      else if (book && (book !== state.book?.id || Number(ch) !== state.chapter)) {
        const b = allBooks().find((x) => x.id === book);
        if (b) go(b, Number(ch) || 1, v || null);
      }
    });
    bindSwipe();
    bindSheetDrag();
  }

  /* --------------------------------------------------------------- start */

  async function init() {
    Object.assign(prefs, store.get('prefs') || {});
    applyPrefs();
    applySide();
    bindControls();
    skeleton();
    try {
      const [translations, books, apocrypha] = await Promise.all([
        getJSON('translations.json'), getJSON('books.json'), getJSON('apocrypha_books.json'),
      ]);
      state.translations = translations;
      state.books = books;
      state.apocrypha = apocrypha.map((b) => ({ ...b, deutero: true }));
    } catch {
      page.replaceChildren(el('div', { class: 'empty' }, el('strong', { text: I18N.en.loadFail }), I18N.en.loadFailHint));
      return;
    }
    if (prefs.parallel) state.t2 = state.translations.find((t) => t.id === prefs.parallel) || null;
    const fromHash = location.hash.slice(1).split('/').filter(Boolean).map(decodeURIComponent);
    const [id, book, ch, v] = fromHash.length ? fromHash : (store.get('pos') || ['am2000']);
    await setTranslation(id, book, Number(ch) || 1, fromHash.length ? v : null);
  }

  if ('serviceWorker' in navigator && (location.protocol === 'https:' || ['localhost', '127.0.0.1'].includes(location.hostname))) {
    addEventListener('load', () => navigator.serviceWorker.register('sw.js').catch(() => { }));
  }

  init();
})();
