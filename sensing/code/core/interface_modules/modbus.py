import pymodbus.client
import pymodbus.constants
import pymodbus.payload
import pymodbus.transaction
import pymodbus.exceptions
import pymodbus.framer
import logging
import asyncio

logger = logging.getLogger(__name__)

pip_requirements = {"pymodbus":"3.8.3"}

class ModbusTCPSync:
    def __init__(self, config):
        self.adapter_addr = config.get("adapter_addr")
        self.adapter_port = config.get("adaptor_port", 502)

        self.modbus_client = pymodbus.client.ModbusTcpClient(self.adapter_addr, port=self.adapter_port,
                                                             framer=pymodbus.framer.FramerType.RTU)

    def initialise(self):
        self.modbus_client.connect()

    def read_register(self, register_addr, count, slave_id):
        try:
            modbus_response = self.modbus_client.read_input_registers(address=register_addr, count=int(count),
                                                                      slave=int(slave_id))
        except pymodbus.exceptions.ModbusException as exc:
            logger.error(f"ERROR: exception in pymodbus {exc}")
            raise exc

        if modbus_response.isError():
            logger.error(f"{modbus_response}")
            raise pymodbus.exceptions.ModbusException(str(modbus_response))

        reading = self.modbus_client.convert_from_registers(modbus_response.registers,
                                                            self.modbus_client.DATATYPE.FLOAT32,
                                                            word_order="little")
        
        logger.debug(f"reading: {reading}")
        
        return reading

class ModbusTCPAsync:
    def __init__(self, config):
        self.adapter_addr = config.get("adapter_addr")
        self.adapter_port = config.get("adaptor_port", 502)

        self.modbus_client = pymodbus.client.AsyncModbusTcpClient(self.adapter_addr, port=self.adapter_port,
                                                             framer=pymodbus.framer.FramerType.RTU)


    async def initialise(self):
        await self.modbus_client.connect()


    async def read_register(self, register_addr, count, slave_id):
        try:
            modbus_response = await self.modbus_client.read_input_registers(address=register_addr, count=int(count), slave=int(slave_id))
        except pymodbus.exceptions.ModbusException as exc:
            logger.error(f"ERROR: exception in pymodbus {exc}")
            raise exc

        if modbus_response.isError():
            logger.error(f"{modbus_response}")
            raise pymodbus.exceptions.ModbusException(str(modbus_response))

        reading = self.modbus_client.convert_from_registers(modbus_response.registers,
                                                            self.modbus_client.DATATYPE.FLOAT32,
                                                            word_order="little")
        
        logger.debug(f"reading: {reading}")
        
        return reading
#
# class ModbusSerialSync:
#     pass
#
# class ModbusUDPSync:
#     pass
#
# class ModbusTLSSync:
#     pass