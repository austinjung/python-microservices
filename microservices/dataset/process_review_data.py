import json
import os
from collections import OrderedDict
from datetime import datetime

from pyciiml.utils.file_utils import check_create_dir, read_json, write_json
from pyciiml.utils.logging_utils import CustomLogger

# Directories
BASE_DIR = os.path.dirname(__file__)
SHARE_FOLDER = os.path.join(BASE_DIR, '../shared-files')
DATASET_DIR = BASE_DIR
DATASET_STATUS_FILE = "dataset_status.json"
LOGS_DIR = os.path.join(BASE_DIR, "../logs")
TERMINOLOGY_ENTITY_TYPE_PATH = os.path.join(BASE_DIR, '../models', 'terminology_entity_types.json')

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
INITIAL_MODIFIED = datetime(year=2000, month=1, day=1, )


def read_reviewed_json(app, file_full_path):
    json_obj = {}
    with open(file_full_path, encoding='utf-8', errors='replace') as f:
        data = f.read()
        try:
            json_obj = json.loads(data)
        except Exception as e:
            app.ml_logger.warning('{0} has no reviewed json'.format(file_full_path))
            app.ml_logger.warning(e)
    return json_obj


def build_current_working_dataset(app, json_filename, json_file_full_path, dataset_file_full_path):
    local_dataset = OrderedDict()
    review_json_objs = read_reviewed_json(app, json_file_full_path)
    total_dataset_count_in_file = 0
    total_processing_dataset_count_in_file = 0
    total_accepted_dataset_count_in_file = 0
    total_skipped_dataset_count_in_file = 0
    total_rejected_dataset_count_in_file = 0
    total_not_started_dataset_count = 0
    for review_obj in review_json_objs:
        if review_obj['entityType'] not in app.terminology_entity_types:
            continue
        source_key = review_obj['selected']['text']  # selected text will be key
        source_key_origin = 'selected'
        if source_key == '':
            source_key = review_obj['highlighted']['text']
            source_key_origin = 'highlighted'
        if source_key == '':
            source_key = review_obj['source']['text']
            source_key_origin = 'source'
        if source_key == '':
            continue  # if there is no selected, highlighted or source
        total_dataset_count_in_file += 1
        if source_key not in local_dataset:
            try:
                local_dataset[source_key] = {
                    'd': review_obj[source_key_origin]['provenance']['d'],
                    'p': review_obj[source_key_origin]['provenance']['p'],
                    'sectionType': review_obj['sectionType'],
                    'entityType': review_obj['entityType'],
                    'code': review_obj.get('code', None),
                    'original': {
                        'highlighted': review_obj['highlighted']['text'],
                        'selected': review_obj['selected']['text'],
                    }
                }
                total_not_started_dataset_count += 1
            except KeyError:
                total_dataset_count_in_file -= 1
        elif source_key in local_dataset:
            total_dataset_count_in_file -= 1
        elif 'accepted' in local_dataset[source_key]:
            total_accepted_dataset_count_in_file += 1
        elif 'skipped' in local_dataset[source_key]:
            total_skipped_dataset_count_in_file += 1
        elif 'rejected' in local_dataset[source_key]:
            total_rejected_dataset_count_in_file += 1
        elif 'inferred' in local_dataset[source_key]:
            total_processing_dataset_count_in_file += 1
        else:
            total_not_started_dataset_count += 1
    app.dataset_status[json_filename] = {
        'total_dataset': total_dataset_count_in_file,
        'accepted_dataset': total_accepted_dataset_count_in_file,
        'skipped_dataset': total_skipped_dataset_count_in_file,
        'rejected_dataset': total_rejected_dataset_count_in_file,
        'processing_dataset': total_processing_dataset_count_in_file,
        'not_started': total_not_started_dataset_count,
        'updated': datetime.now().strftime(DATETIME_FORMAT)
    }
    write_json(local_dataset, dataset_file_full_path)
    app.dataset = local_dataset


def change_current_working_dataset(app, json_filename, dataset_filename):
    json_file_path = os.path.join(SHARE_FOLDER, json_filename)
    json_last_modified_time = os.path.getmtime(json_file_path)
    dataset_file_path = os.path.join(DATASET_DIR, dataset_filename)
    dataset_last_modified_time = os.path.getmtime(dataset_file_path)
    if dataset_last_modified_time > json_last_modified_time:
        app.dataset = read_reviewed_json(app, dataset_file_path)
        if app.dataset_status[json_filename]['processing_dataset'] + app.dataset_status[json_filename]['not_started'] > 0:
            app.selected_dataset = json_filename
    else:
        build_current_working_dataset(app, json_filename, json_file_path, dataset_file_path)
    app.last_read_dataset = json_filename


def config_app(app):
    # Loggers
    check_create_dir(LOGS_DIR)
    REVIEWER_INTERN_SERVICE = 'reviewer-intern-service'
    app.ml_logger = CustomLogger(
        name=REVIEWER_INTERN_SERVICE,
        log_file=os.path.join(LOGS_DIR, '{}.log'.format(REVIEWER_INTERN_SERVICE)),
    ).get_logger()

    app.dataset_status = OrderedDict({'updated': INITIAL_MODIFIED.strftime(DATETIME_FORMAT)})
    app.dataset = OrderedDict()
    app.selected_dataset = None
    app.last_read_dataset = None
    app.terminology_entity_types = read_json(TERMINOLOGY_ENTITY_TYPE_PATH)


def generate_review_dataset(app, dataset_dir=DATASET_DIR):
    dataset_status_file_path = os.path.join(dataset_dir, DATASET_STATUS_FILE)
    if os.path.exists(dataset_status_file_path):
        app.dataset_status = read_reviewed_json(app, dataset_status_file_path)
    else:
        write_json(app.dataset_status, dataset_status_file_path)
    for file in os.listdir(SHARE_FOLDER):
        if file != DATASET_STATUS_FILE and (file.endswith('.json') or file.endswith('.jsonl')):
            full_file_path = os.path.join(SHARE_FOLDER, file)
            dataset_path = os.path.join(DATASET_DIR, file)
            dataset_path = '{0}.data'.format(''.join(dataset_path.split('.')[:-1]))
            if os.path.exists(dataset_path):
                app.dataset = read_reviewed_json(app, dataset_path)
            else:
                build_current_working_dataset(app, file, full_file_path, dataset_path)
            app.last_read_dataset = file
            if file not in app.dataset_status:
                build_current_working_dataset(app, file, full_file_path, dataset_path)
            if app.selected_dataset is None and (
                    app.dataset_status[file]['processing_dataset'] + app.dataset_status[file]['not_started'] > 0):
                app.selected_dataset = file
    app.dataset_status['updated'] = datetime.now().strftime(DATETIME_FORMAT)
    write_json(app.dataset_status, dataset_status_file_path)


def build_dataset_status_from_dataset(app, dataset_filename, dataset_file_full_path):
    dataset_json_objs = read_reviewed_json(app, dataset_file_full_path)
    total_dataset_count_in_file = 0
    total_processing_dataset_count_in_file = 0
    total_accepted_dataset_count_in_file = 0
    total_skipped_dataset_count_in_file = 0
    total_rejected_dataset_count_in_file = 0
    for source, dataset_obj in dataset_json_objs.items():
        total_dataset_count_in_file += 1
        keys = set(dataset_obj.keys())
        if 'inferred' in keys and len(keys.intersection({'accepted', 'skipped', 'rejected'})) == 0:
            total_processing_dataset_count_in_file += 1
        for processed_key in dataset_obj.keys():
            if processed_key in ['d', 'p', 'sectionType', 'entityType', 'code', 'original']:
                continue
            if processed_key == 'accepted':
                total_accepted_dataset_count_in_file += 1
            elif processed_key == 'skipped':
                total_skipped_dataset_count_in_file += 1
            elif processed_key == 'rejected':
                total_rejected_dataset_count_in_file += 1
    json_filename = dataset_filename.replace('.data', '.json')
    app.dataset_status[json_filename] = {
        'total_dataset': total_dataset_count_in_file,
        'accepted_dataset': total_accepted_dataset_count_in_file,
        'skipped_dataset': total_skipped_dataset_count_in_file,
        'rejected_dataset': total_rejected_dataset_count_in_file,
        'processing_dataset': total_processing_dataset_count_in_file,
        'not_started': (
            total_dataset_count_in_file - total_accepted_dataset_count_in_file - total_skipped_dataset_count_in_file
            - total_rejected_dataset_count_in_file - total_processing_dataset_count_in_file
        ),
        'updated': datetime.now().strftime(DATETIME_FORMAT)
    }


def add_dataset(app, file, dataset_dir=DATASET_DIR):
    dataset_status_file_path = os.path.join(dataset_dir, DATASET_STATUS_FILE)
    if os.path.exists(dataset_status_file_path):
        app.dataset_status = read_reviewed_json(app, dataset_status_file_path)
    else:
        write_json(app.dataset_status, dataset_status_file_path)
    if file != DATASET_STATUS_FILE and (file.endswith('.json') or file.endswith('.jsonl')):
        full_file_path = os.path.join(SHARE_FOLDER, file)
        dataset_path = os.path.join(DATASET_DIR, file)
        dataset_path = '{0}.data'.format(''.join(dataset_path.split('.')[:-1]))
        if os.path.exists(dataset_path):
            app.dataset = read_reviewed_json(app, dataset_path)
        else:
            write_json(app.dataset, dataset_path)
        current_selected_dataset = app.selected_dataset
        build_current_working_dataset(app, file, full_file_path, dataset_path)
        app.selected_dataset = current_selected_dataset
        app.last_read_dataset = file
        app.dataset_status['updated'] = datetime.now().strftime(DATETIME_FORMAT)
        write_json(app.dataset_status, dataset_status_file_path)
    elif file == 'terminology_dataset.zip':
        current_selected_dataset = app.selected_dataset
        for data_set_file in os.listdir(DATASET_DIR):
            if data_set_file.endswith('.data'):
                dataset_path = os.path.join(DATASET_DIR, data_set_file)
                build_dataset_status_from_dataset(app, data_set_file, dataset_path)
                app.dataset_status['updated'] = datetime.now().strftime(DATETIME_FORMAT)
                write_json(app.dataset_status, dataset_status_file_path)
                app.last_read_dataset = data_set_file
        app.selected_dataset = current_selected_dataset
