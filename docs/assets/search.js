(() => {
  const field = document.querySelector('#search');
  if (!field) return;
  const rows = [...document.querySelectorAll('[data-search]')];
  const normalize = text => text.normalize('NFKC').toLocaleLowerCase().trim();
  function filter() {
    const words = normalize(field.value).split(/\s+/).filter(Boolean);
    let count = 0;
    for (const row of rows) {
      row.hidden = !words.every(word => normalize(row.dataset.search).includes(word));
      if (!row.hidden) count++;
    }
    document.querySelector('#result-count').textContent = `共 ${count} 个条目 · 含站务示例`;
    document.querySelector('#empty').hidden = count !== 0;
  }
  field.addEventListener('input', filter);
  document.querySelector('#search-form').addEventListener('submit', event => { event.preventDefault(); filter(); });
  document.querySelector('#clear-search').addEventListener('click', () => { field.value = ''; filter(); field.focus(); });
})();
