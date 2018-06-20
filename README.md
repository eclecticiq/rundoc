rundoc 🏃📖
==================================================
[![Gitter Join Chat](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/rundoc/Lobby)
[![PyPI version](https://badge.fury.io/py/rundoc.svg)](https://badge.fury.io/py/rundoc)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Documentation Status](https://readthedocs.org/projects/rundoc/badge/?version=latest)](http://rundoc.readthedocs.io/en/latest/?badge=latest)

A command-line utility that runs code blocks from documentation written in markdown.

Overview
-------------------------

This utility allows you to run your markdown files as if they were scripts. Every code snippet with code highlighting tag is run with interpreter defined by the tag.

### Why do this?

We had a very long installation documentation for our project and needed a quick way of testing it. That's how rundoc is born. It is now a general purpose tool that can be used for multiple purposes like executing a tutorial documentation, using docs as a script, etc.

Installation
-------------------------

### install from pypi (recommend)
`pip3 install rundoc`

### install from github (latest master)
`pip3 install -U git+https://github.com/EclecticIQ/rundoc.git`

Usage
-------------------------

Rundoc collects fenced code blocks from input markdown file and executes them in same order as they appear in the file.

Example of fenced code block in markdown file:

    ```bash
    for x in `seq 0 10`; do
        echo $x
        sleep 1
    done
    ```

Interpreter will be automatically selected using the highlight tag of the code block (in above example `bash`). If highlight tag is not specified, rundoc will ignore that code block.

Rundoc can save json file after execution, which contains all code blocks and their outputs. You can also replay all the actions by running this output file.

### Run markdown file

Execute code blocks in *input.md* file:

```bash
rundoc run input.md
```

- You will be prompted before executing each code block with ability to modify the input.
- When done reviewing/modifying the code block, press *Return* to execute it and move to the next one.
- Program will exit when last code block is finished executing or when you press **ctrl+c**.

#### Skip prompts

You can use `-y` option to skip prompts and execute all code blocks without user interaction:

```bash
rundoc run -y input.md
```

If you need to add a delay between codeblocks, you can add `-p` or `--pause` option to specify number of seconds for the puase. This works only in conjunction with `-y`:

```bash
rundoc run -y -p 2 input.md
```

Some step fails first couple of times but it's normal? That may happen and you would just want to retry that step a couple of times. To do so use `-r` or `--retry` option followed by max number of retries and rundoc will run the same step again until it succeeds or reaches max retries in which case it will exit:

```bash
rundoc run -y -r 10 input.md
```

But you don't want it to retry right away, correct? You can specify a delay between each try with `-P` (capital P) or `--retry-pause` option followed by number of seconds:

```bash
rundoc run -y -r 10 -P 2 input.md
```

#### Start from specific step

You can start at specified step using `-s` or `--step` option:

```bash
rundoc run -s5 input.md
```

This is useful when your N-th code block fails and rundoc exits and you want to continue from that step.

#### Save output

Output can be saved as a json file containing these fields:

- `env` (dict): dictionary of set environment variables for the session
- `code_blocks` (list): list of code blocks that contains the following
    - `code` (str): original code
    - `interpreter` (str): interpreter used for this code block
    - `runs` (list): list of run attempts
        - `output` (str): merged stdout and stderr of the code block execution
        - `retcode` (int): exit code of the code block
        - `time_start` (float): timestamp when execution started (seconds from epoch)
        - `time_stop` (float): timestamp when execution finished (seconds from epoch)
        - `user_code` (str): code that user actually executed with prompt

To save output use `-o` or `--output` option when running rundoc:

```bash
rundoc run -y input.md -o output.json
```

#### Tags

By default, rundoc executes all fenced code blocks that have highlithing tag set in markdown file. If you want to limit execution to subset of the code blocks, use tags. Tags can be specified with `-t` or `--tags` option followed by hash (#) separated list of tags:

```bash
rundoc run -t bash#python3 input.md
```

This will execute only those code blocks that have at least one of the specified highlight tags: in this example only `bash` and `python` code blocks.

If you want to further isolate code blocks of the same highlight tag, you can use rundoc tag syntax, e.g.:

    ```bash#custom-branch#v2#test
    echo "custom-tagged code block"
    ```

In this syntax, multiple tags are applied to same code block and are separated with hash symbol `#`. In the example above there are 4 tags: `bash`, `custom-branch`, `v2` and `test`. First tag always defines the interpreter. If any of it's tags is specified by `-t` or `--tags` option, it will be executed. Code blocks that do not contain at least one of the specified tags will be skipped.

#### More tags

In addition to `-t` or `--tags` option, you can also use the following 2 options to furthere fine-tune your code block filtering:

- `-T` or `--must-have-tags` - same as `--tags` but it requires all listed tags to be present in the markdown code block or it will be skipped. The order of tags is not important.
- `-N`, or `--must-not-have-tags` - same as `--tags` but it requres that **none** of the listed tags is present in the markdown code block. It is used to filter out unwanted ones.

You can use any of the tags features individually or combine them.

#### Environment variables

Define required environment variables anywhere in the documentaion with a special code block tagged as `env` or `environment` at the beginning:

    ```env#version5
    var1=
    var2=
    var3=default_value_3
    var4=default_value_4
    ```

- As in example above, define variables one on each line.
- When you run the docs you will be prompted for those.
- Empty values (e.g. `var1` and `var2` in example) will try to collect actual values from your system environment, so if `var1` was exported before you ran the docs, it will collect it's value as the default value.
- If you used `-y` option, you will be prompted only for variables that have empty values and are not exported in your current system environment.
- All variables will be passed to env for every code block that's being executed.
- If you use rundoc with tag option `-t`, environment blocks will be filtered in the same way as code blocks.

#### Secrets

You can define required credentials or other secrets anywhere in the documentaion as a special code block tagged as `secret` or `secrets` at the beginning:

    ```secrets#production
    username=
    password=
    ```

Secrets behave just as `env` blocks with one single difference: they are never saved in the output file and are **expected to be empty in markdown file** so that user must provide them during execution. If you want to use rundoc as part of automation and can't input secrets by hand, you can always export them beforehand and use `-i` option (see next section).

#### Force variable collection

You can force rundoc to check if any of the variables defined with `env` tag is already exported in your current system environment and use it's value instead of the one defined in markdown file. To do this use `-i` or `--inherit-env` option when running rundoc. The list of variables that is presented to you when you run rundoc and that will be used in the session will now contain values defined in the system environment.

```bash
export var2=system_value_2
export var3=system_value_3
rundoc run input.md -i
```

### Replay

To replay all code blocks found in output of `run` command, just use `replay` command like so:

```bash
rundoc replay output.json
```

The above command will just turn last runs of each code block into a new code block and run them without prompting you about anything (like having `-y` option). It will ignore all run tries that did not succeed. Last run may have original command or user modified one and replay does not think about that, it just runs the last command it finds in each code block.

You can still use `-p`, `-s`, `-o`, `-r`, and `-P` options with `replay` command:

```bash
rundoc replay -s 2 -p 1 -r 20 -P 5 output.json -o replay_output.json
```

Tips and tricks
-------------------------

### Color output

Are you using light terminal background and can't see sh\*t? Use rundoc with `--light` option and save your eyesight!

### List tags

You can list all unique tags that appear in the file and their counts by using `list-tags` command:

```bash
rundoc list-tags input.md
```

### List code blocks

Wouldn't it be great to be able to list all code blocks that are going to be executed before actually using `run` command? You can! To print json file similar to output but without actually running anything you can use `list-blocks` command:

```bash
rundoc list-blocks -t bash -T tag1#tag2#tag3 -N tag4#tag5 input.md
```

or add `--pretty` option to have human readable output:

```bash
rundoc list-blocks -t bash -T tag1#tag2#tag3 -N tag4#tag5 input.md --pretty
```

