# benchrun report

Data: recorded
Adapter: llama-bench
Content ID: 75a75f825509243be92193ebdb2c1d5699eb7f0b76be97e7b45a6b7c049d5e3a

## Phase measurements

- Model loading: unavailable; source: unavailable
- Total execution: 37.510838 s; source: metadata.execution.elapsed_seconds
- Engine startup proxy (model start through first eval): 8.789990 s

Time since model-load start until the context first evaluation completes. Includes that evaluation (part of the timed test with --no-warmup); later context values can be cumulative from the same model start. Not isolated model loading, not additive with prompt/generation time.
Loading-only time remains unavailable without a separate supplied observation. These timers are not additive. Prompt/generation rates are producer-timed records, not end-to-end throughput.

## Loading configuration

```json
{
  "declared": {
    "lazy_mode": "off",
    "use_direct_io": false,
    "use_mmap": true
  },
  "policy": "Observed configuration only. No universal mmap default or workload execution.",
  "producer_records": [
    {
      "devices": "Vulkan1/Vulkan2",
      "flash_attn": 1,
      "main_gpu": 0,
      "n_gpu_layers": 99,
      "no_host": false,
      "no_kv_offload": false,
      "no_op_offload": 0,
      "record_index": 0,
      "split_mode": "layer",
      "tensor_buft_overrides": "none",
      "tensor_split": "1.00/1.00",
      "type_k": "f16",
      "type_v": "f16"
    },
    {
      "devices": "Vulkan1/Vulkan2",
      "flash_attn": 1,
      "main_gpu": 0,
      "n_gpu_layers": 99,
      "no_host": false,
      "no_kv_offload": false,
      "no_op_offload": 0,
      "record_index": 1,
      "split_mode": "layer",
      "tensor_buft_overrides": "none",
      "tensor_split": "1.00/1.00",
      "type_k": "f16",
      "type_v": "f16"
    },
    {
      "devices": "Vulkan1/Vulkan2",
      "flash_attn": 1,
      "main_gpu": 0,
      "n_gpu_layers": 99,
      "no_host": false,
      "no_kv_offload": false,
      "no_op_offload": 0,
      "record_index": 2,
      "split_mode": "layer",
      "tensor_buft_overrides": "none",
      "tensor_split": "1.00/1.00",
      "type_k": "f16",
      "type_v": "f16"
    },
    {
      "devices": "Vulkan1/Vulkan2",
      "flash_attn": 1,
      "main_gpu": 0,
      "n_gpu_layers": 99,
      "no_host": false,
      "no_kv_offload": false,
      "no_op_offload": 0,
      "record_index": 3,
      "split_mode": "layer",
      "tensor_buft_overrides": "none",
      "tensor_split": "1.00/1.00",
      "type_k": "f16",
      "type_v": "f16"
    }
  ]
}
```

1. [recorded] prompt: 639.023 tokens/s; model "DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf"
   software: {"backends": "Vulkan", "build_commit": "c93decc", "build_number": 2}
   hardware: {"cpu_info": "13th Gen Intel(R) Core(TM) i9-13900KF", "gpu_info": "Intel(R) Arc(TM) A310 LP Graphics, Intel(R) Arc(TM) Pro B70 Graphics, NVIDIA GeForce RTX 3090"}
   parameters: {"cpu_mask": "0x0", "cpu_strict": false, "devices": "Vulkan1/Vulkan2", "embeddings": false, "fit_min_ctx": 0, "fit_target": 0, "flash_attn": 1, "lazy_mode": "off", "load_mode": "mmap", "main_gpu": 0, "n_batch": 32, "n_cpu_moe": 0, "n_depth": 0, "n_gen": 0, "n_gpu_layers": 99, "n_prompt": 128, "n_threads": 4, "n_ubatch": 32, "no_host": false, "no_kv_offload": false, "no_op_offload": 0, "poll": 50, "split_mode": "layer", "tensor_buft_overrides": "none", "tensor_split": "1.00/1.00", "type_k": "f16", "type_v": "f16"}
2. [recorded] prompt: 546.467 tokens/s; model "DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf"
   software: {"backends": "Vulkan", "build_commit": "c93decc", "build_number": 2}
   hardware: {"cpu_info": "13th Gen Intel(R) Core(TM) i9-13900KF", "gpu_info": "Intel(R) Arc(TM) A310 LP Graphics, Intel(R) Arc(TM) Pro B70 Graphics, NVIDIA GeForce RTX 3090"}
   parameters: {"cpu_mask": "0x0", "cpu_strict": false, "devices": "Vulkan1/Vulkan2", "embeddings": false, "fit_min_ctx": 0, "fit_target": 0, "flash_attn": 1, "lazy_mode": "off", "load_mode": "mmap", "main_gpu": 0, "n_batch": 32, "n_cpu_moe": 0, "n_depth": 0, "n_gen": 0, "n_gpu_layers": 99, "n_prompt": 512, "n_threads": 4, "n_ubatch": 32, "no_host": false, "no_kv_offload": false, "no_op_offload": 0, "poll": 50, "split_mode": "layer", "tensor_buft_overrides": "none", "tensor_split": "1.00/1.00", "type_k": "f16", "type_v": "f16"}
3. [recorded] generation: 100.052 tokens/s; model "DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf"
   software: {"backends": "Vulkan", "build_commit": "c93decc", "build_number": 2}
   hardware: {"cpu_info": "13th Gen Intel(R) Core(TM) i9-13900KF", "gpu_info": "Intel(R) Arc(TM) A310 LP Graphics, Intel(R) Arc(TM) Pro B70 Graphics, NVIDIA GeForce RTX 3090"}
   parameters: {"cpu_mask": "0x0", "cpu_strict": false, "devices": "Vulkan1/Vulkan2", "embeddings": false, "fit_min_ctx": 0, "fit_target": 0, "flash_attn": 1, "lazy_mode": "off", "load_mode": "mmap", "main_gpu": 0, "n_batch": 32, "n_cpu_moe": 0, "n_depth": 0, "n_gen": 32, "n_gpu_layers": 99, "n_prompt": 0, "n_threads": 4, "n_ubatch": 32, "no_host": false, "no_kv_offload": false, "no_op_offload": 0, "poll": 50, "split_mode": "layer", "tensor_buft_overrides": "none", "tensor_split": "1.00/1.00", "type_k": "f16", "type_v": "f16"}
4. [recorded] generation: 99.785 tokens/s; model "DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf"
   software: {"backends": "Vulkan", "build_commit": "c93decc", "build_number": 2}
   hardware: {"cpu_info": "13th Gen Intel(R) Core(TM) i9-13900KF", "gpu_info": "Intel(R) Arc(TM) A310 LP Graphics, Intel(R) Arc(TM) Pro B70 Graphics, NVIDIA GeForce RTX 3090"}
   parameters: {"cpu_mask": "0x0", "cpu_strict": false, "devices": "Vulkan1/Vulkan2", "embeddings": false, "fit_min_ctx": 0, "fit_target": 0, "flash_attn": 1, "lazy_mode": "off", "load_mode": "mmap", "main_gpu": 0, "n_batch": 32, "n_cpu_moe": 0, "n_depth": 0, "n_gen": 64, "n_gpu_layers": 99, "n_prompt": 0, "n_threads": 4, "n_ubatch": 32, "no_host": false, "no_kv_offload": false, "no_op_offload": 0, "poll": 50, "split_mode": "layer", "tensor_buft_overrides": "none", "tensor_split": "1.00/1.00", "type_k": "f16", "type_v": "f16"}

## Benchmark model

```json
{
  "name": "DeepSeek-R1-Distill-Qwen-7B",
  "quantization": "Q4_K_M",
  "sha256": "78272d8d32084548bd450394a560eb2d70de8232ab96a725769b1f9171235c1c"
}
```

## Benchmark software

```json
{
  "CPU_optional_ISA": "OFF; as-built frozen comparison",
  "MSVC": "19.44.35229.0",
  "Vulkan_SDK": "1.4.363.0",
  "backend": "native Windows Vulkan",
  "source_commit": "c93decc7654dac127d18fd61064565ef00bf8244"
}
```

## Benchmark hardware

```json
{
  "Intel_driver": "32.0.101.9150",
  "NVIDIA_driver": "617.42 / Windows32.0.16.1742",
  "memory_telemetry": {
    "b70_observed_min_in_process_mib": 2005.58203125,
    "b70_peak_mib": 2115.390625,
    "batch": 32,
    "block": "B",
    "collector_cpu_seconds": 6.171875,
    "depth": 0,
    "id": "B-layer",
    "intel_engine_counter_qualification": "Raw WDDM formatted per-process engine counter; values may exceed100 and are not a validated GPU utilization percentage",
    "intel_engine_counter_raw_max": 72.0,
    "intel_power_watts": null,
    "intel_temperature_c": null,
    "intel_utilization_percent": null,
    "mode": "layer",
    "nvidia_active_link_states": [
      [
        2,
        4
      ],
      [
        3,
        4
      ]
    ],
    "nvidia_all_link_states": [
      [
        1,
        4
      ],
      [
        2,
        4
      ],
      [
        3,
        4
      ]
    ],
    "nvidia_observed_min_in_process_mib": 2186.36328125,
    "nvidia_peak_mib": 2241.89453125,
    "nvidia_power_max_watts": 252.71,
    "nvidia_samples_inside": 74,
    "nvidia_smi_memory_peak_mib": 2237.0,
    "nvidia_temperature_max_c": 66.0,
    "process_cpu_seconds": 9.0625,
    "source": "WDDM adapter-wide DedicatedUsage, query intervals inside process interval",
    "wddm_samples_inside": 11
  },
  "selected_mode": "layer"
}
```

## Benchmark execution

```json
{
  "argv": [
    "-m",
    "${MODEL}",
    "-p",
    "128,512",
    "-n",
    "32,64",
    "-d",
    "0",
    "-r",
    "5",
    "--delay",
    "5",
    "-b",
    "32",
    "-ub",
    "32",
    "-t",
    "4",
    "-ngl",
    "99",
    "-fa",
    "on",
    "-ctk",
    "f16",
    "-ctv",
    "f16",
    "-mg",
    "0",
    "-lm",
    "mmap",
    "-lzm",
    "off",
    "-o",
    "json",
    "-v",
    "--progress",
    "--offline",
    "-dev",
    "Vulkan1/Vulkan2",
    "-sm",
    "layer",
    "-ts",
    "1/1"
  ],
  "elapsed_seconds": 37.510838,
  "executable": "${LLAMA_ROOT}\\build\\bin\\llama-bench.exe",
  "exit_code": 0,
  "preflight_nvidia_compute_apps": {},
  "process_cpu_seconds": 9.0625,
  "stop_reason": null,
  "telemetry_scope": "NVIDIA device-wide500ms; WDDM adapter-wide memory and benchmark-PID engine counters; clock zone and wall-clock timestamps omitted from this copy; Intel power unavailable",
  "timed_out": false,
  "timeout_seconds": 120,
  "wddm_collector_cpu_seconds": 6.171875,
  "working_directory": "${LLAMA_ROOT}\\build\\bin"
}
```

## Benchmark telemetry

```json
{
  "during_benchmark": {
    "b70_observed_min_in_process_mib": 2005.58203125,
    "b70_peak_mib": 2115.390625,
    "batch": 32,
    "block": "B",
    "collector_cpu_seconds": 6.171875,
    "depth": 0,
    "id": "B-layer",
    "intel_engine_counter_qualification": "Raw WDDM formatted per-process engine counter; values may exceed100 and are not a validated GPU utilization percentage",
    "intel_engine_counter_raw_max": 72.0,
    "intel_power_watts": null,
    "intel_temperature_c": null,
    "intel_utilization_percent": null,
    "mode": "layer",
    "nvidia_active_link_states": [
      [
        2,
        4
      ],
      [
        3,
        4
      ]
    ],
    "nvidia_all_link_states": [
      [
        1,
        4
      ],
      [
        2,
        4
      ],
      [
        3,
        4
      ]
    ],
    "nvidia_observed_min_in_process_mib": 2186.36328125,
    "nvidia_peak_mib": 2241.89453125,
    "nvidia_power_max_watts": 252.71,
    "nvidia_samples_inside": 74,
    "nvidia_smi_memory_peak_mib": 2237.0,
    "nvidia_temperature_max_c": 66.0,
    "process_cpu_seconds": 9.0625,
    "source": "WDDM adapter-wide DedicatedUsage, query intervals inside process interval",
    "wddm_samples_inside": 11
  },
  "scope": "WDDM adapter-wide DedicatedUsage, query intervals inside process interval"
}
```

## Limitations

- Benchmark metadata missing software.build_flags; do not infer from import host.
- Benchmark metadata missing software.commit; do not infer from import host.
- Benchmark metadata missing hardware.os; do not infer from import host.
