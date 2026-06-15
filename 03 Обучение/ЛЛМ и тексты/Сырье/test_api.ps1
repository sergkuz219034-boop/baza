$headers = @{ 
    "Authorization" = "Bearer sk-d043bf6f75b64830928601519f6f649b"
    "Content-Type" = "application/json" 
}
$body = @{ 
    model = "qwen-plus"
    messages = @( @{ role = "user"; content = "hi" } ) 
} | ConvertTo-Json -Depth 5

try {
    $result = Invoke-RestMethod -Uri "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions" -Headers $headers -Method Post -Body $body
    Write-Output ($result | ConvertTo-Json -Depth 10)
} catch {
    Write-Error $_
}
