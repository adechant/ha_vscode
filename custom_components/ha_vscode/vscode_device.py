import asyncio
import logging
import os
import re
import subprocess
import time
from threading import Lock
from threading import Thread

from .const import PACKAGE_NAME
from .exceptions import HAVSCodeDownloadException
from .exceptions import HAVSCodeTarException
from .exceptions import HAVSCodeZipException

if not "PACKAGE_NAME" in globals():
    PACKAGE_NAME = "ha_vscode"

LOGGER: logging.Logger = logging.getLogger(PACKAGE_NAME)

# don't know why but there is no alpine-armhf version, only linux
architecture_map = {
    "x86_64": "alpine-x64",
    "armv7l": "linux-armhf",
    "aarch64": "alpine-arm64",
}


class VSCodeDeviceAPI:
    """Command line VSCode Tunnel OAuth device flow"""

    _close_session = False

    def __init__(self, storage_dir):
        self.log = LOGGER

        self.log.setLevel(logging.DEBUG)

        ###uncomment if debuggin outside of home assistant
        """handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        self.log.addHandler(handler)"""
        ###

        self.oauthToken = None
        self.devURL = None
        self.proc = None
        self.storage_dir = storage_dir
        self.thread = None
        self.lock = Lock()
        if not os.path.exists(self.storage_dir):
            os.mkdir(self.storage_dir)
        self.exePath = os.path.join(self.storage_dir, "code")

    def downloadViaCurl(self, outdir):
        # curl -Lk https://code.visualstudio.com/sha/download?build=stable&os=cli-alpine-x64 --output /workspaces/ha_core/config/custom_components/ha_vscode/bin/vscode_cli.tar.gz
        result = None
        architecture = os.uname().machine
        getVSCodeCLIcurl = [
            "curl",
            "-Lk",
            f"https://code.visualstudio.com/sha/download?build=stable&os=cli-{architecture_map[architecture]}",
            "--output",
            outdir,
        ]

        hasCurl = subprocess.run(
            ["which", "curl"],
            capture_output=True,
            text=True,
        )

        if hasCurl.returncode == 0:
            self.log.debug("Curl found on the system")
            result = subprocess.run(
                getVSCodeCLIcurl,
                capture_output=True,
                text=True,
                check=True,
            )
        else:
            self.log.debug("Curl not found on the system")
            return None

        return result.returncode == 0

    def downloadViaWGet(self, outdir):
        # wget https://code.visualstudio.com/sha/download?build=stable&os=cli-alpine-x64 -O /workspaces/ha_core/config/custom_components/ha_vscode/bin/vscode_cli.tar.gz

        result = None
        architecture = os.uname().machine
        getVSCodeCLIwget = [
            "wget",
            f"https://code.visualstudio.com/sha/download?build=stable&os=cli-{architecture_map[architecture]}",
            "-O",
            outdir,
        ]

        hasWget = subprocess.run(
            ["which", "wget"],
            capture_output=True,
            text=True,
        )
        if hasWget.returncode == 0:
            self.log.debug("wget found on the system")
            result = subprocess.run(
                getVSCodeCLIwget,
                capture_output=True,
                text=True,
                check=True,
            )
        else:
            self.log.debug("wget not found on the system")
            return None

        return result.returncode == 0

    def unzip(self, outfile):
        # force overwrite of existing files - this will ensure vscode cli is updated. and we don't block on user prompt
        result = subprocess.run(
            ["gzip", "-fd", outfile],
            capture_output=True,
            text=True,
            check=True,
        )
        if result:
            self.log.debug(result.stdout)
            self.log.debug("Unzipped " + outfile)
        else:
            self.log.debug("Error occurred while unzipping " + outfile)
            raise HAVSCodeZipException()

    def untar(self, outfile):
        result = subprocess.run(
            ["tar", "-xvf", outfile[:-3], "-C", self.storage_dir],
            capture_output=True,
            text=True,
            check=True,
        )

        if result.returncode == 0:
            self.log.debug(result.stdout)
            self.log.debug("Untarred " + outfile[:-3])
        else:
            self.log.debug(result.stdout)
            self.log("Error occurred while untarring " + outfile[:-3])
            raise HAVSCodeTarException()

    def checkExe(self):
        # check that the code executable exists
        if not os.path.exists(self.exePath):
            self.log.debug(
                "Error! VSCode executable is not located at: " + self.exePath
            )
        else:
            self.log.debug("VSCode executable is located at: " + self.exePath)

    def reader(self):
        self.log.debug("Starting reader thread")
        try:
            while True:
                line = self.proc.stdout.readline().strip()
                if line is not None:
                    if len(line) > 0:
                        self.log.debug("Parsing line: " + line)
                if not self.checkForOauthToken(line):
                    self.checkForDevURL(line)
        except:
            self.log.debug("Reader threw exception: likely closed stdout")
        finally:
            self.log.debug("Received EOF from stdout, thread exiting...")

    def unregisterTunnel(self):
        if self.proc:
            self.log.debug(
                "Stop tunnel with active subprocess. Stopping and unregistering..."
            )
            self.stopTunnel()

        isUnregistered = subprocess.run(
            [
                self.exePath,
                "tunnel",
                "unregister",
            ],
            capture_output=True,
            text=True,
        )

        if isUnregistered == 0:
            self.log.info("Unregistering tunnel successful.")
        else:
            self.log.error(
                "Could not unregister tunnel. Please run 'code tunnel unregister' manually to avoid future issues."
            )

    def startTunnel(self):
        # if the tunnel is already started, stop it and restart - we otherwise might miss important info written to stdout
        if self.proc:
            self.log.debug(
                "Start tunnel with active subprocess. Stopping and restarting..."
            )
            self.stopTunnel()

        self.proc = subprocess.Popen(
            [self.exePath, "tunnel", "--random-name", "--accept-server-license-terms"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # output stderr to stdout
            # bufsize=1, #was enabled to reduce the buffer size
            # do not put shell=true, as this will spawn 2 processes, a shell, and our command.
            # zombie proesses will ensue if we try to terminate the process with sigint.
            text=True,
        )
        print(self.proc.pid)
        self.log.info("Tunnel Service started with pid: " + str(self.proc.pid))
        # create the queue and the reader thread
        self.thread = Thread(target=self.reader)
        self.thread.daemon = True
        self.thread.start()

    def stopTunnel(self):
        if self.proc is None:
            self.log.debug("Stop Tunnel called with no active subprocess")
            return
        # ? need toclose the stdoutput as it will be closed when process is terminated
        self.log.debug("Terminating subprocess: " + str(self.proc.pid))
        self.proc.terminate()
        self.log.debug("Closing subprocess stdout")
        self.proc.stdout.close()
        while self.proc.poll() is None:
            try:
                self.log.debug("waiting for " + str(self.proc.pid) + " to end")
                self.proc.wait(timeout=0.1)
            except subprocess.TimeoutExpired:
                self.log.debug("Wait timeout expired for subprocess: " + self.proc.pid)
        # wait for the reader thread to end
        if self.thread:
            self.log.debug("Thread is not None. Will check if alive...")
            if self.thread.is_alive():
                self.log.debug("Thread is alive. Will attempt to join...")
                self.thread.join(timeout=0.1)
                if self.thread.is_alive():
                    self.log.debug(
                        "Timeout occurred and thread join failed. Zombie thread may be created"
                    )
                else:
                    self.log.debug("Thread is dead.")
            else:
                self.log.debug("Thread is alive. Will attempt to join...")
        self.thread = None
        self.proc = None
        self.log.info("Tunnel Service ended.")

    # tried asyncio.timeout with a context manager, but some weird shirt was happening.
    # no timeouterror was being thrown and the tiemout in the context manager was being
    # reset to ~5800 seconds.. ??maybe affected by the main event loop somewhere
    # maybe because we weren't waiting on sleep --> try timeout again!
    async def getOAuthToken(self, timeout=3.0):
        out = None
        start = time.time()
        while True:
            self.lock.acquire()
            # self.log.debug("Acquired Lock - getOAuthToken")
            if self.oauthToken:
                out = self.oauthToken
                self.lock.release()
                # self.log.debug("Released Lock - getOAuthToken")
                # self.log.debug("getOAuthToken returning: " + out)
                break

            if (time.time() - start) > timeout:
                # self.log.debug("Released Lock - getOAuthToken")
                # self.log.debug("getOAuthToken returning: None")
                self.lock.release()
                break
            self.lock.release()
            # self.log.debug("Released Lock - getOAuthToken")
            # self.log.debug("Sleeping for 0.1s in getOAuthToken")
            await asyncio.sleep(0.1)
        return out

    # will return none if we can't find the dev url
    async def getDevURL(self, timeout=5.0):
        out = None
        start = time.time()
        while True:
            self.lock.acquire()
            # self.log.debug("Acquired Lock - getDevURL")
            if self.devURL:
                out = self.devURL
                self.lock.release()
                # self.log.debug("Released Lock - getDevURL")
                # self.log.debug("getDevURL returning: " + out)
                break

            if (time.time() - start) > timeout:
                # self.log.debug("Released Lock - getOAuthToken")
                # self.log.debug("getOAuthToken returning: None")
                self.lock.release()
                break
            self.lock.release()
            # self.log.debug("Released Lock - getDevURL")
            # self.log.debug("Sleeping for 0.1s in getDevURL")
            await asyncio.sleep(0.1)
        return out

    def checkForOauthToken(self, line):
        match = re.search(
            "https://github.com/login/device and use code .*$",
            line,
        )
        if match:
            token = match.group()[-9:]
            self.log.info("Github oauth login token: " + token)
            # if we parsed an oauth Token, then the dev url must be stale and we need to re-auth
            self.lock.acquire()
            self.log.debug("Acquired Lock - checkForOauthToken")
            self.oauthToken = token
            self.lock.release()
            self.log.debug("Released Lock - checkForOauthToken")
            return self.oauthToken
        return None

    def checkForDevURL(self, line):
        match = re.search(
            "https://vscode.dev/tunnel/[^/]*/",
            line,
        )
        if match:
            url = match.group()
            self.log.info("Dev url: " + url)
            # if we have a dev url, we don't need an oauth token
            # probably should make this threadsafe
            self.lock.acquire()
            self.log.debug("Acquired Lock - checkForDevURL")
            self.devURL = url
            self.lock.release()
            self.log.debug("Released Lock - checkForDevURL")
            return url
        return None

    def isRunning(self):
        return self.proc is not None

    async def activate(self, timeout=5.0):
        result = await self.getDevURL(timeout=timeout)
        if result:
            self.log.debug("Activated on url: " + result)
        if result is None:
            self.stopTunnel()
        return result

    async def register(self, timeout=3.0):
        outfile = "vscode_cli.tar.gz"
        outdir = os.path.join(self.storage_dir, outfile)

        result = self.downloadViaCurl(outdir)
        if not result:
            self.downloadViaWGet(outdir)
        if result:
            self.log.debug("Downloaded vscode cli to " + outdir)
        else:
            self.log.info(
                "Could not download vscode cli. Curl and wget are both not available on your system."
            )
            raise HAVSCodeDownloadException()

        self.unzip(outdir)
        self.untar(outdir)
        self.checkExe()
        self.startTunnel()
        token = await self.getOAuthToken(timeout=timeout)
        if token:
            self.log.debug("Registered with token: " + token)
        return token


def main():
    api = VSCodeDeviceAPI(".")
    outfile = "vscode_cli.tar.gz"
    outdir = os.path.join(".", outfile)
    api.startTunnel()
    api.getOAuthToken()
    api.getDevURL(timeout=3)
    api.stopTunnel()


if __name__ == "__main__":
    main()
