import requests
from bs4 import BeautifulSoup

def inspect_trends24():
    url = "https://trends24.in/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    
    with open("trends24_raw.html", "w", encoding="utf-8") as f:
        f.write(response.text)
        
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Let's inspect what containers or classes are present in the DOM
    print("Div classes containing 'trend':")
    div_classes = set()
    for div in soup.find_all('div'):
        cls = div.get('class')
        if cls:
            for c in cls:
                if 'trend' in c:
                    div_classes.add(c)
    print(list(div_classes))
    
    # Let's print list items
    li_elements = soup.find_all('li')
    print(f"Total list items found: {len(li_elements)}")
    
    # Check if there's any trend list
    ol_elements = soup.find_all('ol')
    print(f"Total ordered lists found: {len(ol_elements)}")
    
    # Let's write the first card text if any
    with open("trends24_summary.txt", "w", encoding="utf-8") as f:
        f.write(f"Ordered lists: {len(ol_elements)}\n")
        for i, ol in enumerate(ol_elements[:3]):
            f.write(f"\nOL #{i+1}:\n")
            for li in ol.find_all('li'):
                f.write(f"  - {li.text.strip()}\n")

if __name__ == "__main__":
    inspect_trends24()
