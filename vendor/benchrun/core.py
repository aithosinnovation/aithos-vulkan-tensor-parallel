"""Recorded-result adapters and deterministic reports (standard library only)."""
import hashlib
import json
import math
import re
from pathlib import Path
import stat

from . import __version__

MAX_INPUT_BYTES = 64 * 1024 * 1024


class InvalidInput(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False,
                      allow_nan=False) + "\n"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidInput(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_bytes(path):
    path = Path(path)
    # Refuse special files before open, so FIFOs and /dev/zero cannot block.
    info = path.stat()
    if not stat.S_ISREG(info.st_mode):
        raise InvalidInput(f"{path.name}: input must be a regular file")
    if info.st_size > MAX_INPUT_BYTES:
        raise InvalidInput(f"{path.name}: input exceeds {MAX_INPUT_BYTES} bytes")
    with path.open('rb') as stream:
        data = stream.read(MAX_INPUT_BYTES + 1)
    if len(data) > MAX_INPUT_BYTES:
        raise InvalidInput(f"{path.name}: input exceeds {MAX_INPUT_BYTES} bytes")
    return data


def parse_json(data, label):
    if not isinstance(data, bytes) or len(data) > MAX_INPUT_BYTES:
        raise InvalidInput(f"{label}: requires bytes up to {MAX_INPUT_BYTES} bytes")
    try:
        value = json.loads(data, object_pairs_hook=_pairs,
                           parse_constant=lambda x: (_ for _ in ()).throw(
                               InvalidInput(f"non-finite JSON value: {x}")))
        canonical(value).encode('utf-8')
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise InvalidInput(f"{label}: invalid JSON: {exc}") from exc
    return value


def number(value, label, integer=False, positive=False):
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise InvalidInput(f"{label} must be a number")
    try:
        valid = math.isfinite(value) and value >= 0
    except OverflowError:
        valid = False
    if not valid or (integer and not isinstance(value, int)) or (positive and value == 0):
        raise InvalidInput(f"{label} must be a finite {'positive' if positive else 'nonnegative'} {'integer' if integer else 'number'}")
    return value


def _check_rate(reported, computed, label, warnings):
    if not math.isfinite(computed):
        warnings.append(f"{label}: computed rate overflow; input timings require inspection.")
    elif not math.isclose(reported, computed, rel_tol=0.01, abs_tol=1e-9):
        warnings.append(f"{label}: reported rate {reported:g} differs from timing-derived {computed:g} tokens/s by more than 1%.")


def bench_records(raw, warnings):
    if not isinstance(raw, list) or not raw:
        raise InvalidInput("llama-bench input must be a nonempty JSON array")
    records = []
    for index, row in enumerate(raw):
        if not isinstance(row, dict):
            raise InvalidInput(f"row {index} must be an object")
        p = number(row.get("n_prompt"), f"row {index}.n_prompt", integer=True)
        n = number(row.get("n_gen"), f"row {index}.n_gen", integer=True)
        if p + n == 0:
            raise InvalidInput(f"row {index} has no prompt or generation tokens")
        rate = number(row.get("avg_ts"), f"row {index}.avg_ts", positive=True)
        for key in ("stddev_ts", "avg_ns", "stddev_ns"):
            if key in row:
                number(row[key], f"row {index}.{key}")
        for key in ("samples_ns", "samples_ts"):
            if key in row:
                if not isinstance(row[key], list) or not row[key]:
                    raise InvalidInput(f"{key} must be a nonempty array")
                for sample in row[key]:
                    number(sample, key, integer=key == 'samples_ns', positive=True)
        if row.get('samples_ns'):
            rates = [(p + n) * 1e9 / ns for ns in row['samples_ns']]
            _check_rate(rate, sum(rates) / len(rates), f"row {index}", warnings)
        if row.get('samples_ts'):
            _check_rate(rate, sum(row['samples_ts']) / len(row['samples_ts']), f"row {index} samples_ts", warnings)
        known = {"model_filename", "model_type", "model_size", "model_n_params",
                 "build_commit", "build_number", "cpu_info", "gpu_info", "backends",
                 "avg_ts", "stddev_ts", "avg_ns", "stddev_ns", "samples_ns", "samples_ts", "test_time"}
        records.append({
            "kind": "prompt" if n == 0 else "generation" if p == 0 else "combined",
            "kind_origin": "derived_from_token_counts",
            "metrics": {"tokens_per_second": rate,
                        "stddev_tokens_per_second": row.get("stddev_ts"),
                        "samples_ns": row.get("samples_ns"), "samples_ts": row.get("samples_ts")},
            "model": {k: row.get(k) for k in ("model_filename", "model_type", "model_size", "model_n_params")},
            "software": {k: row.get(k) for k in ("build_commit", "build_number", "backends")},
            "hardware": {k: row.get(k) for k in ("cpu_info", "gpu_info")},
            "parameters": {k: v for k, v in row.items() if k not in known},
            "benchmark_time": row.get("test_time"),
        })
    return records


def server_records(raw, warnings):
    if not isinstance(raw, dict) or not isinstance(raw.get("timings"), dict):
        raise InvalidInput("llama-server response requires a timings object")
    timings = raw["timings"]
    cache = timings.get('cache_n')
    if cache is not None:
        number(cache, 'cache_n', integer=True)
        if cache > 0:
            warnings.append(f"llama-server reused {cache} cached prompt tokens; prompt throughput excludes cached work.")
    records = []
    for kind, prefix in (("prompt", "prompt"), ("generation", "predicted")):
        count = number(timings.get(prefix + "_n"), prefix + "_n", integer=True)
        speed = timings.get(prefix + "_per_second")
        duration = number(timings.get(prefix + "_ms"), prefix + "_ms", positive=count > 0)
        if count == 0:
            if speed is not None:
                number(speed, prefix + '_per_second')
            speed = None
            reason = 'No uncached prompt tokens timed' if kind == 'prompt' else 'No generation tokens timed'
        else:
            speed = number(speed, prefix + "_per_second", positive=True)
            _check_rate(speed, count * 1000 / duration, prefix, warnings)
            reason = None
        records.append({"kind": kind, "model": {"model_filename": raw.get("model")},
                        "software": {"system_fingerprint": raw.get("system_fingerprint")},
                        "hardware": {}, "parameters": {"tokens": count, "cache_n": cache},
                        "benchmark_time": raw.get("created"),
                        "metrics": {"tokens_per_second": speed, "duration_ms": duration,
                                    "unavailable_reason": reason}})
    return records


ADAPTERS = {"llama-bench": bench_records, "llama-server": server_records}


def seal(report):
    report.pop('content_id', None)
    report['content_id'] = digest(canonical(report).encode('utf-8'))
    return report


def has_sample_marker(value):
    if isinstance(value, str):
        return bool(re.search(r'\bsample\b', value, re.IGNORECASE))
    if isinstance(value, dict):
        return any(has_sample_marker(x) for x in value.values())
    if isinstance(value, list):
        return any(has_sample_marker(x) for x in value)
    return False


def build_report(raw_bytes, metadata_bytes, adapter, data_kind, stderr_bytes=None):
    """Parse and hash the same bytes; callers cannot supply detached hashes."""
    raw = parse_json(raw_bytes, 'input')
    metadata = parse_json(metadata_bytes, 'metadata')
    if not isinstance(metadata, dict):
        raise InvalidInput("metadata must be an object")
    for section in ("model", "software", "hardware", "execution", "telemetry"):
        if section in metadata and not isinstance(metadata[section], dict):
            raise InvalidInput(f"metadata.{section} must be an object")
    if data_kind not in ("sample", "recorded") or adapter not in ADAPTERS:
        raise InvalidInput("unsupported data kind or adapter")
    warnings = []
    records = ADAPTERS[adapter](raw, warnings)
    for section, field in (("model", "sha256"), ("software", "build_flags"),
                           ("software", "commit"), ("hardware", "os"), ("execution", "argv")):
        if not metadata.get(section, {}).get(field):
            warnings.append(f"Benchmark metadata missing {section}.{field}; do not infer from import host.")
    if not metadata.get('telemetry'):
        warnings.append('No benchmark-time telemetry supplied.')
    checksum = metadata.get("model", {}).get("sha256")
    if checksum is not None and (not isinstance(checksum, str) or len(checksum) != 64
                                or any(c not in "0123456789abcdef" for c in checksum)):
        raise InvalidInput("model.sha256 must be a lowercase 64-character SHA-256 or null")
    execution = metadata.get('execution', {})
    argv = execution.get("argv")
    if argv is not None and (not isinstance(argv, list) or not all(isinstance(x, str) for x in argv)):
        raise InvalidInput("execution.argv must be an array of strings")
    repetitions = execution.get('repetitions')
    if repetitions is not None:
        number(repetitions, 'execution.repetitions', integer=True, positive=True)
        for i, record in enumerate(records):
            samples = record['metrics'].get('samples_ns')
            if samples and len(samples) != repetitions:
                warnings.append(f'row {i}: sample count differs from declared repetitions.')
    if data_kind == "sample":
        warnings.insert(0, "SAMPLE DATA: illustrative fixture, not measured hardware performance.")
    elif has_sample_marker([metadata, records]):
        warnings.insert(0, 'Recorded label conflicts with SAMPLE markers; authenticity requires inspection.')
    for record in records:
        record['data_kind'] = data_kind
    from .measure import phase_measurements
    measurements, loading, stderr_hash = phase_measurements(raw, records, metadata, stderr_bytes, warnings)
    return seal({"schema_version": 2, "benchrun_version": __version__,
                 "data_kind": data_kind, "adapter": adapter,
                 "provenance": {"input_sha256": digest(raw_bytes), "metadata_sha256": digest(metadata_bytes),
                                "metadata_origin": "user_supplied", "record_origin": "input_json", "stderr_sha256": stderr_hash,
                                "stderr_origin": "user_supplied_unverified_pairing" if stderr_bytes is not None else None},
                 "benchmark_metadata": metadata, "measurements": measurements,
                 "loading_configuration": loading, "records": records, "raw_results": raw,
                 "import_host_snapshot": None, "warnings": warnings})


def attach_snapshot(report, host_snapshot):
    report['import_host_snapshot'] = host_snapshot
    report['warnings'].append('Import-host snapshot is NOT benchmark-time hardware or telemetry.')
    return seal(report)


def summary(report):
    lines = ["# benchrun report", ""]
    if report['data_kind'] == 'sample':
        lines.extend(['**SAMPLE DATA — not measured hardware performance.**', ''])
    lines.extend([f"Data: {report['data_kind']}", f"Adapter: {report['adapter']}",
                  f"Content ID: {report['content_id']}", ""])
    phase = report.get('measurements', {})
    lines.extend(['## Phase measurements', ''])
    for title, key in [('Model loading', 'model_loading'), ('Total execution', 'total_execution')]:
        data = phase.get(key, {})
        value = data.get('seconds')
        display = f"{value:.6f} s" if value is not None else 'unavailable'
        lines.append(f"- {title}: {display}; source: {data.get('source', 'unavailable')}")
    proxy = phase.get('engine_load_timer', {})
    proxy_value = proxy.get('first_configuration_seconds')
    proxy_display = f'{proxy_value:.6f} s' if proxy_value is not None else 'unavailable/unattributed'
    lines.extend(['- Engine startup proxy (model start through first eval): ' + proxy_display,
                  '', proxy.get('definition', ''),
                  'Loading-only time remains unavailable without a separate supplied observation. These timers are not additive. Prompt/generation rates are producer-timed records, not end-to-end throughput.', '',
                  '## Loading configuration', '', '```json', canonical(report.get('loading_configuration', {})).rstrip(), '```', ''])
    for index, record in enumerate(report["records"], 1):
        model = json.dumps(record["model"].get("model_filename"), ensure_ascii=True)
        rate = record['metrics']['tokens_per_second']
        display = f'{rate:.3f} tokens/s' if rate is not None else 'unavailable (zero timed tokens)'
        lines.append(f"{index}. [{record['data_kind']}] {record['kind']}: {display}; model {model}")
        for label in ('software', 'hardware', 'parameters'):
            lines.append(f'   {label}: ' + json.dumps(record[label], sort_keys=True, ensure_ascii=True))
    for section in ("model", "software", "hardware", "execution", "telemetry"):
        lines.extend(["", f"## Benchmark {section}", "", "```json",
                      canonical(report["benchmark_metadata"].get(section, {})).rstrip(), "```"])
    if report.get("import_host_snapshot"):
        snap = report["import_host_snapshot"]
        lines.extend(["", "## Import host (not benchmark environment)", "",
                      "```json", canonical(snap).rstrip(), "```", "Full inventory and point-in-time telemetry are in result.json."])
    lines.extend(["", "## Limitations", ""] + ["- " + x for x in report["warnings"]])
    return "\n".join(lines) + "\n"
