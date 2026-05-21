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
from trend_analyzer import scrape_trends, select_best_trend
from source_retriever import retrieve_sources
from news_synthesizer import synthesize_news
from dashboard_renderer import save_run_history, render_html_dashboard
from config import Config

def run_agent_cycle(location=None):
    """Execute a single agent cycle: Fetch, Select, Retrieve, Synthesize, and Update Dashboard."""
    print("\n" + "="*60)
    print(f"STARTING AGENT RUN CYCLE AT {datetime.now().isoformat()}")
    print("="*60)
    
    # Use default location if not specified
    if not location:
        location = Config.TRENDS_LOCATION
        
    try:
        # 1. Fetch current trending topics
        trends = scrape_trends(location)
        if not trends:
            raise ValueError("No trends could be retrieved.")
            
        # 2. Select the best news-worthy trend
        selection = select_best_trend(trends)
        selected_topic = selection["selected_topic"]
        search_query = selection["search_query"]
        reason = selection["reason"]
        
        # 3. Retrieve 20+ online sources
        sources = retrieve_sources(search_query, selected_topic=selected_topic, max_results=Config.MAX_SOURCES)
        print(f"Aggregated {len(sources)} unique sources for analysis.")
        
        # 4. Synthesize facts and draft tweet content
        synthesis = synthesize_news(sources, selected_topic)
        
        # 5. Prepare run payload
        # Replace the URL placeholder in the drafted tweets with the actual primary source link
        primary_url = synthesis["primary_source_url"]
        
        tweet_text_final = synthesis["tweet_text"]
        if "[URL]" in tweet_text_final:
            tweet_text_final = tweet_text_final.replace("[URL]", primary_url)
            
        alt_tweets_final = []
        for alt in synthesis.get("alternative_tweets", []):
            if "[URL]" in alt:
                alt = alt.replace("[URL]", primary_url)
            alt_tweets_final.append(alt)
            
        run_data = {
            "timestamp": datetime.now().isoformat(),
            "selected_topic": selected_topic,
            "reason": reason,
            "search_query": search_query,
            "tweet_text": tweet_text_final,
            "tweet_text_raw": synthesis["tweet_text"],
            "primary_source_name": synthesis["primary_source_name"],
            "primary_source_url": primary_url,
            "summary": synthesis["summary"],
            "alternative_tweets": alt_tweets_final,
            "sources": sources
        }
        
        # 6. Save history and render the premium HTML dashboard
        history = save_run_history(run_data)
        render_html_dashboard(history)
        
        print("\n" + "="*60)
        print("AGENT RUN CYCLE COMPLETED SUCCESSFULLY!")
        print(f"Selected Topic: {selected_topic}")
        print(f"Final Tweet text:\n--- \n{tweet_text_final}\n---")
        print(f"Open dashboard.html to view the complete interactive report & post to X!")
        print("="*60 + "\n")
        
        return run_data
        
    except Exception as e:
        print(f"\nCRITICAL ERROR during agent run cycle: {e}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Test a single cycle directly
    run_agent_cycle()
