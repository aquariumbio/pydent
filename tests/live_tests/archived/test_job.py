import pytest

from pydent.models import Job


@pytest.fixture
def example_job(session, scope='module'):
    """
    example job on Nursery (9/20/2018)
    """
    job = session.Job.find(124660)
    assert job
    return job


class TestJob:

    def test_times(self, example_job):
        job = example_job
        assert job.start_time
        assert job.start_time == '2018-08-22T02:12:06+00:00'
        assert job.end_time
        assert job.end_time == '2018-08-22T02:26:20+00:00'

