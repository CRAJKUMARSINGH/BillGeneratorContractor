"""
HTML post-processor that adds contenteditable annotations to preview HTML.

Adds `contenteditable="true" data-field-id="..."` to editable <td> cells so
the PreviewPanel can capture inline edits and map them back to bill fields.
Also injects a <script> block that forwards edit events to the parent frame
via postMessage.
"""
from bs4 import BeautifulSoup

# Script injected into every preview page.
# Listens for `input` events on contenteditable elements and posts the change
# to the parent window so PreviewPanel can capture it.
_EDIT_LISTENER_SCRIPT = """
<script>
(function () {
  document.addEventListener('input', function (e) {
    var el = e.target;
    if (el && el.contentEditable === 'true' && el.dataset.fieldId) {
      window.parent.postMessage(
        { type: 'field-edit', fieldId: el.dataset.fieldId, value: el.innerText.trim() },
        '*'
      );
    }
  });
})();
</script>
"""


def _has_nested_table(td) -> bool:
    """Return True if the <td> contains a nested <table>."""
    return bool(td.find('table'))


def _is_label_cell(td) -> bool:
    """
    Return True for cells that are clearly label/header cells and should not
    be made editable (e.g. the first column of a key-value header table that
    holds a row number or a static label).
    """
    text = td.get_text(strip=True)
    # Pure numeric cells (row numbers like "1", "2", ...) are labels.
    if text.isdigit():
        return True
    return False


def _annotate_header_table(table) -> None:
    """
    Annotate a header key-value table.

    Expected structure: rows with 2–3 cells where the second cell is the key
    and the third cell is the editable value.  We mark the *value* cell
    (last <td> in the row) with the key text as data-field-id.
    """
    for row in table.find_all('tr'):
        cells = row.find_all('td', recursive=False)
        if len(cells) < 2:
            continue
        # Skip rows whose first cell is a digit (row-number column)
        first_text = cells[0].get_text(strip=True)
        if not first_text.isdigit() and len(cells) < 3:
            # 2-column table: first cell is key, second is value
            key_cell = cells[0]
            value_cell = cells[1]
        elif len(cells) >= 3 and first_text.isdigit():
            # 3-column table: col0=row-number, col1=key, col2=value
            key_cell = cells[1]
            value_cell = cells[2]
        elif len(cells) >= 2:
            key_cell = cells[0]
            value_cell = cells[1]
        else:
            continue

        if _has_nested_table(value_cell):
            continue

        key_text = key_cell.get_text(strip=True)
        if not key_text:
            continue

        value_cell['contenteditable'] = 'true'
        value_cell['data-field-id'] = key_text


def _annotate_bill_items_table(table) -> None:
    """
    Annotate a bill-items table (multi-column data rows).

    Uses `data-field-id="item-{rowIndex}-{colIndex}"` because item numbers
    are not reliably present in the rendered HTML.
    """
    # Skip the header rows (<thead> or rows that contain <th>)
    data_rows = []
    for row in table.find_all('tr'):
        if row.find('th'):
            continue
        # Skip rows that are clearly summary/total rows (colspan spanning most cols)
        tds = row.find_all('td', recursive=False)
        if not tds:
            continue
        # If the row has a single td with a large colspan it's a note/summary row
        if len(tds) == 1 and tds[0].get('colspan'):
            continue
        data_rows.append(row)

    for row_idx, row in enumerate(data_rows):
        cells = row.find_all('td', recursive=False)
        for col_idx, td in enumerate(cells):
            if _has_nested_table(td):
                continue
            # Skip cells with colspan (summary cells)
            if td.get('colspan'):
                continue
            # Skip the first column if it looks like a serial number / label
            if col_idx == 0 and _is_label_cell(td):
                continue

            td['contenteditable'] = 'true'
            td['data-field-id'] = f'item-{row_idx}-{col_idx}'


def annotate_preview_html(html: str, document_type: str) -> str:
    """
    Post-process rendered HTML to add contenteditable annotations and inject
    the postMessage listener script.

    Args:
        html: Fully rendered HTML string from EnterpriseHTMLRenderer.
        document_type: The document type string (used for future per-type logic).

    Returns:
        Modified HTML string with contenteditable attributes and injected script.
    """
    soup = BeautifulSoup(html, 'html.parser')

    tables = soup.find_all('table')

    for table in tables:
        # Heuristic: a "header" table has rows with 2–3 columns and no <thead>
        # A "bill items" table has a <thead> with multiple columns.
        has_thead = bool(table.find('thead'))
        rows = table.find_all('tr')
        if not rows:
            continue

        # Sample the first data row to count columns
        sample_cells = rows[0].find_all(['td', 'th'])
        col_count = len(sample_cells)

        if has_thead or col_count > 3:
            _annotate_bill_items_table(table)
        else:
            _annotate_header_table(table)

    # Inject the postMessage listener script before </body>
    body = soup.find('body')
    if body:
        script_tag = BeautifulSoup(_EDIT_LISTENER_SCRIPT, 'html.parser')
        body.append(script_tag)

    return str(soup)
