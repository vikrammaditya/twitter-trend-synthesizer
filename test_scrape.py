import requests
from bs4 import BeautifulSoup

def test_trends24():
    print("Testing trends24.in...")
    url = "https://trends24.in/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Look for typical structures, e.g. trend-card or trend-link
            cards = soup.find_all(class_="trend-card")
            print(f"Found {len(cards)} trend cards.")
            if cards:
                # Let's print trends from the first card (latest hour)
                first_card = cards[0]
                trends = first_card.find_all('li')
                print(f"Trends in the latest card (found {len(trends)}):")
                for i, trend in enumerate(trends[:10]):
                    a_tag = trend.find('a')
                    trend_text = a_tag.text if a_tag else trend.text
                    print(f"{i+1}. {trend_text.strip()}")
            else:
                print("No trend cards found. Let's see some of the HTML preview:")
                print(response.text[:1000])
        else:
            print("Failed to fetch.")
    except Exception as e:
        print(f"Error: {e}")

def test_getdaytrends():
    print("\nTesting getdaytrends.com...")
    url = "https://getdaytrends.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            trends = soup.find_all(class_="trend-link")
            print(f"Found {len(trends)} trend links.")
            for i, trend in enumerate(trends[:10]):
                print(f"{i+1}. {trend.text.strip()}")
        else:
            print("Failed to fetch.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_trends24()
    test_getdaytrends()
