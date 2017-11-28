"""
Contains class representation of executable code block.
"""
from prompt_toolkit import prompt
from prompt_toolkit.styles import style_from_pygments
from pygments import highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexers import get_lexer_by_name
import logging
import subprocess
import sys

class DocCode(object):
    """Single multi-line code block executed as a script.

    Attributes:
        interpreter (str): Interpreter used to run the code.
        code (str): Base code loaded during initialization.
        user_code (str): User modified version of the code (will be used
            instead if is not None or empty string).
        process (subprocess.Popen): Process object running the interpreter.
        output (dict): Dictinary containing 'stdout' and 'retcode'.
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
        self.user_code = ''
        self.process = None
        self.output = { 'stdout':'', 'retcode':None }

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
        code = self.user_code.strip() or self.code
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
            'user_code': self.user_code,
            'output': self.output,
        }

    def prompt_user(self, prompt_text='» '):
        self.user_code = prompt(
            prompt_text,
            default = self.code,
            lexer = self.get_lexer_class(),
            style = style_from_pygments(self.HighlightStyle)
            )

    def print_stdout(self):
        assert self.process
        line = self.process.stdout.readline().decode('utf-8')
        self.output['stdout'] += line
        print(line, end='')

    def is_running(self):
        return self.process and self.process.poll() is None

    def run(self):
        if not self.process:
            code = self.user_code.strip() or self.code
            logging.debug('Running code {}'.format(code))
            self.process = subprocess.Popen(
                [self.interpreter, '-c', code],
                stdout=subprocess.PIPE,
                stderr=sys.stdout.buffer,
                shell=False,
                )
        while self.is_running():
            self.print_stdout()
        self.output['retcode'] = self.process.poll()

    def kill(self):
        if self.process:
             self.process.kill()


