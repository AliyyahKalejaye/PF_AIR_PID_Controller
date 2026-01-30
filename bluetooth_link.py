import bluetooth

class BluetoothLink:
    def __init__(self, mac_address, port=1):
        self.mac_address = mac_address
        self.port = port
        self.socket = None

    def connect(self):
        self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.socket.connect((self.mac_address, self.port))

    def read_sensor(self):
        """
        Receives sensor value from microcontroller
        Expected format: float value as string
        """
        data = self.socket.recv(1024).decode().strip()
        return float(data)

    def send_control(self, value):
        """
        Sends control signal back to microcontroller
        """
        self.socket.send(f"{value}\n")

    def close(self):
        if self.socket:
            self.socket.close()
