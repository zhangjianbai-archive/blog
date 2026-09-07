(() => {
  const field = document.querySelector('#search');
  if (!field || !document.querySelector('#results')) return;
  const rows = [...document.querySelectorAll('[data-search]')];
  const readableOnly = document.querySelector('#readable-only');
  const normalize = text => text.normalize('NFKC').toLocaleLowerCase().trim();
  function filter() {
    const words = normalize(field.value).split(/\s+/).filter(Boolean);
    let count = 0;
    let readable = 0;
    for (const row of rows) {
      row.hidden = (readableOnly.checked && row.dataset.readable !== 'true') || !words.every(word => normalize(row.dataset.search).includes(word));
      if (!row.hidden) { count++; if (row.dataset.readable === 'true') readable++; }
    }
    for (const group of document.querySelectorAll('[data-filter-group]')) {
      group.hidden = ![...group.querySelectorAll('[data-search]')].some(row => !row.hidden);
    }
    for (const jump of document.querySelectorAll('.category-jumps a')) {
      jump.hidden = document.querySelector(jump.getAttribute('href')).hidden;
    }
    document.querySelector('#result-count').textContent = `${count} 个标题 · ${readable} 篇可阅读全文`;
    document.querySelector('#empty').hidden = count !== 0;
    document.querySelector('#empty-message').textContent = words.length ? '没有匹配的文章' : '暂无文章';
    document.querySelector('#clear-search').hidden = !words.length && !readableOnly.checked;
    const url = new URL(window.location.href);
    if (field.value.trim()) url.searchParams.set('q', field.value.trim());
    else url.searchParams.delete('q');
    if (readableOnly.checked) url.searchParams.set('readable', '1');
    else url.searchParams.delete('readable');
    window.history.replaceState(null, '', url);
  }
  field.addEventListener('input', filter);
  readableOnly.addEventListener('change', filter);
  document.querySelector('#search-form').addEventListener('submit', event => { event.preventDefault(); filter(); });
  document.querySelector('#clear-search').addEventListener('click', () => { field.value = ''; readableOnly.checked = false; filter(); field.focus(); });
  field.value = new URLSearchParams(window.location.search).get('q') || '';
  readableOnly.checked = new URLSearchParams(window.location.search).get('readable') === '1';
  filter();
})();
