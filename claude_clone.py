#!/usr/bin/env python3
"""
claude_clone.py – tiniest possible “Claude Desktop” clone (CLI edition)
to verify Model-Context-Protocol (MCP) servers while also chatting with
Google Gemini.

• Reads claude_desktop_config.json from the same OS-specific location used
  by Claude Desktop.                                                   [2][3]
• Spawns every MCP server entry, wiring up stdin/stdout pipes.
• Uses Google Generative AI SDK for Gemini Pro-2.5 chat.               [5]
• REPL commands
      plain text  -> sent to Gemini, response streamed back
      /mcp name … -> remaining text written to that MCP server’s stdin
      /exit       -> quit

Only dependency:  google-generativeai  (pip install google-generativeai)
"""

import json, os, platform, subprocess, sys, threading, queue, textwrap
from pathlib import Path

# ------------- Gemini setup ---------------------------------------------------
try:
    import google.generativeai as genai       # pip install google-generativeai
except ImportError:
    sys.exit("Please `pip install google-generativeai` first.")

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    sys.exit("Set GEMINI_API_KEY environment variable before running.")

genai.configure(api_key=API_KEY)
GEMINI_MODEL = genai.GenerativeModel("gemini-pro")   # cheapest, good enough

# ------------- locate claude_desktop_config.json ------------------------------
def default_config_path() -> Path:
    system = platform.system()
    if system == "Darwin":   # macOS
        return Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
    if system == "Windows":
        return Path(os.getenv("APPDATA", "")) / "Claude/claude_desktop_config.json"
    # Linux & anything else
    return Path.home() / ".config/Claude/claude_desktop_config.json"

CFG_PATH = default_config_path()
if not CFG_PATH.exists():
    sys.exit(f"Config file not found: {CFG_PATH}\n"
             "Create one that matches the MCP layout shown in docs [2].")

# ------------- spawn MCP servers ----------------------------------------------
def load_config():
    with CFG_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)

def spawn_server(name:str, spec:dict):
    cmd = [spec["command"], *spec.get("args", [])]
    env = os.environ.copy()
    env.update(spec.get("env", {}))
    # Use text mode to make life simple
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )
    return proc

CONFIG = load_config()
MCP_PROCS = {}      # name -> subprocess.Popen
MCP_QUEUES = {}     # name -> queue.Queue for its stdout lines

def reader_thread(name, proc, q):
    for line in proc.stdout:
        q.put(line.rstrip())
    q.put(f"[{name}] ‑- process terminated")

for name, spec in CONFIG.get("mcpServers", {}).items():
    try:
        proc = spawn_server(name, spec)
        q = queue.Queue()
        threading.Thread(target=reader_thread, args=(name, proc, q), daemon=True).start()
        MCP_PROCS[name]  = proc
        MCP_QUEUES[name] = q
        print(f"✓ started MCP server '{name}' (pid {proc.pid})")
    except Exception as e:
        print(f"⚠ could not start MCP server '{name}': {e}")

# ------------- helper: dump any incoming MCP output asynchronously ------------
def drain_queues():
    for name, q in MCP_QUEUES.items():
        while not q.empty():
            line = q.get_nowait()
            print(f"[{name}] → {line}")

# ------------- REPL -----------------------------------------------------------
INTRO = textwrap.dedent("""
  Simple Claude-clone REPL
    type text          → ask Gemini
    /mcp name JSON ... → send raw line to MCP server 'name'
    /exit              → quit
""")
print(INTRO)

gemini_history = []

def ask_gemini(prompt:str):
    full = gemini_history + [ {"role":"user", "parts":[prompt]} ]
    stream = GEMINI_MODEL.generate_content(full, stream=True)
    print("Gemini:", end=" ", flush=True)
    reply_chunks = []
    for chunk in stream:
        piece = chunk.text
        reply_chunks.append(piece)
        print(piece, end="", flush=True)
    print()    # newline
    # update history
    gemini_history.append({"role":"user",   "parts":[prompt]})
    gemini_history.append({"role":"model", "parts":["".join(reply_chunks)]})

try:
    while True:
        drain_queues()
        line = input("> ").strip()
        if not line:
            continue
        if line == "/exit":
            break
        if line.startswith("/mcp "):
            parts = line.split(maxsplit=2)
            if len(parts) < 3:
                print("Usage: /mcp <name> <payload>")
                continue
            name, payload = parts[1], parts[2]
            proc = MCP_PROCS.get(name)
            if not proc:
                print(f"No such MCP server: {name}")
                continue
            try:
                proc.stdin.write(payload + "\n")
                proc.stdin.flush()
            except Exception as e:
                print(f"Write failed: {e}")
            continue
        # otherwise: talk to Gemini
        ask_gemini(line)
except (KeyboardInterrupt, EOFError):
    pass
finally:
    print("\nShutting down…")
    for proc in MCP_PROCS.values():
        proc.terminate()
