
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
                'question': str(row[1]).strip(),
                'marks': row[2],
                'co': row[3],
                'rbt': row[4],
                'difficulty': row[7],
            })

by_co = defaultdict(list)
for q in questions:
    by_co[q['co']].append(q)

# Write all unique questions per CO to output
with open(r'd:\DBMS QB\all_questions_full.txt', 'w', encoding='utf-8') as f:
    for co in sorted(by_co.keys()):
        f.write(f'\n\n==================== {co} ====================\n')
        seen = set()
        for q in by_co[co]:
            key = q['question'].lower().strip()
            if key not in seen:
                seen.add(key)
                marks = q['marks']
                f.write(f"[{marks}M | {q['rbt']} | {q['difficulty']}] {q['question']}\n")

print("Done! Saved to all_questions_full.txt")
