@echo off
echo ========================================
echo  COMPILAR BAIAK BOT DLL
echo ========================================
echo.

:: Verifica se tem compilador
where cl >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo Usando Visual Studio Compiler...
    goto :compile_vs
)

where g++ >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo Usando MinGW G++...
    goto :compile_mingw
)

echo ERRO: Nenhum compilador encontrado!
echo.
echo Instale um dos seguintes:
echo   1. Visual Studio (com C++ tools)
echo   2. MinGW-w64 (g++)
echo.
pause
exit /b 1

:compile_vs
cl /LD /O2 /EHsc BaiakBotDLL.cpp /link /OUT:BaiakBot.dll
if %ERRORLEVEL% == 0 (
    echo.
    echo Compilado com sucesso: BaiakBot.dll
    del BaiakBotDLL.obj 2>nul
) else (
    echo.
    echo ERRO na compilacao!
)
goto :end

:compile_mingw
g++ -shared -O2 -o BaiakBot.dll BaiakBotDLL.cpp -static-libgcc -static-libstdc++
if %ERRORLEVEL% == 0 (
    echo.
    echo Compilado com sucesso: BaiakBot.dll
) else (
    echo.
    echo ERRO na compilacao!
)
goto :end

:end
echo.
pause
