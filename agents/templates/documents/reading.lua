-- Keep wide tables usable without forcing the whole page to scroll horizontally.
function Table(table)
  return {
    pandoc.RawBlock('html', '<div class="table-wrap" role="region" aria-label="Scrollable table" tabindex="0">'),
    table,
    pandoc.RawBlock('html', '</div>')
  }
end
