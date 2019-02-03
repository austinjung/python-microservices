"""
This file test UploadFolderManager
"""
import pytest
from microservices.app import UploadFolderException


def test_rtf_extension_succeeded(shared_folder_manager):
    assert shared_folder_manager.validate_filename('sample.rtf') == 'rtf'


def test_doc_extension_succeeded(shared_folder_manager):
    assert shared_folder_manager.validate_filename('sample.doc') == 'doc'


def test_docx_extension_succeeded(shared_folder_manager):
    assert shared_folder_manager.validate_filename('sample.docx') == 'docx'


def test_xls_extension_succeeded(shared_folder_manager):
    assert shared_folder_manager.validate_filename('sample.xls') == 'xls'


def test_xlsx_extension_succeeded(shared_folder_manager):
    assert shared_folder_manager.validate_filename('sample.xlsx') == 'xlsx'


def test_pdf_extension_succeeded(shared_folder_manager):
    assert shared_folder_manager.validate_filename('sample.pdf') == 'pdf'


def test_no_extension_failed(shared_folder_manager):
    with pytest.raises(UploadFolderException) as excinfo:
        shared_folder_manager.validate_filename('sample')
    assert str(excinfo.value) == 'No extension file not allowed'


def test_sub_directory_failed(shared_folder_manager):
    with pytest.raises(UploadFolderException) as excinfo:
        shared_folder_manager.validate_filename('subdir/sample.pdf')
    assert str(excinfo.value) == 'no subdirectories directories allowed'


def test_file_already_exist_failed(shared_folder_manager, mocker):
    shared_folder_manager.get_file_names_in_folder = (
        mocker.MagicMock(return_value=['uploaded.pdf'])
    )
    with pytest.raises(UploadFolderException) as excinfo:
        shared_folder_manager.validate_filename('uploaded.pdf')
    assert str(excinfo.value) == 'uploaded.pdf exists'
