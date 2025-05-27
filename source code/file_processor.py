import os
import json
from config import Config
from file_parser import *
from collection_handler import *
from datetime import datetime
from db_handler import create_file_collection, delete_file_collection, get_file_collection
from utils import *

def get_file_content(repo_path,file_path):
    full_path = repo_path / file_path
    with open((full_path), encoding="utf8", errors="ignore") as file:
        file_content = file.read()
    return file_content

def process_files_from_directory(repo_path):
    # starting_time = datetime.now()
    global filewise_method_data
    filewise_method_data = {}
    
    delete_file_collection()
    file_collection = create_file_collection()

    documents = []
    metadatas = []
    for root, dirs, files in os.walk(repo_path):
        relative_root = os.path.relpath(root, repo_path)
        for file in files:
            if file.endswith(".java"):
                file_path = os.path.join(relative_root, file)
                file_path = file_path.replace("\\", "/")
                file_content = get_file_content(repo_path, file_path)
                # print("processing", file_path)
                package, methods_dict = extract_package_and_methods(file_content)
                if len(methods_dict)>0 and (package is not None):
                    file_data = ''
                    filewise_method_data[file_path] = {
                        'package': package,
                        'methods': []
                    }
                
                    for signature, body in methods_dict.items():
                        filewise_method_data[file_path]['methods'].append({
                            'signature': signature,
                            'body': body
                        })
                        file_data = file_data + '\n' + body
                    # print("entities", len(methods_dict))
                    chunks = get_chunks(file_data.strip())
                    updated_chunks = ['file: ' + file_path + '\n' + s for s in chunks]
                    documents.extend(updated_chunks)
                    list_of_metadata = [{"file": file_path} for _ in updated_chunks]
                    metadatas.extend(list_of_metadata)

                # for chunk in chunks:
                #     print(chunk)
                #     print("*************")
    # ending_time = datetime.now()
    # print("file processing time:", ending_time-starting_time)
    insert_into_file_collection(file_collection, documents, metadatas)

def manage_file_processing(git_repo, bug_id, prev_commit, current_commit):
    if(prev_commit==""):
        git_repo.checkout(current_commit)
        # time.sleep(30)
        process_files_from_directory(git_repo.path)
    else:
        modified_files = git_repo.diff(from_commit_id = prev_commit, to_commit_id = current_commit)
        if(2*len(modified_files)>=len(filewise_method_data)):
            git_repo.checkout(current_commit)
            # time.sleep(30)
            process_files_from_directory(git_repo.path)
        else:
            process_files_from_git_diff(modified_files)
    store_file_data(bug_id)

def process_files_from_git_diff(modified_files):
    documents = []
    metadatas = []

    modified_java_files = []
    for modified_file in modified_files:
        if modified_file.filename.endswith(".java"):
            if modified_file.change_type.name == "DELETE":
                modified_java_files.insert(0,modified_file)
            else:
                modified_java_files.append(modified_file)

    file_collection = get_file_collection()
    for modified_file in modified_java_files:
        if modified_file.change_type.name == "ADD":
            # print(modified_file.source_code)
            file_path = modified_file.new_path
            file_path = file_path.replace("\\", "/")
            file_content = modified_file.source_code
            # print("Added file:", file_path)
            package, methods_dict = extract_package_and_methods(file_content)
            if len(methods_dict)>0 and (package is not None):
                file_data = ''
                filewise_method_data[file_path] = {
                    'package': package,
                    'methods': []
                }
            
                for signature, body in methods_dict.items():
                    filewise_method_data[file_path]['methods'].append({
                        'signature': signature,
                        'body': body
                    })
                    file_data = file_data + '\n' + body
                # print("entities", len(methods_dict))
                chunks = get_chunks(file_data.strip())
                updated_chunks = ['file: ' + file_path + '\n' + s for s in chunks]
                documents.extend(updated_chunks)
                list_of_metadata = [{"file": file_path} for _ in updated_chunks]
                metadatas.extend(list_of_metadata)
        elif modified_file.change_type.name == "DELETE":
            file_path = modified_file.old_path
            file_path = file_path.replace("\\", "/")
            delete_from_file_collection(file_collection, file_path)
            delete_file_entry(file_path)
            # print("Deleted file:", file_path)
        elif modified_file.change_type.name == "MODIFY":
            file_path = modified_file.new_path
            file_path = file_path.replace("\\", "/")
            
            delete_from_file_collection(file_collection, file_path)
            delete_file_entry(file_path)
            # print("Updated file:", file_path)
            
            file_content = modified_file.source_code
            package, methods_dict = extract_package_and_methods(file_content)
            if len(methods_dict)>0 and (package is not None):
                file_data = ''
                filewise_method_data[file_path] = {
                    'package': package,
                    'methods': []
                }
            
                for signature, body in methods_dict.items():
                    filewise_method_data[file_path]['methods'].append({
                        'signature': signature,
                        'body': body
                    })
                    file_data = file_data + '\n' + body
                # print("entities", len(methods_dict))
                chunks = get_chunks(file_data.strip())
                updated_chunks = ['file: ' + file_path + '\n' + s for s in chunks]
                documents.extend(updated_chunks)
                list_of_metadata = [{"file": file_path} for _ in updated_chunks]
                metadatas.extend(list_of_metadata)
        elif modified_file.change_type.name == "RENAME":
            if modified_file.source_code == None:
                file_path = modified_file.old_path
                old_file_path = file_path.replace("\\", "/")

                # print("Renamed Old Java file:", old_file_path)
                file_path = modified_file.new_path
                new_file_path = file_path.replace("\\", "/")
                # print("Renamed New Java file:", new_file_path)
                
                rename_file_entry(old_file_path, new_file_path)

                old_chunks, old_metadata = get_chunks_and_metadata_of_a_file(file_collection, old_file_path)
                updated_chunks = [chunk.replace(old_file_path, new_file_path) for chunk in old_chunks]

                # print("old info",old_chunks, old_metadata)
                documents.extend(updated_chunks)
                list_of_metadata = [{"file": new_file_path} for _ in updated_chunks]
                metadatas.extend(list_of_metadata)

                # print(updated_chunks, list_of_metadata)
                delete_from_file_collection(file_collection, old_file_path)
            else:
                file_path = modified_file.old_path
                old_file_path = file_path.replace("\\", "/")
                # print("Renamed Old Java file:", old_file_path)
                delete_from_file_collection(file_collection, old_file_path)
                delete_file_entry(file_path)

                file_path = modified_file.new_path
                new_file_path = file_path.replace("\\", "/")

                # print("Renamed New Java file:", new_file_path)
                file_content = modified_file.source_code
                package, methods_dict = extract_package_and_methods(file_content)
                if len(methods_dict)>0 and (package is not None):
                    file_data = ''
                    filewise_method_data[new_file_path] = {
                        'package': package,
                        'methods': []
                    }
                
                    for signature, body in methods_dict.items():
                        filewise_method_data[new_file_path]['methods'].append({
                            'signature': signature,
                            'body': body
                        })
                        file_data = file_data + '\n' + body
                    # print("entities", len(methods_dict))
                    chunks = get_chunks(file_data.strip())
                    updated_chunks = ['file: ' + new_file_path + '\n' + s for s in chunks]
                    documents.extend(updated_chunks)
                    list_of_metadata = [{"file": new_file_path} for _ in updated_chunks]
                    metadatas.extend(list_of_metadata)

    insert_into_file_collection(file_collection, documents,metadatas)


def store_file_data(bug_id):
    try:
        global filewise_method_data    
        file_paths = filewise_method_data.keys()
        all_file_data = []
        for file_path in file_paths:
            file_data = {
                    "filepath" : file_path,
                    "package": filewise_method_data[file_path]['package'],
                    "filename": get_filename_from_path(file_path),
                    "methods": filewise_method_data[file_path]['methods']
                }
            all_file_data.append(file_data)
        
        filename = f"{Config().get_project()}_bug_data/{bug_id}_filewise_method_data.json"
        print(filename)
        output_dir = os.path.dirname(filename)
    
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        with open(filename, 'w') as json_file:
            json.dump(all_file_data, json_file, indent=4)
    except Exception as e:
        print(f"Error processing bug_id {bug_id}: {e}")

def file_exists(file_path):
    if file_path in filewise_method_data:
        return True
    return False

def delete_file_entry(file_path):
    if file_path in filewise_method_data:
        del filewise_method_data[file_path]
    else:
        print(f"File entry not found: {file_path}")

def rename_file_entry(old_file_path, new_file_path):
    if old_file_path in filewise_method_data:
        filewise_method_data[new_file_path] = filewise_method_data.pop(old_file_path)
    else:
        print(f"File entry not found: {old_file_path}")

def get_package_and_methods(file_path):
    if file_path in filewise_method_data:
        package = filewise_method_data[file_path]['package']
        methods = filewise_method_data[file_path]['methods']
        return package, methods
    else:
        print(f"No data found for file: {file_path}")
        return None, None
