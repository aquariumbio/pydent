import time
from collections import Iterable

import pytest

from pydent.base import ModelBase
from pydent.browser import Browser
from pydent.browser import BrowserException
from pydent.exceptions import ForbiddenRequestError

NUM_MODELS = 10


def check_model_in_cache(model, cache):
    """Check if model is in the cache."""
    data = cache.get(model.__class__.__name__, {})
    if not data:
        return "Cache does not have model class: {}".format(model.__class__.__name__)
    m = data.get(model.id, None)
    if not m:
        return "Cache for {} does not have model id {}".format(
            model.__class__.__name__, model.id
        )
    if not m is model:
        return "Model in cache has a different id".format(id(m), id(model))
    return ""


def is_model(v):
    """Check if value is a model base."""
    return issubclass(type(v), ModelBase)


def collect_deserialized_samples(model):
    """Collects the deserialized samples."""
    data = model._get_deserialized_data()
    deserialized_models = []
    for k, v in data.items():
        if is_model(v):
            deserialized_models.append((k, v))
        elif issubclass(type(v), str):
            pass
        elif issubclass(type(v), Iterable):
            for _v in v:
                if is_model(_v):
                    deserialized_models.append((k, _v))
    return deserialized_models


def check_model_deserialized_data(model, cache):
    """Checks to ensure the deserialized samples are in the model cache."""
    deserialized_models = collect_deserialized_samples(model)

    err_msgs = []
    for key, model in deserialized_models:
        err_msg = check_model_in_cache(model, cache)
        if err_msg:
            err_msgs.append(
                "{model}.{key}: {err}".format(model=model, key=key, err=err_msg)
            )
    return err_msgs


def check_model(model, cache):
    """Checks that the model is in the cache and its deserialized samples are
    also in the model cache."""
    err_msgs = []
    err = check_model_in_cache(model, cache)
    if err:
        err_msgs.append(err)
    else:
        err_msgs += check_model_deserialized_data(model, cache)
    return err_msgs


def check_cache_consistency(cache):
    """Validates the consistency of the cache."""
    err_msgs = []
    for model_name, model_dict in cache.items():
        for model in model_dict.values():
            new_errs = check_model(model, cache)
            err_msgs += ["{}: {}".format(model, e) for e in new_errs]
    return err_msgs


def check_models_have(models, key):
    """Check models have deserialized the provided key."""
    n_err_models = 0
    for m in models:
        if not m.is_deserialized(key):
            n_err_models += 1
    if n_err_models:
        return "errors: {}/{} models {} don't have key {}".format(
            n_err_models, len(models), models[0].__class__.__name__, key
        )


def check_models_dont_have(models, key):
    """Check models have not deserialized the provided key."""
    n_err_models = 0
    for m in models:
        if m.is_deserialized(key):
            n_err_models += 1
    if n_err_models:
        return "errors: {}/{} models {} have key {}".format(
            n_err_models, len(models), models[0].__class__.__name__, key
        )


class TestRaisesExceptions:
    def test_get_raises_keyword_err(self, session):
        browser = Browser(session)
        browser.last(NUM_MODELS, "Item")
        with pytest.raises(BrowserException) as e:
            browser.get("Item", "data_assoc")
        assert "Did you mean" in str(e.value)

    def test_get_raises_keyword_err_in_dict(self, session):
        browser = Browser(session)
        browser.last(NUM_MODELS, "Item")
        with pytest.raises(BrowserException) as e:
            browser.get("Item", {"sample": "sample_typ"})
        assert "Did you mean" in str(e.value)


class TestGetAPI:
    """'get' is a dispatching function with a few options.

    These test those options.
    """

    def test_get(self, session):
        """Calling 'get' with just a single keyword should return the models in
        the cache."""

        browser = Browser(session)
        assert browser.get("Sample") == []

        samples = browser.last(NUM_MODELS, "Sample")

        assert browser.get("Sample") == samples

    def test_get_relation(self, session):
        """Calling 'get' with just a single keyword and a string return the
        models the list of models returned."""

        browser = Browser(session)
        assert browser.get("Sample", "sample_type") == []

        samples = browser.last(NUM_MODELS, "Sample")
        sample_types = browser.get("Sample", "sample_type")

        assert sample_types
        for st in sample_types:
            assert st.__class__.__name__ == "SampleType"

    def test_get_relation_with_list_of_models(self, session):
        """Calling 'get' with just a single keyword and a string return the
        models the list of models returned."""

        browser = Browser(session)
        assert browser.get("Sample", "sample_type") == []

        samples = browser.last(NUM_MODELS, "Sample")
        sample_types = browser.get(samples, "sample_type")

        assert sample_types
        for st in sample_types:
            assert st.__class__.__name__ == "SampleType"

    def test_get_nested_relation_from_dict(self, session):
        """Calling 'get' with just a single keyword and a string return the
        models the list of models returned."""

        browser = Browser(session)
        d = {"sample": {"sample_type"}, "object_type": {}}

        assert browser.get("Item", d)

        browser.last(NUM_MODELS, "Item")
        results = browser.get("Item", d)

        assert "sample" in results
        assert "sample_type" in results
        assert "object_type" in results

        assert results["sample"]
        assert results["sample_type"]
        assert results["object_type"]

        errs = check_cache_consistency(browser.model_cache)
        assert not errs


@pytest.mark.parametrize(
    "using_cache",
    [True, False],
    ids=["Using cache (consistent)", "No cache (expect inconsistent)"],
)
def test_consistent_cache_with_attribute_access(session, using_cache):
    """When we do not use the cache, the cache will remain inconsistent when
    attributes are called."""

    def new_sess():
        if using_cache:
            return session.with_cache()
        else:
            return session()

    with new_sess() as sess:
        browser = sess.browser
        samples = browser.last(NUM_MODELS, "Sample")
        errs = check_models_dont_have(samples, "sample_type")
        assert not errs
        browser.retrieve(samples, "sample_type")

        for sample in samples:
            assert sample.is_deserialized("sample_type")
            errs = check_model_in_cache(sample, browser.model_cache)
            assert not errs

            # now we reset the field and attempt to retrieve it
            # if we are using the cache, this should automatically
            # retrieve the cached result
            sample.reset_field("sample_type")
            assert not sample.is_deserialized("sample_type")
            sample.sample_type

        errs = check_cache_consistency(browser.model_cache)
        if using_cache:
            assert not errs
        else:
            assert errs


@pytest.mark.parametrize("method", ["get", "retrieve"])
def test_consistency_with_has_many(session, method):

    browser = Browser(session)
    samples = browser.last(NUM_MODELS, "Sample")

    sample_types = getattr(browser, method)(samples, "sample_type")
    new_samples = getattr(browser, method)(sample_types[:1], "samples")

    # test at least one sample is in the model
    passes = False
    for s in new_samples:
        errs = check_model_in_cache(s, browser.model_cache)
        if not errs:
            passes = True
    assert passes, "At least one of the recalled samples should be in the model cache"


@pytest.mark.parametrize("method", ["get", "retrieve"])
def test_consistency_with_has_many_for_session_cache(session, method):

    with session.with_cache() as sess:
        browser = sess.browser
        samples = browser.last(NUM_MODELS, "Sample")
        sample_types = getattr(browser, method)(samples, "sample_type")

        new_samples = sample_types[0].samples

        # test at least one sample is in the model
        passes = False
        for s in new_samples:
            errs = check_model_in_cache(s, browser.model_cache)
            if not errs:
                passes = True
        assert passes, (
            "At least one of the recalled samples should be in the " "model cache"
        )


class TestGet:
    @pytest.mark.parametrize("method", ["get", "retrieve"], ids=["get()", "retrieve()"])
    @pytest.mark.parametrize(
        "force_refresh",
        [True, False, None],
        ids=["force_refresh", "no_refresh", "default"],
    )
    def test_consistent_cache_with_get_or_retrieve(
        self, session, method, force_refresh
    ):
        """We expect 'retrieve' or 'get' to correctly gather the sample_types
        and place them in the model cache."""

        browser = session.browser
        samples = browser.last(NUM_MODELS, "Sample")

        errs = check_models_dont_have(samples, "sample_type")
        assert not errs

        method = getattr(browser, method)
        if force_refresh is None:
            sample_types = method(samples, "sample_type")
        else:
            sample_types = method(samples, "sample_type", force_refresh=force_refresh)
        assert sample_types, "sample_types_should_be_returned"

        # the browser DO attach the deserialized data to the models
        errs = check_models_have(samples, "sample_type")
        assert not errs

        for sample in samples:
            assert sample.is_deserialized("sample_type")
            errs = check_model_deserialized_data(sample, browser.model_cache)
            assert not errs

        for sample_type in sample_types:
            errs = check_model_in_cache(sample_type, browser.model_cache)
            assert not errs

        for sample in samples:
            errs = check_model_in_cache(sample, browser.model_cache)
            assert not errs

        errs = check_cache_consistency(browser.model_cache)
        assert not errs

    @pytest.mark.parametrize("method", ["get", "retrieve"], ids=["get()", "retrieve()"])
    @pytest.mark.parametrize(
        "force_refresh",
        [True, False, None],
        ids=["force_refresh", "no_refresh", "default"],
    )
    def test_consistent_cache_with_get_or_recursive_retrieve(
        self, session, method, force_refresh
    ):
        """We expect 'retrieve' or 'get' to correctly gather the sample_types
        and place them in the model cache."""

        browser = session.browser
        samples = browser.last(NUM_MODELS, "Sample")

        errs = check_models_dont_have(samples, "sample_type")
        assert not errs

        method = getattr(browser, method)
        if force_refresh is None:
            sample_types = method(samples, "sample_type")
        else:
            sample_types = method(samples, "sample_type", force_refresh=force_refresh)
        assert sample_types, "sample_types_should_be_returned"

        # the browser DO attach the deserialized data to the models
        errs = check_models_have(samples, "sample_type")
        assert not errs

        for sample in samples:
            assert sample.is_deserialized("sample_type")
            errs = check_model_deserialized_data(sample, browser.model_cache)
            assert not errs

        for sample_type in sample_types:
            errs = check_model_in_cache(sample_type, browser.model_cache)
            assert not errs

        for sample in samples:
            errs = check_model_in_cache(sample, browser.model_cache)
            assert not errs

        errs = check_cache_consistency(browser.model_cache)
        assert not errs


class TestForceRefresh:
    def test_retrieve_same_n_samples(self, session):

        browser = Browser(session)
        samples = browser.last(NUM_MODELS, "Sample")
        sample_types = browser.retrieve(samples, "sample_type")
        assert sample_types

        browser2 = Browser(session)
        samples2 = browser2.last(NUM_MODELS, "Sample")
        sample_types2 = browser2.retrieve(samples2, "sample_type", force_refresh=True)

        assert len(sample_types) == len(sample_types2)

    def test_get_same_n_samples(self, session):

        browser = Browser(session)
        samples = browser.last(NUM_MODELS, "Sample")
        sample_types = browser.get(samples, "sample_type")
        assert sample_types

        browser2 = Browser(session)
        samples2 = browser2.last(NUM_MODELS, "Sample")
        sample_types2 = browser2.get(samples2, "sample_type", force_refresh=True)

        assert len(sample_types) == len(sample_types2)

    @pytest.mark.parametrize(
        "force_refresh", [False, None], ids=["no_refresh", "default"]
    )
    @pytest.mark.parametrize(
        "func_name", ["get", "retrieve"], ids=["get()", "retrieve()"]
    )
    def test_retrieve_get_refresh(self, session, force_refresh, func_name):
        """If force refresh is ON, then retrieve should get the EXACT same
        models every time."""
        browser = Browser(session)
        samples = browser.last(NUM_MODELS, "Sample")

        def method():
            if force_refresh is None:
                return getattr(browser, func_name)(samples, "sample_type")
            else:
                return getattr(browser, func_name)(
                    samples, "sample_type", force_refresh=force_refresh
                )

        sample_types = method()
        sample_types2 = method()
        assert sample_types
        assert len(sample_types) == len(sample_types2)

        # no new items
        total_num_items = len({id(x) for x in sample_types + sample_types2})
        assert total_num_items == len(sample_types)

        for st in sample_types:
            errs = check_model_in_cache(st, browser.model_cache)
            assert not errs

        for st in sample_types2:
            errs = check_model_in_cache(st, browser.model_cache)
            assert not errs

    # @pytest.mark.parametrize('func_name', ['get', 'retrieve'],
    #                          ids=['get()', 'retrieve()'])
    # def test_retrieve_get_no_refresh(self, session, func_name):
    #     """If force refresh is ON, then retrieve should get the EXACT same models
    #     every time."""
    #     browser = Browser(session)
    #     samples = browser.last(NUM_MODELS, 'Sample')
    #
    #     def method():
    #         return getattr(browser, func_name)(samples, 'sample_type', force_refresh=True)
    #     sample_types = method()
    #     sample_types2 = method()
    #     assert sample_types
    #     assert len(sample_types) == len(sample_types2)
    #
    #     # no new items
    #     total_num_items = len(set([id(x) for x in sample_types + sample_types2]))
    #     assert total_num_items == 2 * len(sample_types)

    # @pytest.mark.parametrize('force_refresh', [False, True],
    #                          ids=['no_refresh', 'force_refresh'])
    # @pytest.mark.parametrize('func_name', ['get', 'retrieve'],
    #                          ids=['get()', 'retrieve()'])
    # def test_no_refresh_requires_no_requests(self, session, func_name, force_refresh):
    #     """If force refresh is ON, then retrieve should get the EXACT same models
    #     every time."""
    #
    #     with session() as new_session:
    #         browser = Browser(new_session)
    #         samples = browser.last(NUM_MODELS, 'Sample')
    #
    #         def method():
    #             return getattr(browser, func_name)(samples, 'sample_type', force_refresh=True)
    #         method()
    #
    #         browser.session.using_requests = False
    #         if force_refresh:
    #             with pytest.raises(ForbiddenRequestError):
    #                 method()


def test_speed_improvements(session):
    n = 10

    t1 = time.time()
    n1 = session._aqhttp.num_requests
    items = session.Item.last(n)
    samples = [item.sample for item in items]
    object_types = [item.object_type for item in items]
    sample_types = [sample.sample_type for sample in samples if sample]
    for st in sample_types:
        st.field_types
    t2 = time.time()
    n2 = session._aqhttp.num_requests

    t3 = time.time()
    n3 = session._aqhttp.num_requests
    browser = Browser(session)
    items = browser.last(n, "Item")
    browser.get(items, {"sample": {"sample_type": "field_types"}, "object_type": []})
    t4 = time.time()
    n4 = session._aqhttp.num_requests

    fold_diff = (t2 - t1) / (t4 - t3)

    print("Browser is {} times faster than nested for-loops".format(fold_diff))
    print("Browser uses {} requests, while for-loops use {}".format(n4 - n3, n2 - n1))
    assert fold_diff > 1
