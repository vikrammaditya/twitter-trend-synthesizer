import sys
# Set standard output encoding to UTF-8 to prevent UnicodeEncodeError in Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from config import Config
from model_fallback import invoke_with_fallback, AllModelsExhaustedError

class TweetSynthesis(BaseModel):
    summary: str = Field(description="A highly accurate, comprehensive 2-paragraph summary of the synthesized news, timelines, and facts based on the 20+ sources.")
    primary_source_url: str = Field(description="The URL of the single most reliable, authoritative news source from the list.")
    primary_source_name: str = Field(description="The name of the publisher for the primary source (e.g. Reuters, BBC).")
    tweet_text: str = Field(description="The drafted tweet. MUST be strictly under 280 characters. It should summarize the core news beautifully, engage the reader, include 1-2 relevant hashtags, and cite the primary source.")
    alternative_tweets: list[str] = Field(description="A list of 3 alternative tweet drafts (all strictly under 280 characters) with different styles: e.g. educational, engaging/thought-provoking, and breaking news style.")

def synthesize_news(sources, selected_topic):
    """Synthesize 20+ sources and draft the perfect tweet using LangChain and Gemini."""
    print(f"Synthesizing facts and drafting tweet for: '{selected_topic}'...")
    Config.validate()
    
    parser = JsonOutputParser(pydantic_object=TweetSynthesis)
    
    # Format the sources list for the prompt
    formatted_sources = []
    for idx, s in enumerate(sources):
        formatted_sources.append(
            f"Source #{idx+1} [{s['source']}]:\n"
            f"Title: {s['title']}\n"
            f"URL: {s['url']}\n"
            f"Snippet: {s['snippet']}\n"
        )
    sources_str = "\n".join(formatted_sources)
    
    prompt = PromptTemplate(
        template=(
            "You are an expert news editor, investigative journalist, and digital copywriter.\n"
            "Below is a curated set of 20+ web and news sources regarding the trending topic '{topic}':\n\n"
            "{sources_block}\n\n"
            "Your task is to analyze these sources, perform factual synthesis, and produce a structured "
            "report including a comprehensive summary and multiple highly polished tweet drafts.\n\n"
            "INSTRUCTIONS FOR FACTUAL SYNTHESIS:\n"
            "1. Base your summary strictly on the provided sources. Focus on the core event, the timeline, the players involved, and the consensus facts.\n"
            "2. Identify the single most reliable, authoritative source from the list (e.g., prefer major news agencies like Reuters, BBC, AP, Bloomberg, or top tech publications like TechCrunch/The Verge over generic blogs).\n\n"
            "INSTRUCTIONS FOR TWEET DRAFTS (VERY IMPORTANT):\n"
            "1. Each drafted tweet MUST be strictly under 280 characters. This is a hard limit. E.g. length <= 270 characters to be safe.\n"
            "2. Make the tweet engaging, premium, and clean. Do NOT overload it with hashtags (max 1 or 2 high-quality ones).\n"
            "3. Do NOT use cheesy emoji salads. Use max 1-2 standard, relevant emojis if helpful, or keep it text-only and professional.\n"
            "4. Make sure to cite the primary source in the tweet text (e.g., 'Full story on @Reuters: [URL]' or 'Read more at BBC: [URL]'). The system will automatically inject the actual URL, so you can write a placeholder like '[URL]' at the end, but make sure to account for it in the character count! E.g. budget 20 characters for the '[URL]' string.\n"
            "5. Make the tone matches a premium science, business, or tech publisher like MIT Tech Review, Morning Brew, or Quartz.\n\n"
            "{format_instructions}\n"
        ),
        input_variables=["topic", "sources_block"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    # Build chain factory for model fallback engine
    def chain_factory(llm):
        return prompt | llm | parser
    
    try:
        result = invoke_with_fallback(
            chain_factory=chain_factory,
            temperature=0.3,
            invoke_kwargs={
                "topic": selected_topic,
                "sources_block": sources_str
            }
        )
        
        print("\n--- Fact Synthesis Complete ---")
        print(f"Primary Source: {result['primary_source_name']} ({result['primary_source_url']})")
        print(f"Summary length: {len(result['summary'])} chars.")
        print(f"Drafted Tweet: '{result['tweet_text']}'")
        print(f"Tweet length: {len(result['tweet_text'])} characters.")
        
        # Double check character limit and truncate / edit if necessary
        if len(result['tweet_text']) > 280:
            print("Warning: Generated tweet is too long. Running a quick auto-trim.")
            result['tweet_text'] = result['tweet_text'][:270] + "..."
            
        return result

    except AllModelsExhaustedError:
        print("🚨 FATAL: All Gemini models exhausted during news synthesis. Exiting.")
        sys.exit(1)
        
    except Exception as e:
        print(f"Error during news synthesis: {e}")
        # Standard robust fallback in case of non-rate-limit errors
        fallback_tweet = f"Currently trending: {selected_topic}. Major updates are unfolding. Read the full coverage from trusted news sources. #TrendingNews [URL]"
        return {
            "summary": f"Factual synthesis of {selected_topic} could not be fully compiled due to a processing error. The topic is currently trending globally with active coverage across multiple outlets.",
            "primary_source_url": sources[0]["url"] if sources else "https://news.google.com",
            "primary_source_name": sources[0]["source"] if sources else "Google News",
            "tweet_text": fallback_tweet,
            "alternative_tweets": [fallback_tweet, f"What is happening with {selected_topic}? Here are the latest updates. [URL]", f"Catch the latest synthesis on {selected_topic} now. [URL]"]
        }

if __name__ == "__main__":
    # Test execution
    mock_sources = [
        {
            "title": "SpaceX launches sixth Starship test flight",
            "url": "https://reuters.com/technology/space/spacex-launches-sixth-starship-test-flight-2024-11-19/",
            "snippet": "SpaceX launched its giant Starship rocket into space on Tuesday from Texas, achieving a successful splashdown in the Indian Ocean, although it aborted a booster catch attempt.",
            "source": "Reuters"
        },
        {
            "title": "Starship test flight 6 is a success, mostly",
            "url": "https://techcrunch.com/2024/11/19/spacex-starship-flight-6/",
            "snippet": "SpaceX launched its massive Starship rocket for the sixth time. The upper stage flew beautifully, showing off its thermal protection tiles in daytime, before splashing down in the ocean.",
            "source": "TechCrunch"
        }
    ]
    
    res = synthesize_news(mock_sources, "SpaceX Starship Flight 6")
    print("Synthesized output:", res)
