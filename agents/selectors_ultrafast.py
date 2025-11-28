# core/selectors_ultrafast.py

class UltraFastSelector:

    KEYWORDS = {
        "sale": ["FactInternetSales"],
        "internet": ["FactInternetSales"],
        "product": ["DimProduct"],
        "customer": ["DimCustomer"],
        "date": ["DimDate"],
        "year": ["DimDate"],
        "month": ["DimDate"],
    }

    def select(self, question: str, schema: dict):
        q = question.lower()
        tables = set()

        for kw, tbls in self.KEYWORDS.items():
            if kw in q:
                tables.update(tbls)

        # automatic fact + neighbor dims (fast heuristic)
        for t in schema.keys():
            if t.lower().startswith("fact"):
                tables.add(t)

        return list(tables)
