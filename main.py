import argparse
import os
import sys
import json
import datetime
import pandas as pd
import numpy as np

try:
    import dask.dataframe as dd
except (ImportError, TypeError):
    dd = None

from config import OUTPUT_DIR, GRAPH_DIR
from data.loader import IMDBLoader
from analysis.basic_etl import BasicStatisticsVisualizer
from analysis.basic_eda import BasicEDA
from analysis.time_series import TimeSeriesAnalyzer
from analysis.visualizer import EmpiricalVisualizer
from analysis.production_statistics import (
    ProductionTimeline,
    ProductionStatsManager,
)
from engine.knn_model import MovieKNNPredictor
from engine.rag_predictor import TitleRAGPredictor
from engine.query_engine import QueryEngine
from engine.metrics import StatisticalContext, SuccessPredictor
from db_models.analyzer import RelationalAnalyzer
from utils.helpers import RegexMatcher

try:
    from engine.clustering import ProximityEngine
except Exception:
    ProximityEngine = None

try:
    from engine.metrics import StaffEvaluator
except Exception:
    StaffEvaluator = None

try:
    import matplotlib.pyplot as plt
    HAS_MPL = True
except Exception:
    HAS_MPL = False


def _out_dir(mode):
    path = os.path.join(OUTPUT_DIR, mode)
    os.makedirs(path, exist_ok=True)
    return path


def _graph_dir(mode):
    path = os.path.join(GRAPH_DIR, mode)
    os.makedirs(path, exist_ok=True)
    return path


def _save_tsv(df, mode, name):
    path = os.path.join(_out_dir(mode), f"{name}.tsv")
    df.to_csv(path, sep="\t", index=False)
    return path


def _save_json(obj, mode, name):
    path = os.path.join(_out_dir(mode), f"{name}.json")
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, default=str)
    return path


def load_data(loader):
    result = loader.load_merged_lake()
    if hasattr(result, "compute"):
        return result.compute()
    return result


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_query(args, loader):
    df = load_data(loader)
    result = QueryEngine.execute(args.sql, df)
    if isinstance(result, dict):
        for k, v in result.items():
            print(f"{k}: {v}")
        _save_json(result, "query", f"query_{args.label}")
    elif isinstance(result, pd.DataFrame):
        print(result.to_string(index=False))
        _save_tsv(result, "query", f"query_{args.label}")
    elif isinstance(result, str):
        print(result)
    else:
        print(result)


def cmd_describe(args, loader):
    df = load_data(loader)
    info = {
        "shape": list(df.shape),
        "columns": list(df.columns),
        "dtypes": {str(k): str(v) for k, v in df.dtypes.items()},
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1024 ** 2, 2),
    }
    print(f"Shape: {info['shape']}")
    print(f"\nColumns ({len(info['columns'])}):")
    for c in df.columns:
        print(f"  {c}: {df[c].dtype}")
    print(f"\nMemory usage: {info['memory_mb']} MB")
    _save_json(info, "describe", f"describe_{args.label}")


def cmd_stats(args, loader):
    df = load_data(loader)
    if args.column:
        if args.column not in df.columns:
            print(f"Column '{args.column}' not found.")
            sys.exit(1)
        result = df[args.column].describe()
        print(result)
        _save_json(result.to_dict(), "stats", f"stats_{args.column}_{args.label}")
    else:
        result = df.describe()
        print(result)
        _save_tsv(result.reset_index(), "stats", f"stats_all_{args.label}")


def cmd_eda(args, loader):
    df = load_data(loader)
    gdir = _graph_dir("eda")
    print("Running Exploratory Data Analysis...")
    eda = BasicEDA(df1=df)

    spread = eda.get_spread(df)
    spread_rec = {
        "n_years": spread[0],
        "year_range": spread[1],
        "n_title_types": spread[2],
        "n_genres": spread[3],
    }
    _save_json(spread_rec, "eda", f"spread_{args.label}")

    top_genres = eda.get_top_genres_grouped_by_decade(df)
    if HAS_MPL:
        _plot_decade_genres(top_genres, gdir, args.label)

    print("\nEDA complete. Results saved to execution_file_results/eda/")


def _plot_decade_genres(top_genres, gdir, label):
    for decade_key, data in top_genres.items():
        if data.empty:
            continue
        plt.figure(figsize=(10, 5))
        ax = data.plot.bar(x="genres", y="averageRating", legend=False)
        plt.title(f"Top Genres by Decade: {decade_key}")
        plt.ylabel("Avg Rating")
        plt.tight_layout()
        plt.savefig(os.path.join(gdir, f"genres_{decade_key}_{label}.png"))
        plt.close()


def cmd_etl(args, etl):
    print("Running ETL pipeline...")
    if args.download:
        for alias in args.download:
            df = etl.download_file(alias)
            print(f"Downloaded {alias}: {df.shape}")
    df = etl.get_merged_title_dfs()
    print(f"Merged shape: {df.shape}")
    nullity = etl.get_nullity_count(df)
    print(f"Nullity:\n{nullity}")
    nullity.to_csv(os.path.join(_out_dir("etl"), f"nullity_{args.label}.tsv"), sep="\t")


def cmd_knn(args, loader):
    df = load_data(loader)
    print(f"KNN search for target: {args.target} (k={args.k})")
    knn = MovieKNNPredictor(k=args.k)
    knn.prepare_features(df)
    knn.fit()
    results = knn.predict(args.target)
    if results is None:
        print(f"Title '{args.target}' not found.")
    else:
        print(results.to_string(index=False))
        _save_tsv(results, "knn", f"knn_{args.target}_{args.label}")


def cmd_timeseries(args, loader):
    df = load_data(loader)
    gdir = _graph_dir("timeseries")
    print("Time Series Analysis...")
    ts = TimeSeriesAnalyzer(df)

    yearly = ts.analyze_title_progression(
        output_path=os.path.join(gdir, f"progression_{args.label}.png")
    )
    yearly_df = yearly.reset_index()
    yearly_df.columns = ["startYear", "title_count"]
    _save_tsv(yearly_df, "timeseries", f"progression_{args.label}")

    genre_ev = ts.analyze_genre_evolution(top_n_genres=args.top_genres)
    genre_df = genre_ev.reset_index()
    _save_tsv(genre_df, "timeseries", f"genre_evolution_{args.label}")

    if HAS_MPL:
        genre_ev.plot(kind="line", figsize=(12, 6))
        plt.title(f"Evolution of Top {args.top_genres} Genres")
        plt.savefig(os.path.join(gdir, f"genre_evolution_{args.label}.png"))
        plt.close()


def cmd_rag(args, loader):
    df = load_data(loader)
    print(f"RAG retrieval for: '{args.query}' (k={args.k})")
    rag = TitleRAGPredictor()
    rag.fit(df)
    results = rag.predict(args.query, k=args.k)
    print(results.to_string(index=False))
    _save_tsv(results, "rag", f"rag_{args.label}")


def cmd_relational(args, loader):
    if dd is None:
        print("dask is required for relational analysis.")
        return
    data_dir = args.data_dir
    principals = dd.read_csv(
        os.path.join(data_dir, "title.principals.tsv"),
        sep="\t", na_values="\\N",
    ).compute()
    names = dd.read_csv(
        os.path.join(data_dir, "name.basics.tsv"),
        sep="\t", na_values="\\N",
    ).compute()
    titles = load_data(loader)
    print(f"Relational analysis for: {args.name}")
    rel = RelationalAnalyzer(principals, names, titles)

    impact = rel.analyze_person_impact(args.name)
    if impact:
        for k, v in impact.items():
            print(f"  {k}: {v}")
        _save_json(impact, "relational", f"impact_{args.name}_{args.label}")
    else:
        print(f"Person '{args.name}' not found.")
        return

    collab = rel.get_top_collaborators(args.name)
    if collab is not None and not collab.empty:
        print(f"\nTop collaborators:")
        print(collab.to_string(index=False))
        _save_tsv(collab, "relational", f"collaborators_{args.name}_{args.label}")

    if StaffEvaluator is not None:
        person = names[names["primaryName"].str.contains(args.name, case=False, na=False)]
        if not person.empty:
            nconst = person.iloc[0]["nconst"]
            person_titles = principals[principals["nconst"] == nconst].merge(titles, on="tconst")
            se = StaffEvaluator(nconst, person.iloc[0]["primaryName"], person_titles)
            staff_rec = {
                "nconst": nconst,
                "name": person.iloc[0]["primaryName"],
                "versatility_index": float(se.versatility_index),
                "success_likelihood": float(
                    se.get_success_likelihood(threshold=args.threshold)
                ),
            }
            print(f"\nStaff evaluation:")
            for k, v in staff_rec.items():
                print(f"  {k}: {v}")
            _save_json(staff_rec, "relational", f"staff_eval_{args.name}_{args.label}")


def cmd_production(args, loader):
    basics = loader.load_basics()
    if hasattr(basics, "compute"):
        computed = basics.compute()
    else:
        computed = basics
    filtered = computed[computed["startYear"].astype(float) > args.min_year]
    timelines = [
        ProductionTimeline(
            row["tconst"], row["primaryTitle"],
            int(row["startYear"]),
            int(row["endYear"]) if row["endYear"] != "\\N" else None,
        )
        for _, row in filtered.iterrows()
    ]
    avg = ProductionStatsManager.get_aggregate_longevity(timelines)
    print(f"Found {len(timelines)} titles (from {args.min_year}+)")
    print(f"Average longevity: {avg:.1f} years")
    rows = []
    for t in timelines:
        rows.append({
            "tconst": t.tconst,
            "primaryTitle": t.primary_title,
            "startYear": t.start_year,
            "endYear": t.end_year or "",
            "lifespan": t.lifespan,
            "status": "Archived" if not t.is_ongoing else "Active",
        })
        print(f"  {t.tconst} | {t.primary_title} ({t.start_year}-{t.end_year or 'ongoing'})")
    pdf = pd.DataFrame(rows)
    _save_tsv(pdf, "production", f"velocity_{args.label}")

    if HAS_MPL:
        gdir = _graph_dir("production")
        EmpiricalVisualizer.save_velocity_plot(
            timelines, f"longevity_{args.label}", output_dir=gdir
        )


def cmd_cluster(args, loader):
    if ProximityEngine is None:
        print("sklearn is required for clustering.")
        return
    df = load_data(loader)
    print("Building proximity clusters...")
    engine = ProximityEngine(k=args.k)
    engine.build_feature_matrix(df)
    print(f"Model fitted with {len(engine.data_ref)} titles")
    rec = {
        "k": args.k,
        "n_titles": len(engine.data_ref),
        "n_features": engine.model.n_features_in_,
    }
    _save_json(rec, "cluster", f"cluster_{args.label}")


def cmd_metrics(args, loader):
    ratings = loader.load_ratings()
    if hasattr(ratings, "compute"):
        ratings = ratings.compute()
    ctx = StatisticalContext(
        float(ratings["averageRating"].mean()),
        float(ratings["numVotes"].quantile(0.90)),
    )
    print(f"Global mean (C): {ctx.C:.4f}")
    print(f"Vote threshold (m): {ctx.m:.0f}")

    n = min(args.n, len(ratings))
    sample = ratings.sample(n)
    rows = []
    for _, row in sample.iterrows():
        wr = ctx.calculate_weighted_rating(row["numVotes"], row["averageRating"])
        print(f"  {row['tconst']}: raw={row['averageRating']} weighted={wr:.4f}")
        rows.append({
            "tconst": row["tconst"],
            "raw_rating": float(row["averageRating"]),
            "numVotes": int(row["numVotes"]),
            "weighted_rating": round(wr, 4),
        })
    pdf = pd.DataFrame(rows)
    _save_tsv(pdf, "metrics", f"bayesian_sample_{args.label}")


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        description="Movie Title Analysis EDA Query Engine"
    )
    parser.add_argument("--data_dir", default="data", help="Directory containing IMDb TSV files")
    parser.add_argument("--label", default=None, help="Output file label (default: timestamp)")

    sub = parser.add_subparsers(dest="mode", required=True)

    p_query = sub.add_parser("query", help="Run a SQL-like query against the dataset")
    p_query.add_argument("sql", help='e.g., "SELECT * WHERE averageRating > 7.5 LIMIT 10"')
    p_query.set_defaults(func=cmd_query)

    p_describe = sub.add_parser("describe", help="Dataset overview (shape, dtypes, missing)")
    p_describe.set_defaults(func=cmd_describe)

    p_stats = sub.add_parser("stats", help="Column statistics")
    p_stats.add_argument("--column", "-c", help="Column name; omit for full describe")
    p_stats.set_defaults(func=cmd_stats)

    p_eda = sub.add_parser("eda", help="Exploratory Data Analysis")
    p_eda.set_defaults(func=cmd_eda)

    p_etl = sub.add_parser("etl", help="ETL pipeline (download + merge)")
    p_etl.add_argument("--download", "-d", nargs="*", choices=[
        "title_basics", "title_ratings", "title_episodes", "title_crews",
        "title_principals", "title_akas", "name_basics",
    ], help="Datasets to download")
    p_etl.set_defaults(func=cmd_etl)

    p_knn = sub.add_parser("knn", help="KNN movie recommendations")
    p_knn.add_argument("--target", required=True, help="tconst of the title")
    p_knn.add_argument("--k", type=int, default=5, help="Number of neighbors")
    p_knn.set_defaults(func=cmd_knn)

    p_ts = sub.add_parser("timeseries", help="Time series analysis")
    p_ts.add_argument("--top_genres", type=int, default=5, help="Top N genres to track")
    p_ts.set_defaults(func=cmd_timeseries)

    p_rag = sub.add_parser("rag", help="RAG title retrieval")
    p_rag.add_argument("query", help="Search text")
    p_rag.add_argument("--k", type=int, default=5)
    p_rag.set_defaults(func=cmd_rag)

    p_rel = sub.add_parser("relational", help="Person impact analysis")
    p_rel.add_argument("name", help="Person name")
    p_rel.add_argument("--threshold", type=float, default=7.5, help="Success rating threshold")
    p_rel.set_defaults(func=cmd_relational)

    p_prod = sub.add_parser("production", help="Production velocity / longevity")
    p_prod.add_argument("--min_year", type=int, default=2000)
    p_prod.add_argument("--top", type=int, default=10)
    p_prod.set_defaults(func=cmd_production)

    p_cluster = sub.add_parser("cluster", help="Build proximity clusters")
    p_cluster.add_argument("--k", type=int, default=10)
    p_cluster.set_defaults(func=cmd_cluster)

    p_metrics = sub.add_parser("metrics", help="Bayesian weighted rating sample")
    p_metrics.add_argument("--n", type=int, default=5, help="Number of sample titles")
    p_metrics.set_defaults(func=cmd_metrics)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if not args.label:
        args.label = ts

    loader = IMDBLoader(args.data_dir)
    etl = BasicStatisticsVisualizer()

    if args.mode == "etl":
        cmd_etl(args, etl)
    else:
        args.func(args, loader)


if __name__ == "__main__":
    main()
