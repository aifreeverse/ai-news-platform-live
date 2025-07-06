"""
Enhanced AI News Website with Full Features
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from datetime import datetime
import asyncio
from typing import List, Dict, Optional
import json
import os

from backend.services.lm_studio_client import LMStudioClient
from backend.services.news_scraper_enhanced import EnhancedNewsScraperService
from backend.websocket_manager import WebSocketManager

# Global variables
news_cache = []
trending_cache = []
websocket_manager = WebSocketManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("🚀 Starting Enhanced AI News Platform...")
    
    # Start background news fetching
    asyncio.create_task(background_news_updater())
    
    yield
    
    # Shutdown
    print("📴 Shutting down Enhanced AI News Platform...")

app = FastAPI(
    title="Enhanced AI News Platform",
    description="AI-powered news with LM Studio integration, 3D visualization, and real-time updates",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    """Enhanced homepage with 3D visualization"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🚀 Enhanced AI News Platform</title>
        <!-- Three.js replaced with simple visualization -->
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: white;
                overflow-x: hidden;
            }
            
            .header {
                text-align: center;
                padding: 20px;
                background: rgba(0, 0, 0, 0.2);
                backdrop-filter: blur(10px);
            }
            
            .header h1 {
                font-size: 2.5rem;
                margin-bottom: 10px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            
            .status-bar {
                display: flex;
                justify-content: space-around;
                padding: 10px;
                background: rgba(0, 0, 0, 0.1);
                font-size: 0.9rem;
            }
            
            .status-item {
                display: flex;
                align-items: center;
                gap: 5px;
            }
            
            .status-indicator {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #4CAF50;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }
            
            .main-container {
                display: grid;
                grid-template-columns: 1fr 400px;
                gap: 20px;
                padding: 20px;
                height: calc(100vh - 200px);
            }
            
            .visualization-container {
                background: rgba(0, 0, 0, 0.3);
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                position: relative;
                overflow: hidden;
            }
            
            .sidebar {
                display: flex;
                flex-direction: column;
                gap: 20px;
            }
            
            .news-panel, .trending-panel {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 20px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                flex: 1;
            }
            
            .panel-title {
                font-size: 1.2rem;
                margin-bottom: 15px;
                color: #fff;
                border-bottom: 1px solid rgba(255, 255, 255, 0.2);
                padding-bottom: 10px;
            }
            
            .news-item {
                background: rgba(0, 0, 0, 0.2);
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 10px;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .news-item:hover {
                background: rgba(0, 0, 0, 0.4);
                transform: translateX(5px);
            }
            
            .news-title {
                font-size: 0.9rem;
                font-weight: bold;
                margin-bottom: 5px;
            }
            
            .news-meta {
                font-size: 0.8rem;
                opacity: 0.7;
                display: flex;
                justify-content: space-between;
            }
            
            .trending-item {
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .trending-topic {
                font-weight: bold;
            }
            
            .trending-count {
                background: rgba(255, 255, 255, 0.2);
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 0.8rem;
            }
            
            .article-detail-panel {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: rgba(0, 0, 0, 0.9);
                backdrop-filter: blur(20px);
                border-radius: 15px;
                padding: 0;
                max-width: 600px;
                width: 90%;
                max-height: 80vh;
                overflow-y: auto;
                z-index: 1000;
                border: 1px solid rgba(255, 255, 255, 0.2);
                display: none;
            }
            
            .panel-content {
                padding: 30px;
                position: relative;
            }
            
            .close-btn {
                position: absolute;
                top: 15px;
                right: 20px;
                background: none;
                border: none;
                color: white;
                font-size: 24px;
                cursor: pointer;
                opacity: 0.7;
            }
            
            .close-btn:hover {
                opacity: 1;
            }
            
            .read-more {
                display: inline-block;
                background: linear-gradient(45deg, #667eea, #764ba2);
                color: white;
                padding: 10px 20px;
                border-radius: 25px;
                text-decoration: none;
                margin-top: 15px;
                transition: all 0.3s ease;
            }
            
            .read-more:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
            }
            
            @media (max-width: 768px) {
                .main-container {
                    grid-template-columns: 1fr;
                    height: auto;
                }
                
                .visualization-container {
                    height: 400px;
                }
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 Enhanced AI News Platform</h1>
            <p>Real-time AI processing with 3D visualization and live updates</p>
        </div>
        
        <div class="status-bar">
            <div class="status-item">
                <div class="status-indicator" id="lm-status"></div>
                <span>LM Studio: <span id="lm-text">Connecting...</span></span>
            </div>
            <div class="status-item">
                <div class="status-indicator" id="ws-status"></div>
                <span>WebSocket: <span id="ws-text">Connecting...</span></span>
            </div>
            <div class="status-item">
                <div class="status-indicator" id="news-status"></div>
                <span>News: <span id="news-text">Loading...</span></span>
            </div>
        </div>
        
        <div class="main-container">
            <div class="visualization-container" id="visualization-container">
                <!-- 3D visualization will be rendered here -->
            </div>
            
            <div class="sidebar">
                <div class="news-panel">
                    <div class="panel-title">📰 Latest News</div>
                    <div id="news-list">
                        <div class="news-item">Loading news articles...</div>
                    </div>
                </div>
                
                <div class="trending-panel">
                    <div class="panel-title">🔥 Trending Topics</div>
                    <div id="trending-list">
                        <div class="trending-item">Loading trending topics...</div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="/static/js/simple-visualization.js"></script>
        <script>
            let newsVisualization;
            let websocket;
            
            // Initialize 3D visualization
            function initVisualization() {
                try {
                    // Simple visualization will auto-initialize
                    console.log('3D visualization initialized');
                } catch (error) {
                    console.error('Failed to initialize 3D visualization:', error);
                    document.getElementById('three-container').innerHTML = 
                        '<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: white;">3D Visualization Loading...</div>';
                }
            }
            
            // WebSocket connection
            function connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws`;
                
                websocket = new WebSocket(wsUrl);
                
                websocket.onopen = function(event) {
                    console.log('WebSocket connected');
                    updateStatus('ws', true, 'Connected');
                };
                
                websocket.onmessage = function(event) {
                    const message = JSON.parse(event.data);
                    handleWebSocketMessage(message);
                };
                
                websocket.onclose = function(event) {
                    console.log('WebSocket disconnected');
                    updateStatus('ws', false, 'Disconnected');
                    // Reconnect after 5 seconds
                    setTimeout(connectWebSocket, 5000);
                };
                
                websocket.onerror = function(error) {
                    console.error('WebSocket error:', error);
                    updateStatus('ws', false, 'Error');
                };
            }
            
            function handleWebSocketMessage(message) {
                switch (message.type) {
                    case 'news_update':
                    case 'initial_data':
                        updateNewsDisplay(message.data);
                        if (newsVisualization) {
                            newsVisualization.updateNewsData(message.data);
                        }
                        updateStatus('news', true, `${message.count} articles`);
                        break;
                    
                    case 'trending_update':
                        updateTrendingDisplay(message.data);
                        break;
                    
                    case 'system_status':
                        updateSystemStatus(message.data);
                        break;
                }
            }
            
            function updateNewsDisplay(articles) {
                const newsList = document.getElementById('news-list');
                newsList.innerHTML = articles.map(article => `
                    <div class="news-item" onclick="showArticleDetail(${JSON.stringify(article).replace(/"/g, '&quot;')})">
                        <div class="news-title">${article.title}</div>
                        <div class="news-meta">
                            <span>${article.category || 'General'}</span>
                            <span>${article.source}</span>
                        </div>
                    </div>
                `).join('');
            }
            
            function updateTrendingDisplay(trending) {
                const trendingList = document.getElementById('trending-list');
                trendingList.innerHTML = trending.map(item => `
                    <div class="trending-item">
                        <span class="trending-topic">${item.topic}</span>
                        <span class="trending-count">${item.mentions}</span>
                    </div>
                `).join('');
            }
            
            function updateStatus(type, isOnline, text) {
                const indicator = document.getElementById(`${type}-status`);
                const textElement = document.getElementById(`${type}-text`);
                
                indicator.style.background = isOnline ? '#4CAF50' : '#f44336';
                textElement.textContent = text;
            }
            
            function updateSystemStatus(status) {
                updateStatus('lm', status.lm_studio_online, status.lm_studio_online ? 'Online' : 'Offline');
            }
            
            function showArticleDetail(article) {
                if (newsVisualization) {
                    newsVisualization.showArticleDetails(article);
                }
            }
            
            // Initialize everything
            document.addEventListener('DOMContentLoaded', function() {
                initVisualization();
                connectWebSocket();
                
                // Check LM Studio status
                fetch('/api/health')
                    .then(response => response.json())
                    .then(data => {
                        updateStatus('lm', data.lm_studio_online, data.lm_studio_online ? 'Online' : 'Offline');
                    })
                    .catch(() => {
                        updateStatus('lm', false, 'Error');
                    });
            });
        </script>
    </body>
    </html>
    """
    return html_content

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

@app.get("/api/news")
async def get_news():
    """Get all news articles"""
    return {
        "status": "success",
        "data": news_cache,
        "total": len(news_cache)
    }

@app.get("/api/trending")
async def get_trending():
    """Get trending topics"""
    return {
        "status": "success",
        "data": trending_cache
    }

@app.get("/api/health")
async def health_check():
    """Enhanced health check with LM Studio status"""
    lm_studio_online = False
    
    try:
        async with LMStudioClient() as client:
            lm_studio_online = await client.health_check()
    except:
        pass
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "lm_studio_online": lm_studio_online,
        "websocket_connections": websocket_manager.get_connection_count(),
        "cached_articles": len(news_cache)
    }

@app.post("/api/refresh")
async def manual_refresh(background_tasks: BackgroundTasks):
    """Manually trigger news refresh"""
    background_tasks.add_task(fetch_and_process_news)
    return {"status": "success", "message": "News refresh initiated"}

async def background_news_updater():
    """Background task to update news every hour"""
    while True:
        try:
            await fetch_and_process_news()
            # Wait 1 hour (3600 seconds)
            await asyncio.sleep(3600)
        except Exception as e:
            print(f"Error in background updater: {e}")
            await asyncio.sleep(300)  # Wait 5 minutes on error

async def fetch_and_process_news():
    """Enhanced news fetching with AI processing"""
    global news_cache, trending_cache
    
    try:
        print("🔄 Fetching news from multiple sources...")
        
        # Fetch raw articles
        async with EnhancedNewsScraperService() as scraper:
            raw_articles = await scraper.fetch_all_sources()
            trending_topics = await scraper.get_trending_topics(raw_articles)
        
        if not raw_articles:
            print("⚠️ No articles fetched, using sample data")
            raw_articles = get_sample_articles()
        
        # Process with AI
        processed_articles = []
        async with LMStudioClient() as ai_client:
            lm_available = await ai_client.health_check()
            
            for article in raw_articles[:20]:  # Limit to 20 articles
                try:
                    if lm_available:
                        # AI processing
                        category = await ai_client.categorize_article(article['title'], article['content'])
                        summary = await ai_client.summarize_article(article['title'], article['content'])
                        sentiment = await ai_client.analyze_sentiment(article['content'])
                        keywords = await ai_client.extract_keywords(article['content'])
                    else:
                        # Fallback processing
                        category = "Technology"
                        summary = article['content'][:200] + "..."
                        sentiment = "Neutral"
                        keywords = []
                    
                    processed_article = {
                        'id': len(processed_articles) + 1,
                        'title': article['title'],
                        'content': article['content'],
                        'summary': summary,
                        'category': category,
                        'sentiment': sentiment,
                        'keywords': keywords,
                        'source': article['source'],
                        'url': article.get('url', ''),
                        'published': article.get('published', datetime.now().isoformat()),
                        'processed_at': datetime.now().isoformat()
                    }
                    processed_articles.append(processed_article)
                    
                except Exception as e:
                    print(f"Error processing article: {e}")
                    continue
        
        # Update cache
        news_cache = processed_articles
        trending_cache = trending_topics
        
        # Broadcast updates
        await websocket_manager.broadcast_news_update(processed_articles)
        await websocket_manager.broadcast_trending_update(trending_topics)
        
        # System status update
        async with LMStudioClient() as client:
            lm_online = await client.health_check()
        
        await websocket_manager.broadcast_system_status({
            'lm_studio_online': lm_online,
            'articles_processed': len(processed_articles),
            'last_update': datetime.now().isoformat()
        })
        
        print(f"✅ Processed {len(processed_articles)} articles successfully")
        
    except Exception as e:
        print(f"❌ Error in news processing: {e}")
        # Use sample data as fallback
        if not news_cache:
            news_cache = get_sample_articles()
            await websocket_manager.broadcast_news_update(news_cache)

def get_sample_articles():
    """Sample articles for fallback"""
    return [
        {
            'id': 1,
            'title': 'AI Breakthrough: Quantum Computing Advances',
            'summary': 'Scientists achieve new milestone in quantum AI processing with revolutionary algorithms.',
            'category': 'Technology',
            'sentiment': 'Positive',
            'keywords': ['AI', 'Quantum', 'Computing', 'Breakthrough'],
            'source': 'Tech News',
            'url': '#',
            'published': datetime.now().isoformat()
        },
        {
            'id': 2,
            'title': 'Machine Learning Revolutionizes Healthcare',
            'summary': 'New AI models predict diseases with 99% accuracy, transforming medical diagnosis.',
            'category': 'Healthcare',
            'sentiment': 'Positive',
            'keywords': ['Machine Learning', 'Healthcare', 'AI', 'Diagnosis'],
            'source': 'Medical Journal',
            'url': '#',
            'published': datetime.now().isoformat()
        },
        {
            'id': 3,
            'title': 'Autonomous Vehicles Hit the Streets',
            'summary': 'Self-driving cars begin commercial deployment in major cities worldwide.',
            'category': 'Transportation',
            'sentiment': 'Positive',
            'keywords': ['Autonomous', 'Vehicles', 'Self-driving', 'Transportation'],
            'source': 'Auto News',
            'url': '#',
            'published': datetime.now().isoformat()
        }
    ]

if __name__ == "__main__":
    uvicorn.run(
        "enhanced_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
