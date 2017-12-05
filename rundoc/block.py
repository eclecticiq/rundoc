"""
Contains class representation of executable code block.
"""
from prompt_toolkit import prompt
from prompt_toolkit.styles import style_from_pygments
from pygments import highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexers import get_lexer_by_name
import subprocess
import sys

class DocBlock(object):
    """Single multi-line code block executed as a script.

    Attributes:
        interpreter (str): Interpreter used to run the code.
        code (str): Base code loaded during initialization.
        process (subprocess.Popen): Process object running the interpreter.
        runs (list): List of dictinaries, each containing the following:
            'user_code': User modified version of the code (will be used
                instead of main code unless it's set to None or empty string).
            'stdout': Full output of executed code block.
            'retcode': exit code of the code block executed
    """
    def __init__(self, code, interpreter, darkbg=True):
        if darkbg:
            from pygments.styles.monokai import MonokaiStyle as HighlightStyle
            self.HighlightStyle = HighlightStyle
        else:
            from pygments.styles.manni import ManniStyle as HighlightStyle
            self.HighlightStyle = HighlightStyle
        self.interpreter = interpreter
        self.code = code
        self.process = None
        self.runs = []  # elements inside are like:
                        #   {
                        #       'user_code':'',
                        #       'stdout':'',
                        #       'retcode':None
                        #   }

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
            'runs': self.runs,
        }

    def prompt_user(self, prompt_text='» '):
        self.last_run['user_code'] = prompt(
            prompt_text,
            default = self.code,
            lexer = self.get_lexer_class(),
            style = style_from_pygments(self.HighlightStyle)
            )

    def print_stdout(self):
        assert self.process
        line = self.process.stdout.readline().decode('utf-8')
        self.last_run['stdout'] += line
        print(line, end='')

    def is_running(self):
        return self.process and self.process.poll() is None

    def run(self, prompt=True):
        if not self.process:
            self.runs.append(
                {
                    'user_code':'',
                    'stdout':'',
                    'retcode':None
                }
            )
            if prompt:
                self.prompt_user()
            else:
                self.last_run['user_code'] = self.code
            code = self.last_run['user_code'].strip()
            self.process = subprocess.Popen(
                [self.interpreter, '-c', code],
                stdout=subprocess.PIPE,
                stderr=sys.stdout.buffer,
                shell=False,
                )
        while self.is_running():
            self.print_stdout()
        self.last_run['retcode'] = self.process.poll()
        self.process = None

    def kill(self):
        if self.process:
             self.process.kill()


