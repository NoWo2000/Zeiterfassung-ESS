#Autor: Paul Rosenberg

python setup.py

#Copy config.ini
Copy-Item .\config.ini .\dist\config.ini

#Copy Befehl für csv und xlsx Datei
#Copy CSV file is not required
Copy-Item .\Auswertung.xlsx .\dist\Auswertung.xlsx

#Create Zip Folder
Compress-Archive -Path .\dist\* -DestinationPath Zeiterfassung.zip