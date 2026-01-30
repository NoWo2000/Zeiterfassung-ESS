from configparser import ConfigParser

class Configuration:
    def __init__(self):
        self.config = ConfigParser(allow_no_value=True)
        self.config.optionxform = str
        self.config.read("config.ini", encoding="utf-8")

    def get_combobox_value(self, name):
        return self.config.options(name)

    def update(self):
        self.delete_all()
        self.config.read("config.ini")

    def delete_all(self):
        for section in self.config.sections():
            self.config.remove_section(section)
