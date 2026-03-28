import os
import re
import time
from collections import Counter
import wikipedia
from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from groq import Groq
from dotenv import load_dotenv
from duckduckgo_search import DDGS
from textblob import TextBlob

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
AI_MODEL = "llama-3.1-8b-instant" 

class YouTubeCopilotAPI:
    def __init__(self):
        self.youtube = None
        if YOUTUBE_API_KEY:
            self.youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY.strip())
            
        self.ai_client = None
        if GROQ_API_KEY:
            self.ai_client = Groq(api_key=GROQ_API_KEY.strip())
            
        self.lang_map = {
            "English": "en", "Hindi": "hi", "Marathi": "mr", 
            "Tamil": "ta", "Telugu": "te", "Spanish": "es"
        }

    def extract_video_id(self, url_or_id):
        if not url_or_id: return None
        if len(url_or_id) == 11 and " " not in url_or_id: return url_or_id 
        regex = r"(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/|youtube\.com\/shorts\/)([^\"&?\/\s]{11})"
        match = re.search(regex, url_or_id)
        return match.group(1) if match else None

    def extract_links(self, text):
        if not text: return []
        url_pattern = re.compile(r'https?://\S+|www\.\S+')
        raw_links = url_pattern.findall(text)
        clean_links = [link.rstrip('.,!?"\'') for link in raw_links]
        return list(set(clean_links)) 

    def get_video_metadata(self, video_id):
        if not self.youtube: return None
        try:
            request = self.youtube.videos().list(part="snippet,statistics", id=video_id)
            response = request.execute()
            if not response.get('items'): return None
            
            item = response['items'][0]
            snippet = item['snippet']
            stats = item.get('statistics', {})
            
            return {
                "title": snippet.get("title", ""),
                "description": snippet.get("description", ""),
                "channel": snippet.get("channelTitle", ""),
                "date": snippet.get("publishedAt", "")[:10],
                "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0))
            }
        except: return None

    def search_trending_topics(self, query, lang="All Languages", max_results=5):
        if not self.youtube: return []
        try:
            search_params = {'q': query, 'part': 'snippet', 'type': 'video', 'maxResults': max_results}
            if lang != "All Languages": search_params['relevanceLanguage'] = self.lang_map.get(lang, "en")
            request = self.youtube.search().list(**search_params)
            response = request.execute()
            return [{'Video ID': item['id']['videoId'], 'Thumbnail': item['snippet']['thumbnails']['high']['url'], 'Title': item['snippet']['title'], 'Channel': item['snippet']['channelTitle']} for item in response.get('items', [])]
        except: return []

    def get_video_stats(self, video_ids):
        if not self.youtube or not video_ids: return []
        try:
            ids_string = ','.join(video_ids)
            request = self.youtube.videos().list(part='statistics', id=ids_string)
            response = request.execute()
            stats_list = []
            for item in response.get('items', []):
                stats = item['statistics']
                stats_list.append({
                    'Video ID': item['id'], 
                    'Views': int(stats.get('viewCount', 0)), 
                    'Likes': int(stats.get('likeCount', 0)), 
                    'Comments': int(stats.get('commentCount', 0))
                })
            return stats_list
        except: return []

    def get_live_trending(self, category_id="0", region_code="IN", max_results=15):
        if not self.youtube: return []
        try:
            request = self.youtube.videos().list(part='snippet,statistics', chart='mostPopular', regionCode=region_code, videoCategoryId=category_id, maxResults=max_results)
            response = request.execute()
            videos = []
            for item in response.get('items', []):
                stats = item['statistics']
                videos.append({
                    'Video ID': item['id'], 'Title': item['snippet']['title'], 'Channel': item['snippet']['channelTitle'],
                    'Published': item['snippet']['publishedAt'][:10],
                    'Thumbnail': item['snippet']['thumbnails']['high']['url'],
                    'Views': int(stats.get('viewCount', 0)), 'Likes': int(stats.get('likeCount', 0)), 'Comments': int(stats.get('commentCount', 0))
                })
            return videos
        except: return []

    def get_custom_niche_trends(self, query, timeframe="Anytime", max_results=15):
        if not self.youtube: return []
        try:
            search_params = {'q': query, 'part': 'snippet', 'type': 'video', 'maxResults': max_results, 'order': 'viewCount'}
            if timeframe == "Today (Last 24h)": search_params['publishedAfter'] = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
            elif timeframe == "This Week": search_params['publishedAfter'] = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
            elif timeframe == "This Month": search_params['publishedAfter'] = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
            
            request = self.youtube.search().list(**search_params)
            response = request.execute()
            if not response.get('items'): return []
            
            video_ids = [item['id']['videoId'] for item in response['items']]
            stats_list = self.get_video_stats(video_ids)
            videos = []
            for item in response['items']:
                vid_id = item['id']['videoId']
                stat = next((s for s in stats_list if s['Video ID'] == vid_id), None)
                if stat:
                    videos.append({
                        'Video ID': vid_id, 'Thumbnail': item['snippet']['thumbnails']['high']['url'], 
                        'Title': item['snippet']['title'], 'Channel': item['snippet']['channelTitle'], 
                        'Published': item['snippet']['publishedAt'][:10],
                        'Views': stat['Views'], 'Likes': stat['Likes'], 'Comments': stat['Comments']
                    })
            return videos
        except Exception: return []

    def get_topic_context(self, query):
        if not self.ai_client: return None
        raw_data = {"wiki": [], "web": [], "stats": [], "forums": [], "news": [], "pdfs": []}
        safe_images = []
        try:
            wiki_res = wikipedia.search(query)
            if wiki_res:
                try: page = wikipedia.page(wiki_res[0], auto_suggest=False)
                except wikipedia.exceptions.DisambiguationError as e: page = wikipedia.page(e.options[0], auto_suggest=False) 
                raw_data["wiki"].append({"title": page.title, "url": page.url, "snippet": page.summary[:1000]})
                safe_images = [img for img in page.images if img.lower().endswith(('.png', '.jpg', '.jpeg'))][:4]
        except Exception: pass
        try:
            with DDGS() as ddgs:
                try: 
                    for res in list(ddgs.text(query, max_results=3)): raw_data["web"].append({"title": res.get('title'), "url": res.get('href'), "snippet": res.get('body')})
                    time.sleep(1.5)
                except: pass
                try: 
                    for res in list(ddgs.text(f"{query} filetype:pdf", max_results=3)): raw_data["pdfs"].append({"title": res.get('title'), "url": res.get('href'), "snippet": res.get('body')})
                    time.sleep(1.5)
                except: pass
                try: 
                    for res in list(ddgs.text(f"{query} site:reddit.com", max_results=3)): raw_data["forums"].append({"title": res.get('title'), "url": res.get('href'), "snippet": res.get('body')})
                    time.sleep(1.5)
                except: pass
        except Exception: pass 
        total_sources = sum(len(v) for k, v in raw_data.items())

        if total_sources > 0:
            prompt = f"""Act as a Senior Research Analyst and YouTube Strategist. I am doing deep research on: '{query}'. 
            Based on the raw data collected, synthesize a high-level briefing. RAW DATA: {raw_data}
            
            Format exactly like this using Markdown:
            ### ⏱️ The 60-Second Brief
            ### 📊 The Hard Numbers
            ### 🗣️ The Real Conversation
            ### 💰 Monetization & Sponsors
            ### 🧠 Production Angles
            ### 🏷️ Top 15 SEO Tags
            ### 🎨 AI Thumbnail Prompts
            """
        else:
            prompt = f"""Act as an Expert Content Strategist. I am doing deep research on: '{query}'. 
            My live scrapers are rate-limited, so you MUST rely entirely on your internal training data.
            
            Format exactly like this using Markdown:
            ### ⏱️ The 60-Second Brief
            ⚠️ *Live Scraper Blocked. Report generated from AI Memory Bank.*
            ### 📊 Historical Data & Context
            ### 🗣️ Common Public Debates
            ### 💰 Monetization & Sponsors
            ### 🧠 Production Angles
            ### 🏷️ Top 15 SEO Tags
            ### 🎨 AI Thumbnail Prompts
            """
        try:
            chat = self.ai_client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=AI_MODEL, temperature=0.5)
            ai_summary = chat.choices[0].message.content
        except Exception as e: ai_summary = f"⚠️ AI Engine failed. Error: {e}"
        return {"title": query.title(), "ai_briefing": ai_summary, "raw_data": raw_data, "images": safe_images}

    def get_video_transcript(self, video_id):
        try:
            ytt_api = YouTubeTranscriptApi()
            transcript_list = ytt_api.list(video_id)
            try: transcript_to_fetch = transcript_list.find_transcript(['en'])
            except:
                original_transcript = next(iter(transcript_list))
                try: transcript_to_fetch = original_transcript.translate('en')
                except: transcript_to_fetch = original_transcript
            transcript_data = transcript_to_fetch.fetch()
            if isinstance(transcript_data[0], dict): return " ".join([entry['text'] for entry in transcript_data])
            else: return " ".join([snippet.text for snippet in transcript_data])
        except Exception as e: return f"❌ Could not extract transcript. Error: {e}"

    def generate_local_insights(self, text, is_transcript=True):
        if not text or "❌" in text: return None
        words = text.lower().split()
        word_count = len(words)
        est_minutes = max(1, round(word_count / 150))
        wpm = word_count / est_minutes if est_minutes > 0 else 0
        stop_words = {'the', 'and', 'to', 'a', 'of', 'in', 'is', 'that', 'for', 'it', 'on', 'you', 'this', 'with', 'as', 'are', 'be', 'was', 'have', 'but', 'not', 'they', 'so', 'can', 'if', 'what', 'about', 'just', 'from', 'all', 'out', 'up', 'or', 'my', 'do', 'we'}
        meaningful_words = [w.strip(".,!?\"'") for w in words if w.isalpha() and w not in stop_words and len(w) > 4]
        top_keywords_tuples = Counter(meaningful_words).most_common(10)
        top_keywords = [word[0] for word in top_keywords_tuples]
        keyword_counts = {word: count for word, count in top_keywords_tuples}
        brand_safety_score = max(0, 100 - (sum(1 for w in meaningful_words if w in ['fuck', 'shit', 'sex', 'kill', 'murder']) * 5))
        cpm_tier = "High 🟢 ($8-$15 CPM)" if len(text) > 2000 else "Medium 🟡 ($4-$7 CPM)"
        if brand_safety_score < 70: cpm_tier = "Low 🔴 (Risk)"
        return {
            "minutes": f"~{est_minutes} Min",
            "words": f"{word_count:,} total",
            "wpm": f"{round(wpm)} wpm",
            "tags": top_keywords, 
            "keyword_counts": keyword_counts,
            "brand_safety": f"{brand_safety_score}%", 
            "cpm_tier": cpm_tier                      
        }

    def get_ai_strategy_breakdown(self, transcript_text, metadata):
        if not self.ai_client: return "⚠️ System Notice: Groq API Key missing."
        if "❌" in transcript_text or not transcript_text:
            content_to_analyze = f"Title: {metadata.get('title')}\nDescription: {metadata.get('description')}"
        else:
            content_to_analyze = transcript_text[:5000]

        prompt = f"""Act as a brutal but fair YouTube Strategist. You are helping a creator reverse-engineer a competitor's video so they can make a better one.
        Analyze this transcript/metadata: {content_to_analyze}
        
        Provide EXACTLY this Markdown structure. Be highly specific and critical based on the actual text:
        ### 🏆 What They Did Right (Strengths)
        ### ⚠️ Where They Failed (Mistakes to Exploit)
        ### 💡 How to Beat Them
        """
        try:
            chat = self.ai_client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=AI_MODEL, temperature=0.7)
            return chat.choices[0].message.content
        except Exception as e: return f"⚠️ Strategy engine unavailable. Try again later. (Error: {str(e)})"

    def generate_production_plan(self, topic, audience, tone):
        if not self.ai_client: return "⚠️ System Notice: Groq API Key missing."
        prompt = f"""Act as an elite YouTube Executive Producer. I need a complete 'Production Blueprint' for a new video.
        Topic: '{topic}'
        Target Audience: '{audience}'
        Vibe/Tone: '{tone}'
        
        You MUST format your response into exactly 5 sections separated by the characters "|||". 
        Do NOT use markdown headers like ### for the section titles, I will add them in the UI. Just provide the raw content for each section.
        
        [Content for 3 highly clickable Title & Thumbnail concepts]
        |||
        [Content for a word-for-word script of the first 30 seconds (The Hook)]
        |||
        [Content for a detailed bulleted outline of the rest of the video script]
        |||
        [Content for a B-Roll shot list and editing/visual suggestions]
        |||
        [Content for the Upload Packet: SEO Description, 15 Tags, and a Pinned Comment]
        """
        try:
            chat = self.ai_client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=AI_MODEL, temperature=0.8)
            return chat.choices[0].message.content
        except Exception as e: return f"⚠️ Production engine failed. Error: {str(e)}"

    def generate_chat_response(self, prompt, history):
        if not self.ai_client: return "⚠️ Groq API Key missing."
        
        system_prompt = """You are an elite YouTube Script Writer and Editor. 
        - If the user asks you to write a script or a hook, write a highly engaging, well-paced YouTube script with visual cues.
        - If the user pastes a draft script, act as a brutal but fair editor. Critique the hook, identify retention drops, fix the pacing, and offer a rewritten version.
        Keep formatting clean and highly readable.
        """
        
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history: messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": prompt})
        try:
            chat = self.ai_client.chat.completions.create(messages=messages, model=AI_MODEL, temperature=0.7)
            return chat.choices[0].message.content
        except Exception as e: return f"❌ Chat Error: {e}"