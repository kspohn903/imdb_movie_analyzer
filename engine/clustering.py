from sklearn.neighbors import NearestNeighbors
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import FeatureUnion
import pandas as pd
import numpy as np

class ProximityEngine:
    """KNN-based likelihood estimation for neighborhood clustering."""
    def __init__(self, k=10):
        self.model = NearestNeighbors(n_neighbors=k, metric='cosine')
        self.tfidf = TfidfVectorizer(stop_words='english')
        self.scaler = StandardScaler()
        self.data_ref = None

    def build_feature_matrix(self, df_computed):
        """Fits proximity based on Genres, Ratings, and Runtimes."""
        self.data_ref = df_computed.reset_index(drop=True)
        
        # Genre Vectorization
        genre_matrix = self.tfidf.fit_transform(self.data_ref['genres'].fillna('None'))
        
        # Numerical scaling (Rating/Runtime)
        numerical_cols = ['averageRating', 'numVotes']
        numerical_matrix = self.scaler.fit_transform(self.data_ref[numerical_cols].fillna(0))
        
        # Combined Feature Space
        combined = np.hstack([genre_matrix.toarray(), numerical_matrix])
        self.model.fit(combined)
        return combined

    def get_similar_titles(self, feature_vector, top_n=10):
        distances, indices = self.model.kneighbors(feature_vector.reshape(1, -1))
        return self.data_ref.iloc[indices[0]]
