# AI Support Agent

A tool-using LLM agent that answers customer questions by querying a SQLite database and escalating to support tickets.

**Skills shown:** Python, Generative AI / LLM APIs, prompt engineering, AI agents, chatbot, database + API integration, error handling, simple evals.

## Run
```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key
python agent.py          # interactive chat
python agent.py --eval   # run basic checks
```

Try: "Where is order 1001?", "Do you have a USB-C hub?", "My order 1002 is late, help!"

## How it works
1. The model receives the user message plus tool definitions.
2. If it requests a tool, the agent runs the Python function and returns the result.
3. The loop repeats until the model gives a final answer.

## Ideas to extend
- Swap SQLite for Postgres, add a Streamlit/FastAPI front end
- Add retrieval (RAG) over a FAQ document
- Log tool calls and expand the eval set
