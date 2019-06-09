import pytest

# skip tests
pytestmark = pytest.mark.skip("These tests utilize a live session with alot of requests."
                              "In the future, we may want to utilize something like pyvrc to avoid"
                              "sending live requests to Aquarium.")

@pytest.mark.benchmark
class TestBenchmarkQuery(object):

    def method1_single_query(self, session):
        return session.Plan.last(20)

    def method2_server_side_serialization(self, session):
        return session.Plan.last(20, include={
            'operations': {
                'include': {
                    'field_values': {
                        'include': ['sample', 'item']
                    }
                }
            }
        })

    def method3_using_built_in_cache(self, session):
        with session.with_cache() as sess:
            return sess.Plan.last(20)

    def method4_using_browser(self, session):
        with session.with_cache() as sess:
            plans = sess.Plan.last(20)
            sess.browser.recursive_retrieve(plans, {
                'operations': {
                    'field_values': {
                        'sample',
                        'item'
                    }
                }
            })
            return plans

    def benchmark_test(self, get_plans, session):
        def _benchmark_test():
            plans = get_plans(session)
            for p in plans:
                for op in p.operations:
                    for fv in op.field_values:
                        fv.sample
            return plans
        return _benchmark_test

    @pytest.mark.parametrize('method', [
        'method1_single_query',
        'method2_server_side_serialization',
        'method3_using_built_in_cache',
        'method4_using_browser'
    ])
    def test_query_benchmark(self, benchmark, session, method):
        func = getattr(self, method)
        benchmark(self.benchmark_test(func, session))
