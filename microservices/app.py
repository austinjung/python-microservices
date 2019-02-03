import os

from flask import (
    Flask, request, abort, jsonify, make_response,
    send_from_directory, url_for, redirect
)
from werkzeug.utils import secure_filename


ROOT_URL = '/'
SHARE_FOLDER = 'shared-files'
SHARE_FOLDER_LIST_URL = '/download'
SHARE_FOLDER_DOWNLOAD_BASE_URL = SHARE_FOLDER_LIST_URL + '/'
SHARE_FOLDER_UPLOAD_URL = '/upload'
DEFAULT_ALLOWED_EXTENSIONS = (
    'txt', 'rtf', 'doc', 'docx', 'xls', 'xlsx', 'pdf',
)


if not os.path.exists(SHARE_FOLDER):
    os.makedirs(SHARE_FOLDER)


class UploadFolderException(Exception):
    pass


class UploadFolderManager(object):
    def __init__(self, upload_folder=SHARE_FOLDER, allowed_extensions=None):
        if allowed_extensions is None:
            allowed_extensions = DEFAULT_ALLOWED_EXTENSIONS
        self.upload_folder = upload_folder
        self.allowed_extensions = allowed_extensions

    def get_extension(self, filename):
        ext = os.path.splitext(filename)[1]
        if ext.startswith('.'):
            ext = ext[1:]
        return ext.lower()

    def get_file_names_in_folder(self):
        return os.listdir(self.upload_folder)

    def validate_filename(self, filename):
        ext = self.get_extension(filename)
        if ext not in self.allowed_extensions:
            if ext == '':
                ext = 'No extension'
            raise UploadFolderException(
                '{ext} file not allowed'.format(ext=ext)
            )
        if '/' in filename:
            raise UploadFolderException(
                'no subdirectories directories allowed'
            )
        if filename in self.get_file_names_in_folder():
            raise UploadFolderException(
                '{filename} exists'.format(filename=filename)
            )

    def save_uploaded_file_from_api(self, filename, file_data):
        new_filename = secure_filename(filename)
        self.validate_filename(new_filename)
        with open(os.path.join(self.upload_folder, new_filename), 'wb') as fp:
            fp.write(file_data)
        return '{filename} uploaded'.format(filename=new_filename)

    def save_uploaded_file_from_form(self, file):
        if file is None:
            raise UploadFolderException(
                'No file found'
            )
        filename = secure_filename(file.filename)
        self.validate_filename(filename)
        file.save(os.path.join(self.upload_folder, filename))
        return '{filename} uploaded'.format(filename=filename)

    def get_upload_folder(self):
        return self.upload_folder


api = Flask(__name__)
api.shared_folder_manager = UploadFolderManager(SHARE_FOLDER)


@api.route(ROOT_URL)
def hello_world():
    return redirect(url_for('.upload_file_from_form'))


@api.route(SHARE_FOLDER_LIST_URL)
def list_files():
    """Endpoint to list files on the server."""
    files = []
    base_url = request.url_root[:-1]
    for filename in api.shared_folder_manager.get_file_names_in_folder():
        path = os.path.join(api.shared_folder_manager.upload_folder, filename)
        if os.path.isfile(path):
            files.append({
                'filename': filename,
                'url': base_url + url_for('.get_file', filename=filename)
            })
    return make_response(jsonify(files)), 200


@api.route(SHARE_FOLDER_DOWNLOAD_BASE_URL + '<string:filename>')
def get_file(filename):
    """Download a file as a attachment."""
    return send_from_directory(
        api.shared_folder_manager.get_upload_folder(),
        filename,
        as_attachment=True
    )


@api.route('/upload/<string:filename>', methods=['POST'])
def upload_file(filename):
    """Upload a file with api."""
    try:
        result = api.shared_folder_manager.save_uploaded_file_from_api(
            filename, request.data
        )
        # Return 201 CREATED
        return result, 201
    except UploadFolderException as e:
        abort(400, str(e))


@api.route('/upload', methods=['POST', 'GET'])
def upload_file_from_form():
    """Upload a file from form."""
    if request.method == 'POST':
        try:
            file = request.files['file']
            api.shared_folder_manager.save_uploaded_file_from_form(file)
            return redirect(url_for('list_files'))
        except UploadFolderException as e:
            upload_url = (
                request.url_root[:-1] + url_for('.upload_file_from_form')
            )
            return """
            <!doctype html>
            <title>Upload file error</title>
            <h1>Upload file error</h1>
            <p>{error}</p>
            <a href={upload_url}>Try again</a>
            """.format(
                error=str(e), upload_url=upload_url
            )
    return """
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form action="" method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload></p>
    </form>
    <p>%s</p>
    """ % "<br>".join(api.shared_folder_manager.get_file_names_in_folder())

if __name__ == '__main__':
    api.run(host='0.0.0.0')
