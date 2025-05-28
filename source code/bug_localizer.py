import csv
import sys
from datetime import datetime
from bug_data_retriever import get_bug_data
from bug_report_processor import BugReportProcessor
import concurrent.futures
import threading

lock = threading.Lock()

def process_bug(bug, project, output_file):
    bug_report_processor = BugReportProcessor(
        project, bug['bug_id'], str(bug['summary'] or 'N/A'), str(bug['description'] or 'N/A')
    )
    result = bug_report_processor.rank_files()
    
    with lock:
        with open(output_file, 'a', newline="", encoding='utf-8', errors='ignore') as output_csv:
            writer = csv.writer(output_csv)
            writer.writerow([bug['bug_id'], result, bug['fixed_files']])


def process_bugs_parallelly(bugs, project, output_file):
    with open(output_file, 'w', newline="", encoding='utf-8', errors='ignore') as output_csv:
        writer = csv.writer(output_csv)
        writer.writerow(['bug_id', 'suspicious_files', 'fixed_files'])

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(lambda bug: process_bug(bug, project, output_file), bugs)


if __name__ == "__main__":
    start_time = datetime.now()

    project = sys.argv[1]
    input_xml_file = sys.argv[2]
    output_file = project + '_intermediate_ranking.csv'

    bugs = get_bug_data(input_xml_file)
    process_bugs_parallelly(bugs, project, output_file)

    end_time = datetime.now()
    print("total time", end_time-start_time)