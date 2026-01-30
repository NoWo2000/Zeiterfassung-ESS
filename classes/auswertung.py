import tkinter as tk
from tkinter import ttk
from datetime import date as dt_date
import pandas as pd

class Auswertung:
    def __init__(self, log_file):
        self.log_file = log_file

    def analyze_log_file(self) -> dict | None:
        """
        Liest die Log-Datei ein und aggregiert die Arbeitszeiten nach Datum, PSP-Element und Kunde.
        Verwendet Pandas für das Einlesen, analog zur Hauptanwendung.
        """
        try:
            # Pandas zum Einlesen verwenden, analog zu sum_time_for_day in gui.py
            # Wir gehen davon aus, dass das Trennzeichen ';' ist (wie beim Schreiben).
            df = pd.read_csv(self.log_file, sep=";", decimal=",", encoding="utf-8")
            
            # Spaltennamen normalisieren (strip whitespace)
            df.columns = df.columns.str.strip()
            
            # Sicherstellen, dass notwendige Spalten existieren
            required_columns = ["Datum", "PSP", "Kunde", "Zeit", "Kommentar"]
            if not all(col in df.columns for col in required_columns):
                print(f"Fehler: Fehlende Spalten in {self.log_file}")
                return None

            result = {}
            
            for index, row in df.iterrows():
                date_val = str(row["Datum"])
                psp_element = str(row["PSP"])
                customer = str(row["Kunde"])
                
                # Zeit ist bereits float dank decimal="," im read_csv
                time_val = row["Zeit"]
                if pd.isna(time_val):
                    time_val = 0.0
                else:
                    time_val = float(time_val)

                comment = str(row["Kommentar"]) if not pd.isna(row["Kommentar"]) else ""

                if date_val not in result:
                    result[date_val] = {}

                if psp_element not in result[date_val]:
                    result[date_val][psp_element] = {"__total__": 0.0}

                if customer not in result[date_val][psp_element]:
                    result[date_val][psp_element][customer] = {"__total__": 0.0, "__comment__": ""}

                result[date_val][psp_element][customer]["__total__"] += time_val
                result[date_val][psp_element]["__total__"] += time_val
                result[date_val][psp_element][customer]["__comment__"] = comment

            return result

        except Exception as e:
            print(f"Fehler beim Analysieren der Log-Datei: {e}")
            return None

    def display_results(self, log_data: dict):
        """
        Zeigt die Ergebnisse in einem neuen Toplevel-Fenster an (Treeview).
        """
        def jump_to_date():
            selected_date = date_combobox.get()
            if selected_date in log_data:
                for child in tree.get_children():
                    values = tree.item(child)['values']
                    if values[0] == selected_date:
                        # item ID
                        tree.see(child)
                        tree.selection_set(child)
                        break

        # Toplevel statt Tk, damit die Hauptanwendung nicht blockiert wird
        # und kein zweiter Mainloop gestartet wird (was zu Fehlern führen kann).
        window = tk.Toplevel()
        window.title("Log-Auswertung")

        frame = tk.Frame(window)
        frame.pack(padx=10, pady=10, anchor="nw")

        # Das heutige Datum erhalten
        today = dt_date.today().strftime("%d.%m.%Y")

        # Erstelle den Combobox für die Datumsauswahl und setze das heutige Datum als Standardwert
        date_combobox = ttk.Combobox(frame, values=list(log_data.keys()))
        date_combobox.set(today)
        date_combobox.grid(row=0, column=0)

        jump_button = ttk.Button(frame, text="Zum ausgewählten Tag springen", command=jump_to_date)
        jump_button.grid(row=0, column=1, padx=5)

        tree = ttk.Treeview(window)
        tree["columns"] = ("Datum", "PSP-Element", "Kunde", "Zeit", "Kommentar")  # Hinzufügen der Kommentar-Spalte

        tree.heading("Datum", text="Datum")
        tree.heading("PSP-Element", text="PSP-Element")
        tree.heading("Kunde", text="Kunde")
        tree.heading("Zeit", text="Zeit")
        tree.heading("Kommentar", text="Kommentar")  # Überschrift für die Kommentar-Spalte

        colors = ["#ffe6cc", "#ccffff"]  # Liste von Farben für die Datumszeilen
        color_index = 0

        for date, psp_elements in log_data.items():
            total_time = sum([psp_element["__total__"] for psp_element in psp_elements.values()])
            comment = ""  # Kommentar initialisieren

            tree.insert("", tk.END, values=("", "", "", "", ""), tags=("date",))  # Einfügen der leeren Zeile

            if "__comment__" in psp_elements:
                comment = psp_elements["__comment__"]  # Kommentar für das Datum

            tree.insert("", tk.END, values=(date, "", "", total_time, comment), tags=("heading", "date"), iid=f"date_{date}")

            for psp_element, customers in psp_elements.items():
                if psp_element != "__total__" and psp_element != "__comment__":
                    psp_total_time = customers["__total__"]
                    tree.insert("", tk.END, values=("", psp_element, "", psp_total_time, ""), tags=("total", f"date_{date}"))

                    for customer, time_data in customers.items():
                        if customer != "__total__" and customer != "__comment__":
                            time = time_data["__total__"]
                            comment = time_data["__comment__"]
                            tree.insert("", tk.END, values=(date, psp_element, customer, time, comment), tags=(f"date_{date}"))

            # Farbe für die Datumszeile festlegen
            tree.tag_configure(f"date_{date}", background=colors[color_index % len(colors)])
            color_index += 1

        tree["height"] = 20

        tree.tag_configure("heading", font=("Arial", 10, "bold"))
        tree.tag_configure("total", font=("Arial", 10, "bold"))
        tree.tag_configure("date", font=("Arial", 10, "bold"))

        tree.pack(fill="both", expand=True)
        
        # Initialen Sprung ausführen (optional)
        jump_to_date()
        
        # window.mainloop() entfernen, da wir uns im Loop der Hauptanwendung befinden

    def run_analysis(self):
        log_data = self.analyze_log_file()
        if log_data:
            self.display_results(log_data)


