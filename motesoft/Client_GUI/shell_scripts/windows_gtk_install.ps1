### THIS SCRIPT NEEDS TO BE RUN AS ADMINISTRATOR ###

try {choco} catch {Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))}
choco install -y --force --params "/InstallDir:C:\msys64" msys2

c:\msys64\msys2_shell.cmd -defterm -mingw64 -no-start -full-path -here -c "pacman -Suy --noconfirm"
c:\msys64\msys2_shell.cmd -defterm -mingw64 -no-start -full-path -here -c "pacman -S --noconfirm mingw-w64-x86_64-gtk3 mingw-w64-x86_64-python3 mingw-w64-x86_64-python3-gobject mingw-w64-x86_64-python3-matplotlib"
c:\msys64\msys2_shell.cmd -defterm -mingw64 -no-start -full-path -here -c "pacman -S mingw-w64-x86_64-python-pip"
c:\msys64\msys2_shell.cmd -defterm -mingw64 -no-start -full-path -here -c "pip3 install matplotlib labjack_ljm"

echo "installation complete, if you're seeing this message it probably all worked."