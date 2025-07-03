# Educhain MCP Server – README

***A minimal MCP server that turns Educhain’s AI content generators into plug-and-play tools for Claude Desktop***

## 1. Project overview

This repository wraps the **Educhain** library in a small HTTP-less MCP server built with **FastMCP** so that Claude Desktop can ask for:

* **Multiple-choice questions (MCQs)** generated on demand
* **Lesson plans** in structured JSON
* **Flashcards** converted from the MCQs for spaced-repetition practice

The educhain mcp server talks to Google’s **Gemini 2.5-flash** model through `langchain_google_genai` and needs only one environment variable (`GEMINI_API_KEY`) to run.

## 2. Directory layout

```
.
├── educhain_mcp_server_final.py                # Current production server (recommended)
├── documented_educhain_mcp_server_final.py     # Documentation
├── claude_desktop_config.json                  # Claude desktop config
├── .env.example                                # Example file for .env
├── test_educhain.py                            # Unit-style test script / playground 
├── trials.md                                   # trials
├── Readme.md                                   # Readme
├── res2.json / res2.txt                        # Sample lesson-plan output
└── requirements.txt                            # Generated with `pip freeze`
...
```

Older prototypes (`v3–v6`) are left in the repo for traceability.

## 3. Quick-start (local)

1. Clone and create a virtual env
```bash
git clone https://github.com/SinghArindam/Educhain_MCP.git
cd Educhain_MCP
```

#### MacOS/Linux

```bash
python -m venv .venv && source .venv/bin/activate  
```

#### Windows: 

```bash
python -m venv .venv && .venv\Scripts\activate
```

2. Install Python deps

```bash
pip install -r requirements.txt
```

3. Set your Google Generative AI key

```bash
echo "GEMINI_API_KEY=<your key>" > .env
```

4. Open `claude_desktop_config.json` and add:

```json
{
  "servers": [
    {
      "name": "Educhain MCP Server",
      "executable": "path/to/python/venv",
      "args": ["path/to/educhain_mcp_server_final.py"]
    }
  ]
}
```

Exit and restart Claude Desktop, wait for upto 30s (based on device).

Claude will offer three new tools once it detects the process.

## 5. Usage examples inside Claude

| Request (user) | Tool triggered | Expected reply (short) |
| :-- | :-- | :-- |
| “Generate 16 multiple-choice questions on Python loops” | generate_mcqs | JSON list of 16 MCQs |
| “Provide a lesson plan for teaching algebra” | generate_lesson_plan | Structured lesson plan |
| “Make 7 flashcards about World War II causes” | generate_flashcards | Q-A flashcards |

## 6. Function  Testing (without Claude)

Run the playground script:

```bash
python test_educhain.py
```

It prints MCQs, a full lesson plan and flashcards to the console and dumps the plan to `res2.json` for inspection.

## 7. Development journey (mini-changelog)

| Version | Key idea | Result |
| :-- | :-- | :-- |
| **v1 (main.py)** | Verified FastMCP scaffold, hard-coded dummies | Proved Claude integration |
| **v3** | Switched to real Educhain calls, Gemini 2.0 | First live MCQs \& plans |
| **v4** | Added JSON serialization helpers | Cleaner lesson-plan output |
| **v5** | Typed responses, error handling | Better Claude consent prompts |
| **v6 (current)** | Logging, validation of LLM output, helper `result` wrapper | Stable production build |
| **v6.5 (lab)** | Direct Gemini prompt for lesson plan, custom JSON cleaner | Exploring fallback path |

## 8. Problems faced \& how were they fixed

* **Messy JSON from the LLM** – Gemini occasionally returned Markdown code-blocks and smart quotes.
    - Wrote `clean_and_parse_json()` to strip back-ticks, triple quotes and escape sequences before `json.loads()`.
* **Missing required fields in MCQs** – Some responses lacked `answer`; added per-item validation and logs in `generate_mcqs()` so bad items are skipped.
* **Environment key errors** – Forgetting to export `GEMINI_API_KEY` raised a runtime exception; wrapped client init in a try/except and logged helpful hints.
* **Claude permission prompts repeating** – Supplying `@mcp.tool()` docstrings and returning consistent shapes fixed the warnings.

## 9. Documentation
Inside
```
documented_educhain_mcp_server_final.py
```

## 10. Dependencies (trimmed)

```
Python 3.11
educhain @ git+https://github.com/satvik314/educhain
mcp-server>=0.2.7         # supplies FastMCP
langchain-google-genai>=0.0.10
google-generativeai>=0.3.2
python-dotenv>=1.0
```

Install automatically through `pip install -r requirements.txt`.

## 11. Extending the server

* Add more Educhain engines (e.g., `content_engine.generate_flashcards()` when released).
* Swap Gemini with OpenAI by changing the `LLMConfig(custom_model=ChatOpenAI(...))` line.
* Containerize with **Docker** – the repo includes a sample `Dockerfile` in the `docker/` folder (to be committed in next sprint).


## 12. License \& attribution

Source code © 2025 *Arindam Singh*. MIT License.
Educhain © Satvik314.
Gemini © Google LLC.
