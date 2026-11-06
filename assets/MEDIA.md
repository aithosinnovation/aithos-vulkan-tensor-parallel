# Figures and media

The primary square and wide graphics show the same 64-token generation test at depth zero and requested batch/ubatch 32. The ranges are the process medians from two blocks per mode, in tokens per second. Bars start at zero, end at the higher median, and mark the lower median. They are scoped to one Windows host, one 7B model, equal 1/1 splits, and a build with optional CPU ISA extensions off. The square PNG is the X attachment; the wide PNG is the report and site figure. Editable SVGs and `scripts/make_publication_graphics.py` are included.

`prompt-posthoc-wide.png` and SVG show a separate 512-token prompt sensitivity at requested batch/ubatch 512, added after the primary matrix. Its rates must not be compared directly with generation rates.

`comparison.png` and SVG are the historical dense dual-panel comparison, retained for provenance, not as the current overview. The animated figure deck is historical too; it presents stored measurements, not live inference. Other figures show numerical-error rows, observed memory peaks, a conceptual topology, and workload-specific measurements.

The topology diagram's observed Gen3 x4 label identifies the highest recorded RTX link state. Active telemetry samples also include Gen1 x4 and Gen2 x4; the diagram does not establish constant link speed or measured bandwidth. PNG metadata contains only the lab software label and DPI.
