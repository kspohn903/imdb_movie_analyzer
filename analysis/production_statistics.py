from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import os

class ResultType(Enum):
    BASELINE_DIR = os.environ["BASELINE_EDA_DIR"] = "execution_file_results/baseline_eda_statistics"
    CREW_REEL = f"{BASELINE_DIR}/crew_reel_percentage.tsv"
    VELOCITY = f"{BASELINE_DIR}/production_velocity.tsv"

@dataclass
class ProductionTimeline():
    """Dynamic evaluation of a title's chronological footprint."""
    tconst: str
    primary_title: str
    start_year: int
    end_year: int = None
    
    def __post_init__(self):
        self.is_ongoing = self.end_year is None
        self.lifespan = (self.end_year or datetime.now().year) - self.start_year
    
    def to_dict(self):
        return {
            "tconst": self.tconst,
            "longevity": self.lifespan,
            "status": "Archived" if not self.is_ongoing else "Active"
        }

class ProductionAnalyzer():
    """Handles the heavy lifting of mapping Dask rows to Timeline objects."""
    def __init__(self, dask_basics):
        self.df = dask_basics

    def get_entity_velocity(self, query_filter):
        """Returns a collection of ProductionTimeline objects."""
        results = self.df[query_filter].compute()
        return [
            ProductionTimeline(
                row['tconst'], 
                row['primaryTitle'], 
                int(row['startYear']), 
                int(row['endYear']) if row['endYear'] != '\\N' else None
            )
            for _, row in results.iterrows()
        ]

@dataclass
class TitleLifecycle():
    tconst: str
    start_year: int
    end_year: int = None

    def calculate_longevity(self):
        """Returns years from start to finish/present."""
        effective_end = self.end_year if self.end_year else datetime.now().year
        return max(0, effective_end - self.start_year)

class ProductionStatsManager():
    """Manages collections of title lifecycles."""
    @staticmethod
    def get_aggregate_longevity(lifecycle_list):
        if not lifecycle_list: return 0
        return sum(item.calculate_longevity() for item in lifecycle_list) / len(lifecycle_list)
