
from shcmdmgr import filemanip, cio

class Command:
    # command can be either str, or a function (str[]) -> None
    def __init__(self, command: any, description: str = None, alias: str = None, creation_time: str = None):
        self.command = command
        if description == '':
            description = None
        self.description = description
        if alias == '':
            alias = None
        self.alias = alias
        self.creation_time = creation_time

    @classmethod
    def from_json(cls, data):
        return cls(**data)

def load_commands(commands_file_location) -> [Command]:
    commands_db = filemanip.load_json_file(commands_file_location)
    return [Command.from_json(j) for j in commands_db]
