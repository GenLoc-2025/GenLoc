from bug_data_retriever import get_bug_data
from pydriller import Git
from config import Config
from file_processor import *
from db_handler import initialize_db
from file_parser import initialize_parser
from collection_handler import get_suspicious_files
from datetime import datetime
import sys

def main():
    start_time = datetime.now()
    project = sys.argv[1]
    repo_path = sys.argv[2]
    xml_path = sys.argv[3]
    embedding_type = sys.argv[4]
    config = Config()
    config.set_project(project)
    config.set_embedding_type(embedding_type)
    new_bugs = get_bug_data(xml_path)

    git_repo = Git(repo_path)
    prev_commit = ""

    initialize_parser()
    initialize_db()

    for bug in new_bugs:
        print('bug-id:', bug['bug_id'], 'commits', prev_commit, f"{bug['fixing_commit']}~1")
        manage_file_processing(git_repo, bug['bug_id'], prev_commit, f"{bug['fixing_commit']}~1")
        # starting_time = datetime.now()
        get_suspicious_files(bug['bug_id'], str(bug['summary'] or '')+ ' ' + str(bug['description'] or ''))
        # ending_time = datetime.now()
        # print('searching time:', ending_time-starting_time)

        prev_commit = f"{bug['fixing_commit']}~1"
    
    end_time = datetime.now()

    print('total time', end_time-start_time)
    print("*********************************************************************************************")

if __name__ == "__main__":
    main()