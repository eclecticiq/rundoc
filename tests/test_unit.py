import inspect
import io
import json
import os
import re
import stat
import tempfile
import threading
import time
from types import *

import pytest
from pygments import highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexers import get_lexer_by_name
from pygments.styles.manni import ManniStyle
from pygments.styles.native import NativeStyle

import rundoc.__main__ as rm
import rundoc.block as rb
import rundoc.commander as rc
import rundoc.parsers as rp
from rundoc import BadInterpreter, BadEnv, RundocException, CodeFailed


###
# Fixtures
###

@pytest.fixture
def environment():
    e = {
        'custom_var1': '1',
        'CUSTOM_VAR2': '2',
        'custom_var3': 'some text',
    }
    for key in e:
        os.environ[key] = e[key]
    return e


@pytest.fixture
def orderedenv(environment):
    oenv = rc.OrderedEnv()
    for var in environment:
        oenv.append(var, environment[var])
    return oenv


@pytest.fixture
def test_vars():
    return [
        ('test1', 'value111'),
        ('test2', 'value222'),
        ('test3', 'value333'),
    ]


@pytest.yield_fixture
def sandbox():
    with tempfile.TemporaryDirectory() as directory:
        yield directory


@pytest.yield_fixture
def dummy_file(sandbox, environment):
    fpath = os.path.join(sandbox, 'dummy_file')
    with open(fpath, 'a+') as f:
        f.write('some {dummy} data\n')
        for key in environment:
            f.write(' abc %:' + key + ':%')
    yield fpath


@pytest.fixture
def docblock_bash():
    code = 'echo "it is working"'
    # use bash as interpreter
    tags = ['bash', 'test', 'main']
    light = False
    return rb.DocBlock(code, tags, light)


@pytest.fixture
def docblock_bash_light():
    code = 'echo "it is working"'
    # use bash as interpreter
    tags = ['bash', 'test', 'main']
    # color print optimized for light background terminal
    light = True
    return rb.DocBlock(code, tags, light)


@pytest.fixture
def docblock_unknown():
    code = 'echo "it is working"'
    # use binary in path as interpreter but one that has no code highlighting
    tags = ['cd', 'test', 'main']
    light = False
    return rb.DocBlock(code, tags, light)


@pytest.fixture
def mkd_file():
    data = b'bash#test\nls\n```\n\n```bash#test\nls -al\n```'
    f = io.BytesIO()
    f.write(data)
    f.seek(0)
    return f


###
# Tests for block.py
###

REGISTERED_BLOCK_ACTIONS = 5


def test_block_action():
    assert len(rb.block_actions) == REGISTERED_BLOCK_ACTIONS

    def dummy_block_action(args, contents):
        return 0

    rb.block_action(dummy_block_action)
    assert len(rb.block_actions) == REGISTERED_BLOCK_ACTIONS + 1
    assert type(rb.block_actions['dummy-block-action']) == FunctionType
    assert rb.block_actions['dummy-block-action'] == dummy_block_action
    del (rb.block_actions['dummy-block-action'])
    assert len(rb.block_actions) == REGISTERED_BLOCK_ACTIONS


def test_fill_env_placeholders__valid(environment):
    before = ''
    for key in environment:
        before += ' abc %:' + key + ':%'
    after = before.replace('%:', '{').replace(':%', '}').format(**environment)
    assert rb.fill_env_placeholders(before) == after


def test_fill_env_placeholders__unclosed(environment):
    invalid_env = 'Text %:invalid_var '
    before = ''
    for key in environment:
        before += ' abc %:' + key + ':%'
    after = before.replace('%:', '{').replace(':%', '}').format(**environment)
    before = invalid_env + before + invalid_env
    after = invalid_env + after + invalid_env
    assert rb.fill_env_placeholders(before) == after


def test_fill_env_placeholders__unopened(environment):
    invalid_env = 'Text invalid_var:% '
    before = ''
    for key in environment:
        before += ' abc %:' + key + ':%'
    after = before.replace('%:', '{').replace(':%', '}').format(**environment)
    before = invalid_env + before + invalid_env
    after = invalid_env + after + invalid_env
    assert rb.fill_env_placeholders(before) == after


def test_write_file_action__no_fill(sandbox):
    testfile = os.path.join(sandbox, inspect.currentframe().f_code.co_name)
    before = 'some random text\nmore text'
    rb._write_file_action({0: testfile, 1: '774'}, before, fill=False)
    with open(testfile, 'r') as f:
        assert f.read() == before + '\n'


def test_write_file_action__fill(sandbox, environment):
    testfile = os.path.join(sandbox, inspect.currentframe().f_code.co_name)
    before = 'some random text\nmore text'
    for key in environment:
        before += ' abc %:' + key + ':%'
    after = before.replace('%:', '{').replace(':%', '}').format(**environment)
    rb._write_file_action({0: testfile, 1: '774'}, before, fill=True)
    with open(testfile, 'r') as f:
        assert f.read() == after + '\n'


def test_create_file__fresh(sandbox, environment):
    testfile = os.path.join(sandbox, inspect.currentframe().f_code.co_name)
    before = ''
    for key in environment:
        before += ' abc %:' + key + ':%'
    after = before.replace('%:', '{').replace(':%', '}').format(**environment)
    rb._create_file({0: testfile}, before)
    with open(testfile, 'r') as f:
        assert f.read() == before + '\n'


def test_create_file__existing(sandbox, environment, dummy_file):
    testfile = dummy_file
    before = ''
    for key in environment:
        before += ' abc %:' + key + ':%'
    after = before.replace('%:', '{').replace(':%', '}').format(**environment)
    rb._create_file({0: testfile}, before)
    with open(testfile, 'r') as f:
        assert f.read() == before + '\n'


def test_r_create_file__fresh(sandbox, environment):
    testfile = os.path.join(sandbox, inspect.currentframe().f_code.co_name)
    before = ''
    for key in environment:
        before += ' abc %:' + key + ':%'
    after = before.replace('%:', '{').replace(':%', '}').format(**environment)
    rb._r_create_file({0: testfile}, before)
    with open(testfile, 'r') as f:
        assert f.read() == after + '\n'


def test_r_create_file__existing(sandbox, environment, dummy_file):
    testfile = dummy_file
    before = ''
    for key in environment:
        before += ' abc %:' + key + ':%'
    after = before.replace('%:', '{').replace(':%', '}').format(**environment)
    rb._r_create_file({0: testfile}, before)
    with open(testfile, 'r') as f:
        assert f.read() == after + '\n'


def test_create_file__permissions(sandbox, environment):
    testfile = os.path.join(sandbox, inspect.currentframe().f_code.co_name)
    permissions = '777'
    before = ''
    for key in environment:
        before += ' abc %:' + key + ':%'
    after = before.replace('%:', '{').replace(':%', '}').format(**environment)
    rb._create_file({0: testfile, 1: permissions}, before)
    with open(testfile, 'r') as f:
        assert f.read() == before + '\n'
    assert str(oct(os.stat(testfile)[stat.ST_MODE]))[-3:] == permissions


def test_r_create_file__permissions(sandbox, environment):
    testfile = os.path.join(sandbox, inspect.currentframe().f_code.co_name)
    permissions = '777'
    before = ''
    for key in environment:
        before += ' abc %:' + key + ':%'
    after = before.replace('%:', '{').replace(':%', '}').format(**environment)
    rb._r_create_file({0: testfile, 1: permissions}, before)
    with open(testfile, 'r') as f:
        assert f.read() == after + '\n'
    assert str(oct(os.stat(testfile)[stat.ST_MODE]))[-3:] == permissions


def test_append_file__fresh(sandbox, environment):
    testfile = os.path.join(sandbox, inspect.currentframe().f_code.co_name)
    before = ''
    for key in environment:
        before += ' abc %:' + key + ':%'
    after = before.replace('%:', '{').replace(':%', '}').format(**environment)
    rb._append_file({0: testfile}, before)
    with open(testfile, 'r') as f:
        assert f.read() == before + '\n'


def test_append_file__existing(sandbox, environment, dummy_file):
    testfile = dummy_file
    with open(dummy_file, 'r') as f:
        initial_contents = f.read()
    before = ''
    for key in environment:
        before += ' abc %:' + key + ':%'
    after = before.replace('%:', '{').replace(':%', '}').format(**environment)
    rb._append_file({0: testfile}, before)
    with open(testfile, 'r') as f:
        assert f.read() == initial_contents + before + '\n'


def test_r_append_file__fresh(sandbox, environment):
    testfile = os.path.join(sandbox, inspect.currentframe().f_code.co_name)
    before = ''
    for key in environment:
        before += ' abc %:' + key + ':%'
    after = before.replace('%:', '{').replace(':%', '}').format(**environment)
    rb._r_append_file({0: testfile}, before)
    with open(testfile, 'r') as f:
        assert f.read() == after + '\n'


def test_r_append_file__existing(sandbox, environment, dummy_file):
    testfile = dummy_file
    with open(dummy_file, 'r') as f:
        initial_contents = f.read()
    before = ''
    for key in environment:
        before += ' abc %:' + key + ':%'
    after = before.replace('%:', '{').replace(':%', '}').format(**environment)
    rb._r_append_file({0: testfile}, before)
    with open(testfile, 'r') as f:
        assert f.read() == initial_contents + after + '\n'


def test_append_file__permissions(sandbox, environment):
    testfile = os.path.join(sandbox, inspect.currentframe().f_code.co_name)
    permissions = '777'
    before = ''
    for key in environment:
        before += ' abc %:' + key + ':%'
    after = before.replace('%:', '{').replace(':%', '}').format(**environment)
    rb._append_file({0: testfile, 1: permissions}, before)
    with open(testfile, 'r') as f:
        assert f.read() == before + '\n'
    assert str(oct(os.stat(testfile)[stat.ST_MODE]))[-3:] == permissions


def test_r_append_file__permissions(sandbox, environment):
    testfile = os.path.join(sandbox, inspect.currentframe().f_code.co_name)
    permissions = '777'
    before = ''
    for key in environment:
        before += ' abc %:' + key + ':%'
    after = before.replace('%:', '{').replace(':%', '}').format(**environment)
    rb._r_append_file({0: testfile, 1: permissions}, before)
    with open(testfile, 'r') as f:
        assert f.read() == after + '\n'
    assert str(oct(os.stat(testfile)[stat.ST_MODE]))[-3:] == permissions


def test_docblock_init_with_bad_interpreter():
    with pytest.raises(BadInterpreter):
        rb.DocBlock(tags=['bad_interpreter'], code='')


def test_get_block_action__known_actions():
    for action in {
        'create-file',
        'r-create-file',
        'append-file',
        'r-append-file',
    }:
        assert isinstance(rb.get_block_action(action + ':text'), LambdaType)


def test_get_block_action__undefined_action():
    assert rb.get_block_action('unknown:text') == None


def test_docblock__get_lexer__bash(docblock_bash):
    db_lexer = docblock_bash.get_lexer()
    pygments_lexer = get_lexer_by_name('bash')
    assert db_lexer.__class__ == pygments_lexer.__class__


def test_docblock__get_lexer__unknown(docblock_unknown):
    db_lexer = docblock_unknown.get_lexer()
    assert db_lexer == None


def test_docblock__str(docblock_bash):
    code = docblock_bash.code
    interpreter = docblock_bash.interpreter
    lexer_class = get_lexer_by_name(interpreter)
    s = highlight(code, lexer_class, Terminal256Formatter(style=NativeStyle))
    assert str(docblock_bash) == s


def test_docblock_str__last_run(docblock_bash):
    user_code = 'echo "changed"'
    docblock_bash.runs.append(
        {
            'user_code': user_code,
            'output': '',
            'retcode': None,
            'time_start': None,
            'time_stop': None,
        }
    )
    docblock_bash.last_run['user_code'] = user_code
    interpreter = docblock_bash.interpreter
    lexer_class = get_lexer_by_name(interpreter)
    s = highlight(user_code, lexer_class, Terminal256Formatter(style=NativeStyle))
    assert str(docblock_bash) == s


def test_docblock__str__light(docblock_bash_light):
    code = docblock_bash_light.code
    interpreter = docblock_bash_light.interpreter
    lexer_class = get_lexer_by_name(interpreter)
    s = highlight(code, lexer_class, Terminal256Formatter(style=ManniStyle))
    assert str(docblock_bash_light) == s


def test_docblock__get_dict(docblock_bash):
    assert type(docblock_bash.get_dict()) == type({})
    bash_block_dict = {
        'interpreter': 'bash',
        'code': 'echo "this is a test"',
        'tags': ['bash', 'test', 'main'],
        'runs': []
    }
    docblock = rb.DocBlock(
        bash_block_dict['code'],
        bash_block_dict['tags'],
    )
    actual_dict = docblock.get_dict()
    assert bash_block_dict == actual_dict
    docblock.run(prompt=False)
    while docblock.process:
        time.sleep(0.1)
    actual_dict = docblock.get_dict()
    for key in ('interpreter', 'code', 'tags'):
        assert bash_block_dict[key] == actual_dict[key]
    assert actual_dict['runs'][0]['user_code'] == docblock.code
    assert actual_dict['runs'][0]['output'] == 'this is a test\n'
    assert actual_dict['runs'][0]['retcode'] == 0
    assert actual_dict['runs'][0]['time_start'] > 0
    assert actual_dict['runs'][0]['time_stop'] > 0


def docblock_worker(docblock):
    docblock.run(prompt=False)


def test_docblock__run_and_kill():
    # Note that kill will only send SIGKILL to the running process without
    # any knowledge on how this will be handeled. What is guaranteed is that
    # process.poll() will contain some exitcode.
    docblock = rb.DocBlock(
        'echo "start"\nsleep 2\necho "this is test"',
        ['bash', 'test'],
    )
    assert docblock.process == None
    t = threading.Thread(target=docblock_worker, args=(docblock,))
    t.start()
    time.sleep(1)
    assert docblock.process and docblock.process.poll() is None
    docblock.kill()
    time.sleep(0.1)
    assert docblock.process and type(docblock.process.poll()) is int


def test_docblock__run_action(dummy_file):
    docblock = rb.DocBlock(
        'some content',
        ['r-create-file:{}'.format(dummy_file), 'test'],
    )
    docblock.run(prompt=False)
    assert docblock.last_run['retcode'] == 0


def test_docblock__run_unknown_action():
    with pytest.raises(BadInterpreter):
        docblock = rb.DocBlock(
            'some content',
            ['unknown-action:bad-data', 'test'],
        )


###
# Tests for commander.py
###

def test_orderedenv__str(orderedenv, environment):
    for var in environment:
        assert orderedenv[var] == environment[var]
    assert len(orderedenv) == len(environment)
    assert "\n".join([var + "=" + environment[var] for var in environment]) == \
           str(orderedenv)


def test_orderedenv__append(orderedenv):
    s = str(orderedenv)
    s_append = '\ntest=value123'
    orderedenv.append('test', 'value123')
    assert str(orderedenv) == s + s_append


def test_orderedenv__extend(orderedenv, test_vars):
    s = str(orderedenv)
    s_extend = '\n' + '\n'.join(['{0}={1}'.format(vars[0], vars[1]) for vars in test_vars])
    orderedenv_extend = rc.OrderedEnv()
    for var, value in test_vars:
        orderedenv_extend.append(var, value)
    orderedenv.extend(orderedenv_extend)
    assert str(orderedenv) == s + s_extend


def test_orderedenv__import_string(orderedenv, test_vars):
    s = str(orderedenv)
    s_import = '\n' + '\n'.join(['{0}={1}'.format(vars[0], vars[1]) for vars in test_vars])
    orderedenv.import_string(s_import)
    assert str(orderedenv) == s + s_import


def test_orderedenv__import_string__no_equal(orderedenv, test_vars):
    s_import = "bad env format"
    with pytest.raises(BadEnv):
        orderedenv.import_string(s_import)


def test_orderedenv__import_string__missing_var(orderedenv, test_vars):
    s_import = "=value777"
    with pytest.raises(BadEnv):
        orderedenv.import_string(s_import)


def test_orderedenv__load(orderedenv, test_vars):
    s = str(orderedenv)
    s_load = '\n' + '\n'.join(['{0}={1}'.format(vars[0], vars[1]) for vars in test_vars])
    for var, value in test_vars:
        os.environ[var] = value
    for var, value in test_vars:
        orderedenv.append(var, '')
    orderedenv.load()
    assert str(orderedenv) == s + s_load


def test_orderedenv__inherit_existing_env(orderedenv, test_vars):
    s = str(orderedenv)
    s_load = '\n' + '\n'.join(['{0}={1}'.format(vars[0], vars[1]) for vars in test_vars])
    for var, value in test_vars:
        os.environ[var] = value
    for var, value in test_vars:
        orderedenv.append(var, 'bad value')
    orderedenv.inherit_existing_env()
    assert str(orderedenv) == s + s_load


def test_doccommander_doc_block__step():
    dc = rc.DocCommander()
    dc.add('ls\n', ['bash', 'test1'])
    dc.step = 1
    assert dc.doc_block == dc.doc_blocks[0]


def test_doccommander_doc_block__no_step():
    dc = rc.DocCommander()
    dc.add('ls\n', ['bash', 'test1'])
    assert dc.doc_block == None


def test_doccommander_get_dict():
    dc = rc.DocCommander()
    dc.add('ls\n', ['bash', 'test1'])
    assert dc.get_dict() == {
        "code_blocks": [
            {
                "code": "ls\n",
                "tags": ["bash", "test1"],
                "interpreter": "bash",
                "runs": []
            }
        ], "env": {}
    }


def test_doccommander_add():
    dc = rc.DocCommander()
    assert len(dc.doc_blocks) == 0
    dc.add('ls\n', ['bash', 'test1'])
    assert len(dc.doc_blocks) == 1
    assert dc.doc_blocks[0].code == 'ls\n'
    assert dc.doc_blocks[0].tags == ['bash', 'test1']
    dc.add('ls -al\n', ['bash', 'test2'])
    assert len(dc.doc_blocks) == 2
    assert dc.doc_blocks[0].code == 'ls\n'
    assert dc.doc_blocks[0].tags == ['bash', 'test1']
    assert dc.doc_blocks[1].code == 'ls -al\n'
    assert dc.doc_blocks[1].tags == ['bash', 'test2']


def doccommander_worker(dc):
    try:
        dc.run()
    except ValueError as e:
        # in case output file was closed prematuraly
        pass


def test_doccommander_add__while_running():
    dc = rc.DocCommander()
    dc.add('sleep 2\n', ['bash', 'test1'])
    t = threading.Thread(target=doccommander_worker, args=(dc,))
    t.start()
    time.sleep(1)
    with pytest.raises(RundocException):
        dc.add('echo "bad"\n', ['bash', 'test1'])


def test_doccommander_add__unknown_interpreter():
    dc = rc.DocCommander()
    with pytest.raises(SystemExit):
        dc.add('sleep 1\n', ['unknown', 'test1'])


def test_doccommander_die_with_grace(dummy_file):
    dc = rc.DocCommander()
    dc.add('echo "test"\n', ['bash', 'test1'])
    dc.add('sleep 2\n', ['bash', 'test1'])
    with open(dummy_file, 'w') as f:
        dc.output = f
        t = threading.Thread(target=doccommander_worker, args=(dc,))
        t.start()
        time.sleep(1)
        dc.die_with_grace()
    with open(dummy_file, 'r') as f:
        output = json.loads(f.read())
        assert output['code_blocks'][0]['runs'][0]['output'] == 'test\n'


def test_doccommander_write_output(dummy_file):
    dc = rc.DocCommander()
    dc.add('echo "test"\n', ['bash', 'test1'])
    dc.run()
    with open(dummy_file, 'w') as f:
        dc.output = f
        dc.write_output()
    with open(dummy_file, 'r') as f:
        output = json.loads(f.read())
        assert len(output['code_blocks']) == 1


def test_doccommander_run(dummy_file):
    dc = rc.DocCommander()
    dc.add('echo "test1"\n', ['bash', 'test1'])
    dc.add('echo "test2"\n', ['bash', 'test1'])
    dc.add('echo "test3"\n', ['bash', 'test1'])
    with open(dummy_file, 'w') as f:
        dc.run(inherit_env=True, output=f)
    assert len(dc.get_dict()['code_blocks']) == 3
    for cb in dc.get_dict()['code_blocks']:
        assert len(cb['runs']) == 1


def test_doccommander_run__failed():
    dc = rc.DocCommander()
    dc.add('cat /non_existent', ['bash', 'test1'])
    with pytest.raises(CodeFailed):
        dc.run(retry=5, retry_pause=0.1)


###
# Tests for parsers.py
###

def test_parsers__mkd_to_html__select_none():
    data = '```bash#test1\nls\n```\n\n```bash#test2\nls -al\n```'
    assert rp.mkd_to_html(
        data) == '<pre><code class="bash test1 rundoc_selected">ls\n</code></pre>\n\n<pre><code class="bash test2 rundoc_selected">ls -al\n</code></pre>'


def test_parsers__mkd_to_html__select_bash():
    data = '```bash#test1\nls\n```\n\n```bash#test2\nls -al\n```'
    assert rp.mkd_to_html(data,
                          'bash') == '<pre><code class="bash test1 rundoc_selected">ls\n</code></pre>\n\n<pre><code class="bash test2 rundoc_selected">ls -al\n</code></pre>'


def test_parsers__mkd_to_html__select_test1():
    data = '```bash#test1\nls\n```\n\n```bash#test2\nls -al\n```'
    assert rp.mkd_to_html(data,
                          'test1') == '<pre><code class="bash test1 rundoc_selected">ls\n</code></pre>\n\n<pre><code class="bash test2">ls -al\n</code></pre>'


def test_parsers__mkd_to_html__select_test2():
    data = '```bash#test1\nls\n```\n\n```bash#test2\nls -al\n```'
    assert rp.mkd_to_html(data,
                          'test2') == '<pre><code class="bash test1">ls\n</code></pre>\n\n<pre><code class="bash test2 rundoc_selected">ls -al\n</code></pre>'


def test_parsers__mkd_to_html__select_bash_diselect_test2():
    data = '```bash#test1\nls\n```\n\n```bash#test2\nls -al\n```'
    assert rp.mkd_to_html(data, 'bash', '',
                          'test2') == '<pre><code class="bash test1 rundoc_selected">ls\n</code></pre>\n\n<pre><code class="bash test2">ls -al\n</code></pre>'


def test_parsers__mkd_to_html__select_must_have_test2():
    data = '```bash#test1\nls\n```\n\n```bash#test2\nls -al\n```'
    assert rp.mkd_to_html(data, '', 'test2',
                          '') == '<pre><code class="bash test1">ls\n</code></pre>\n\n<pre><code class="bash test2 rundoc_selected">ls -al\n</code></pre>'


def test_parsers__parse_doc():
    f = io.StringIO()
    data = '```env\na=b\n```\n```bash#test1\nls\n```\n\n```bash#test2\nls -al\n```'
    expected = rc.DocCommander()
    expected.add('ls\n', ['bash', 'test1'])
    expected.add('ls -al\n', ['bash', 'test2'])
    f.write(data)
    f.seek(0)
    c = rp.parse_doc(f, 'bash')
    assert c.get_dict() == expected.get_dict()


def test_parsers__parse_doc__single_session():
    f = io.StringIO()
    data = '```env\na=b\n```\n```bash#test1\nls\n```\n\n```bash#test2\nls -al\n```'
    expected = rc.DocCommander()
    expected.add('ls\nls -al\n', ['bash'])
    expected.env.import_string("a=b")
    f.write(data)
    f.seek(0)
    c = rp.parse_doc(f, single_session='bash')
    assert c.get_dict() == expected.get_dict()


def test_parsers__parse_output():
    data = '```env\na=b\n```\n```bash#test1\nls\n```\n\n```bash#test2\nls -al\n```'
    input = io.StringIO()
    input.write(data)
    input.seek(0)
    c1 = rp.parse_doc(input)
    json1 = json.dumps(c1.get_dict())
    output = io.StringIO()
    output.name = 'test'
    c1.output = output
    c1.run()
    output.seek(0)
    c2 = rp.parse_output(output)
    json2 = json.dumps(c2.get_dict())
    assert json1 == json2


def test_parsers__get_tags():
    data = '```env\na=b\n```\n```bash#test1\nls\n```\n\n```bash#test2\nls -al\n```'
    input = io.StringIO()
    input.write(data)
    input.seek(0)
    tags = rp.get_tags(input)
    assert len(tags) == 4
    for tag, num in tags:
        if tag == 'bash':
            assert num == 2
        elif tag in ['env', 'test1', 'test2']:
            assert num == 1
        else:
            assert tag == ''


def test_parsers__get_blocks():
    data = '```env\na=b\n```\n```bash#test1\nls\n```\n\n```bash#test2\nls -al\n```'
    input = io.StringIO()
    input.write(data)
    input.seek(0)
    got_blocks = rp.get_blocks(input, pretty=True)
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    got_blocks = ansi_escape.sub('', got_blocks)
    expect = '1. [bash] bash#test1\n=================\nls\n\n2. [bash] bash#test2\n=================\nls -al\n\n'
    assert got_blocks == expect


def test_parsers__get_blocks__json():
    data = '```env\na=b\n```\n```bash#test1\nls\n```\n\n```bash#test2\nls -al\n```'
    input = io.StringIO()
    input.write(data)
    input.seek(0)
    got_blocks = rp.get_blocks(input)
    input.seek(0)
    expect = rp.parse_doc(input)
    assert json.loads(got_blocks) == expect.get_dict()


def test_parsers__get_clean_doc():
    data = '```env\na=b\n```\nyes\n```bash#test1\nls\n```\n\n- Test ```bash:me\n\n```bash (\\/me^) {&}_[2=\']-$%!*:test2\nls -al\n```'
    expect = '```env\na=b\n```\nyes\n```bash\nls\n```\n\n- Test ```bash:me\n\n```bash (\\/me^) {&}_[2=\']-$%!*\nls -al\n```'
    input = io.StringIO()
    input.write(data)
    input.seek(0)
    assert rp.get_clean_doc(input) == expect


###
# Tests for __main__.py
###

def test_main_add_options():
    rm.add_options(rm._run_control_options)
    rm.add_options(rm._run_specific_options)
    rm.add_options(rm._output_style_options)
    rm.add_options(rm._tag_options)
