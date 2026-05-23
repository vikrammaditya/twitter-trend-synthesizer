import sys
# Set standard output encoding to UTF-8 to prevent UnicodeEncodeError in Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from datetime import datetime
import json
import traceback
from typing import TypedDict, List, Dict, Any, Optional

from langgraph.graph import StateGraph, START, END

from trend_analyzer import scrape_trends, select_best_trend
from source_retriever import retrieve_sources
from news_synthesizer import synthesize_news
from dashboard_renderer import save_run_history, render_html_dashboard
from config import Config


class AgentState(TypedDict):
    location: str
    trends: List[str]
    selected_topic: Optional[str]
    search_query: Optional[str]
    reason: Optional[str]
    sources: List[Dict[str, Any]]
    synthesis: Optional[Dict[str, Any]]
    tweet_text: Optional[str]
    alternative_tweets: List[str]
    primary_source_name: Optional[str]
    primary_source_url: Optional[str]
    summary: Optional[str]
    run_data: Optional[Dict[str, Any]]
    error: Optional[str]


# ---------------------------------------------------------
# GRAPH NODES
# ---------------------------------------------------------

def scrape_trends_node(state: AgentState) -> Dict[str, Any]:
    """Node: Scrape latest trends from trends24."""
    print("\n--- [LangGraph Node] Scraping Latest Trends ---")
    try:
        trends = scrape_trends(state["location"])
        if not trends:
            raise ValueError("No trends could be retrieved.")
        return {"trends": trends}
    except Exception as e:
        return {"error": f"Error during trend scraping: {str(e)}"}


def select_trend_node(state: AgentState) -> Dict[str, Any]:
    """Node: Choose the best factual trend using Gemini."""
    print("\n--- [LangGraph Node] Selecting Best Trend ---")
    if not state.get("trends"):
        return {"error": "Cannot select trend: No trends available in state."}
    try:
        selection = select_best_trend(state["trends"])
        return {
            "selected_topic": selection["selected_topic"],
            "search_query": selection["search_query"],
            "reason": selection["reason"]
        }
    except Exception as e:
        return {"error": f"Error during trend selection: {str(e)}"}


def retrieve_sources_node(state: AgentState) -> Dict[str, Any]:
    """Node: Search DuckDuckGo and aggregate 20+ sources."""
    print("\n--- [LangGraph Node] Retrieving Online Sources ---")
    search_query = state.get("search_query")
    selected_topic = state.get("selected_topic")
    if not search_query or not selected_topic:
        return {"error": "Cannot retrieve sources: Missing search_query or selected_topic in state."}
    try:
        sources = retrieve_sources(search_query, selected_topic=selected_topic, max_results=Config.MAX_SOURCES)
        print(f"Aggregated {len(sources)} unique sources for analysis.")
        return {"sources": sources}
    except Exception as e:
        return {"error": f"Error during source retrieval: {str(e)}"}


def synthesize_news_node(state: AgentState) -> Dict[str, Any]:
    """Node: Perform factual synthesis and draft primary/alternative tweets."""
    print("\n--- [LangGraph Node] Synthesizing News & Drafting Tweets ---")
    sources = state.get("sources")
    selected_topic = state.get("selected_topic")
    if not sources or not selected_topic:
        return {"error": "Cannot synthesize news: Missing sources or selected_topic in state."}
    try:
        synthesis = synthesize_news(sources, selected_topic)
        primary_url = synthesis["primary_source_url"]
        
        # Process tweets to replace [URL] placeholder
        tweet_text_final = synthesis["tweet_text"]
        if "[URL]" in tweet_text_final:
            tweet_text_final = tweet_text_final.replace("[URL]", primary_url)
            
        alt_tweets_final = []
        for alt in synthesis.get("alternative_tweets", []):
            if "[URL]" in alt:
                alt = alt.replace("[URL]", primary_url)
            alt_tweets_final.append(alt)
            
        return {
            "synthesis": synthesis,
            "tweet_text": tweet_text_final,
            "alternative_tweets": alt_tweets_final,
            "primary_source_name": synthesis["primary_source_name"],
            "primary_source_url": primary_url,
            "summary": synthesis["summary"]
        }
    except Exception as e:
        return {"error": f"Error during news synthesis: {str(e)}"}


def render_dashboard_node(state: AgentState) -> Dict[str, Any]:
    """Node: Format output payload, save to JSON database, and render HTML."""
    print("\n--- [LangGraph Node] Saving History & Rendering Dashboard ---")
    try:
        run_data = {
            "timestamp": datetime.now().isoformat(),
            "selected_topic": state["selected_topic"],
            "reason": state["reason"],
            "search_query": state["search_query"],
            "tweet_text": state["tweet_text"],
            "tweet_text_raw": state["synthesis"]["tweet_text"],
            "primary_source_name": state["primary_source_name"],
            "primary_source_url": state["primary_source_url"],
            "summary": state["summary"],
            "alternative_tweets": state["alternative_tweets"],
            "sources": state["sources"]
        }
        history = save_run_history(run_data)
        render_html_dashboard(history)
        return {"run_data": run_data}
    except Exception as e:
        return {"error": f"Error during dashboard rendering: {str(e)}"}


def error_handling_node(state: AgentState) -> Dict[str, Any]:
    """Node: Gracefully intercept and log issues in the pipeline."""
    error_msg = state.get("error", "Unknown error occurred.")
    print(f"\n🚨 [LangGraph Node] Error Intercepted: {error_msg}")
    return {}


# ---------------------------------------------------------
# CONDITIONAL EDGES ROUTING
# ---------------------------------------------------------

def route_after_scrape(state: AgentState) -> str:
    if state.get("error"):
        return "error_handling"
    return "select_trend"


def route_after_select(state: AgentState) -> str:
    if state.get("error"):
        return "error_handling"
    return "retrieve_sources"


def route_after_retrieve(state: AgentState) -> str:
    if state.get("error"):
        return "error_handling"
    return "synthesize_news"


def route_after_synthesize(state: AgentState) -> str:
    if state.get("error"):
        return "error_handling"
    return "render_dashboard"


# ---------------------------------------------------------
# GRAPH COMPILATION
# ---------------------------------------------------------

workflow = StateGraph(AgentState)

# Add all nodes
workflow.add_node("scrape_trends", scrape_trends_node)
workflow.add_node("select_trend", select_trend_node)
workflow.add_node("retrieve_sources", retrieve_sources_node)
workflow.add_node("synthesize_news", synthesize_news_node)
workflow.add_node("render_dashboard", render_dashboard_node)
workflow.add_node("error_handling", error_handling_node)

# Set starting point
workflow.add_edge(START, "scrape_trends")

# Bind conditional transitions
workflow.add_conditional_edges(
    "scrape_trends",
    route_after_scrape,
    {
        "error_handling": "error_handling",
        "select_trend": "select_trend"
    }
)

workflow.add_conditional_edges(
    "select_trend",
    route_after_select,
    {
        "error_handling": "error_handling",
        "retrieve_sources": "retrieve_sources"
    }
)

workflow.add_conditional_edges(
    "retrieve_sources",
    route_after_retrieve,
    {
        "error_handling": "error_handling",
        "synthesize_news": "synthesize_news"
    }
)

workflow.add_conditional_edges(
    "synthesize_news",
    route_after_synthesize,
    {
        "error_handling": "error_handling",
        "render_dashboard": "render_dashboard"
    }
)

# Connect to finish
workflow.add_edge("render_dashboard", END)
workflow.add_edge("error_handling", END)

# Compile ready-to-run graph
compiled_graph = workflow.compile()


# ---------------------------------------------------------
# PUBLIC INTERFACE (Compatible with app.py)
# ---------------------------------------------------------

def run_agent_cycle(location=None):
    """Execute a single agent cycle: Fetch, Select, Retrieve, Synthesize, and Update Dashboard.
    
    This is orchestrator flow fully powered by a stateful LangGraph agentic pipeline.
    """
    print("\n" + "="*60)
    print(f"STARTING LANGGRAPH AGENT RUN CYCLE AT {datetime.now().isoformat()}")
    print("="*60)
    
    # Use default location if not specified
    if not location:
        location = Config.TRENDS_LOCATION
        
    initial_state: AgentState = {
        "location": location,
        "trends": [],
        "selected_topic": None,
        "search_query": None,
        "reason": None,
        "sources": [],
        "synthesis": None,
        "tweet_text": None,
        "alternative_tweets": [],
        "primary_source_name": None,
        "primary_source_url": None,
        "summary": None,
        "run_data": None,
        "error": None
    }
    
    try:
        final_state = compiled_graph.invoke(initial_state)
        
        # Verify if an error was registered during execution
        if final_state.get("error"):
            print(f"\nCRITICAL ERROR during LangGraph agent run cycle: {final_state['error']}")
            return None
            
        run_data = final_state.get("run_data")
        if not run_data:
            print("\nCRITICAL ERROR: No run data generated in final state.")
            return None
            
        print("\n" + "="*60)
        print("LANGGRAPH AGENT RUN CYCLE COMPLETED SUCCESSFULLY!")
        print(f"Selected Topic: {run_data['selected_topic']}")
        print(f"Final Tweet text:\n--- \n{run_data['tweet_text']}\n---")
        print(f"Open dashboard.html to view the complete interactive report & post to X!")
        print("="*60 + "\n")
        
        return run_data
        
    except Exception as e:
        print(f"\nCRITICAL EXCEPTION during LangGraph invocation: {e}")
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Test a single cycle directly
    run_agent_cycle()
