param([Parameter(Mandatory=$true)][string]$Case,[Parameter(Mandatory=$true)][string]$LlamaRoot,[Parameter(Mandatory=$true)][string]$WorkRoot)
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
$root=$LlamaRoot;$work=$WorkRoot
$plans=Get-Content "$work\plans.json" -Raw|ConvertFrom-Json
$plan=@($plans|Where-Object {$_.id -eq $Case});if($plan.Count -ne 1){throw 'Unknown or duplicate case'};$plan=$plan[0]
$exe="$root\build\bin\llama-bench.exe";$model=$plan.model
$ident=Get-Content "$work\frozen-binaries.json" -Raw|ConvertFrom-Json
foreach($entry in $ident.PSObject.Properties){if((Get-FileHash "$root\build\bin\$($entry.Name)" -Algorithm SHA256).Hash.ToLower() -ne $entry.Value){throw 'Frozen binary differs'}}
if((Get-FileHash $model -Algorithm SHA256).Hash.ToLower() -ne $plan.model_sha256){throw 'Model hash differs'}
$nv='C:\Windows\System32\nvidia-smi.exe'
$compute=& $nv --query-compute-apps=pid,process_name --format=csv,noheader
if($LASTEXITCODE -eq 0 -and (($compute -join '').Trim().Length -gt 0)){throw "Other NVIDIA compute process present: $compute"}
$others=Get-Process llama-bench,llama-bench-impl,aithos-layer-check,aithos-mixed-repeat,llama-completion -ErrorAction SilentlyContinue
if($others){throw 'Another lab inference process is running'}
$dir="$work\runs\$Case";if(Test-Path $dir){throw 'Case already exists; choose documented new attempt, never overwrite'};New-Item -ItemType Directory -Path $dir -Force|Out-Null
$plan|ConvertTo-Json -Depth 12|Set-Content "$dir\plan.json"
$argvList=@($plan.argv)
$psi=[Diagnostics.ProcessStartInfo]::new();$psi.FileName=$exe;$psi.WorkingDirectory="$root\build\bin";$psi.UseShellExecute=$false;$psi.RedirectStandardOutput=$true;$psi.RedirectStandardError=$true
$psi.Arguments=($argvList|ForEach-Object {'"'+$_.Replace('"','\"')+'"'}) -join ' '
$envState=@{};foreach($key in @('PATH','VULKAN_SDK','VK_SDK_PATH','VK_LAYER_PATH','VK_ADD_LAYER_PATH','VK_INSTANCE_LAYERS','VK_LOADER_DEBUG')){$envState[$key]=$psi.EnvironmentVariables[$key]};$envState|ConvertTo-Json|Set-Content "$dir\process-environment.json"
$tele=$null;$counter=$null;$teleOut=$null;$teleErr=$null
$ti=[Diagnostics.ProcessStartInfo]::new();$ti.FileName=$nv;$ti.UseShellExecute=$false;$ti.RedirectStandardOutput=$true;$ti.RedirectStandardError=$true
$ti.Arguments='--query-gpu=timestamp,index,uuid,name,driver_version,memory.used,utilization.gpu,power.draw,temperature.gpu,pcie.link.gen.current,pcie.link.width.current,pcie.link.gen.max,pcie.link.width.max --format=csv,noheader,nounits --loop-ms=500'
$tele=[Diagnostics.Process]::new();$tele.StartInfo=$ti
$tele.Start()|Out-Null
$teleOut=[IO.File]::Open("$dir\nvidia.csv",[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::ReadWrite);$teleErr=[IO.File]::Open("$dir\nvidia.stderr",[IO.FileMode]::CreateNew)
$teleOutTask=$tele.StandardOutput.BaseStream.CopyToAsync($teleOut);$teleErrTask=$tele.StandardError.BaseStream.CopyToAsync($teleErr)
$proc=[Diagnostics.Process]::new();$proc.StartInfo=$psi
$out=[IO.File]::Open("$dir\original.json",[IO.FileMode]::CreateNew);$err=[IO.File]::Open("$dir\stderr.log",[IO.FileMode]::CreateNew)
$obs=[Collections.Generic.List[object]]::new();$reason=$null;$began=[DateTime]::UtcNow;$watch=[Diagnostics.Stopwatch]::StartNew();$started=$false;$lastThermal=0
try{
 if(!$proc.Start()){throw 'Failed to start benchmark'};$started=$true;$h=$proc.Handle;$benchPid=$proc.Id
 $ot=$proc.StandardOutput.BaseStream.CopyToAsync($out);$et=$proc.StandardError.BaseStream.CopyToAsync($err)
 # Existing WDDM counters supply adapter-wide memory and per-process engine usage, not power.
 $collector=@'
$ErrorActionPreference='Continue';$ProgressPreference='SilentlyContinue'
$began=[DateTime]::UtcNow
while(([DateTime]::UtcNow-$began).TotalSeconds -lt 125){
 if(!(Get-Process -Id BENCHPID -ErrorAction SilentlyContinue)){break}
 $a=[DateTime]::UtcNow.ToString('o')
 try{$mem=@(Get-CimInstance Win32_PerfFormattedData_GPUPerformanceCounters_GPUAdapterMemory|Select-Object Name,DedicatedUsage,SharedUsage,TotalCommitted);$eng=@(Get-CimInstance Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine|Where-Object {$_.Name -like 'pid_BENCHPID_*'}|Select-Object Name,UtilizationPercentage);@{started_at=$a;finished_at=[DateTime]::UtcNow.ToString('o');memory=$mem;benchmark_engines=$eng}|ConvertTo-Json -Depth 8 -Compress|Add-Content -Path 'OUTFILE' -Encoding UTF8}catch{@{started_at=$a;error=$_.Exception.Message}|ConvertTo-Json -Compress|Add-Content -Path 'OUTFILE' -Encoding UTF8}
 Start-Sleep -Milliseconds 2000
}
'@
 $collector=$collector.Replace('BENCHPID',"$benchPid").Replace('OUTFILE',"$dir\wddm.jsonl")
 $ci=[Diagnostics.ProcessStartInfo]::new();$ci.FileName='C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe';$ci.UseShellExecute=$false;$ci.CreateNoWindow=$true
 $ci.Arguments='-NoProfile -NonInteractive -EncodedCommand '+[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($collector))
 $counter=[Diagnostics.Process]::new();$counter.StartInfo=$ci;$counter.Start()|Out-Null;$counterHandle=$counter.Handle
 while(!$proc.WaitForExit(100)){
  if($watch.Elapsed.TotalSeconds -ge $plan.timeout_seconds){$reason='timeout';$proc.Kill();break}
  try{$proc.Refresh();$obs.Add(@{at=[DateTime]::UtcNow.ToString('o');cpu_seconds=$proc.TotalProcessorTime.TotalSeconds;working_set_bytes=$proc.WorkingSet64})}catch{}
  if($watch.Elapsed.TotalSeconds-$lastThermal -ge 2){
   $lastThermal=$watch.Elapsed.TotalSeconds
   try{$line=Get-Content "$dir\nvidia.csv" -Tail 1;$cols=$line -split ',';if($cols.Count -ge 9 -and [double]$cols[8] -ge 85){$reason='thermal_guard_85C';$proc.Kill();break}}catch{}
  }
 }
 $proc.WaitForExit();$finished=[DateTime]::UtcNow;$watch.Stop();$ot.GetAwaiter().GetResult()|Out-Null;$et.GetAwaiter().GetResult()|Out-Null
 $obs|ConvertTo-Json -Depth 4|Set-Content "$dir\process-observations.json"
 @{executable=$exe;argv=$argvList;working_directory=$psi.WorkingDirectory;pid=$benchPid;started_at=$began.ToString('o');finished_at=$finished.ToString('o');elapsed_seconds=$watch.Elapsed.TotalSeconds;process_cpu_seconds=$proc.TotalProcessorTime.TotalSeconds;timeout_seconds=$plan.timeout_seconds;timed_out=($reason -eq 'timeout');stop_reason=$reason;exit_code=$proc.ExitCode;utc_offset_seconds=[TimeZoneInfo]::Local.GetUtcOffset($began).TotalSeconds;preflight_nvidia_compute_apps=$compute;telemetry_scope='NVIDIA device-wide500ms; WDDM adapter-wide memory and benchmark-PID engine counters; clocks use native UTC+recorded NV timezone; Intel power unavailable'}|ConvertTo-Json -Depth 10|Set-Content "$dir\execution.json"
}catch{
 @{error=$_.Exception.Message;exit_code=$null;stop_reason='capture_error';started_at=$began.ToString('o');finished_at=[DateTime]::UtcNow.ToString('o')}|ConvertTo-Json|Set-Content "$dir\execution.json";throw
}finally{
 if($started -and !$proc.HasExited){$proc.Kill();$proc.WaitForExit()};$out.Dispose();$err.Dispose()
 if($counter -and !$counter.HasExited){if(!$counter.WaitForExit(2500)){$counter.Kill();$counter.WaitForExit()}}
 if($counter){try{$counter.Refresh();$cpu=$counter.TotalProcessorTime.TotalSeconds;$exec=Get-Content "$dir\execution.json" -Raw|ConvertFrom-Json;$exec|Add-Member -NotePropertyName wddm_collector_cpu_seconds -NotePropertyValue $cpu -Force;$exec|ConvertTo-Json -Depth 10|Set-Content "$dir\execution.json"}catch{}}
 if($tele -and !$tele.HasExited){$tele.Kill();$tele.WaitForExit()};$teleOutTask.GetAwaiter().GetResult()|Out-Null;$teleErrTask.GetAwaiter().GetResult()|Out-Null;$teleOut.Dispose();$teleErr.Dispose()
}
Get-Content "$dir\execution.json"
