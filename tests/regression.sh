#!/bin/bash
# -*- coding: UTF-8 -*-

###
#
# Regression tests for rundoc tool
#
###

script_dir=$(cd `dirname "$0"`; pwd; cd - 2>&1 >> /dev/null)
cd $script_dir

if [ "$1" = "gen" ]; then
    generate=true
elif [ "$1" = "" ]; then
    generate=false
else
    echo "Bad option $1"
    exit 1
fi


# tools

tests=0
failed_tests=0

verify_zero_exit() {
    if [ "$?" != "0" ]; then
        echo "Exited with non 0, but 0 expected."
        ((failed_tests++))
    fi
}

verify_non_zero_exit() {
    if [ "$?" = "0" ]; then
        echo "Exited with 0, but failure expected."
        ((failed_tests++))
    fi
}

strip_timestamps() {
    local file_path=$1
    sed -ri '/^\s*"time_(start|stop)": [0-9]{10}\.[0-9]*,?$/d' $file_path
}

# good tests

## tags
test_tags() {
    tags=$1
    ((tests++))
    if $generate; then
        local file_name=regression_test_good_$tags.json
    else
        echo -n "Test tags: $tags"
        local file_name=out_test_good_$tags.json
    fi
    if [ -z $tags ]; then
        rundoc run -y test_good.md \
            -o $file_name > /dev/null
    else
        rundoc run -y test_good.md \
            -o $file_name -t $(echo $tags | sed 's/_/,/g') > /dev/null
    fi
    verify_zero_exit
    strip_timestamps $file_name
    if ! $generate; then
        # compare with existing ones
        diff \
            regression_test_good_$tags.json \
            out_test_good_$tags.json \
            > /dev/null 2>&1
        if [ "$?" != 0 ]; then
            ((failed_tests++))
            echo " -> failed"
        else
            echo " -> success"
        fi
        rm -f $file_name
    fi
}
test_tags
test_tags bad-tag
test_tags bash
test_tags python3
test_tags block-1
test_tags block-2
test_tags block-1_block-2
test_tags block-2_block-1
test_tags python_bash
test_tags bash_python


# done
tests=0
failed_tests=0

