# Update Step Functions State Machine with Error Handling
Write-Host "🔄 Updating Step Functions State Machine..." -ForegroundColor Green

$stateMachineArn = "arn:aws:states:us-east-1:090130568474:stateMachine:ChordScout-Transcription-dev"
$definitionPath = "backend/step-functions/transcription-workflow-with-error-handling.json"

# Update the state machine
Write-Host "Updating state machine definition..." -ForegroundColor Yellow
$result = aws stepfunctions update-state-machine --state-machine-arn $stateMachineArn --definition "file://$definitionPath"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Step Functions state machine updated successfully!" -ForegroundColor Green
    Write-Host "The workflow now includes proper error handling for YouTube download failures." -ForegroundColor Cyan
} else {
    Write-Host "❌ Failed to update state machine" -ForegroundColor Red
    Write-Host $result
}