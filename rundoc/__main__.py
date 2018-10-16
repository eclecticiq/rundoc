"""
Main module for rundoc command line utility.
"""
from rundoc import parsers, ansi
from textwrap import dedent
import click
import logging
import rundoc
import sys

logger = logging.getLogger(__name__)

def add_options(options:list):
    "Aggregate click options from a list and pass as single decorator."
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func
    return _add_options

_run_control_options = [
    click.option('-s', '--step', default=1, show_default=True,
        help="Step number to start at (greater than 0)."
    ),
    click.option('-p', '--pause', default=0.0, show_default=True,
        help="Number of seconds to pause before each code block."
    ),
    click.option('-r', '--retry', default=0, show_default=True,
        help="Number of retries for failed code blocks."
    ),
    click.option('-P', '--retry-pause', default=1.0, show_default=True,
        help=dedent(
        """Seconds to pause before retriyng failed code block. Actual pause
        will be max value of '--pause' and '--retry-pause'.""")
    ),
    click.option('-o', '--output', type=click.File('w'),
        help=dedent(
        """Output file. All codes, modifications and output of execution will
        be saved here. This file can be later used as an input argument to
        'replay' command.""")
    ),
    click.option('-y', '--yes', is_flag=True,
        help=dedent("""[Deprecated: this is now default behaviour. See '-a' to
        disable] Confirm all steps without prompting user.""")
    ),
    click.option('-a', '--ask', count=True,
        help=dedent("""Let rundoc ask you for input on variables and/or code.
        No option: ask for missing vars.
        -a: ask for all vars.
        -aa: ask for all vars and modify code on failure.
        -aaa: ask for all vars and code."""),
    ),
    click.option('-b', '--breakpoint', type=int, multiple=True,
        help=dedent("""Step number on which to force prompt for code input. You can
        use this option multiple times to add multiple breakpoints."""),
    ),
]

_run_specific_options = [
    click.option('-i', '--inherit-env', is_flag=True,
        help=dedent(
        """Override default env variable values with values from existing
        environment. Useful when you export variables before running rundoc and
        expect them to override default values that are set in the docs.""")
    ),
    click.option('-j', '--single-session', type=str, default='',
    help=dedent(
    """Run all blocks in a single interpreter session. By default, each block
    is run in seperate session, rendering definitions from previous ones lost.
    Specify the interpreter (only one) after this option.""")
    ),
]

_output_style_options = [
    click.option('--light', is_flag=True,
        help="Use theme for light terminal background."
    ),
]

_tag_options = [
    click.option('-t', '--tags', type=str, default='',
        help=dedent(
        """Hash (#) separated list of tags, e.g. '-t bash#proj-2#test_3'.
        Filter out all code blocks that don't contain at least one of the
        listed tags. (Works like OR logic).""")
    ),
    click.option('-T', '--must-have-tags', type=str, default='',
        help=dedent(
        """Hash (#) separated list of tags, e.g. '-t bash#proj-2#test_3)'.
        Filter out all code blocks that are missing at least one of the listed
        tags. (Works like AND logic).""")
    ),
    click.option('-N', '--must-not-have-tags', type=str, default='',
        help=dedent(
        """Hash (#) separated list of tags, e.g. '-t bash#proj-2#test_3)'.
        Filter out all code blocks that contain at least one of the listed
        tags. (Works like AND NOT logic).""")
    ),
]


@click.group()
@click.version_option(version=rundoc.__version__,
    message="%(prog)s %(version)s - {}".format(rundoc.__copyright__))
@click.option('-d', '--debug', is_flag=True,
    help="Enable debug mode with output of each action in the log.")
@click.pass_context
def cli(ctx, **kwargs):
    logging.basicConfig(
        format = '%(asctime)s.%(msecs)03d, %(levelname)s: %(message)s',
        datefmt = '%Y-%m-%d %H:%M:%S',
        filename = None,
        level = logging.DEBUG if ctx.params.get('debug') else logging.WARNING,
        )

@cli.command()
@add_options(_run_control_options)
@add_options(_output_style_options)
@add_options(_tag_options)
@add_options(_run_specific_options)
@click.argument('input', type=click.File('r'))
def run(**kwargs):
    "Run code from markdown file."
    if kwargs['yes']: print("{}Deprecated option: -y, --yes. See -a, --ask instead.{}".format(ansi.yellow, ansi.end))
    try:
        commander = parsers.parse_doc(**kwargs)
    except rundoc.BadEnv as e:
        print("{}{}{}".format(ansi.red, e, ansi.end))
        sys.exit(1)
    try:
        commander.run(**kwargs)
    except KeyboardInterrupt:
        commander.die_with_grace()
        sys.exit(1)
    except rundoc.BadEnv as e:
        print("{}{}{}".format(ansi.red, e, ansi.end))
        sys.exit(1)
    except rundoc.CodeFailed as e:
        sys.exit(1)

@cli.command()
@add_options(_run_control_options)
@add_options(_output_style_options)
@click.argument('input', type=click.File('r'))
def replay(**kwargs):
    "Run code from the output of 'run' command."
    if kwargs['yes']: print("{}Deprecated option: -y, --yes. See -a, --ask instead.{}".format(ansi.yellow, ansi.end))
    try:
        commander = parsers.parse_output(**kwargs)
    except Exception as e:
        logger.error('Failed to parse file: {}'.format(e))
        sys.exit(1)
    try:
        commander.run(**kwargs)
    except KeyboardInterrupt:
        commander.die_with_grace()
        sys.exit(1)
    except rundoc.BadEnv as e:
        print("{}{}{}".format(ansi.red, e, ansi.end))
        sys.exit(1)
    except rundoc.CodeFailed as e:
        sys.exit(1)


@cli.command(name='list-tags')
@click.argument('input', type=click.File('r'))
def list_tags(**kwargs):
    "List all unique tags in the markdown file."
    try:
        tags = parsers.get_tags(**kwargs)
        max_num_len = len(str(tags[0][0]))
        for key, value in tags:
            print("{}{}{}".format(
                value, ' '*(max_num_len - len(str(value))), key))
    except Exception as e:
        logger.error('Failed to parse file: {}'.format(e))
        sys.exit(1)

@cli.command(name='action-tags')
def special_tags(**kwargs):
    "Show available action tags and their use in markdown."
    block_actions = rundoc.block.block_actions
    action_tags_info = ""
    for key in block_actions.keys():
        action_tags_info += "\n" + block_actions[key].__doc__
    print(action_tags_info)
    sys.exit(0)

@cli.command(name='list-blocks')
@add_options(_tag_options)
@add_options(_output_style_options)
@click.option('--pretty', is_flag=True, help="Human readable terminal output.")
@click.argument('input', type=click.File('r'))
def list_blocks(**kwargs):
    "List all blocks that would be executed with selected tags and parameters."
    try:
        parsers.print_blocks(**kwargs)
    except Exception as e:
        logger.error('Failed to parse file: {}'.format(e))
        sys.exit(1)

@cli.command(name='clean-doc')
@click.argument('input', type=click.File('r'))
def clean_doc(**kwargs):
    "Read markdown file, strip any rundoc specific markup and send to stdout."
    try:
        parsers.print_clean_doc(**kwargs)
    except Exception as e:
        logger.error('Failed to parse file: {}'.format(e))
        sys.exit(1)

if __name__ == '__main__':
    cli()

