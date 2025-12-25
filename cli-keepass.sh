#!/bin/bash
#Start script for the gt7-journal app on a linux systems.
BASEDIR=$(dirname $0)
cd $BASEDIR
if [ -z ${VIRTUAL_ENV+x} ]; then
    . venv/bin/activate
fi
python cli-main.py $@