import sys
import json
from bug_data_retriever import get_bug_data

def get_suspicious_files(file_path, top_n=50):
    with open(file_path, 'r') as file:
        parsed_data = json.load(file)
        parsed_data = parsed_data[0]

    files = [
        (parsed_data["metadata"][i]["file"], 1 - parsed_data["distance"][i])
        for i in range(len(parsed_data["metadata"]))
    ]
    sorted_files = sorted(files, key=lambda x: x[1], reverse=True)

    unique_files = {}
    for file, similarity in sorted_files:
        if file not in unique_files:
            unique_files[file] = similarity

    top_files = list(unique_files.items())[:top_n]

    return top_files


def calculate_accuracy_at_k(bug_data):
    for top in [1,5,10,50]:
        count = 0
        total_bug = 0
        for bug in bug_data:
            suspicious_files = bug['suspicious_files']
            # length_of_suspicious_files = len(suspicious_files)

            fixed_files = bug['fixed_files'].split('.java')
            fixed_files = [(file + '.java').strip() for file in fixed_files[:-1]]

            # print(bug['bug_id'], fixed_files)
            for fixed_file in fixed_files:
                if fixed_file in suspicious_files[0:top]:
                    print(bug['bug_id'],fixed_file)
                    count = count + 1
                    break
            total_bug = total_bug + 1
        print('accuracy@', top, count, total_bug, (count*100/total_bug))


def calculate_mean_reciprocal_rank_at_k(bug_data):
    for top in [10]:
        total_bug = 0
        inverse_rank = 0
        for bug in bug_data:
            suspicious_files = bug['suspicious_files']
            length_of_suspicious_files = len(suspicious_files)
            fixed_files = bug['fixed_files'].split('.java')
            fixed_files = [(file + '.java').strip() for file in fixed_files[:-1]]
            # print("ID ",item['bug_id'])
            # print(suspicious_files)
            # print("length_of_suspicious_files",length_of_suspicious_files)
            minimum_length = min(top,length_of_suspicious_files)
            for i in range(minimum_length):
                if(suspicious_files[i] in fixed_files):
                    # print('first rank', item['bug_id'], i+1, suspicious_files[i])
                    inverse_rank = inverse_rank + (1/(i+1))
                    break
            total_bug = total_bug + 1
        if inverse_rank == 0:
            print("MRR@", top, 0)
        else:
            print("MRR@", top, (1/total_bug)*inverse_rank)
           
     
def calculate_mean_average_precision_at_k(bug_data):
    for top in [10]:
        total_bug = 0
        total_average_precision = 0
        for bug in bug_data:
            average_precision = 0
            precision = 0
            suspicious_files = bug['suspicious_files']
            length_of_suspicious_files = len(suspicious_files)
            fixed_files = bug['fixed_files'].split('.java')
            fixed_files = [(file + '.java').strip() for file in fixed_files[:-1]]
            number_of_relevant_files = 0
            minimum_length = min(top,length_of_suspicious_files)
            for i in range(minimum_length):
                # print("i",i)
                if(suspicious_files[i] in fixed_files):
                    # print(item['bug_id'],suspicious_files[i], " relevant")
                    number_of_relevant_files = number_of_relevant_files + 1                        
                    precision = precision + (number_of_relevant_files/(i+1))
                # print("precision ", precision)
            average_precision = precision/len(fixed_files)
            # print("average_precision" ,average_precision, len(fixed_files))
            total_average_precision = total_average_precision + average_precision
            total_bug = total_bug + 1
        mean_average_precision = total_average_precision/total_bug
        print("MAP@", top, mean_average_precision)


def main():
    project = sys.argv[1]
    xml_path = sys.argv[2]

    bug_data = []
    bugs = get_bug_data(xml_path)
    for bug in bugs:
        # print(bug['bug_id'])        
        suspicious_files = get_suspicious_files(project+'_bug_data/'+bug['bug_id']+'.json')

        bug_data_entry = {
            'bug_id': bug['bug_id'],
            'fixed_files': bug['fixed_files'],
            'suspicious_files': [file for file, _ in suspicious_files]
        }
        bug_data.append(bug_data_entry)

        # break

    calculate_accuracy_at_k(bug_data)
    calculate_mean_reciprocal_rank_at_k(bug_data)
    calculate_mean_average_precision_at_k(bug_data)
    
if __name__ == "__main__":
    main()