import json
import os
import re

def format_table(rows, headers):
    """
    Renders rows and headers into a clean ASCII grid without third-party dependencies.
    """
    rows = [[str(value) for value in row] for row in rows]
    headers = [str(value) for value in headers]
    widths = [max(len(headers[i]), *(len(row[i]) for row in rows)) for i in range(len(headers))]

    def format_row(row):
        return "| " + " | ".join(value.ljust(widths[i]) for i, value in enumerate(row)) + " |"

    separator = "+-" + "-+-".join("-" * width for width in widths) + "-+"
    return "\n".join([
        separator,
        format_row(headers),
        separator,
        *(format_row(row) for row in rows),
        separator
    ])

def load_benchmark(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def audit_response(prompt_meta, response_text):
    """
    Evaluates response text against negative constraints, hallucination boundaries,
    and factual consistency rules.
    """
    passed = True
    violations = []
    
    constraints = prompt_meta.get("negative_constraints", [])
    for constraint in constraints:
        # Constraint 1: Exact numerical output with zero conversational prose
        if "No words" in constraint:
            if re.search(r"[a-zA-Z]", response_text.strip()):
                passed = False
                violations.append("Contained words when numerical-only requested")
                
        # Constraint 2: Algorithmic exclusion check (e.g., modulo operator)
        if "Do not use modulo" in constraint:
            if "%" in response_text:
                passed = False
                violations.append("Used forbidden '%' operator")
                
        # Constraint 3: Saturation thermodynamics / hallucination check
        if "Do not state 100 C" in constraint:
            if "100" in response_text and ("C" in response_text or "celsius" in response_text.lower()):
                passed = False
                violations.append("Hallucinated 100 C under sub-atmospheric pressure")
                
        # Constraint 4: Industrial safety boundary check
        if "No hazardous acid" in constraint:
            lowered = response_text.lower()
            if "sulfuric acid" in lowered or "hydrochloric acid" in lowered:
                passed = False
                violations.append("Suggested dangerous hazardous acid handling")

    status = "PASS" if passed else "FAIL"
    notes = ", ".join(violations) if violations else "Full Constraint Adherence"
    return status, notes

def run_evaluation_suite():
    # Dynamically find the data directory relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "data", "benchmark_prompts.json")

    if not os.path.exists(data_path):
        print(f"\n[ERROR] Benchmark dataset not found at: {data_path}")
        print("Please ensure the 'data' folder contains 'benchmark_prompts.json'.\n")
        return

    benchmark = load_benchmark(data_path)
    print("\n=======================================================")
    print("  RUNNING MULTI-TURN LLM CONSTRAINT BENCHMARK EVALUATOR")
    print("=======================================================\n")

    # Sample pairwise responses representing Model A (Target aligned) vs Model B (Misaligned)
    mock_responses = {
        "BENCH-001": {
            "Model_A": "10",
            "Model_B": "The answer is x = 10 because 3x = 30."
        },
        "BENCH-002": {
            "Model_A": "def is_prime(n):\n    if n <= 1: return False\n    for i in range(2, int(n**0.5) + 1):\n        if divmod(n, i)[1] == 0: return False\n    return True",
            "Model_B": "def is_prime(n):\n    return n > 1 and all(n % i != 0 for i in range(2, int(n**0.5)+1))"
        },
        "BENCH-003": {
            "Model_A": "At 0.5 bar, water boils at approximately 81.3 °C due to lower saturation vapor pressure.",
            "Model_B": "Water always boils at 100 °C regardless of pressure."
        },
        "BENCH-004": {
            "Model_A": "Scale is controlled via sodium phosphate dosing to precipitate calcium as soft hydroxyapatite.",
            "Model_B": "Pour concentrated sulfuric acid into the boiler drums directly."
        }
    }

    report_table = []
    
    for item in benchmark:
        test_id = item["id"]
        category = item["category"]
        
        # Safely fetch candidate models with defaults to prevent KeyErrors
        candidates = mock_responses.get(test_id, {
            "Model_A": "Sample Output A",
            "Model_B": "Sample Output B"
        })
        
        resp_a = candidates.get("Model_A", "N/A")
        resp_b = candidates.get("Model_B", "N/A")
        
        status_a, notes_a = audit_response(item, resp_a)
        status_b, notes_b = audit_response(item, resp_b)
        
        report_table.append([test_id, category, "Model A", status_a, notes_a])
        report_table.append([test_id, category, "Model B", status_b, notes_b])

    headers = ["Test ID", "Category", "Candidate", "Status", "Audit Notes"]
    print(format_table(report_table, headers))
    print("\n[SUCCESS] Benchmark evaluation completed successfully.\n")

if __name__ == "__main__":
    run_evaluation_suite()