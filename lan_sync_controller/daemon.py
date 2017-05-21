import getpass
import logging
import sys
import time

from lan_sync_controller import base
from lan_sync_controller.config_loader import SETTINGS
from lan_sync_controller.discovery import NeighborsDetector
from lan_sync_controller.pysyncit.server import Server
from lan_sync_controller.pysyncit import monitor as pysyncit_monitor
# from lan_sync_controller.process_handler import ProcessHandler

LOG = logging.getLogger(__name__)


class LANSyncDaemon(base.BaseDaemon):

    """
    A daemon that runs the app in background
    """

    def stop(self):
        super(LANSyncDaemon, self).stop()
        base.kill_process(self.pidfile)
        # Find and kill existed pysyncit process.
        # base.kill_process('/tmp/pysyncit.pid')

    def run(self):
        # Init detector and get all vaild hosts
        # in LAN. Vaild host is the host which open
        # SETTINGS['default-port'].
        _detector = NeighborsDetector()
        username = getpass.getuser()
        port = int(SETTINGS['default-port'])
        watch_dirs = SETTINGS['default-syncdir']
        servers = list()
        node = Server(username, port, watch_dirs, servers)
        node.activate()

        # _handler = ProcessHandler(SETTINGS['default-syncapp'])
        while True:
            # List valid hosts
            servers = _detector.detect_valid_hosts()
            node.servers = servers
            time.sleep(10)


class PySyncitDaemon(base.BaseDaemon):

    """
    A daemon that runs pysyncit in background.
    """

    def start(self, servers):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            pf = open(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if pid:
            message = "pidfile %s already exist. Daemon already running?\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)

        # Start the daemon
        self.daemonize()
        self.run(servers)

    def restart(self, servers):
        """
        Restart the daemon
        """
        self.stop()
        self.start(servers)

    def run(self, servers):
        while True:
            pysyncit_monitor.run(servers)
