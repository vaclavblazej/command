#!/usr/bin/env python3
# ================================================================================
#
#    shell-command-manager
#    Tool for managing custom commands from a central location
#    Copyright (C) 2020-2021  Václav Blažej
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ================================================================================

import datetime
import os
import shlex
import subprocess
import sys
from os.path import join, exists
from string import Template

from shcmdmgr import config, filemanip, project, complete, cio
from shcmdmgr.args import Argument, CommandArgument, ArgumentGroup
from shcmdmgr.command import Command, load_commands
from shcmdmgr.parser import Parser
from shcmdmgr.project import Project

WORKING_DIRECTORY = os.getcwd()
DEFAULT_COMMAND_WAS_INJECTED = False

# == Main Logic ==================================================================

def main():
    ''' Do the basic setup so the program runs correctly and invoke the desired command '''
    logger = None
    try:
        (app, pars, conf, proj, logger) = setup()
        pars.shift() # skip the program invocation
        pars.load_all([app.argument_groups['OUTPUT_ARGUMENTS']])
        logger.setLevel(conf['logging_level'])
        logger.debug('Configuration: %s', str(conf))
        logger.debug('Script folder: %s', cio.quote(config.SCRIPT_PATH))
        logger.debug('Working directory: %s', cio.quote(WORKING_DIRECTORY))
        logger.debug('Arguments: %s', str(sys.argv))
        if proj: os.environ[config.PROJECT_ROOT_VAR] = proj.directory
        pars.load_all([app.argument_groups['OPTIONAL_ARGUMENTS']])
        if conf['scope'] == config.AUTOMATIC_SCOPE:
            if proj: conf['scope'] = config.PROJECT_SCOPE
            else: conf['scope'] = config.GLOBAL_SCOPE
        if conf['scope'] == config.PROJECT_SCOPE and not proj:
            logger.critical('Scope is set to "project", however no project is present. To create a project in the current folder run the "--init" command.')
            return config.USER_ERROR
        return app.main_command()
    except KeyboardInterrupt:
        if logger: logger.critical('Manually interrupted!')

def setup():
    ''' Create instances necessary for runtime '''
    logger = config.get_logger()
    form = cio.Formatter(logger)
    pars = Parser(sys.argv, form, logger)
    conf = config.get_conf()
    proj = Project.retrieve_project_if_present(WORKING_DIRECTORY, form)
    app = App(conf, logger, form, pars, proj)
    return (app, pars, conf, proj, logger)

class App:
    def __init__(self, conf, logger, form, pars, proj):
        self.conf = conf
        self.logger = logger
        self.form = form
        self.parser = pars
        self.project = proj
        self.argument_groups_cache = None

    def main_command(self):
        ''' Either perform the command if available or invoke the default command '''
        current_command = self.parser.peek()
        self.logger.debug('Current command {}'.format(current_command))
        if current_command:
            return self.execute_command(current_command)
        elif not self.parser.help:
            return self.invoke_default_command()

    def invoke_default_command(self):
        ''' Push the default command into arguments and run the whole command again '''
        default_command = self.conf['default_command']
        if default_command:
            new_args = shlex.split(default_command)
            if len(new_args) != 0:
                global DEFAULT_COMMAND_WAS_INJECTED
                if DEFAULT_COMMAND_WAS_INJECTED:
                    self.logger.warning('The default command is invalid, it must include a command argument')
                    return config.USER_ERROR
                DEFAULT_COMMAND_WAS_INJECTED = True
                self.logger.debug('Applying defalt arguments %s', new_args)
                sys.argv += new_args
                return main()
        self.logger.warning('No command given')
        return config.USER_ERROR

    def execute_command(self, current_command):
        ''' The main execution is issued from here '''
        if not self.parser.may_have(self.all_commands()):
            self.logger.warning('The argument/command %s was not found', cio.quote(current_command))
            self.logger.info('run "cmd --help" if you are having trouble')
            return config.USER_ERROR
        return config.SUCCESSFULL_EXECUTION

    def all_commands(self):
        return [
            self.argument_groups['PROJECT_COMMANDS'],
            self.argument_groups['CUSTOM_COMMANDS'],
            self.argument_groups['CMD_COMMANDS']
        ]

    # == Formatting ==================================================================

    def print_general_help(self):
        help_str = ''
        help_str += 'usage: cmd [-q|-v|-d] [-g|-p] <command> [<args>]\n'
        help_str += '\n'
        help_str += 'Manage custom commands from a central location\n'
        self.form.print_str(help_str)
        main_groups = [
            self.argument_groups['PROJECT_COMMANDS'],
            self.argument_groups['CUSTOM_COMMANDS'],
            self.argument_groups['CMD_SHOWN_COMMANDS'],
            self.argument_groups['OPTIONAL_ARGUMENTS'],
        ]
        self.form.print_str(ArgumentGroup.to_str(main_groups), end='')
        self.form.print_str()
        additional_str = 'Run "cmd --help <command>" to get help for a specific command'
        self.form.print_str(additional_str)
        return config.SUCCESSFULL_EXECUTION

    # == Commands ====================================================================

    def cmd_help(self):
        self.parser.enable_help()
        self.parser.remove_first_argument()
        if self.parser.peek() == None:
            self.print_general_help()
        return self.main_command()

    def cmd_version(self):
        self.parser.expect_nothing('prints out the version of shell command manager in formatting: "cmd version <ver>" where <ver> is in format 1.0.0[-devX]')
        self.form.print_str('cmd version ' + config.VERSION)
        return config.SUCCESSFULL_EXECUTION

    def cmd_initialize(self):
        self.parser.expect_nothing()
        new_file = join(WORKING_DIRECTORY, config.PROJECT_COMMANDS_FILE_LOCATION)
        if not exists(new_file):
            os.mkdir(os.path.dirname(new_file))
            # filemanip.save_json_file([], new_file)
        else:
            self.logger.error('The project is already initialized in direcotry {}'.format(WORKING_DIRECTORY))
        return config.SUCCESSFULL_EXECUTION

    def cmd_save(self):
        properties = {
                'alias': None,
                'description': None,
                'args': None,
        }
        other_args = [
            Argument('--alias', '-a', lambda: set_function(properties, 'alias', self.parser.shift()), 'one word shortcut used to invoke the command'),
            Argument('--descr', '-d', lambda: set_function(properties, 'description', self.parser.shift()), 'few words about the command\'s functionality'),
            Argument('--', None, lambda: set_function(properties, 'args', self.parser.get_rest()), 'command to be saved follows'),
        ]
        self.parser.load_all([ArgumentGroup('save arguments (missing will be queried)', other_args)])
        if not properties['args']: properties['args'] = self.form.input_str('Command: ')
        show_edit = False
        if len(properties['args']) == 0: # supply the last command from history
            history_file_location = join(os.environ['HOME'], self.conf['history_home'])
            history_command_in_binary = subprocess.check_output(['tail', '-1', history_file_location])
            history_command = history_command_in_binary[:-1].decode("utf-8")
            properties['args'] = shlex.split(history_command)
            show_edit = True
        if len(properties['args']) != 0 and exists(properties['args'][0]): # substitute relative file path for absolute
            if self.conf['scope'] == config.PROJECT_SCOPE:
                path_from_project_root = os.path.relpath(join(WORKING_DIRECTORY, properties['args'][0]), self.project.directory)
                properties['args'][0] = '${}/{}'.format(config.PROJECT_ROOT_VAR, path_from_project_root)
            if self.conf['scope'] == config.GLOBAL_SCOPE:
                properties['args'][0] = os.path.realpath(join(WORKING_DIRECTORY, properties['args'][0]))
            show_edit = True
        command_to_save = properties['args']
        if show_edit:
            command_to_save = self.form.input_str('The command to be saved: ', prefill=command_to_save)
        else:
            self.form.print_str('Saving command: ' + command_to_save)
        commands_file_location = self.get_context_command_file_location()
        if not exists(commands_file_location):
            filemanip.save_json_file([], commands_file_location)
        if not properties['alias']: properties['alias'] = self.form.input_str('Alias: ')
        if not properties['description']: properties['description'] = self.form.input_str('Short description: ')
        commands_db = load_commands(commands_file_location)
        creation_time = str(datetime.datetime.now().strftime(self.conf['time_format']))
        commands_db.append(Command(command_to_save, properties['description'], properties['alias'], creation_time))
        filemanip.save_json_file(commands_db, commands_file_location)
        return config.SUCCESSFULL_EXECUTION

    def get_context_command_file_location(self) -> str:
        if self.conf['scope'] == config.PROJECT_SCOPE and project: return self.project.commands_file
        if self.conf['scope'] == config.GLOBAL_SCOPE: return config.GLOBAL_COMMANDS_FILE_LOCATION
        return None

    def cmd_edit(self):
        self.parser.expect_nothing('opens the file containing all saved command metadata in editor determined by the exported shell variable "$EDITOR"')
        editor = 'vim'
        try:
            editor = Template('$EDITOR').substitute(os.environ)
        except KeyError:
            pass
        subprocess.run([editor, self.get_context_command_file_location()], check=True)
        return config.SUCCESSFULL_EXECUTION

    def cmd_complete(self):
        """Return completion words. Is common interface to be used from shell completion scripts."""
        self.parser.remove_first_argument()
        if self.parser.complete: return main()
        self.parser.enable_completion()
        main_res = main()
        for word in self.parser.complete.words:
            print(word, end=' ')
        print()
        return main_res

    def cmd_completion(self):
        """Print out command which is to be added to user's shell rc file to enable completion."""
        shell = self.parser.shift()
        self.parser.expect_nothing()
        completion_init_script_path = complete.completion_setup_script_path(shell)
        if exists(completion_init_script_path):
            self.form.print_str('source {} cmd'.format(completion_init_script_path))
        else:
            raise Exception('unsuported shell {}, choose bash or zsh'.format(cio.quote(shell)))
        return config.SUCCESSFULL_EXECUTION

    def load_aliases_raw(self):
        commands_db = load_commands(config.GLOBAL_COMMANDS_FILE_LOCATION)
        return [cmd.alias for cmd in commands_db if cmd.alias]

    def load_aliases(self):
        commands_db = load_commands(config.GLOBAL_COMMANDS_FILE_LOCATION)
        return [CommandArgument(cmd, self.logger, self.parser) for cmd in commands_db if cmd.alias]

    def load_project_aliases_raw(self):
        if self.project:
            return [cmd.alias for cmd in self.project.commands if cmd.alias]
        return None

    def load_project_aliases(self):
        if self.project:
            return [CommandArgument(cmd, self.logger, self.parser) for cmd in self.project.commands if cmd.alias]
        return None

    # == Arguments ===================================================================

    @property
    def argument_args(self):
        res = {}
        res['SAVE'] = Argument('--save', '-s', self.cmd_save, 'Saves command which is passed as further arguments')
        res['EDIT'] = Argument('--edit', '-e', self.cmd_edit, 'Edit the command database in text editor')
        res['INIT'] = Argument('--init', '-i', self.cmd_initialize, 'Initialize a project')
        res['VERSION'] = Argument('--version', '-V', self.cmd_version, 'Prints out version information')
        res['HELP'] = Argument('--help', '-h', self.cmd_help, 'Request detailed information about flags or commands')
        res['COMPLETE'] = Argument('--complete', None, self.cmd_complete, 'Returns list of words which are supplied to the completion shell command')
        res['COMPLETION'] = Argument('--completion', None, self.cmd_completion, 'Return shell command to be added to the .rc file to allow completion')
        res['QUIET'] = Argument('--quiet', '-q', lambda: set_function(self.conf, 'logging_level', config.QUIET_LEVEL), 'No output will be shown')
        res['VERBOSE'] = Argument('--verbose', '-v', lambda: set_function(self.conf, 'logging_level', config.VERBOSE_LEVEL), 'More detailed output information')
        res['DEBUG'] = Argument('--debug', '-d', lambda: set_function(self.conf, 'logging_level', config.DEBUG_LEVEL), 'Very detailed messages of script\'s inner workings')
        res['project_SCOPE'] = Argument('--project', '-p', lambda: set_function(self.conf, 'scope', 'project'), 'Applies the command in the project command collection')
        res['GLOBAL_SCOPE'] = Argument('--global', '-g', lambda: set_function(self.conf, 'scope', 'global'), 'Applies the command in the global command collection')
        return res

    @property
    def argument_groups(self):
        if self.argument_groups_cache:
            return self.argument_groups_cache
        res = {}
        project_aliases = self.load_project_aliases()
        project_help_string = None
        if (project_aliases != None) and (len(project_aliases) == 0):
            project_help_string = 'You may add new project commands via running "cmd --save" inside any project subdirectory. If the command is given alias, it will shop up here.'
        res['PROJECT_COMMANDS'] = ArgumentGroup('project commands', None, self.load_project_aliases, project_help_string)
        res['CUSTOM_COMMANDS'] = ArgumentGroup('custom commands', None, self.load_aliases, 'You may add new custom commands via "cmd --save if the command is given alias, it will show up here.')
        args = self.argument_args
        res['CMD_COMMANDS'] = ArgumentGroup('management commands', [args['SAVE'], args['EDIT'], args['INIT'], args['VERSION'], args['HELP'], args['COMPLETE'], args['COMPLETION']])
        res['CMD_SHOWN_COMMANDS'] = ArgumentGroup('management commands', [args['SAVE'], args['EDIT'], args['INIT'], args['VERSION'], args['HELP']])
        res['OUTPUT_ARGUMENTS'] = ArgumentGroup('', [args['QUIET'], args['VERBOSE'], args['DEBUG']])
        res['OPTIONAL_ARGUMENTS'] = ArgumentGroup('optional arguments', [args['QUIET'], args['VERBOSE'], args['DEBUG'], args['project_SCOPE'], args['GLOBAL_SCOPE']])
        self.argument_groups_cache = res
        return self.argument_groups_cache

def set_function(what, property_name, value):
    ''' Helper function to enable setting a variable to be a command '''
    what[property_name] = value

# == Main invocation =============================================================

if __name__ == '__main__':
    sys.exit(main())
