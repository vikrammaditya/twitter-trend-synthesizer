import json
import os
from datetime import datetime
import urllib.parse

def save_run_history(run_data, history_file="history.json"):
    """Save the latest run details to a local JSON database."""
    print("Saving run details to history database...")
    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception as e:
            print(f"Error loading history.json: {e}. Reinitializing.")
            
    # Add new run to the start of the list
    history.insert(0, run_data)
    
    # Keep up to 50 runs to manage file size
    history = history[:50]
    
    try:
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        print(f"Saved. Database has {len(history)} runs.")
        return history
    except Exception as e:
        print(f"Error writing to history.json: {e}")
        return [run_data]

def render_html_dashboard(history_data, output_file="dashboard.html"):
    """Render a premium, self-contained, interactive HTML dashboard."""
    print(f"Rendering premium interactive dashboard to: '{output_file}'...")
    
    # Serialize history database to embed as Javascript
    history_json_str = json.dumps(history_data, ensure_ascii=False).replace("`", "\\`").replace("${", "\\${")
    
    # HTML Content
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>X Trend Synthesizer & Dashboard</title>
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;600;700;800&display=swap" rel="stylesheet">
    <!-- FontAwesome Icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        :root {{
            --bg-dark: #0b0f19;
            --bg-card: rgba(20, 24, 38, 0.7);
            --bg-hover: rgba(30, 37, 58, 0.9);
            --border-color: rgba(255, 255, 255, 0.08);
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --primary: #8b5cf6; /* Violet */
            --primary-glow: rgba(139, 92, 246, 0.4);
            --secondary: #06b6d4; /* Cyan */
            --secondary-glow: rgba(6, 182, 212, 0.4);
            --accent: #ec4899; /* Pink */
            --success: #10b981; /* Emerald */
            --font-outfit: 'Outfit', sans-serif;
            --font-inter: 'Inter', sans-serif;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            background-color: var(--bg-dark);
            color: var(--text-primary);
            font-family: var(--font-inter);
            min-height: 100vh;
            overflow-x: hidden;
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(139, 92, 246, 0.08) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(6, 182, 212, 0.08) 0%, transparent 40%);
        }}

        header {{
            background: rgba(11, 15, 25, 0.8);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border-color);
            position: sticky;
            top: 0;
            z-index: 100;
            padding: 1.25rem 2rem;
        }}

        .header-inner {{
            max-width: 1600px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .logo-section {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .logo-section i {{
            font-size: 2rem;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            filter: drop-shadow(0 0 8px var(--primary-glow));
        }}

        .logo-section h1 {{
            font-family: var(--font-outfit);
            font-size: 1.5rem;
            font-weight: 800;
            letter-spacing: -0.5px;
            background: linear-gradient(to right, #ffffff, #d8b4fe);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .status-badge {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.2);
            padding: 0.35rem 0.85rem;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--success);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .status-dot {{
            width: 8px;
            height: 8px;
            background-color: var(--success);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--success);
            animation: pulse 1.5s infinite;
        }}

        @keyframes pulse {{
            0% {{ transform: scale(0.9); opacity: 0.6; }}
            50% {{ transform: scale(1.1); opacity: 1; }}
            100% {{ transform: scale(0.9); opacity: 0.6; }}
        }}

        .main-container {{
            max-width: 1600px;
            margin: 2.5rem auto;
            padding: 0 3rem;
            display: grid;
            grid-template-columns: 280px 1fr;
            gap: 2.5rem;
        }}

        /* History Sidebar */
        .sidebar {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 1.5rem;
            backdrop-filter: blur(8px);
            height: fit-content;
            max-height: 80vh;
            overflow-y: auto;
        }}

        .sidebar h2 {{
            font-family: var(--font-outfit);
            font-size: 1.15rem;
            font-weight: 700;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--text-primary);
        }}

        .sidebar h2 i {{
            color: var(--primary);
        }}

        .history-list {{
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }}

        .history-item {{
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid transparent;
            padding: 0.85rem 1rem;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        .history-item:hover {{
            background: rgba(255, 255, 255, 0.05);
            border-color: rgba(255, 255, 255, 0.05);
            transform: translateX(4px);
        }}

        .history-item.active {{
            background: rgba(139, 92, 246, 0.1);
            border-color: rgba(139, 92, 246, 0.25);
            box-shadow: inset 0 0 8px rgba(139, 92, 246, 0.05);
        }}

        .history-item h3 {{
            font-family: var(--font-outfit);
            font-size: 0.95rem;
            font-weight: 600;
            margin-bottom: 0.25rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            color: #ffffff;
        }}

        .history-item.active h3 {{
            color: #e9d5ff;
        }}

        .history-item span {{
            font-size: 0.75rem;
            color: var(--text-secondary);
            display: block;
        }}

        /* Content Area */
        .content-area {{
            display: flex;
            flex-direction: column;
            gap: 2rem;
        }}

        .main-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 2rem;
            backdrop-filter: blur(8px);
            position: relative;
            overflow: hidden;
        }}

        .main-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: linear-gradient(to right, var(--primary), var(--secondary), var(--accent));
        }}

        .trend-title-container {{
            margin-bottom: 1.5rem;
        }}

        .trend-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            background: rgba(139, 92, 246, 0.15);
            border: 1px solid rgba(139, 92, 246, 0.25);
            color: #c084fc;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-bottom: 0.75rem;
        }}

        .trend-title {{
            font-family: var(--font-outfit);
            font-size: 2.25rem;
            font-weight: 800;
            line-height: 1.2;
            background: linear-gradient(135deg, #ffffff 0%, #e5e7eb 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .trend-reason {{
            font-size: 0.95rem;
            color: var(--text-secondary);
            margin-top: 0.5rem;
            line-height: 1.5;
            font-style: italic;
        }}

        /* Grid for Tweet and Synthesis */
        .dashboard-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
        }}

        @media (max-width: 1200px) {{
            .dashboard-grid {{
                grid-template-columns: 1fr;
            }}
            .main-container {{
                grid-template-columns: 1fr;
                padding: 0 2rem;
            }}
        }}

        /* Tweet Box */
        .tweet-panel {{
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 16px;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
        }}

        .panel-header {{
            font-family: var(--font-outfit);
            font-size: 1.1rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .panel-header-title {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--secondary);
        }}

        .tweet-content-box {{
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 1.25rem;
            font-size: 1.05rem;
            line-height: 1.5;
            min-height: 120px;
            color: #f3f4f6;
            white-space: pre-wrap;
            position: relative;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
        }}

        .btn-group {{
            display: flex;
            gap: 0.75rem;
        }}

        .btn {{
            flex: 1;
            padding: 0.75rem 1rem;
            border-radius: 10px;
            font-family: var(--font-outfit);
            font-size: 0.95rem;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            border: none;
        }}

        .btn-primary {{
            background: linear-gradient(135deg, var(--primary) 0%, #7c3aed 100%);
            color: #ffffff;
            box-shadow: 0 4px 12px rgba(139, 92, 246, 0.2);
        }}

        .btn-primary:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(139, 92, 246, 0.35);
            filter: brightness(1.1);
        }}

        .btn-secondary {{
            background: rgba(255, 255, 255, 0.05);
            color: #ffffff;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}

        .btn-secondary:hover {{
            background: rgba(255, 255, 255, 0.08);
            transform: translateY(-2px);
        }}

        .btn:active {{
            transform: translateY(0);
        }}

        /* Synthesis panel */
        .synthesis-panel {{
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 16px;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}

        .synthesis-content {{
            font-size: 0.95rem;
            line-height: 1.6;
            color: var(--text-secondary);
            text-align: justify;
        }}
        
        .synthesis-content p {{
            margin-bottom: 0.75rem;
        }}
        
        .synthesis-content p:last-child {{
            margin-bottom: 0;
        }}

        .publisher-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            background: rgba(6, 182, 212, 0.1);
            border: 1px solid rgba(6, 182, 212, 0.2);
            color: #22d3ee;
            padding: 0.3rem 0.75rem;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 600;
            width: fit-content;
        }}

        /* Sources Grid */
        .sources-section {{
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}

        .section-title {{
            font-family: var(--font-outfit);
            font-size: 1.35rem;
            font-weight: 800;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            background: linear-gradient(to right, #ffffff, #9ca3af);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .sources-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1.25rem;
        }}

        .source-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 14px;
            padding: 1.25rem;
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
            cursor: pointer;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            text-decoration: none;
            color: inherit;
        }}

        .source-card:hover {{
            background: var(--bg-hover);
            border-color: rgba(6, 182, 212, 0.3);
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(6, 182, 212, 0.08);
        }}

        .source-card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .source-label {{
            font-family: var(--font-outfit);
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--secondary);
            background: rgba(6, 182, 212, 0.08);
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
        }}

        .source-label.news {{
            color: var(--accent);
            background: rgba(236, 72, 153, 0.08);
        }}

        .source-card h4 {{
            font-family: var(--font-outfit);
            font-size: 0.95rem;
            font-weight: 600;
            line-height: 1.4;
            color: #ffffff;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            height: 2.8rem;
        }}

        .source-card p {{
            font-size: 0.825rem;
            line-height: 1.5;
            color: var(--text-secondary);
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}

        /* Alternative Tweets Panel */
        .alternatives-section {{
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}

        .alt-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.25rem;
        }}

        @media (max-width: 900px) {{
            .alt-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        .alt-card {{
            background: rgba(255, 255, 255, 0.015);
            border: 1px solid var(--border-color);
            border-radius: 14px;
            padding: 1.25rem;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            gap: 1rem;
        }}

        .alt-text {{
            font-size: 0.925rem;
            line-height: 1.5;
            color: var(--text-primary);
            white-space: pre-wrap;
        }}

        .alt-actions {{
            display: flex;
            gap: 0.5rem;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            padding-top: 0.75rem;
        }}

        .btn-mini {{
            flex: 1;
            padding: 0.45rem 0.75rem;
            border-radius: 6px;
            font-family: var(--font-outfit);
            font-size: 0.8rem;
            font-weight: 600;
            cursor: pointer;
            border: none;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.35rem;
            transition: all 0.2s;
        }}

        .btn-mini-primary {{
            background: rgba(139, 92, 246, 0.15);
            color: #d8b4fe;
            border: 1px solid rgba(139, 92, 246, 0.25);
        }}

        .btn-mini-primary:hover {{
            background: rgba(139, 92, 246, 0.25);
            transform: translateY(-1px);
        }}

        .btn-mini-secondary {{
            background: rgba(255, 255, 255, 0.03);
            color: var(--text-secondary);
            border: 1px solid var(--border-color);
        }}

        .btn-mini-secondary:hover {{
            background: rgba(255, 255, 255, 0.07);
            color: #ffffff;
            transform: translateY(-1px);
        }}

        /* Toast Notification */
        .toast {{
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: rgba(16, 185, 129, 0.9);
            backdrop-filter: blur(8px);
            color: white;
            padding: 0.85rem 1.5rem;
            border-radius: 10px;
            font-weight: 600;
            box-shadow: 0 10px 25px rgba(16, 185, 129, 0.3);
            display: flex;
            align-items: center;
            gap: 0.5rem;
            transform: translateY(150%);
            transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            z-index: 1000;
        }}

        .toast.show {{
            transform: translateY(0);
        }}
    </style>
</head>
<body>

    <header>
        <div class="header-inner">
            <div class="logo-section">
                <i class="fa-brands fa-x-twitter"></i>
                <h1>Trend Synthesizer</h1>
            </div>
            <div class="status-badge">
                <span class="status-dot"></span>
                Agent Active
            </div>
        </div>
    </header>

    <div class="main-container">
        
        <!-- Sidebar -->
        <div class="sidebar">
            <h2><i class="fa-solid fa-clock-rotate-left"></i> Run History</h2>
            <div class="history-list" id="historyList">
                <!-- Javascript will populate this -->
            </div>
        </div>

        <!-- Content Area -->
        <div class="content-area">
            
            <!-- Main Details Panel -->
            <div class="main-card">
                <div class="trend-title-container">
                    <div class="trend-badge">
                        <i class="fa-solid fa-arrow-trend-up"></i> Top Trending Topic
                    </div>
                    <h2 class="trend-title" id="trendTitle">Selected Topic Loading...</h2>
                    <p class="trend-reason" id="trendReason">Loading curation details...</p>
                </div>

                <div class="dashboard-grid">
                    
                    <!-- Tweet Panel -->
                    <div class="tweet-panel">
                        <div class="panel-header">
                            <span class="panel-header-title">
                                <i class="fa-brands fa-x-twitter"></i> Drafted Tweet
                            </span>
                            <span style="font-size: 0.8rem; color: var(--text-secondary);" id="tweetCharCount">0 / 280 chars</span>
                        </div>
                        <div class="tweet-content-box" id="tweetContent">
                            Draft loading...
                        </div>
                        <div class="btn-group">
                            <button class="btn btn-primary" id="btnShareX" onclick="shareOnX()">
                                <i class="fa-brands fa-x-twitter"></i> Share to X
                            </button>
                            <button class="btn btn-secondary" id="btnCopyTweet" onclick="copyTweet()">
                                <i class="fa-solid fa-copy"></i> Copy Tweet
                            </button>
                        </div>
                    </div>

                    <!-- Synthesis Panel -->
                    <div class="synthesis-panel">
                        <div class="panel-header" style="color: var(--primary);">
                            <span><i class="fa-solid fa-compass"></i> Fact Synthesis</span>
                            <span class="publisher-badge" id="primarySourceBadge">
                                <i class="fa-solid fa-circle-check"></i> Source: Reuters
                            </span>
                        </div>
                        <div class="synthesis-content" id="synthesisContent">
                            Fact synthesis loading...
                        </div>
                    </div>

                </div>
            </div>

            <!-- Alternative Tweets Panel -->
            <div class="alternatives-section">
                <h3 class="section-title"><i class="fa-solid fa-wand-magic-sparkles"></i> Alternative Tweet Drafts</h3>
                <div class="alt-grid" id="altGrid">
                    <!-- Populated by JS -->
                </div>
            </div>

            <!-- 20+ Sources Panel -->
            <div class="sources-section">
                <h3 class="section-title" id="sourcesTitle"><i class="fa-solid fa-newspaper"></i> 20+ Retreived Sources</h3>
                <div class="sources-grid" id="sourcesGrid">
                    <!-- Populated by JS -->
                </div>
            </div>

        </div>

    </div>

    <!-- Toast Confirmation -->
    <div class="toast" id="copyToast">
        <i class="fa-solid fa-circle-check"></i> Text copied to clipboard!
    </div>

    <script>
        // Embed the history dataset
        const historyDatabase = {history_json_str};
        
        let currentRunIndex = 0;

        function initializeDashboard() {{
            if (historyDatabase.length === 0) {{
                document.getElementById('trendTitle').innerText = "No Runs Yet";
                document.getElementById('trendReason').innerText = "Run the script once to generate trending reports.";
                return;
            }}
            
            renderHistoryList();
            loadRun(0);
        }}

        function renderHistoryList() {{
            const list = document.getElementById('historyList');
            list.innerHTML = '';
            
            historyDatabase.forEach((run, idx) => {{
                const item = document.createElement('div');
                item.className = `history-item ${{idx === currentRunIndex ? 'active' : ''}}`;
                item.onclick = () => loadRun(idx);
                
                const time = new Date(run.timestamp).toLocaleString();
                
                item.innerHTML = `
                    <h3>${{escapeHtml(run.selected_topic)}}</h3>
                    <span>${{time}}</span>
                `;
                list.appendChild(item);
            }});
        }}

        function loadRun(index) {{
            currentRunIndex = index;
            
            // Highlight active sidebar item
            const items = document.querySelectorAll('.history-item');
            items.forEach((item, idx) => {{
                if (idx === index) {{
                    item.classList.add('active');
                }} else {{
                    item.classList.remove('active');
                }}
            }});
            
            const run = historyDatabase[index];
            if (!run) return;
            
            // Load main details
            document.getElementById('trendTitle').innerText = run.selected_topic;
            document.getElementById('trendReason').innerText = run.reason || 'Curated based on X activity.';
            
            // Format and load tweet text
            let tweetText = run.tweet_text;
            if (run.primary_source_url) {{
                tweetText = tweetText.replace('[URL]', run.primary_source_url);
            }}
            document.getElementById('tweetContent').innerText = tweetText;
            document.getElementById('tweetCharCount').innerText = `${{tweetText.length}} / 280 chars`;
            
            // Load synthesis
            let summaryHtml = '';
            if (run.summary) {{
                const paras = run.summary.split('\\n\\n');
                paras.forEach(p => {{
                    if (p.trim()) {{
                        summaryHtml += `<p>${{escapeHtml(p.trim())}}</p>`;
                    }}
                }});
            }} else {{
                summaryHtml = '<p>Fact synthesis details are unavailable for this run.</p>';
            }}
            document.getElementById('synthesisContent').innerHTML = summaryHtml;
            
            // Load primary publisher badge
            const badge = document.getElementById('primarySourceBadge');
            if (run.primary_source_name) {{
                badge.style.display = 'inline-flex';
                badge.innerHTML = `<i class="fa-solid fa-circle-check"></i> Source: ${{escapeHtml(run.primary_source_name)}}`;
                badge.title = run.primary_source_url;
            }} else {{
                badge.style.display = 'none';
            }}
            
            // Load 20+ sources
            const sourcesGrid = document.getElementById('sourcesGrid');
            sourcesGrid.innerHTML = '';
            const sources = run.sources || [];
            
            document.getElementById('sourcesTitle').innerHTML = `<i class="fa-solid fa-newspaper"></i> ${{sources.length}}+ Verified Sources Analyzed`;
            
            sources.forEach(src => {{
                const card = document.createElement('a');
                card.className = 'source-card';
                card.href = src.url;
                card.target = '_blank';
                
                const typeClass = src.type === 'news' ? 'news' : '';
                const typeLabel = src.type === 'news' ? 'News Article' : 'Web Page';
                
                card.innerHTML = `
                    <div class="source-card-header">
                        <span class="source-label ${{typeClass}}">${{typeLabel}}</span>
                        <span style="font-size: 0.75rem; color: var(--text-secondary);">${{escapeHtml(src.source)}}</span>
                    </div>
                    <h4>${{escapeHtml(src.title)}}</h4>
                    <p>${{escapeHtml(src.snippet)}}</p>
                `;
                sourcesGrid.appendChild(card);
            }});
            
            // Load alternatives
            const altGrid = document.getElementById('altGrid');
            altGrid.innerHTML = '';
            const alts = run.alternative_tweets || [];
            
            alts.forEach((alt, altIdx) => {{
                let fullAltText = alt;
                if (run.primary_source_url) {{
                    fullAltText = fullAltText.replace('[URL]', run.primary_source_url);
                }}
                
                const card = document.createElement('div');
                card.className = 'alt-card';
                
                card.innerHTML = `
                    <div class="alt-text">${{escapeHtml(fullAltText)}}</div>
                    <div class="alt-actions">
                        <button class="btn-mini btn-mini-primary" onclick="shareCustomX(\`${{escapeJs(fullAltText)}}\`)">
                            <i class="fa-brands fa-x-twitter"></i> Share
                        </button>
                        <button class="btn-mini btn-mini-secondary" onclick="copyCustomText(this, \`${{escapeJs(fullAltText)}}\`)">
                            <i class="fa-solid fa-copy"></i> Copy
                        </button>
                    </div>
                `;
                altGrid.appendChild(card);
            }});
        }}

        function shareOnX() {{
            const tweet = document.getElementById('tweetContent').innerText;
            const url = `https://twitter.com/intent/tweet?text=${{encodeURIComponent(tweet)}}`;
            window.open(url, '_blank');
        }}

        function shareCustomX(text) {{
            const url = `https://twitter.com/intent/tweet?text=${{encodeURIComponent(text)}}`;
            window.open(url, '_blank');
        }}

        function copyTweet() {{
            const tweet = document.getElementById('tweetContent').innerText;
            navigator.clipboard.writeText(tweet).then(() => {{
                showToast();
            }});
        }}

        function copyCustomText(btn, text) {{
            navigator.clipboard.writeText(text).then(() => {{
                const originalHtml = btn.innerHTML;
                btn.innerHTML = '<i class="fa-solid fa-check"></i> Copied';
                btn.style.color = '#10b981';
                setTimeout(() => {{
                    btn.innerHTML = originalHtml;
                    btn.style.color = '';
                }}, 1500);
            }});
        }}

        function showToast() {{
            const toast = document.getElementById('copyToast');
            toast.classList.add('show');
            setTimeout(() => {{
                toast.classList.remove('show');
            }}, 2000);
        }}

        function escapeHtml(text) {{
            if (!text) return '';
            const map = {{
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#039;'
            }};
            return text.replace(/[&<>"']/g, function(m) {{ return map[m]; }});
        }}

        function escapeJs(text) {{
            if (!text) return '';
            return text.replace(/\\\\/g, '\\\\\\\\')
                       .replace(/'/g, "\\\\'")
                       .replace(/"/g, '\\\\"')
                       .replace(/\\n/g, '\\\\n')
                       .replace(/\\r/g, '\\\\r');
        }}

        // Initialize when page loads
        window.onload = initializeDashboard;
    </script>
</body>
</html>
"""
    
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        print("Premium dashboard rendered successfully.")
    except Exception as e:
        print(f"Error rendering dashboard: {e}")
