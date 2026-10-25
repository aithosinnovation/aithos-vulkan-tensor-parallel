"""CLI entry point; import recorded data, never execute benchmark commands."""
import argparse
from pathlib import Path
import sys

from .collect import safe_snapshot
from .core import ADAPTERS, InvalidInput, attach_snapshot, build_report, canonical, read_bytes, summary


def main(argv=None):
    parser = argparse.ArgumentParser(description='Capture recorded benchmark results. Does not run GPU workloads.')
    commands = parser.add_subparsers(dest='command', required=True)
    imp = commands.add_parser('import', help='Import recorded JSON into a new report directory')
    imp.add_argument('--input', type=Path, required=True)
    imp.add_argument('--metadata', type=Path, required=True)
    imp.add_argument('--format', choices=ADAPTERS, default='llama-bench')
    imp.add_argument('--kind', choices=['sample', 'recorded'], required=True)
    imp.add_argument('--out', type=Path, required=True, help='New directory; refuses overwrite')
    imp.add_argument('--stderr', type=Path, help='Optional saved producer stderr; extracts engine-reported model-load observations')
    imp.add_argument('--snapshot-host', action='store_true', help='Read-only host inventory and one telemetry observation')
    args = parser.parse_args(argv)
    try:
        if args.out.exists():
            raise InvalidInput(f'output already exists: {args.out}')
        raw_bytes, metadata_bytes = read_bytes(args.input), read_bytes(args.metadata)
        report = build_report(raw_bytes, metadata_bytes, args.format, args.kind,
                              read_bytes(args.stderr) if args.stderr else None)
        if args.snapshot_host:
            attach_snapshot(report, safe_snapshot())
        result_text, summary_text = canonical(report), summary(report)
        args.out.mkdir(mode=0o700)
        (args.out / 'result.json').write_text(result_text, encoding='utf-8')
        (args.out / 'summary.md').write_text(summary_text, encoding='utf-8')
        print(summary_text, end='')
        return 0
    except (OSError, InvalidInput, ValueError, OverflowError) as exc:
        print(f'benchrun: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
