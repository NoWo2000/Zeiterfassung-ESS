from classes.gui import Gui
from classes.configuration import Configuration


if __name__ == "__main__":
    config = Configuration()
    gui = Gui(config)
    gui.window.mainloop()

