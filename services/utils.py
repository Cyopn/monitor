"""
Cross-platform service management utilities
"""
import os
import sys
import subprocess
import signal
import time
import shutil
import re
import threading
import psutil
from typing import Optional, Tuple


ANSI_ESCAPE_RE = re.compile(rb'\x1B(?:\[[0-?]*[ -/]*[@-~])')


def is_process_running(pid: int) -> bool:
    """Check if a process with given PID is running"""
    try:
        process = psutil.Process(pid)
        return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
    except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
        return False


def terminate_process(pid: int, timeout: int = 5) -> bool:
    """Terminate a process gracefully, then forcefully if needed"""
    try:
        if sys.platform == 'win32':
            # Windows: use taskkill
            subprocess.run(
                ['taskkill', '/T', '/PID', str(pid)],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            # Wait for graceful termination
            time.sleep(1)
            if is_process_running(pid):
                # Force kill
                subprocess.run(
                    ['taskkill', '/F', '/T', '/PID', str(pid)],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
        else:
            # Linux and other Unix systems: terminate the process group.
            try:
                os.killpg(os.getpgid(pid), signal.SIGTERM)
                for _ in range(timeout):
                    if not is_process_running(pid):
                        return True
                    time.sleep(1)
                os.killpg(os.getpgid(pid), signal.SIGKILL)
            except ProcessLookupError:
                return True

        # Check if process is still running
        return not is_process_running(pid)
    except Exception:
        return False


def terminate_process_group(pgid: int, timeout: int = 5) -> bool:
    """Terminate an entire process group"""
    try:
        if sys.platform == 'win32':
            # Windows: taskkill doesn't have direct process group support
            # We'll need to find child processes manually
            try:
                parent = psutil.Process(pgid)
                children = parent.children(recursive=True)
                for child in children:
                    terminate_process(child.pid, timeout)
                terminate_process(pgid, timeout)
                return True
            except psutil.NoSuchProcess:
                return True
        else:
            # Unix/Linux: kill the process group
            try:
                os.killpg(pgid, signal.SIGTERM)
                # Wait for graceful termination
                for _ in range(timeout):
                    if not is_process_running(pgid):
                        return True
                    time.sleep(1)
                # Force kill
                os.killpg(pgid, signal.SIGKILL)
                return True
            except ProcessLookupError:
                return True
    except Exception:
        return False


def get_process_info(pid: int) -> Optional[dict]:
    """Get information about a process"""
    try:
        proc = psutil.Process(pid)
        return {
            'pid': proc.pid,
            'name': proc.name(),
            'status': proc.status(),
            'cpu_percent': proc.cpu_percent(interval=0.05),
            'memory_percent': proc.memory_percent(),
            'memory_bytes': proc.memory_info().rss,
            'create_time': proc.create_time(),
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


def get_system_resources() -> dict:
    """Return host resource usage in a platform-independent format."""
    memory = psutil.virtual_memory()
    disk = shutil.disk_usage(os.getcwd())
    return {
        'cpu_percent': psutil.cpu_percent(interval=0.1),
        'memory_percent': memory.percent,
        'memory_used_bytes': memory.used,
        'memory_total_bytes': memory.total,
        'disk_percent': (disk.used / disk.total * 100) if disk.total else 0,
        'disk_used_bytes': disk.used,
        'disk_total_bytes': disk.total,
    }


def service_log_path(log_dir: str, service_id: int) -> str:
    """Return the platform-independent log path for a service."""
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, f'service-{service_id}.log')


def read_service_logs(log_path: str, max_bytes: int = 20000) -> str:
    """Read the most recent part of a service log without unbounded I/O."""
    try:
        with open(log_path, 'rb') as log_file:
            log_file.seek(0, os.SEEK_END)
            start = max(0, log_file.tell() - max_bytes)
            log_file.seek(start)
            content = log_file.read()
        text = ANSI_ESCAPE_RE.sub(b'', content).decode(
            'utf-8', errors='replace')
        if start:
            text = text.split('\n', 1)[-1]
        return text
    except FileNotFoundError:
        return ''
    except OSError:
        return 'No se pudieron leer los registros del servicio.'


def _capture_process_output(process: subprocess.Popen, log_path: str) -> None:
    """Write process output without terminal formatting codes."""
    try:
        with open(log_path, 'wb') as log_file:
            for output in iter(process.stdout.readline, b''):
                log_file.write(ANSI_ESCAPE_RE.sub(b'', output))
                log_file.flush()
    finally:
        if process.stdout:
            process.stdout.close()


def start_process(command: str, cwd: str, env: dict = None,
                  log_path: str = None) -> Tuple[bool, Optional[int], str]:
    """Start a process and return success, PID, and message"""
    try:
        if env is None:
            env = os.environ.copy()

        capture_output = log_path is not None
        if log_path:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)

        popen_args = {
            'cwd': cwd,
            'env': env,
            'shell': True,
            'stdout': subprocess.PIPE if capture_output else None,
            'stderr': subprocess.STDOUT,
        }
        if sys.platform == 'win32':
            popen_args['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            popen_args['preexec_fn'] = os.setsid
        proc = subprocess.Popen(command, **popen_args)

        if capture_output:
            threading.Thread(
                target=_capture_process_output,
                args=(proc, log_path),
                daemon=True,
            ).start()

        return True, proc.pid, f"Process started with PID {proc.pid}"
    except Exception as e:
        return False, None, f"Failed to start process: {str(e)}"
