<div align="center">

# 🦉 Math Buddies

### A colorful math practice website that helps children learn **+ − × ÷**

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)

*Pick an operation, pick a level, and practice with Ollie the owl!* 🍎🎈⭐🍪

</div>

---

## ✨ Features

| | Feature | Description |
|---|---|---|
| ➕ | **4 operations + mix** | Addition, subtraction, multiplication, division, or a random mix 🎲 |
| 🐣 | **3 difficulty levels** | Easy, Medium and Hard, so the game grows with the child |
| 🖼️ | **Picture hints** | Apples to count, balloons to take away, groups of stars, cookies to share |
| 💪 | **Second chance** | A wrong answer shows a hint and lets the child try again |
| ⭐ | **Score & streaks** | Points, a 🔥 streak counter, and 1–3 stars at the end of each round |
| 📋 | **Round review** | See every question, with the right answer for the ones that were missed |
| 📚 | **Times table helper** | Tap any square of the 10 × 10 table to see the multiplication explained |
| 📱 | **Tablet friendly** | Big on-screen number pad, so no keyboard is needed |

## 🎯 Levels

| Level | ➕ Addition | ➖ Subtraction | ✖️ Multiplication | ➗ Division |
|---|---|---|---|---|
| 🐣 **Easy** | sums up to 10 | numbers up to 10 | tables 1–5 | tables 1–5 |
| 🐥 **Medium** | sums up to 20 | numbers up to 20 | tables 2–10 | tables 2–10 |
| 🦅 **Hard** | two-digit numbers | numbers up to 100 | tables 2–12 | tables 2–12 |

> ✅ Subtraction never gives a negative answer, and division always comes out to a whole number.

## 🚀 Getting started

**1. Clone the project**
```bash
git clone https://github.com/ilyanIT/mathCases.git
cd mathCases
```

**2. Install Flask** (only the first time)
```bash
pip install -r requirements.txt
```

**3. Start the website**
```bash
python app.py
```

**4. Open it in your browser** 👉 **http://127.0.0.1:5000**

Press `Ctrl + C` in the terminal to stop the website.

## 🎮 How to play

1. 🦉 Choose an **operation** (for example ➕ Addition)
2. 🐣 Choose a **level**
3. 🚀 Press **Let's go!**
4. 🔢 Type the answer with the number pad and press **✔**
5. 💡 Stuck? Press **Show me a hint**
6. ⭐ After 10 questions, see your stars and review your answers

## 📁 Project structure

```
mathCases/
├── app.py             # The whole website: math logic, pages and design
├── requirements.txt   # Python packages needed (Flask)
└── README.md          # This file
```

Inside `app.py`:

| Part | What it does |
|---|---|
| `make_question()` | Creates a random question for the chosen operation and level |
| `make_hint()` | Builds the picture or tip that helps solve a question |
| `@app.route(...)` | The pages: home, play, answer, result, times table |
| `TEMPLATES` | The HTML and CSS that the browser shows |

## 🛠️ Built with

- **[Python](https://www.python.org/)**: the game logic
- **[Flask](https://flask.palletsprojects.com/)**: the web server and pages
- **HTML + CSS**: the colorful design (no extra libraries)

## 🌱 Ideas for the future

- [ ] 🔊 Sounds for right and wrong answers
- [ ] 🏆 Save best scores for each child
- [ ] 🌍 French and Arabic versions
- [ ] ⏱️ A timed challenge mode
- [ ] 🔢 Fractions and decimals for older children

---

<div align="center">

Made with ❤️ by **[ilyanIT](https://github.com/ilyanIT)**

⭐ If you like this project, give it a star!

</div>
