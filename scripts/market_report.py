#!/usr/bin/env python3
"""
Daily Market Report Script
- Crypto: Top gainers 24h from CoinGecko
- Forex: Major pairs + news from multiple sources
- ETF: Market moving news and events
Sends report to Telegram
"""

import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# ========== TELEGRAM ==========
def send_telegram_message(message):
    """Send message to Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }
    try:
        response = requests.post(url, data=payload, timeout=30)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

# ========== CRYPTO ==========
def get_crypto_gainers():
    """Get top crypto gainers from CoinGecko"""
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            'vs_currency': 'usd',
            'order': 'price_change_percentage_24h_desc',
            'per_page': 10,
            'page': 1,
            'sparkline': False,
            'price_change_percentage': '24h'
        }
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        gainers = []
        for coin in data:
            pct = coin.get('price_change_percentage_24h', 0)
            if pct and pct > 0:
                gainers.append({
                    'name': coin.get('name', 'N/A'),
                    'symbol': coin.get('symbol', '').upper(),
                    'price': coin.get('current_price', 0),
                    'change_24h': pct
                })
        
        return gainers[:10]
    except Exception as e:
        print(f"CoinGecko error: {e}")
        return []

# ========== FOREX NEWS ==========
def get_forex_news():
    """Scrape forex news from multiple sources"""
    news_items = []
    
    # Try Investing.com forex news
    try:
        url = "https://www.investing.com/news/forex-news"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        articles = soup.select('.articleItem')[:5]
        for article in articles:
            title_elem = article.select_one('.title')
            if title_elem:
                news_items.append({
                    'title': title_elem.get_text(strip=True),
                    'source': 'Investing.com'
                })
    except Exception as e:
        print(f"Investing.com error: {e}")
    
    # Fallback: Try DailyForex
    if len(news_items) < 3:
        try:
            url = "https://www.dailyforex.com/forex-news"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            titles = soup.select('.news-title, h3 a, .article-title')[:5]
            for title in titles:
                text = title.get_text(strip=True)
                if text and len(text) > 20:
                    news_items.append({
                        'title': text,
                        'source': 'DailyForex'
                    })
        except Exception as e:
            print(f"DailyForex error: {e}")
    
    return news_items[:5]

# ========== ETF & MARKET NEWS ==========
def get_etf_market_news():
    """Get ETF and broader market news"""
    news_items = []
    
    # Try ETF.com
    try:
        url = "https://www.etf.com/news"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        articles = soup.select('.news-title, .title a, h3 a')[:5]
        for article in articles:
            text = article.get_text(strip=True)
            if text and len(text) > 20:
                news_items.append({
                    'title': text,
                    'source': 'ETF.com'
                })
    except Exception as e:
        print(f"ETF.com error: {e}")
    
    # Try Yahoo Finance ETF news as fallback
    if len(news_items) < 3:
        try:
            url = "https://finance.yahoo.com/topic/etf/"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            titles = soup.select('h3, .js-content-viewer')[:5]
            for title in titles:
                text = title.get_text(strip=True)
                if text and len(text) > 20 and 'ETF' in text.upper():
                    news_items.append({
                        'title': text,
                        'source': 'Yahoo Finance'
                    })
        except Exception as e:
            print(f"Yahoo Finance error: {e}")
    
    return news_items[:5]

# ========== ECONOMIC CALENDAR ==========
def get_economic_events():
    """Get important economic events for today"""
    events = []
    try:
        url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        today = datetime.now(pytz.UTC).strftime('%m-%d-%Y')
        
        for event in data:
            if event.get('date', '').startswith(today):
                impact = event.get('impact', '')
                if impact in ['High', 'Medium']:
                    events.append({
                        'title': event.get('title', 'N/A'),
                        'country': event.get('country', ''),
                        'impact': impact,
                        'forecast': event.get('forecast', ''),
                        'previous': event.get('previous', '')
                    })
        
        return events[:5]
    except Exception as e:
        print(f"Economic calendar error: {e}")
        return []

# ========== FORMAT REPORT ==========
def format_report(crypto, forex_news, etf_news, events):
    """Format all data into Telegram message"""
    now = datetime.now(pytz.timezone('Asia/Jakarta'))
    report = f"📊 <b>DAILY MARKET REPORT</b>\n"
    report += f"📅 {now.strftime('%A, %d %B %Y %H:%M')} WIB\n"
    report += "─" * 30 + "\n\n"
    
    # Crypto Section
    report += "🚀 <b>TOP CRYPTO GAINERS (24H)</b>\n"
    if crypto:
        for i, coin in enumerate(crypto, 1):
            change = coin['change_24h']
            report += f"{i}. <b>{coin['symbol']}</b> - {coin['name']}\n"
            report += f"   💰 ${coin['price']:,.4f} | 📈 +{change:.2f}%\n"
    else:
        report += "⚠️ Data tidak tersedia\n"
    
    report += "\n" + "─" * 30 + "\n\n"
    
    # Forex Section
    report += "💱 <b>FOREX NEWS</b>\n"
    if forex_news:
        for i, news in enumerate(forex_news, 1):
            report += f"{i}. {news['title']}\n"
            report += f"   📰 {news['source']}\n"
    else:
        report += "⚠️ Data tidak tersedia\n"
    
    report += "\n" + "─" * 30 + "\n\n"
    
    # ETF Section
    report += "📈 <b>ETF & MARKET NEWS</b>\n"
    if etf_news:
        for i, news in enumerate(etf_news, 1):
            report += f"{i}. {news['title']}\n"
            report += f"   📰 {news['source']}\n"
    else:
        report += "⚠️ Data tidak tersedia\n"
    
    report += "\n" + "─" * 30 + "\n\n"
    
    # Economic Events
    report += "📅 <b>ECONOMIC CALENDAR (TODAY)</b>\n"
    if events:
        for i, event in enumerate(events, 1):
            impact_emoji = "🔴" if event['impact'] == 'High' else "🟡"
            report += f"{i}. {impact_emoji} {event['title']}\n"
            report += f"   🌍 {event['country']} | Impact: {event['impact']}\n"
            if event['forecast']:
                report += f"   Forecast: {event['forecast']} | Prev: {event['previous']}\n"
    else:
        report += "✅ Tidak ada event high impact hari ini\n"
    
    report += "\n" + "─" * 30 + "\n"
    report += "🤖 Generated by Hermes Agent\n"
    report += "Data: CoinGecko, Investing.com, ETF.com, ForexFactory"
    
    return report

# ========== MAIN ==========
def main():
    print("Fetching market data...")
    
    # Fetch all data
    crypto = get_crypto_gainers()
    forex_news = get_forex_news()
    etf_news = get_etf_market_news()
    events = get_economic_events()
    
    # Format report
    report = format_report(crypto, forex_news, etf_news, events)
    
    print(f"Report generated ({len(report)} chars)")
    
    # Send to Telegram
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        success = send_telegram_message(report)
        if success:
            print("✅ Report sent to Telegram successfully!")
        else:
            print("❌ Failed to send to Telegram")
            print("\n--- REPORT PREVIEW ---\n")
            print(report)
    else:
        print("⚠️ Telegram credentials not set")
        print("\n--- REPORT PREVIEW ---\n")
        print(report)

if __name__ == "__main__":
    main()
