from chromadb import Documents, EmbeddingFunction, Embeddings
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import tiktoken
import time

class BaseEmbedding(EmbeddingFunction):
    """Base class for embedding functions"""
    def __call__(self, input: Documents) -> Embeddings:
        raise NotImplementedError("Subclasses must implement __call__")

class AlibabaEmbedding(BaseEmbedding):
    _model = None
    _tokenizer = None

    @classmethod
    def _load_model(cls):
        if cls._model is None:
            cls._model = SentenceTransformer(
                'Alibaba-NLP/gte-modernbert-base',
                trust_remote_code=True,
            )
            cls._tokenizer = cls._model.tokenizer

    def __call__(self, input: Documents) -> Embeddings:
        try:
            self._load_model()
            embeddings = self._model.encode(input, convert_to_numpy=True)
            return embeddings.tolist()
        except Exception as e:
            print("Problem in embedding!")
            print(f"Alibaba embedding error: {e}")
            return None

def alibaba_tokenize(text):
    AlibabaEmbedding._load_model()
    return len(AlibabaEmbedding._tokenizer.encode(text, add_special_tokens=False))

# class JinaEmbedding(BaseEmbedding):
#     _model = None
#     _tokenizer = None

#     @classmethod
#     def _load_model(cls):
#         if cls._model is None:
#             cls._model = SentenceTransformer(
#                 'jinaai/jina-embeddings-v3',
#                 trust_remote_code=True,
#             )
#             cls._tokenizer = cls._model.tokenizer

#     def __call__(self, input: Documents) -> Embeddings:
#         try:
#             self._load_model()
#             embeddings = self._model.encode(input, convert_to_numpy=True)
#             return embeddings.tolist()
#         except Exception as e:
#             print("Problem in embedding!")
#             print(f"Jina embedding error: {e}")
#             return None

# def jina_tokenize(text):
#     JinaEmbedding._load_model()
#     return len(JinaEmbedding._tokenizer.encode(text, add_special_tokens=False))

class OpenAIEmbedding:
    _api_key_loaded = False
    _client = None
    _tokenizer = tiktoken.get_encoding("cl100k_base")

    def __call__(self, input: Documents) -> Embeddings:
        if not OpenAIEmbedding._api_key_loaded:
            try:
                with open('api_key.txt', 'r') as file:
                    api_key = file.read().strip()
                OpenAIEmbedding._client = OpenAI(api_key=api_key)
                OpenAIEmbedding._api_key_loaded = True
            except FileNotFoundError:
                raise Exception("API key file 'api_key.txt' not found")
            except Exception as e:
                raise Exception(f"Error reading API key: {e}")

        retries = 5
        for attempt in range(retries):
            try:
                response = OpenAIEmbedding._client.embeddings.create(
                    input=input,
                    model="text-embedding-3-small"
                )
                embeddings = [data.embedding for data in response.data]
                return embeddings
            except Exception as e:
                print("Problem in embedding!")
                print(f"OpenAI embedding error: {e}")
                time.sleep(5 * (attempt + 1))
        return None


def openai_tokenize(text):
    """Tokenizer function for OpenAI embeddings"""        
    return len(OpenAIEmbedding._tokenizer.encode(text))
