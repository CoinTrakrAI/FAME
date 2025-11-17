# FAME Direct Communication Guide

## Quick Start - Talk Directly to FAME

### Option 1: Desktop GUI (Recommended)
**Run:** `fame_desktop.py` or double-click `fame_desktop.py`

This opens FAME's full desktop interface with:
- Chat window for direct conversation
- Voice input support (if enabled)
- System status monitoring
- Question processing capabilities

### Option 2: Question Processing

FAME can automatically detect and answer question files:

1. **Check for unanswered questions:**
   ```
   Type in chat: "list questions"
   ```

2. **Answer a specific question:**
   ```
   Type in chat: "answer question 22"
   ```

3. **Answer all unanswered questions:**
   ```
   Type in chat: "answer all"
   ```

### Option 3: Direct Python Console

**Run:** `fame_console.py` (from FameLivingSystem folder)

Opens interactive Python console with FAME loaded.

---

## How Question Files Work

1. **Question files** are named `QUESTION_X.md` (e.g., `QUESTION_22.md`)
2. FAME reads the question file automatically when you:
   - Type "answer question X" in chat
   - Type "answer all" to process all unanswered questions
3. **Answer files** are created as `QUESTION_X_ANSWER.md`
4. FAME processes the question and writes its response

---

## Example Usage

### In Desktop Chat:
```
You: list questions
FAME: Found 1 unanswered question(s):
      Question 22: QUESTION_22.md

You: answer question 22
FAME: Question 22 processed. Answer stub created. FAME will now analyze and complete the answer.
```

---

## Current Status

✅ **Working:**
- Desktop GUI with chat interface
- Question file detection
- Answer file generation
- Financial data integration
- Web search integration (for current facts)

⚠️ **Needs Configuration:**
- FAME's AI response generation (connect to OpenAI API or LocalAI)
- Full autonomous answer completion

---

## To Enable Full Autonomous Responses

1. Set `OPENAI_API_KEY` environment variable, OR
2. Start LocalAI Docker container (via desktop GUI)
3. FAME will then generate complete answers automatically

---

## File Locations

- **Questions:** `FAME_Desktop/QUESTION_*.md`
- **Answers:** `FAME_Desktop/QUESTION_*_ANSWER.md`
- **Main Desktop App:** `fame_desktop.py`
- **Question Handler:** `fame_question_handler.py`

