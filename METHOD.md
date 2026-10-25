# Method, environment and reproduction

## Immutable identity

Source `c93decc7654dac127d18fd61064565ef00bf8244`, tree `2283717ec7405683ed30b2e3d52ef7267c64c16b`; Windows native unpatched llama.cpp. The tested upstream source is identified by this immutable commit and tree. No assumption is made that today's PR head has the same behavior. The model hash and exact build details are in `data/software.json`. Build count 2 comes from shallow history, not an upstream release number.

MSVC 19.44.35229.0 / toolset 14.44.35207, VS Build Tools 17.14.42, Windows SDK 10.0.26100.0, CMake 3.31.6-msvc6, Ninja 1.12.1, Vulkan SDK 1.4.363.0. Intel 32.0.101.9150, NVIDIA 617.42 / Windows 32.0.16.1742. CPU i9-13900KF. No driver or global-configuration changes. Existing overlays retained. The primary source build had optional CPU ISA flags OFF. Reproduce those flags to compare this implementation. This is not a recommended universal build recipe. One host produced these measurements.

Key CMake flags:

```
-DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON -DGGML_BACKEND_DL=ON
-DGGML_CPU=ON -DGGML_CPU_ALL_VARIANTS=OFF -DGGML_NATIVE=OFF
-DGGML_SSE42=OFF -DGGML_AVX=OFF -DGGML_AVX2=OFF
-DGGML_BMI2=OFF -DGGML_AVX512=OFF
-DGGML_AVX512_VBMI=OFF -DGGML_AVX512_VNNI=OFF -DGGML_AVX512_BF16=OFF -DGGML_AVX_VNNI=OFF
-DGGML_VULKAN=ON -DGGML_CUDA=OFF -DGGML_SYCL=OFF -DGGML_RPC=OFF
-DLLAMA_BUILD_SERVER=OFF -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_MTMD=OFF
-DLLAMA_OPENSSL=OFF -DLLAMA_BUILD_TOOLS=ON
```

Do not add separate MSVC cache options `-DGGML_FMA` or `-DGGML_F16C`. On this pin those options are absent for MSVC: `ggml/CMakeLists.txt` declares `GGML_FMA` and `GGML_F16C` only when the compiler is not MSVC, and its comment says MSVC implies F16C and FMA with AVX2 or AVX512. The MSVC CPU file then defines `GGML_FMA` and `GGML_F16C` only on the `GGML_AVX2` path (`ggml/src/ggml-cpu/CMakeLists.txt`). `GGML_AVX2=OFF` prevents that path. The list above is the recorded effective cache state. The ISA `OFF` values were not passed on the original command line: they were inherited from the first, failed configure (with the default `GGML_NATIVE=ON`) when the same build directory was reconfigured with `GGML_NATIVE=OFF`. A fresh configure with only `GGML_NATIVE=OFF` would enable them. To reproduce this implementation, pass them explicitly as listed.

Use an isolated source and build directory and the existing supported Windows C++ tools and Vulkan SDK. Pass explicit `Vulkan_INCLUDE_DIR`, `Vulkan_LIBRARY`, `Vulkan_GLSLC_EXECUTABLE`, and `SPIRV-Headers_DIR` to the selected SDK. Do not rely on another application's runtime or modify its configuration. Compile `llama-bench` and `llama-completion`. The source snapshot's absent `.git` means build-version metadata needs explicit `LLAMA_BUILD_NUMBER=2` and `LLAMA_BUILD_COMMIT=c93decc` if the labels are to match. The full pin, tree, and hashes remain authoritative. Binary identity across different build paths or toolchains is not promised.

Model: existing `DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf`, 4,683,073,248 bytes, SHA-256 `78272d8d32084548bd450394a560eb2d70de8232ab96a725769b1f9171235c1c`. The producer-reported tensor size differs from the GGUF file bytes because of metadata and layout. Hash before the run. Do not redistribute weights here. Do not fetch a different quantization under the same label.

## Finite process design

Primary A (R, B, L, T) and B (T, L, B, R) use `-p 128,512 -n 32,64 -d 0`. Primary C (B, R, T, L) uses `-p 512 -n 64 -d 1024`. Separate post-hoc sensitivity D (R, B, L, T) and E (T, L, B, R) uses `-p 512 -n 64 -d 0 -b 512 -ub 512`. Spaces are required between flags and values. Exact argument arrays are in `data/run-plans.json`. The token stream is the fixed default CRT synthetic stream, with the same ordered test list and warmup across modes. These are random token IDs, not natural-language prompts. Dataset-depth prefill is outside the timed regions, and cache-state serialization and restoration are part of the run behavior. The Meta depth benchmark completed with cached-state log entries.

Common flags (primary batch 32; the sensitivity replaces both 32s with 512):

```
-m MODEL -b 32 -ub 32 -t 4 -ngl 99 -fa on -ctk f16 -ctv f16 -mg 0
-lm mmap -lzm off -r 5 --delay 5 -o json -v --progress --offline
```

Per-mode flags: RTX `-dev Vulkan2 -sm none`; B70 `-dev Vulkan1 -sm none`; layer `-dev Vulkan1/Vulkan2 -sm layer -ts 1/1`; tensor uses the same device list with `-sm tensor -ts 1/1`. Exact usable commands have a space after `-ts`. The recorded values are `Vulkan1/Vulkan2` and `1/1`. JSON arrays are unambiguous. Device numbers must be re-enumerated and descriptions checked on another host. The A310 is excluded even though `gpu_info` inventories all visible adapters. `main_gpu` 0 is the first selected device, not global Vulkan0.

One native process at a time, 120 s watchdog, 85 °C NVIDIA guard, no retry, 3 s between processes plus model hashing and a 5 s delay per test. No cache flush, no clock or power changes, no backend-layer changes, and no hardware A/B. All 20 processes exited 0. No experimental failure was hidden. Counterbalanced blocks were retained with all individual samples, including slow outliers. No additional runs were made to choose a favorable score.

Built-in prompt warmup equals the full `n_prompt`. Generation warmup is one decode. Five samples per test. Effective contexts, in declared JSON order: pp128 → 256, pp512 → 512, tg32 / tg64 → 256; pp512 at depth 1024 → 1536, tg64 at depth 1024 → 1280. Context and KV precision are the same across modes within each test, not across all tests. `n_batch` may be clamped internally to the context despite the producer-recorded requested 512. Declared and effective distinctions must be retained. No context CLI flag was invented.

## Capture and interpretation

Original stdout JSON, stderr, argv, environment, PIDs, the native watchdog, and process CPU and memory observations were retained privately. Release files are redacted copies: `model_filename` is reduced to the basename, and local root, user-profile paths, and persistent adapter UUID and LUID values are redacted. No numeric samples or parameters were changed. The release SHA-256 for each sanitized producer JSON is recorded in `data/redactions.json`; original private hashes are withheld. Redacted files cannot be claimed byte-identical to the originals. The full `PATH` and the private inventory are omitted.

The NVIDIA sampler at 500 ms reports device-wide memory, power, temperature, and the actual PCIe link generation and width. The WDDM counter process polls at about 2 s, maps adapter LUIDs through DXGI, and records dedicated and shared memory and raw benchmark-PID engine counters. Query intervals wholly inside the native process bounds are retained. The same sampler ran in all 20 processes, and its CPU cost was recorded. Memory charts use WDDM for both cards, not a mixture of nvidia-smi and Intel providers. The total peak includes loading, all tests, and background usage, not just model weights. Engine counters above 100 were observed. True Intel utilization, power, and temperature remain unavailable and were never inferred as 0. WDDM compute-app checks are not a completeness proof.

Rate per repetition = `(n_prompt + n_gen) * 1e9 / samples_ns`. The summary is the median and range per process, then matched-block ratios relative to the RTX. Preserve the producer `samples_ts`, with its rounding, as input. Primary statistics use integer nanoseconds. There is no n = 10 independence assumption, no significance claim, no best-run selection, and no fitted uncertainty. Cross-block spread is meaningful. One C block is not repeatability. CPU ISA OFF, ubatch shape, collector overhead, cache and thermal order, and clock behavior are confounders. Correlation does not isolate interconnect causality. PCIe causality is unknown.

Pure model-load seconds are NULL in the timing imports. The engine load proxy overlaps the first evaluation and cannot be added to inference or treated as loading-only. Total process wall time includes all phases and delays. Do not rank configurations by wall time when the workload lists differ. Separate correctness load-call samples are single warm-file-cache observations, not replicated load performance. Timing figures are not loading figures.

## Rerun on your own machine

Do not execute scripts automatically on opening the site. See `scripts/prepare_run.py` to bind your existing `MODEL` and `LLAMA_ROOT` into a new work directory and freeze the current binaries and model hash. It never installs tools. Then invoke `scripts/run-case.ps1` with explicit `Case`, `LlamaRoot`, and `WorkRoot` from a native PowerShell process. That script is the collected supervisor with the lab root parameterized. It writes only new work directories and refuses to overwrite. The guarded variant now checks selected device descriptions with a bounded, read-only `--list-devices` probe before inference. That additional check was added after collection; `scripts/supervisor-as-collected.ps1` preserves the original collected supervisor with only root paths parameterized. The recorded plans hard-code `Vulkan1` (B70) and `Vulkan2` (RTX 3090) from this host's enumeration. On any other host, list the devices with the same `llama-bench.exe` first, and edit the `-dev` values in the prepared `plans.json` before launching. The new guard rejects an A310, swapped device identity or wrong selected-device count. Re-enumeration remains necessary because aliases are host-specific. This is real GPU work. It requires your informed choice and compatible hardware. It does not change global configurations. Offline verification is preferable if you only want to inspect the data.

Record your source, toolchain, drivers, and differences. Equal filenames or device indices do not prove equivalence. Fixed timing bit-identity across hosts is not expected. Figure dependencies are project-local and locked. Use a virtual environment. Never replace the inference dependencies. No public publishing commands are included.

## Requested versus effective batch sizes

The JSON records preserve requested batch/ubatch. Native logs show both effective values as 32 in the primary matrix, 512 for sensitivity pp512, and 64 for sensitivity tg64. The context constructor clamps batch before padding the requested 64-token context to 256. `data/summary.json` records `effective_batch`/`effective_ubatch` separately; CSV has both. Site ub512 labels identify the requested setting, not an actual 512-token decode batch. Each generation evaluation still consumes one input token. This is another reason not to infer kernel equivalence across different requested settings.
