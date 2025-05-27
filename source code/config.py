import threading

class Config:
    _instance = None
    _lock = threading.Lock()
    VALID_EMBEDDING_TYPES = ['gte', 'openai', 'jina']

    def __new__(cls):
        """Thread-safe Singleton instantiation"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # Double-checked locking
                    cls._instance = super(Config, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the Config instance once"""
        if not self._initialized:
            self._project = ""
            self._embedding_type = self.VALID_EMBEDDING_TYPES[0]  # Default embedding
            self._initialized = True

    def get_project(self):
        """Get the project name"""
        return self._project

    def get_embedding_type(self):
        """Get the embedding type"""
        return self._embedding_type

    def set_project(self, project):
        """Set the project name"""
        if isinstance(project, str) and project:
            self._project = project
        else:
            raise ValueError("Project must be a non-empty string")

    def set_embedding_type(self, embedding_type):
        """Set the embedding type"""
        if isinstance(embedding_type, str) and embedding_type in self.VALID_EMBEDDING_TYPES:
            self._embedding_type = embedding_type
        else:
            raise ValueError(f"Embedding type must be one of {self.VALID_EMBEDDING_TYPES}")
