import os
import requests
import json
import re
from zipfile import ZipFile
from datetime import datetime
from collections import defaultdict

from pyciiml.utils.file_utils import read_json, remove_file, write_json

from flask import (
    Flask, request, abort, jsonify, make_response,
    send_from_directory, url_for, redirect, render_template
)
from werkzeug.utils import secure_filename
from http import HTTPStatus
from string import punctuation
import nltk
from nltk import word_tokenize

nltk.download('punkt')

from dataset.process_review_data import (
    generate_review_dataset, add_dataset, config_app, DATASET_STATUS_FILE, DATASET_DIR, DATETIME_FORMAT
)

ROOT_URL = '/'
SHARE_FOLDER = 'shared-files'
DATASET_FOLDER = 'dataset'
SHARE_FOLDER_DOWNLOAD_URL = '/download'
SHARE_FOLDER_URL = '/{0}'.format(SHARE_FOLDER)
DATASET_FOLDER_URL = '/{0}'.format(DATASET_FOLDER)
SHARE_FOLDER_VIEW_URL = '/view/'
SHARE_FOLDER_DELETE_URL = '/delete/'
SHARE_FOLDER_DOWNLOAD_BASE_URL = SHARE_FOLDER_DOWNLOAD_URL + '/'
DATASET_EXPORT_URL = '/dataset/export'
PROCESS_STATUS_URL = '/status'
SHARE_FOLDER_UPLOAD_URL = '/upload'
MED_TERMINOLOGY_FIND_CODE = '/find_codes'
INFER_NEXT = '/infer_next'
SET_DATASET_AND_INFER_NEXT = '/set_dataset_and_infer_next'
ACCEPT_AND_PROCESS_NEXT = '/accept_and_process_next'
ACCEPT_EXTRACTOR_AND_PROCESS_NEXT = '/accept_extractor_and_process_next'
REJECT_AND_LEARN = '/reject_and_learn'
SKIP = '/skip'
GET_MED_TERMINOLOGIES = '/get_terminologies'
GET_MED_TERMINOLOGY_CODE_URL = '/terminology_code'
DEFAULT_ALLOWED_EXTENSIONS = ('json', 'jsonl', 'zip')

if not os.path.exists(SHARE_FOLDER):
    os.makedirs(SHARE_FOLDER)
if not os.path.exists(DATASET_FOLDER):
    os.makedirs(DATASET_FOLDER)

# Directories
BASE_DIR = os.path.dirname(__file__)
DATASET_ABSOLUTE_PATH = os.path.join(BASE_DIR, 'dataset')
EXPORT_ZIP_FILE_NAME = 'terminology_dataset.zip'
EXPORT_ZIP_FILE_PATH = os.path.join(DATASET_FOLDER, EXPORT_ZIP_FILE_NAME)
CIITIZEN_MED_DICTIONARY_PATH = os.path.join(BASE_DIR, 'models', 'ciitizen_medical_dictionary.json')
MERCK_MED_DICTIONARY_PATH = os.path.join(BASE_DIR, 'models', 'merck_medical_dictionary.json')

MED_TERMINOLOGY_CODE_PATH = os.path.join(BASE_DIR, 'models', 'med_terminology_code_verbose.json')
MED_TERMINOLOGY_CODE_TREE_PATH = os.path.join(BASE_DIR, 'models', 'med_terminology_code_tree.json')

med_embeddings = set(read_json(CIITIZEN_MED_DICTIONARY_PATH)).union(set(read_json(MERCK_MED_DICTIONARY_PATH)))

med_terminology_code_verbose = read_json(MED_TERMINOLOGY_CODE_PATH)
med_terminology_code_tree = read_json(MED_TERMINOLOGY_CODE_TREE_PATH)

stop_words = {
    "/", "-", ",", "(", ")", "[", "]", "upper", "left", "right", "down", "lower", "region",
    "with", "w", "without", "wo", "w/wo", "contrast", "about", "again", "against", "ain't", "all",
    "am", "an", "and", "any", "are", "n't", "aren't", "as", "at", "be", "because", "been", "being", "but",
    "by", "can", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "during",
    "each", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he's",
    "her", "here", "hers", "herself", "him", "himself", "his", "how", "if", "in", "is", "isn't", "it",
    "it's", "its", "itself", "just", "'ll", "i'll", "you'll", "he'll", "she'll", "they'll", "i'm", "'m", "me",
    "might", "mightn't", "must", "more", "most", "mustn't", "my", "myself", "needn't", "need", "no", "nor", "not",
    "now", "of", "on", "only", "or", "other", "our", "ours", "ourselves", "own", "same", "shan't", "she",
    "she's", "she'd", "he'd", "should", "should've", "shouldn't", "so", "some", "such", "than", "that",
    "that'll", "the", "their", "theirs", "them", "themselves", "then", "there", "these", "they", "this", "those",
    "through", "to", "too", "i've", "very", "was", "wasn't", "we", "we've", "were", "weren't", "what", "when",
    "where", "which", "while", "who", "whom", "why", "will", "with", "wo", "won't", "would", "wouldn't", "y", "you",
    "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves", "i'd", "they'd",
    "top", "middle", "bottom", '``', "''", "•", "date", "time",
}

suppress_words_patterns = [
    r'\s?\d{1,2}/\d{1,2}/\d{2,4}\s?',
    r'(january|jan|february|feb|march|mar|april|apr|may|june|jun)\s+\d{1,2},\s?\d{2,4}\s?',
    r'(july|jul|august|aug|september|sep|october|oct|november|nov|december|dec)\s+\d{1,2},\s?\d{2,4}\s?'
    r'\s?\d{1,2}:\d{1,2}\s\bpm\b|\bPM\b|\bam\b|\bAM\b\s+',
    r'\s?\d{1,2}:\d{1,2}\s+',
    r'\s+\d+\s+day[s]?',
    r'\s+\d{3,}',
    r'</sub>', r'<sub>',
    r'</sup>', r'<sup>',
    r'<', r'>', r'\^',
]
suppress_words = r'|'.join(map(r'(?:{})'.format, suppress_words_patterns))

suppress_words_patterns_for_highlight = [
    r'\s?\d{1,2}/\d{1,2}/\d{2,4}\s?',
    r'(january|jan|february|feb|march|mar|april|apr|may|june|jun)\s+\d{1,2},\s?\d{2,4}\s?',
    r'(july|jul|august|aug|september|sep|october|oct|november|nov|december|dec)\s+\d{1,2},\s?\d{2,4}\s?'
    r'(January|Jan|February|Feb|March|Mar|April|Apr|May|June|Jun)\s+\d{1,2},\s?\d{2,4}\s?',
    r'(July|Jul|August|Aug|September|Sep|October|Oct|November|Nov|December|Dec)\s+\d{1,2},\s?\d{2,4}\s?'
    r'\s?\d{1,2}:\d{1,2}\s\bpm\b|\bPM\b|\bam\b|\bAM\b\s+',
    r'\s?\d{1,2}:\d{1,2}\s+',
    r'\s?\d{1,2}-\d{1,2}-\d{2,4}\s?',
    r'\s?\d+\s+day[s]?',
    r'\s?(\(|\[|\{)?\d+(\.|\)|\]|\}|)?',
    r'\s+\d+',
    r'</sub>', r'<sub>',
    r'</sup>', r'<sup>',
    r'<', r'>', r'\^',
]
suppress_words_for_highlight = r'|'.join(map(r'(?:{})'.format, suppress_words_patterns_for_highlight))

replace_words = r'/|\\n'


def preprocess_text_for_med_embedding(text, filter_stop_words=True):
    """Preprocess text."""
    lower_text = text.lower()
    suppressed_text = re.sub(suppress_words, '', lower_text)
    replaced_text = re.sub(replace_words, ' ', suppressed_text)
    if filter_stop_words:
        tokens = [token for token in word_tokenize(replaced_text)
                  if token not in punctuation and token not in stop_words]
    else:
        tokens = [token for token in word_tokenize(replaced_text)
                  if token not in punctuation]

    return tokens


class UploadFolderException(Exception):
    pass


class UploadFolderManager(object):
    def __init__(self, app, upload_folder=SHARE_FOLDER, allowed_extensions=None):
        if allowed_extensions is None:
            allowed_extensions = DEFAULT_ALLOWED_EXTENSIONS
        self.app = app
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
        return ext

    def save_uploaded_file_from_api(self, filename, file_data):
        new_filename = secure_filename(filename)
        self.validate_filename(new_filename)
        with open(os.path.join(self.upload_folder, new_filename), 'wb') as fp:
            fp.write(file_data)
        if filename == EXPORT_ZIP_FILE_NAME:
            with ZipFile(filename, 'r') as zip_ref:
                zip_ref.extractall(DATASET_FOLDER)
        if filename == EXPORT_ZIP_FILE_NAME:
            zip_file_path = os.path.join(DATASET_FOLDER, new_filename)
            with open(zip_file_path, 'wb') as fp:
                fp.write(file_data)
            with ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall()
            new_filename = filename
        else:
            with open(os.path.join(self.upload_folder, new_filename), 'wb') as fp:
                fp.write(file_data)
        add_dataset(self.app, new_filename)
        return '{filename} uploaded'.format(filename=new_filename)

    def save_uploaded_file_from_form(self, file):
        if file is None:
            raise UploadFolderException(
                'No file found'
            )
        filename = secure_filename(file.filename)
        self.validate_filename(filename)
        if filename == EXPORT_ZIP_FILE_NAME:
            zip_file_path = os.path.join(DATASET_FOLDER, filename)
            file.save(zip_file_path)
            with ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall()
        else:
            file.save(os.path.join(self.upload_folder, filename))
        add_dataset(self.app, filename)
        return '{filename} uploaded'.format(filename=filename)

    def get_upload_folder(self):
        return self.upload_folder

    def get_export_abs_folder(self):
        return DATASET_ABSOLUTE_PATH


api = Flask(__name__)
api.shared_folder_manager = UploadFolderManager(api, SHARE_FOLDER)
config_app(api)
generate_review_dataset(api)


def clean_orphan_dataset():
    global api
    orphan_dataset = []
    for ds in api.dataset_status.keys():
        if ds == 'updated':
            continue
        dataset_path = os.path.join(DATASET_DIR, ds.replace('.jsonl', '.data').replace('.json', '.data'))
        if not os.path.exists(dataset_path):
            orphan_dataset.append(ds)
    if len(orphan_dataset) > 0:
        for ds in orphan_dataset:
            api.dataset_status.pop(ds)
        dataset_status_file = os.path.join(DATASET_DIR, DATASET_STATUS_FILE)
        write_json(api.dataset_status, dataset_status_file)


clean_orphan_dataset()


@api.route(ROOT_URL)
def main_url():
    global api
    if api.selected_dataset:
        current_doc_url = '/view/{0}'.format(api.selected_dataset)
    else:
        current_doc_url = '#'
    auto_process = request.args.get('auto-process')
    jumbotron = 'Ciitizen AI Med-Terminology Intern'
    return render_template('index.html', current_doc_url=current_doc_url, current_doc_name=api.selected_dataset,
                           auto_process=auto_process, jumbotron=jumbotron)


@api.route(PROCESS_STATUS_URL)
def show_status():
    """Endpoint to show process status."""
    get_next_dataset_context()
    files = []
    global api
    current_doc_url = '/view/{0}'.format(api.selected_dataset)
    total_dataset = 0
    total_accepted_dataset = 0
    total_skipped_dataset = 0
    total_rejected_dataset = 0
    total_processing_dataset = 0
    total_not_started = 0
    for filename, status in api.dataset_status.items():
        if '.json' in filename:
            if status['total_dataset'] > 0:
                files.append({
                    'filename': filename,
                    'progress': (status['total_dataset'] - status['not_started']) * 100 / status['total_dataset'],
                    'total_dataset': status['total_dataset'],
                    'accepted_dataset': status['accepted_dataset'] * 100 / status['total_dataset'],
                    'skipped_dataset': status['skipped_dataset'] * 100 / status['total_dataset'],
                    'rejected_dataset': status['rejected_dataset'] * 100 / status['total_dataset'],
                    'processing_dataset': status['processing_dataset'] * 100 / status['total_dataset'],
                    'not_started': status['not_started'] * 100 / status['total_dataset'],
                    "updated": status['updated']
                })
            else:
                files.append({
                    'filename': filename,
                    'progress': 0.0,
                    'total_dataset': 0,
                    'accepted_dataset': 0.0,
                    'skipped_dataset': 0.0,
                    'rejected_dataset': 0.0,
                    'processing_dataset': 0.0,
                    'not_started': 0.0,
                    "updated": status['updated']
                })
            total_dataset += status['total_dataset']
            total_accepted_dataset += status['accepted_dataset']
            total_skipped_dataset += status['skipped_dataset']
            total_rejected_dataset += status['rejected_dataset']
            total_processing_dataset += status['processing_dataset']
            total_not_started += status['not_started']
    jumbotron = 'Process status'
    if total_dataset > 0:
        sum = {
            'progress': (total_dataset - total_not_started) * 100 / total_dataset,
            'total_dataset': total_dataset,
            'accepted_dataset': total_accepted_dataset * 100 / total_dataset,
            'skipped_dataset': total_skipped_dataset * 100 / total_dataset,
            'rejected_dataset': total_rejected_dataset * 100 / total_dataset,
            'processing_dataset': total_processing_dataset * 100 / total_dataset,
            'not_started': total_not_started * 100 / total_dataset,
        }
    else:
        sum = {
            'progress': 0.0,
            'total_dataset': 0,
            'accepted_dataset': 0.0,
            'skipped_dataset': 0.0,
            'rejected_dataset': 0.0,
            'processing_dataset': 0.0,
            'not_started': 0.0,
        }
    return render_template('process_status.html', files=files, current_doc_url=current_doc_url, sum=sum,
                           current_doc_name=api.selected_dataset, jumbotron=jumbotron)


@api.route(SHARE_FOLDER_DOWNLOAD_BASE_URL + '<string:filename>')
def download_file(filename):
    """Download a file as a attachment."""
    return send_from_directory(
        api.shared_folder_manager.get_upload_folder(),
        filename,
        as_attachment=True
    )


def zip_dataset(full_path_files):
    with ZipFile(EXPORT_ZIP_FILE_PATH, mode='w') as zf:
        for file in full_path_files:
            zf.write(file)


@api.route(DATASET_EXPORT_URL)
def export_dataset():
    """Download a dataset as a attachment."""
    files = [
        os.path.join(DATASET_FOLDER, file) for file in os.listdir(DATASET_FOLDER)
        if file.endswith('.data')
    ]
    zip_dataset(files)
    return send_from_directory(
        DATASET_FOLDER,
        EXPORT_ZIP_FILE_NAME,
        as_attachment=True
    )


@api.route(SHARE_FOLDER_UPLOAD_URL + '/<string:filename>', methods=['POST'])
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


@api.route(GET_MED_TERMINOLOGIES, methods=['POST'])
def api_get_terminologies():
    """get med-embedding terminologies"""
    if request.method == 'POST':
        context = request.json['context']
        # preprocessed_context = set(preprocess_text_for_med_embedding(context))
        processed_context = set(context.lower().split())
        key_tokens = processed_context.intersection(med_embeddings)
        response = {
            "key_tokens": " ".join(key_tokens),
            "message": HTTPStatus.OK.phrase,
            "status-code": HTTPStatus.OK,
            "method": request.method,
            "timestamp": datetime.now().isoformat(),
            "url": request.url,
        }

        return make_response(jsonify(response), response["status-code"])


@api.route(GET_MED_TERMINOLOGY_CODE_URL, methods=['POST'])
def api_get_terminology_code_detail():
    """get med-embedding terminology code detail"""
    if request.method == 'POST':
        code = request.json['code']
        entity_type = request.json['entity_type']
        synonyms = []
        relations = []
        if code not in med_terminology_code_verbose[entity_type]:
            if code not in med_terminology_code_tree:
                response = {
                    "synonyms": "Not found",
                    "relations": "Not found",
                    "message": HTTPStatus.NOT_FOUND.phrase,
                    "status-code": HTTPStatus.NOT_FOUND,
                    "method": request.method,
                    "timestamp": datetime.now().isoformat(),
                    "url": request.url,
                }
                return make_response(jsonify(response), response["status-code"])
            else:
                code_detail = med_terminology_code_tree[code]
        else:
            code_detail = med_terminology_code_verbose[entity_type][code]
        attr_dict = {
            'STY': "Top concept",
            'CHD': "Parent",
            "PAR": "Children",
            'SY': "Synonym"
        }
        for attr, desc_list in code_detail.items():
            if attr in attr_dict:
                attr = attr_dict[attr]
            if attr == 'Synonym':
                for itm in desc_list:
                    synonyms.append("{0}: {1}".format("Synonym", itm))
            else:
                for itm in desc_list:
                    relations.append("{0}: {1}".format(attr, itm))
                relations.append("")
        response = {
            "synonyms": "\n".join(synonyms),
            "relations": "\n".join(relations),
            "message": HTTPStatus.OK.phrase,
            "status-code": HTTPStatus.OK,
            "method": request.method,
            "timestamp": datetime.now().isoformat(),
            "url": request.url,
        }

        return make_response(jsonify(response), response["status-code"])


def get_t2_find_code(payload, max_results=5):
    payload["max_results"] = max_results

    endpoint_url = "https://api.dev.ciitizen.net/medembed/find_codes"
    # endpoint_url = "http://localhost:3000/medembed/find_codes"
    r = requests.post(endpoint_url, json=payload)
    return r


def get_end_index_for_payload(start_index, window_length, context):
    end_index = start_index
    length_of_context = len(context)
    for idx in range(start_index, start_index + window_length):
        if idx >= length_of_context or context[idx] in ['\\n', '\n']:
            return end_index
        end_index = idx
    return end_index


def generate_payload(processed_context, concept_window_length=10, context_window_length=15):
    payloads = []
    for index, token in enumerate(processed_context):
        try:
            int(token)  # skip integer token
            continue
        except ValueError:
            concept_end_idx = get_end_index_for_payload(index, concept_window_length, processed_context)
            if concept_end_idx == index:
                continue
            suppressed_text = re.sub(suppress_words, '', token)
            if suppressed_text in ['']:
                continue
            context_end_idx = get_end_index_for_payload(index, context_window_length, processed_context)
            if token in med_embeddings:
                payload = {
                    "concept_text": ' '.join(processed_context[index: concept_end_idx]),
                    "context_text": ' '.join(processed_context[index: context_end_idx]),
                    "entity_type": "",
                    "start_idx": index,
                    "last_idx": concept_end_idx,
                }
                payloads.append(payload)
    return payloads


def generate_payload_by_line(processed_context_lines, entity_type=""):
    payloads = []
    for line in processed_context_lines:
        processed_line = ' '.join(preprocess_text_for_med_embedding(line))
        if processed_line == '':
            continue
        payload = {
            "concept_text": processed_line,
            "context_text": processed_line,
            "entity_type": entity_type,
            "highlighted": processed_line
        }
        payloads.append(payload)
    return payloads


def generate_payload_by_highlighted(highlighted, processed_context_lines, entity_type=""):
    payloads = []
    processed_highlighted_tokens = preprocess_text_for_med_embedding(highlighted)
    processed_highlighted = ' '.join(processed_highlighted_tokens)
    for line in processed_context_lines:
        processed_line_tokens = preprocess_text_for_med_embedding(line)
        processed_line = ' '.join(processed_line_tokens)
        if set(processed_highlighted_tokens).intersection(set(processed_line_tokens)):
            payload = {
                "concept_text": processed_highlighted,
                "context_text": processed_line,
                "entity_type": entity_type,
                "highlighted": processed_highlighted
            }
            payloads.append(payload)
    return payloads


def append_highlighted(prev_highlighted, start_idx, end_idx, concept_line_text, highlighted_tokens):
    if start_idx < end_idx:
        if prev_highlighted:
            highlighted_tokens.append(
                "<mark class='c0177'>{0}</mark>".format(concept_line_text[start_idx: end_idx])
            )
        else:
            highlighted_tokens.append(
                "<span>{0}</span>".format(concept_line_text[start_idx: end_idx])
            )
    return not prev_highlighted, end_idx, end_idx


def get_highlight(concept_line_text):
    highlighted_tokens = []
    start_idx = 0
    end_idx = 0
    index = 0
    highlighted = False
    suppressed_text = re.sub(suppress_words_for_highlight, '', concept_line_text)
    for token in concept_line_text.split():
        if token not in suppressed_text or token.lower() not in med_embeddings:
            if highlighted:
                highlighted, start_idx, end_idx = append_highlighted(
                    highlighted, start_idx, end_idx, concept_line_text, highlighted_tokens
                )
        else:
            if not highlighted:
                highlighted, start_idx, end_idx = append_highlighted(
                    highlighted, start_idx, end_idx, concept_line_text, highlighted_tokens
                )
        index += len(token) + 1
        end_idx = index
    append_highlighted(highlighted, start_idx, end_idx, concept_line_text, highlighted_tokens)
    return highlighted_tokens


def get_highlight_from_concept(concept_line_text, concept):
    highlighted_tokens = []
    start_idx = 0
    end_idx = 0
    index = 0
    highlighted = False
    for token in concept_line_text.split():
        if token not in concept:
            if highlighted:
                highlighted, start_idx, end_idx = append_highlighted(
                    highlighted, start_idx, end_idx, concept_line_text, highlighted_tokens
                )
        else:
            if not highlighted:
                highlighted, start_idx, end_idx = append_highlighted(
                    highlighted, start_idx, end_idx, concept_line_text, highlighted_tokens
                )
        index += len(token) + 1
        end_idx = index
    append_highlighted(highlighted, start_idx, end_idx, concept_line_text, highlighted_tokens)
    return ' '.join(highlighted_tokens)


@api.route(MED_TERMINOLOGY_FIND_CODE, methods=['POST'])
def api_find_code():
    """find code from med-embedding terminology service"""
    find_code_results = []
    if request.method == 'POST':
        context = request.json['context_text']
        entity_type = request.json['entity_type']
        processed_context_lines = context.lower().replace('\\n', '\n').replace('\n\n', '\n').split('\n')
        payloads = generate_payload_by_line(processed_context_lines, entity_type=entity_type)
        response = {}
        for payload in payloads:
            r = get_t2_find_code(payload)
            if r.status_code == 200:
                response = json.loads(r.content)
                for result in response['results']:
                    result['synonym'] = payload['concept_text']
                find_code_results.extend(response['results'])
            else:
                pass

        sorted_results = sorted(find_code_results, key=lambda x: (x['confidence']), reverse=True)
        sorted_top_concept = sort_by_code_weight_with_same_parent(sorted_results)
        for concept in sorted_top_concept:
            concept['highlighted'] = ''.join(get_highlight(concept['synonym']))
        response['results'] = sorted_top_concept
        if len(sorted_top_concept) == 0:
            response['message'] = "No match found"

        return make_response(jsonify(response), response.get("status-code", 400))


def get_next_dataset():
    global api
    if api.selected_dataset not in api.dataset_status:
        api.selected_dataset = None
    local_selected_dataset = api.selected_dataset
    select_next = api.selected_dataset is None or \
                  (api.dataset_status[api.selected_dataset]['not_started'] +
                   api.dataset_status[api.selected_dataset]['processing_dataset'] <= 0)
    for ds in api.dataset_status.keys():
        if select_next is False:
            break
        if ds == 'updated' or local_selected_dataset == ds:
            continue
        api.selected_dataset = ds
        select_next = api.selected_dataset is None or \
                      (api.dataset_status[api.selected_dataset]['not_started'] +
                       api.dataset_status[api.selected_dataset]['processing_dataset'] <= 0)

    if api.selected_dataset and api.selected_dataset != api.last_read_dataset:
        api.dataset = read_json(os.path.join(
            DATASET_DIR, api.selected_dataset.replace('.jsonl', '.data').replace('.json', '.data'))
        )
        api.last_read_dataset = api.selected_dataset
    return not select_next


def get_next_dataset_context():
    global api
    context_text = None
    entity_type = None
    extracted_code = None
    highlighted = None
    inprogress = None
    clean_orphan_dataset()
    if get_next_dataset() is False:
        return context_text, entity_type, extracted_code, highlighted, inprogress
    processed = {'accepted', 'skipped', 'rejected'}
    for source, data in api.dataset.items():
        if not processed.intersection(set(data.keys())):
            context_text = source
            entity_type = data['entityType']
            extracted_code = data.get('code', 'No code extracted by document pipeline')
            highlighted = data['original'].get('highlighted', '')
            inprogress = data.get('inferred', None) is not None
            break
    return context_text, entity_type, extracted_code, highlighted, inprogress


def get_weighted_concept_score(kv):
    occurance = len(kv[1])
    if 'preferred_terminology' in kv[1][0]:
        preferred_tokens = set(kv[1][0]['preferred_terminology'][0].lower().split())
    else:
        preferred_tokens = set()
    synonym_tokens = set(kv[1][0]['synonym'].lower().split())
    if len(preferred_tokens.intersection(synonym_tokens)) > 1:
        extra_score = 0.2
    else:
        extra_score = 0.0
    return kv[1][0]['concept_score'] * (1 + occurance * 0.05) + extra_score


def sort_by_code_weight_with_same_parent(results):
    code_weight_dict = defaultdict(list)
    for result in results:
        if 'preferred_terminology' not in result:  # depreciated code
            continue
        if result['code'] in med_terminology_code_tree:
            general_code, general_terminology = med_terminology_code_tree[result['code']].get('GC', [None, None])
        else:
            general_code = None
        if general_code:
            code_weight_dict[general_code].append(result)
        else:
            code_weight_dict[result['code']].append(result)
    sorted_by_code_weight = sorted(code_weight_dict.items(), key=get_weighted_concept_score, reverse=True)
    sorted_results = []
    for code, results_with_same_code in sorted_by_code_weight:
        top_result = sorted(results_with_same_code, key=lambda x: x['confidence'], reverse=True)[0]
        if top_result['concept_score'] >= 0.80:
            sorted_results.append(top_result)
        if len(sorted_results) > 4:
            break
    return sorted_results


def infer_next_code():
    """find code from unprocessed dataset"""
    global api
    find_code_results = []
    context, entity_type, extracted_code, original_highlighted, inprogress = get_next_dataset_context()
    if context is None:
        response = {
            "message": "All contexts were processed.",
            "method": "POST",
            "results": [],
            "status-code": 200
        }
        return make_response(jsonify(response), response.get("status-code", 400))
    # if original_highlighted in ['', None]:
    processed_context_lines = (
        context.lower().replace('\\n', '\n').replace('\n\n', '\n')
        .replace(';', '\n').replace(':', '\n').replace('.', ' . ').split('\n')
    )
    payloads = generate_payload_by_line(processed_context_lines, entity_type=entity_type)
    # else:
    #     processed_context_lines = context.lower().replace('\\n', '\n').replace('\n\n', '\n').split('\n')
    #     payloads = generate_payload_by_highlighted(original_highlighted, processed_context_lines,
    #                                                entity_type=entity_type)
    response = {}
    for payload in payloads:
        r = get_t2_find_code(payload)
        if r.status_code == 200:
            response = json.loads(r.content)
            for result in response['results']:
                result['synonym'] = payload['concept_text']
            find_code_results.extend(response['results'])
        else:
            pass

    sorted_results = sorted(find_code_results, key=lambda x: (x['confidence']), reverse=True)
    sorted_top_concept = sort_by_code_weight_with_same_parent(sorted_results)
    response['results'] = sorted_top_concept
    """
    if original_highlighted in ['', None]:
        selected_concept = sorted_top_concept[0].get('synonym', sorted_top_concept[0].get('preferred_terminology'))
        # selected_concept = sorted_top_concept[0].get('preferred_terminology', [sorted_top_concept[0].get('synonym')])[0]
    else:
        selected_concept = original_highlighted
    response_context_lines = (
        context.replace('\\n', '\n').replace('\n\n', '\n')
        .replace(';', '\n').replace(':', '\n').replace('.', ' . ').split('\n')
    )
    index = 0
    selected_concept_tokens = set(selected_concept.lower().replace(';', '').replace(':', '').split())
    for processed_context in processed_context_lines:
        processed_context_tokens = set(processed_context.split())
        if selected_concept_tokens.intersection(processed_context_tokens) == selected_concept_tokens:
            response_context_lines[index] = get_highlight_from_concept(response_context_lines[index], selected_concept)
        index += 1
    response['context'] = '<br>'.join(response_context_lines)
    """
    response['context'] = context
    entity_codes = []
    if entity_type in med_terminology_code_verbose:
        for code, detail in med_terminology_code_verbose[entity_type].items():
            if code in med_terminology_code_tree:
                terminology = med_terminology_code_tree[code].get('PT', detail.get('SY', detail.get('STY'))[0])
            else:
                terminology = detail.get('SY', detail.get('STY'))[0]
            entity_codes.append([code, terminology])
    response['entity_codes'] = entity_codes
    response['entity_type'] = entity_type
    response['extracted_code'] = extracted_code
    response['original_highlighted'] = original_highlighted
    response['current_process'] = api.selected_dataset
    if len(sorted_top_concept) == 0:
        response['message'] = "OK"
        response['match_with_extracted'] = False
    else:
        if extracted_code and extracted_code == sorted_top_concept[0]['code']:
            response['match_with_extracted'] = True
        elif extracted_code:
            response['match_with_extracted'] = False
        response['message'] = "OK"
    jsonify_response = jsonify(response)
    api.dataset[context]['inferred'] = sorted_top_concept
    dataset_file_path = os.path.join(DATASET_DIR,
                                     api.selected_dataset.replace('.jsonl', '.data').replace('.json', '.data'))
    write_json(api.dataset, dataset_file_path)
    if not inprogress:
        api.dataset_status[api.selected_dataset]['processing_dataset'] += 1
        api.dataset_status[api.selected_dataset]['not_started'] -= 1
    api.dataset_status['updated'] = datetime.now().strftime(DATETIME_FORMAT)
    dataset_status_file_path = os.path.join(DATASET_DIR, DATASET_STATUS_FILE)
    write_json(api.dataset_status, dataset_status_file_path)

    return make_response(jsonify_response, response.get("status-code", 400))


@api.route(INFER_NEXT, methods=['POST'])
def api_infer_next_code():
    if request.method == 'POST':
        return infer_next_code()


@api.route(SET_DATASET_AND_INFER_NEXT, methods=['POST'])
def api_set_dataset_and_infer_next_code():
    global api
    if request.method == 'POST':
        if 'selected_dataset' not in request.json:
            response = {
                "message": "No file is selected.",
                "method": "POST",
                "status-code": HTTPStatus.BAD_REQUEST
            }
        else:
            api.selected_dataset = request.json['selected_dataset']
            response = {
                "message": "{0} is selected.".format(api.selected_dataset),
                "method": "POST",
                "status-code": HTTPStatus.OK
            }
        return make_response(jsonify(response), response.get("status-code", 400))


@api.route(ACCEPT_AND_PROCESS_NEXT, methods=['POST'])
def api_accept_and_infer_next_code():
    """Accept infer results of current dataset"""
    global api
    if request.method == 'POST':
        context, entity_type, extracted_code, original_highlighted, inprogress = get_next_dataset_context()
        api.dataset[context]['accepted'] = True
        dataset_file_path = os.path.join(DATASET_DIR,
                                         api.selected_dataset.replace('.jsonl', '.data').replace('.json', '.data'))
        write_json(api.dataset, dataset_file_path)
        api.dataset_status[api.selected_dataset]['processing_dataset'] -= 1
        api.dataset_status[api.selected_dataset]['accepted_dataset'] += 1
        api.dataset_status['updated'] = datetime.now().strftime(DATETIME_FORMAT)
        dataset_status_file_path = os.path.join(DATASET_DIR, DATASET_STATUS_FILE)
        write_json(api.dataset_status, dataset_status_file_path)

        return infer_next_code()


@api.route(ACCEPT_EXTRACTOR_AND_PROCESS_NEXT, methods=['POST'])
def api_accept_extractor_and_infer_next_code():
    """Accept infer results of current dataset"""
    global api
    if request.method == 'POST':
        context, entity_type, extracted_code, original_highlighted, inprogress = get_next_dataset_context()
        api.dataset[context]['rejected'] = {
            'selected': 'original',
            'entityType': entity_type,
            'code': extracted_code,
        }
        dataset_file_path = os.path.join(DATASET_DIR,
                                         api.selected_dataset.replace('.jsonl', '.data').replace('.json', '.data'))
        write_json(api.dataset, dataset_file_path)
        api.dataset_status[api.selected_dataset]['processing_dataset'] -= 1
        api.dataset_status[api.selected_dataset]['rejected_dataset'] += 1
        api.dataset_status['updated'] = datetime.now().strftime(DATETIME_FORMAT)
        dataset_status_file_path = os.path.join(DATASET_DIR, DATASET_STATUS_FILE)
        write_json(api.dataset_status, dataset_status_file_path)

        return infer_next_code()


@api.route(REJECT_AND_LEARN, methods=['POST'])
def api_reject_and_learn_code():
    """Accept infer results of current dataset"""
    global api
    if request.method == 'POST':
        new_code = request.json['new_code']
        new_code_terminology = request.json['new_code_terminology']
        highlighted = request.json['highlighted']
        context, entity_type, extracted_code, original_highlighted, inprogress = get_next_dataset_context()
        api.dataset[context]['rejected'] = {
            'selected': 'new_learn',
            'new_code_terminology': new_code_terminology,
            'highlighted': highlighted,
            'code': new_code,
        }
        dataset_file_path = os.path.join(DATASET_DIR,
                                         api.selected_dataset.replace('.jsonl', '.data').replace('.json', '.data'))
        write_json(api.dataset, dataset_file_path)
        api.dataset_status[api.selected_dataset]['processing_dataset'] -= 1
        api.dataset_status[api.selected_dataset]['rejected_dataset'] += 1
        api.dataset_status['updated'] = datetime.now().strftime(DATETIME_FORMAT)
        dataset_status_file_path = os.path.join(DATASET_DIR, DATASET_STATUS_FILE)
        write_json(api.dataset_status, dataset_status_file_path)

        return infer_next_code()


@api.route(SKIP, methods=['POST'])
def api_skip():
    """Accept infer results of current dataset"""
    global api
    if request.method == 'POST':
        context, entity_type, extracted_code, original_highlighted, inprogress = get_next_dataset_context()
        api.dataset[context]['skipped'] = True
        dataset_file_path = os.path.join(DATASET_DIR,
                                         api.selected_dataset.replace('.jsonl', '.data').replace('.json', '.data'))
        write_json(api.dataset, dataset_file_path)
        api.dataset_status[api.selected_dataset]['processing_dataset'] -= 1
        api.dataset_status[api.selected_dataset]['skipped_dataset'] += 1
        api.dataset_status['updated'] = datetime.now().strftime(DATETIME_FORMAT)
        dataset_status_file_path = os.path.join(DATASET_DIR, DATASET_STATUS_FILE)
        write_json(api.dataset_status, dataset_status_file_path)

        return infer_next_code()


@api.route(SHARE_FOLDER_UPLOAD_URL, methods=['POST', 'GET'])
def upload_file_from_form():
    """Upload a file from form."""
    global api
    if request.method == 'POST':
        try:
            files = request.files['files']
            api.shared_folder_manager.save_uploaded_file_from_form(files)
            return make_response(jsonify({'message': '{0} uploaded'.format(files.filename)}), 200)
        except UploadFolderException as e:
            return make_response(jsonify({'message': '{0}'.format(e)}), 400)
    current_doc_url = '/view/{0}'.format(api.selected_dataset)
    jumbotron = 'Upload data to get med-terminology codes'
    return render_template('file_upload.html', current_doc_url=current_doc_url, current_doc_name=api.selected_dataset,
                           jumbotron=jumbotron)


@api.route(SHARE_FOLDER_VIEW_URL + '<string:filename>', methods=['POST', 'GET'])
def view_file(filename):
    """view a file"""
    global api
    current_doc_url = '/view/{0}'.format(api.selected_dataset)
    file_path = os.path.join(BASE_DIR, DATASET_FOLDER, filename.replace('.jsonl', '.data').replace('.json', '.data'))
    if '.json' in filename and os.path.exists(file_path):
        file_content = json.dumps(read_json(file_path), indent=8)
        return render_template('json_viewer.html', filename=filename, error=False, file_content=file_content,
                               current_doc_url=current_doc_url, current_doc_name=api.selected_dataset)
    else:
        return render_template('json_viewer.html', filename=filename, error=True, file_content='',
                               current_doc_url=current_doc_url, current_doc_name=api.selected_dataset)


@api.route(SHARE_FOLDER_DELETE_URL + '<string:filename>', methods=['POST'])
def delete_file(filename):
    """delete file"""
    global api
    if '.json' in filename and filename in api.shared_folder_manager.get_file_names_in_folder():
        try:
            file_path = os.path.join(BASE_DIR, SHARE_FOLDER, filename)
            dataset_folder = os.path.join(BASE_DIR, DATASET_FOLDER)
            dataset_path = os.path.join(dataset_folder, filename).replace('.jsonl', '.data').replace('.json', '.data')
            remove_file(file_path)
            remove_file(dataset_path)
            api.dataset_status.pop(filename)
            dataset_status_file_path = os.path.join(dataset_folder, DATASET_STATUS_FILE)
            write_json(api.dataset_status, dataset_status_file_path)
            api.selected_dataset = None
            return make_response(jsonify({'message': '{0} deleted'.format(filename)}), 200)
        except Exception as e:
            return make_response(jsonify({'message': '{0}'.format(e)}), 400)
    else:
        dataset_folder = os.path.join(BASE_DIR, DATASET_FOLDER)
        dataset_path = os.path.join(dataset_folder, filename).replace('.jsonl', '.data').replace('.json', '.data')
        remove_file(dataset_path)
        api.dataset_status.pop(filename)
        dataset_status_file_path = os.path.join(dataset_folder, DATASET_STATUS_FILE)
        write_json(api.dataset_status, dataset_status_file_path)
        api.selected_dataset = None
        return make_response(jsonify({'message': '{0} deleted'.format(filename)}), 200)


if __name__ == '__main__':
    api.run(host='0.0.0.0', port=3000)
