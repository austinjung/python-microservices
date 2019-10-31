import os
import json
from datetime import datetime
from collections import defaultdict

from pyciiml.utils.logging_utils import CustomLogger
from pyciiml.utils.file_utils import check_create_dir, read_json, write_json

# Directories
BASE_DIR = os.path.dirname(__file__)
SHARE_FOLDER = os.path.join(BASE_DIR, '../shared-files')
DATASET_DIR = BASE_DIR
DATASET_STATUS_FILE = "dataset_status.json"
LOGS_DIR = os.path.join(BASE_DIR, "../logs")

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'

# Loggers
check_create_dir(LOGS_DIR)
REVIEWER_INTERN_SERVICE = 'reviewer-intern-service'
ml_logger = CustomLogger(
    name=REVIEWER_INTERN_SERVICE,
    log_file=os.path.join(LOGS_DIR, '{}.log'.format(REVIEWER_INTERN_SERVICE)),
).get_logger()

dataset_status = {}
dataset = {}
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


def generate_review_dataset(dataset_dir=DATASET_DIR):
    global dataset, dataset_status
    dataset_status_file_path = os.path.join(dataset_dir, DATASET_STATUS_FILE)
    if os.path.exists(dataset_status_file_path):
        dataset_status = read_reviewed_json(dataset_status_file_path)
    for file in os.listdir(SHARE_FOLDER):
        if file != DATASET_STATUS_FILE and (file.endswith('.json') or file.endswith('.jsonl')):
            full_file_path = os.path.join(SHARE_FOLDER, file)
            dataset_path = os.path.join(DATASET_DIR, file)
            dataset_path = '{0}.data'.format(''.join(dataset_path.split('.')[:-1]))
            if os.path.exists(dataset_path):
                dataset = read_reviewed_json(dataset_path)
            review_json_objs = read_reviewed_json(full_file_path)
            total_dataset_count_in_file = 0
            total_processing_dataset_count_in_file = 0
            total_processed_dataset_count_in_file = 0
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
                            'original': {
                                'highlighted': review_obj['highlighted']['text'],
                                'selected': review_obj['selected']['text'],
                            }
                        }
                    except KeyError:
                        total_dataset_count_in_file -= 1
                elif 'accepted' in dataset[source_key]:
                    total_processed_dataset_count_in_file += 1
                elif 'inferred' in dataset[source_key]:
                    total_processing_dataset_count_in_file += 1
                else:
                    total_dataset_count_in_file -= 1
            dataset_status[file] = {
                'total_dataset': total_dataset_count_in_file,
                'processing_dataset': total_processing_dataset_count_in_file,
                'processed_dataset': total_processed_dataset_count_in_file,
                'updated': datetime.now().strftime(DATETIME_FORMAT)
            }
            write_json(dataset, dataset_path)
    dataset_status['updated'] = datetime.now().strftime(DATETIME_FORMAT)
    write_json(dataset_status, dataset_status_file_path)
