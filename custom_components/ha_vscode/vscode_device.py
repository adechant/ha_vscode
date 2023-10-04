import subprocess
import time


class VSCodeDeviceAPI:
    """Command line VSCode Tunnel OAuth device flow"""

    _close_session = False

    def __init__(self):
        self.test = "test"

    async def activation(self):
        result = subprocess.run(
            ["which apt-get"], shell=True, capture_output=True, text=True
        )
        time.sleep(2)
        return result.stdout

    async def register(self):
        result = subprocess.run(
            ["which code"], shell=True, capture_output=True, text=True
        )
        time.sleep(2)
        return result.stdout
