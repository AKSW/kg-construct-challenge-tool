"""
RPT is a general purpose RDF tool

**Website**: https://github.com/SmartDataAnalytics/RdfProcessingToolkit

"""

VERSION='1.9.7-SNAPSHOT'
TIMEOUT = 6 * 3600  # 6 hours

import os
import shlex
from timeout_decorator import timeout, TimeoutError  # type: ignore
from bench_executor.container import Container
from bench_executor.logger import Logger


class Rpt(Container):
    """RPT container for executing rmltk, sansa etc."""

    _INSTANCES = 0

    def __init__(self, data_path: str, config_path: str, directory: str,
                 verbose: bool):
        self._instance = Rpt._INSTANCES
        Rpt._INSTANCES = Rpt._INSTANCES + 1

        self._data_path = os.path.abspath(data_path)
        self._config_path = os.path.abspath(config_path)
        self._logger = Logger(__name__ + '.' + str(self._instance), directory, verbose)
        self._verbose = verbose

        os.makedirs(os.path.join(self._data_path, 'rpt'), exist_ok=True)
        super().__init__(f'aksw/rpt:{VERSION}', 'rpt' + '-' + str(self._instance),
                         self._logger,
                         volumes=[f'{self._data_path}/rpt:/data',
                                  f'{self._data_path}/shared:/data/shared'])

    @timeout(TIMEOUT)
    def _execute_with_timeout(self, arguments: list, *, working_dir=None) -> bool:
        """Execute a mapping with a provided timeout.

        Returns
        -------
        success : bool
            Whether the execution was successfull or not.
        """
        return self.run_and_wait_for_exit(' '.join(map(shlex.quote, arguments)),
                                          working_dir=working_dir)

    def execute(self, command, arguments=None, working_dir='/data/shared') -> bool:
        """Execute rpt with given arguments.

        Parameters
        ----------
        command : str
            Command to run
        arguments : list
            Arguments to supply to rpt.

        Returns
        -------
        success : bool
            Whether the execution succeeded or not.
        """
        if arguments is None:
            arguments = []
        self._logger.debug(f'{self._instance}: Calling rpt {command} with {arguments!r}')
        try:
            result = self._execute_with_timeout([*command.split(' '), *arguments],
                                                working_dir=working_dir)
            self.stop()
            return result
        except TimeoutError:
            msg = f'{self._instance}: Timeout ({TIMEOUT}s) reached for rpt'
            self._logger.warning(msg)

        return False

    def execute_capture(self, command, output, arguments=None, working_dir='/data/shared') -> bool:
        """Execute rpt with given arguments and save the result.

        Parameters
        ----------
        command : str
            Command to run
        output : str
            Filename to save the output to.
        arguments : list
            Arguments to supply to rpt.

        Returns
        -------
        success : bool
            Whether the execution succeeded or not.
        """
        if arguments is None:
            arguments = []
        self._logger.debug(f'{self._instance}: Calling rpt {command} with {arguments!r}')
        try:
            result = self._execute_with_timeout([*command.split(' '), *arguments],
                                                working_dir=working_dir)
            if result:
                if not output.startswith('/'):
                    output = working_dir + '/' + output
                if output.startswith('/data/shared'):
                    output = self._data_path + output.removeprefix('/data')
                else:
                    output = self._data_path + '/rpt' + output.removeprefix('/data')
                with open(output, 'wb') as outf:
                    for line in self._container.logs(stdout=True, stream=True):
                        outf.write(line)

            self.stop()
            return result
        except TimeoutError:
            msg = f'{self._instance}: Timeout ({TIMEOUT}s) reached for rpt'
            self._logger.warning(msg)

        return False
