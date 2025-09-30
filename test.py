import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("YELP_API_KEY")
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

def fetch_businesses(term, location, limit=50):
    """Fetch up to 240 results (50 per page) for a term/location."""
    all_results = []
    for offset in range(0, 250, 50):
        url = "https://api.yelp.com/v3/businesses/search"
        params = {"term": term, "location": location, "limit": limit, "offset": offset}
        resp = requests.get(url, headers=HEADERS, params=params)
        data = resp.json()
        if "businesses" not in data:
            break
        all_results.extend(data["businesses"])
        if len(data["businesses"]) < 50:
            break
    return all_results

def flatten_businesses(biz_list):
    rows = []
    for b in biz_list:
        rows.append({
            "id": b.get("id"),
            "name": b.get("name"),
            "rating": b.get("rating"),
            "review_count": b.get("review_count"),
            "price": b.get("price"),
            "categories": ",".join([c["title"] for c in b.get("categories", [])]),
            "latitude": b.get("coordinates", {}).get("latitude"),
            "longitude": b.get("coordinates", {}).get("longitude"),
            "city": b.get("location", {}).get("city"),
            "zip": b.get("location", {}).get("zip_code"),
            "is_closed": b.get("is_closed"),
            "url": b.get("url")
        })
    return pd.DataFrame(rows)

if __name__ == "__main__":
    terms = ["coffee", "pizza"]
    locations = ["Manhattan, NY", "Brooklyn, NY"]
    all_data = []

    for t in terms:
        for loc in locations:
            print(f"Fetching {t} in {loc}...")
            biz = fetch_businesses(t, loc)
            df = flatten_businesses(biz)
            df["term"] = t
            df["location_query"] = loc
            all_data.append(df)

    final_df = pd.concat(all_data, ignore_index=True)
    final_df.to_csv("yelp_businesses_raw.csv", index=False)
    print(f"Saved {len(final_df)} businesses to yelp_businesses_raw.csv")
