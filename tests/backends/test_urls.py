"""
This file contains the functional tests for urls.
"""
import os
from mock import patch, Mock


def test_home_page_redirect_to_upload(test_client):
    response = test_client.get('/')
    assert response.status_code == 302
    assert '/upload' in response.headers[2][1]
