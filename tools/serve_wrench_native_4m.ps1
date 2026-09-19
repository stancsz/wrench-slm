param(
    [string]$ModelPath = 'D:\models\Wrench-Qwen3.6-8expert-profiled-W4A16-NVFP4-calibrated-v7-Safety-ExplicitSchema-TextOnly-HF-native2M-candidate',
    [string]$Host = '127.0.0.1',
    [int]$Port = 28180,
    [int]$GlobalFullLayer = 39,
    [int]$SlidingWindow = 65536,
    [string]$ServedModel = 'wrench-8e-native4m'
)

$overlay = Join-Path $PSScriptRoot '..\runtime\freetoken_wrench_long_context'
$env:PYTHONPATH = (Resolve-Path $overlay).Path
$env:WRENCH_LONG_CONTEXT_OVERLAY = '1'
$env:WRENCH_GLOBAL_FULL_LAYERS = [string]$GlobalFullLayer
$env:WRENCH_SWA_WINDOW = [string]$SlidingWindow

& 'C:\Users\stanc\AppData\Local\FreeToken\venv\Scripts\ft.exe' serve `
    --model $ModelPath `
    --host $Host `
    --port $Port `
    --served-model-name $ServedModel `
    --max-seq-len-override 4000000 `
    --max-prefill-length 32768 `
    --max-running-requests 1 `
    --memory-ratio 0.90 `
    --moe-strategy offload `
    --moe-cache-auto `
    --text-model-only `
    --cache-type radix `
    --tool-call-parser qwen `
    --reasoning-parser off
