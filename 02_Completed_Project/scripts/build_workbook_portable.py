"""Populate the original JS workbook layout and recalculate it with LibreOffice."""
from datetime import date
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from lxml import etree
from openpyxl.utils import get_column_letter

from office import convert

ROOT = Path(__file__).resolve().parents[1]
NAMESPACE = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
ASSETS = ('HDFCBANK', 'ICICIBANK', 'SBIN', 'BAJFINANCE', 'SHRIRAMFIN', 'MUTHOOTFIN', 'NIFTY50')
CONTRACTS = (('HDFCBANK', 'CE'), ('HDFCBANK', 'PE'), ('BAJFINANCE', 'CE'), ('BAJFINANCE', 'PE'))


def rows_at(first, column, rows):
    return {f'{get_column_letter(column + j)}{first + i}': value
            for i, row in enumerate(rows) for j, value in enumerate(row)}


def date_serial(value):
    return (date.fromisoformat(value) - date(1899, 12, 30)).days


def populate(xml, inputs):
    tree = etree.fromstring(xml)
    cells = {cell.get('r'): cell for cell in tree.iter(NAMESPACE + 'c')}
    for address, value in inputs.items():
        cell = cells[address]
        if cell.find(NAMESPACE + 'f') is not None:
            raise ValueError(f'Workbook input points to formula cell {address}')
        for child in list(cell):
            cell.remove(child)
        if isinstance(value, str):
            cell.set('t', 'inlineStr')
            inline = etree.SubElement(cell, NAMESPACE + 'is')
            etree.SubElement(inline, NAMESPACE + 't').text = value
        else:
            cell.set('t', 'n')
            etree.SubElement(cell, NAMESPACE + 'v').text = str(value)
    for cell in cells.values():
        if cell.find(NAMESPACE + 'f') is not None:
            value = cell.find(NAMESPACE + 'v')
            if value is not None:
                cell.remove(value)
    return etree.tostring(tree, encoding='UTF-8', xml_declaration=True)


def main():
    def load(path):
        return json.loads((ROOT / path).read_text(encoding='utf-8'))

    source = load('artifacts/workbook_equity_inputs.json')
    prices = source['prices']
    cases = load('artifacts/options_results.json')['observations']
    manifest = load('data/source_manifest.json')
    if len(prices) != 1237 or tuple((x['symbol'], x['option_type']) for x in cases) != CONTRACTS:
        raise ValueError('Workbook layout is for the archived 1,237 dates and four original contracts.')
    summary = source['results']['metadata']
    price_inputs = rows_at(6, 1, [[date_serial(p['date']), *[float(p[a]) for a in ASSETS]] for p in prices])
    price_inputs.update(rows_at(6, 10, [[s['symbol'], s['url']] for s in manifest['sources']]))
    case_inputs = rows_at(6, 1, [
        [x['symbol'], x['option_type'], date_serial(x['date']), date_serial(x['expiry']),
         x['spot'], x['strike'], x['market_price'], x['volume_contracts'], x['open_interest_contracts'],
         x['sigma_historical'], x['derived_iv'], x['source_url'], 'Close'] for x in cases])
    value_inputs = {'xl/worksheets/sheet2.xml': {
        'D6': summary['risk_free_rate'], 'D7': summary['trading_days_per_year'],
        'D13': cases[0]['dividend_yield_continuous']},
        'xl/worksheets/sheet6.xml': price_inputs,
        'xl/worksheets/sheet7.xml': case_inputs}
    out = ROOT / 'output'
    out.mkdir(exist_ok=True)
    with TemporaryDirectory(prefix='finance-workbook-') as work:
        source_file = Path(work) / 'Finance_Analysis.xlsx'
        with ZipFile(ROOT / 'templates/Finance_Workbook_Layout.xlsx') as template, ZipFile(source_file, 'w') as active:
            for member in template.infolist():
                content = template.read(member)
                if member.filename.startswith('xl/worksheets/sheet') and member.filename.endswith('.xml'):
                    content = populate(content, value_inputs.get(member.filename, {}))
                active.writestr(member, content)
        # Convert in staging to prevent a failed run from handing off a stale output.
        staged = convert(source_file, Path(work) / 'recalculated', 'xlsx:Calc Office Open XML')
        (out / staged.name).write_bytes(staged.read_bytes())
    print(out / 'Finance_Analysis.xlsx')


if __name__ == '__main__':
    main()
