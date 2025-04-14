import sys
import time
import os
import tempfile
import asyncio
import json
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional


class Lean:
    def __init__(self,
                 elan_home: Optional[str] = None,
                 repl_path: Optional[str] = None,
                 log_file=tempfile.mkstemp(suffix='.log', text=True)[1],
                 default_timeout=120):
        if elan_home is not None:
            os.environ['ELAN_HOME'] = os.path.abspath(elan_home)

        if repl_path is not None:
            os.environ['REPL_PATH'] = os.path.abspath(repl_path)

        self.log_file = log_file
        handler = RotatingFileHandler(self.log_file, maxBytes=1024 * 1024, backupCount=3, encoding='utf-8')
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[handler])
        print(f'logging file is at: {self.log_file}')

        self.default_timeout = default_timeout
        self._loop = asyncio.new_event_loop()

    @staticmethod
    async def call_repl(kwargs):
        start_time = time.time()
        script_path = os.path.join(os.path.dirname(__file__), 'repl')
        if sys.platform == 'win32':
            script_path += '.bat'
            process = await asyncio.create_subprocess_shell(
                f'{script_path} {json.dumps(kwargs)}', stdout=asyncio.subprocess.PIPE)
        else:
            script_path += '.sh'
            process = await asyncio.create_subprocess_exec(
                script_path, json.dumps(kwargs), stdout=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        stdout = stdout.decode('utf-8')
        logging.info(f'keyword arguments: {kwargs}')
        logging.info(f'response: {stdout}')
        response = json.loads(stdout)
        messages = response['messages'] if 'messages' in response.keys() else []
        response_time = time.time() - start_time
        return messages, response_time

    async def call_repl_with_timeout(self, kwargs, timeout):
        try:
            messages, response_time = await asyncio.wait_for(self.call_repl(kwargs), timeout=timeout)
            return False, messages, response_time
        except asyncio.TimeoutError:
            return True, None, timeout

    def send_args(self, args, enable_timeout=True, timeout=None):
        if enable_timeout:
            if timeout is None:
                timeout = self.default_timeout
            is_timeout, messages, response_time = self._loop.run_until_complete(
                self.call_repl_with_timeout(args, timeout))
            if is_timeout:
                error_text = f'Lean REPL timeout with {timeout}s.'
                print(error_text)
                logging.error(error_text)
                return None, response_time
        else:
            messages, response_time = self._loop.run_until_complete(self.call_repl(args))
        return messages, response_time

    def command_mode(self, cmd, **kwargs):
        args = {'cmd': cmd}
        args.update(**kwargs)
        return self.send_args(args)

    def file_mode(self, file_path, **kwargs):
        args = {'path': os.path.abspath(file_path)}
        args.update(**kwargs)
        return self.send_args(args)


if __name__ == '__main__':
    tp = Lean()
    messages, _ = tp.command_mode('def f := 2\nexample : f = 2 := rfl')
    print(messages)
    messages, _ = tp.file_mode('../test.lean')
    print(messages)
