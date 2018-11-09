#!/bin/bash
# -*- coding: UTF-8 -*-

set -e

script_dir=$(cd `dirname "$0"`; pwd; cd - 2>&1 >> /dev/null)
cd $script_dir

./regression.sh

cd ..
if [ -d "env" ]; then rm -rf env; fi
pip3 install virtualenv
virtualenv -p python3 env
source env/bin/activate

pip install pytest coverage pytest-cov
pip install -U .
py.test -vv --cov=rundoc --cov-report html
coverage report

exit 0

