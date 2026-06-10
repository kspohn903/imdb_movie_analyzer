import pandas as pd
import numpy as np
import re
from collections import Counter

class TitleRAGPredictor:
    def __init__(self):
        self.df = None
        self.vocab = {}
        self.idf = {}
        self.tfidf_matrix = None

    def _tokenize(self, text):
        return re.findall(r'\w+', text.lower())

    def fit(self, df):
        """Fits a simple TF-IDF model manually."""
        self.df = df.copy()
        self.df['context'] = (self.df['primaryTitle'] + " " + self.df['genres'].fillna('')).fillna('')
        
        documents = [self._tokenize(ctx) for ctx in self.df['context']]
        num_docs = len(documents)
        
        # Build vocabulary and DF
        df_counts = Counter()
        for doc in documents:
            df_counts.update(set(doc))
        
        self.vocab = {word: i for i, word in enumerate(df_counts.keys())}
        self.idf = {word: np.log(num_docs / (count + 1)) for word, count in df_counts.items()}
        
        # Build TF-IDF matrix
        self.tfidf_matrix = np.zeros((num_docs, len(self.vocab)))
        for i, doc in enumerate(documents):
            tf = Counter(doc)
            for word, count in tf.items():
                if word in self.vocab:
                    self.tfidf_matrix[i, self.vocab[word]] = count * self.idf[word]
        
        # L2 Normalize for cosine similarity
        norms = np.linalg.norm(self.tfidf_matrix, axis=1, keepdims=True)
        self.tfidf_matrix = np.divide(self.tfidf_matrix, norms, out=np.zeros_like(self.tfidf_matrix), where=norms!=0)

    def predict(self, query, k=5):
        """Retrieves titles based on string input using manual TF-IDF."""
        if self.tfidf_matrix is None:
            raise ValueError("Predictor not fitted.")
        
        query_tokens = self._tokenize(query)
        query_tf = Counter(query_tokens)
        query_vec = np.zeros(len(self.vocab))
        
        for word, count in query_tf.items():
            if word in self.vocab:
                query_vec[self.vocab[word]] = count * self.idf[word]
        
        # Normalize query
        norm = np.linalg.norm(query_vec)
        if norm > 0:
            query_vec /= norm
        
        # Cosine similarity
        similarities = np.dot(self.tfidf_matrix, query_vec)
        
        top_indices = similarities.argsort()[-k:][::-1]
        results = self.df.iloc[top_indices].copy()
        results['similarity_score'] = similarities[top_indices]
        
        return results[['tconst', 'primaryTitle', 'genres', 'averageRating', 'similarity_score']]
