import sys
# Set standard output encoding to UTF-8 to prevent UnicodeEncodeError in Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import requests
from bs4 import BeautifulSoup
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
import json
from config import Config

class TrendSelection(BaseModel):
    selected_topic: str = Field(description="The chosen trending topic text (cleaned, without # if it reads better as a search term).")
    search_query: str = Field(description="The optimized web search query to retrieve news about this topic.")
    reason: str = Field(description="Brief explanation of why this topic was chosen as the most interesting/newsworthy.")

def scrape_trends(location="global"):
    """Scrape the latest hour's trending topics from trends24.in."""
    print(f"Scraping latest trends for location: '{location}'...")
    
    if location == "global" or not location:
        url = "https://trends24.in/"
    else:
        # standardizing location slug (e.g. 'united states' -> 'united-states')
        loc_slug = location.lower().replace(" ", "-").replace("_", "-")
        url = f"https://trends24.in/{loc_slug}/"
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 404 and location != "global":
            print(f"Location '{location}' not found on trends24.in. Falling back to global trends.")
            return scrape_trends("global")
            
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # trends24 displays trends in 'trend-card' div blocks containing <ol> lists.
        # The first trend-card / ol corresponds to the latest hour.
        cards = soup.find_all(class_="trend-card")
        if not cards:
            # Fallback check for any <ol> list
            ol_elements = soup.find_all('ol')
            if ol_elements:
                latest_ol = ol_elements[0]
            else:
                raise ValueError("No trend list elements found in the HTML.")
        else:
            latest_ol = cards[0].find('ol')
            if not latest_ol:
                latest_ol = cards[0]
                
        trends = []
        for li in latest_ol.find_all('li'):
            a_tag = li.find('a')
            trend_text = a_tag.text if a_tag else li.text
            trend_text = trend_text.strip()
            if trend_text:
                trends.append(trend_text)
                
        if not trends:
            raise ValueError("No trend items extracted from the list.")
            
        print(f"Successfully scraped {len(trends)} trending topics.")
        return trends
        
    except Exception as e:
        print(f"Error scraping trends: {e}")
        # Return a fallback list in case of network failures so the system doesn't crash
        return ["OpenAI GPT-4o", "SpaceX Starship Launch", "Global Warming Climate Summit", "Nvidia Stock Split", "NASA Artemis Mission"]

def select_best_trend(trends_list):
    """Use LangChain + Gemini to select the single best topic to write about."""
    print("Selecting the best trending topic using LangChain & Gemini...")
    Config.validate()
    
    from model_fallback import invoke_with_fallback, AllModelsExhaustedError
    
    parser = JsonOutputParser(pydantic_object=TrendSelection)
    
    prompt = PromptTemplate(
        template=(
            "You are a professional, highly analytical editor and trend curator.\n"
            "Below is a list of currently trending topics and hashtags on X (Twitter):\n"
            "{trends}\n\n"
            "Analyze this list and select the single BEST topic to create a highly informative and engaging "
            "news summary/tweet about. \n\n"
            "CRITERIA FOR SELECTION:\n"
            "1. Focus on topics that are educational, major global news, technology, science, astronomy, notable pop culture milestones, or significant business announcements.\n"
            "2. Avoid generic hashtags (e.g. #MondayMotivation, #TBT, #friyay) or daily routine hashtags.\n"
            "3. Avoid spam, adult topics, cryptocurrency scams/shilling, highly repetitive bot-driven topics, or purely cryptic gibberish.\n"
            "4. Prefer topics where there is actual, verifiable news that can be researched.\n"
            "5. Convert the selection to a clean, search-friendly topic name (e.g. convert '#ArtemisIII' to 'NASA Artemis III Mission').\n\n"
            "{format_instructions}\n"
        ),
        input_variables=["trends"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    # Build chain factory for model fallback engine
    def chain_factory(llm):
        return prompt | llm | parser
    
    try:
        trends_str = "\n".join([f"- {t}" for t in trends_list[:40]]) # limit to top 40 for quality
        result = invoke_with_fallback(
            chain_factory=chain_factory,
            temperature=0.2,
            invoke_kwargs={"trends": trends_str}
        )
        
        print(f"Selected Topic: '{result['selected_topic']}'")
        print(f"Optimized Search Query: '{result['search_query']}'")
        print(f"Reason: {result['reason']}")
        return result

    except AllModelsExhaustedError:
        print("🚨 FATAL: All Gemini models exhausted during trend selection. Exiting.")
        sys.exit(1)
        
    except Exception as e:
        print(f"Error selecting best trend: {e}")
        # Robust fallback selection in case of non-rate-limit LLM errors
        # We try to pick a realistic looking topic from the scraped list
        fallback_topic = "SpaceX Starship Launch"
        for t in trends_list:
            if not t.startswith("#") and len(t.split()) > 1 and "motivation" not in t.lower():
                fallback_topic = t
                break
        return {
            "selected_topic": fallback_topic,
            "search_query": fallback_topic + " news updates",
            "reason": "Fallback selection due to system/LLM parsing error."
        }

if __name__ == "__main__":
    # Test execution
    trends = scrape_trends(Config.TRENDS_LOCATION)
    print("Scraped trends:", trends[:10])
    selected = select_best_trend(trends)
    print("Selected:", selected)
