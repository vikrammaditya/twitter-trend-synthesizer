import argparse
import sys
import os
from datetime import datetime

# Set standard output encoding to UTF-8 to prevent UnicodeEncodeError in Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
from apscheduler.schedulers.blocking import BlockingScheduler
from config import Config
from agent_orchestrator import run_agent_cycle

def setup_dotenv_file():
    """Ensure .env exists. Auto-populate with GEMINI_API_KEY from environment if available."""
    if not os.path.exists(".env"):
        print("Local '.env' file not found. Setting up from template...")
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        
        # If no key in shell process, let's look for system variables or leave empty
        template_path = ".env.template"
        
        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Replace placeholder with current key if we found one
            if gemini_key:
                content = content.replace("your_gemini_api_key_here", gemini_key)
                print("Successfully auto-detected GEMINI_API_KEY and pre-filled your .env file!")
            
            with open(".env", "w", encoding="utf-8") as f:
                f.write(content)
            print("Created '.env' file successfully.")
        else:
            # Fallback direct creation
            with open(".env", "w", encoding="utf-8") as f:
                f.write(f"GEMINI_API_KEY={gemini_key}\nTRENDS_LOCATION=global\nCHECK_INTERVAL_HOURS=2\n")
            print("Created a new basic '.env' file.")
            
        # Re-load environment variables
        from dotenv import load_dotenv
        load_dotenv(override=True)
        Config.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def main():
    parser = argparse.ArgumentParser(
        description="X Trend Synthesizer & Dashboard Agent - Alternative A (Interactive Post Flow)"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--run-now", 
        action="store_true", 
        help="Execute a single immediate research, synthesis, and dashboard generation run."
    )
    group.add_argument(
        "--scheduler", 
        action="store_true", 
        help="Start the background scheduler to run the agent cycle every N hours."
    )
    parser.add_argument(
        "--location", 
        type=str, 
        default=None,
        help="Override the X trend location (e.g. 'united-states', 'india', 'united-kingdom')."
    )
    
    args = parser.parse_args()
    
    # Ensure environment file is prepared
    setup_dotenv_file()
    
    # Validate configurations
    try:
        Config.validate()
    except ValueError as e:
        print(f"\nConfiguration Error: {e}")
        print("Please check your '.env' file and make sure GEMINI_API_KEY is correctly set.")
        sys.exit(1)
        
    location = args.location or Config.TRENDS_LOCATION
    
    if args.run_now:
        print("Executing single run cycle...")
        run_agent_cycle(location=location)
        
    elif args.scheduler:
        interval_hours = Config.CHECK_INTERVAL_HOURS
        print("\n" + "#"*70)
        print(f"STARTING BACKGROUND AGENT DAEMON SCHEDULER")
        print(f"Curation Target Location: '{location}'")
        print(f"Check Interval: Every {interval_hours} Hours")
        print(f"Log updates will stream below. Press Ctrl+C to terminate.")
        print("#"*70 + "\n")
        
        # Run a cycle immediately on startup so the user doesn't wait
        print("Running initial startup cycle...")
        run_agent_cycle(location=location)
        
        # Initialize the blocking scheduler
        scheduler = BlockingScheduler()
        
        # Schedule the job to run every N hours
        scheduler.add_job(
            run_agent_cycle,
            'interval',
            hours=interval_hours,
            args=[location],
            next_run_time=datetime.now() # sets it up, but since we already ran it we could let it schedule normally
        )
        
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            print("\nScheduler stopped by user request. Exiting agent daemon.")
            sys.exit(0)

if __name__ == "__main__":
    main()
