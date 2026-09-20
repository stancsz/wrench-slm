param(
    [string]$ModelPath = 'D:\models\Wrench-Qwen3.6-8expert-profiled-W4A16-NVFP4-calibrated-v7-Safety-ExplicitSchema-TextOnly-HF-native2M-candidate',
    [string]$BindHost = '127.0.0.1',
    [int]$Port = 28180,
    [string]$GlobalFullLayer = '39',
    [int]$SlidingWindow = 65536,
    [int]$KvReserveTokens = 8192,
    [string]$ServedModel = 'wrench-8e-native4m'
)

$overlay = Join-Path $PSScriptRoot '..\runtime\freetoken_wrench_long_context'
$env:PYTHONPATH = (Resolve-Path $overlay).Path
$env:WRENCH_LONG_CONTEXT_OVERLAY = '1'
$env:CUDA_MODULE_LOADING = 'LAZY'
$env:PYTORCH_NVML_BASED_CUDA_CHECK = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$env:NUMEXPR_NUM_THREADS = '1'
$env:WRENCH_GLOBAL_FULL_LAYERS = [string]$GlobalFullLayer
$env:WRENCH_SWA_WINDOW = [string]$SlidingWindow

& 'C:\Users\stanc\AppData\Local\FreeToken\venv\Scripts\ft.exe' serve `
    --model $ModelPath `
    --host $BindHost `
    --port $Port `
    --served-model-name $ServedModel `
    --max-seq-len-override 4000000 `
    --max-prefill-length 32768 `
    --max-running-requests 1 `
    --num-tokenizer 0 `
    --memory-ratio 0.90 `
    --moe-strategy offload `
    --expert-load serial `
    --moe-cache-auto `
    --kv-reserve-tokens $KvReserveTokens `
    --num-tokens 4000000 `
    --text-model-only `
    --cache-type radix `
    --tool-call-parser qwen `
    --reasoning-parser off
