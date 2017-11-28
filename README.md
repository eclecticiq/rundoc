rundoc
==================================================

Run code blocks from documentation written in markdown.

Installation
-------------------------

### install from pypi
`pip3 install fusecry`  

### install from github
`pip3 install -U git+https://github.com/EclecticIQ/rundoc.git`

Usage
-------------------------

Rundoc collects fenced code blocks from input markdown file and executes them in same order as they appear in the file.

Example of fenced code block in markdown file:

~~~markdown
 ```bash
 for x in `seq 0 10`; do
     echo $x
     sleep 1
 done
 ```
~~~

Interpreter will be automatically selected using the highlight tag of the code block (in our example `bash`). If highlight tag is not specified, bash will be used by default.

### Run markdown file

- Execute code blocks in *input.md* file:

```bash
rundoc run input.md
```

- You will be prompted before executing each code block with ability to modify the input.
- When done reviewing/modifying the code block, press *Return* to execute it and move to the next one.
- Program will exit when last code block is finished executing or when any code block exits with non 0 exit code.

### Skip prompts

You can use `-y` option to skip prompts and execute all code blocks without user interaction:

```bash
rundoc run -y input.md
```

If you need to add a delay between codeblocks, you can add `-p` or `--pause` option to specify number of seconds for the puase. This works only in conjunction with `-y`:

```bash
rundoc run -y -p 2 input.md
```

### Start from specific step

You can start at specified step using `-s` or `--step` option:

```bash
rundoc run -s5 input.md
```

This is useful when your N-th code block exits with error and you want to continue from that step.

### Save output

Output can be saved as a json list of executed code blocks containing:

- `code_blocks`: list of code blocks that contains the following
    - `code`: original code
    - `user_code`: code that user actually executed with prompt
    - `interpreter`: interpreter used for this code block
    - `output`
        - `stdout`: complete stdout of the code block
        - `retcode`: exit code of the code block
- `env`: dictionary of set environment variables for the session

To save output use `-o` or `--output` option:

```bash
rundoc run input.md -o output.json
```

### Tags

By default, rundoc executes all fenced code blocks. If you want to limit execution to subset of the code blocks, use tags. Tags can be specified with `-t` or `--tags` option followed by comma-separated list of tags:

```bash
rundoc run -t bash,python3 input.md
```

This will execute only those code blocks that have specified highlight tag.

If you want to further isolate code blocks of the same highlight tag, you can use rundoc tag syntax, e.g.:

~~~markdown
 ```bash_custom-branch_v2_test
 echo "custom-tagged code block"
 ```
~~~

In this syntax, multiple tags are applied to same code block and are separated with underscore `_`. In the example above there are 3 tags: `bash`, `custom-branch`, `v2` and `test`. First tag always defines the interpreter. If any of it's tags is specified by `--tags` option, it will be executed. Code blocks that do not contain any of the specified tags will be skipped.

### Environment variables

You can define required environment variables anywhere in the documentaion as a spectial code block tagged as `env`:

~~~markdown
 ```env
 var1=
 var2=
 var3=default_value_3
 var4=default_value_4
 ```
~~~

- As in example above, define variables one on each line.
- When you run the docs you will be prompted for those.
- Empty values (e.g. `var1` and `var2` in example) will try to collect actual values from your environment, so if `var1` was exported before you ran the docs, it will collect it's value as the default value.
- If you used `-y` option, you will be prompted only for variables that have empty values and are not exported in your current system environment.
- All variables will be passed to env for every code block that's being executed.

