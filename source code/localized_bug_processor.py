import csv
import sys

def extract_bug_ids_by_accuracy_sections(filepath):
    bug_ids = {
        "accuracy1": set(),
        "accuracy5": set(),
        "accuracy10": set()
    }

    section = "accuracy1"

    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()

            if line.startswith("accuracy@ 10"):
                break
            elif line.startswith("accuracy@ 5"):
                section = "accuracy10"
                continue
            elif line.startswith("accuracy@ 1"):
                section = "accuracy5"
                continue

            if line.startswith("below 10 files!"):
                continue

            tokens = line.split()
            if tokens and tokens[0].isdigit():
                bug_ids[section].add(tokens[0])

    return bug_ids

project = sys.argv[1]

# === File paths ===
files = [f'../result-3/results/{project}-embedding-res.txt', f'../result-2/results/{project}-embedding-res.txt', f'../result-1/results/{project}-embedding-res.txt']
all_results = []

for idx, file in enumerate(files):
    result = extract_bug_ids_by_accuracy_sections(file)
    all_results.append(result)

    max_len = max(len(result["accuracy1"]), len(result["accuracy5"]), len(result["accuracy10"]))
    pad = lambda s: sorted(s) + [""] * (max_len - len(s))
    rows = zip(pad(result["accuracy1"]), pad(result["accuracy5"]), pad(result["accuracy10"]))

    out_file = f"localized_bugs_{project}-run-{idx+1}.csv"
    with open(out_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Accuracy@1", "Accuracy@5", "Accuracy@10"])
        writer.writerows(rows)

    print(f"Saved individual run {idx+1} bug data to '{out_file}'")

# === Intersection: common in all three files ===
common_accuracy1 = set.intersection(*[res['accuracy1'] for res in all_results])
common_accuracy5 = set.intersection(*[res['accuracy5'] for res in all_results])
common_accuracy10 = set.intersection(*[res['accuracy10'] for res in all_results])

max_len = max(len(common_accuracy1), len(common_accuracy5), len(common_accuracy10))
pad = lambda s: sorted(s) + [""] * (max_len - len(s))

rows = zip(pad(common_accuracy1), pad(common_accuracy5), pad(common_accuracy10))

# === Write common bugs by level ===
with open(f"{project}_common_bugs.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Accuracy@1", "Accuracy@5", "Accuracy@10"])
    writer.writerows(rows)

print(f"Saved common bugs per accuracy level to 'common_bugs_by_level.csv'")

# === Union: bug appears in at least one file ===
union_accuracy1 = set.union(*[res['accuracy1'] for res in all_results])
union_accuracy5 = set.union(*[res['accuracy5'] for res in all_results])
union_accuracy10 = set.union(*[res['accuracy10'] for res in all_results])

max_len_union = max(len(union_accuracy1), len(union_accuracy5), len(union_accuracy10))
pad = lambda s: sorted(s) + [""] * (max_len_union - len(s))

rows_union = zip(pad(union_accuracy1), pad(union_accuracy5), pad(union_accuracy10))

# === Write union bugs to CSV ===
with open(f"{project}_union_bugs.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Accuracy@1", "Accuracy@5", "Accuracy@10"])
    writer.writerows(rows_union)

print(f"Saved union bugs per accuracy level to 'union_bugs_by_level.csv'")
