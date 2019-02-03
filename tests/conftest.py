import pytest
from microservices.app import api


@pytest.fixture(scope='module')
def test_client():
    api.config.from_pyfile('flask_test.cfg')

    # Flask provides a way to test your application by exposing the Werkzeug test Client
    # and handling the context locals for you.
    testing_client = api.test_client()

    # Establish an application context before running the tests.
    ctx = api.app_context()
    ctx.push()

    yield testing_client  # this is where the testing happens!

    ctx.pop()


@pytest.fixture(scope='module')
def shared_folder_manager():
    return api.shared_folder_manager
