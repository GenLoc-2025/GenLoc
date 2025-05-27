import os
import statistics
from bug_data_retriever import get_bug_data
from pydriller import Git
import sys

project = sys.argv[1]
repo_path = sys.argv[2]
xml_path = sys.argv[3]

git_repo = Git(repo_path)
bugs = get_bug_data(xml_path)

java_file_counts = []
java_loc_counts = []

for bug in bugs:
    # checkout the commit just before the fix
    git_repo.checkout(f"{bug['fixing_commit']}~1")

    file_count = 0
    loc_count = 0

    for root, dirs, files in os.walk(git_repo.path):
        for fname in files:
            if fname.endswith('.java'):
                file_count += 1
                file_path = os.path.join(root, fname)
                # count non-blank lines (optional: include all lines)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        loc_count += 1

    java_file_counts.append(file_count)
    java_loc_counts.append(loc_count)

def print_stats(name, data):
    print(f"{name} — Max: {max(data)}, Min: {min(data)}, "
          f"Mean: {statistics.mean(data):.2f}, Median: {statistics.median(data)}")

print_stats("Java file count", java_file_counts)
print_stats("Java LOC count", java_loc_counts)
