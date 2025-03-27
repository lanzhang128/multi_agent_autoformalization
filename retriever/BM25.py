import re
import numpy as np
from rank_bm25 import BM25Okapi
from .abstract import BaseRetriever


def isabelle_tokenize(text):
    # Tokenize letters and symbols separately
    pattern = r'\\<.*?>|[a-zA-Z]+|::|[^\s\w]'
    tokens = re.findall(pattern, text)
    return tokens


class BM25Retriever(BaseRetriever):
    description = 'A BM25 retriever.'

    def __init__(self,
                 name: str = 'BM25Retriever',
                 **kwargs):
        super().__init__(name, **kwargs)

    def _instantiate(self, corpus, formal_language=''):
        self.fn_tokenize = str.split
        if formal_language:
            if formal_language[:8] == 'Isabelle':
                self.fn_tokenize = isabelle_tokenize

        tokenized_corpus = [self.fn_tokenize(doc) for doc in corpus]
        self.model = BM25Okapi(tokenized_corpus)

    def retrieve(self, query, top_n=1):
        scores = self.model.get_scores(self.fn_tokenize(query))
        return np.argsort(scores).tolist()[::-1][:top_n]
