from openai import OpenAI

class OpenAIClientManager:
    def __init__(self):
        self._api_key = None
        self._client = None
        self._load_api_key()

    def _load_api_key(self):
        if self._api_key is None:
            try:
                with open('api_key.txt', 'r') as file:
                    self._api_key = file.read().strip()
                self._client = OpenAI(api_key=self._api_key)
            except FileNotFoundError:
                raise Exception("API key file 'api_key.txt' not found")
            except Exception as e:
                raise Exception(f"Error reading API key: {e}")

    def get_client(self):
        if self._client is None:
            self._load_api_key()
        return self._client