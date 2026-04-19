from flask import Flask, jsonify, render_template, request, Response, stream_with_context
import openpyxl
from collections import defaultdict
import g4f

app = Flask(__name__)

# ── Free AI setup ───────────────────────────────────────────────────────────
# We use g4f (gpt4free) to generate answers without needing any API keys.
# It automatically routes requests to free providers.

# ── Load Excel data once at startup ─────────────────────────────────────────
def load_questions():
    wb = openpyxl.load_workbook(r'd:\DBMS QB\final dbms.xlsx')
    ws = wb['MAIN_SHEET']
    questions = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i >= 13:
            if row[0] is not None and row[1] is not None:
                questions.append({
                    'sr':         row[0],
                    'question':   str(row[1]).strip(),
                    'marks':      row[2],
                    'co':         str(row[3]).strip() if row[3] else '',
                    'rbt':        str(row[4]).strip() if row[4] else '',
                    'difficulty': str(row[7]).strip() if row[7] else '',
                })
    return questions

QUESTIONS = load_questions()

# ── Stats ────────────────────────────────────────────────────────────────────
def get_stats():
    return {
        'total': len(QUESTIONS),
        'two':   sum(1 for q in QUESTIONS if q['marks'] == 2),
        'five':  sum(1 for q in QUESTIONS if q['marks'] == 5),
        'ten':   sum(1 for q in QUESTIONS if q['marks'] == 10),
        'cos':   len(set(q['co'] for q in QUESTIONS if q['co'])),
    }

# ── Routes ───────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats')
def stats():
    return jsonify(get_stats())

@app.route('/api/cos')
def cos():
    unique = sorted(set(q['co'] for q in QUESTIONS if q['co']))
    return jsonify(unique)

@app.route('/api/questions')
def questions():
    marks_filter = request.args.get('marks', 'all')
    co_filter    = request.args.get('co', 'all')
    search       = request.args.get('search', '').lower().strip()
    page         = int(request.args.get('page', 1))
    per_page     = 20

    filtered = QUESTIONS
    if marks_filter != 'all':
        filtered = [q for q in filtered if str(q['marks']) == marks_filter]
    if co_filter != 'all':
        filtered = [q for q in filtered if q['co'] == co_filter]
    if search:
        filtered = [q for q in filtered if search in q['question'].lower()]

    seen, deduped = set(), []
    for q in filtered:
        key = q['question'].lower()
        if key not in seen:
            seen.add(key)
            deduped.append(q)

    total   = len(deduped)
    start   = (page - 1) * per_page
    results = deduped[start:start + per_page]

    return jsonify({
        'total':   total,
        'page':    page,
        'pages':   (total + per_page - 1) // per_page,
        'results': results,
    })

# ── Streaming answer endpoint ────────────────────────────────────────────────
@app.route('/api/answer')
def answer():
    question = request.args.get('q', '').strip()
    marks    = request.args.get('marks', '')

    if not question:
        return jsonify({'error': 'No question provided'}), 400

    # Calibrate depth by marks
    if marks == '2':
        depth = "Give a concise answer in 2-4 sentences suitable for a 2-mark exam question."
    elif marks == '5':
        depth = "Give a clear, structured answer with brief explanation suitable for a 5-mark exam question (around 8-12 lines)."
    else:
        depth = "Give a detailed, well-structured answer with headings/points suitable for a 10-mark exam question."

    prompt = (
        f"You are a DBMS (Database Management Systems) expert and professor. "
        f"{depth}\n\n"
        f"Question: {question}\n\n"
        f"Answer in plain text. Use numbered points or bullet points where helpful. "
        f"Do NOT use markdown symbols like **, ##, or ---. Keep the language academic but clear."
    )

    def generate():
        try:
            response = g4f.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
            for message in response:
                if message:
                    yield str(message).encode('utf-8')
        except Exception as e:
            yield f"\n[Error generating answer: {str(e)}]".encode('utf-8')

    return Response(stream_with_context(generate()), mimetype='text/plain')


# ── Bulk answer endpoint (page) ──────────────────────────────────────────────
@app.route('/api/answer-page', methods=['POST'])
def answer_page():
    data      = request.get_json()
    questions = data.get('questions', [])

    if not questions:
        return jsonify({'error': 'No questions'}), 400

    numbered = "\n".join(f"{i+1}. [{q['marks']}M] {q['question']}"
                         for i, q in enumerate(questions))

    prompt = (
        "You are a DBMS expert professor. Answer each of the following exam questions. "
        "For each, start with 'Q<number>.' then give the answer. "
        "Use plain text only — no **, ##, or markdown symbols. "
        "Separate each answer with a blank line.\n\n"
        f"{numbered}"
    )

    def generate():
        try:
            response = g4f.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
            for message in response:
                if message:
                    yield str(message).encode('utf-8')
        except Exception as e:
            yield f"\n[Error: {str(e)}]".encode('utf-8')

    return Response(stream_with_context(generate()), mimetype='text/plain')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)
