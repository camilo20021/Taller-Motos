@echo off
REM ============================================================
REM  Gestion de Taller - Permitir conexion de tablets por Wi-Fi
REM ============================================================
REM  Windows bloquea por defecto que otros dispositivos se conecten.
REM  Este archivo abre el puerto 5000 para que las tablets del taller
REM  (en el mismo Wi-Fi) puedan entrar al programa.
REM
REM  Ejecutar UNA sola vez:  clic derecho -> "Ejecutar como administrador".
REM ============================================================

netsh advfirewall firewall delete rule name="Gestion de Taller (tablets)" >nul 2>&1
netsh advfirewall firewall add rule name="Gestion de Taller (tablets)" dir=in action=allow protocol=TCP localport=5000

echo.
echo ============================================================
echo  Listo. Las tablets en el mismo Wi-Fi ya pueden conectarse
echo  a la direccion que muestra el programa (http://IP:5000).
echo ============================================================
echo.
pause
