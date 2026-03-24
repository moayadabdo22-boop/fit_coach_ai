# Start both backend and frontend servers

Write-Host "Starting AI Coach Fitness Platform..." -ForegroundColor Green
Write-Host ""

# Start backend in new window
Write-Host "[BACKEND] Starting Backend Server..." -ForegroundColor Cyan
Write-Host "URL: http://localhost:8002" -ForegroundColor Gray
$backendPath = "D:\chatbot coach\fit-coach-ai-main\ai_backend"
$backendCmd = "cd '$backendPath'; uvicorn main:app --host 127.0.0.1 --port 8002 --reload"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -WindowStyle Normal

# Wait for backend to start
Start-Sleep -Seconds 4

# Start frontend in new window  
Write-Host "[FRONTEND] Starting Frontend Server..." -ForegroundColor Cyan
Write-Host "URL: http://localhost:5173" -ForegroundColor Gray
$frontendPath = "D:\chatbot coach\fit-coach-ai-main"
$frontendCmd = "cd '$frontendPath'; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd -WindowStyle Normal

Write-Host ""
Write-Host "SERVERS STARTED!" -ForegroundColor Green
Write-Host ""
Write-Host "Access your AI Coach at:" -ForegroundColor Yellow
Write-Host "  Frontend:  http://localhost:5173" -ForegroundColor White
Write-Host "  Backend:   http://localhost:8002" -ForegroundColor White
Write-Host "  API Docs:  http://localhost:8002/docs" -ForegroundColor White
Write-Host ""
Write-Host "New windows opened with server output. Check them for details." -ForegroundColor Gray
