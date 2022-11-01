import os.path
import subprocess
import time
from dataclasses import dataclass
import time
from typing import List
from pyctcdecode import build_ctcdecoder
from transformers import Wav2Vec2CTCTokenizer
import logging


logger = logging.getLogger(__name__)


@dataclass
class Command:
    name: str
    args: List[str]


class LanguageDecoderBuilder:
    def __init__(
            self,
            commands_dir: str,
            language_dir: str
    ):
        self.commands_dir = commands_dir
        self.language_text_path = os.path.join(language_dir, "language.txt")
        self.language_model_path = os.path.join(language_dir, "language.arpa")

    def _get_arg_values(self, arg_name: str) -> List[str]:
        path = os.path.join(self.commands_dir, arg_name) + ".txt"
        with open(path, "r") as f:
            lines = f.readlines()
        arg_values = [line.strip() for line in lines]
        return arg_values

    def _get_commands(self) -> List[Command]:
        path = os.path.join(self.commands_dir, "commands.txt")
        with open(path, "r") as f:
            lines = f.readlines()
        commands: List[Command] = []
        for line in lines:
            line = line.strip()
            command_words_list = line.split(" ")
            name = command_words_list[0]
            args = command_words_list[1:]
            commands.append(Command(name, args))
        return commands

    def _generate_possible_commands(self, command_list: List[Command]) -> List[str]:
        possible_commands: List[str] = []
        for command in command_list:
            list_of_command_possibilities: List[str] = [command.name]
            for arg in command.args:
                arg_values = self._get_arg_values(arg)
                list_of_arg_possibilities: List[str] = []
                for arg_value in arg_values:
                    for possibility in list_of_command_possibilities:
                        list_of_arg_possibilities.append(" ".join([possibility, arg_value]))
                list_of_command_possibilities = list_of_arg_possibilities
            possible_commands += list_of_command_possibilities
        return possible_commands

    def _save_language_text(self, possible_commands: List[str]):
        with open(self.language_text_path, "w") as f:
            f.writelines([f"{l}\n" for l in possible_commands])

    def _generate_model_file(self):
        completed_process = subprocess.run([
            "ngram-count",
            "-text",
            self.language_text_path,
            "-order",
            "3",
            "-wbdiscount",
            "-unk",
            "-lm",
            self.language_model_path
        ])
        if completed_process.returncode != 0:
            raise RuntimeError(completed_process.stderr)

    def _build_decoder(self, tokens: List[str]):
        logger.info("building decoder")
        decoder = build_ctcdecoder(tokens, self.language_model_path, alpha=2.0, beta=-1.0)
        logger.info("done building decoder!")
        time.sleep(1)
        logger.info("done sleeping after building decoder!")
        return decoder

    def build_language(self):
        commands = self._get_commands()
        possible_commands = self._generate_possible_commands(commands)
        self._save_language_text(possible_commands)
        self._generate_model_file()

    def build_decoder(self, tokenizer: Wav2Vec2CTCTokenizer):
        logger.info("updating tokens")
        tokens = [x[0] for x in sorted(tokenizer.get_vocab().items(), key=lambda x: x[1])]
        tokens[tokens.index('|')] = " "
        decoder = self._build_decoder(tokens)
        return decoder
