import os
import csv
import json
import sys
import re

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
        file_names = [item["file"] for item in data["ranked_list"]]
        
        return file_names
    except json.JSONDecodeError as e:
        print("Failed to parse JSON:", e)
        return []
    except KeyError as e:
        print("Missing expected key:", e)
        return []

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

    unique_suspicious_filenames = []
    for suspicious_filename in parse_json(data):
        if suspicious_filename not in unique_suspicious_filenames:
            unique_suspicious_filenames.append(suspicious_filename)
    
    for suspicious_filename in unique_suspicious_filenames:
        found = False
        for current_file in file_wise_method_data:
            current_filepath = current_file.get("filepath")
            if current_filepath == suspicious_filename:
                suspicious_files.append(current_filepath)
                found = True
                break
        if (found == False):
            # print("no exact match",suspicious_filename)
            partial_matches = []
            for current_file in file_wise_method_data:
                current_filename = current_file.get("filename")
                if current_filename == extract_filename(suspicious_filename):
                    current_filepath = current_file.get("filepath")
                    partial_matches.append(current_filepath)
            most_similar_file, similarity_score = find_most_similar_file(suspicious_filename, partial_matches)
            # print('most similar file', suspicious_filename, most_similar_file, similarity_score)
            
            if most_similar_file:
                suspicious_files.append(most_similar_file)
            # else:
            #     print('no match',suspicious_filename)
    
    return suspicious_files  

def process_bug_results(project, csv_path):
    bug_results = {}
    with open(csv_path, newline='', encoding='utf-8', errors='ignore') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            bug_id = row['bug_id']
            try:
                suspicious_files = get_suspicious_files(project, row['bug_id'], row['suspicious_files'])
                fixed_files = row['fixed_files'].split('.java')
                fixed_files = [(file + '.java').strip() for file in fixed_files[:-1]]
                
                bug_results[bug_id] = {
                    'suspicious_files': suspicious_files,
                    'fixed_files': fixed_files
                }
            except Exception as e:
                    print(e)
                
    return bug_results

def calculate_accuracy_at_k(project, csv_path):
    bug_results = process_bug_results(project, csv_path)
    for top in [1,5,10]:
        count = 0
        total_bug = 0
        for bug_id, result in bug_results.items():
            suspicious_files = result['suspicious_files']
            fixed_files = result['fixed_files']

            if len(suspicious_files)<10:
                print('below 10 files!', bug_id, len(suspicious_files))
                
            for fixed_file in fixed_files:
                if fixed_file in suspicious_files[0:top]:
                    print(bug_id,fixed_file)
                    count = count + 1
                    break
            total_bug = total_bug + 1
        print('accuracy@', top, count, total_bug, (count*100/total_bug))

def calculate_mean_reciprocal_rank_at_k(project, csv_path):
    bug_results = process_bug_results(project, csv_path)

    for top in [10]:
        total_bug = 0
        inverse_rank = 0
        for bug_id, result in bug_results.items():
            suspicious_files = result['suspicious_files']
            length_of_suspicious_files = len(suspicious_files)
            fixed_files = result['fixed_files']
            minimum_length = min(top,length_of_suspicious_files)

            for i in range(minimum_length):
                if(suspicious_files[i] in fixed_files):
                    print('first rank', bug_id, i+1, suspicious_files[i])
                    inverse_rank = inverse_rank + (1/(i+1))
                    break

            total_bug = total_bug + 1
        if inverse_rank == 0:
            print("MRR@", top, 0)
        else:
            print("MRR@", top, (1/total_bug)*inverse_rank)

def calculate_mean_average_precision_at_k(project, csv_path):
    bug_results = process_bug_results(project, csv_path)
    for top in [10]:
        total_bug = 0
        total_average_precision = 0
        for bug_id, result in bug_results.items():
            suspicious_files = result['suspicious_files']
            length_of_suspicious_files = len(suspicious_files)
            fixed_files = result['fixed_files']
            precision = 0
            average_precision = 0
            number_of_relevant_files = 0
            minimum_length = min(top,length_of_suspicious_files)
            for i in range(minimum_length):
                if(suspicious_files[i] in fixed_files):
                    print(bug_id,suspicious_files[i], " relevant")
                    number_of_relevant_files = number_of_relevant_files + 1                        
                    precision = precision + (number_of_relevant_files/(i+1))
            average_precision = precision/len(fixed_files)
            
            total_average_precision = total_average_precision + average_precision
            total_bug = total_bug + 1
        mean_average_precision = total_average_precision/total_bug
        print("MAP@", top, mean_average_precision)

if __name__ == "__main__":
    root_dir = ''#'llm-baseline/'
    project = sys.argv[1]
    input_filename = root_dir+project+'-ranking-using-function-call.csv'
    calculate_accuracy_at_k(project, input_filename)
    calculate_mean_reciprocal_rank_at_k(project, input_filename)
    calculate_mean_average_precision_at_k(project, input_filename) 