import chromadb
from chromadb import Settings
from config import Config 

def initialize_db():
    global client
    client = chromadb.Client(settings=Settings(allow_reset=True))
    client.reset()


def create_file_collection():
    global client, file_collection
    
    config = Config()
    embedding_type = config.get_embedding_type()
    if embedding_type == 'gte':
        from embedding_handler import AlibabaEmbedding
        print('gte embedding') 
        embedding_function = AlibabaEmbedding()
    elif embedding_type == 'openai':
        from embedding_handler import OpenAIEmbedding
        print('openai embedding')
        embedding_function = OpenAIEmbedding()
    # else:
    #     from embedding_handler import JinaEmbedding
    #     print('jina embedding') 
    #     embedding_function = JinaEmbedding()
    file_collection = client.create_collection(name='java-files', embedding_function= embedding_function, metadata={"hnsw:space": "cosine", "hnsw:M": 32})

    return file_collection


def delete_file_collection():
    global client
    try:
        client.delete_collection('java-files')
    except:
        print('file collection does not exist')


def get_file_collection():
    global file_collection
    return file_collection