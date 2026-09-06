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
    document.querySelector('#result-count').textContent = `${count} 篇`;
    document.querySelector('#empty').hidden = count !== 0;
    document.querySelector('#empty-message').textContent = words.length ? '没有匹配的文章' : '暂无文章';
    document.querySelector('#clear-search').hidden = !words.length;
  }
  field.addEventListener('input', filter);
  document.querySelector('#search-form').addEventListener('submit', event => { event.preventDefault(); filter(); });
  document.querySelector('#clear-search').addEventListener('click', () => { field.value = ''; filter(); field.focus(); });
  field.value = new URLSearchParams(window.location.search).get('q') || '';
  filter();
})();
