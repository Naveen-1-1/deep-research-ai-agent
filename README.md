# 🤖 Deep Research AI Agent

An intelligent multi-agent research system powered by **CrewAI**. It performs web research via **Firecrawl MCP**, analyzes results with **Ollama** (default) or **Google Gemini**, and generates professional PDF reports.

![Deep Research AI Agent UI](assets/ai-agent-research-ui.png)

## ✨ Features

- **Multi-Agent Architecture**: Three specialized CrewAI agents:
  - **Research Agent** — web search via `firecrawl_search`
  - **Summarization Agent** — structured bullet summaries
  - **Presentation Agent** — professional report formatting
- **Single LLM provider** — `LLM_PROVIDER=ollama` (default) or `gemini` for all agents ([`utils/llm_config.py`](utils/llm_config.py))
- **Firecrawl MCP search** — one tool, `firecrawl_search`, backed by `npx` + `firecrawl-mcp` ([`services/firecrawl_mcp.py`](services/firecrawl_mcp.py))
- **Configurable research** — adjustable breadth and depth
- **PDF reports** — downloadable ReportLab output with source links
- **Log safety** — API keys redacted in logs and CrewAI console output

## 🏗️ Architecture

```
User Query (Streamlit)
       ↓
Research Agent  ──tool──►  firecrawl_search
       │                        ↓
       │              services/firecrawl_mcp.py
       │                        ↓
       │              npx -y firecrawl-mcp (stdio MCP)
       ↓
Summarization Agent  →  Presentation Agent  →  PDF
       ↑
  Same LLM (Ollama or Gemini via LiteLLM)
```

**Research Agent**

- Only tool: **`firecrawl_search`** (see [`utils/tool_names.py`](utils/tool_names.py))
- MCP is **not** attached via CrewAI `mcps=`; the tool calls Firecrawl directly
- Requires **Node.js / `npx`** and `FIRECRAWL_KEY`
- `max_retry_limit=2` on task errors

**Summarization & Presentation Agents**

- No tools; same `LLM_PROVIDER` as the researcher
- Turn research notes into bullets, then a full report with cited URLs

### LLM provider (one only)

Set **`LLM_PROVIDER`** to **`ollama`** or **`gemini`**. All agents use the same model string from [`utils/llm_config.py`](utils/llm_config.py). There is no mixing (e.g. Ollama for one agent and Gemini for another).

| `LLM_PROVIDER` | Required in `.env` |
|----------------|-------------------|
| **`ollama`** (default) | `OLLAMA_MODEL`, `OLLAMA_BASE_URL`, Ollama running locally |
| **`gemini`** | `GOOGLE_API_KEY`, optional `GEMINI_MODEL` |

Copy [`.env.example`](.env.example) to `.env` and configure **one** provider block.

## 📋 Prerequisites

- **Python 3.11–3.13** (3.13+ supported; 3.11–3.13 recommended for package compatibility)
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
pip install -r requirements.txt
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
```

Install [Ollama](https://ollama.com/) and pull your model: `ollama pull qwen3:8b`

### Gemini (optional)

```env
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your-google-api-key-here
GEMINI_MODEL=gemini-2.5-flash-lite
FIRECRAWL_KEY=your-firecrawl-api-key-here
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
4. Watch agent progress in the terminal
5. Read the report, preview the PDF, and download

**Breadth** = number of search angles. **Depth** = follow-up searches per angle.

## 📦 Project structure

```
deep-research-ai-agent/
├── main.py                      # Streamlit UI
├── controllers/
│   └── research_controller.py   # Crew kickoff, PDF assembly
├── services/
│   ├── agents_service.py        # CrewAI agents, tasks, firecrawl_search tool
│   └── firecrawl_mcp.py         # MCP client (firecrawl_search calls)
├── models/
│   └── pdf_generator.py         # ReportLab PDF
├── utils/
│   ├── llm_config.py            # LLM_PROVIDER → LiteLLM model string
│   ├── tool_names.py            # Canonical tool name constants
│   ├── mcp_config.py            # find_npx() helper (+ legacy Crew MCP config)
│   ├── markdown_cleaner.py        # Report cleanup, URL extraction
│   ├── log_sanitizer.py         # Secret redaction in logs
│   └── crewai_safe_console.py   # Secret redaction in CrewAI UI
├── assets/
│   └── ai-agent-research-ui.png
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

## 🛠️ Technology stack

| Category | Technology |
|----------|------------|
| Multi-agent framework | [CrewAI](https://www.crewai.com/) |
| UI | [Streamlit](https://streamlit.io/) |
| LLM routing | [LiteLLM](https://docs.litellm.ai/) (`ollama/...` or `gemini/...`) |
| Local LLM | [Ollama](https://ollama.com/) |
| Cloud LLM | [Google Gemini](https://ai.google.dev/) |
| Web search | [Firecrawl](https://www.firecrawl.dev/) via [MCP](https://modelcontextprotocol.io/) |
| MCP runtime | `firecrawl-mcp` (stdio through `npx`) |
| PDF | [ReportLab](https://www.reportlab.com/) |

## 🔍 How it works

1. **Load config** — `.env` → [`llm_config.py`](utils/llm_config.py) picks one provider for all agents.
2. **Research** — Research Agent calls **`firecrawl_search`**; [`firecrawl_mcp.py`](services/firecrawl_mcp.py) spawns `npx -y firecrawl-mcp` and runs `firecrawl_search` with your query.
3. **URLs** — Search results are parsed; links are stored for the PDF.
4. **Summarize** — Summarization Agent condenses the research task output.
5. **Report** — Presentation Agent writes Introduction / Key Findings / Conclusion.
6. **Deliver** — Markdown is cleaned; PDF is generated and shown in Streamlit.

## 🐛 Troubleshooting

**`Invalid LLM_PROVIDER` or missing API key**

- Use only `ollama` or `gemini` in `.env`
- For `gemini`, set `GOOGLE_API_KEY`
- For `ollama`, ensure `ollama serve` / Ollama app is running and `OLLAMA_MODEL` matches `ollama list`

**`Firecrawl MCP requires npx` / MCP not available**

- Install [Node.js](https://nodejs.org/) so `npx --version` works
- Or set `NPX_PATH` in `.env` to the full path to `npx`

**`Firecrawl API key is not configured`**

- Set `FIRECRAWL_KEY` in `.env`

**`Google Gen AI native provider not available`** (Gemini mode)

```bash
pip install "crewai[google-genai]"
```

**Gemini `404` / model not found**

- Set `GEMINI_MODEL` to a [supported model id](https://ai.google.dev/gemini-api/docs/models) (default: `gemini-2.5-flash-lite`)

**Ollama: `Invalid response from LLM call - None or empty`**

- Common with smaller or “thinking” models under CrewAI tool-calling
- Try a larger model (e.g. `qwen3:8b`) or `LLM_PROVIDER=gemini` for more reliable agent loops
- `firecrawl_search` may still succeed in logs even if the agent fails to finish notes

**Ollama: research ignores search results**

- Ensure the model follows tool output; try `gemini` or reduce breadth/depth for shorter runs

**Streamlit port in use**

```bash
streamlit run main.py --server.port 8502
```

## 📊 Performance notes

| Provider | Speed | Cost |
|----------|--------|------|
| **Ollama** | Depends on hardware and model size; local, no API token billing | Free (local compute) |
| **Gemini** | Generally faster tool-calling for CrewAI | Billed per Google AI pricing; `gemini-2.5-flash-lite` is cost-effective |

- Typical run: **1–5 minutes** depending on breadth, depth, and model
- Each extra **breadth** adds searches (and MCP startup cost per tool call)
- Firecrawl usage counts against your Firecrawl plan credits

## 📄 License

MIT License — see [LICENSE](LICENSE). **Copyright (c) 2025 Naveen Shankar**

## 🙏 Acknowledgments

- [CrewAI](https://www.crewai.com/)
- [Ollama](https://ollama.com/) and [Google Gemini](https://ai.google.dev/)
- [Firecrawl](https://www.firecrawl.dev/) and the Firecrawl MCP server
- [Streamlit](https://streamlit.io/)

**Important**

- Firecrawl key and Node/`npx` are required for web search
- Choose **one** of Ollama or Gemini via `LLM_PROVIDER`
- Review generated reports for accuracy; LLMs can misread or skip tool output
