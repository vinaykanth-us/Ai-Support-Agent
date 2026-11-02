"""AI Support Agent: an LLM agent with tool use over a SQLite database.

Covers: Generative AI/LLM APIs, prompt engineering, AI agents, chatbot,
Python, database + API integration, and basic evaluation/troubleshooting.
"""
import json
import os
import sqlite3
from importlib import import_module

try:
    anthropic = import_module("anthropic")
except ModuleNotFoundError:
    anthropic = None

MODEL = os.getenv("MODEL", "claude-sonnet-5-5")
client = anthropic.Anthropic() if anthropic else None  # reads ANTHROPIC_API_KEY from env

SYSTEM = """You are a customer support agent for an online electronics store.
Use the tools to look up real data; never invent order details.
If you cannot resolve an issue, create a support ticket.
Be concise and friendly."""


# ---------- Database ----------
def init_db() -> sqlite3.Connection:
    db = sqlite3.connect(":memory:", check_same_thread=False)
    db.executescript(
        """
        CREATE TABLE products(id INTEGER PRIMARY KEY, name TEXT, price REAL, stock INT);
        CREATE TABLE orders(id INTEGER PRIMARY KEY, customer TEXT, product_id INT,
                            status TEXT, eta TEXT);
        CREATE TABLE tickets(id INTEGER PRIMARY KEY AUTOINCREMENT, customer TEXT, issue TEXT);
        INSERT INTO products VALUES (1,'Wireless Mouse',24.99,50),(2,'USB-C Hub',39.5,0),
                                    (3,'Mechanical Keyboard',89.0,12);
        INSERT INTO orders VALUES (1001,'alice',1,'shipped','2026-11-05'),
                                  (1002,'bob',2,'backordered','2026-11-20'),
                                  (1003,'alice',3,'processing','2026-11-08');
        """
    )
    return db


DB = init_db()


# ---------- Tools ----------
def lookup_order(order_id: int) -> dict:
    row = DB.execute(
        "SELECT o.id, o.customer, p.name, o.status, o.eta FROM orders o "
        "JOIN products p ON p.id = o.product_id WHERE o.id = ?",
        (order_id,),
    ).fetchone()
    if not row:
        return {"error": f"Order {order_id} not found"}
    return dict(zip(["order_id", "customer", "product", "status", "eta"], row))


def search_products(query: str) -> list:
    rows = DB.execute(
        "SELECT name, price, stock FROM products WHERE name LIKE ?", (f"%{query}%",)
    ).fetchall()
    return [{"name": n, "price": p, "in_stock": s > 0} for n, p, s in rows]


def create_ticket(customer: str, issue: str) -> dict:
    cur = DB.execute("INSERT INTO tickets(customer, issue) VALUES (?,?)", (customer, issue))
    DB.commit()
    return {"ticket_id": cur.lastrowid, "status": "created"}


TOOLS = [
    {
        "name": "lookup_order",
        "description": "Get status and ETA for an order by its numeric ID.",
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "integer"}},
            "required": ["order_id"],
        },
    },
    {
        "name": "search_products",
        "description": "Search products by name; returns price and availability.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "create_ticket",
        "description": "Escalate an unresolved issue to a human support ticket.",
        "input_schema": {
            "type": "object",
            "properties": {"customer": {"type": "string"}, "issue": {"type": "string"}},
            "required": ["customer", "issue"],
        },
    },
]
DISPATCH = {f.__name__: f for f in (lookup_order, search_products, create_ticket)}


# ---------- Agent loop ----------
def run_turn(messages: list) -> str:
    """Call the model, execute any requested tools, repeat until it answers."""
    if client is None:
        raise RuntimeError("The Anthropic SDK is missing. Install it with: pip install anthropic")
    while True:
        resp = client.messages.create(
            model=MODEL, max_tokens=1000, system=SYSTEM, tools=TOOLS, messages=messages
        )
        messages.append({"role": "assistant", "content": resp.content})
        if resp.stop_reason != "tool_use":
            return "".join(b.text for b in resp.content if b.type == "text")

        results = []
        for block in resp.content:
            if block.type == "tool_use":
                try:
                    out = DISPATCH[block.name](**block.input)
                except Exception as e:  # surface errors to the model
                    out = {"error": str(e)}
                print(f"  [tool] {block.name}({block.input}) -> {out}")
                results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(out)}
                )
        messages.append({"role": "user", "content": results})


# ---------- Tiny eval ----------
EVALS = [
    ("Where is order 1001?", "2026-11-05"),
    ("Is the USB-C Hub available?", "stock"),
]


def run_evals():
    for q, expected in EVALS:
        ans = run_turn([{"role": "user", "content": q}])
        ok = expected.lower() in ans.lower()
        print(f"{'PASS' if ok else 'FAIL'}: {q}\n  {ans}\n")


if __name__ == "__main__":
    import sys

    if "--eval" in sys.argv:
        run_evals()
    else:
        history = []
        print("Support agent ready. Type 'quit' to exit.")
        while (user := input("\nYou: ").strip()) != "quit":
            history.append({"role": "user", "content": user})
            print("Agent:", run_turn(history))
