import json
import requests
import time

def run_benchmark_simple():
    """Run benchmark queries and generate submission.json in the required format"""
    
    # Load benchmark queries
    with open('benchmark_queries.json', 'r') as f:
        benchmark_data = json.load(f)
    
    base_url = "http://localhost:8001"
    results = {}
    
    print("Running benchmarks for submission.json...")
    print("=" * 50)
    
    for query_id, query_info in benchmark_data['queries'].items():
        query_text = query_info['query']
        query_type = query_info['type']
        
        print(f"Query {query_id}: {query_type} search for '{query_text}'")
        
        # Construct API endpoint
        endpoint = f"{base_url}/search/{query_type}"
        params = {'q': query_text, 'limit': 500}
        
        try:
            response = requests.get(endpoint, params=params)
            
            if response.status_code == 200:
                data = response.json()
                medicine_names = []
                
                # Extract just the medicine names
                for result in data.get('results', []):
                    name = result.get('name', '').strip()
                    if name and name not in medicine_names:  # Avoid duplicates
                        medicine_names.append(name)
                
                results[query_id] = medicine_names
                print(f"  ✅ Found {len(medicine_names)} unique medicines")
                
                # Show first few results
                for i, name in enumerate(medicine_names[:5]):
                    print(f"    {i+1}. {name}")
                if len(medicine_names) > 5:
                    print(f"    ... and {len(medicine_names) - 5} more")
                    
            else:
                print(f"  ❌ Error: HTTP {response.status_code}")
                results[query_id] = []
                
        except Exception as e:
            print(f"  ❌ Exception: {str(e)}")
            results[query_id] = []
        
        print()
    
    # Generate submission.json in the required format
    submission = {
        "results": results
    }
    
    # Save submission.json
    with open('submission.json', 'w') as f:
        json.dump(submission, f, indent=2)
    
    print("=" * 50)
    print("Submission Summary:")
    total_medicines = sum(len(medicines) for medicines in results.values())
    non_empty_queries = len([q for q in results.values() if q])
    
    print(f"✅ Queries with results: {non_empty_queries}/10")
    print(f"📊 Total medicine names: {total_medicines}")
    print(f"📄 Format: Simple medicine names list")
    print("\n✅ submission.json generated in required format!")
    
    # Show summary of each query
    print("\nQuery Results Summary:")
    for qid, medicines in results.items():
        query_info = benchmark_data['queries'][qid]
        print(f"  Query {qid} ({query_info['type']} - '{query_info['query']}'): {len(medicines)} results")

if __name__ == "__main__":
    run_benchmark_simple()