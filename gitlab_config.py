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

import os

# gitlab url
base_url = os.getenv('BASE_URL', '')

# gitlab access_token
access_token = os.getenv('ACCESS_TOKEN', '')

# clean up dest filter_group project
filter_group = os.getenv('GROUP', '')

# clean up dest filter_id project
filter_id = os.getenv('PROJECT_ID', '')

# dry_run
dry_run = bool(int(os.getenv('DRY_RUN', 0)) == 1)
