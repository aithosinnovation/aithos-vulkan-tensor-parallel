"""Normalize recorded observations; never choose a loader or run a workload."""
import math
import re

from .core import InvalidInput, MAX_INPUT_BYTES, canonical, digest, number

LOADING_KEYS = ('use_mmap', 'use_direct_io', 'devices', 'main_gpu', 'split_mode',
                'tensor_split', 'n_gpu_layers', 'type_k', 'type_v', 'flash_attn',
                'no_kv_offload', 'tensor_buft_overrides', 'no_op_offload', 'no_host')
ENGINE_DEFINITION = ('Time since model-load start until the context first evaluation completes. '
                     'Includes that evaluation (part of the timed test with --no-warmup); '
                     'later context values can be cumulative from the same model start. '
                     'Not isolated model loading, not additive with prompt/generation time.')


def phase_measurements(raw, records, metadata, stderr_bytes, warnings):
    timing, declared_loading = metadata.get('timing', {}), metadata.get('loading', {})
    if not isinstance(timing, dict) or not isinstance(declared_loading, dict):
        raise InvalidInput('metadata.timing and metadata.loading must be objects')
    for key in ('use_mmap', 'use_direct_io'):
        if key in declared_loading and declared_loading[key] is not None and not isinstance(declared_loading[key], bool):
            raise InvalidInput(f'metadata.loading.{key} must be boolean or null')
    declared_load = timing.get('model_load_seconds')
    if 'model_load_definition' in timing and not isinstance(timing['model_load_definition'], str):
        raise InvalidInput('timing.model_load_definition must be a string')
    if declared_load is not None:
        number(declared_load, 'timing.model_load_seconds')
    total = metadata.get('execution', {}).get('elapsed_seconds')
    if total is not None:
        number(total, 'execution.elapsed_seconds')
    engine_loads, log_hash = [], None
    if stderr_bytes is not None:
        if not isinstance(stderr_bytes, bytes) or len(stderr_bytes) > MAX_INPUT_BYTES:
            raise InvalidInput('stderr must be bytes up to the input size limit')
        log_hash = digest(stderr_bytes)
        text = stderr_bytes.decode('utf-8', errors='replace')
        for index, line in enumerate(text.splitlines(), 1):
            if not re.search(r'llama_perf_context_print:\s+load time\s*=', line):
                continue
            match = re.search(r'load time\s*=\s*(\S+)\s+ms', line)
            try:
                value = float(match.group(1)) / 1000 if match else float('nan')
                number(value, 'stderr engine timer')
            except (ValueError, OverflowError):
                warnings.append(f'Unparseable/nonfinite engine load-time line {index}; observation unavailable.')
                continue
            engine_loads.append(value)
    measurements = {
        'model_loading': {'seconds': declared_load,
                          'source': 'metadata.timing.model_load_seconds' if declared_load is not None else 'unavailable',
                          'definition': timing.get('model_load_definition', 'Independently supplied loading-only observation; boundaries must be documented by capture. Never inferred by subtracting inference or copied from overlapping engine timers.')},
        'engine_load_timer': {'first_configuration_seconds': None,
                             'seconds_since_model_start_by_context': engine_loads,
                             'definition': ENGINE_DEFINITION,
                             'pairing': 'Caller-supplied stderr pairing; hash identifies bytes but does not authenticate same-run origin.'},
        'total_execution': {'seconds': total, 'source': 'metadata.execution.elapsed_seconds' if total is not None else 'unavailable',
                            'definition': 'Captured process wall time; excludes import and optional later host snapshot.'},
        'prompt_processing': [], 'generation': [], 'combined': []}
    producer_loading, signatures = [], set()
    count_matches = bool(engine_loads) and len(engine_loads) == len(records)
    if engine_loads and not count_matches:
        warnings.append('Engine load-timer count differs from producer record count; values cannot be attributed to records/configurations.')
    for index, record in enumerate(records):
        metrics = record['metrics']
        entry = {'record_index': index, 'tokens_per_second': metrics['tokens_per_second'],
                 'timed_seconds': metrics['duration_ms'] / 1000 if metrics.get('duration_ms') is not None else None,
                 'scope': 'producer timed record; separate from process wall time; overlaps engine startup timer when first eval is timed'}
        if isinstance(raw, list):
            row = raw[index]
            if row.get('avg_ns') is not None:
                entry['timed_seconds'] = row['avg_ns'] / 1e9
            entry.update(n_prompt=row.get('n_prompt'), n_gen=row.get('n_gen'))
            setting = {k: row[k] for k in LOADING_KEYS if k in row}
            for key in ('use_mmap', 'use_direct_io'):
                if key in setting and setting[key] is not None and not isinstance(setting[key], bool):
                    raise InvalidInput(f'producer {key} must be boolean or null')
                if declared_loading.get(key) is not None and key in setting and declared_loading[key] != setting[key]:
                    warnings.append(f'row {index}: declared loading.{key} conflicts with producer value; neither is overwritten.')
            signatures.add(canonical({'model_filename': row.get('model_filename'),
                                      'build_commit': row.get('build_commit'), 'loading': setting}))
        else:
            setting = {}
            signatures.add(canonical({'model': record['model'], 'software': record['software']}))
        record['loading_configuration'] = {'producer_reported': setting, 'declared': declared_loading,
                                           'producer_status': 'reported' if isinstance(raw, list) else 'not_available_in_server_response',
                                           'origin': 'producer JSON plus unmodified supplied metadata.loading; missing values unknown'}
        record['engine_load_timer'] = {'seconds_since_model_start': engine_loads[index] if count_matches else None,
                                       'association': 'positional, caller-supplied log, matching count' if count_matches else 'unattributed',
                                       'definition': ENGINE_DEFINITION}
        producer_loading.append({'record_index': index, **setting})
        group = 'prompt_processing' if record['kind'] == 'prompt' else 'generation' if record['kind'] == 'generation' else 'combined'
        measurements[group].append(entry)
    mixed = len(signatures) > 1
    if mixed:
        if engine_loads:
            warnings.append('Multiple model/loading configurations: no shared model-load or engine-timer scalar is attributed across configurations.')
        if declared_load is not None:
            measurements['model_loading']['declared_unattributed_seconds'] = declared_load
            measurements['model_loading']['seconds'] = None
            measurements['model_loading']['source'] = 'unattributed_across_configurations'
    if engine_loads and count_matches and not mixed:
        measurements['engine_load_timer']['first_configuration_seconds'] = engine_loads[0]
    if declared_load is not None and total is not None and declared_load > total + .1:
        warnings.append('Declared model loading exceeds total runtime; timer scopes require inspection.')
    return measurements, {'declared': declared_loading, 'producer_records': producer_loading,
                          'policy': 'Observed configuration only. No universal mmap default or workload execution.'}, log_hash
