from enum import Enum
from typing import List


EC_ADDRESS = str("/sys/kernel/debug/ec/ec0/io")


class RegisterList:
    def _read_registers(self) -> List[str]:
        with open(self.ec_address, "rb") as f:
            content = f.read()
        registers_list = content.hex('-').split('-')
        return registers_list

    def __init__(self, ec_address: str):
        self.ec_address = ec_address
        self.registers = self._read_registers()

    def read_register(self, address: int) -> int:
        return int(self.registers[address], 16)

    def write_register(self, value: int, address: int) -> None:
        write_val = ('0' + hex(value).replace('0x', ''))[-2:]
        self.registers[address] = write_val

    def write_changes(self):
        registers_string = ' '.join(self.registers)
        registers_bytes = bytes.fromhex(registers_string)
        with open(EC_ADDRESS, "wb") as f:
            f.write(registers_bytes)

    def update(self):
        self.registers = self._read_registers()


class Register:
    def __init__(self, address: int, register_list: RegisterList):
        self.address = address
        self.register_list = register_list

    # @staticmethod
    # def __serialize_value__(stdout_val: bytes):
    #     str_val = stdout_val.decode('utf-8')
    #     int_val = int(str_val.split(' ')[0])
    #     return int_val

    def read(self) -> int:
        return self.register_list.read_register(self.address)

    def write(self, value: int):
        self.register_list.write_register(value, self.address)


class Modes(Enum):
    AUTO = "auto"
    MANUAL = "manual"


class ModeRegister(Register):
    def __init__(self, address: int, register_list: RegisterList, manual_value: int, auto_value: int) -> None:
        super().__init__(address, register_list)
        self.manual_value: int = manual_value
        self.auto_value = auto_value

    def __set_auto__(self):
        self.write(self.auto_value)

    def __set_manual__(self):
        self.write(self.manual_value)

    def set_mode(self, mode: Modes):
        mode_register = {
            Modes.AUTO: self.__set_auto__,
            Modes.MANUAL: self.__set_manual__
        }
        mode_register[mode]()


class FanRegister(Register):
    def __init__(self, address: int, register_list: RegisterList, min: int, max: int) -> None:
        super().__init__(address, register_list)
        self.min: int = min
        self.max: int = max


class Fan:
    RESOLUTION = 50

    @classmethod
    def from_dict(cls, config: dict, register_list: RegisterList, max_temp: int):
        name = config["name"]
        mode_config = config["mode"]
        mode_register = ModeRegister(
            address=mode_config["register"],
            register_list=register_list,
            manual_value=mode_config["manual"],
            auto_value=mode_config["auto"]
        )
        fan_read_registers: List[FanRegister] = []
        read_configs = config["read"]
        for read_config in read_configs:
            read_register = FanRegister(
                address=read_config["register"],
                register_list=register_list,
                min=read_config["min"],
                max=read_config["max"]
            )
            fan_read_registers.append(read_register)
        fan_write_registers: List[FanRegister] = []
        write_configs = config["write"]
        for write_config in write_configs:
            write_register = FanRegister(
                address=write_config["register"],
                register_list=register_list,
                min=write_config["min"],
                max=write_config["max"]
            )
            fan_write_registers.append(write_register)
        temp_register = FanRegister(
            address=config["temp"],
            register_list=register_list,
            min=0,
            max=max_temp
        )
        fan = cls(
            name,
            mode_register,
            fan_read_registers,
            fan_write_registers,
            temp_register
        )
        return fan

    def __init__(
            self,
            name: str,
            mode_register: ModeRegister,
            fan_read_registers: List[FanRegister],
            fan_write_registers: List[FanRegister],
            temperature_register: FanRegister
    ) -> None:
        self.name: str = name
        self._mode: ModeRegister = mode_register
        self._read_list: List[FanRegister] = fan_read_registers
        self._write_list: List[FanRegister] = fan_write_registers
        self._temp: FanRegister = temperature_register
        self._history_len = 500
        self._read_history: List[List[int]] = [[] for _ in self._read_list]
        self._temperature_history: List[int] = []

    def map_value(self, value, range_min, range_max):
        return int(((value - range_min) / (range_max - range_min)) * self.RESOLUTION)

    def unmap_value(self, value, range_min, range_max):
        return int(((value * (range_max - range_min)) / self.RESOLUTION) + range_min)

    @property
    def mode(self):
        return self._mode

    @property
    def read_registers(self):
        return self._read_list

    @property
    def write_registers(self):
        return self._write_list

    @property
    def temperature_register(self):
        return self._temp

    @property
    def history_length(self):
        return self.history_length

    @history_length.setter
    def history_length(self, length: int):
        self._history_len = length

    def read_temperature(self):
        return self._temp.read()

    @property
    def temperature_history(self):
        temperature = self.read_temperature()
        self._temperature_history.append(temperature)
        # if len(self._temperature_history) > self.history_length:
        #     self._temperature_history = self._temperature_history[len(self._temperature_history)-self._history_len:]
        index = len(self._temperature_history) - self._history_len if len(self._temperature_history) > self._history_len else 0
        self._temperature_history = self._temperature_history[index:]
        return self._temperature_history

    def read_speeds(self):
        speeds = [r.read() for r in self._read_list]
        return speeds

    @property
    def read_history(self):
        speeds = self.read_speeds()
        for i, hist in enumerate(self._read_history):
            hist.append(speeds[i])
            # if len(hist) > self._history_len:
            #     hist = hist[len(hist) - self._history_len:]
            index = len(hist) - self._history_len if len(hist) > self._history_len else 0
            hist = hist[index:]
            self._read_history[i] = hist
        return self._read_history

    def set_speed(self, speed: float):
        self._mode.set_mode(Modes.MANUAL)
        speed = int(speed * self.RESOLUTION)
        for write in self._write_list:
            speed = self.unmap_value(speed, write.min, write.max)
            write.write(speed)

    def set_mode(self, mode: Modes):
        self._mode.set_mode(mode)

    def get_mode(self):
        mode_value = self._mode.manual_value
        if mode_value == self._mode.read():
            return Modes.MANUAL
        if mode_value == self._mode.read():
            return Modes.AUTO
        raise ValueError(f"Invalid mode value: {mode_value}, for {self.name}!")
