"""Best-effort read-only import-host snapshot. Never runs a benchmark."""
import csv
from datetime import datetime, timezone
from pathlib import Path
import platform
import shutil
import subprocess
import os


def _text(value):
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='replace')
    return value or ''


def probe(argv, timeout=3):
    try:
        result = subprocess.run(argv, capture_output=True, text=True, errors='replace',
                                timeout=timeout, check=False, shell=False)
        return {"status": "ok" if result.returncode == 0 else "error",
                "argv": argv, "timeout_seconds": timeout, "returncode": result.returncode,
                "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}
    except subprocess.TimeoutExpired as exc:
        return {"status": "unavailable", "argv": argv, "reason": 'TimeoutExpired',
                "timeout_seconds": timeout, "stdout": _text(exc.stdout), "stderr": _text(exc.stderr)}
    except (OSError, ValueError) as exc:
        return {"status": "unavailable", "argv": argv, "reason": type(exc).__name__,
                "timeout_seconds": timeout}


def pci_gpus(root=Path('/sys/bus/pci/devices')):
    devices = []
    for path in sorted(root.glob('*')):
        try:
            cls = (path / 'class').read_text().strip()
            if not cls.startswith('0x03'):
                continue
            devices.append({"pci_address": path.name,
                            "vendor_id": (path / 'vendor').read_text().strip(),
                            "device_id": (path / 'device').read_text().strip(),
                            "driver": (path / 'driver').resolve().name if (path / 'driver').exists() else None,
                            "virtual": (path / 'vendor').read_text().strip() == '0x1414'})
        except (OSError, RuntimeError):
            continue
    return devices


def snapshot():
    release = platform.release()
    result = {"observed_at": datetime.now(timezone.utc).isoformat(),
              "system": platform.system(), "release": release,
              "environment": "WSL" if 'microsoft' in release.lower() else platform.system(),
              "machine": platform.machine(), "python_version": platform.python_version(),
              "cpu": {"logical_count": os.cpu_count(), "model": platform.processor() or None},
              "memory_total_bytes": None, "pci_display_devices": pci_gpus(),
              "telemetry_scope": "single import-time observation, not a benchmark time series"}
    try:
        for line in Path('/proc/cpuinfo').read_text().splitlines():
            if line.startswith('model name'):
                result['cpu']['model'] = line.split(':', 1)[1].strip()
                break
    except (OSError, ValueError):
        pass
    try:
        for line in Path('/proc/meminfo').read_text().splitlines():
            if line.startswith('MemTotal:'):
                result['memory_total_bytes'] = int(line.split()[1]) * 1024
    except (OSError, ValueError):
        pass
    executable = shutil.which('nvidia-smi')
    if executable:
        fields = ['name', 'uuid', 'driver_version', 'memory.total', 'memory.used',
                  'temperature.gpu', 'utilization.gpu', 'power.draw']
        obs = probe([executable, '--query-gpu=' + ','.join(fields), '--format=csv,noheader,nounits'])
        obs['units'] = {'memory.total': 'MiB', 'memory.used': 'MiB', 'temperature.gpu': 'C',
                        'utilization.gpu': 'percent', 'power.draw': 'W'}
        obs['devices'] = []
        if obs['status'] == 'ok':
            rows = list(csv.reader(obs['stdout'].splitlines(), skipinitialspace=True))
            if not rows or any(len(row) != len(fields) for row in rows):
                obs['status'] = 'error'
                obs['reason'] = 'unexpected nvidia-smi CSV shape'
            else:
                obs['devices'] = [dict(zip(fields, (x.strip() for x in row))) for row in rows]
        result['nvidia'] = obs
    else:
        result['nvidia'] = {'status': 'unavailable', 'reason': 'nvidia-smi not on PATH'}
    result['intel'] = {'status': 'unavailable',
                       'reason': 'Intel telemetry adapter not implemented; PCI inventory may be incomplete under WSL'}
    return result


def safe_snapshot():
    try:
        return snapshot()
    except Exception as exc:
        # Optional diagnostics must not discard an otherwise valid benchmark.
        return {'status': 'error', 'reason': type(exc).__name__,
                'observed_at': datetime.now(timezone.utc).isoformat()}
