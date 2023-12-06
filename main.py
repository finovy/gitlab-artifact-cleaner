"""
This is a small python script to clear up old gitlab build artifacts.

There are 3 variables you should modify:
* base_url: path to your gitlab
* access_token: your personal access token to make gitlab api calls
* delete_everything_older_than: configure the timedelta as you wish

!!IMPORTANT!!
By default this script does only make dry-runs and does not actually delete any files!
In the second to last line is a function call. Change the dry_run=True to False to actually delete artifacts!
"""

import datetime
import functools
import json
import logging
import os.path
import re
import sys
from typing import Optional
from gitlab_config import base_url, access_token, filter_group, dry_run

import requests

now = datetime.datetime.now()
delete_everything_older_than = now - datetime.timedelta(weeks=4)


def fetch_projects(group=None):
    logging.debug('start fetching list of projects')
    list_of_projects = []

    for project_batch in make_api_call('/projects', {'simple': 'true', 'archived': 'false', 'per_page': 100}, True):
        projects_list = json.loads(project_batch)
        for p in projects_list:
            list_of_projects.append({
                'id': p['id'],
                'name': p['path_with_namespace'],
            })

    return list_of_projects


def fetch_jobs(project_id: str):
    list_of_jobs = []

    for jobs_batch in make_api_call(f"/projects/{project_id}/jobs", {'per_page': 2000}):
        jobs_list = json.loads(jobs_batch)
        for j in jobs_list:
            list_of_jobs.append({
                'id': j['id'],
                'project_id': project_id,
                'artifacts': j['artifacts'],
                'date': j['finished_at']
            })

    return list_of_jobs


date_format = "%Y-%m-%dT%H:%M:%S.%fZ"


def delete_artifacts_of_project(target_project, dry_run):
    deleted_bytes = 0

    total_num_of_jobs = len(target_project['jobs'])
    i = 0

    for job in target_project['jobs']:
        i += 1

        if len(job['artifacts']) == 0:
            continue

        date = datetime.datetime.strptime(job['date'], date_format)
        if date < delete_everything_older_than:
            deleted_bytes += functools.reduce(
                lambda total, artifact: total + artifact['size'] if artifact['size'] else 0, job['artifacts'], 0)

        if not dry_run:
            logging.info(f"deleting job artifacts of {target_project['project_name']}: [{i}/{total_num_of_jobs}]")
            try:
                make_api_call(f'/projects/{job["project_id"]}/jobs/{job["id"]}/artifacts', {}, method='delete',
                              all_pages=False)
            except RuntimeError:
                pass

    logging.info(f"deleted {format_bytes(deleted_bytes)} for project {target_project['project_name']}")
    return deleted_bytes

def build_projects_jobs_and_artifacts_list(list_of_projects):
    num_of_projects = len(list_of_projects)

    artifact_sizes_by_project = []

    i = 0
    for project in list_of_projects:
        i += 1
        logging.info(f'fetching {project["name"]} [{i}/{num_of_projects}]')
        jobs = fetch_jobs(project['id'])
        total_size = functools.reduce(
            lambda total, job: total + (
                functools.reduce(lambda sub_total, artifact: sub_total + artifact['size'] if artifact['size'] else 0,
                                 job['artifacts'], 0)),
            jobs, 0)
        artifact_sizes_by_project.append({
            'project_id': project['id'],
            'project_name': project['name'],
            'total_size': total_size,
            'jobs': jobs
        })

    artifact_sizes_by_project.sort(key=lambda e: e['total_size'], reverse=True)
    return artifact_sizes_by_project


def make_api_call(path: str, params: dict, all_pages: bool = True, method: str = 'get'):
    api_url = base_url + '/api/v4'

    params_for_request = f"?access_token={access_token}"
    for key, value in params.items():
        params_for_request += f"&{key}={value}"

    url = api_url + path + params_for_request
    results = []
    while url is not None:
        logging.debug(f'GET request to {url}')

        if method == 'get':
            result = requests.get(url)
        elif method == 'delete':
            result = requests.delete(url)
        else:
            raise RuntimeError(f"unsupported method '{method}'")

        if result.status_code >= 400:
            logging.error(f'API call failed! Got response code {result.status_code} when tried to call {url}')
            break

        results.append(result.content)
        url = get_next_from_link_header(result.headers.get('Link')) if all_pages else None

    return results


def get_next_from_link_header(link_header: str) -> Optional[str]:
    # look for next page to visit
    p = re.compile('(<(https://\S+)>; rel=\"next")')
    hits = p.findall(link_header)
    if len(hits) == 0:
        return None

    return hits[0][1]


# got it from https://stackoverflow.com/questions/12523586/python-format-size-application-converting-b-to-kb-mb-gb-tb
def format_bytes(bytes_to_format):
    """Return the given bytes as a human friendly kb, mb, gb, or tb string."""
    b = float(bytes_to_format)
    kb = float(1024)
    mb = float(kb ** 2)  # 1,048,576
    gb = float(kb ** 3)  # 1,073,741,824
    tb = float(kb ** 4)  # 1,099,511,627,776

    if b < kb:
        return '{0} {1}'.format(b, 'Bytes' if 0 == b > 1 else 'Byte')
    elif kb <= b < mb:
        return '{0:.2f} KB'.format(b / kb)
    elif mb <= b < gb:
        return '{0:.2f} MB'.format(b / mb)
    elif gb <= b < tb:
        return '{0:.2f} GB'.format(b / gb)
    elif tb <= b:
        return '{0:.2f} TB'.format(b / tb)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    projects_fil = []

    if not access_token:
        logging.error('access_token must be set!')
        sys.exit(1)

    if not base_url:
        logging.error('base_url must be set!')
        sys.exit(1)

    if not os.path.exists('projects.json'):
        projects = fetch_projects()
        fp = open('projects.json', 'w')
        json.dump(projects, fp)
        fp.close()
    else:
        projects = json.load(open('projects.json', 'r'))

    for i in projects:
        if filter_group not in [None, ""]:
            if filter_group in i['name']:
                projects_fil.append(i)

    for project in projects_fil:
        delete_artifacts_of_project(project, dry_run=dry_run)
