from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from playwright.async_api import async_playwright, TimeoutError, Error
from bs4 import BeautifulSoup, Comment

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UrlRequest(BaseModel):
    url: str

@app.post("/api/scrape")
async def scrape_url(request: UrlRequest):
    try:
        clean_text = await fetch_and_clean_webpage(request.url)
        return {"text": clean_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def fetch_and_clean_webpage(url):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(url, wait_until='networkidle')
            
            await page.wait_for_timeout(2000)
            
            html_content = await page.content()
            await browser.close()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            unwanted_tags = [
                'script', 'style', 'header', 'footer', 'nav', 'aside',
                'iframe', 'ad', 'advertisement', 'meta', 'noscript',
                'figure', 'video', 'audio', 'canvas', 'svg'
            ]
            for tag in soup(unwanted_tags):
                tag.decompose()
            
            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract()
            
            text = soup.get_text(separator=' ')
            text = ' '.join(text.split())
            lines = [line.strip() for line in text.split('.') if line.strip()]
            clean_text = '. '.join(lines)
            
            return clean_text
    
    except (TimeoutError, Error) as e:
        return f"Error fetching the webpage: {e}"