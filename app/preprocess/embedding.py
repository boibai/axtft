from FlagEmbedding import BGEM3FlagModel

_embedding_model = None

def load_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = BGEM3FlagModel(
            "BAAI/bge-m3",
            use_fp16=True,
        )

def get_embedding_model():
    if _embedding_model is None:
        raise RuntimeError("Embedding model is not loaded.")
    return _embedding_model