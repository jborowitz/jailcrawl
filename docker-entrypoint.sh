#!/bin/bash

set -e

# Drop root privileges if we are running elasticsearch
if [ "$1" = 'test' ]; then
    export PYTHONPATH="${PYTHONPATH}:/opt/scraper_common/" && \
        cd /opt/ && \
	python ./Alabama-Connecticut\ Complete/Alabama-Complete/Alabama_calhoun_201982.py
    exit 0
fi

