import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration from environment variables
CSV_PATH = os.getenv("CSV_PATH", "/Users/jasonmartinez/Downloads/yelp_etl/Yelp-Bi-Project/yelp_businesses_raw.csv")
DB_NAME = os.getenv("DB_NAME", "yelp_bi")
DB_USER = os.getenv("DB_USER", "jasonmartinez")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)
cur = conn.cursor()

# Create a temp table with NO primary key (avoids duplicate ID errors)
cur.execute("""
DROP TABLE IF EXISTS tmp_biz;
CREATE TEMP TABLE tmp_biz (
    id TEXT,
    name TEXT,
    rating NUMERIC,
    review_count INT,
    price TEXT,
    categories TEXT,
    latitude NUMERIC,
    longitude NUMERIC,
    city TEXT,
    zip TEXT,
    is_closed BOOLEAN,
    url TEXT,
    term TEXT,
    location_query TEXT,
    pulled_at TIMESTAMP DEFAULT NOW()
);
""")

# Load CSV into temp table
with open(CSV_PATH, "r", encoding="utf-8") as f:
    cur.copy_expert("""
        COPY tmp_biz (id,name,rating,review_count,price,categories,latitude,longitude,city,zip,is_closed,url,term,location_query)
        FROM STDIN WITH (FORMAT CSV, HEADER TRUE, DELIMITER ',');
    """, f)

# Insert into the real table, skipping duplicates
cur.execute("""
INSERT INTO raw.businesses
(id,name,rating,review_count,price,categories,latitude,longitude,city,zip,is_closed,url,term,location_query)
SELECT DISTINCT ON (id)
       id,name,rating,review_count,price,categories,latitude,longitude,city,zip,is_closed,url,term,location_query
FROM tmp_biz
ORDER BY id, pulled_at DESC
ON CONFLICT (id) DO NOTHING;
""")

conn.commit()
cur.close()
conn.close()

print("✅ Data loaded into raw.businesses")
