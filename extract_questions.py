
import openpyxl
from collections import defaultdict

wb = openpyxl.load_workbook(r'd:\DBMS QB\final dbms.xlsx')
ws = wb['MAIN_SHEET']

questions = []
for i, row in enumerate(ws.iter_rows(values_only=True)):
    if i >= 13:
        if row[0] is not None and row[1] is not None:
            questions.append({
                'sr': row[0],
                'question': row[1],
                'marks': row[2],
                'co': row[3],
                'rbt': row[4],
                'difficulty': row[7],
            })

by_co = defaultdict(list)
for q in questions:
    by_co[q['co']].append(q)

for co in sorted(by_co.keys()):
    print(f'\n=== {co} ({len(by_co[co])} questions) ===')
    for q in by_co[co][:5]:
        marks = q['marks']
        qtext = q['question']
        print(f'  [{marks}M] {qtext}')
