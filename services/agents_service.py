from crewai import Crew, Agent, Task
from crewai.tools import tool
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import requests
import logging

extracted_links = []

# Add dotenv import
from dotenv import load_dotenv
load_dotenv()

# API Keys
FIRECRAWL_KEY = os.getenv("FIRECRAWL_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper function to get LLM model string with Gemini fallback
def get_llm_model():
    """
    Returns the appropriate LLM model string for CrewAI.
    CrewAI uses LiteLLM which supports multiple providers.
    """
    if GOOGLE_API_KEY and GOOGLE_API_KEY.strip():
        logger.info("Using Google Gemini as LLM")
        os.environ["GEMINI_API_KEY"] = GOOGLE_API_KEY
        return "gemini/gemini-2.5-flash-lite"
    else:
        raise ValueError("Google API key is not configured. Please set the API key in .env file.")

# Firecrawl Search function using CrewAI tool decorator
@tool("FirecrawlSearch")
def firecrawl_search(query: str) -> str:
    """Search the web using Firecrawl API and return HTML content or fallback LLM answer."""
    response = requests.get(
        f"https://api.firecrawl.dev/v1/search?query={query}",
        headers={"Authorization": f"Bearer {FIRECRAWL_KEY}"}
    )

    if response.status_code == 200:
        try:
            json_data = response.json()
            results = json_data.get("results", [])
            if results:
                for result in results:
                    url = result.get("url")
                    if url:
                        extracted_links.append(url)
                return response.text
        except Exception:
            pass

    # Use Gemini fallback when search fails
    try:
        if GOOGLE_API_KEY and GOOGLE_API_KEY.strip():
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash-lite",
                google_api_key=GOOGLE_API_KEY,
                temperature=0.3,
                convert_system_message_to_human=True
            )
            fallback_response = llm.invoke([
                HumanMessage(content=f"Please provide a clear explanation about: {query}. Include definition, features, and common use cases.")
            ])
            return fallback_response.content
        else:
            return f"Search failed and no fallback LLM available. Query was: {query}"
    except Exception as e:
        logger.error(f"Fallback LLM also failed: {e}")
        return f"Search failed and LLM fallback unavailable. Query was: {query}"


# Implement Researcher, Summarizer, and presenter Agents
def setup_agents_and_tasks(query, breadth, depth):
    # Get the appropriate LLM model string
    llm_model = get_llm_model()
    logger.info(f"Setting up agents with LLM model: {llm_model}")

    researcher = Agent(
        name="Research Agent",
        role="Web searcher and data collector",
        goal="Conduct deep recursive web research",
        backstory="Expert in online information mining and query generation",
        tools=[firecrawl_search],
        llm=llm_model,
        verbose=True,
        allow_delegation=False
    )

    summarizer = Agent(
        name="Summarization Agent",
        role="Content summarizer",
        goal="Condense detailed findings into concise summaries",
        backstory="Skilled in summarizing complex texts for better understanding",
        tools=[],
        llm=llm_model,
        verbose=True,
        allow_delegation=True
    )

    presenter = Agent(
        name="Presentation Agent",
        role="Report formatter",
        goal="Create readable and well-structured reports",
        backstory="Experienced in generating polished documents for readers",
        tools=[],
        llm=llm_model,
        verbose=True,
        allow_delegation=True
    )

    # Build research description based on breadth and depth
    breadth_instruction = f"Generate {breadth} different search queries or angles to explore this topic thoroughly."
    depth_instruction = f"For each angle, perform {depth} levels of investigation (initial search + {depth-1} follow-up searches on interesting findings)."
    
    task_research = Task(
        description=f"""Perform comprehensive research on: {query}
        
        Research Parameters:
        - {breadth_instruction}
        - {depth_instruction}
        
        For example, if breadth=3 and depth=2:
        - Generate 3 different search angles
        - For each angle, do initial search + 1 follow-up on most relevant finding
        
        Ensure you explore the topic from multiple perspectives and dig deep into each one.""",
        expected_output="Raw web content from multiple search angles, source links, and detailed notes organized by search angle",
        agent=researcher
    )

    task_summarize = Task(
        description="Summarize the research findings into structured points.",
        expected_output="Summarized bullets categorized by topic",
        agent=summarizer
    )

    task_present = Task(
        description="Format all summaries into a professional report.",
        expected_output="A final human-readable report",
        agent=presenter
    )

    # Scale max_steps based on breadth and depth
    # Each breadth*depth combo needs approximately 5-10 steps
    max_steps = max(20, breadth * depth * 7)
    max_time = max(300, breadth * depth * 60)  # ~1 min per breadth*depth unit
    
    crew = Crew(
        agents=[researcher, summarizer, presenter],
        tasks=[task_research, task_summarize, task_present],
        verbose=True,
        max_steps=max_steps,
        max_time=max_time
    )

    return crew, researcher, firecrawl_search