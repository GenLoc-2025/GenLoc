import os
import csv
import json
import sys
import re
from datetime import datetime

def tokenize_filename(filename):
    normalized = re.sub(r'[\./]', ' ', filename) # Replace '/' and '.' with spaces, then split by whitespace
    tokens = normalized.split()
    return set(token.lower() for token in tokens if token)

def jaccard_similarity(set1, set2):
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union > 0 else 0

def find_most_similar_file(target_file, file_list):
    target_tokens = tokenize_filename(target_file)
    similarity_scores = []
    for filename in file_list:
        file_tokens = tokenize_filename(filename)
        similarity = jaccard_similarity(target_tokens, file_tokens)
        similarity_scores.append((filename, similarity))
    
    similarity_scores.sort(key=lambda x: x[1], reverse=True)
    
    if similarity_scores:
        most_similar, score = similarity_scores[0]
        return most_similar, score
    else:
        return None, 0

def parse_json(json_data):
    try:
        data = json.loads(json_data)
        bug_report_analysis = data.get("analysis_of_the_bug_report", "")
        results = []
        for item in data["ranked_list"]:
            file_name = item.get("file", "")
            justification = item.get("justification", "")
            results.append((file_name, justification))        
        
        return bug_report_analysis, results
    except json.JSONDecodeError as e:
        print("Failed to parse JSON:", e)
        return "",[]
    except KeyError as e:
        print("Missing expected key:", e)
        return "",[]

def extract_filename(full_path):
    if not full_path.endswith(".java"):
        full_path = full_path + '.java'
    base_name = os.path.basename(full_path)
    return base_name.split(".")[-2] + '.' + base_name.split(".")[-1]

def get_suspicious_files(project, bug_id, data):
    suspicious_files = []
    json_file = project + '_bug_data/' + bug_id + '_filewise_method_data.json'
    
    with open(json_file, 'r') as current_file:
        file_wise_method_data = json.load(current_file)

    seen_filenames = set()
    bug_report_analysis, results = parse_json(data)
    for suspicious_filename, justification in results:
        if suspicious_filename in seen_filenames:
            continue
        seen_filenames.add(suspicious_filename)
        
        found = False
        for current_file in file_wise_method_data:
            current_filepath = current_file.get("filepath")
            if current_filepath == suspicious_filename:
                suspicious_files.append({
                    'file': current_filepath,
                    'justification': justification
                })
                found = True
                break
        
        if not found:
            partial_matches = []
            for current_file in file_wise_method_data:
                current_filename = current_file.get("filename")
                if current_filename == extract_filename(suspicious_filename):
                    current_filepath = current_file.get("filepath")
                    partial_matches.append(current_filepath)
            most_similar_file, similarity_score = find_most_similar_file(suspicious_filename, partial_matches)
            if most_similar_file:
                suspicious_files.append({
                    'file': most_similar_file,
                    'justification': justification
                })

    suspicious_files_json = json.dumps({
        'ranked_list': suspicious_files
    })

    return bug_report_analysis, suspicious_files_json

def process_bug_results(project, csv_path):
    bug_results = {}
    with open(csv_path, newline='', encoding='utf-8', errors='ignore') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            bug_id = row['bug_id']
            try:
                bug_report_analysis, suspicious_files = get_suspicious_files(project, row['bug_id'], row['suspicious_files'])
                fixed_files = row['fixed_files'].split('.java')
                fixed_files = [(file + '.java').strip() for file in fixed_files[:-1]]
                
                bug_results[bug_id] = {
                    'bug_report_analysis': bug_report_analysis,
                    'suspicious_files': suspicious_files,
                    'fixed_files': fixed_files
                }
            except Exception as e:
                    print(e)
                
    return bug_results

def prepare_final_ranked_list(project, csv_path):
    bug_results = process_bug_results(project, csv_path)
    output_csv = project + '_final_ranked_output.csv'

    with open(output_csv, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(['bug_id', 'bug_report_analysis', 'suspicious_files', 'fixed_files'])

        for bug_id, result in bug_results.items():
            analysis = result['bug_report_analysis']
            suspicious_files_json = result['suspicious_files']
            fixed_files = ','.join(result['fixed_files'])
            writer.writerow([bug_id, analysis, suspicious_files_json, fixed_files])

    print(f"Final results written to: {output_csv}")


if __name__ == "__main__":
    root_dir = ''#'llm-baseline/'
    project = sys.argv[1]
    start_time = datetime.now()
    input_filename = root_dir+project+'-ranking-using-function-call.csv'
    prepare_final_ranked_list(project, input_filename)
    end_time = datetime.now()

    print('total time', end_time-start_time)