#!/bin/bash

set -e

if [ "$1" = 'test' ]; then
    export PYTHONPATH="${PYTHONPATH}:/opt/scraper_common/" && \
        cd /opt/ && \
	python ./Alabama_calhoun.py
    exit 0
fi

if [ "$1" = 'run_one' ]; then
    export PYTHONPATH="${PYTHONPATH}:/opt/scraper_common/" && \
        cd /opt/ && \
	python $2
    exit 0
fi

if [ "$1" = 'run_all' ]; then
    export PYTHONPATH="${PYTHONPATH}:/opt/scraper_common/" && \
        cd /opt/ && \
	python ./jailscrape/runall.py
    exit 0
fi

