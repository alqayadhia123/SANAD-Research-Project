"""Small POSIX process supervisor for local lab use.

Production Compose runs one process per container; this supervisor is not used
as a substitute for an orchestrator or container restart policy.
"""
from __future__ import annotations
import logging, os, signal, subprocess, sys, time
from dataclasses import dataclass

log = logging.getLogger("sanad.supervisor")

@dataclass
class Service:
    name: str
    command: list[str]
    critical: bool = True
    restart: bool = True
    process: subprocess.Popen | None = None
    failures: int = 0

class Supervisor:
    def __init__(self, services: list[Service], shutdown_timeout: int = 20):
        self.services = services
        self.shutdown_timeout = shutdown_timeout
        self.stopping = False

    def _request_stop(self, _sig, _frame):
        self.stopping = True

    def run(self) -> int:
        signal.signal(signal.SIGTERM, self._request_stop)
        signal.signal(signal.SIGINT, self._request_stop)
        try:
            for service in self.services:
                service.process = subprocess.Popen(service.command, start_new_session=True)
            while not self.stopping:
                for service in self.services:
                    if service.process is None:
                        continue
                    code = service.process.poll()
                    if code is None:
                        continue
                    log.error("%s exited (%s)", service.name, code)
                    if service.critical:
                        return 1
                    if service.restart and not self.stopping:
                        service.process = None
                        service.failures += 1
                    else:
                        service.process = None
                        delay = min(60, 2 ** min(service.failures, 6))
                        time.sleep(delay)
                        service.process = subprocess.Popen(service.command, start_new_session=True)
                time.sleep(0.5)
            return 0
        finally:
            for service in reversed(self.services):
                proc = service.process
                if proc is None or proc.poll() is not None:
                    continue
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                    proc.wait(timeout=self.shutdown_timeout)
                except (ProcessLookupError, subprocess.TimeoutExpired):
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    proc.wait()
