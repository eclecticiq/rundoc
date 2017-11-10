"""
Main module for rundoc command line utility.
"""
from bs4 import BeautifulSoup
import argcomplete
import argparse
import json
import logging
import markdown
import re
import signal
import subprocess
import sys

class clr:
    ''' 
    ANSI colors for pretty output.
    '''
    RED = '\033[91m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

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
    def __init__(self, code, interpreter):
        self.interpreter = interpreter
        self.code = code
        self.user_code = ''
        self.process = None
        self.output = { 'stdout':'', 'retcode':None }

    def get_dict(self):
        return {
            'interpreter': self.interpreter,
            'code': self.code,
            'user_code': self.user_code,
            'output': self.output,
        }

    def print_stdout(self):
        assert self.process
        line = self.process.stdout.readline().decode('utf-8')
        self.output['stdout'] += line
        print(line, end='')

    def print_stderr(self):
        assert self.process
        line = self.process.stderr.readline()
        self.output['stderr'] += line
        print(line.decode('utf-8'), end='')

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


class DocCommander(object):
    """
    Manages DocCode objects and executes them in succession.
    """
    def __init__(self):
        self.doc_codes = []
        self.running = False
        self.failed = False
        self.current_doc_code = None
        signal.signal(signal.SIGINT, self.__signal_handler)

    def __signal_handler(self, signal, frame):
        """Handle keyboard interrupt."""
        logging.debug('KeyboardInterrupt received.')
        sys.stderr.write(
            "\nKeyboardInterrupt captured. Stopping rundoc gracefully.\n")
        if self.current_doc_code:
            self.current_doc_code.kill()
        else:
            sys.exit(1)

    def get_dict(self):
        return [ x.get_dict() for x in self.doc_codes ]

    def add(self, code, interpreter='bash'):
        if not interpreter:
            interpreter = 'bash'
        self.doc_codes.append(DocCode(code, interpreter))

    def ask_user(self, doc_code):
        doc_code.user_code= input(
            doc_code.code + '  '
            )

    def run(self, step=1, yes=False):
        """Run all the doc_codes one by one starting from `step`.

        Args:
            step (int): Number of step to start with. Defaults to 1. Steps
                start at 1.
            yes (bool): Auto-confirm all steps without user interaction.
                Defaults to False.

        Returns:
            JSON representation of commands and outputs.
        """
        logging.debug('Running DocCommander.')
        assert self.running == False
        assert self.failed == False
        self.running = True
        for doc_code in self.doc_codes[step-1:]:
            logging.debug("Beginning of step {}".format(step))
            print("\n{}═══╣ Step {} ({}){}".format(
                clr.BOLD,
                step,
                doc_code.interpreter,
                clr.END,
                )
            )
            if yes:
                print(doc_code.code, end='')
            else:
                self.ask_user(doc_code) # let user modify the code
            print("────")
            self.current_doc_code = doc_code
            self.current_doc_code.run() # run in blocking manner
            if doc_code.output['retcode'] == 0:
                logging.debug("Step {} finished.".format(step))
            else:
                self.failed = True
            if self.failed:
                self.running = False
                logging.error('Failed on step {}'.format(step))
                print("───┤ {}Failed at step {} with exit code '{}'{}\n".format(
                    clr.RED,
                    step,
                    doc_code.output['retcode'],
                    clr.END,
                    )
                )
                self.current_doc_code = None
                break
            self.current_doc_code = None
            print("───┤ {}done{}\n".format(clr.GREEN, clr.END))
            step += 1
        return json.dumps(self.get_dict(), sort_keys=True, indent=4)

def __parse_args():
    """Parse command line arguments and return an argparse object."""
    parser = argparse.ArgumentParser(
        prog = "rundoc",
        description="Run code from markdown code blocks in controlled manner",
        )
    parser.add_argument(
        "-v", "--version", action="store_true",
        help="Show version info and exit."
        )
    parser.add_argument(
        "-d", "--debug", action="store_true",
        help="Enable debug mode with output of each action in the log."
        )
    subparsers = parser.add_subparsers(
        description="(use each command with -h for more help)",
        dest="cmd",
        )

    parser_run = subparsers.add_parser(
        "run",
        description="Run markdown as a script."
        )
    parser_run.add_argument(
        "mkd_file_path", type=str, action="store",
        help="Markdown file path."
        )
    parser_run.add_argument(
        "-t", "--tags", action="store",
        help='''Coma-separated list of tags (e.g. -t
            bash,bash_proj-2,python3_proj2). Part of tag until first underscore
            will be used as selected interpreter for that code. If no tags are
            provided, all code blocks will be used. Untagged code blocks will
            use bash as default interpreter.'''
        )
    parser_run.add_argument(
        "-s", "--step", type=int, action="store",
        help="Start at step STEP. Defaults to 1."
        )
    parser_run.add_argument(
        "-o", "--output", type=str, action="store",
        help='''Output file. All codes, modifications and output of execution
            will be saved here. This file can be later used as an argument to
            'rerun' command which will execute all steps without any user
            interaction.'''
        )
    parser_run.add_argument(
        "-y", "--yes", action="store_true",
        help="Confirm all steps with no user interaction."
        )
    parser_run.set_defaults(
        tags="",
        step=1,
        output=None,
        )

    parser_rerun = subparsers.add_parser(
        "rerun",
        description="Run codes saved as json output by 'run' command."
        )
    parser_rerun.add_argument(
        "saved_output_path", type=str, action="store",
        help="Path of saved output file from 'run' or 'rerun' command."
        )
    parser_rerun.add_argument(
        "-s", "--step", type=int, action="store",
        help="Start at step STEP. Defaults to 1."
        )
    parser_rerun.add_argument(
        "-o", "--output", type=str, action="store",
        help='''Output file. All codes, modifications and output of execution
            will be saved here. This file can be later used as an input
            argument to 'rerun' command.'''
        )
    parser_rerun.set_defaults(
        step=1,
        output=None,
        )

    argcomplete.autocomplete(parser)
    return parser.parse_args()

def parse_doc(mkd_file_path, tags=""):
    """Parse code blocks from markdown file and return DocCommander object.

    Args:
        mkd_file_path (str): Path to markdown file.
        code_tag (str): Code highlight specifier in markdown. We can use this
            to filter only certain code blocks. If it's set to empty string or
            None, all code blocks will be used. Defaults to "bash".

    Returns:
        DocCommander object.
    """
    mkd_data = ""
    with open(mkd_file_path, 'r') as f:
        mkd_data = f.read()
    html_data = markdown.markdown(
        mkd_data,
        extensions=['toc', 'tables', 'footnotes', 'fenced_code']
        )
    soup = BeautifulSoup(html_data, 'html.parser')
    # collect all elements with selected tags as classes
    classes = re.compile(
        "^({})$".format('|'.join(tags.split(','))) if tags else '.*'
        )
    code_block_elements = soup.findAll('code', attrs={"class":classes,})
    commander = DocCommander()
    for element in code_block_elements:
        class_name = element.get_attribute_list('class')[0]
        interpreter = None
        if class_name:
            interpreter = class_name.split("_")[0]
        commander.add(
            element.getText(),
            interpreter
        )
    return commander

def parse_output(output_file_path):
    """Load json output, create and return DocCommander object.

    Args:
        output_file_path (str): Path to saved output file.

    Returns:
        DocCommander object.
    """
    output_data = None
    with open(output_file_path, 'r') as f:
        output_data = f.read()
    data = json.loads(output_data)
    commander = DocCommander()
    for d in data:
        doc_code = DocCode(d['code'], d['interpreter'])
        doc_code.user_command = d['user_code']
        commander.doc_codes.append(doc_code)
    return commander


def main():
    args = __parse_args()
    logging.basicConfig(
        format = '%(asctime)s.%(msecs)03d, %(levelname)s: %(message)s',
        datefmt = '%Y-%m-%d %H:%M:%S',
        filename = None,
        level = logging.DEBUG if args.debug else logging.CRITICAL,
        )
    if args.version:
        print("rundoc {} - Copyright {} {} <{}>".format(
            rundoc.__version__,
            rundoc.__year__,
            rundoc.__author__,
            rundoc.__author_email__,
            ))
        sys.exit(0)
    output = ""
    if args.cmd == 'run':
        commander = parse_doc(args.mkd_file_path, tags=args.tags)
        output = commander.run(step=args.step, yes=args.yes)
    if args.cmd == 'rerun':
        commander = parse_output(args.saved_output_path)
        output = commander.run(step=args.step, yes=True)
    if args.cmd in ('rerun', 'run') and args.output:
        with open(args.output, 'w+') as f:
            f.write(output)

if __name__ == '__main__':
    main()

