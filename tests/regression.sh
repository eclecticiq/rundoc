#!/bin/bash
# -*- coding: UTF-8 -*-

###
#
# Regression tests for rundoc tool
#
###

script_dir=$(cd `dirname "$0"`; pwd; cd - 2>&1 >> /dev/null)
cd $script_dir/regression_test_files

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
        echo -n "$tests. Test tags: $tags"
        local file_name=out_test_good_$tags.json
    fi
    if [ -z $tags ]; then
        rundoc run -y test_good.md \
            -o $file_name > /dev/null
    else
        rundoc run -y test_good.md \
            -o $file_name -t $tags > /dev/null
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

### SCRIPT STARTS HERE

echo "
Rundoc regression tests
=======================
"

test_tags
test_tags bad-tag
test_tags bash
test_tags python3
test_tags block-1
test_tags block-2
test_tags block-1#block-2
test_tags block-2#block-1
test_tags python#bash
test_tags bash#python


# bad tests
((tests++))
if $generate; then
    rundoc run -y test_bad.md -o regression_test_bad_.json
else
    echo -n "$tests. Test stderr."
    rundoc run -y test_bad.md -o out_test_bad_.json > /dev/null 2>&1
    compare_len=$(<regression_test_bad_.json | grep '"output"' | wc -c)
    test_len=$(<out_test_bad_.json | grep '"output"' | wc -c)
    # because the order of the output is unpredictable we only compare the len
    if [ "$compare_len" == "$test_len" ]; then
        echo " -> success"
    else
        ((failed_tests++))
        echo " -> failed"
    fi
    rm -f out_test_bad_.json
fi

# done
echo "Tests run: $tests"
echo "Failed tests: $failed_tests"
exit $failed_tests

