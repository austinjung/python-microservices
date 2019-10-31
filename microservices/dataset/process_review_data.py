import os
import json
from datetime import datetime
from collections import defaultdict, OrderedDict

from pyciiml.utils.logging_utils import CustomLogger
from pyciiml.utils.file_utils import check_create_dir, read_json, write_json

# Directories
BASE_DIR = os.path.dirname(__file__)
SHARE_FOLDER = os.path.join(BASE_DIR, '../shared-files')
DATASET_DIR = BASE_DIR
DATASET_STATUS_FILE = "dataset_status.json"
LOGS_DIR = os.path.join(BASE_DIR, "../logs")

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
INITIAL_MODIFIED = datetime(year=2000, month=1, day=1,)

# Loggers
check_create_dir(LOGS_DIR)
REVIEWER_INTERN_SERVICE = 'reviewer-intern-service'
ml_logger = CustomLogger(
    name=REVIEWER_INTERN_SERVICE,
    log_file=os.path.join(LOGS_DIR, '{}.log'.format(REVIEWER_INTERN_SERVICE)),
).get_logger()

dataset_status = OrderedDict({'updated': INITIAL_MODIFIED.strftime(DATETIME_FORMAT)})
dataset = OrderedDict()
terminology_entity_types = read_json(os.path.join(BASE_DIR, '../models', 'terminology_entity_types.json'))


def read_reviewed_json(file_full_path):
    json_obj = {}
    with open(file_full_path, encoding='utf-8', errors='replace') as f:
        data = f.read()
        try:
            json_obj = json.loads(data)
        except Exception as e:
            ml_logger.warning('{0} has no reviewed json'.format(file_full_path))
            ml_logger.warning(e)
    return json_obj


def build_current_working_dataset(json_filename, json_file_full_path, dataset_file_full_path):
    local_dataset = OrderedDict()
    review_json_objs = read_reviewed_json(json_file_full_path)
    total_dataset_count_in_file = 0
    total_processing_dataset_count_in_file = 0
    total_accepted_dataset_count_in_file = 0
    total_rejected_dataset_count_in_file = 0
    precision = 0.0
    for review_obj in review_json_objs:
        if review_obj['entityType'] not in terminology_entity_types:
            continue
        source_key = review_obj['source']['text']  # source text will be key
        if source_key == '':
            source_key = review_obj['selected']['text']
        if source_key == '':
            source_key = review_obj['highlighted']['text']
        if source_key == '':
            continue
        total_dataset_count_in_file += 1
        if source_key not in local_dataset:
            try:
                local_dataset[source_key] = {
                    'd': review_obj['source']['provenance']['d'],
                    'p': review_obj['source']['provenance']['p'],
                    'sectionType': review_obj['sectionType'],
                    'entityType': review_obj['entityType'],
                    'code': review_obj.get('code', None),
                    'precision': 0.0,
                    'original': {
                        'highlighted': review_obj['highlighted']['text'],
                        'selected': review_obj['selected']['text'],
                    }
                }
            except KeyError:
                total_dataset_count_in_file -= 1
        elif 'accepted' in local_dataset[source_key]:
            total_accepted_dataset_count_in_file += 1
            precision += local_dataset[source_key]['precision']
        elif 'rejected' in local_dataset[source_key]:
            total_rejected_dataset_count_in_file += 1
        elif 'inferred' in local_dataset[source_key]:
            total_processing_dataset_count_in_file += 1
        else:
            total_dataset_count_in_file -= 1
    dataset_status[json_filename] = {
        'total_dataset': total_dataset_count_in_file,
        'accepted_dataset': total_accepted_dataset_count_in_file,
        'annotated_dataset': total_accepted_dataset_count_in_file,
        'processing_dataset': total_processing_dataset_count_in_file,
        'precision': precision,
        'updated': datetime.now().strftime(DATETIME_FORMAT)
    }
    write_json(local_dataset, dataset_file_full_path)
    return local_dataset


def change_current_working_dataset(json_filename, dataset_filename):
    global dataset
    json_file_path = os.path.join(SHARE_FOLDER, json_filename)
    json_last_modified_time = os.path.getmtime(json_file_path)
    dataset_file_path = os.path.join(DATASET_DIR, dataset_filename)
    dataset_last_modified_time = os.path.getmtime(dataset_file_path)
    if dataset_last_modified_time > json_last_modified_time:
        dataset = read_reviewed_json(dataset_file_path)
    else:
        dataset = build_current_working_dataset(json_filename, json_file_path, dataset_file_path)

def generate_review_dataset(dataset_dir=DATASET_DIR):
    global dataset, dataset_status
    dataset_status_file_path = os.path.join(dataset_dir, DATASET_STATUS_FILE)
    if os.path.exists(dataset_status_file_path):
        dataset_status = read_reviewed_json(dataset_status_file_path)
    else:
        write_json(dataset_status, dataset_status_file_path)
    for file in os.listdir(SHARE_FOLDER):
        if file != DATASET_STATUS_FILE and (file.endswith('.json') or file.endswith('.jsonl')):
            full_file_path = os.path.join(SHARE_FOLDER, file)
            dataset_path = os.path.join(DATASET_DIR, file)
            dataset_path = '{0}.data'.format(''.join(dataset_path.split('.')[:-1]))
            if os.path.exists(dataset_path):
                dataset = read_reviewed_json(dataset_path)
            else:
                write_json(dataset, dataset_path)
            review_json_objs = read_reviewed_json(full_file_path)
            total_dataset_count_in_file = 0
            total_processing_dataset_count_in_file = 0
            total_accepted_dataset_count_in_file = 0
            total_rejected_dataset_count_in_file = 0
            precision = 0.0
            for review_obj in review_json_objs:
                if review_obj['entityType'] not in terminology_entity_types:
                    continue
                source_key = review_obj['source']['text']  # source text will be key
                if source_key == '':
                    source_key = review_obj['selected']['text']
                if source_key == '':
                    source_key = review_obj['highlighted']['text']
                if source_key == '':
                    continue
                total_dataset_count_in_file += 1
                if source_key not in dataset:
                    try:
                        dataset[source_key] = {
                            'd': review_obj['source']['provenance']['d'],
                            'p': review_obj['source']['provenance']['p'],
                            'sectionType': review_obj['sectionType'],
                            'entityType': review_obj['entityType'],
                            'code': review_obj.get('code', None),
                            'precision': 0.0,
                            'original': {
                                'highlighted': review_obj['highlighted']['text'],
                                'selected': review_obj['selected']['text'],
                            }
                        }
                    except KeyError:
                        total_dataset_count_in_file -= 1
                elif 'accepted' in dataset[source_key]:
                    total_accepted_dataset_count_in_file += 1
                    precision += dataset[source_key]['precision']
                elif 'rejected' in dataset[source_key]:
                    total_rejected_dataset_count_in_file += 1
                elif 'inferred' in dataset[source_key]:
                    total_processing_dataset_count_in_file += 1
                else:
                    total_dataset_count_in_file -= 1
            dataset_status[file] = {
                'total_dataset': total_dataset_count_in_file,
                'accepted_dataset': total_accepted_dataset_count_in_file,
                'annotated_dataset': total_accepted_dataset_count_in_file,
                'processing_dataset': total_processing_dataset_count_in_file,
                'precision': precision,
                'updated': datetime.now().strftime(DATETIME_FORMAT)
            }
            write_json(dataset, dataset_path)
    dataset_status['updated'] = datetime.now().strftime(DATETIME_FORMAT)
    write_json(dataset_status, dataset_status_file_path)
