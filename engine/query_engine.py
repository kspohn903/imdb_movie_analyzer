import re
import pandas as pd
import numpy as np

SAFE_CHARS = re.compile(r"^[A-Za-z0-9\s_\*\.\'\"\(\)=<>!&|+\-/,%()]+$")

DANGEROUS = [
    re.compile(p)
    for p in [
        r"__", r"\bimport\b", r"\bos\b", r"\bsys\b", r"\bsubprocess\b",
        r"\beval\s*\(", r"\bexec\s*\(", r"\bopen\s*\(", r"\b__import__\b",
        r"\bcompile\s*\(", r"\bglobals\s*\(", r"\blocals\s*\(",
    ]
]

AGG_MAP = {
    "COUNT": "count",
    "AVG": "mean",
    "SUM": "sum",
    "MIN": "min",
    "MAX": "max",
    "STD": "std",
    "VAR": "var",
}


class QueryEngine:
    """SQL-like → pandas query engine with regex validation and safe eval."""

    @staticmethod
    def validate(query: str) -> str:
        if not query or not query.strip():
            raise ValueError("Empty query")
        if not SAFE_CHARS.match(query):
            raise ValueError("Query contains disallowed characters")
        for d in DANGEROUS:
            if d.search(query):
                raise ValueError(f"Query blocked by safety pattern: {d.pattern}")
        return query.strip()

    @staticmethod
    def _parse_where(where: str) -> str:
        has_complex = bool(
            re.search(r"\b(LIKE|IN)\s", where, re.IGNORECASE)
        )
        where = re.sub(
            r"(\w+)\s+BETWEEN\s+(\S+)\s+AND\s+(\S+)",
            r"\1.between(\2, \3)",
            where,
            flags=re.IGNORECASE,
        )
        where = re.sub(
            r"(\w+)\s+LIKE\s+['\"]([^'\"]*)['\"]",
            lambda m: f"{m.group(1)}.str.contains('{m.group(2).replace('%', '')}')",
            where,
            flags=re.IGNORECASE,
        )
        where = re.sub(
            r"(\w+)\s+IN\s+\(([^)]+)\)",
            lambda m: f"{m.group(1)}.isin([{m.group(2)}])",
            where,
            flags=re.IGNORECASE,
        )
        if has_complex:
            parts = re.split(r"\s+(AND|OR)\s+", where, flags=re.IGNORECASE)
            rebuilt = []
            for p in parts:
                p = p.strip()
                if p.upper() == "AND":
                    rebuilt.append("&")
                elif p.upper() == "OR":
                    rebuilt.append("|")
                else:
                    rebuilt.append(f"({p})")
            where = " ".join(rebuilt)
        return where

    @staticmethod
    def _safe_eval(expr: str, df: pd.DataFrame) -> pd.Series:
        clean = expr.strip()
        if not re.match(r"^[\w\s\.\'\"()\[\]=<>!&|+\-*/%,_]+$", clean):
            raise ValueError(f"Unsafe WHERE expression: {expr}")
        if "str.contains" in clean or "isin" in clean or "between" in clean:
            ns = {col: df[col] for col in df.columns}
            ns["__builtins__"] = {}
            return eval(clean, ns)
        clean_lower = re.sub(r"\b(AND|OR|NOT)\b", lambda m: m.group(1).lower(), clean)
        return df.eval(clean_lower)

    @classmethod
    def execute(cls, query: str, df: pd.DataFrame):
        q = cls.validate(query)
        qu = q.upper()

        if qu == "HELP":
            return (
                "Supported queries:\n"
                "  SELECT [cols|*] [WHERE condition] [ORDER BY col ASC|DESC] [LIMIT n]\n"
                "  SELECT agg(col) [WHERE ...] GROUP BY col [ORDER BY ...] [LIMIT n]\n"
                "  DESCRIBE\n"
                "  STATS column\n"
                "  TOP n column\n"
                "  HELP"
            )

        if qu == "DESCRIBE":
            info = {
                "shape": df.shape,
                "columns": list(df.columns),
                "dtypes": {str(k): str(v) for k, v in df.dtypes.items()},
                "missing": df.isnull().sum().to_dict(),
            }
            return info

        m = re.match(r"STATS\s+(\w+)", q, re.IGNORECASE)
        if m:
            col = m.group(1)
            if col not in df.columns:
                raise ValueError(f"Unknown column: {col}")
            return df[col].describe().to_dict()

        m = re.match(r"TOP\s+(\d+)\s+(\w+)", q, re.IGNORECASE)
        if m:
            n, col = int(m.group(1)), m.group(2)
            if col not in df.columns:
                raise ValueError(f"Unknown column: {col}")
            return df[col].value_counts().head(n).reset_index()

        m = re.match(
            r"SELECT\s+(.+?)(?:\s+WHERE\s+(.+?))?(?:\s+GROUP\s+BY\s+(\w+))?(?:\s+ORDER\s+BY\s+(.+?))?(?:\s+LIMIT\s+(\d+))?\s*$",
            q,
            re.IGNORECASE,
        )
        if m:
            select_expr = m.group(1).strip()
            where_clause = m.group(2)
            group_by_col = m.group(3)
            order_by_clause = m.group(4)
            limit_val = m.group(5)

            result = df.copy()

            if where_clause:
                mask = cls._safe_eval(cls._parse_where(where_clause), result)
                result = result[mask]

            if group_by_col:
                if group_by_col not in df.columns:
                    raise ValueError(f"Unknown column for GROUP BY: {group_by_col}")
                agg_m = re.match(
                    r"(\w+)\((\*|\w+)\)(?:\s+AS\s+(\w+))?",
                    select_expr,
                    re.IGNORECASE,
                )
                if agg_m:
                    func_name = agg_m.group(1).upper()
                    agg_target = agg_m.group(2)
                    if func_name not in AGG_MAP:
                        raise ValueError(f"Unknown aggregation: {func_name}")
                    pandas_func = AGG_MAP[func_name]
                    if agg_target == "*":
                        num_cols = result.select_dtypes(
                            include=[np.number]
                        ).columns
                        result = result.groupby(group_by_col)[num_cols].agg(pandas_func)
                    else:
                        result = (
                            result.groupby(group_by_col)[agg_target]
                            .agg(pandas_func)
                            .reset_index()
                        )
                else:
                    result = result.groupby(group_by_col).apply(lambda x: x)
            else:
                if select_expr == "*":
                    pass
                else:
                    cols = [c.strip() for c in select_expr.split(",")]
                    for c in cols:
                        if c not in df.columns:
                            raise ValueError(f"Unknown column: {c}")
                    result = result[cols]

            if order_by_clause:
                parts = order_by_clause.strip().split()
                order_col = parts[0]
                if order_col not in result.columns:
                    raise ValueError(f"Cannot ORDER BY unknown column: {order_col}")
                ascending = len(parts) < 2 or parts[1].upper() != "DESC"
                result = result.sort_values(order_col, ascending=ascending)

            if limit_val:
                result = result.head(int(limit_val))

            return result

        raise ValueError(f"Cannot parse query: {q}")
