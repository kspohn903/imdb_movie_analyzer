import pandas as pd
import numpy as np
from scipy.spatial.distance import cdist

class MovieKNNPredictor:
    def __init__(self, k=5):
        self.k = k
        self.is_fitted = False
        self.feature_matrix = None
        self.df = None
        self.genres_list = []
        self.types_list = []

    def prepare_features(self, df):
        """
        Features: Genres (One-hot), titleType (One-hot), runtimeMinutes (Scaled)
        Manual implementation to avoid scikit-learn dependency.
        """
        df = df.copy()
        df['genres_split'] = df['genres'].fillna('').apply(lambda x: x.split(',') if isinstance(x, str) else [])
        df['runtimeMinutes'] = pd.to_numeric(df['runtimeMinutes'], errors='coerce').fillna(0)
        
        # One-hot encode genres
        all_genres = set()
        for g_list in df['genres_split']:
            all_genres.update(g_list)
        self.genres_list = sorted(list(all_genres))
        
        genre_matrix = np.zeros((len(df), len(self.genres_list)))
        for i, g_list in enumerate(df['genres_split']):
            for g in g_list:
                if g in self.genres_list:
                    genre_matrix[i, self.genres_list.index(g)] = 1
        
        # One-hot encode titleType
        self.types_list = sorted(df['titleType'].unique().tolist())
        type_matrix = np.zeros((len(df), len(self.types_list)))
        for i, t in enumerate(df['titleType']):
            if t in self.types_list:
                type_matrix[i, self.types_list.index(t)] = 1
        
        # Scale runtime (Simple Min-Max)
        runtimes = df['runtimeMinutes'].values.reshape(-1, 1)
        rt_min = runtimes.min()
        rt_max = runtimes.max()
        if rt_max > rt_min:
            runtime_scaled = (runtimes - rt_min) / (rt_max - rt_min)
        else:
            runtime_scaled = runtimes * 0
        
        # Combine features
        self.feature_matrix = np.hstack([genre_matrix, type_matrix, runtime_scaled])
        self.df = df.reset_index(drop=True)
        self.is_fitted = True

    def fit(self):
        # NearestNeighbors in scipy is just cdist
        pass

    def predict(self, title_id):
        if not self.is_fitted:
            raise ValueError("Model not fitted.")
        
        idx_list = self.df[self.df['tconst'] == title_id].index
        if len(idx_list) == 0:
            return None
        
        idx = idx_list[0]
        target_vec = self.feature_matrix[idx].reshape(1, -1)
        
        # Calculate cosine distances
        distances = cdist(target_vec, self.feature_matrix, metric='cosine')[0]
        
        # Get top K+1 (to exclude self)
        indices = np.argsort(distances)[:self.k + 1]
        
        # Exclude the title itself
        results_indices = [i for i in indices if i != idx][:self.k]
        results = self.df.iloc[results_indices]
        return results[['tconst', 'primaryTitle', 'genres', 'runtimeMinutes', 'averageRating']]
