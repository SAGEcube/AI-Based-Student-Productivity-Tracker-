# 🎯 StudyFlow AI — Student Productivity Tracker

An AI-powered dashboard for students to track tasks, log focus sessions, set goals, and receive personalized productivity suggestions from Gemini AI.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📊 **Dashboard** | Weekly charts for task completion & focus time |
| ✅ **Task Manager** | Add, filter, and complete tasks with priority levels |
| ⏱️ **Focus Timer** | Pomodoro-style timer with session logging |
| 🏆 **Goals Tracker** | Set academic/habit goals with deadlines |
| 🤖 **AI Coach** | Gemini-powered personalized suggestions & Q&A |

---

## 🚀 Setup & Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
streamlit run app.py
```

### 3. Add your Gemini API key
- Visit [aistudio.google.com](https://aistudio.google.com) → Get API Key (free)
- Paste it in the **sidebar** of the app

---

## 📁 Project Structure

```
productivity_tracker/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── data/
    └── student_data.json   # Auto-generated data store
```

---

## 🧠 Productivity Score Formula

| Component | Weight | Based On |
|---|---|---|
| Task Completion | 40 pts | % of today's tasks marked done |
| Focus Time | 40 pts | Minutes logged (target: 120 min) |
| Goal Activity | 20 pts | Number of active goals |

---

## 🛠️ Tech Stack

- **Frontend:** Streamlit + custom CSS
- **Charts:** Plotly
- **AI:** Google Gemini 2.0 Flash API
- **Data:** Local JSON persistence
- **Language:** Python 3.10+

---

## 📌 Resume Description

> **AI-Based Student Productivity Tracker** | Python, Streamlit, Gemini API — 2026  
> Developed an AI-powered dashboard for task tracking, productivity scoring, and personalized improvement suggestions using the Gemini 2.0 Flash API. Built interactive Pomodoro timer, weekly analytics charts, and goal management system. Focused on user engagement through clean UI design and structured data workflows.
