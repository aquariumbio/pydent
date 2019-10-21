from pydent.browser import Browser


def test_relationship_network(session):
    with session.with_cache() as sess:

        def get_models(m):
            for fv in m.field_values:
                if fv.sample:
                    yield fv.sample, {}

        def cache(models):
            if models:
                session = models[0].session
                session.browser.get(models, {"field_values": "sample"})

        samples = sess.Sample.last(100)
        g = sess.browser.relationship_network(
            samples, get_models=get_models, cache_func=cache
        )

        assert g.number_of_nodes() > 100
        print(g.number_of_nodes())
        for e in g.edges():
            print(e)

        roots = []
        for n in g.nodes:
            if not list(g.predecessors(n)):
                roots.append(n)

        for n in roots:
            m = getattr(sess, n[0]).find(n[1])
            for fv in m.field_values:
                assert not fv.sample


def test_sample_network(session):

    with session.with_cache() as sess:
        samples = session.Sample.last(100)
        sess.browser.sample_network(samples)


def test_plan_network(session):

    with session.with_cache() as sess:
        sess.set_verbose(True)
        browser = Browser(session)

        browser.last(10, "Plan")
        operations = browser.get("Plan", "operations")

        def get_models(model):
            if model.__class__.__name__ == "Operation":
                for op in model.successors:
                    if op is None:
                        raise Exception
                    yield op, {}

        def cache_func(models):
            session = models[0].session
            session.browser.get(
                models,
                {
                    "plans": {
                        "operations": {
                            "field_values": {
                                "wires_as_dest": {
                                    "source": "operation",
                                    "destination": "operation",
                                },
                                "wires_as_source": {
                                    "source": "operation",
                                    "destination": "operation",
                                },
                            }
                        }
                    }
                },
            )

        g = sess.browser.relationship_network(
            operations, get_models=get_models, cache_func=cache_func, strict_cache=True
        )
    print(g.number_of_nodes())
    print(g.number_of_edges())
