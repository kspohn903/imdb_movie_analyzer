import os

# Path Management
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "execution_file_results")
GRAPH_DIR = os.path.join(BASE_DIR, "graphics")

# Dask Performance Tuning (Rightsized for 8GB RAM)
DASK_SETTINGS = {
    "n_workers": 2,
    "threads_per_worker": 2,
    "memory_limit": "3GB",  # Leaves 2GB overhead for OS/Other
    "blocksize": "64MB"      # Keeps task graph manageable
}

# Empirical Constants
VOTE_QUANTILE_THRESHOLD = 0.95
SIGNIFICANCE_LEVEL = 0.05
