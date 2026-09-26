# GPX benchmark input

The first benchmark uses immutable Git blob SHAs rather than mutable branch URLs.

The reference route and independent Suunto recording are both stored in the Gotaleden repository. Their blob SHAs are recorded in `benchmarks/gotaleden-75-v1.json`.

For blind reconstruction, the reference route must not be supplied to candidate generation or scoring. The Suunto recording is initially used only to quantify ordinary device/route disagreement; if a later benchmark chooses to expose participant GPS as evidence, that fact must be declared in the benchmark run.

A benchmark runner should normalize GPX `trkpt` coordinates to a GeoJSON LineString before calling `benchmark_geometry.py`. This keeps geometry comparison independent from source file format.
