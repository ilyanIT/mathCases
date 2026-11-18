"""
Math Buddies - a math practice website for children, written in Python (Flask).

How to run (on this PC, Flask is installed in the Anaconda Python 3.13):
    1. py -3.13 app.py
    2. Open http://127.0.0.1:5000 in your browser
    3. Press Ctrl + C in the terminal to stop the website
"""
import random

from flask import Flask, redirect, render_template, request, session, url_for
from jinja2 import DictLoader

app = Flask(__name__)
app.secret_key = "math-buddies-secret-change-me"

TOTAL_QUESTIONS = 10

OPERATIONS = {
    "add": {"symbol": "+", "name": "Addition", "color": "#ff7a59", "emoji": "🍎"},
    "sub": {"symbol": "−", "name": "Subtraction", "color": "#2fb4c9", "emoji": "🎈"},
    "mul": {"symbol": "×", "name": "Multiplication", "color": "#8e6cf0", "emoji": "⭐"},
    "div": {"symbol": "÷", "name": "Division", "color": "#2bb673", "emoji": "🍪"},
    "mix": {"symbol": "🎲", "name": "Mix it up", "color": "#f5a700", "emoji": ""},
}

LEVELS = {
    "easy": ("🐣 Easy", "Numbers up to 10"),
    "medium": ("🐥 Medium", "Up to 20 · tables to 10"),
    "hard": ("🦅 Hard", "Up to 100 · tables to 12"),
}

PRAISE = ["Great job! 🎉", "Awesome! 🌟", "You're a math star! ⭐", "Super! 🚀",
          "Perfect! 👏", "Brilliant! 🧠", "Yes! You got it! 🥳"]


# ---------------------------------------------------------------------------
# Math logic
# ---------------------------------------------------------------------------
def make_question(op, level):
    """Create one question. Subtraction is never negative, division is always exact."""
    if op == "mix":
        op = random.choice(["add", "sub", "mul", "div"])

    if op == "add":
        if level == "easy":
            a = random.randint(1, 9)
            b = random.randint(1, 10 - a)
        elif level == "medium":
            a = random.randint(3, 17)
            b = random.randint(1, 20 - a)
        else:
            a = random.randint(10, 99)
            b = random.randint(10, 99)
        answer = a + b

    elif op == "sub":
        if level == "easy":
            a = random.randint(2, 10)
            b = random.randint(1, a)
        elif level == "medium":
            a = random.randint(10, 20)
            b = random.randint(1, a)
        else:
            a = random.randint(20, 100)
            b = random.randint(5, a)
        answer = a - b

    else:
        low, high = {"easy": (1, 5), "medium": (2, 10), "hard": (2, 12)}[level]
        if op == "mul":
            a = random.randint(low, high)
            b = random.randint(1, high)
            answer = a * b
        else:  # division: build it from a multiplication so it divides exactly
            b = random.randint(low, high)
            answer = random.randint(2 if level == "hard" else 1, high)
            a = b * answer

    return {"op": op, "a": a, "b": b, "answer": answer}


def make_quiz(op, level):
    """Create a list of different questions."""
    questions, seen = [], set()
    tries = 0
    while len(questions) < TOTAL_QUESTIONS and tries < 500:
        tries += 1
        q = make_question(op, level)
        key = (q["op"], q["a"], q["b"])
        if key not in seen:
            seen.add(key)
            questions.append(q)
    while len(questions) < TOTAL_QUESTIONS:
        questions.append(make_question(op, level))
    return questions


def objects(count, emoji, css=""):
    return "".join(f'<span class="{css}">{emoji}</span>' for _ in range(count))


def make_hint(q):
    """Return a picture or a tip (as HTML) that helps the child solve the question."""
    a, b, op = q["a"], q["b"], q["op"]
    e = OPERATIONS[op]["emoji"]

    if op == "add":
        if a + b <= 20:
            return (f"<p>Count all the {e}!</p><div class='objs'>{objects(a, e)}"
                    f"<span class='plus'>+</span>{objects(b, e, 'b')}</div>")
        ta, tb = a // 10 * 10, b // 10 * 10
        return (f"<p>Split into tens and ones:</p>"
                f"<p>Tens: {ta} + {tb} = <b>{ta + tb}</b><br>"
                f"Ones: {a % 10} + {b % 10} = <b>{a % 10 + b % 10}</b></p>"
                f"<p>Now add those two together!</p>")

    if op == "sub":
        if a <= 20:
            return (f"<p>Start with {a} {e}. Take away {b}. How many are left?</p>"
                    f"<div class='objs'>{objects(a - b, e)}{objects(b, e, 'gone')}</div>")
        tb, ob = b // 10 * 10, b % 10
        if tb == 0:
            return f"<p>Count back {b} from {a}.</p>"
        return (f"<p>Take away the tens first: {a} − {tb} = <b>{a - tb}</b></p>"
                f"<p>Then take away {ob} more.</p>")

    if op == "mul":
        if a * b <= 40:
            groups = "".join(f"<div class='group'>{objects(b, e)}</div>" for _ in range(a))
            return (f"<p>{a} group{'s' if a > 1 else ''} of {b}. Count them all!</p>"
                    f"<div class='groups'>{groups}</div>")
        return (f"<p>{a} × {b} means adding {b}, {a} times.</p>"
                f"<p>Skip-count by {b}: {b}, {b * 2}, {b * 3}, … ({a} jumps)</p>")

    # division
    if a <= 40:
        return (f"<p>Share {a} {e} equally onto {b} plate{'s' if b > 1 else ''}. "
                f"How many on each plate?</p><div class='objs'>{objects(a, e)}</div>"
                f"<p>Think: {b} × ? = {a}</p>")
    return (f"<p>Think: {b} × ? = {a}</p>"
            f"<p>Skip-count by {b}: {b}, {b * 2}, {b * 3}, … until you reach {a}. "
            f"How many jumps?</p>")


# ---------------------------------------------------------------------------
# Web pages
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    return render_template("home.html", operations=OPERATIONS, levels=LEVELS)


@app.route("/start", methods=["POST"])
def start():
    op = request.form.get("op")
    level = request.form.get("level", "easy")
    if op not in OPERATIONS or level not in LEVELS:
        return render_template("home.html", operations=OPERATIONS, levels=LEVELS,
                               message="Oops! First pick an operation. 👆")
    session.clear()
    session.update(op=op, level=level, questions=make_quiz(op, level), index=0,
                   score=0, streak=0, best=0, tries=0, results=[])
    return redirect(url_for("play"))


@app.route("/play")
def play():
    if "questions" not in session:
        return redirect(url_for("home"))
    index = session["index"]
    if index >= TOTAL_QUESTIONS:
        return redirect(url_for("result"))

    q = session["questions"][index]
    show_hint = session["tries"] > 0 or request.args.get("hint")
    return render_template(
        "play.html",
        q=q,
        op=OPERATIONS[q["op"]],
        number=index + 1,
        total=TOTAL_QUESTIONS,
        progress=index * 100 // TOTAL_QUESTIONS,
        score=session["score"],
        streak=session["streak"],
        feedback=session.pop("feedback", None),
        feedback_kind=session.pop("feedback_kind", ""),
        hint=make_hint(q) if show_hint else None,
    )


@app.route("/answer", methods=["POST"])
def answer():
    if "questions" not in session or session["index"] >= TOTAL_QUESTIONS:
        return redirect(url_for("home"))

    q = session["questions"][session["index"]]
    sym = OPERATIONS[q["op"]]["symbol"]
    text = request.form.get("answer", "").strip()

    if not text.isdigit():
        session["feedback"], session["feedback_kind"] = "Please type a number first. 🔢", "bad"
        return redirect(url_for("play"))

    given = int(text)
    if given == q["answer"]:
        session["score"] += 1
        session["streak"] += 1
        session["best"] = max(session["best"], session["streak"])
        message = random.choice(PRAISE)
        if session["streak"] >= 3:
            message += f" {session['streak']} in a row! 🔥"
        session["feedback"] = f"✔ {message}   {q['a']} {sym} {q['b']} = {q['answer']}"
        session["feedback_kind"] = "ok"
        session["results"].append({**q, "ok": True})
        go_to_next_question()
    else:
        session["tries"] += 1
        if session["tries"] < 2:
            session["feedback"] = "Not quite — try again! 💪 Look at the hint below."
            session["feedback_kind"] = "bad"
        else:
            session["feedback"] = (f"{q['a']} {sym} {q['b']} = {q['answer']}. "
                                   f"You'll get the next one! 🌈")
            session["feedback_kind"] = "bad"
            session["streak"] = 0
            session["results"].append({**q, "ok": False, "given": given})
            go_to_next_question()

    session.modified = True
    if session["index"] >= TOTAL_QUESTIONS:
        return redirect(url_for("result"))
    return redirect(url_for("play"))


def go_to_next_question():
    session["index"] += 1
    session["tries"] = 0


@app.route("/result")
def result():
    if "results" not in session:
        return redirect(url_for("home"))
    score = session["score"]
    stars = 3 if score >= 9 else 2 if score >= 6 else 1 if score >= 3 else 0
    titles = ["Keep practicing! 🌱", "Good try! 👍", "Great work! 🎉", "Math champion! 🏆"]
    return render_template("result.html", score=score, total=TOTAL_QUESTIONS, stars=stars,
                           title=titles[stars], best=session["best"],
                           results=session["results"], operations=OPERATIONS,
                           op=session["op"], level=session["level"])


@app.route("/table")
def times_table():
    row = request.args.get("r", type=int)
    col = request.args.get("c", type=int)
    if not (row and col and 1 <= row <= 10 and 1 <= col <= 10):
        row = col = None
    return render_template("table.html", row=row, col=col)


# ---------------------------------------------------------------------------
# HTML templates (kept here so the whole website is in one Python file)
# ---------------------------------------------------------------------------
TEMPLATES = {
"base.html": """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Math Buddies</title>
<link href="https://fonts.googleapis.com/css2?family=Baloo+2:wght@500;700;800&display=swap" rel="stylesheet">
<style>
  :root{--bg:#fff7e8;--ink:#2d2a4a;--muted:#6b6790;--card:#fff;--ok:#2bb673;--bad:#ef5b5b;--mul:#8e6cf0}
  *{box-sizing:border-box}
  body{margin:0;min-height:100vh;color:var(--ink);font-family:'Baloo 2',system-ui,'Segoe UI',sans-serif;
    background:var(--bg) radial-gradient(#ffe2b8 2px,transparent 2px);background-size:28px 28px}
  a{color:inherit;text-decoration:none}
  button{font-family:inherit;cursor:pointer;border:none;color:inherit}
  .wrap{max-width:760px;margin:0 auto;padding:16px}
  .logo{font-size:clamp(26px,6vw,38px);font-weight:800;margin:0 0 8px;display:inline-block}
  .logo span:nth-child(1){color:#ff7a59}.logo span:nth-child(2){color:#2fb4c9}
  .logo span:nth-child(3){color:#8e6cf0}.logo span:nth-child(4){color:#2bb673}
  .hero{display:flex;align-items:center;gap:14px;margin:8px 0 18px}
  .mascot{font-size:64px;animation:bob 2.4s ease-in-out infinite}
  @keyframes bob{50%{transform:translateY(-6px) rotate(-4deg)}}
  .bubble{background:var(--card);border-radius:20px;padding:12px 16px;font-size:19px;font-weight:600;box-shadow:0 4px 0 #e9dcc4;flex:1}
  h2{font-size:20px;margin:18px 0 10px;color:var(--muted)}
  .ops{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px}
  .op-card{background:var(--c);color:#fff;border-radius:22px;padding:14px 8px;display:flex;flex-direction:column;align-items:center;
    font-size:18px;font-weight:700;box-shadow:0 6px 0 rgba(0,0,0,.18);cursor:pointer;outline:4px solid transparent;transition:transform .1s}
  .op-card .sym{font-size:46px;line-height:1.1;font-weight:800}
  .op-card:has(input:checked){outline-color:var(--ink);transform:scale(1.05)}
  .ops input,.levels input{position:absolute;opacity:0;pointer-events:none}
  .levels{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
  .level{background:var(--card);border-radius:18px;padding:10px 6px;font-size:18px;font-weight:700;text-align:center;
    box-shadow:0 4px 0 #e9dcc4;cursor:pointer;outline:3px solid transparent}
  .level small{display:block;font-size:13px;font-weight:500;color:var(--muted)}
  .level:has(input:checked){outline-color:var(--mul);background:#f1ecff}
  .big-btn{display:block;width:100%;margin:22px 0 10px;padding:16px;font-size:26px;font-weight:800;color:#fff;text-align:center;
    background:linear-gradient(135deg,#ff7a59,#f5a700);border-radius:22px;box-shadow:0 6px 0 #c9631b}
  .big-btn.alt{background:linear-gradient(135deg,#8e6cf0,#2fb4c9);box-shadow:0 6px 0 #5a43a8}
  .big-btn:active{transform:translateY(4px)}
  .link-btn{display:block;text-align:center;font-size:18px;font-weight:700;color:var(--mul);text-decoration:underline}
  .top{display:flex;align-items:center;gap:10px}
  .icon-btn{background:var(--card);border-radius:14px;padding:6px 12px;font-size:22px;box-shadow:0 4px 0 #e9dcc4}
  .progress{flex:1;height:18px;background:#f3e6cf;border-radius:99px;overflow:hidden}
  .progress div{height:100%;background:linear-gradient(90deg,#2bb673,#8fdc5b);border-radius:99px}
  .pill{background:var(--card);border-radius:99px;padding:4px 14px;font-weight:700;font-size:18px;box-shadow:0 3px 0 #e9dcc4;white-space:nowrap}
  .stats{display:flex;gap:10px;justify-content:center;margin:12px 0}
  .feedback{text-align:center;font-size:21px;font-weight:700;border-radius:16px;padding:6px 10px;margin-bottom:12px}
  .feedback.ok{background:#e3f7ec;color:#1d8a55}.feedback.bad{background:#fde8e8;color:#c03b3b}
  .card{background:var(--card);border-radius:28px;padding:20px 14px;text-align:center;box-shadow:0 8px 0 #e9dcc4;border-top:10px solid var(--c)}
  .problem{font-size:clamp(44px,12vw,84px);font-weight:800;line-height:1.1;display:flex;justify-content:center;align-items:center;gap:.25em;flex-wrap:wrap}
  .problem .op{color:var(--c)}
  .answer{width:2.4em;font:inherit;text-align:center;color:var(--mul);background:#f6f1ff;border:4px dashed #cbbdf7;border-radius:18px;padding:0}
  .answer:focus{outline:none;border-style:solid}
  .hint{margin-top:12px;background:#fff9e6;border:3px dashed #f5c55a;border-radius:18px;padding:10px;font-size:18px}
  .hint p{margin:4px 0}
  .objs{font-size:28px;line-height:1.3;display:flex;flex-wrap:wrap;justify-content:center;gap:2px;align-items:center}
  .objs .b{filter:hue-rotate(160deg)}
  .objs .gone{opacity:.25}
  .objs .plus{font-weight:800;margin:0 8px;color:var(--muted)}
  .groups{display:flex;flex-wrap:wrap;justify-content:center;gap:8px}
  .group{border:3px solid #cbbdf7;border-radius:14px;padding:2px 6px;font-size:22px;background:#faf8ff}
  .pad{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:16px}
  .key{background:var(--card);border-radius:18px;padding:10px 0;font-size:30px;font-weight:800;box-shadow:0 5px 0 #e9dcc4}
  .key:active{transform:translateY(4px)}
  .key.check{background:var(--ok);color:#fff;box-shadow:0 5px 0 #1d8a55}
  .key.del{background:#ffe3dc;color:var(--bad)}
  .hint-btn{display:block;width:max-content;margin:14px auto 0;background:#fff3cc;border-radius:16px;padding:8px 18px;font-size:20px;font-weight:700;box-shadow:0 4px 0 #f0d78a}
  .stars{font-size:64px;letter-spacing:6px}.stars .dim{filter:grayscale(1);opacity:.3}
  .review{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin:16px 0}
  .chip{border-radius:12px;padding:4px 10px;font-weight:700;font-size:17px}
  .chip.ok{background:#e3f7ec;color:#1d8a55}.chip.miss{background:#fde8e8;color:#c03b3b}
  .row-btns{display:flex;gap:10px}.row-btns > *{flex:1}
  .table-wrap{overflow-x:auto;background:var(--card);border-radius:22px;padding:10px;box-shadow:0 6px 0 #e9dcc4}
  table{border-collapse:separate;border-spacing:4px;margin:0 auto}
  td,th{width:42px;height:38px;text-align:center;font-weight:700;font-size:17px;border-radius:10px}
  th{background:#efe9ff;color:var(--mul)}
  td{background:#faf6ee}td a{display:block;line-height:38px}
  td.hl{background:#ffe9a8}td.pick{background:var(--mul);color:#fff}
  .learn-out{text-align:center;font-size:clamp(30px,8vw,48px);font-weight:800;margin:10px 0}
  .learn-out small{display:block;font-size:17px;font-weight:600;color:var(--muted)}
  @media (max-width:420px){.levels{grid-template-columns:1fr}td,th{width:28px;height:28px;font-size:13px}td a{line-height:28px}}
</style>
</head>
<body>
<div class="wrap">
  <a href="/" class="logo"><span>Math</span> <span>Bud</span><span>di</span><span>es</span></a>
  {% block content %}{% endblock %}
</div>
</body>
</html>""",

"home.html": """{% extends "base.html" %}{% block content %}
<div class="hero">
  <div class="mascot">🦉</div>
  <div class="bubble">{{ message or "Hi! I'm Ollie the owl. What do you want to practice today?" }}</div>
</div>
<form method="post" action="{{ url_for('start') }}">
  <h2>1. Choose an operation</h2>
  <div class="ops">
    {% for key, op in operations.items() %}
    <label class="op-card" style="--c: {{ op.color }}">
      <input type="radio" name="op" value="{{ key }}">
      <span class="sym">{{ op.symbol }}</span><span>{{ op.name }}</span>
    </label>
    {% endfor %}
  </div>
  <h2>2. Choose a level</h2>
  <div class="levels">
    {% for key, (title, desc) in levels.items() %}
    <label class="level">
      <input type="radio" name="level" value="{{ key }}" {% if key == 'easy' %}checked{% endif %}>
      {{ title }}<small>{{ desc }}</small>
    </label>
    {% endfor %}
  </div>
  <button class="big-btn">Let's go! 🚀</button>
</form>
<a class="link-btn" href="{{ url_for('times_table') }}">📚 Times table helper</a>
{% endblock %}""",

"play.html": """{% extends "base.html" %}{% block content %}
<div class="top">
  <a class="icon-btn" href="/" title="Home">🏠</a>
  <div class="progress"><div style="width: {{ progress }}%"></div></div>
  <div class="pill">{{ number }}/{{ total }}</div>
</div>
<div class="stats">
  <span class="pill">⭐ {{ score }}</span>
  <span class="pill">🔥 {{ streak }}</span>
</div>
{% if feedback %}<div class="feedback {{ feedback_kind }}">{{ feedback }}</div>{% endif %}
<form method="post" action="{{ url_for('answer') }}">
  <div class="card" style="--c: {{ op.color }}">
    <div class="problem">
      <span>{{ q.a }}</span><span class="op">{{ op.symbol }}</span><span>{{ q.b }}</span><span>=</span>
      <input class="answer" id="answer" name="answer" inputmode="numeric" pattern="[0-9]*"
             maxlength="4" autocomplete="off" autofocus placeholder="?">
    </div>
    {% if hint %}<div class="hint">{{ hint | safe }}</div>{% endif %}
  </div>
  <div class="pad">
    {% for k in ['1','2','3','4','5','6','7','8','9'] %}
    <button type="button" class="key" data-key="{{ k }}">{{ k }}</button>
    {% endfor %}
    <button type="button" class="key del" data-key="del">⌫</button>
    <button type="button" class="key" data-key="0">0</button>
    <button type="submit" class="key check">✔</button>
  </div>
</form>
{% if not hint %}<a class="hint-btn" href="?hint=1">💡 Show me a hint</a>{% endif %}
<script>
  // Tiny helper so children can tap the big number buttons instead of typing.
  const box = document.getElementById('answer');
  document.querySelectorAll('[data-key]').forEach(btn => btn.onclick = () => {
    if (btn.dataset.key === 'del') box.value = box.value.slice(0, -1);
    else if (box.value.length < 4) box.value += btn.dataset.key;
    box.focus();
  });
</script>
{% endblock %}""",

"result.html": """{% extends "base.html" %}{% block content %}
<div class="card" style="--c:#f5a700">
  <div class="stars">{% for i in range(3) %}<span class="{{ '' if i < stars else 'dim' }}">⭐</span>{% endfor %}</div>
  <h1 style="margin:6px 0">{{ title }}</h1>
  <p style="font-size:20px;margin:4px 0">You got {{ score }} out of {{ total }} right. Best streak: {{ best }} 🔥</p>
  <div class="review">
    {% for r in results %}
    <span class="chip {{ 'ok' if r.ok else 'miss' }}">
      {{ '✔' if r.ok else '✘' }} {{ r.a }} {{ operations[r.op].symbol }} {{ r.b }} = {{ r.answer }}
      {% if not r.ok %}(you said {{ r.given }}){% endif %}
    </span>
    {% endfor %}
  </div>
  <div class="row-btns">
    <form method="post" action="{{ url_for('start') }}">
      <input type="hidden" name="op" value="{{ op }}">
      <input type="hidden" name="level" value="{{ level }}">
      <button class="big-btn">Play again 🔁</button>
    </form>
    <a class="big-btn alt" href="/">Home 🏠</a>
  </div>
</div>
{% endblock %}""",

"table.html": """{% extends "base.html" %}{% block content %}
<div class="top" style="margin-bottom:12px">
  <a class="icon-btn" href="/" title="Home">🏠</a>
  <div class="bubble">Tap any number to see the multiplication!</div>
</div>
<div class="learn-out">
  {% if row %}{{ row }} × {{ col }} = {{ row * col }}
    <small>{{ row }} group{{ 's' if row > 1 }} of {{ col }} makes {{ row * col }}</small>
  {% else %}? × ? = ?<small>Tap a number in the table</small>{% endif %}
</div>
<div class="table-wrap">
  <table>
    <tr><th>×</th>{% for c in range(1, 11) %}<th>{{ c }}</th>{% endfor %}</tr>
    {% for r in range(1, 11) %}
    <tr><th>{{ r }}</th>
      {% for c in range(1, 11) %}
        {% if row and r == row and c == col %}{% set cls = 'pick' %}
        {% elif row and ((r == row and c <= col) or (c == col and r <= row)) %}{% set cls = 'hl' %}
        {% else %}{% set cls = '' %}{% endif %}
        <td class="{{ cls }}"><a href="?r={{ r }}&c={{ c }}">{{ r * c }}</a></td>
      {% endfor %}
    </tr>
    {% endfor %}
  </table>
</div>
{% endblock %}""",
}

app.jinja_env.loader = DictLoader(TEMPLATES)


if __name__ == "__main__":
    print("Math Buddies is running! Open http://127.0.0.1:5000 in your browser.")
    app.run(debug=True)
