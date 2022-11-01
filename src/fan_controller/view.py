from typing import List

from fan_controller.fan import Fan

import numpy as np


class ViewController:
    def __init__(self, fans: List[Fan]):
        self.fans = fans

    @staticmethod
    def represent_value(val: int, resolution: int):
        values = {
            'filler': '█',
            'empty': ' ',
            0: " ",
            1: "▁",
            2: "▂",
            3: "▃",
            4: "▄",
            5: "▅",
            6: "▆",
            7: "▇",
            8: "█",
        }
        values_len = len(values) - 2
        max_multiplier = int(resolution / values_len)
        multiplier = int(val / values_len)
        residual = val % values_len
        base = multiplier * [values["filler"]]
        out = (max_multiplier - multiplier) * [values['empty']] + [values[residual]] + base
        return out

    def serialize_history(self, history, range_min, range_max, resolution):
        mapped = [int(((val - range_min) / (range_max - range_min)) * resolution) for val in history]
        represented = np.array([self.represent_value(val, resolution) for val in mapped])
        represented = np.transpose(represented)
        out = ""
        for i in represented:
            out += ''.join(i)
            out += '\n'
        return out

    # def make_graph(self, history: 'list[int]', register: FanRegister, registers_list):
    #     @dataclass
    #     class Graphed:
    #         history: "list[int]"
    #         graph: str
    #
    #     columns: int = os.get_terminal_size().columns
    #     history.append(register.read(registers_list))
    #     hist_len = len(history)
    #     if hist_len > columns:
    #         history = history[(hist_len - columns):]
    #     graph = str(self.serialize_history(history, register.min, register.max))
    #     return Graphed(history, graph)

    # def get_summary(self, registers_list):
    #     out = ""
    #
    #     out += self.name + '\n'
    #     out += f"mode: {self.get_mode(registers_list)}\n"
    #     graphed_read = self.make_graph(self.__read_history, self.__read, registers_list)
    #     self.__read_history = graphed_read.history
    #     speed_raw = self.__read_history[-1]
    #     speed_percent = int((self.map_value(speed_raw, self.__read.min, self.__read.max) / self.RESOLUTION) * 100)
    #     out += f'fan speed: {speed_percent}%\n'
    #     out += graphed_read.graph + '\n'
    #
    #     graphed_temp = self.make_graph(self.__temp_history, self.__temp, registers_list)
    #     self.__temp_history = graphed_temp.history
    #     out += f'temperature: {self.__temp_history[-1]}°C\n'
    #     out += graphed_temp.graph + '\n'
    #
    #     return out

    def get_fan_representation(self, fan: Fan):
        out = f"{fan.name}\n" \
              f"temperature:\n"
        temp_graph = self.serialize_history(
            fan.temperature_history,
            fan.temperature_register.min,
            fan.temperature_register.max,
            fan.RESOLUTION
        )
        out += temp_graph + "\n"
        for i, read_register in enumerate(fan.read_registers):
            out += f"fan {i+1}:\n"
            register_graph = self.serialize_history(
                fan.read_history[i],
                read_register.min,
                read_register.max,
                fan.RESOLUTION
            )
            out += register_graph + "\n"
        return out
