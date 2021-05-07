
from os.path import join

from shcmdmgr import config

class Complete:
    """
    Manage completion option list. Create an instance of this class
    add the last argument and then supply list of all currently feasible
    arguments.
    """

    def __init__(self, last_arg: str):
        self.last_arg = last_arg
        self.words = []
        self.invoked = False

    @property
    def words(self):
        res_words = []
        for word in self.__words:
            viable_word = word[0] != '-'
            viable_completion = len(self.last_arg) != 0
            if word.startswith(self.last_arg) and (len(self.last_arg) != 0 or word[0] != '-'):
                res_words.append(word)
        return res_words

    @words.setter
    def words(self, words):
        for word in words:
            if len(word) == 0:
                raise Exception('An empty word was supplied to Complete, supplied list was {}'.format(words))
        self.__words = words

    def add_words(self, new_words):
        if not self.__words:
            self.__words = []
        self.__words += new_words

    def check_invocation(self):
        if self.invoked:
            raise Exception('Completion final method executed more than twice!')
        self.invoked = True

    def nothing(self):
        self.check_invocation()
        return config.SUCCESSFULL_EXECUTION

    def commands(self, *words_lists):
        self.check_invocation()
        for words_list in words_lists:
            self.add_words(words_list)
        return config.SUCCESSFULL_EXECUTION

def completion_setup_script_path(shell: str) -> str:
    return join(config.DATA_PATH, 'completion/setup.{}'.format(shell))
