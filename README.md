# 🤖 Deep Research AI Agent

An intelligent **multi-agent** research system powered by **LangChain**. A ReAct **Research Agent** autonomously searches the web via **Firecrawl MCP**, then **Summarization** and **Presentation** agents produce a professional PDF report — using **Ollama** (default) or **Google Gemini**.

![Deep Research AI Agent UI](assets/ai-agent-research-ui.png)

## ✨ Features

- **Three-agent workflow** — Research (autonomous + tools) → Summarizer → Presenter ([`services/langchain_pipeline.py`](services/langchain_pipeline.py))
- **ReAct research agent** — decides when and how to call `firecrawl_search` (no fixed search script)
- **Single search tool** — Firecrawl MCP only ([`services/firecrawl_mcp.py`](services/firecrawl_mcp.py))
- **Single LLM provider** — `LLM_PROVIDER=ollama` (default) or `gemini` ([`utils/llm_config.py`](utils/llm_config.py))
- **Configurable research** — breadth and depth as guidance in the research agent prompt
- **PDF reports** — downloadable ReportLab output with source links
- **Log safety** — API keys redacted in logs; `LOG_LEVEL` for terminal verbosity

## 🏗️ Architecture

```
User Query (Streamlit)
       ↓
Research Agent (ReAct) ──tool──► firecrawl_search → Firecrawl MCP (stdio)
       ↓
Summarization Agent (LCEL chain, no tools)
       ↓
Presentation Agent (LCEL chain, no tools)
       ↓
PDF + Streamlit preview
```

| Agent | Tools | Role |
|-------|--------|------|
| **Research** | `firecrawl_search` | Autonomous web research; chooses queries and follow-ups |
| **Summarization** | None | Bullet summary from research notes |
| **Presentation** | None | Final report (Introduction, Key Findings, Conclusion) |

**Firecrawl MCP** spawns `npx -y firecrawl-mcp` over stdio. Requires **Node.js / `npx`** and `FIRECRAWL_KEY`.

### LLM provider (one only)

Set **`LLM_PROVIDER`** to **`ollama`** or **`gemini`**. All agents use the same model from [`utils/llm_config.py`](utils/llm_config.py).

| `LLM_PROVIDER` | Required in `.env` |
|----------------|-------------------|
| **`ollama`** (default) | `OLLAMA_MODEL`, `OLLAMA_BASE_URL`, Ollama running locally |
| **`gemini`** | `GOOGLE_API_KEY`, optional `GEMINI_MODEL` |

Copy [`.env.example`](.env.example) to `.env` and configure **one** provider block.

## 📋 Prerequisites

- **Python 3.11–3.13**
- **pip** and a virtual environment
- **Firecrawl API key** — always required
- **Node.js / `npx`** — required to run `firecrawl-mcp`
- **Ollama** — when `LLM_PROVIDER=ollama`
- **Google API key** — when `LLM_PROVIDER=gemini`

## 🚀 Installation

1. **Clone the repository**

```bash
git clone <your-repo-url>
cd deep-research-ai-agent
```

2. **Create and activate a virtual environment**

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

3. **Install dependencies**

```bash
python -m pip install -r requirements.txt
```

4. **Configure environment**

```bash
cp .env.example .env
# Edit .env — set LLM_PROVIDER, keys, and model names
```

## ⚙️ Configuration

### Ollama (default)

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen3:8b
OLLAMA_BASE_URL=http://localhost:11434
FIRECRAWL_KEY=your-firecrawl-api-key-here
LOG_LEVEL=INFO
```

Install [Ollama](https://ollama.com/) and pull your model: `ollama pull qwen3:8b`

### Gemini (optional)

```env
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your-google-api-key-here
GEMINI_MODEL=gemini-2.5-flash-lite
FIRECRAWL_KEY=your-firecrawl-api-key-here
LOG_LEVEL=INFO
```

Optional: `NPX_PATH=/full/path/to/npx` if `npx` is not on your `PATH`.

### Getting API keys

**Google AI (Gemini)** — [Google AI Studio](https://aistudio.google.com/apikey)

**Firecrawl** — [firecrawl.dev](https://www.firecrawl.dev/) → API settings

## 🎯 Usage

### Start the app

```bash
streamlit run main.py
```

Opens at `http://localhost:8501`

### Run a research job

1. Enter a **research query**
2. Set **Search Breadth** (1–10, default **3**) and **Search Depth** (1–5, default **2**)
3. Click **Run Deep Research**
4. Watch agent progress in the terminal (`LOG_LEVEL=INFO`)
5. Read the report, preview the PDF, and download

**Breadth** and **depth** guide the Research Agent’s prompt (approximate angles and follow-up levels); the agent chooses concrete searches.

## 📦 Project structure

```
deep-research-ai-agent/
├── main.py                      # Streamlit UI
├── controllers/
│   └── research_controller.py   # Orchestration, PDF assembly
├── services/
│   ├── langchain_pipeline.py    # ReAct research + summarize + present
│   └── firecrawl_mcp.py         # MCP client
├── models/
│   └── pdf_generator.py         # ReportLab PDF
├── utils/
│   ├── llm_config.py            # LLM_PROVIDER → LangChain ChatModel
│   ├── tool_names.py            # firecrawl_search constant
│   ├── url_extract.py           # URL collection from search JSON
│   ├── mcp_config.py            # find_npx()
│   ├── markdown_cleaner.py
│   └── log_sanitizer.py
├── assets/                      # UI screenshot (optional)
├── requirements.txt
├── .env.example
└── README.md
```

## 🛠️ Technology stack

| Category | Technology |
|----------|------------|
| Agents | LangChain `create_agent` (ReAct research agent) |
| Chains | LangChain LCEL (summarize, present) |
| UI | [Streamlit](https://streamlit.io/) |
| Local LLM | [Ollama](https://ollama.com/) via `langchain-ollama` |
| Cloud LLM | [Google Gemini](https://ai.google.dev/) via `langchain-google-genai` |
| Web search | [Firecrawl](https://www.firecrawl.dev/) via MCP |
| PDF | [ReportLab](https://www.reportlab.com/) |

## 🔍 How it works

1. **Load config** — `.env` → [`llm_config.py`](utils/llm_config.py).
2. **Research Agent** — ReAct loop calls `firecrawl_search` until it finishes notes (`recursion_limit` scales with breadth × depth).
3. **Summarization Agent** — condenses research output into bullets.
4. **Presentation Agent** — writes the final markdown report.
5. **Deliver** — PDF + Streamlit preview with collected URLs.

## 🐛 Troubleshooting

**No logs in terminal**

- Set `LOG_LEVEL=INFO` in `.env` and restart Streamlit.
- Logs appear when you run a research job, not only at startup.

**Research Agent empty output / tool-calling failures (Ollama)**

- Use a larger model (`qwen3:8b`) or `LLM_PROVIDER=gemini`.
- Smaller models may fail to call tools reliably.

**`Firecrawl MCP requires npx`**

- Install [Node.js](https://nodejs.org/) or set `NPX_PATH` in `.env`.

**Incomplete report / missing URLs**

- Try Gemini or reduce breadth/depth for shorter runs.

## 📄 License

MIT License — see [LICENSE](LICENSE). **Copyright (c) 2025 Naveen Shankar**

## 🙏 Acknowledgments

- [LangChain](https://www.langchain.com/)
- [Ollama](https://ollama.com/) and [Google Gemini](https://ai.google.dev/)
- [Firecrawl](https://www.firecrawl.dev/)
- [Streamlit](https://streamlit.io/)
