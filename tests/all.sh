#!/bin/bash
# -*- coding: UTF-8 -*-

set -e

script_dir=$(cd `dirname "$0"`; pwd; cd - 2>&1 >> /dev/null)
cd $script_dir

./regression.sh

exit 0

