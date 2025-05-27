import os
import re
import csv
import pandas as pd
from collections import Counter
from llm_evaluator import get_suspicious_files

def load_bug_results(project, csv_path):
    bug_results = {}
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                bug_id = row['bug_id']
                suspicious = get_suspicious_files(project, row['bug_id'], row['suspicious_files'])
                fixed = row['fixed_files'].split('.java')
                fixed = [(file + '.java').strip() for file in fixed[:-1]]
                
                bug_results[bug_id] = {
                    'suspicious': suspicious,
                    'fixed': fixed
                }
            except Exception as e:
                    print(e)
                
    return bug_results

def identify_successful_function_calls(bug_results, log_dir, output_path):
    results = []

    for filename in os.listdir(log_dir):
        bug_id = filename.replace("_log.txt", "").replace("bug_", "")
        if bug_id not in bug_results:
            continue
        
        suspicious_files = bug_results[bug_id]["suspicious"]
        fixed_files = bug_results[bug_id]["fixed"]
        if not fixed_files:
            continue

        with open(os.path.join(log_dir, filename), 'r', encoding='utf-8') as f:
            lines = f.readlines()

        current_function = None
        current_iteration = None

        for i, line in enumerate(lines):
            # Track iteration
            match_iter = re.search(r'Iteration (\d+)', line)
            if match_iter:
                current_iteration = int(match_iter.group(1))

            # Track function call
            match_call = re.search(r'Function called: (\w+)', line)
            if match_call:
                current_function = match_call.group(1)

            # Track function response
            match_response = re.search(r'Function response for \w+: (.+)', line)
            if match_response and current_function:
                try:
                    response_text = match_response.group(1)
                    if response_text.startswith("[") or response_text.startswith("{"):
                        response_data = eval(response_text)

                        # Convert dict to list of values if needed
                        if isinstance(response_data, dict):
                            response_files = list(response_data.values())
                        else:
                            response_files = response_data

                        if not isinstance(response_files, list):
                            continue

                        # Match fixed files
                        number_of_correct_buggy_files = calculate_hit_at_10(suspicious_files, fixed_files)
                        if number_of_correct_buggy_files>0:
                            for fixed_file in fixed_files:
                                if any(fixed_file in str(resp_file) for resp_file in response_files):
                                    results.append((bug_id, current_function, fixed_file, current_iteration))
                                    break  # Only log the first match per function response
                except Exception as e:
                    print(f"[Warning] Failed to parse response in bug {bug_id}: {e}")

    # Save results
    df = pd.DataFrame(results, columns=["bug_id", "function_call", "fixed_file", "iteration"])
    df.to_csv(output_path, index=False)
    print(f"Logged successful function calls with iterations to {output_path}")

def parse_logs(log_dir):
    function_usage = {}
    function_count = 0
    bug_count = 0
    for filename in os.listdir(log_dir):
        bug_id = filename.replace("_log.txt", "").replace("bug_", "")
        path = os.path.join(log_dir, filename)
        functions = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                match = re.search(r'Function called: (\w+)', line)
                if match:
                    functions.append(match.group(1))
        function_usage[bug_id] = functions
        function_count = function_count + len(functions)
        bug_count = bug_count + 1
    print('average number of functions called', (function_count/bug_count))
    return function_usage


def calculate_hit_at_10(suspicious, fixed):
    if not fixed:
        return 0
    return len(set(suspicious[:10]) & set(fixed))


def analyze_function_contribution(bug_results, function_usage):
    successful_functions = Counter()
    failed_functions = Counter()

    for bug_id, result in bug_results.items():
        suspicious = result['suspicious']
        fixed = result['fixed']
        number_of_correct_buggy_files = calculate_hit_at_10(suspicious, fixed)

        if bug_id in function_usage:
            if number_of_correct_buggy_files > 0:
                successful_functions.update(function_usage[bug_id])
            else:
                failed_functions.update(function_usage[bug_id])
    
    return successful_functions, failed_functions


def main():
    projects = ['aspectj','birt','eclipse','jdt','swt','tomcat']
    root_dir = "result-3-default-temp/"
    for project in projects:
        print('project',project)
        log_dir =  root_dir+project
        csv_path = root_dir+"output_files/"+project+"-ranking-using-function-call.csv"
        output_path = project+"-successful-function-hits.csv"

        bug_results = load_bug_results(project, csv_path)
        function_usage = parse_logs(log_dir)
        successful_fn, failed_fn = analyze_function_contribution(bug_results, function_usage)

        identify_successful_function_calls(bug_results, log_dir, output_path)

        print("\n--- Most Used Functions in Successful Bugs ---")
        for fn, count in successful_fn.most_common():
            print(f"{fn}: {count}")

        print("\n--- Most Used Functions in Failed Bugs ---")
        for fn, count in failed_fn.most_common():
            print(f"{fn}: {count}")

        summary = pd.DataFrame({
            'Function': list(set(successful_fn.keys()) | set(failed_fn.keys())),
            'Success_Count': [successful_fn.get(f, 0) for f in set(successful_fn.keys()) | set(failed_fn.keys())],
            'Failure_Count': [failed_fn.get(f, 0) for f in set(successful_fn.keys()) | set(failed_fn.keys())]
        }).sort_values(by='Success_Count', ascending=False)

        print("\n--- Function Contribution Summary ---")
        print(summary)

if __name__ == "__main__":
    main()
