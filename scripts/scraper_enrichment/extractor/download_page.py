# download_page.py
import requests
from bs4 import BeautifulSoup

def download_and_clean(url):
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    # Elimina scripts y estilos
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()
    text = soup.get_text(separator=' ', strip=True)
    return text 