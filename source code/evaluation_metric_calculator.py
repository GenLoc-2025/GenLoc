import os
import csv
import json
import sys
import re


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


def process_bug_results(csv_path):
    bug_results = {}
    with open(csv_path, newline='', encoding='utf-8', errors='ignore') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            bug_id = row['bug_id']
            try:
                suspicious_files = parse_json(row['suspicious_files'])
                fixed_files = row['fixed_files'].split(',')
                
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
    input_filename = root_dir+project+'_final_ranked_output.csv'
    calculate_accuracy_at_k(project, input_filename)
    calculate_mean_reciprocal_rank_at_k(project, input_filename)
    calculate_mean_average_precision_at_k(project, input_filename) 