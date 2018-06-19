"""
Contains class representation of executable code block.
"""
from prompt_toolkit import prompt
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import style_from_pygments_cls
from pygments import highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexers import get_lexer_by_name
from rundoc import BadEnv, CodeFailed, BadInterpreter
import logging
import os
import select
import subprocess
import sys
import time

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
    def __init__(self, code, interpreter, darkbg=True, tags=""):
        if darkbg:
            from pygments.styles.native import NativeStyle as HighlightStyle
            self.HighlightStyle = HighlightStyle
        else:
            from pygments.styles.manni import ManniStyle as HighlightStyle
            self.HighlightStyle = HighlightStyle
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
        interpreter_exists = subprocess.call(
            ['bash', '-c', 'command -v {} 2>&1>/dev/null'.format(interpreter)])
        if interpreter_exists != 0:
            raise BadInterpreter("Bad interpreter: '{}'".format(interpreter))

    @property
    def last_run(self):
        if len(self.runs):
            return self.runs[-1]
        else:
            return None

    def get_lexer_class(self):
        lexer_class = None
        try:
            # try because lexer may not exist for current interpreter
            return get_lexer_by_name(self.interpreter).__class__
        except:
            # no lexer, return plain text
            return None

    def __str__(self):
        lexer_class = self.get_lexer_class()
        code = ''
        if self.last_run:
            code = self.last_run['user_code'].strip()
        else:
            code = self.code
        if lexer_class:
            return highlight(
                code,
                lexer_class(),
                Terminal256Formatter(style=self.HighlightStyle)
                )
        return code

    def get_dict(self):
        return {
            'interpreter': self.interpreter,
            'code': self.code,
            'tags': self.tags,
            'runs': self.runs,
        }

    def prompt_user(self, prompt_text='» '):
        self.last_run['user_code'] = prompt(
            prompt_text,
            default = self.code,
            lexer = PygmentsLexer(self.get_lexer_class()),
            style = style_from_pygments_cls(self.HighlightStyle)
            )

    def print_output(self, final=False):
        """Read both stdout and stderr, populate them in the variable and print.

        Args:
            final (bool): Used to collect final bytes after the process exists.
        """
        encoding = sys.stdout.encoding
        if final:
            line = self.process.stderr.read().decode(encoding)
            self.last_run['output'] += line
            sys.stderr.write(line)
            line = self.process.stdout.read().decode(encoding)
            self.last_run['output'] += line
            sys.stdout.write(line)
        else:
            assert self.process
            reads = [self.process.stdout.fileno(), self.process.stderr.fileno()]
            ret = select.select(reads, [], [])
            line = ""
            for fd in ret[0]:
                if fd == self.process.stderr.fileno():
                    line = self.process.stderr.readline().decode(encoding)
                    self.last_run['output'] += line
                    sys.stderr.write(line)
                if fd == self.process.stdout.fileno():
                    line = self.process.stdout.readline().decode(encoding)
                    self.last_run['output'] += line
                    sys.stdout.write(line)
            return len(line) > 0

    def is_running(self):
        return self.process and self.process.poll() is None

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
            if prompt:
                self.prompt_user()
            else:
                self.last_run['user_code'] = self.code
            code = self.last_run['user_code'].strip()
            self.last_run['time_start'] = time.time()
            self.process = subprocess.Popen(
                [self.interpreter, '-c', code],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                )
        while self.is_running():
            self.print_output()
        self.print_output(final=True)
        self.last_run['time_stop'] = time.time()
        self.last_run['retcode'] = self.process.poll()
        self.process = None

    def kill(self):
        if self.process:
             self.process.kill()


