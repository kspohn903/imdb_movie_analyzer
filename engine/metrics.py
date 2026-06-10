import numpy as np
from scipy import stats

try:
    import dask.dataframe as dd
except (ImportError, TypeError):
    dd = None

class StaffEvaluator():
    """Evaluates staff based on reputation and entropy metrics."""
    def __init__(self, nconst, name, projects_df):
        self.nconst = nconst
        self.name = name
        self.projects = projects_df 
        
    @property
    def versatility_index(self):
        """Objective parameter: Shannon Entropy of roles."""
        categories = self.projects['category'].value_counts()
        return stats.entropy(categories)

    def get_success_likelihood(self, threshold=7.5):
        """Likelihood estimation using a Gaussian fit of historical performance."""
        if len(self.projects) < 3: 
           return 0.0
        mu, std = stats.norm.fit(self.projects['averageRating'])
        return 1 - stats.norm.cdf(threshold, mu, std)

class StatisticalContext():
    """Encapsulates global dataset parameters for Bayesian calculations."""
    def __init__(self, global_mean, vote_threshold):
        self.C = global_mean
        self.m = vote_threshold
        
    def calculate_weighted_rating(self, v, r):
        """Standard Bayesian Weighted Rating."""
        if v == 0 and self.m == 0: return 0
        return (v / (v + self.m) * r) + (self.m / (v + self.m) * self.C)

class SuccessPredictor():
    """Predicts empirical likelihood using Gaussian distributions."""
    @staticmethod
    def estimate_rating_probability(historical_ratings, threshold=7.5):
        if len(historical_ratings) < 2:
            return 0.0
        mu, std = stats.norm.fit(historical_ratings)
        if std == 0:
            return 1.0 if mu >= threshold else 0.0
        return 1 - stats.norm.cdf(threshold, mu, std)
