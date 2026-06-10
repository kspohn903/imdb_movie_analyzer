import unittest
import pandas as pd
import numpy as np
from engine.query_engine import QueryEngine
from analysis.production_statistics import TitleLifecycle, ProductionStatsManager

try:
    from engine.metrics import StatisticalContext, SuccessPredictor
    HAS_DASK = True
except (ImportError, TypeError):
    HAS_DASK = False


SAMPLE_DF = pd.DataFrame(
    {
        "tconst": [f"tt{i:07d}" for i in range(1, 11)],
        "primaryTitle": [
            "Alpha", "Beta", "Gamma", "Delta", "Epsilon",
            "Zeta", "Eta", "Theta", "Iota", "Kappa",
        ],
        "genres": [
            "Action,Drama", "Comedy", "Drama,Romance", "Action,Thriller",
            "Comedy,Drama", "Horror", "Sci-Fi,Action", "Romance,Comedy",
            "Thriller,Drama", "Documentary",
        ],
        "startYear": list(range(2000, 2010)),
        "averageRating": [8.5, 6.1, 7.8, 7.2, 6.9, 5.5, 8.1, 7.0, 6.4, 9.0],
        "numVotes": [10000, 200, 5000, 3000, 1500, 800, 7000, 4000, 2500, 12000],
        "runtimeMinutes": [120, 90, 110, 105, 95, 100, 130, 98, 115, 85],
    }
)


class TestIMDBAnalysisEngine(unittest.TestCase):

    def test_production_longevity(self):
        lifecycle = TitleLifecycle(tconst="tt01", start_year=2000, end_year=2010)
        self.assertEqual(lifecycle.calculate_longevity(), 10)
        ongoing = TitleLifecycle(tconst="tt02", start_year=2020, end_year=None)
        self.assertEqual(ongoing.calculate_longevity(), 2026 - 2020)


@unittest.skipIf(not HAS_DASK, "dask not available")
class TestMetrics(unittest.TestCase):

    def setUp(self):
        self.ctx = StatisticalContext(global_mean=7.0, vote_threshold=100)

    def test_bayesian_weighting(self):
        low_vote_rating = self.ctx.calculate_weighted_rating(v=10, r=10.0)
        self.assertLess(low_vote_rating, 8.0)
        high_vote_rating = self.ctx.calculate_weighted_rating(v=1000, r=10.0)
        self.assertGreater(high_vote_rating, 9.0)

    def test_likelihood_estimation(self):
        perfect_history = [8.0, 8.5, 9.0, 8.2, 8.7]
        prob = SuccessPredictor.estimate_rating_probability(
            perfect_history, threshold=7.5
        )
        self.assertGreater(prob, 0.8)


class TestQueryEngine(unittest.TestCase):

    def test_validate_rejects_dangerous(self):
        with self.assertRaises(ValueError):
            QueryEngine.validate("SELECT * WHERE __import__('os').system('ls')")
        with self.assertRaises(ValueError):
            QueryEngine.validate("SELECT * ; DROP TABLE")
        with self.assertRaises(ValueError):
            QueryEngine.validate("import os; os.system('rm -rf /')")

    def test_validate_accepts_legit(self):
        self.assertTrue(
            QueryEngine.validate("SELECT * WHERE averageRating > 7.5 LIMIT 10")
        )
        self.assertTrue(QueryEngine.validate("DESCRIBE"))
        self.assertTrue(QueryEngine.validate("STATS averageRating"))
        self.assertTrue(QueryEngine.validate("TOP 5 genres"))

    def test_describe(self):
        result = QueryEngine.execute("DESCRIBE", SAMPLE_DF)
        self.assertEqual(result["shape"], (10, 7))

    def test_stats(self):
        result = QueryEngine.execute("STATS averageRating", SAMPLE_DF)
        self.assertAlmostEqual(result["mean"], 7.25, places=2)

    def test_top(self):
        result = QueryEngine.execute("TOP 3 genres", SAMPLE_DF)
        self.assertEqual(len(result), 3)

    def test_select_all(self):
        result = QueryEngine.execute("SELECT * LIMIT 3", SAMPLE_DF)
        self.assertEqual(len(result), 3)
        self.assertEqual(list(result.columns), list(SAMPLE_DF.columns))

    def test_select_columns(self):
        result = QueryEngine.execute(
            "SELECT primaryTitle, averageRating LIMIT 5", SAMPLE_DF
        )
        self.assertEqual(list(result.columns), ["primaryTitle", "averageRating"])
        self.assertEqual(len(result), 5)

    def test_select_where(self):
        result = QueryEngine.execute(
            "SELECT primaryTitle, averageRating WHERE averageRating > 7.5", SAMPLE_DF
        )
        self.assertTrue((result["averageRating"] > 7.5).all())

    def test_select_where_order_limit(self):
        result = QueryEngine.execute(
            "SELECT primaryTitle, averageRating WHERE averageRating > 6.0 ORDER BY averageRating DESC LIMIT 3",
            SAMPLE_DF,
        )
        self.assertEqual(len(result), 3)
        self.assertEqual(result.iloc[0]["primaryTitle"], "Kappa")

    def test_select_group_by_avg(self):
        df = SAMPLE_DF.copy()
        df["decade"] = (df["startYear"] // 10) * 10
        result = QueryEngine.execute(
            "SELECT AVG(averageRating) GROUP BY decade", df
        )
        self.assertIn("averageRating", result.columns)
        self.assertIn("decade", result.columns)

    def test_select_where_like(self):
        result = QueryEngine.execute(
            "SELECT primaryTitle WHERE genres LIKE '%Action%'", SAMPLE_DF
        )
        self.assertIn("Alpha", result["primaryTitle"].values)
        self.assertIn("Eta", result["primaryTitle"].values)

    def test_help(self):
        result = QueryEngine.execute("HELP", SAMPLE_DF)
        self.assertIn("SELECT", result)

    def test_validation_blocks_semicolon(self):
        with self.assertRaises(ValueError):
            QueryEngine.execute("SELECT *; DROP TABLE", SAMPLE_DF)

    def test_validation_blocks_import(self):
        with self.assertRaises(ValueError):
            QueryEngine.execute("SELECT * WHERE import os", SAMPLE_DF)

    def test_validation_blocks_eval_call(self):
        with self.assertRaises(ValueError):
            QueryEngine.execute("SELECT * WHERE eval('x')", SAMPLE_DF)

    def test_unknown_column(self):
        with self.assertRaises(ValueError):
            QueryEngine.execute("SELECT nonexistent", SAMPLE_DF)


if __name__ == "__main__":
    unittest.main()
