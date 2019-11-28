"""
This file contains the functional tests for urls.
"""
import json
from io import StringIO

import pytest
from mock import patch

from microservices.app import (
    ROOT_URL,
    SHARE_FOLDER_URL,
    SHARE_FOLDER_DOWNLOAD_BASE_URL,
    SHARE_FOLDER_UPLOAD_URL,
)


@pytest.mark.skip("app changed")
def test_home_page_redirect_to_upload(test_client):
    response = test_client.get(ROOT_URL)
    assert response.status_code == 200
    assert SHARE_FOLDER_UPLOAD_URL in response.headers[2][1]


@pytest.mark.skip("app changed")
def test_get_list_file_api_returns_uploaded_file_list(
        test_client, shared_folder_manager, mocker
):
    shared_folder_manager.get_file_names_in_folder = (
        mocker.MagicMock(return_value=['uploaded.pdf'])
    )
    expected_response = [
        {
            'filename': 'uploaded.pdf',
            'url': 'http://localhost/download/uploaded.pdf'
        }
    ]
    with patch('os.path.isfile', return_value=True):
        response = test_client.get(SHARE_FOLDER_URL)
        assert response.status_code == 200
        assert json.loads(response.data) == expected_response


def test_get_down_file_api_returns_file(test_client):
    expected_response = b'dummy_file_content'
    with patch(
            'microservices.app.send_from_directory',
            return_value='dummy_file_content'
    ):
        response = test_client.get(
            SHARE_FOLDER_DOWNLOAD_BASE_URL + 'uploaded.pdf'
        )
        assert response.status_code == 200
        assert response.data == expected_response


def test_post_upload_file_api_returns_succeed(
        test_client, shared_folder_manager, mocker
):
    shared_folder_manager.save_uploaded_file_from_api = (
        mocker.MagicMock(return_value='uploading.pdf file uploaded')
    )
    response = test_client.post(SHARE_FOLDER_UPLOAD_URL + '/uploading.pdf')
    assert response.status_code == 201


@pytest.mark.skip("app changed")
def test_post_upload_file_form_returns_succeed_with_redirect_to_list(
        test_client, shared_folder_manager, mocker
):
    shared_folder_manager.save_uploaded_file_from_form = (
        mocker.MagicMock(return_value='uploading.pdf file uploaded')
    )
    response = test_client.post(
        SHARE_FOLDER_UPLOAD_URL,
        buffered=True,
        data={'file': (StringIO('my file contents'), 'test.txt')}
    )
    assert response.status_code == 302
    assert SHARE_FOLDER_URL in response.headers[2][1]
