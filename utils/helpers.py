import re

class RegexMatcher:
    @staticmethod
    def match_imperfect(query, target_list):
        """Standard regex token specifier matching."""
        pattern = re.compile(f".*{re.escape(query)}.*", re.IGNORECASE)
        return [t for t in target_list if pattern.match(str(t))]

    @staticmethod
    def clean_currency_string(val):
        """Utility for future profitability modules."""
        if not val or val == '\\N': return 0.0
        return float(re.sub(r'[^\d.]', '', str(val)))
