import os
import json
import logging
import threading
from openai_client_manager import OpenAIClientManager
from file_data_processor import FileDataProcessor

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_file",
            "description": "Search for a Java file in the codebase using an inferred or guessed name. Returns the fully qualified filename if it exists.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Inferred filename to search (e.g., Person.java)"
                    }
                },
                "required": ["filename"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_method",
            "description": "Search for a method across the codebase by its name. Returns the files where the method is found.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "method_name": {
                        "type": "string",
                        "description": "The name of the method to search for (e.g., updatePersonDetails)"
                    }
                },
                "required": ["method_name"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_candidate_filenames",
            "description": "Retrieve 50 fully qualified filenames from the code base that might be relevant. Useful when filename inference is uncertain.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_method_signatures_of_a_file",
            "description": "Get all method signatures defined in a given Java file.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Fully qualified name of the file to inspect."
                    }
                },
                "required": ["filename"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_method_body",
            "description": "Retrieve the body of a specified method from a Java file.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Fully qualified name of the file that contains the method."
                    },
                    "method_signature": {
                        "type": "string",
                        "description": "The full signature of the method whose body should be returned."
                    }
                },
                "required": ["filename", "method_signature"],
                "additionalProperties": False
            }
        }
    }
]



class BugReportProcessor:
    _dir_creation_lock = threading.Lock()
    def __init__(self, project, bug_id, bug_report_summary, bug_report_description):
        if not all([project, bug_id, bug_report_summary, bug_report_description]):
            raise ValueError("All parameters must be non-empty")
        self.project = project
        self.bug_id = bug_id
        self.bug_report_summary = bug_report_summary
        self.bug_report_description = bug_report_description
        self.file_data_processor = FileDataProcessor(self.project, self.bug_id)
        self.openai_client_manager = OpenAIClientManager()
        
        self.project_log_dir = os.path.join(os.getcwd(), self.project)
        with BugReportProcessor._dir_creation_lock:
            os.makedirs(self.project_log_dir, exist_ok=True)

        self.logger = logging.getLogger(f"bug_{bug_id}")
        if not self.logger.handlers:
            log_file = os.path.join(self.project_log_dir, f"bug_{bug_id}_log.txt")
            file_handler = logging.FileHandler(log_file)
            formatter = logging.Formatter('%(asctime)s - %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            self.logger.setLevel(logging.INFO)

    def create_prompt(self):
        prompt = f"""
Given a bug report, your goal is to analyze and rank files by their likelihood of containing the bug. 

Bug Report Summary:
{self.bug_report_summary}

Bug Report Description:
{self.bug_report_description}
"""
        clean_string = prompt.encode('utf-8', 'ignore').decode()
        # print(clean_string)
        # print("**********************************************************************")
        return clean_string
    
    def rank_files(self):
        system_content = """You are an expert software engineer specializing in fault localization. Your goal is to identify the most probable buggy Java files based on a given bug report. You have access to five functions that will help you infer file names, locate methods, and analyze source code. You must follow an iterative, reasoning-based approach, refining your strategy dynamically based on prior successes and failures. Continue this process until you either (a) produce a well-justified ranked list of the 10 most relevant files based on the bug report, or (b) reach the maximum limit of 10 iterations. **In the 10th iteration, you must provide your final output regardless of confidence level.**

**Workflow**  
1. Analyze the Bug Report:
- Extract relevant keywords, error messages, and functional hints from the bug summary and description.  
- Identify potential components (e.g., UI, database, networking) involved in the issue.  

2. Search:
- Use `search_file()` to check if a filename matching the extracted keywords or functionality exists in the codebase.  
- If the bug report references a specific method name, use `search_method()` to locate the file(s) containing that method.  
- If an inferred filename or method location does not exist, refine your strategy: adjust assumptions, explore variations, and retry.  
- If no strong inference can be made, use `get_candidate_filenames()` to retrieve 50 potential filenames.  
- From the retrieved filenames, prioritize those that align with the bug report’s keywords, functionality, or mentioned methods.  

3. Method Analysis:
- For shortlisted files, retrieve method signatures using `get_method_signatures_of_a_file()`.  
- Identify methods that directly align with the bug’s context (e.g., matching function names, handling related data).  
- If method signatures suggest a relevant function, retrieve its implementation using `get_method_body()`.  
- Analyze logic to determine if it aligns with the bug’s symptoms.  

4. Refinement and Ranking:
- Rank files based on multiple factors:  
  - Keyword and functionality match  
  - Method or filename alignment with bug context  
  - Code logic alignment with the bug description  
- If uncertainty remains, refine the analysis by iterating over previous steps with adjusted assumptions.  

5. Output:  
- Provide a ranked list of the **10 most relevant files** based on their likelihood of containing the bug.  
- Ensure filenames **exactly match** those provided—**do not modify case, structure, or abbreviate them**.  
- Justify each file’s inclusion, clearly explaining its relevance to the bug. 
"""
        try:
            client = self.openai_client_manager.get_client()
            messages = [
                {"role": "system", "content": system_content}, {"role": "user", "content": self.create_prompt()}
            ]
            iteration_count = 0
            max_iterations = 10
            while iteration_count < max_iterations:
                self.logger.info(f"Iteration {iteration_count}")
                # print("iteration",iteration_count)
                if iteration_count == 0:
                    tool_choice = "required"
                elif iteration_count == max_iterations-2:
                    tool_choice = "none"
                else:
                    tool_choice = "auto"
                response = client.chat.completions.create(
                    model = "gpt-4o-mini",
                    # temperature= 0,
                    messages = messages,
                    tools = tools,
                    tool_choice = tool_choice,
                    response_format = {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "output_format",
                            "strict": True,
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "analysis_of_the_bug_report": {
                                        "type": "string",
                                        "description": "Detailed analysis of the bug summary and description, including extracted keywords, error messages, affected components, and any referenced methods or functionality that help narrow down relevant files."
                                    },
                                    "ranked_list": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "file": {
                                                    "type": "string",
                                                    "description": "The fully qualified file name, exactly as it appears in the codebase (case and structure preserved)."
                                                },
                                                "justification": {
                                                    "type": "string",
                                                    "description": "Explanation of why the file is relevant to the bug report, including any matching keywords, inferred functionality, method signature matches, and analysis of method body logic."
                                                }
                                            },
                                            "required": ["file", "justification"],
                                            "additionalProperties": False
                                        },
                                    },
                                },
                                "required": ["analysis_of_the_bug_report", "ranked_list"],
                                "additionalProperties": False
                            }
                        }
                    }
                )
                response_message = response.choices[0].message
                tool_calls = response_message.tool_calls
                
                if tool_calls:
                    # print(tool_calls)
                    messages.append(response_message)

                    for tool_call in tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)

                        self.logger.info(f"Function called: {function_name}, Arguments: {function_args}")

                        if function_name == "search_file":
                            function_response = self.file_data_processor.search_file(function_args.get("filename"))
                        elif function_name == "search_method":
                            function_response = self.file_data_processor.search_method(function_args.get("method_name"))
                        elif function_name == "get_candidate_filenames":
                            function_response = self.file_data_processor.get_candidate_filenames()
                        elif function_name == "get_method_signatures_of_a_file":
                            function_response = self.file_data_processor.get_method_signatures_of_a_file(function_args.get("filename"))
                        elif function_name == "get_method_body":
                            method_signature = function_args.get("method_signature")
                            filename = function_args.get("filename")
                            function_response = self.file_data_processor.get_method_body(filename, method_signature)
                        else:
                            function_response = {"error": f"Unknown function: {function_name}"}
                        
                        self.logger.info(f"Function response for {function_name}: {function_response}")
                        
                        messages.append(
                            {
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": function_name,
                                "content": json.dumps(function_response),
                            }
                        )
                    iteration_count = iteration_count + 1
                else:
                    self.logger.info(f"API Usage: {response.usage}")
                    print("messages",messages,iteration_count)
                    return response_message.content
        
        except Exception as e:
            print(f"An error occurred: {e}")