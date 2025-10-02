from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import os
from dotenv import load_dotenv
import time
import re

load_dotenv()

app = FastAPI(title="Medicine Search API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "medicine_search"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "password"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5433")
    )

@app.get("/", response_class=HTMLResponse)
async def root():
    return """<!DOCTYPE html>
<html>
<head>
    <title>Medicine Search Portal</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 20px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; text-align: center; margin-bottom: 30px; font-size: 2.5em; font-weight: 700; }
        .search-section { margin-bottom: 30px; }
        .search-box { display: flex; margin: 20px 0; gap: 10px; }
        input[type="text"] { flex: 1; padding: 15px 20px; font-size: 18px; border: 3px solid #3498db; border-radius: 15px; outline: none; transition: all 0.3s; }
        input[type="text"]:focus { border-color: #e74c3c; box-shadow: 0 0 0 3px rgba(231, 76, 60, 0.1); }
        .search-btn-main { padding: 15px 30px; font-size: 18px; background: #3498db; color: white; border: none; border-radius: 15px; cursor: pointer; transition: all 0.3s; font-weight: 600; }
        .search-btn-main:hover { background: #2980b9; transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
        .search-types { display: flex; justify-content: center; gap: 15px; flex-wrap: wrap; margin: 20px 0; }
        .search-btn { padding: 12px 25px; background: #ecf0f1; color: #2c3e50; border: 2px solid #bdc3c7; border-radius: 25px; cursor: pointer; transition: all 0.3s; font-weight: 600; font-size: 16px; }
        .search-btn:hover { background: #d5dbdb; transform: translateY(-2px); }
        .search-btn.active { background: #e74c3c; color: white; border-color: #c0392b; box-shadow: 0 5px 15px rgba(231, 76, 60, 0.3); }
        .results { margin-top: 30px; }
        .medicine { border: 2px solid #ecf0f1; padding: 25px; margin: 20px 0; border-radius: 15px; background: #fafafa; transition: all 0.3s; position: relative; }
        .medicine:hover { border-color: #3498db; box-shadow: 0 10px 25px rgba(0,0,0,0.1); transform: translateY(-3px); }
        .medicine h4 { color: #2c3e50; margin-bottom: 15px; font-size: 1.4em; display: flex; align-items: center; gap: 10px; }
        .medicine p { margin: 10px 0; font-size: 16px; line-height: 1.5; }
        .medicine strong { color: #34495e; }
        .loading { text-align: center; color: #7f8c8d; font-size: 1.3em; padding: 40px; }
        .score { background: linear-gradient(45deg, #3498db, #e74c3c); color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8em; font-weight: bold; }
        .search-info { text-align: center; margin: 20px 0; padding: 15px; background: #ecf0f1; border-radius: 10px; }
        .no-results { text-align: center; font-size: 1.2em; color: #e74c3c; padding: 40px; }
        @media (max-width: 768px) {
            .container { padding: 20px; }
            h1 { font-size: 2em; }
            .search-types { justify-content: center; }
            .search-btn { padding: 10px 15px; font-size: 14px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏥 Medicine Search Portal</h1>
        <div class="search-section">
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="Search medicines (e.g., aspirin, paracetamol, ibuprofen)..." autocomplete="off">
                <button class="search-btn-main" onclick="searchMedicines()">🔍 Search</button>
            </div>
            <div class="search-types">
                <button class="search-btn active" id="prefix-btn" onclick="setSearchType('prefix')">🎯 Prefix</button>
                <button class="search-btn" id="substring-btn" onclick="setSearchType('substring')">📝 Contains</button>
                <button class="search-btn" id="fulltext-btn" onclick="setSearchType('fulltext')">📚 Smart</button>
                <button class="search-btn" id="fuzzy-btn" onclick="setSearchType('fuzzy')">🔄 Fuzzy</button>
            </div>
        </div>
        <div id="results" class="results"></div>
    </div>
    <script>
        let currentSearchType = 'prefix';
        
        function setSearchType(type) {
            currentSearchType = type;
            document.querySelectorAll('.search-btn').forEach(btn => btn.classList.remove('active'));
            document.getElementById(type + '-btn').classList.add('active');
        }
        
        async function searchMedicines() {
            const query = document.getElementById('searchInput').value.trim();
            if (!query) {
                alert('⚠️ Please enter a medicine name to search');
                return;
            }
            
            document.getElementById('results').innerHTML = '<div class="loading">🔍 Searching medicines database...</div>';
            
            try {
                const response = await fetch(`/search/${currentSearchType}?q=${encodeURIComponent(query)}`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                
                const resultsDiv = document.getElementById('results');
                if (data.results && data.results.length > 0) {
                    const searchTypeNames = {
                        'prefix': 'Prefix Search',
                        'substring': 'Contains Search', 
                        'fulltext': 'Smart Search',
                        'fuzzy': 'Fuzzy Search'
                    };
                    
                    resultsDiv.innerHTML = `
                        <div class="search-info">
                            <strong>✅ Found ${data.count} medicines using ${searchTypeNames[data.type]} (${data.execution_time_ms}ms)</strong>
                        </div>
                        ${data.results.map(med => `
                            <div class="medicine">
                                <h4>
                                    💊 ${med.name}
                                    ${med.rank ? `<span class="score">Rank: ${med.rank.toFixed(2)}</span>` : ''}
                                    ${med.similarity_score ? `<span class="score">${(med.similarity_score * 100).toFixed(0)}% Match</span>` : ''}
                                </h4>
                                <p><strong>🏭 Manufacturer:</strong> ${med.manufacturer_name || 'Not specified'}</p>
                                <p><strong>💊 Type:</strong> ${med.type || 'Not specified'}</p>
                                <p><strong>💰 Price:</strong> ${med.price || 'Not specified'}</p>
                                <p><strong>📦 Pack Size:</strong> ${med.pack_size_label || 'Not specified'}</p>
                                <p><strong>🧪 Composition:</strong> ${med.short_composition || 'Not specified'}</p>
                            </div>
                        `).join('')}
                    `;
                } else {
                    resultsDiv.innerHTML = `
                        <div class="no-results">
                            ❌ No medicines found for "${query}"<br>
                            💡 Try different search terms or switch search types
                        </div>
                    `;
                }
            } catch (error) {
                document.getElementById('results').innerHTML = `
                    <div class="no-results">
                        ⚠️ Search error occurred<br>
                        Please try again or contact support
                    </div>
                `;
                console.error('Search error:', error);
            }
        }
        
        document.getElementById('searchInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchMedicines();
            }
        });
        
        // Auto-focus search input
        document.getElementById('searchInput').focus();
    </script>
</body>
</html>"""

@app.get("/health")
async def health_check():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM medicines")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return {"status": "healthy", "medicines_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

@app.get("/search/prefix")
async def search_prefix(q: str = Query(..., min_length=1, max_length=100)):
    start_time = time.time()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, manufacturer_name, type, price, pack_size_label, short_composition
            FROM medicines
            WHERE name ILIKE %s || '%%'
            ORDER BY name
            LIMIT 100
        """, (q,))
        results = []
        for row in cursor.fetchall():
            results.append({
                "name": row[0],
                "manufacturer_name": row[1],
                "type": row[2],
                "price": row[3],
                "pack_size_label": row[4],
                "short_composition": row[5]
            })
        cursor.close()
        conn.close()
        execution_time = time.time() - start_time
        return {
            "query": q,
            "type": "prefix",
            "results": results,
            "count": len(results),
            "execution_time_ms": round(execution_time * 1000, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/search/substring")
async def search_substring(q: str = Query(..., min_length=1, max_length=100)):
    start_time = time.time()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, manufacturer_name, type, price, pack_size_label, short_composition
            FROM medicines
            WHERE name ILIKE '%%' || %s || '%%'
            ORDER BY name
            LIMIT 100
        """, (q,))
        results = []
        for row in cursor.fetchall():
            results.append({
                "name": row[0],
                "manufacturer_name": row[1],
                "type": row[2],
                "price": row[3],
                "pack_size_label": row[4],
                "short_composition": row[5]
            })
        cursor.close()
        conn.close()
        execution_time = time.time() - start_time
        return {
            "query": q,
            "type": "substring",
            "results": results,
            "count": len(results),
            "execution_time_ms": round(execution_time * 1000, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/search/fulltext")
async def search_fulltext(q: str = Query(..., min_length=1, max_length=100)):
    start_time = time.time()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Smart search with ranking based on position and exact matches
        cursor.execute("""
            SELECT name, manufacturer_name, type, price, pack_size_label, short_composition,
                   CASE 
                       WHEN LOWER(name) = LOWER(%s) THEN 1.0
                       WHEN LOWER(name) LIKE LOWER(%s) || ' %%' THEN 0.9
                       WHEN LOWER(name) LIKE '%% ' || LOWER(%s) || ' %%' THEN 0.8
                       WHEN LOWER(name) LIKE '%% ' || LOWER(%s) THEN 0.7
                       WHEN LOWER(name) LIKE LOWER(%s) || '%%' THEN 0.6
                       ELSE 0.5 
                   END as rank
            FROM medicines
            WHERE LOWER(name) LIKE '%%' || LOWER(%s) || '%%'
            ORDER BY rank DESC, name
            LIMIT 100
        """, (q, q, q, q, q, q))
        results = []
        for row in cursor.fetchall():
            results.append({
                "name": row[0],
                "manufacturer_name": row[1],
                "type": row[2],
                "price": row[3],
                "pack_size_label": row[4],
                "short_composition": row[5],
                "rank": float(row[6])
            })
        cursor.close()
        conn.close()
        execution_time = time.time() - start_time
        return {
            "query": q,
            "type": "fulltext",
            "results": results,
            "count": len(results),
            "execution_time_ms": round(execution_time * 1000, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

def calculate_similarity(s1, s2):
    """Simple similarity calculation without pg_trgm extension"""
    s1, s2 = s1.lower(), s2.lower()
    if s1 == s2:
        return 1.0
    
    # Levenshtein distance approximation
    len1, len2 = len(s1), len(s2)
    if len1 == 0: return 0.0
    if len2 == 0: return 0.0
    
    # Simple character overlap
    common_chars = set(s1) & set(s2)
    max_len = max(len1, len2)
    overlap_score = len(common_chars) / max_len
    
    # Length difference penalty
    length_diff = abs(len1 - len2) / max_len
    length_score = 1 - length_diff
    
    # Substring bonus
    substring_bonus = 0
    if s1 in s2 or s2 in s1:
        substring_bonus = 0.3
    
    return min(1.0, overlap_score * 0.6 + length_score * 0.4 + substring_bonus)

@app.get("/search/fuzzy")
async def search_fuzzy(q: str = Query(..., min_length=1, max_length=100)):
    start_time = time.time()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Get a broader set of potential matches for fuzzy search
        cursor.execute("""
            SELECT name, manufacturer_name, type, price, pack_size_label, short_composition
            FROM medicines
            WHERE LOWER(name) LIKE '%%' || LOWER(%s) || '%%'
               OR LOWER(name) LIKE '%%' || LOWER(SUBSTRING(%s, 1, 3)) || '%%'
            LIMIT 200
        """, (q, q))
        
        raw_results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Calculate similarity scores in Python
        results = []
        for row in raw_results:
            similarity = calculate_similarity(q, row[0])
            if similarity > 0.1:  # Filter threshold
                results.append({
                    "name": row[0],
                    "manufacturer_name": row[1],
                    "type": row[2],
                    "price": row[3],
                    "pack_size_label": row[4],
                    "short_composition": row[5],
                    "similarity_score": similarity
                })
        
        # Sort by similarity score
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        results = results[:100]  # Limit to 100
        
        execution_time = time.time() - start_time
        return {
            "query": q,
            "type": "fuzzy",
            "results": results,
            "count": len(results),
            "execution_time_ms": round(execution_time * 1000, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)