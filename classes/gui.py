from tkinter import Tk, Label, Button, Menu
from tkinter import messagebox, ttk
import sv_ttk
import time 
import time
from os import path as os_path
from webbrowser import open as webbrowser_open
from tkcalendar import DateEntry
from datetime import date
from pandas import read_csv as pd_read_csv, isnull as pb_isnull

import platform
import subprocess
import sys
from classes.auswertung import Auswertung

# Konstanten für Dateinamen
LOG_FILE = "log.csv"
CONFIG_FILE = "config.ini"


class Gui:
    def __init__(self, config) -> None:

        # window configuration
        self.configure_window()

        # labelconfiguration
        self.configure_labels()

        # entryfield configuration
        self.configure_entryfields(config)

        # button config
        self.configure_buttons()

        # Menu configuration
        self.configure_menu(config)

        # build GUI
        self.configure_gui_order()

        # Load last entry
        self.get_last_value()
        today = date.today()
        self.todays_hours_sum = self.sum_time_for_day(today.strftime("%d.%m.%Y"))

        # Auswertungsobjekt erstellen
        self.auswertung = Auswertung("log.csv")


        self.my_label_last_entry_information.config(
            text=f"Heutige Arbeitszeit (h): {self.todays_hours_sum}"
        )

    def save_button_action(self):
        self.entry_text = (
            self.entrybox_option_date.get()
            + self.entrybox_psp.get()
            + self.entrybox_customer.get()
            + self.entrybox_duration.get()
            + self.entrybox_comment.get()
        )
        if self.entry_text == "":
            self.my_label_last_timestamp.config(
                text="Bitte zurerst eine Eingabe tätigen"
            )
            messagebox.showerror(message="Bitte zuerst Daten angeben", title="Error #1")
        else:
            if self.entrybox_psp.get() == "":
                messagebox.showerror(
                    message="Bitte gib ein PSP-Element an!", title="Error #3"
                )
            else:
                if self.entrybox_option_date.get() == "":
                    self.timestamp = time.strftime("%d.%m.%Y")
                else:
                    self.timestamp = self.entrybox_option_date.get()
                self.kw = time.strftime("%U")
                self.last_timestamp = time.strftime("%H:%M")
                if str(self.entrybox_duration.get()) == "":
                    messagebox.showerror(
                        message="Bitte gib eine Bearbeitungszeit an!", title="Error #2"
                    )
                else:
                    try:
                        duration_min = float(self.entrybox_duration.get())
                        self.time_in_h = str(round(duration_min / 60, 4))
                    except ValueError:
                        messagebox.showerror(
                            message="Bitte gib eine gültige Zahl für die Dauer an!", title="Error #2"
                        )
                        return
                self.time_in_h = self.time_in_h.replace(".", ",")
                self.entry_text = ";".join(
                    [
                        self.timestamp,
                        self.kw,
                        self.entrybox_psp.get(),
                        self.entrybox_customer.get(),
                        self.time_in_h,
                        self.entrybox_comment.get(),
                    ]  # Datum;Kalenderwoche;PSP;Kunde;Zeit;Kommentar
                )
                if not os_path.exists("log.csv"):
                    datei = open("log.csv", "w", encoding="utf-8")
                    datei.write("Datum;Kalenderwoche;PSP;Kunde;Zeit;Kommentar")
                else:
                    datei = open("log.csv", "a", encoding="utf-8")
                datei.write(f"\n{self.entry_text}")
                datei.close()
                today = date.today()
                self.todays_hours_sum = self.sum_time_for_day(today.strftime("%d.%m.%Y"))
                self.my_label_last_timestamp.config(
                    text=f"Letzter Eintrag um {self.last_timestamp}"
                )
                self.my_label_last_entry_information.config(
                    text=f"{self.entrybox_psp.get()}  {self.entrybox_customer.get()}  {self.time_in_h}h  {self.entrybox_comment.get()}\nHeutige Arbeitszeit (h): {self.todays_hours_sum}"
                )
                self.entrybox_option_date.set_date(date.today())
                self.entrybox_psp.set("")
                self.entrybox_customer.set("")
                self.entrybox_duration.set("")
                self.entrybox_comment.set("")
                self.entrybox_sleeptimer.set("")

    def sleeptimer_button_action(self):
        """
        Aktiviert den Sleeptimer. Das Fenster wird ausgeblendet und nach der
        angegebenen Zeit wieder eingeblendet.
        """
        timer_value = self.entrybox_sleeptimer.get()
        if not timer_value:
            messagebox.showerror("Fehler", "Bitte geben Sie einen Wert für den Sleep-Timer ein.")
            return

        try:
            sleep_min = int(timer_value)
        except ValueError:
             messagebox.showerror("Fehler", "Bitte geben Sie eine gültige Zahl ein.")
             return
        
        # Datensatz speichern
        self.save_button_action()

        # Fenster ausblenden
        self.window.withdraw()
        
        # Timer starten (in Millisekunden umrechnen)
        self.window.after(sleep_min * 60 * 1000, self.wake_up)

    def wake_up(self):
        """
        Callback-Funktion für den Sleeptimer.
        Bringt das Fenster zurück und zeigt eine Erinnerung.
        """
        messagebox.showinfo(message="Arbeitszeiten Eintragen", title="Erinnerung")
        self.window.deiconify()

    def action_get_info_dialog(self):
        m_text = "\
                ************************\n\
                Autor: Noah Wollenhaupt\n\
                Date: 20.01.23\n\
                Version: 1.0.5\n\
                ************************"
        messagebox.showinfo(message=m_text, title="Infos")

    def open_excel(self):
        """Öffnet die Auswertungs-Exceldatei abhängig vom Betriebssystem."""
        file_path = "Auswertung.xlsx"
        if not os_path.exists(file_path):
             messagebox.showwarning("Datei nicht gefunden", f"Die Datei {file_path} wurde nicht gefunden.")
             return

        system_platform = platform.system()
        try:
            if system_platform == "Windows":
                os.startfile(file_path)
            elif system_platform == "Darwin":  # macOS
                subprocess.call(["open", file_path])
            else:  # Linux
                subprocess.call(["xdg-open", file_path])
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Öffnen der Datei: {e}")

    def show_table(self): 
        self.auswertung.run_analysis()

    def sum_time_for_day(self, date):
        self.data = pd_read_csv("log.csv", sep=";", decimal=",")
            # Ignore case in PSP and customer columns 
        self.data["PSP"] = self.data["PSP"].str.upper() 
        self.data["Kunde"] = self.data["Kunde"].str.upper() 

        # Filter the data by the desired date
        filtered_data = self.data[self.data["Datum"] == date]

        # Sum time for the filtered data
        total_time = filtered_data["Zeit"].sum() 

        return total_time
 

    def open_configuration(self):
        """Öffnet die Konfigurationsdatei abhängig vom Betriebssystem."""
        if not os_path.exists(CONFIG_FILE):
             messagebox.showwarning("Datei nicht gefunden", f"Die Datei {CONFIG_FILE} wurde nicht gefunden.")
             return

        system_platform = platform.system()
        try:
            if system_platform == "Windows":
                 subprocess.run(["notepad.exe", CONFIG_FILE])
            elif system_platform == "Darwin":  # macOS
                subprocess.call(["open", "-t", CONFIG_FILE]) # -t opens with default text editor
            else:  # Linux
                subprocess.call(["xdg-open", CONFIG_FILE])
        except Exception as e:
             messagebox.showerror("Fehler", f"Fehler beim Öffnen der Datei: {e}")

    def reload_configuration(self, config):
        config.update()
        self.configure_entryfields(config)
        self.configure_gui_order()

    def open_update_site(self):
        update_url = "https://gitlab.wollenhaupt.xyz/Nowo/zeiterfassungstool/-/releases"
        webbrowser_open(update_url, new=0, autoraise=True)

    def get_last_value(self):
        if os_path.exists("log.csv"):
            last_line = ""
            with open("log.csv", "r", encoding="utf-8") as f:
                last_line = f.readlines()[-1]
            if last_line != "Datum;Kalenderwoche;PSP;Kunde;Zeit;Kommentar" and last_line != "Datum;Kalenderwoche;PSP;Kunde;Zeit;Kommentar\n":
                last_line_arr = last_line.split(";")
                self.my_label_last_timestamp.config(
                    text=f"Letzter Eintrag am {last_line_arr[0]}"
                )
                self.my_label_last_entry_information.config(
                    text=f"{last_line_arr[2]}  {last_line_arr[3]}  {last_line_arr[4]}h  {last_line_arr[5]}"
                )


    # Configuration Section start:

    def configure_window(self):
        self.window = Tk()
        # window configurations
        self.window.title("Smart ESS")
        # self.window.geometry("520x450") # Let auto-size handle it or keep it if preferred
        self.window.resizable(False, False)
        # self.window.attributes("-alpha", 0.975)
        
        # Apply Sun Valley Theme
        # Standard Modern: Light Theme by default
        sv_ttk.set_theme("light")

        # Create a main frame to hold content (important for background color in sv-ttk)
        self.main_frame = ttk.Frame(self.window, padding=20)
        self.main_frame.pack(fill="both", expand=True)

    def configure_labels(self):
        self.my_label_option_date = ttk.Label(self.main_frame, text="Datum (Optional): ")
        self.my_label_psp = ttk.Label(self.main_frame, text="PSP: ")
        self.my_label_customer = ttk.Label(self.main_frame, text="Kunde: ")
        self.my_label_duration = ttk.Label(self.main_frame, text="Dauer (min): ")
        self.my_label_sleeptimer = ttk.Label(self.main_frame, text="Sleeptimer (min): ")
        self.my_label_last_timestamp = ttk.Label(self.main_frame, text="")
        self.my_label_last_entry_information = ttk.Label(self.main_frame, text="")
        self.my_label_comment = ttk.Label(self.main_frame, text="Kommentar: ")

    def configure_entryfields(self, config):
        width_val = 25
        self.entrybox_option_date = DateEntry(
            self.main_frame, width=width_val, selectmode='day', date_pattern='dd.mm.yyyy'
        )

        self.entrybox_psp = ttk.Combobox(
            self.main_frame, width=width_val, values=config.get_combobox_value("psp")
        )

        self.entrybox_customer = ttk.Combobox(
            self.main_frame, width=width_val, values=config.get_combobox_value("customer")
        )

        self.entrybox_duration = ttk.Combobox(
            self.main_frame, width=width_val, values=config.get_combobox_value("times")
        )

        self.entrybox_comment = ttk.Combobox(
            self.main_frame, width=width_val, values=config.get_combobox_value("comments")
        )

        self.entrybox_sleeptimer = ttk.Combobox(
            self.main_frame, width=width_val, values=config.get_combobox_value("times")
        )

    def configure_buttons(self):
        self.button_save = ttk.Button(
            self.main_frame, text="Speichern", command=self.save_button_action
        )
        self.button_sleeptimer = ttk.Button(
            self.main_frame, text="Sleeptimer", command=self.sleeptimer_button_action
        )

    def configure_menu(self, config):
        self.menulist = Menu(self.window)
        self.menu_file = Menu(self.menulist, tearoff=0)
        self.menu_configuration = Menu(self.menulist, tearoff=0)
        self.menu_help = Menu(self.menulist, tearoff=0)
        self.menu_analysis = Menu(self.menulist, tearoff=0) 

        self.menu_analysis.add_command(label="Tabelle", command=self.show_table) 
        self.menu_analysis.add_command(label="Excel", command=self.open_excel) 

        self.menu_help.add_command(label="Info", command=self.action_get_info_dialog)
        self.menu_file.add_command(label="Update verfügbar?", command=self.open_update_site)
        self.menu_configuration.add_command(label="Öffnen", command=self.open_configuration)
        self.menu_configuration.add_command(label="Neu Einlesen", command= lambda: self.reload_configuration(config))
        self.menu_file.add_command(label="Beenden", command=self.window.quit)

        self.menulist.add_cascade(label="Programm", menu=self.menu_file)
        self.menulist.add_cascade(label="Auswertung", menu=self.menu_analysis) 
        self.menulist.add_cascade(label="Konfiguration", menu=self.menu_configuration)
        self.menulist.add_cascade(label="Hilfe", menu=self.menu_help)
        self.window.config(menu=self.menulist)

    def configure_gui_order(self):
        # Compact layout
        pad_x = 5
        pad_y = 5
        
        # Row 0: Date
        self.my_label_option_date.grid(row=0, column=0, padx=pad_x, pady=pad_y, sticky="w")
        self.entrybox_option_date.grid(row=0, column=1, padx=pad_x, pady=pad_y, sticky="ew")
        
        # Row 1: PSP
        self.my_label_psp.grid(row=1, column=0, padx=pad_x, pady=pad_y, sticky="w")
        self.entrybox_psp.grid(row=1, column=1, padx=pad_x, pady=pad_y, sticky="ew")
        
        # Row 2: Customer
        self.my_label_customer.grid(row=2, column=0, padx=pad_x, pady=pad_y, sticky="w")
        self.entrybox_customer.grid(row=2, column=1, padx=pad_x, pady=pad_y, sticky="ew")
        
        # Row 3: Duration
        self.my_label_duration.grid(row=3, column=0, padx=pad_x, pady=pad_y, sticky="w")
        self.entrybox_duration.grid(row=3, column=1, padx=pad_x, pady=pad_y, sticky="ew")
        
        # Row 4: Comment
        self.my_label_comment.grid(row=4, column=0, padx=pad_x, pady=pad_y, sticky="w")
        self.entrybox_comment.grid(row=4, column=1, padx=pad_x, pady=pad_y, sticky="ew")
        
        # Row 5: Save Button (Full width)
        self.button_save.grid(row=5, column=0, columnspan=2, padx=pad_x, pady=(10, 5), sticky="ew")
        
        # Row 6: Sleeptimer (Input + Button in same row if possible, or stacked compactly)
        # Let's put Label and Input on one row, Button on next, but tight.
        self.my_label_sleeptimer.grid(row=6, column=0, padx=pad_x, pady=(15, pad_y), sticky="w")
        self.entrybox_sleeptimer.grid(row=6, column=1, padx=pad_x, pady=(15, pad_y), sticky="ew")
        
        self.button_sleeptimer.grid(row=7, column=0, columnspan=2, padx=pad_x, pady=pad_y, sticky="ew")
        
        # Row 8+: Info
        self.my_label_last_timestamp.grid(row=8, column=0, columnspan=2, padx=pad_x, pady=(15, 2))
        self.my_label_last_entry_information.grid(row=9, column=0, columnspan=2, padx=pad_x, pady=2)

    # Configuration section end
