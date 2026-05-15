# 🤖 Deep Research AI Agent

An intelligent multi-agent research system powered by CrewAI and Google Gemini that performs comprehensive web research, analyzes information, and generates professional reports. The system uses coordinated AI agents to deliver thorough, well-structured research outputs.

![Deep Research AI Agent UI](assets/ai-agent-research-ui.png)

## ✨ Features

- **Multi-Agent Architecture**: Three specialized CrewAI agents working together:
  - Research Agent: Conducts deep web searches
  - Summarization Agent: Structures and condenses findings
  - Presentation Agent: Formats professional reports
- **Google Gemini Integration**: Powered by Gemini 2.5 Flash Lite for fast, efficient AI processing
- **Web Research via Firecrawl MCP**: Web search through the official Firecrawl MCP server (`firecrawl_search`)
- **Intelligent Fallback**: If web search fails, Gemini provides direct answers
- **Configurable Research Parameters**: Adjustable breadth and depth for customized research
- **PDF Report Generation**: Automatic creation of downloadable, formatted PDF reports
- **Real-time Progress**: Watch agents work through the research process in real-time
- **Markdown Cleaning**: Clean, readable output with proper formatting
- **Source Citations**: Automatic extraction and listing of research sources

## 🏗️ Architecture

### Multi-Agent System

```
User Query → Research Agent → Summarization Agent → Presentation Agent → PDF Report
                    ↓
         Firecrawl MCP Server (firecrawl_search)
                    ↓
            Google Gemini Fallback
```

**Research Agent**
- Role: Web searcher and data collector
- MCP: [Firecrawl MCP](https://www.firecrawl.dev/mcp) (`firecrawl_search` via hosted endpoint)
- Fallback: Gemini knowledge tool when search is unavailable
- Performs recursive web searches based on breadth and depth parameters

**Summarization Agent**
- Role: Content summarizer
- Condenses research findings into structured, categorized points
- Maintains accuracy while improving readability

**Presentation Agent**
- Role: Report formatter
- Creates polished, professional research reports
- Ensures consistency and proper structure

### LLM: Google Gemini

The system uses Google's **Gemini 2.5 Flash Lite** model for:
- All agent reasoning and decision-making
- Fallback responses when web search is unavailable
- Fast, cost-effective research processing

## 📋 Prerequisites

- Python 3.13+
- pip package manager
- API Keys:
  - **Google API Key** (required) - For Gemini AI
  - **Firecrawl API Key** (required) - For web search

## 🚀 Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd deep-research-ai-agent
```

2. **Create and activate virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

## ⚙️ Configuration

1. **Create `.env` file** in the project root:
```env
GOOGLE_API_KEY=your-google-api-key-here
FIRECRAWL_KEY=your-firecrawl-api-key-here
```

### Getting API Keys

**Google AI (Gemini)**
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and paste it in your `.env` file

**Firecrawl**
1. Visit [Firecrawl](https://www.firecrawl.dev/)
2. Sign up for an account
3. Navigate to API settings
4. Copy your API key and paste it in your `.env` file

## 🎯 Usage

### Starting the Application

```bash
streamlit run main.py
```

The application will open in your default browser at `http://localhost:8501`

### Conducting Research

1. **Enter Research Query**: Type your research topic in the text input field
2. **Configure Parameters**:
   - **Search Breadth** (1-10): Number of different search queries to perform
   - **Search Depth** (1-5): How deep to recurse into each search
3. **Click "Run Deep Research"**
4. **Monitor Progress**: Watch agents work in real-time
5. **Review Results**: 
   - Read the formatted report in the text area
   - Preview the PDF in the embedded viewer
   - Download the PDF report using the download button

### Research Parameters Explained

- **Breadth = 3, Depth = 2** (Default): Balanced research with moderate coverage
- **Breadth = 10, Depth = 5**: Comprehensive, exhaustive research (slower)
- **Breadth = 1, Depth = 1**: Quick, focused research on a specific topic

## 📦 Project Structure

```
deep-research-ai-agent/
├── main.py                      # Streamlit UI application
├── controllers/
│   └── research_controller.py   # Orchestrates research workflow
├── services/
│   └── agents_service.py        # CrewAI agents and Gemini integration
├── models/
│   └── pdf_generator.py         # PDF report generation with ReportLab
├── utils/
│   └── markdown_cleaner.py      # Markdown formatting utilities
├── assets/
│   └── ai-agent-research-ui.png # Application screenshot
├── requirements.txt             # Python dependencies
├── .env                         # API keys (not tracked in git)
├── .gitignore                   # Git ignore rules
├── LICENSE                      # MIT License
└── README.md                    # This file
```

## 🛠️ Technology Stack

| Category | Technology |
|----------|-----------|
| **Multi-Agent Framework** | [CrewAI](https://www.crewai.com/) |
| **Web Interface** | [Streamlit](https://streamlit.io/) |
| **Language Model** | [Google Gemini 2.5 Flash Lite](https://ai.google.dev/) |
| **Web Search** | [Firecrawl MCP Server](https://www.firecrawl.dev/mcp) |
| **MCP Protocol** | [Model Context Protocol](https://modelcontextprotocol.io/) |
| **LLM Integration** | [LangChain](https://langchain.com/) |
| **PDF Generation** | [ReportLab](https://www.reportlab.com/) |

## 🔍 How It Works

### Step-by-Step Process

1. **Initialization**
   - Load API keys from `.env` file
   - Initialize Google Gemini model
   - Create three specialized agents

2. **Research Phase**
   - Research Agent receives user query
   - Performs web searches using the Firecrawl MCP `firecrawl_search` tool
   - If search fails, falls back to Gemini for direct answers
   - Source URLs are extracted from the final report for the PDF

3. **Summarization Phase**
   - Summarization Agent processes raw research data
   - Structures findings into categorized points
   - Maintains context while condensing information

4. **Presentation Phase**
   - Presentation Agent formats the final report
   - Ensures readability and professional structure
   - Adds proper headings and organization

5. **Output Generation**
   - Markdown cleaning removes formatting artifacts
   - PDF report generated with ReportLab
   - Source links compiled and included
   - Report displayed in UI with download option

## 🧪 Example Use Cases

- **Academic Research**: Gather comprehensive information on scholarly topics
- **Market Research**: Analyze trends, competitors, and market conditions
- **Technical Documentation**: Research technologies and best practices
- **News Analysis**: Compile information on current events from multiple sources
- **Due Diligence**: Research companies, products, or services
- **Literature Reviews**: Gather and summarize published research

## 🐛 Troubleshooting

### Common Issues

**"Google Gen AI native provider not available"**
```bash
pip uninstall crewai
pip install "crewai[google-genai]"
```

**"Google API key is not configured"**
- Ensure `GOOGLE_API_KEY` is set in `.env` file
- Check for typos or extra spaces in the key
- Verify the key is active at [Google AI Studio](https://makersuite.google.com/)

**"Firecrawl API key is not configured" or MCP connection errors**
- Verify `FIRECRAWL_KEY` is correct in `.env`
- Check your Firecrawl API quota/credits at [firecrawl.dev](https://www.firecrawl.dev/)
- Ensure `mcp` is installed: `pip install mcp`
- Firecrawl MCP uses **stdio** when `npx` is installed (API key never in URLs)
- Without Node.js: **FirecrawlSearchDirect** REST tool is used instead (no hosted MCP URL in logs)
- Optional: `FIRECRAWL_MCP_TRANSPORT=http` forces hosted MCP (not recommended — key appears in URLs)
- System will use Gemini fallback when search is insufficient

**Model name errors (404 NOT_FOUND)**
- The code uses `gemini-2.5-flash-lite`
- If this model is deprecated, update line 29 in `services/agents_service.py` to current model name
- Check available models at [Google AI documentation](https://ai.google.dev/)

**Streamlit connection errors**
```bash
streamlit run main.py --server.port 8502  # Try different port
```

## 📊 Performance Notes

- **Average Research Time**: 1-3 minutes depending on parameters
- **Breadth Impact**: Each additional breadth point adds ~15-30 seconds
- **Depth Impact**: Each additional depth level adds ~10-20 seconds per query
- **API Costs**: Gemini 2.5 Flash Lite is cost-effective (~$0.075 per 1M tokens)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Copyright (c) 2025 Naveen Shankar**

## 🙏 Acknowledgments

- [CrewAI](https://www.crewai.com/) for the multi-agent framework
- [Google](https://ai.google.dev/) for Gemini AI
- [Firecrawl](https://www.firecrawl.dev/) for web search capabilities
- [Streamlit](https://streamlit.io/) for the elegant UI framework

**⚠️ Important Notes:**
- This application requires active API keys with sufficient quota
- Monitor your API usage on [Google AI Studio](https://makersuite.google.com/) and Firecrawl dashboard
- Research quality depends on Firecrawl API availability and quality
- Generated reports should be reviewed for accuracy

**Made with ❤️ using CrewAI and Google Gemini**
