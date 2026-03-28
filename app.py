import streamlit as st
import pandas as pd
import numpy as np
from textblob import TextBlob
import urllib.parse
import altair as alt
from src.api.youtube_fetcher import YouTubeCopilotAPI

st.set_page_config(page_title="YouTube Creator OS", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    
    .table-container {
        width: 100%;
        overflow-x: auto;
        border-radius: 8px;
        border: 1px solid #30363d;
        background-color: #0E1117;
        margin-top: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .premium-table {
        width: 100%;
        border-collapse: collapse;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 14px;
        color: #c9d1d9;
    }
    .premium-table th {
        background-color: #161b22;
        color: #8b949e;
        font-weight: 600;
        text-align: left;
        padding: 10px 12px;
        border-bottom: 1px solid #30363d;
        white-space: nowrap;
    }
    .premium-table td {
        padding: 8px 12px;
        border-bottom: 1px solid #21262d;
        vertical-align: middle;
    }
    .premium-table tr:hover { background-color: #1f242c; }
    
    .thumb-img {
        width: 120px;
        height: 68px;
        object-fit: cover;
        object-position: center;
        border-radius: 6px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.4);
        display: block;
    }
    
    .premium-table th:nth-child(2), .premium-table td:nth-child(2) {
        min-width: 250px;
        max-width: 350px;
        font-weight: 500;
        color: #f0f6fc;
        line-height: 1.4;
        white-space: normal;
    }
    
    .watch-btn {
        background-color: #238636;
        color: #ffffff !important;
        padding: 6px 12px;
        border-radius: 6px;
        text-decoration: none;
        font-weight: 600;
        display: inline-block;
        transition: background-color 0.2s;
        white-space: nowrap;
    }
    .watch-btn:hover { background-color: #2ea043; text-decoration: none; }
    
    .launchpad-link {
        text-decoration: none;
        color: #58a6ff;
        font-weight: 500;
        margin-right: 12px;
        font-size: 13px;
    }
    .launchpad-link:hover { text-decoration: underline; color: #79c0ff; }

    /* 🚀 SPREAD TABS EVENLY ACROSS SCREEN */
    div[role="tablist"] {
        display: flex;
        justify-content: space-between;
        width: 100%;
    }
    button[data-baseweb="tab"] {
        flex: 1; 
        display: flex;
        justify-content: center; 
        margin: 0 !important; 
        font-size: 16px !important;
        font-weight: 600 !important;
    }
    </style>
""", unsafe_allow_html=True)

# 🚀 COMPACT, CENTERED, PREMIUM TITLE
st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h1 style="font-size: 2.8rem; font-weight: bold; color: #FFFFFF; margin-bottom: 0;">
            🤖 YouTube Creator Intelligent System
        </h1>
        <p style="font-size: 1.1rem; color: #A0AEC0; margin-top: 5px;">
            End-to-End Analytics ✦ Deep Research ✦ Production Studio
        </p>
    </div>
""", unsafe_allow_html=True)

st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "👋 I am your AI Co-Pilot. You can paste a script draft here for a brutal grade, or ask me to write a scene from scratch!"}]

def load_api(): return YouTubeCopilotAPI()
try: api = load_api()
except Exception as e: st.error(f"⚠️ Initialization Error: {e}"); st.stop()

def calculate_engagement(df):
    df['Views'] = pd.to_numeric(df.get('Views', 0), errors='coerce').fillna(0).astype(int)
    df['Likes'] = pd.to_numeric(df.get('Likes', 0), errors='coerce').fillna(0).astype(int)
    df['Comments'] = pd.to_numeric(df.get('Comments', 0), errors='coerce').fillna(0).astype(int)
    
    rates = []
    for _, row in df.iterrows():
        v = row['Views']
        if v > 0: rates.append(round(min(((row['Likes'] + row['Comments']) / v) * 100, 100.0), 2))
        else: rates.append(0.0)
            
    df['Views_Raw'] = df['Views'].copy() 
    df['Eng_Raw'] = rates
    df['Engagement Rate'] = [f"{r:.2f}%" for r in rates]
    df['Views'] = df['Views'].apply(lambda x: f"{x:,}")
    df['Likes'] = df['Likes'].apply(lambda x: f"{x:,}")
    df['Comments'] = df['Comments'].apply(lambda x: f"{x:,}")
    return df

def display_dataframe(df):
    if df.empty:
        st.warning("No data found.")
        return
    display_df = df.copy()
    if 'Video ID' in display_df.columns:
        display_df['Watch Link'] = display_df['Video ID'].apply(lambda x: f'<a class="watch-btn" href="https://www.youtube.com/watch?v={x}" target="_blank">▶ Watch</a>')
    if 'Thumbnail' in display_df.columns:
        display_df['Thumbnail'] = display_df['Thumbnail'].apply(lambda x: f'<img class="thumb-img" src="{x}">')
    safe_columns = ['Thumbnail', 'Title', 'Channel', 'Published', 'Views', 'Likes', 'Comments', 'Engagement Rate', 'Watch Link']
    display_df = display_df[[c for c in safe_columns if c in display_df.columns]]
    html = '<div class="table-container"><table class="premium-table"><thead><tr>'
    for col in display_df.columns: html += f'<th>{col}</th>'
    html += '</tr></thead><tbody>'
    for _, row in display_df.iterrows():
        html += '<tr>'
        for col in display_df.columns: html += f'<td>{row[col]}</td>'
        html += '</tr>'
    html += '</tbody></table></div>'
    st.markdown(html, unsafe_allow_html=True)

def plot_sentiment_arc(text):
    words = text.split()
    if len(words) < 50: return None
    chunk_size = max(1, len(words) // 10)
    sentiments = [round(TextBlob(" ".join(words[i*chunk_size : (i+1)*chunk_size])).sentiment.polarity, 2) for i in range(10)]
    df = pd.DataFrame({"Progress": [f"{i*10}%" for i in range(1, 11)], "Energy": sentiments})
    chart = alt.Chart(df).mark_area(
        line={'color':'#a855f7', 'strokeWidth': 3}, 
        color='#a855f7', opacity=0.2, interpolate='monotone'
    ).encode(
        x=alt.X('Progress', sort=None, axis=alt.Axis(labelAngle=0, title="Video Timeline")),
        y=alt.Y('Energy', title="Sentiment Polarity"),
        tooltip=['Progress', 'Energy']
    ).properties(height=280)
    st.altair_chart(chart, use_container_width=True)

tab1, tab2, tab3, tab4 = st.tabs(["🔥 Trending", "🔬 Video X-Ray", "🔍 Deep Research", "🎬 Production Studio"])

# --- TAB 1: TRENDING ---
with tab1:
    col_header, col_radio = st.columns([2, 1])
    with col_header:
        st.subheader("📈 Live Market Trends")
        st.markdown("Discover what's going viral right now across broad categories or your specific niche.")
    with col_radio:
        st.markdown("<br>", unsafe_allow_html=True)
        trend_mode = st.radio("Search Mode:", ["Broad Categories", "Custom Niche"], horizontal=True, label_visibility="collapsed")

    with st.container(border=True):
        if "Broad" in trend_mode:
            col1, col2 = st.columns(2)
            categories = {"Technology": "28", "Gaming": "20", "Comedy": "23", "Music": "10", "Entertainment": "24", "General": "0"}
            regions = {"India": "IN", "United States": "US", "United Kingdom": "GB", "Canada": "CA", "Australia": "AU", "Japan": "JP"}
            with col1: selected_category = st.selectbox("🎯 Select Domain", list(categories.keys()))
            with col2: selected_region = st.selectbox("🌍 Select Region", list(regions.keys()))
            fetch_button = st.button("🚀 Fetch Live Trends", type="primary", use_container_width=True)
        else:
            colA, colB = st.columns([2, 1])
            with colA: custom_niche = st.text_input("🎯 Enter Specific Niche (e.g., 'Data Science'):")
            with colB: time_filter = st.selectbox("⏱️ Timeframe", ["Anytime", "This Month", "This Week", "Today (Last 24h)"])
            fetch_button = st.button("🚀 Search Niche Creators", type="primary", use_container_width=True)

    st.divider()

    if "Broad" in trend_mode:
        if fetch_button:
            with st.spinner(f"Pulling market data for {selected_region}..."):
                trending_data = api.get_live_trending(category_id=categories[selected_category], region_code=regions[selected_region])
                if trending_data:
                    df = pd.DataFrame(trending_data)
                    df = calculate_engagement(df)
                    st.markdown("#### 📊 Market Summary")
                    k1, k2, k3 = st.columns(3)
                    k1.metric("Average Views", f"{int(df['Views_Raw'].mean()):,}")
                    k2.metric("Average Engagement", f"{df['Eng_Raw'].mean():.2f}%") 
                    k3.metric("Total Market Views", f"{int(df['Views_Raw'].sum()):,}")
                    display_dataframe(df)
                else: st.warning("⚠️ YouTube does not currently have trending data for this category.")
        else:
            st.info("👆 Select your parameters above and click 'Fetch Live Trends' to analyze the market.")
    else:
        if fetch_button and custom_niche:
            with st.spinner(f"Scanning YouTube for {time_filter} trends..."):
                niche_data = api.get_custom_niche_trends(custom_niche, timeframe=time_filter)
                if niche_data:
                    df = pd.DataFrame(niche_data)
                    df = calculate_engagement(df)
                    st.markdown("#### 📊 Niche Summary")
                    k1, k2, k3 = st.columns(3)
                    k1.metric("Average Views", f"{int(df['Views_Raw'].mean()):,}")
                    k2.metric("Average Engagement", f"{df['Eng_Raw'].mean():.2f}%") 
                    k3.metric("Total Market Views", f"{int(df['Views_Raw'].sum()):,}")
                    display_dataframe(df)
                else: st.warning("No viral data found for this niche. Try broadening your search.")
        elif fetch_button and not custom_niche:
            st.error("⚠️ Please enter a niche topic in the search box before searching.")
        else:
            st.info("👆 Enter your specific niche above and click search to uncover top creators.")


# --- TAB 2: VIDEO X-RAY ---
with tab2:
    st.subheader("🔬 Video X-Ray & Competitor Deconstruction")
    st.markdown("Reverse-engineer viral videos to extract their secret documents, affiliate links, and viewer retention hooks.")
    
    with st.container(border=True):
        col_url, col_btn = st.columns([4, 1])
        with col_url:
            user_input = st.text_input("🎯 Paste Target YouTube Link:", placeholder="https://www.youtube.com/watch?v=...")
        with col_btn:
            st.markdown("<br>", unsafe_allow_html=True)
            analyze_btn = st.button("🔬 X-Ray Video", type="primary", use_container_width=True)

    st.divider()

    if analyze_btn and user_input:
        target_video_id = api.extract_video_id(user_input)
        if target_video_id:
            with st.spinner("Extracting metadata, hidden links, transcripts, and generating X-Ray visuals..."):
                transcript_text = api.get_video_transcript(target_video_id)
                metadata = api.get_video_metadata(target_video_id) 
                
                if metadata:
                    hidden_links = api.extract_links(metadata.get('description', ''))
                    
                    col_identity, col_vitals = st.columns([1, 1.2])
                    
                    with col_identity:
                        with st.container(border=True):
                            st.success("Target Acquired")
                            if metadata['thumbnail']: 
                                st.image(metadata['thumbnail'], use_column_width=True)
                            st.markdown(f"### {metadata['title']}")
                            st.markdown(f"**👤 Channel:** `{metadata['channel']}` | **📅 Uploaded:** `{metadata['date']}`")
                            
                            with st.expander("🔗 Resources & Links Used by Creator"):
                                if hidden_links:
                                    st.caption("Auto-extracted links from the description:")
                                    for link in hidden_links: st.markdown(f"- [{link}]({link})")
                                else:
                                    st.caption("No URLs detected in the description.")
                                    
                            with st.expander("📝 View Original Video Description"): 
                                st.write(metadata['description'])
                                
                    with col_vitals:
                        with st.container(border=True):
                            st.markdown("#### 📈 Vital Signs")
                            m1, m2 = st.columns(2)
                            m3, m4 = st.columns(2)
                            
                            views = metadata['views']
                            likes = metadata['likes']
                            comments = metadata['comments']
                            eng_rate = round(((likes + comments) / views * 100), 2) if views > 0 else 0
                            
                            m1.metric("👁️ Total Views", f"{views:,}")
                            m2.metric("👍 Total Likes", f"{likes:,}")
                            m3.metric("💬 Comments", f"{comments:,}")
                            m4.metric("🔥 True Engagement", f"{eng_rate}%")
                            
                        has_transcript = "❌" not in transcript_text
                        text_to_analyze = transcript_text if has_transcript else metadata.get('description', '')
                        
                        if text_to_analyze and len(text_to_analyze.strip()) > 20:
                            insights = api.generate_local_insights(text_to_analyze, is_transcript=has_transcript)
                            with st.container(border=True):
                                st.markdown("#### ⚙️ Technical Script Specs")
                                sc, pc, tc = st.columns(3)
                                sc.metric("⏱️ Est. Length", insights['minutes'], insights['words'])
                                pc.metric("🗣️ Speaking Pace", insights['wpm'])
                                top_kw = insights['tags'][0] if insights['tags'] else "N/A"
                                tc.metric("🎯 Top Keyword", top_kw.capitalize())
                            
                            with st.container(border=True):
                                st.markdown("#### 🛡️ Monetization & Safety")
                                s1, s2 = st.columns(2)
                                s1.metric("Brand Safety", insights['brand_safety'])
                                s2.metric("Est. CPM Tier", insights['cpm_tier'].split(' ')[0])
                            
                            with st.container(border=True):
                                st.markdown("#### 🏷️ Extracted Script Tags")
                                st.caption("Most frequently spoken keywords you can copy for your own tags:")
                                tags_formatted = " • ".join([f"#{t.capitalize()}" for t in insights['tags']])
                                st.markdown(f"`{tags_formatted}`")
                                
                        else: 
                            st.error("❌ Transcript and Description are both empty.")

                    if text_to_analyze and len(text_to_analyze.strip()) > 20:
                        st.markdown("### 🚀 Competitor Deconstruction")

                        with st.container(border=True):
                            st.write(api.get_ai_strategy_breakdown(transcript_text, metadata))
                                    
                        st.markdown("### 📉 Keyword & Narrative Flow")
                        chart_col1, chart_col2 = st.columns(2)
                        with chart_col1:
                            with st.container(border=True):
                                st.markdown("#### 🗣️ Script Frequencies")
                                kw_df = pd.DataFrame(list(insights['keyword_counts'].items()), columns=['Keyword', 'Mentions'])
                                chart1 = alt.Chart(kw_df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color='#3b82f6').encode(
                                    x=alt.X('Keyword', sort='-y', axis=alt.Axis(labelAngle=-45, title=None)),
                                    y=alt.Y('Mentions', title=None),
                                    tooltip=['Keyword', 'Mentions']
                                ).properties(height=280)
                                st.altair_chart(chart1, use_container_width=True)
                                
                        with chart_col2:
                            with st.container(border=True):
                                st.markdown("#### 🎭 Narrative Sentiment Arc")
                                plot_sentiment_arc(text_to_analyze)
                                
                else: 
                    st.error("❌ Invalid Link or Video is Private.")
    elif analyze_btn and not user_input:
        st.error("⚠️ Please enter a YouTube URL.")
    else:
        st.info("👆 Paste a competitor's YouTube link above to X-Ray their strategy, links, and retention hooks.")


# --- TAB 3: DEEP RESEARCH ---
with tab3:
    st.subheader("🔍 Deep Research Workspace")
    st.markdown("A professional documentation dashboard. Collect raw data, analyze sources, and build your bibliography.")
    
    with st.container(border=True):
        query = st.text_input("🎯 Initialize Research Board for Topic:", placeholder="e.g., Solid State Batteries")
        research_btn = st.button("🚀 Build Research Board", type="primary", use_container_width=True)

    st.divider()

    if research_btn and query:
        with st.spinner(f"Compiling intelligence from Academic, News, and Social nodes for '{query}'..."):
            context = api.get_topic_context(query)
            search_results = api.search_trending_topics(query, max_results=3) 
            
            if context:
                col_main, col_sidebar = st.columns([2.2, 1])
                
                with col_main:
                    with st.container(border=True):
                        st.markdown("### 🧠 Executive Content Strategy")
                        st.write(context['ai_briefing'])
                
                with col_sidebar:
                    st.markdown("### 🗄️ Evidence Locker")
                    raw = context['raw_data']
                    safe_query = urllib.parse.quote(query)
                    
                    with st.expander("📄 Deep Data & Academia", expanded=True):
                        if raw['pdfs'] or raw.get('stats'):
                            for item in raw['pdfs'] + raw.get('stats', []): 
                                st.markdown(f"- [{item['title'][:40]}...]({item['url']})")
                            st.divider()
                        st.markdown("**🚀 Direct Launchpads:**")
                        st.markdown(f"<a class='launchpad-link' href='https://www.perplexity.ai/search?q={safe_query}' target='_blank'>🧠 Perplexity AI</a>", unsafe_allow_html=True)
                        st.markdown(f"<a class='launchpad-link' href='https://scholar.google.com/scholar?q={safe_query}' target='_blank'>🎓 Google Scholar</a>", unsafe_allow_html=True)
                        st.markdown(f"<a class='launchpad-link' href='https://www.google.com/search?q=filetype%3Apdf+{safe_query}' target='_blank'>📄 Google PDFs</a>", unsafe_allow_html=True)
                        st.markdown(f"<a class='launchpad-link' href='https://archive.org/search.php?query={safe_query}' target='_blank'>🏛️ Internet Archive</a>", unsafe_allow_html=True)
                            
                    with st.expander("🗣️ Public Pulse & Socials", expanded=False):
                        if raw['forums']:
                            for item in raw['forums']: 
                                st.markdown(f"- [{item['title'][:40]}...]({item['url']})")
                            st.divider()
                        st.markdown("**🚀 Direct Launchpads:**")
                        st.markdown(f"<a class='launchpad-link' href='https://www.tiktok.com/search?q={safe_query}' target='_blank'>📱 TikTok</a>", unsafe_allow_html=True)
                        st.markdown(f"<a class='launchpad-link' href='https://www.reddit.com/search/?q={safe_query}' target='_blank'>👽 Reddit</a>", unsafe_allow_html=True)
                        st.markdown(f"<a class='launchpad-link' href='https://twitter.com/search?q={safe_query}' target='_blank'>🐦 X (Twitter)</a>", unsafe_allow_html=True)
                        st.markdown(f"<a class='launchpad-link' href='https://www.quora.com/search?q={safe_query}' target='_blank'>❓ Quora</a>", unsafe_allow_html=True)
                            
                    with st.expander("📰 News & Trends", expanded=False):
                        if raw['news']:
                            for item in raw['news']: 
                                st.markdown(f"- [{item['title'][:40]}...]({item['url']})")
                            st.divider()
                        st.markdown("**🚀 Direct Launchpads:**")
                        st.markdown(f"<a class='launchpad-link' href='https://trends.google.com/trends/explore?q={safe_query}' target='_blank'>📈 Google Trends</a>", unsafe_allow_html=True)
                        st.markdown(f"<a class='launchpad-link' href='https://news.google.com/search?q={safe_query}' target='_blank'>📰 Google News</a>", unsafe_allow_html=True)
                        st.markdown(f"<a class='launchpad-link' href='https://hn.algolia.com/?q={safe_query}' target='_blank'>💻 Hacker News</a>", unsafe_allow_html=True)
                            
                    st.divider()
                    st.markdown("### 🎨 Visual Asset Hub")
                    st.caption("1-Click search links for copyright-free stock media.")
                    st.markdown(f"🎥 [Find B-Roll on Pexels](https://www.pexels.com/search/{safe_query}/)")
                    st.markdown(f"📷 [Find Images on Unsplash](https://unsplash.com/s/photos/{safe_query})")
                    st.markdown(f"🎵 [Find Audio on Pixabay](https://pixabay.com/music/search/{safe_query}/)")
                    
                    st.divider()
                    st.markdown("### 🎥 Direct Competitors")
                    if search_results:
                        for vid in search_results:
                            with st.container(border=True):
                                st.image(vid['Thumbnail'], use_column_width=True)
                                st.markdown(f"**[{vid['Title'][:40]}...]**")
                                
    elif research_btn and not query:
        st.error("⚠️ Please enter a topic to research.")
    else:
        st.info("👆 Enter a topic above and click 'Build Research Board' to start your deep dive.")


# --- TAB 4: PRODUCTION STUDIO ---
with tab4:
    st.subheader("🎬 The Production Studio & Writer's Room")
    st.markdown("Turn your research into a finalized storyboard, and draft your script with your AI Co-Pilot.")
    
    with st.container(border=True):
        colA, colB, colC = st.columns(3)
        with colA: 
            prod_topic = st.text_input("🎯 Core Topic Idea:", placeholder="Reality of Ajit Doval")
        with colB: 
            prod_audience = st.selectbox("👥 Target Audience:", ["Beginners/General", "Intermediate", "Experts/Professionals"])
        with colC: 
            prod_tone = st.selectbox("🎭 Content Tone:", ["Educational & Serious", "High-Energy & Entertaining", "Dramatic & Story-Driven"])
            
        prod_btn = st.button("🎬 Generate Master Storyboard", type="primary", use_container_width=True)

    if prod_btn and prod_topic:
        with st.spinner(f"Drafting full production storyboard for '{prod_topic}'..."):
            raw_plan = api.generate_production_plan(prod_topic, prod_audience, prod_tone)
            ref_videos = api.search_trending_topics(prod_topic, lang="All Languages", max_results=3) 
            
            plan_parts = [p.strip() for p in raw_plan.split("|||")]
            
            if len(plan_parts) >= 5:
                st.markdown("### 📋 The Director's Storyboard")
                
                card_col1, card_col2 = st.columns(2)
                with card_col1:
                    with st.container(border=True):
                        st.markdown("#### 🎯 Title & Thumbnail Concepts")
                        st.write(plan_parts[0])
                with card_col2:
                    with st.container(border=True):
                        st.markdown("#### 🪝 The 30-Second Hook Script")
                        st.write(plan_parts[1])
                
                card_col3, card_col4 = st.columns(2)
                with card_col3:
                    with st.container(border=True):
                        st.markdown("#### 📐 Main Script Blueprint")
                        st.write(plan_parts[2])
                with card_col4:
                    with st.container(border=True):
                        st.markdown("#### 🎬 Visuals & B-Roll Shot List")
                        st.write(plan_parts[3])
                
                with st.container(border=True):
                    st.markdown("#### 📦 The Upload Packet (SEO, Tags, Desc)")
                    st.write(plan_parts[4])
            else:
                st.warning("⚠️ The AI formatting glitched slightly. Here is the raw production plan:")
                st.write(raw_plan)
                
            st.divider()
            
            st.markdown("### 📺 Visual Inspiration Board")
            st.caption("Here are the thumbnails currently dominating this topic on YouTube:")
            if ref_videos:
                video_ids = [v['Video ID'] for v in ref_videos]
                df_refs = calculate_engagement(pd.merge(pd.DataFrame(ref_videos), pd.DataFrame(api.get_video_stats(video_ids)), on='Video ID'))
                display_dataframe(df_refs)
    
    st.divider()
    
    st.markdown("### 💬 The AI Co-Pilot")
    st.caption("Chat with your AI director. Ask it to write a script from scratch, or paste your draft for an instant brutal critique on pacing and retention.")
    
    col_chat1, col_chat2 = st.columns([4, 1])
    with col_chat2:
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = [{"role": "assistant", "content": "👋 Chat cleared! Paste your script draft for a grade, or ask me to write a scene from scratch."}]
            st.rerun()
            
    with st.container(border=True):
        for message in st.session_state.messages:
            with st.chat_message(message["role"]): 
                st.markdown(message["content"])
                
        if prompt := st.chat_input("Paste a script to review, or ask: 'Write a 60-second intro about Ajit Doval'"):
            with st.chat_message("user"): 
                st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = api.generate_chat_response(prompt, st.session_state.messages[:-1])
                    st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})