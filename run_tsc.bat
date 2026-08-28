@echo off
cd /d "c:\Users\ADMIN\OneDrive\Desktop\AtmoGraph AI\atmograph-ai\frontend"
node_modules\.bin\tsc.cmd --noEmit --project tsconfig.json 2>&1
echo TSC_EXIT=%ERRORLEVEL%
