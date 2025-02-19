#!/usr/bin/env python3

"""
This module holds the Container and ContainerManager classes. The Container
class is responsible for abstracting the Docker containers and allow running
containers easily and make sure they are initialized before using them.
The Containermanager class allows to create container networks, list all
running containers and stop them.
"""

from time import time, sleep
from typing import List, Tuple, Optional
from bench_executor.logger import Logger
from bench_executor.docker import Docker

WAIT_TIME = 1  # seconds
TIMEOUT_TIME = 600  # seconds
NETWORK_NAME = 'bench_executor'


class ContainerManager():
    """Manage containers and networks."""

    def __init__(self, docker: Docker):
        """Creates an instance of the ContainerManager class."""
        self._docker = docker

    def create_network(self, name: str):
        """Create a container network.

        Parameters
        ----------
        name : str
            Name of the network
        """
        self._docker.create_network(name)


class Container():
    """Container abstracts a Docker container

    Abstract how to run a command in a container, start or stop a container,
    or retrieve logs. Also allow to wait for a certain log entry to appear or
    exit successfully.
    """

    def __init__(self, container: str, name: str, logger: Logger,
                 ports: dict = {}, environment: dict = {},
                 volumes: List[str] = [],
                 expect_failure: bool = False):
        """Creates an instance of the Container class.

        Parameters
        ----------
        container : str
            Container ID.
        name : str
            Pretty name of the container.
        logger : Logger
            Logger class to use for container logs.
        expect_failue : bool
            If a failure is expected or not.
        ports : dict
            Ports mapping of the container onto the host.
        environment : dict
            Environment variables to expose to the container.
        volumes : list
            Volumes mapping of the container onto the host.
        """
        self._docker = Docker(logger)
        self._manager = ContainerManager(self._docker)
        self._container_id: Optional[str] = None
        self._container_name = container
        self._name = name
        self._ports = ports
        self._volumes = volumes
        self._environment = environment
        self._proc_pid = None
        self._long_id = None
        self._cgroups_mode = None
        self._cgroups_dir = None
        self._started = False
        self._logger = logger
        self._expect_failure = expect_failure

        # create network if not exist
        self._manager.create_network(NETWORK_NAME)

    @property
    def started(self) -> bool:
        """Indicates if the container is already started"""
        return self._started

    @property
    def name(self) -> str:
        """The pretty name of the container"""
        return self._name

    def run(self, command: str = '', *, working_dir=None, detach=True, environment=None) -> bool:
        """Run the container.

        This is used for containers which are long running to provide services
        such as a database or endpoint.

        Parameters
        ----------
        command : str
            The command to execute in the container, optionally and defaults to
            no command.
        working_dir : str
            Set a working directory in the container (optional)
        detach : bool
            If the container may run in the background, default True.

        Returns
        -------
        success : bool
            Whether running the container was successfull or not.
        """
        if environment is None:
            environment = {}

        def merge_env(e1, e2):
            r = {}
            for key in set(e1.keys()).union(e2.keys()):
                if key in e2:
                    in_e1 = key in e1
                    is_arr = isinstance(e2[key], list) or (in_e1 and isinstance(e1[key], list))
                    if in_e1 and (is_arr or key == "JDK_JAVA_OPTIONS"):
                        if is_arr:
                            r[key] = [*e1[key], *e2[key]]
                        else:
                            r[key] = f'{e1[key]} {e2[key]}'
                    else:
                        r[key] = e2[key]
                else:
                    r[key] = e1[key]
                if isinstance(r[key], list):
                    r[key] = ' '.join(r[key])
            return r

        e = merge_env(self._environment, environment)
        v = self._volumes
        self._started, self._container_id = \
            self._docker.run(self._container_name, command, self._name, detach,
                             self._ports, NETWORK_NAME, e, v, working_dir)

        if not self._started:
            self._logger.error(f'Starting container "{self._name}" failed!')
        return self._started

    def exec(self, command: str) -> Tuple[bool, List[str]]:
        """Execute a command in the container.

        Parameters
        ----------
        command : str
            The command to execute in the container.

        Returns
        -------
        success : bool
            Whether the command was executed successfully or not.
        logs : list
            The logs of the container for executing the command.
        """
        logs: List[str] = []

        if self._container_id is None:
            self._logger.error('Container is not initialized yet')
            return False, []
        exit_code = self._docker.exec(self._container_id, command)
        logs = self._docker.logs(self._container_id)
        if logs is not None:
            for line in logs:
                self._logger.debug(line)
        if exit_code == 0:
            return True, logs

        return False, logs

    def run_and_wait_for_log(self, log_line: str, command: str = '', *, working_dir=None) -> bool:
        """Run the container and wait for a log line to appear.

        This blocks until the container's log contains the `log_line`.

        Parameters
        ----------
        log_line : str
            The log line to wait for in the logs.
        command : str
            The command to execute in the container, optionally and defaults to
            no command.
        working_dir : str
            Set a working directory in the container (optional)

        Returns
        -------
        success : bool
            Whether the container exited with status code 0 or not.
        """
        if not self.run(command, working_dir=working_dir):
            self._logger.error(f'Command "{command}" failed')
            return False

        if self._container_id is None:
            self._logger.error('Container is not initialized yet')
            return False

        start = time()
        found_line = False
        line_number = 0
        while (True):
            logs = self._docker.logs(self._container_id)
            for index, line in enumerate(logs):
                # Only print new lines when iterating
                if index > line_number:
                    line_number = index
                    self._logger.debug(line)

                if time() - start > TIMEOUT_TIME:
                    msg = f'Starting container "{self._name}" timed out!'
                    self._logger.error(msg)
                    break

                if log_line in line:
                    found_line = True
                    break

            if found_line:
                sleep(WAIT_TIME)
                return True

        # Logs are collected on success, log them on failure
        self._logger.error(f'Waiting for container "{self._name}" failed!')
        logs = self._docker.logs(self._container_id)
        for line in logs:
            self._logger.error(line)
        return False

    def run_and_wait_for_exit(self, command: str = '', *, working_dir=None, environment=None) -> bool:
        """Run the container and wait for exit

        This blocks until the container exit and gives a status code.

        Parameters
        ----------
        command : str
            The command to execute in the container, optionally and defaults to
            no command.
        working_dir : str
            Set a working directory in the container (optional)

        Returns
        -------
       success : bool
            Whether the container exited with status code 0 or not.
        """
        if not self.run(command, working_dir=working_dir, environment=environment):
            return False

        if self._container_id is None:
            self._logger.error('Container is not initialized yet')
            return False

        status_code = self._docker.wait(self._container_id)
        logs = self._docker.logs(self._container_id)
        if logs is not None:
            for line in logs:
                # On success, logs are collected when the container is stopped.
                if status_code != 0 and not self._expect_failure:
                    self._logger.error(line)
                elif status_code == 0 and self._expect_failure:
                    self._logger.error(line)
                else:
                    self._logger.debug(line)

        if status_code == 0 and not self._expect_failure:
            self.stop()
            return True
        elif status_code != 0 and self._expect_failure:
            self.stop()
            return True

        if self._expect_failure and status_code == 0:
            self._logger.error('Expected a failed status code but got "0"')
        else:
            self._logger.error('Command failed while waiting for '
                               f'exit with status code: {status_code}')
        return False

    def stop(self) -> bool:
        """Stop a running container

        Stops the container and removes it, including its volumes.

        Returns
        -------
        success : bool
            Whether stopping the container was successfull or not.
        """

        if self._container_id is None:
            self._logger.error('Container is not initialized yet')
            return False

        self._docker.stop(self._container_id)
        return True
