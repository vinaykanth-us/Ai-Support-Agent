# AI Support Agent — Step by Step Procedure
Based on the actual Claude files: agent.py, README.md, requirements.txt

## Before you start
- You need: Python 3, a terminal, and an Anthropic API key (kept in an environment variable, never pasted in chat or in code).

## Procedure

### Step 1 — Create the project folder
Create a folder called `ai-support-agent` and put these 3 files in it:
- `agent.py`
- `README.md`
- `requirements.txt` (contains exactly one line: `anthropic`)

### Step 2 — Install the package
```bash
pip install -r requirements.txt
```
Check: no error at the end of the install.

### Step 3 — Set your API key (do not put it in code)
```bash
export ANTHROPIC_API_KEY=your_key_here
```
On Windows PowerShell, use `$env:ANTHROPIC_API_KEY="your_key_here"` instead.
Check without printing the key:
```bash
python3 -c "import os; print(bool(os.getenv('ANTHROPIC_API_KEY')))"
```
It should print `True`.

### Step 4 — Check the code runs (syntax only, no API call)
```bash
python3 -m py_compile agent.py
```
Check: no error, and it prints nothing. This does NOT prove the agent works live — only that the Python is valid.

### Step 5 — Understand what will happen when you run it
When agent.py starts, `init_db()` creates an in-memory SQLite database with:
- Products: Wireless Mouse $24.99 (50 in stock), USB-C Hub $39.50 (0 in stock), Mechanical Keyboard $89.00 (12 in stock)
- Orders: 1001 alice / Wireless Mouse / shipped / 2026-11-05; 1002 bob / USB-C Hub / backordered / 2026-11-20; 1003 alice / Mechanical Keyboard / processing / 2026-11-08
- Tickets: empty to start

Important: in-memory means everything resets when the program closes, including tickets you create.

### Step 6 — Start the chat
```bash
python agent.py
```
You should see: `Support agent ready. Type 'quit' to exit.`

### Step 7 — Test question 1: order lookup
Type:
```
Where is order 1001?
```
Expected path: model calls `lookup_order` with order_id 1001, gets alice / Wireless Mouse / shipped / 2026-11-05, then answers with that date.
Check: the answer must contain `2026-11-05`. If it invents a different date, the tool was not used — stop and check the system prompt and tool definitions.

### Step 8 — Test question 2: product availability
Type:
```
Do you have a USB-C hub?
```
Expected path: model calls `search_products` with query "USB-C Hub", gets price $39.50 and stock 0, so in_stock is False.
Check: the answer must say it is out of stock / backordered, not available.

### Step 9 — Test question 3: escalation to a ticket
Type:
```
My order 1002 is late, help!
```
Expected path: order 1002 is backordered to 2026-11-20. If it cannot be resolved, the model should call `create_ticket` with a customer name and issue, and return a ticket_id with status "created".
Check: you see a `[tool] create_ticket(...)` log line in the terminal.

### Step 10 — Watch the tool log
While chatting, every tool call prints a line like:
```
[tool] lookup_order({'order_id': 1001}) -> {'order_id': 1001, 'customer': 'alice', 'product': 'Wireless Mouse', 'status': 'shipped', 'eta': '2026-11-05'}
```
If you never see a tool line, the model is answering from memory, not from data — that is the bug to fix first.

### Step 11 — Run the built-in eval
Quit the chat, then run:
```bash
python agent.py --eval
```
It runs 2 fixed questions:
1. "Where is order 1001?" — PASS if the answer contains `2026-11-05`
2. "Is the USB-C Hub available?" — PASS if the answer contains `stock`
Note: eval 2 is a soft check — it passes only if the model's wording happens to include the word "stock" (for example "out of stock"). A stronger check would test the tool result directly.

### Step 12 — Exit cleanly
Type `quit` in the chat. Remember: the database is in-memory, so tickets and any changes are lost on exit. That is expected for this demo.

### Step 13 — If something fails, check in this order
1. API key not set or wrong variable name → re-export it, restart the terminal
2. Tool never called → system prompt must list the tools and say "use tools, never invent order details"
3. Agent invents an order → same fix as above, plus check the tool definitions are passed to the model call
4. Database empty / order not found → check you typed 1001, 1002, or 1003 exactly; other ids correctly return "Order not found"
5. Chat crashes on a tool error → the try/except in run_turn should return the error to the model, not crash; check that block is intact

### Step 14 — Before putting it on GitHub
- Remove any API key from code, screenshots, and terminal history you share
- Confirm the README says: sample data only, in-memory database, how to run, and how to run --eval
- Run the chat once end to end yourself, and run --eval, and note the results
- Only then link it in your application email

## One-line summary
Install → set key → syntax check → chat → test order, product, ticket → watch tool log → run --eval → quit → clean up secrets before sharing.
