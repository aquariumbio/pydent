from pydent.models import User, Group, Sample, SampleType
import requests
from pydent import AqSession
from pydent.session import AqHTTP


def test_load_model_from_json(monkeypatch, mock_login_post):
    """
    Tests heirarchical loading of a JSON file into Trident Models.

    Should return a User with name and login attributes. Groups attribute should
    contain a list of Group models.
    """
    # Create a mock session
    monkeypatch.setattr(requests, "post", mock_login_post)
    aquarium_url = "http://52.52.525.52"
    session = AqSession("username", "password", aquarium_url)

    # monkey patch the "find" method
    def find_user(*args, json_data=None, **kwargs):
        user_default = {
            "name": "default_name",
            "login": "default_login",
            "groups": [
                {"id": 1, "name": "default_group1"},
                {"id": 2, "name": "defulat_group2"}
            ]
        }
        json_data.update(user_default)
        return json_data

    monkeypatch.setattr(AqHTTP, "post", find_user)

    # find a user
    u = session.User.find_using_session(1)

    # assert user properties
    assert isinstance(u, User)
    assert u.id == 1
    assert u.name == "default_name"
    assert u.login == "default_login"

    # test load groups
    g = u.groups
    assert len(u.groups) == 2
    assert isinstance(u.groups[0], Group)
    assert u.groups[1].id == 2


def test_load_model_with_database_connection(monkeypatch, mock_login_post):
    """Tests a relationship using a database connection.

    Should return a Sample instance with an accessible SampleType instance.
    """
    # Create a mock session
    monkeypatch.setattr(requests, "post", mock_login_post)
    aquarium_url = "http://52.52.525.52"
    session = AqSession("username", "password", aquarium_url)

    # monkey patch the "find" method
    def find_user(*args, json_data=None, **kwargs):
        sample_default = {
            "id": 3,
            "name": "MyPrimer",
            "sample_type_id": 5
        }

        sample_type_default = {
            "name": "Primer",
            "id": 5
        }

        if json_data["model"] == "Sample":
            if json_data["id"] == sample_default["id"]:
                json_data.update(sample_default)
                return json_data

        if json_data["model"] == "SampleType":
            if json_data["id"] == sample_type_default["id"]:
                json_data.update(sample_type_default)
                return json_data

    monkeypatch.setattr(AqHTTP, "post", find_user)

    sample = session.Sample.find_using_session(3)
    sample_type = sample.sample_type

    # Sample properties
    assert isinstance(sample, Sample)
    assert sample.id == 3
    assert sample.name == "MyPrimer"
    assert sample.sample_type_id == 5

    # SampleType properties
    assert isinstance(sample_type, SampleType)
    assert sample_type.name == "Primer"
    assert sample_type.id == 5

def test_load_model_with_many(monkeypatch, mock_login_post):
    """Tests a relationship using a database connection.

        Should return a Sample instance with an accessible SampleType instance.
    """

    # Create a mock session
    monkeypatch.setattr(requests, "post", mock_login_post)
    aquarium_url = "http://52.52.525.52"
    session = AqSession("username", "password", aquarium_url)

    def mock_post(*args, json_data=None, **kwargs):
        if "method" in json_data:
            if json_data["method"] == "where":
                samples = [
                    {"id": 1, "sample_type_id": 3, "name": "sample1"},
                    {"id": 2, "sample_type_id": 3, "name": "sample2"},
                    {"id": 3, "sample_type_id": 5, "name": "sample3"},
                ]
                return [s for s in samples if
                        s["sample_type_id"] == json_data["arguments"]["sample_type_id"]]
        return {
                "id": 3,
                "name": "Primer"
            }

    monkeypatch.setattr(AqHTTP, "post", mock_post)

    st = session.SampleType.find_using_session(3)
    samples = st.samples

    assert len(samples) == 2
    assert isinstance(samples[0], Sample)

#
# def test_load_model_with_many_through(monkeypatch, mock_post):
#     """Tests a relationship using a database connection.
#
#         Should return a Sample instance with an accessible SampleType instance.
#     """
#
#     # Create a mock session
#     monkeypatch.setattr(requests, "post", mock_post)
#     aquarium_url = "http://52.52.525.52"
#     session = AqSession("username", "password", aquarium_url)
#
#     def mock_post(*args, json_data=None, **kwargs):
#         if "method" in json_data:
#             if json_data["method"] == "where":
#                 if json_data["model"] ==
#                 samples = [
#                     {"id": 1, "sample_type_id": 3, "name": "sample1"},
#                     {"id": 2, "sample_type_id": 3, "name": "sample2"},
#                     {"id": 3, "sample_type_id": 5, "name": "sample3"},
#                 ]
#                 return [s for s in samples if
#                         s["sample_type_id"] == json_data["arguments"]["sample_type_id"]]
#         return {
#                 "id": 3,
#                 "name": "Primer"
#             }
#
#     monkeypatch.setattr(AqHTTP, "post", mock_post)
#
#     st = session.SampleType.find(3)
#     samples = st.samples
#
#     assert len(samples) == 2
#     assert isinstance(samples[0], Sample)