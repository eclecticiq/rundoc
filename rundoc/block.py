"""
Contains class representation of executable code block.
"""
from collections import OrderedDict
from prompt_toolkit import prompt
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import style_from_pygments_cls
from pygments import highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexers import get_lexer_by_name
from rundoc import BadEnv, CodeFailed, BadInterpreter
import grp
import logging
import os
import pwd
import re
import select
import subprocess
import sys
import time

block_actions = OrderedDict()
def block_action(f):
    """Decorator: Add function as action item in block_actions.

    Function needs to accept exactly 2 arguments:
        args      - List of arguments which is a ':' split of a tag without the
                    first element. First element is used as name of action.
        contents  - Data from the code block.
    """
    block_actions.setdefault(
        f.__name__.replace("_", "-").strip('-'), f)
    return f

def fill_env_placeholders(s):
    "Replace %:VARIABLE:% with value of VARIABLE in os.environ."
    variables = re.findall("(%:[A-Za-z_][A-Za-z0-9_]*:%)", s)
    variables = list(set(map(lambda x: x[2:-2], variables)))
    res = s
    for variable in variables:
        res = res.replace("%:"+variable+":%", os.environ.get(variable) or "")
    return res

def _write_file_action(args, contents, mode='a', fill=False):
    "Helper function used by 'create-file' and 'append-file' actions."
    filename    = os.path.expanduser(args.get(0))
    permissions = args.get(1)
    user        = args.get(2)
    group       = args.get(3)
    uid = None
    gid = None
    if user: # pragma: no cover
        uid = pwd.getpwnam(user).pw_uid
    else:
        uid = os.geteuid()
    if group: # pragma: no cover
        gid = grp.getgrnam(group).gr_gid
    else:
        if user: # pragma: no cover
            gid = pwd.getpwuid(uid).pw_gid
        else:
            gid = os.getegid()
    if permissions:
        permissions = int(permissions, 8)
    else:
        permissions = 0o644
    with open(filename, mode) as fh:
        fh.write((fill_env_placeholders(contents) if fill else contents)+"\n")
    os.chmod(filename, permissions)
    os.chown(filename, uid, gid)
    return 0

@block_action
def _create_file(args, contents):
    """create-file:NAME[:OCTAL_PERMISSIONS[:USERNAME[:GROUP]]]
    Create file on path NAME with OCTAL_PERMISSIONS owned by USERNAME:GROUP and
    fill with contents of a code block.
    Example:
        ```create-file:~/.config/test.cfg:640#tag1#tag2
        example = True
        ```
    """
    return _write_file_action(args, contents, 'w+')

@block_action
def _r_create_file(args, contents):
    """r-create-file:NAME[:OCTAL_PERMISSIONS[:USERNAME[:GROUP]]]
    Same as 'create-file' but also replace %:VAR:% placeholders with env vars.
    Example:
        ```env
        example_value=True
        ```
        ```r-create-file:~/.config/test.cfg:640#tag1#tag2
        example = %:example_value:%
        ```
    """
    return _write_file_action(args, contents, 'w+', True)

@block_action
def _append_file(args, contents):
    """append-file:PATH/NAME[:OCTAL_PERMISSIONS[:USERNAME[:GROUP]]]
    Edit file on path NAME, set OCTAL_PERMISSIONS and chown to USERNAME:GROUP
    and paste contents of a code block at the end of the file.
    Example:
        ```append-file:~/.config/test.cfg:640#tag1#tag2
        port = 9200
        ```
    """
    return _write_file_action(args, contents, 'a+')

@block_action
def _r_append_file(args, contents):
    """r-append-file:PATH/NAME[:OCTAL_PERMISSIONS[:USERNAME[:GROUP]]]
    Same as 'append-file' but also replace %:VAR:% placeholders with env vars.
    Note that only code block contents will be replaced. Existing part of file
    will not be changed.
    Example:
        ```env
        port_number=9200
        ```
        ```r-append-file:~/.config/test.cfg:640#tag1#tag2
        port = %:port_number:%
        ```
    """
    return _write_file_action(args, contents, 'a+', True)

@block_action
def _usage(args, contents): # pragma: no cover
    """usage
    Print code block contents and exit. Used to print usage help if no tags are
    provided.
    Example:
        ```usage
        To setup the product run:
            rundoc run README.md -t setup
        To upgrade the product run:
            rundoc run README.md -t upgrade
        ```
    """
    sys.exit(0)

def get_block_action(tag):
    "Return an action function based on code block tag."
    parts_list = list(filter(bool, tag.split(':')))
    action_name = parts_list.pop(0)
    if action_name not in block_actions:
        return None
    action_args = dict([i, parts_list[i]] for i in range(0, len(parts_list)))
    return lambda contents: block_actions[action_name](action_args, contents)

class DocBlock(object):
    """Single multi-line code block executed as a script.

    Attributes:
        interpreter (str): Interpreter used to run the code.
        code (str): Base code loaded during initialization.
        process (subprocess.Popen): Process object running the interpreter.
        runs (list): List of dictinaries, each containing the following:
            'user_code': User modified version of the code (will be used
                instead of main code unless it's set to None or empty string).
            'output': Full output of executed code block.
            'retcode': exit code of the code block executed
    """
    def __init__(self, code, tags, light=False):
        if light:
            from pygments.styles.manni import ManniStyle as HighlightStyle
            self.HighlightStyle = HighlightStyle
        else:
            from pygments.styles.native import NativeStyle as HighlightStyle
            self.HighlightStyle = HighlightStyle
        interpreter = tags[0]
        self.interpreter = interpreter
        self.code = code
        self.tags = tags
        self.process = None
        self.runs = []  # elements inside are like:
                        #   {
                        #       'user_code':'',
                        #       'output':'',
                        #       'retcode':None,
                        #       'time_start': None,
                        #       'time_stop': None
                        #   }
        self.is_action = interpreter.split(':')[0] in block_actions
        interpreter_exists = subprocess.call(
                ['bash','-c','command -v {} 2>&1>/dev/null'.format(interpreter)]
            ) == 0
        if not self.is_action and not interpreter_exists:
            raise BadInterpreter("Bad interpreter: '{}'".format(interpreter))

    @property
    def last_run(self):
        if len(self.runs):
            return self.runs[-1]
        else:
            return None

    def get_lexer(self):
        try:
            # try because lexer may not exist for current interpreter
            return get_lexer_by_name(self.interpreter)
        except:
            # no lexer
            return None

    def __str__(self):
        code = ''
        if self.last_run:
            code = self.last_run['user_code'].strip()
        else:
            code = self.code
        if self.get_lexer():
            return highlight(
                code,
                self.get_lexer(),
                Terminal256Formatter(style=self.HighlightStyle)
                )
        return code # pragma: no cover

    def get_dict(self):
        return {
            'interpreter': self.interpreter,
            'code': self.code,
            'tags': self.tags,
            'runs': self.runs,
        }

    def prompt_user(self, prompt_text='» '): # pragma: no cover
        lexer = self.get_lexer()
        pygments_lexer = PygmentsLexer(lexer.__class__) if lexer else None
        # ^^ we have to wrap lexer in PygmentsLexer of prompt toolkit
        self.last_run['user_code'] = prompt(
            prompt_text,
            default = self.code,
            lexer = pygments_lexer,
            style = style_from_pygments_cls(self.HighlightStyle),
            )

    def print_output(self, final=False):
        """Read both stdout and stderr, populate them in the variable and print.

        Args:
            final (bool): Used to collect final bytes after the process exists.
        """
        encoding = sys.stdout.encoding
        if final and self.process: # ask for process because might be an action
            line = self.process.stdout.read().decode(encoding)
            self.last_run['output'] += line
            sys.stdout.write(line)
        else:
            assert self.process
            chunk = self.process.stdout.read(1).decode(encoding)
            self.last_run['output'] += chunk
            sys.stdout.write(chunk)

    def run(self, prompt=True):
        if not self.process:
            self.runs.append(
                {
                    'user_code': '',
                    'output': '',
                    'retcode': None,
                    'time_start': None,
                    'time_stop': None,
                }
            )
            if prompt: # pragma: no cover
                self.prompt_user()
            else:
                self.last_run['user_code'] = self.code
            code = self.last_run['user_code'].strip()
            self.last_run['time_start'] = time.time()
            if self.is_action:
                action = get_block_action(self.interpreter)
                self.last_run['retcode'] = action(code)
                self.last_run['time_stop'] = time.time()
                self.process = None
                return
            else:
                self.process = subprocess.Popen(
                    [self.interpreter],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    shell=False,
                    )
                self.process.stdin.write(code.encode())
                self.process.stdin.flush()
                self.process.stdin.close()
        while self.process and self.process.poll() is None:
            self.print_output()
        self.print_output(final=True)
        self.last_run['time_stop'] = time.time()
        self.last_run['retcode'] = self.process.poll()
        self.process = None

    def kill(self):
        if self.process:
             self.process.kill()


