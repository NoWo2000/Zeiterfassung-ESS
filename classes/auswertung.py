import csv
import tkinter as tk
from tkinter import ttk
from datetime import date as dt_date

class Auswertung:
    def __init__(self, log_file):
        self.log_file = log_file

    def analyze_log_file(self):
        result = {}
        
        # Mögliche Trennzeichen, die ausprobiert werden können
        delimiters = [';', ',', '\t']
        
        for delimiter in delimiters:
            try:
                with open(self.log_file, 'r') as file:
                    reader = csv.reader(file, delimiter=delimiter)
                    next(reader)  # Überspringe die Header-Zeile
                    for row in reader:
                        if len(row) >= 6:  # Überprüfe, ob genügend Spalten vorhanden sind
                            date = row[0]
                            psp_element = row[2]
                            customer = row[3]
                            time = float(row[4].replace(',', '.'))  # Konvertiere das Zeitformat in einen Float-Wert
                            comment = row[5]  # Kommentar aus der CSV-Datei

                            # Überprüfe, ob das Datum bereits im Ergebnis enthalten ist, andernfalls füge es hinzu
                            if date not in result:
                                result[date] = {}

                            # Überprüfe, ob das PSP-Element bereits im Ergebnis enthalten ist, andernfalls füge es hinzu
                            if psp_element not in result[date]:
                                result[date][psp_element] = {"__total__": 0.0}

                            # Überprüfe, ob der Kunde bereits im Ergebnis enthalten ist, andernfalls füge ihn hinzu
                            if customer not in result[date][psp_element]:
                                result[date][psp_element][customer] = {"__total__": 0.0, "__comment__": ""}

                            # Addiere die Zeit zum Gesamtzeit des Kunden für das PSP-Element an diesem Tag
                            result[date][psp_element][customer]["__total__"] += time
                            result[date][psp_element]["__total__"] += time

                            # Füge den Kommentar zum Ergebnis hinzu
                            result[date][psp_element][customer]["__comment__"] = comment

                # Wenn der Code bis hierhin erfolgreich ausgeführt wird, wurde das richtige Trennzeichen gefunden
                print(f"Erfolgreiches Lesen der CSV-Datei mit Trennzeichen: {delimiter}")
                return result

            except csv.Error:
                # Wenn ein Fehler beim Lesen der CSV-Datei auftritt, probiere das nächste Trennzeichen
                continue
        
        # Wenn kein gültiges Trennzeichen gefunden wurde, gib eine Fehlermeldung aus
        print("Fehler: Kein gültiges Trennzeichen gefunden.")
        return None

    def display_results(self, log_data):
        def jump_to_date():
            selected_date = date_combobox.get()
            if selected_date in log_data:
                for child in tree.get_children():
                    values = tree.item(child)['values']
                    if values[0] == selected_date:
                        index = tree.get_children().index(child) + 1
                        tree.see(tree.get_children()[index])
                        break

        window = tk.Tk()
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
        jump_to_date()
        window.mainloop()

    def run_analysis(self):
        log_data = self.analyze_log_file()
        if log_data:
            self.display_results(log_data)

auswertung = Auswertung('log.csv')

