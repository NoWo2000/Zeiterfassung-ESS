from nicegui import ui, app
from datetime import date
from classes.configuration import Configuration
import pandas as pd
import os
import time
from classes.auswertung import Auswertung # Import logic if needed, but we will reimplement viewing in NiceGUI
from classes.configuration import Configuration
import pandas as pd
import os
import time

class GuiNice:
    def __init__(self, config):
        self.config = config
        self.log_file = "log.csv"
        
        # UI Elements state
        self.date_input = None
        self.psp_input = None
        self.customer_input = None
        self.duration_input = None
        self.comment_input = None
        self.sleeptimer_input = None
        
        # Labels for feedback
        self.last_entry_label = None
        
        # Initialize UI
        self.setup_ui()
        self.refresh_last_entry()

    def setup_ui(self):
        ui.colors(primary='#5898d4', secondary='#262626', accent='#111b27', dark='#1d1d1d')
        
        # Tabs for navigation
        with ui.tabs().classes('w-full') as tabs:
            self.tab_booking = ui.tab('Buchung')
            self.tab_analysis = ui.tab('Auswertung')

        with ui.tab_panels(tabs, value=self.tab_booking).classes('w-full h-full p-0'):
            
            # --- BOOKING TAB ---
            with ui.tab_panel(self.tab_booking).classes('w-full items-center justify-start p-2 gap-2'):
                # ui.label('Smart ESS').classes('text-xl font-bold text-primary mb-2') # Removed as per user request
                
                with ui.card().classes('w-full max-w-md p-3 gap-2 no-shadow border-[1px]'):
                    # Date Input
                    with ui.row().classes('w-full items-center gap-2'):
                         self.date_input = ui.input('Datum').props('dense placeholder="dd.mm.yyyy"').classes('flex-grow')
                         with self.date_input.add_slot('append'):
                            ui.icon('event').classes('cursor-pointer').on('click', lambda: date_dialog.open())
                            with ui.dialog() as date_dialog, ui.card():
                                ui.date().on('change', lambda e: (self.date_input.set_value(pd.to_datetime(e.value).strftime("%d.%m.%Y")), date_dialog.close()))

                    # PSP Input
                    self.psp_input = ui.select(
                        options=self.config.get_combobox_value("psp"), 
                        label='PSP', 
                        with_input=True
                    ).props('dense options-dense').classes('w-full')
                    
                    # Customer Input
                    self.customer_input = ui.select(
                        options=self.config.get_combobox_value("customer"), 
                        label='Kunde', 
                        with_input=True
                    ).props('dense options-dense').classes('w-full')
                    
                    # Duration Input
                    self.duration_input = ui.select(
                        options=self.config.get_combobox_value("times"), 
                        label='Dauer (min)', 
                        with_input=True
                    ).props('dense options-dense').classes('w-full')

                    # Comment Input
                    self.comment_input = ui.select(
                        options=self.config.get_combobox_value("comments"),
                        label='Kommentar',
                        with_input=True,
                        new_value_mode='add-unique'
                    ).props('dense options-dense').classes('w-full')
                    
                    # Save Button
                    ui.button('Speichern', on_click=self.save_entry).props('dense').classes('w-full bg-primary')

                    ui.separator().classes('my-1')

                    # Sleeptimer
                    with ui.row().classes('w-full gap-2 items-center'):
                        self.sleeptimer_input = ui.select(
                            options=self.config.get_combobox_value("times"), 
                            label='Sleeptimer (min)', 
                            with_input=True
                        ).props('dense options-dense').classes('flex-grow')
                        ui.button('Start', on_click=self.start_sleeptimer).props('dense outline').classes('w-auto')

                # Info Section (Fixed at bottom or just below)
                with ui.card().classes('w-full max-w-md p-2 bg-gray-100 dark:bg-gray-800 text-xs gap-1'):
                    self.last_entry_label = ui.label('Lade...').classes('text-gray-600 dark:text-gray-400 whitespace-pre-line')

            # --- ANALYSIS TAB ---
            with ui.tab_panel(self.tab_analysis).classes('w-full p-2'):
                ui.label('Log Auswertung').classes('text-lg font-bold mb-2')
                self.analysis_container = ui.column().classes('w-full')
                ui.button('Aktualisieren', on_click=self.show_analysis_table).props('dense outline').classes('w-full mb-2')
                self.show_analysis_table() # Initial load

    def show_analysis_table(self):
        self.analysis_container.clear()
        if not os.path.exists(self.log_file):
            with self.analysis_container:
                ui.label('Keine Log-Datei gefunden.').classes('text-red-500')
            return

        try:
            df = pd.read_csv(self.log_file, sep=";", decimal=",", encoding="utf-8")
            
            # Ensure Date is datetime for sorting
            df['DateObj'] = pd.to_datetime(df['Datum'], dayfirst=True)
            df = df.sort_values(by=['DateObj', 'PSP'], ascending=[False, True])
            
            # Calculate total hours
            total_hours_all = df['Zeit'].sum()

            with self.analysis_container:
                # ui.label(f'Gesamtstunden: {total_hours_all:.2f} h').classes('text-xl font-bold mb-4 w-full text-center') # Removed as per user request
                
                # Group by Date
                for date_val, date_group in df.groupby('Datum', sort=False):
                    date_hours = date_group['Zeit'].sum()
                    
                    with ui.expansion(f'{date_val} ({date_hours:.2f} h)').classes('w-full bg-gray-100 dark:bg-gray-800 mb-1 rounded'):
                        # Group by PSP within Date
                        for psp_val, psp_group in date_group.groupby('PSP'):
                            psp_hours = psp_group['Zeit'].sum()
                            
                            with ui.expansion(f'{psp_val} ({psp_hours:.2f} h)').classes('w-full ml-4 border-l-2 border-primary pl-2'):
                                # Detailed Table for this PSP on this Date
                                cols = [
                                    {'name': 'Kunde', 'label': 'Kunde', 'field': 'Kunde', 'align': 'left'},
                                    {'name': 'Zeit', 'label': 'Zeit (h)', 'field': 'Zeit', 'align': 'right'},
                                    {'name': 'Kommentar', 'label': 'Kommentar', 'field': 'Kommentar', 'align': 'left'},
                                ]
                                # Convert Timestamp to string in records to avoid JSON serialization error
                                records = psp_group.to_dict('records')
                                for record in records:
                                    if 'DateObj' in record:
                                        del record['DateObj'] # Remove the helper column
                                
                                ui.table(columns=cols, rows=records).props('dense flat hide-bottom').classes('w-full')
        except Exception as e:
            with self.analysis_container:
                ui.label(f'Fehler bei der Auswertung: {e}').classes('text-red-500')

    def save_entry(self):
        # Validation
        if not self.psp_input.value:
            ui.notify('Bitte gib ein PSP-Element an!', type='negative')
            return
        if not self.duration_input.value:
            ui.notify('Bitte gib eine Bearbeitungszeit an!', type='negative')
            return

        # Prepare Data
        timestamp = self.date_input.value if self.date_input.value else date.today().strftime("%d.%m.%Y")
        kw = pd.to_datetime(timestamp, dayfirst=True).strftime("%U")
        
        try:
            duration_min = float(self.duration_input.value)
            time_in_h = str(round(duration_min / 60, 4)).replace(".", ",")
        except ValueError:
             ui.notify('Bitte gib eine gültige Zahl für die Dauer an!', type='negative')
             return

        entry_text = ";".join([
            timestamp,
            kw,
            self.psp_input.value,
            self.customer_input.value or "",
            time_in_h,
            self.comment_input.value or ""
        ])

        # Write to File
        file_exists = os.path.exists(self.log_file)
        with open(self.log_file, "a", encoding="utf-8") as datei:
            if not file_exists:
                datei.write("Datum;Kalenderwoche;PSP;Kunde;Zeit;Kommentar")
            datei.write(f"\n{entry_text}")

        ui.notify('Eintrag gespeichert!', type='positive')
        self.clear_inputs()
        self.refresh_last_entry()

    def start_sleeptimer(self):
        try:
            minutes = int(self.sleeptimer_input.value)
            self.save_entry()
            ui.notify(f'Sleeptimer gestartet für {minutes} Minuten. Fenster wird minimiert (simuliert).', type='info')
            
            # NiceGUI runs in browser, so "hiding" window is tricky in native mode. 
            # We can however use a timer to show a notification/dialog later.
            ui.timer(minutes * 60, lambda: ui.notify('Sleeptimer abgelaufen! Zeit wieder an die Arbeit zu gehen.', close_button='OK', type='warning', timeout=None), once=True)
            
        except (ValueError, TypeError):
            ui.notify('Bitte gültige Minuten für Sleeptimer eingeben', type='negative')

    def clear_inputs(self):
        self.date_input.value = None
        self.psp_input.value = None
        self.customer_input.value = None
        self.duration_input.value = None
        self.comment_input.value = None
        self.sleeptimer_input.value = None

    def refresh_last_entry(self):
        if not os.path.exists(self.log_file):
            self.last_entry_label.text = "Keine Einträge vorhanden."
            return

        try:
            df = pd.read_csv(self.log_file, sep=";", decimal=",", encoding="utf-8")
            if df.empty:
                 self.last_entry_label.text = "Keine Einträge vorhanden."
                 return
            
            last_row = df.iloc[-1]
            today_str = date.today().strftime("%d.%m.%Y")
            todays_sum = df[df['Datum'] == today_str]['Zeit'].sum()

            info_text = (
                f"Letzter Eintrag: {last_row['Datum']} | {last_row['PSP']} | {last_row['Kunde']} | {last_row['Zeit']}h\n"
                f"Heutige Arbeitszeit: {todays_sum:.4f} h"
            )
            self.last_entry_label.text = info_text
        except Exception as e:
            self.last_entry_label.text = f"Fehler beim Lesen der Log-Datei: {e}"

def run_app():
    config = Configuration()
    GuiNice(config)
    # Native mode for desktop-like experience
    # Native mode for desktop-like experience
    ui.run(native=True, window_size=(500, 600), title="Smart ESS", reload=False)

if __name__ == "__main__":
    run_app()
