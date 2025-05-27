import os
import re
import json
from itertools import islice
from rapidfuzz.distance import DamerauLevenshtein


class FileDataProcessor:
    def __init__(self, project, bug_id):
        self.file_level_data = ''
        self.suspicious_files = ''
        self.process_file_level_data(
            project+'_bug_data/' + bug_id + '_filewise_method_data.json')
        self.process_suspicious_filenames(
            project + '_bug_data/' + bug_id + '.json')

    def process_file_level_data(self, file_path):
        with open(file_path, 'r') as current_file:
            self.file_level_data = json.load(current_file)

    def process_suspicious_filenames(self, file_path, top_n=50):
        with open(file_path, 'r') as file:
            parsed_data = json.load(file)
            parsed_data = parsed_data[0]

        files = [
            (parsed_data["metadata"][i]["file"],
             1 - parsed_data["distance"][i])
            for i in range(len(parsed_data["metadata"]))
        ]
        unique_files = dict(sorted(files, key=lambda x: x[1], reverse=True))

        self.suspicious_files = [file for file,
                                 _ in islice(unique_files.items(), top_n)]

    def get_candidate_filenames(self):
        return self.suspicious_files

    def extract_filename(self, full_path):
        if not full_path.endswith(".java"):
            full_path = full_path + '.java'
        base_name = os.path.basename(full_path)
        return base_name.split(".")[-2] + '.' + base_name.split(".")[-1]

    def search_file(self, filename):
        processed_filename = self.extract_filename(filename)
        matches = []
        for file in self.file_level_data:
            current_filename = file.get("filename")
            if current_filename == processed_filename:
                matches.append(
                    {"filename": filename, "fully qualified filename": file.get("filepath")})
        if matches:
            return matches
        else:
            return {
                "error": "File not found",
                "filename": filename
            }

    def get_method_name(self, method_signature):
        try:
            index = method_signature.index("(")
            return method_signature[:index].strip()
        except ValueError:
            return method_signature.strip()

    def search_method(self, method_name):
        processed_method_name = self.get_method_name(method_name)
        matches = []
        for file in self.file_level_data:
            methods = file.get("methods", [])
            for method in methods:
                method_signature = method["signature"]
                current_method_name = self.get_method_name(method_signature)
                if current_method_name == processed_method_name:
                    matches.append({"filename": file.get(
                        "filepath"), "method signature": self.normalize_method_signature(method_signature)})
        if matches:
            return matches
        else:
            return {
                "error": "Method not found",
                "filename": method_name
            }

    
    def normalize_method_signature(self, method_signature):
        method_signature = re.sub(r'\s+', ' ', method_signature.strip())
        method_signature = re.sub(r'\(\s+', '(', method_signature)
        method_signature = re.sub(r'\s+\)', ')', method_signature)
        return method_signature


    def get_method_signatures_of_a_file(self, fully_qualified_filename):
        for file in self.file_level_data:
            current_filepath = file.get("filepath")
            if current_filepath == fully_qualified_filename:
                methods = file.get("methods", [])
                signatures = [self.normalize_method_signature(method["signature"]) for method in methods]

                return {"filename": fully_qualified_filename, "method signatures": signatures}

        matches = []
        for file in self.file_level_data:
            current_filename = file.get("filename")
            if current_filename == self.extract_filename(fully_qualified_filename):
                current_filepath = file.get("filepath")
                methods = file.get("methods", [])
                signatures = [self.normalize_method_signature(method["signature"]) for method in methods]
                matches.append({"filename": current_filepath,
                               "method signatures": signatures})

        if (len(matches) > 1):
            print('multiple files matched!')
            print(matches)

        if matches:
            return matches
        else:
            return {
                "error": "File not found",
                "filename": fully_qualified_filename
            }

    def match_method_body(self, methods, method_signature, filename, threshold=5):
        for method in methods:
            if self.normalize_method_signature(method["signature"]) == method_signature:
                return [{"filename": filename, "method signature": method_signature, "method body": method["body"]}]

        closest_matches = []
        closest_distance = float('inf')

        for method in methods:
            distance = DamerauLevenshtein.distance(method_signature, self.normalize_method_signature(method["signature"]))

            if distance <= threshold:
                if distance < closest_distance:
                    closest_matches = [method]
                    closest_distance = distance
                elif distance == closest_distance:
                    closest_matches.append(method)
        if len(closest_matches) > 1:
            print('multiple method signatures matched')
            # print(closest_matches)
        if closest_matches:
            return [
                {
                    "filename": filename,
                    "method signature": self.normalize_method_signature(match["signature"]),
                    "method body": match["body"]
                } for match in closest_matches
            ]
        else:
            return None

    def get_method_body(self, fully_qualified_filename, method_signature):
        method_body = None

        for file in self.file_level_data:
            current_filepath = file.get("filepath")
            if current_filepath == fully_qualified_filename:
                methods = file.get("methods", [])
                method_body = self.match_method_body(
                    methods, method_signature, fully_qualified_filename)
                if method_body:
                    return method_body

        matches = []
        for file in self.file_level_data:
            current_filename = file.get("filename")
            if current_filename == self.extract_filename(fully_qualified_filename):
                current_filepath = file.get("filepath")
                methods = file.get("methods", [])
                partial_matches = self.match_method_body(
                    methods, method_signature, current_filepath)
                if partial_matches:
                    matches.extend(partial_matches)

        if matches:
            return matches
        else:
            return {
                "error": "Problem in filename or method signature",
                "filename": fully_qualified_filename,
                "method signature": method_signature
            }
