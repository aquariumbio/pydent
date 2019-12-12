class QueryBuilder:
    class Not:
        def __init__(self, v):
            self.v = v

    @classmethod
    def sql(cls, data):
        rows = []
        for k, v in data.items():
            if not isinstance(v, cls.Not):
                rows.append('{} = "{}"'.format(k, v))
            else:
                rows.append('{} != "{}"'.format(k, v.v))
        return " AND ".join(rows)
