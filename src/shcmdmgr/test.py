import unittest
import os.path
import sys
from contextlib import contextmanager
from io import StringIO

from shcmdmgr import complete, filemanip, config, cio, util, parser, __main__
from shcmdmgr.complete import Complete

# https://stackoverflow.com/a/17981937/3791757
@contextmanager
def captured_output():
    '''
    Captures stdout and stderr for testing, and allows assert on it later.

    with captured_output() as (out, err):
        print('test')
    output = out.getvalue().strip()
    '''
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class TestCompletion(unittest.TestCase):
    def test_complete_initialization(self):
        com = Complete('last')
        self.assertTrue(com)

    def test_complete_return_nothing(self):
        com = Complete('last')
        self.assertEqual(com.nothing(), config.SUCCESSFULL_EXECUTION)

    def test_complete_return_words(self):
        com = Complete('last')
        com.add_words(['last-a', 'random', 'last-b'])
        com.add_words(['lastly', 'least', 'qq-last'])
        self.assertEqual(com.words, ['last-a', 'last-b', 'lastly'])

    def test_completion_location(self):
        self.assertTrue(complete.completion_setup_script_path('bash').endswith('bash'))
        self.assertTrue(complete.completion_setup_script_path('zsh').endswith('zsh'))

class TestFilemanip(unittest.TestCase):
    def test_load(self):
        filemanip.load_json_file(os.path.join('test', 'cmds.json'))

    def test_load_err(self):
        try:
            filemanip.load_json_file(os.path.join('test', 'nonexistant.json'))
        except FileNotFoundError:
            return
        self.assertFalse('should reach this')

    def test_save(self):
        res = filemanip.load_json_file(os.path.join('test', 'cmds.json'))
        filemanip.save_json_file(res, os.path.join('test', 'tmp.json'))

    def test_compelx(self):
        res = filemanip.load_json_file(os.path.join('test', 'cmds.json'))
        filemanip.save_json_file(res, os.path.join('test', 'tmp.json'))
        self.assertEqual(res, filemanip.load_json_file(os.path.join('test', 'tmp.json')))

class TestConfig(unittest.TestCase):
    def test_configuration(self):
        config.get_conf()

    def test_logger(self):
        config.get_logger()

    def test_logger_levels(self):
        log = config.get_logger()
        log.setLevel(config.QUIET_LEVEL) # todo, actually test them
        log.debug('test')
        log.verbose('test')
        log.info('test')
        log.critical('test')
        log.error('test')

class TestUtil(unittest.TestCase):
    def test_terminal(self):
        (width, height) = util.get_terminal_dimensions()
        self.assertIs(type(width), int)
        self.assertIs(type(height), int)

def main_setup(arguments):
    sys.argv = ['program'] + arguments
    conf = config.get_conf()
    logger = config.get_logger()
    form = cio.Formatter(logger)
    pars = parser.Parser(arguments, form, logger)
    return (conf, logger, form, pars)

def make_parser(arguments):
    (_, _, _, pars) = main_setup(arguments)
    return pars

class TestParser(unittest.TestCase):
    def test_init(self):
        pars = make_parser([])

    def test_test(self):
        with captured_output() as (out, err):
            pars = make_parser([])
        output = out.getvalue().strip()
        print(output)

def make_app(arguments):
    (conf, logger, form, pars) = main_setup(arguments)
    return __main__.App(conf, logger, form, pars, None)

class TestMainGeneral(unittest.TestCase):
    def test_main_no_param(self):
        make_app([]).main_command()

    def test_main_version(self):
        make_app(['--version']).main_command()

    def test_main_completion(self):
        make_app(['--complete', '']).main_command()
        make_app(['--complete', '--version', '']).main_command()

    def test_main_help(self):
        make_app(['--help']).main_command()
        make_app(['--h']).main_command()

    def test_main_output_settings(self):
        make_app(['--quiet']).main_command()
        make_app(['--verbose']).main_command()
        make_app(['--debug']).main_command()


if __name__ == '__main__':
    unittest.main()
