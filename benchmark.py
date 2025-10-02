import json
import time
import requests
import statistics
from typing import Dict, List
import os

class BenchmarkRunner:
    def __init__(self, api_base_url: str = "http://localhost:8001"):
        self.api_base_url = api_base_url
        self.results = {}

    def load_benchmark_queries(self, file_path: str) -> List[Dict]:
        """Load benchmark queries from JSON file"""
        with open(file_path, 'r') as f:
            data = json.load(f)
                
        queries = data.get('queries', {})
        # Convert the queries object to a list format expected by the code
        query_list = []
        for query_id, query_data in queries.items():
            query_list.append({
                'id': int(query_id),
                'type': query_data['type'],
                'query': query_data['query']
            })
        return query_list

    def run_single_query(self, query_type: str, query: str, iterations: int = 5) -> Dict:
        """Run a single query multiple times and measure performance"""
        endpoint = f"/search/{query_type}"
        url = f"{self.api_base_url}{endpoint}"

        latencies = []
        results = None

        for _ in range(iterations):
            start_time = time.time()
            try:
                response = requests.get(url, params={"q": query}, timeout=10)
                response.raise_for_status()
                results = response.json()
            except Exception as e:
                print(f"Error running query {query_type}:{query} - {e}")
                continue

            end_time = time.time()
            latency = (end_time - start_time) * 1000  # Convert to milliseconds
            latencies.append(latency)

        if latencies:
            return {
                "avg_latency_ms": statistics.mean(latencies),
                "min_latency_ms": min(latencies),
                "max_latency_ms": max(latencies),
                "std_dev_ms": statistics.stdev(latencies) if len(latencies) > 1 else 0,
                "results_count": len(results.get("results", [])) if results else 0,
                "results": [r.get("name") for r in results.get("results", [])] if results else []
            }
        else:
            return {
                "error": "Failed to run query",
                "results": []
            }

    def run_benchmarks(self, queries_file: str, output_file: str = "benchmark_results.json"):
        """Run all benchmark queries and save results"""
        queries = self.load_benchmark_queries(queries_file)

        print("Running benchmarks...")
        benchmark_data = {}

        for query in queries:
            query_id = str(query['id'])
            query_type = query['type']
            query_text = query['query']

            print(f"Running query {query_id}: {query_type} - '{query_text}'")

            result = self.run_single_query(query_type, query_text)

            if query_id not in benchmark_data:
                benchmark_data[query_id] = []

            benchmark_data[query_id].extend(result.get("results", []))

            # Remove duplicates while preserving order
            benchmark_data[query_id] = list(dict.fromkeys(benchmark_data[query_id]))

        # Save benchmark results
        with open(output_file, 'w') as f:
            json.dump({"results": benchmark_data}, f, indent=2)

        print(f"Benchmark results saved to {output_file}")
        return benchmark_data

    def generate_submission_json(self, benchmark_results: Dict, output_file: str = "submission.json"):
        """Generate submission.json in the required format"""
        submission_data = {
            "results": benchmark_results
        }

        with open(output_file, 'w') as f:
            json.dump(submission_data, f, indent=2)

        print(f"Submission file generated: {output_file}")

def main():
    # Check if API is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("API server is not running. Please start the server first.")
            return
    except:
        print("Cannot connect to API server. Please start the server first.")
        return

    # Run benchmarks
    runner = BenchmarkRunner()

    # Path to benchmark queries
    benchmark_file = "benchmark_queries.json"

    if not os.path.exists(benchmark_file):
        print(f"Benchmark file not found: {benchmark_file}")
        return

    # Run benchmarks and generate submission
    results = runner.run_benchmarks(benchmark_file)
    runner.generate_submission_json(results)

if __name__ == "__main__":
    main()
