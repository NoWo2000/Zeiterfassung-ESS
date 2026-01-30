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

    def get_items(self, section: str) -> List[tuple]:
        """
        Gibt die Items einer Sektion als Liste von (Key, Value) Tupeln zurück.
        """
        if self.config.has_section(section):
            return self.config.items(section)
        return []

    def add_item(self, section: str, item: str, value: str = None):
        """
        Fügt ein Item zu einer Sektion hinzu (optional mit Wert) und speichert die Konfiguration.
        """
        if not self.config.has_section(section):
            self.config.add_section(section)
        
        # Always set, updating if exists or creating if not
        self.config.set(section, item, value)
        self.save()

    def remove_item(self, section: str, item: str):
        """
        Entfernt ein Item aus einer Sektion und speichert die Konfiguration.
        """
        if self.config.has_section(section):
            self.config.remove_option(section, item)
            self.save()

    def save(self):
        """
        Speichert die aktuelle Konfiguration in die config.ini Datei.
        """
        with open("config.ini", "w", encoding="utf-8") as configfile:
            self.config.write(configfile)

    def delete_all(self):
        """
        Löscht alle aktuell geladenen Sektionen aus dem ConfigParser-Objekt (intern).
        """
        self.config.clear()
        # Re-apply defaults if any were needed, but ConfigParser() init handled that. 
        # Actually clear() might wipe optionxform too on some versions? 
        # Safer to just remove sections.
        for section in self.config.sections():
            self.config.remove_section(section)
