import sys
import time
import os
import tempfile
import asyncio
import json
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional


class Isabelle:
    def __init__(self,
                 isabelle_path: Optional[str] = None,
                 server_name='test',
                 log_file=tempfile.mkstemp(suffix='.log', text=True)[1],
                 default_session='HOL',
                 default_timeout=120,
                 verbose=True):
        if isabelle_path is not None:
            self.isabelle_path = os.path.abspath(isabelle_path)
            os.environ['ISABELLE_DIRPATH'] = self.isabelle_path
        else:
            self.isabelle_path = os.environ['ISABELLE_DIRPATH']

        self.log_file = log_file
        handler = RotatingFileHandler(self.log_file, maxBytes=1024 * 1024, backupCount=3)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[handler])
        print(f'logging file is at: {self.log_file}')

        self.server_name = server_name
        self.default_session = default_session
        self.session_ids = []
        self.running = True
        self.default_timeout = default_timeout
        self.verbose = verbose

        self._loop = asyncio.new_event_loop()

        self._loop.run_until_complete(self._init_isabelle_server())
        self.session_start()

    async def _init_isabelle_server(self):
        args = ['server', '-n', self.server_name]
        start_time = time.time()
        if sys.platform == 'win32':
            process = await asyncio.create_subprocess_exec(
                os.path.join(os.path.dirname(__file__), 'Cygwin-Server.bat'),
                *args, stdout=asyncio.subprocess.PIPE)
        else:
            process = await asyncio.create_subprocess_exec(
                os.path.join(self.isabelle_path, 'bin/isabelle'),
                *args, stdout=asyncio.subprocess.PIPE)

        self.process = process

        if self.process.stdout is not None:
            server_info = await self.process.stdout.readline()
            server_info = server_info.decode('utf-8')
            info_text = f'Isabelle server started with info: {server_info} in {time.time() - start_time:.2f}s.'
            print(info_text)
            logging.info(info_text)
            self.address, self.port = server_info.split()[3].split(':')
            self.port = int(self.port)
            self.password = server_info.split()[-1][1:-2]
        else:
            await self.process_terminate()
            self.running = False
            error_text = 'Isabelle server did not start as expected.'
            logging.error(error_text)
            raise ValueError(error_text)

    async def send_server_command(self, cmd):
        start_time = time.time()
        reader, writer = await asyncio.open_connection(self.address, self.port)
        command = self.password + '\n' + cmd + '\n'
        writer.write(command.encode('utf-8'))
        await writer.drain()
        logging.info(cmd + '\n')

        responses = []

        if cmd == 'shutdown':
            line = await reader.readline()
            line = line.decode('utf-8').rstrip()
            logging.info(line)

        else:
            ok_count = 0
            read_bytes = False
            num_bytes = 0
            while True:
                if read_bytes:
                    line = await reader.readexactly(num_bytes)
                    read_bytes = False
                else:
                    line = await reader.readline()
                line = line.decode('utf-8').rstrip()
                if not line:
                    break

                tag = line.split()[0]
                if tag.isdigit():
                    read_bytes = True
                    num_bytes = int(tag)
                    if self.verbose:
                        logging.info(line)

                elif tag == 'OK':
                    logging.info(line)
                    if line == 'OK':
                        response = ''
                        responses.append((tag, response))
                        break
                    ok_count += 1
                    if ok_count > 1:
                        if 'echo' in cmd or 'help' in cmd:
                            response = line[len(tag) + 1:]
                            responses.append((tag, response))
                            break
                        else:
                            response = json.loads(line[len(tag) + 1:])
                            responses.append((tag, response))
                            if 'purge_theories' in cmd:
                                break

                elif tag in ['NOTE', 'FINISHED', 'FAILED', 'ERROR']:
                    if self.verbose or tag != 'NOTE':
                        logging.info(line)

                    if len(line) - len(tag) < 2:
                        error_text = f'Isabelle server did not respond as expected. Message:{line}'
                        print(error_text)
                        logging.error(error_text)
                        responses.append(('', line))
                        break
                    else:
                        if line[len(tag) + 1] == '{' and line[-1] == '}':
                            response = json.loads(line[len(tag)+1:])
                            responses.append((tag, response))
                            if tag != 'NOTE':
                                break
                        elif tag == 'ERROR' and line[len(tag) + 1] == '\"' and line[-1] == '\"':
                            response = line[len(tag) + 1:]
                            responses.append((tag, response))
                            break
                        else:
                            error_text = f'Isabelle server did not respond as expected. Message:{line}'
                            print(error_text)
                            logging.error(error_text)
                            responses.append(('', line))
                            break

                else:
                    error_text = f'Isabelle server did not respond as expected. Message:{line}'
                    print(error_text)
                    logging.error(error_text)
                    responses.append(('', line))
                    break

        writer.close()
        await writer.wait_closed()
        response_time = time.time() - start_time
        return responses, response_time

    async def send_server_command_with_timeout(self, cmd, timeout):
        try:
            responses, response_time = await asyncio.wait_for(self.send_server_command(cmd), timeout=timeout)
            return False, responses, response_time
        except asyncio.TimeoutError:
            return True, [], timeout

    def session_start(self, session=None):
        args = {'session': session if session is not None else self.default_session}
        cmd = 'session_start ' + json.dumps(args)
        responses, response_time = self._loop.run_until_complete(self.send_server_command(cmd))
        last_response = responses[-1]
        if last_response[0] == 'FINISHED':
            session_id = last_response[1]['session_id']
            self.session_ids.append(session_id)
            info_text = f'Isabelle server session {session_id} started in {response_time:.2f}s.'
            print(info_text)
            logging.info(info_text)
        else:
            error_text = f'Isabelle server session_start failed with response: {last_response}.'
            print(error_text)
            logging.error(error_text)

    def session_stop(self, session_id=None):
        if not self.session_ids:
            print('No running sessions on Isabelle server.')
            return
        if session_id is not None:
            if session_id not in self.session_ids:
                print(f'Session {session_id} is not running on Isabelle server.')
                return
            self.session_ids.pop(self.session_ids.index(session_id))
        else:
            session_id = self.session_ids.pop(-1)
        args = {'session_id': session_id}

        cmd = 'session_stop ' + json.dumps(args)
        responses, response_time = self._loop.run_until_complete(self.send_server_command(cmd))
        last_response = responses[-1]
        if last_response[0] == 'FINISHED':
            info_text = f'Isabelle server session {session_id} ended in {response_time:.2f}s.'
            print(info_text)
            logging.info(info_text)

        elif last_response[0] == 'FAILED':
            warning_text = f'Isabelle server session_stop session {session_id} ended with response: {last_response}.'
            print(warning_text)
            logging.warning(warning_text)

        else:
            error_text = f'Isabelle server session_stop failed with response: {last_response}.'
            print(error_text)
            logging.error(error_text)

    def cancel_task(self, task_id):
        args = {'task': task_id}
        cmd = 'cancel ' + json.dumps(args)
        responses, response_time = self._loop.run_until_complete(self.send_server_command(cmd))
        last_response = responses[-1]
        info_text = f'Isabelle server cancel {task_id} in {response_time:.2f}s. Message: {last_response}'
        print(info_text)
        logging.info(info_text)

    def purge_theories(self, theories, session_id=None, master_dir=None):
        if not self.session_ids:
            print('No running sessions on Isabelle server.')
            return
        args = {'theories': theories}
        if session_id is not None:
            if session_id not in self.session_ids:
                print(f'Session {session_id} is not running on Isabelle server.')
                return
        else:
            session_id = self.session_ids[-1]
        args['session_id'] = session_id
        if master_dir is not None:
            args['master_dir'] = master_dir
        cmd = 'purge_theories ' + json.dumps(args)
        responses, response_time = self._loop.run_until_complete(self.send_server_command(cmd))
        last_response = responses[-1]
        info_text = f'Isabelle server purge_theories in {response_time:.2f}s. Message: {last_response}'
        print(info_text)
        logging.info(info_text)

    def _use_theories(self, theories, session_id=None, master_dir=None, enable_timeout=True, timeout=None):
        if not self.session_ids:
            print('No running sessions on Isabelle server.')
            return None, 0
        args = {'theories': theories}
        if session_id is not None:
            if session_id not in self.session_ids:
                print(f'Session {session_id} is not running on Isabelle server.')
                return None, 0
        else:
            session_id = self.session_ids[-1]
        args['session_id'] = session_id
        if master_dir is not None:
            args['master_dir'] = master_dir
        cmd = 'use_theories ' + json.dumps(args)
        if enable_timeout:
            if timeout is None:
                timeout = self.default_timeout
            is_timeout, responses, response_time = self._loop.run_until_complete(
                self.send_server_command_with_timeout(cmd, timeout))
            if is_timeout:
                error_text = f'Isabelle server use_theory timeout with {timeout}s.'
                print(error_text)
                logging.error(error_text)
                self.restart()
                return None, response_time
        else:
            responses, response_time = self._loop.run_until_complete(
                self.send_server_command(cmd))

        last_response = responses[-1]
        if last_response[0] == 'FINISHED':
            info_text = f'Isabelle server use_theory ended in {response_time:.2f}s.'
            if self.verbose:
                print(info_text)
            logging.info(info_text)
            return last_response, response_time
        else:
            error_text = f'Isabelle server use_theory failed with response: {last_response}.'
            print(error_text)
            logging.error(error_text)
            return None, response_time

    def use_theories(self, *args, **kwargs):
        try:
            return self._use_theories(*args, **kwargs)
        except KeyboardInterrupt:
            print('KeyboardInterrupt detected. Terminate the Isabelle server.')
            self.terminate()
            self.running = False
            sys.exit(130)

    async def process_terminate(self):
        if self.process.returncode is None:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.communicate(), timeout=10)
            except asyncio.TimeoutError:
                print('Timeout during process termination! Force to kill the process.')
                self.process.kill()
                await self.process.communicate()

    def shutdown_server_and_process(self):
        async def check_shutdown(address, port):
            await asyncio.sleep(2)
            try:
                await asyncio.wait_for(asyncio.open_connection(address, port), timeout=5)
                warning_text = f'Isabelle server {address}:{port} might not shutdown and still respond.'
                print(warning_text)
                logging.warning(warning_text)
            except ConnectionRefusedError:
                info_text = f'Isabelle server {address}:{port} shutdown.'
                print(info_text)
                logging.info(info_text)
            except asyncio.TimeoutError:
                warning_text = f'Isabelle server {address}:{port} might not shutdown and not respond.'
                print(warning_text)
                logging.warning(warning_text)

        self._loop.run_until_complete(self.send_server_command('shutdown'))
        self._loop.run_until_complete(check_shutdown(self.address, self.port))
        self._loop.run_until_complete(self.process_terminate())
        self.session_ids = []

    def restart(self):
        self.shutdown_server_and_process()
        self._loop.run_until_complete(self._init_isabelle_server())
        self.session_start()

    def terminate(self):
        self.shutdown_server_and_process()
        self._loop.close()


if __name__ == '__main__':
    tp = Isabelle(default_session='HOL')
    tp.session_start('random')
    tp.session_stop()
    tp.session_stop()
    tp.session_start('HOL')
    tp.cancel_task('123')
    tp.purge_theories(["HOL-Unix.Unix"])
    response, response_time = tp.use_theories(["HOL-Unix.Unix"])
    print(response[0] if response is not None else response)
    print(f'{response_time}s')
    tp.purge_theories(["HOL-Unix.Unix"])
    response, response_time = tp.use_theories(["HOL-Unix.Uni"])
    print(response[0] if response is not None else response)
    print(f'{response_time}s')
    response, response_time = tp.use_theories(["HOL-Unix.Unix"], session_id='12122121')
    print(response[0] if response is not None else response)
    print(f'{response_time}s')
    response, response_time = tp.use_theories(["HOL-Matrix_LP.Matrix"])
    print(response[0] if response is not None else response)
    print(f'{response_time}s')
    response, response_time = tp.use_theories(["HOL-Probability.Probability"])
    print(response[0] if response is not None else response)
    print(f'{response_time}s')

    if tp.running:
        tp.terminate()
