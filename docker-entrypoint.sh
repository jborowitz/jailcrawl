#!/bin/bash

set -e

# Drop root privileges if we are running elasticsearch
if [ "$1" = 'test' ]; then
    export PYTHONPATH="${PYTHONPATH}:/opt/scraper_common/" && \
        cd /opt/ && \
	python ./Alabama_calhoun.py
    exit 0
fi

# Drop root privileges if we are running elasticsearch
if [ "$1" = 'run_one' ]; then
    export PYTHONPATH="${PYTHONPATH}:/opt/scraper_common/" && \
        cd /opt/ && \
	python $2
    exit 0
fi

