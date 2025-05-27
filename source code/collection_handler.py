from config import Config
from utils import calculate_hash, save_data_to_json, count_tokens
from langchain_text_splitters import RecursiveCharacterTextSplitter
from datetime import datetime
from db_handler import get_file_collection

bug_report_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 8191,
    chunk_overlap = 0,
    length_function=count_tokens
)

def insert_into_file_collection(file_collection, documents, metadata):
    # starting_time = datetime.now()
    
    ids = [calculate_hash(metadata[i]['file']+documents[i]) for i in range(len(documents))]
    set_of_ids = set()
    indexes = []
    for index, value in enumerate(ids):
        if value not in set_of_ids:
            set_of_ids.add(value)         
        else:
            indexes.append(index)
            # print(index, "duplicate")

    updated_documents = [x for i, x in enumerate(documents) if i not in indexes]
    updated_metadata = [x for i, x in enumerate(metadata) if i not in indexes]
    updated_ids = [x for i, x in enumerate(ids) if i not in indexes]

    max_batch_size = 700
    for i in range(0, len(updated_documents), max_batch_size):
        subset_of_documents = updated_documents[i:i + max_batch_size]
        subset_of_metadata = updated_metadata[i:i + max_batch_size]
        subset_of_ids= updated_ids[i:i + max_batch_size]

        file_collection.add(
            documents=subset_of_documents,
            metadatas=subset_of_metadata,
            ids=subset_of_ids
        )
        # print("db size: ", collection.count())
    # ending_time = datetime.now()
    # print("insertion time:", ending_time-starting_time)


def delete_from_file_collection(file_collection, file_path):
    file_collection.delete(
        where={"file": file_path}
    )
    # print("db size: ", collection.count())


def get_chunks_and_metadata_of_a_file(file_collection, file_path):
    data = file_collection.get(where={"file": file_path})
    chunks = data["documents"]
    metadatas = data["metadatas"]

    return chunks, metadatas


def get_chunks_and_metadata_of_a_list_of_files(file_collection, file_paths):
    data = file_collection.get(where={"file": {"$in": file_paths}})
    chunks = data["documents"]
    metadatas = data["metadatas"]

    return chunks, metadatas


def get_data_from_file_collection(file_collection):
    print(file_collection.get(include = ["metadatas"]))


def get_suspicious_files(bug_id, content):
    if content is None or '':
        print("no content!!!!!!!")
        return
    file_collection = get_file_collection()
    bug_report_chunks = bug_report_splitter.split_text(content)

    results = file_collection.query(
        query_texts=bug_report_chunks,
        n_results=300,
        include=['documents', 'metadatas' , 'distances'] 
    )

    # print(results)

    retrieved_documents = results['documents']
    retrieved_metadatas = results['metadatas']
    retrieved_distances = results['distances']

    save_data_to_json(retrieved_documents, retrieved_metadatas, retrieved_distances, Config().get_project() +'_bug_data/'+ bug_id + '.json')
