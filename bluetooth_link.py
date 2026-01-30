import asyncio
from bleak import BleakClient

class BluetoothLink:
    """
    Handles Bluetooth Low Energy communication between
    the computer and the microcontroller.
    """

    def __init__(self, device_address, characteristic_uuid):
        self.device_address = device_address
        self.characteristic_uuid = characteristic_uuid
        self.client = BleakClient(device_address)

    async def connect(self):
        if not self.client.is_connected:
            await self.client.connect()

    async def disconnect(self):
        if self.client.is_connected:
            await self.client.disconnect()

    async def read_measurement(self):
        """
        Reads a sensor value from the microcontroller.
        Expected format: UTF-8 encoded float string
        Example: b"12.45"
        """
        data = await self.client.read_gatt_char(self.characteristic_uuid)
        return float(data.decode().strip())

    async def send_control_output(self, value):
        """
        Sends the controller output back to the microcontroller.
        """
        await self.client.write_gatt_char(
            self.characteristic_uuid,
            str(value).encode()
        )

