from configparser import ConfigParser
from typing import List

class Configuration:
    """
    Klasse ("Configuration") verwaltet das Einlesen und Bereitstellen der Konfiguration
    aus der config.ini Datei.
    """
    def __init__(self):
        self.config = ConfigParser(allow_no_value=True)
        # Groß-/Kleinschreibung beibehalten
        self.config.optionxform = str
        self.config.read("config.ini", encoding="utf-8")

    def get_combobox_value(self, name: str) -> List[str]:
        """
        Gibt die Optionen einer Sektion als Liste zurück.
        
        Args:
            name (str): Name der Sektion (z.B. 'customer', 'psp').
        
        Returns:
            List[str]: Liste der Optionen.
        """
        if self.config.has_section(name):
            return self.config.options(name)
        return []

    def update(self):
        """
        Lädt die Konfiguration neu aus der Datei.
        """
        self.delete_all()
        self.config.read("config.ini", encoding="utf-8")

    def delete_all(self):
        """
        Löscht alle aktuell geladenen Sektionen aus dem ConfigParser-Objekt.
        """
        for section in self.config.sections():
            self.config.remove_section(section)
