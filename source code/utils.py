import os
import json
import hashlib
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import Config
from embedding_handler import alibaba_tokenize, openai_tokenize

def count_tokens(text):
    config = Config()
    embedding_type = config.get_embedding_type()
    if embedding_type == 'gte':
        return alibaba_tokenize(text)
    elif embedding_type == 'openai':
        return openai_tokenize(text)

entity_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 300,
    chunk_overlap = 0,
    length_function=count_tokens
)

def calculate_hash(content):
    content_bytes = content.encode('utf-8')
    hash_object = hashlib.sha256(content_bytes)
    hash_value = hash_object.hexdigest()
    return hash_value

def get_chunks(entity):
    chunks = entity_splitter.split_text(entity)
    return chunks

def get_filename_from_path(fully_qualified_filename):
    return os.path.basename(fully_qualified_filename)

def save_data_to_json(retrieved_documents, retrieved_metadatas, retrieved_distances, output_file):
    output_dir = os.path.dirname(output_file)
    
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    data_to_save = [
        {
            "document": doc,
            "metadata": meta,
            "distance": dist
        }
        for doc, meta, dist in zip(retrieved_documents, retrieved_metadatas, retrieved_distances)
    ]

    with open(output_file, 'w') as json_file:
        json.dump(data_to_save, json_file, indent=4)