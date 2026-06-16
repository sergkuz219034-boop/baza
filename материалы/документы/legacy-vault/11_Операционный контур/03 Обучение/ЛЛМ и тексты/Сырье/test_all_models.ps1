$headers = @{ 
    "Authorization" = "Bearer sk-d043bf6f75b64830928601519f6f649b"
    "Content-Type" = "application/json" 
}
$models = @("qwen-turbo", "qwen-plus", "qwen-max", "qwen3.6-flash", "qwen3.6-35b-a3b")
$baseUrl = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions"

foreach ($model in $models) {
    Write-Output "Testing model: $model..."
    $body = @{ 
        model = $model
        messages = @( @{ role = "user"; content = "hi" } ) 
    } | ConvertTo-Json -Depth 5
    
    try {
        $result = Invoke-RestMethod -Uri $baseUrl -Headers $headers -Method Post -Body $body
        Write-Output "SUCCESS for $model!"
        Write-Output ($result | ConvertTo-Json -Depth 10)
        break
    } catch {
        Write-Output "FAILED for $($model): $($_.Exception.Message)"
        if ($_.ErrorDetails) { Write-Output "Details: $($_.ErrorDetails.Message)" }
    }
}
