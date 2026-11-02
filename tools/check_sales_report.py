"""Read back the app-generated XLSX and compare it with the supplied report."""
import argparse
from pathlib import Path
from openpyxl import load_workbook

parser = argparse.ArgumentParser()
parser.add_argument('reference', type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
reference = load_workbook(args.reference, data_only=True)
generated = load_workbook(root / 'verification/sales-report/reference-format-export.xlsx', data_only=True)
assert reference.sheetnames == generated.sheetnames
keys = {'Summary': 0, 'Meetings': 2, 'Follow Ups': 4, 'Overdue Follow Ups': 4,
        'Quotations': 4, 'Updates': 4, 'Documents': 4, 'Hope Leads': 2}

def equal(a, b):
    if a is None: a = ''
    if b is None: b = ''
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) < 1e-7
    return str(a) == str(b)

for name, key in keys.items():
    source, actual = reference[name], generated[name]
    header = 5 if name == 'Summary' else 1
    assert source.max_row == actual.max_row and source.max_column == actual.max_column, name
    for a, b in zip(source[header], actual[header]):
        assert equal(a.value, b.value), (name, a.coordinate)
        assert str(a.fill.fgColor.rgb)[-6:] == str(b.fill.fgColor.rgb)[-6:], (name, 'header fill')
        assert a.font.bold == b.font.bold and str(a.font.color.rgb)[-6:] == str(b.font.color.rgb)[-6:], (name, 'header font')
        assert a.alignment.horizontal == b.alignment.horizontal, (name, 'alignment')
    assert source.column_dimensions['A'].width == actual.column_dimensions['A'].width
    rows = {str(row[key]): row for row in actual.iter_rows(min_row=header+1, values_only=True)}
    for row in source.iter_rows(min_row=header+1, values_only=True):
        other = rows[str(row[key])]
        for column, (a, b) in enumerate(zip(row, other)):
            assert equal(a, b), (name, 'column', column+1)
    if name == 'Summary':
        for index in range(1, 5):
            assert source.cell(index, 1).value == actual.cell(index, 1).value

safety = load_workbook(root / 'verification/sales-report/safety.xlsx')
assert safety.active['A2'].data_type == 's' and safety.active['A2'].value == '=1+1'
assert safety.active['A3'].value == '00123'
print('PASS: all eight sheet schemas, detailed cells, summary totals, header styles and text safety.')
