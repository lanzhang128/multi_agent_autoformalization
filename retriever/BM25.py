import numpy as np
from rank_bm25 import BM25Okapi
from .abstract import BaseRetriever


class BM25Retriever(BaseRetriever):
    description = 'A BM25 retriever.'

    def __init__(self,
                 name: str = 'BM25Retriever',
                 **kwargs):
        super().__init__(name, **kwargs)

    def _instantiate(self, corpus):
        tokenized_corpus = [doc.split() for doc in corpus]
        self.model = BM25Okapi(tokenized_corpus)

    def retrieve(self, query, top_n=1):
        scores = self.model.get_scores(query.split())
        return np.argsort(scores).tolist()[-top_n:]
