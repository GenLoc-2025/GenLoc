# GenLoc
It is a novel bug localization approach that combines semantic retrieval with the step-by-step reasoning capabilities of Large Language Models (LLMs) to identify buggy files for a given bug report. It operates in two primary steps to localize relevant files. First, it retrieves a set of semantically similar files using embedding-based similarity. Next, an LLM, supported by a set of external functions, iteratively analyzes the bug report and source files.

## 🗂️ Directory Structure

* `source_code/`: This folder contains the source code of GenLoc.
* `output_files/`: Ranked list produced by GenLoc (for each trial).
* `localized_bugs/`: Contains bugs localized by each bug localization approach.
* `dataset/`: Contains XML files and GitHub URLs of the projects used for bug localization.
---

## ⚙️ Set-Up

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Place your OpenAI API key in a file named `api_key.txt` in the project root directory.

---

## 🔧 How to Run

To run GenLoc, first navigate to the source code directory:

```bash
cd source_code
```

Then, execute the following steps:

```bash
# Step 1: Execute embedding-based retrieval
# Format: python main.py <project_name> <project_repo_path> <bug_report_xml> <embedding_model>
# Example:
python main.py aspectj dataset/aspectj dataset/aspectj.xml openai

# Step 2: Run the LLM-based analysis
# Format: python bug_localizer.py <project_name> <bug_report_xml>
# Example:
python bug_localizer.py aspectj dataset/aspectj.xml

# Step 3: Perform post-processing
# Format: python post_processor.py <project_name>
# Example:
python post_processor.py aspectj

# Step 4: Evaluate performance using standard metrics
# Format: python evaluation_metric_calculator.py <project_name>
# Example:
python evaluation_metric_calculator.py aspectj
```

---