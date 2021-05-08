import sys

from shcmdmgr import config, cio
from shcmdmgr.args import ArgumentGroup
from shcmdmgr.complete import Complete

class Parser:
    """
    Provide a common interface to interact with commandline arguments.
    It also handles help and completion.
    """
    def __init__(self, arguments, form, logger):
        self.arguments = arguments
        self.complete = None
        self.form = form
        self.help = False
        self.logger = logger

    def enable_help(self):
        """
        All commands will print possible arguments and their description
        instead of their normal behavior.
        """
        if self.help:
            self.form.print_str('usage: cmd --help <command>')
            self.form.print_str('prints more defailed information about how to use the <command>')
            sys.exit(config.SUCCESSFULL_EXECUTION)
        self.help = True

    def enable_completion(self):
        """
        All commands will print list of possible arguments instead of their
        normal behavior.
        """
        last_arg = sys.argv[-1]
        sys.argv = sys.argv[:-1]
        self.complete = Complete(last_arg)
        self.logger.setLevel(config.QUIET_LEVEL)
        # fixme: no output must be ensured as soon as possible, however if main is called again, it may reset logger level to something more verbose

    def peek(self):
        """Returns the first argument, but doesn't remove it."""
        res = None
        if len(self.arguments) != 0:
            res = self.arguments[0]
        self.logger.debug('Parser peek {}'.format(cio.quote(res)))
        return res

    def get_command(self):
        # if self.complete:
        #     return self.complete.commands(self.load_aliases_raw(), self.load_project_aliases_raw())
        # if self.help.print:
        #     return self.print_general_help()
        self.logger.debug('Parser command')

    def get_rest(self):
        """Returns all of the remaining arguments."""
        if self.help:
            sys.exit(config.SUCCESSFULL_EXECUTION)
        res = self.arguments
        self.arguments = []
        return res

    def shift(self):
        res = self.peek()
        self.arguments = self.arguments[1:]
        return res

    def expect_nothing(self):
        cur = self.peek()
        if cur:
            self.form.print_str('parameter {} is given where no parameter was expected'.format(cio.quote(cur)))
            sys.exit(config.USER_ERROR)

    # def expect(self, name, description):
    #     cur = self.peek()
    #     if not cur:
    #         if self.help:
    #             pass # todo

    def may_have(self, groups: [ArgumentGroup]):
        current = self.peek()
        if current:
            for args in [group.arguments for group in groups if group.arguments]:
                for arg in args:
                    if current in [arg.arg_name, arg.short_arg_name]:
                        self.shift()
                        arg.function()
                        return True
        elif self.help:
            self.form.print_str(ArgumentGroup.to_str(groups), end='')
            sys.exit(config.SUCCESSFULL_EXECUTION)
        return False

    def load_all(self, groups: [ArgumentGroup]):
        while self.may_have(groups): pass

    @staticmethod
    def remove_first_argument():
        sys.argv = [sys.argv[0]] + sys.argv[2:]
