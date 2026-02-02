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
            self.tab_settings = ui.tab('Einstellungen')

        with ui.tab_panels(tabs, value=self.tab_booking).classes('w-full h-full p-0'):
            
            # --- BOOKING TAB ---
            with ui.tab_panel(self.tab_booking).classes('w-full items-center justify-start p-2 gap-2'):
                # ui.label('Smart ESS').classes('text-xl font-bold text-primary mb-2') # Removed as per user request
                
                with ui.card().classes('w-full max-w-md p-3 gap-2 no-shadow border-[1px]'):
                    # Date Input
                    with ui.row().classes('w-full items-center gap-2'):
                         self.date_input = ui.input('Datum (Optional)').props('dense placeholder="Leer für heute"').classes('flex-grow')
                         
                         # Date Dialog - define after input so self.date_input exists
                         with ui.dialog() as date_dialog, ui.card():
                            date_picker = ui.date()
                            
                            def on_date_change():
                                try:
                                    # NiceGUI Date picker returns YYYY-MM-DD string value
                                    date_str = date_picker.value
                                    if date_str:
                                        # Format to German standard dd.mm.yyyy
                                        formatted_date = pd.to_datetime(date_str).strftime("%d.%m.%Y")
                                        self.date_input.value = formatted_date
                                        date_dialog.close()
                                except Exception as ex:
                                    ui.notify(f"Fehler beim Datum: {ex}", type='negative')
                            
                            date_picker.on('update:model-value', on_date_change)
                         
                         with self.date_input.add_slot('append'):
                            ui.icon('event').classes('cursor-pointer').on('click', lambda: date_dialog.open())

                    # PSP Input
                    self.psp_input = ui.select(
                        options=self._get_psp_options(), 
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
                    # Using datalist for true free-text experience with suggestions
                    comment_options = self.config.get_combobox_value("comments")
                    self.comment_datalist = ui.element('datalist').props('id=comment_suggestions')
                    with self.comment_datalist:
                        for opt in comment_options:
                            ui.element('option').props(f'value="{opt}"')
                    
                    self.comment_input = ui.input(
                        label='Kommentar',
                    ).props('dense list=comment_suggestions').classes('w-full')
                    
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

            # --- SETTINGS TAB ---
            with ui.tab_panel(self.tab_settings).classes('w-full p-2 gap-2'):
                ui.label('Konfiguration verwalten').classes('text-lg font-bold mb-2')
                
                self.render_settings_list("PSP-Elemente", "psp", "Neues PSP-Element", with_description=True)
                self.render_settings_list("Kunden", "customer", "Neuer Kunde")
                self.render_settings_list("Kommentare (Vorlagen)", "comments", "Neuer Kommentar")

    def show_analysis_table(self):
        self.analysis_container.clear()
        if not os.path.exists(self.log_file):
            with self.analysis_container:
                ui.label('Keine Log-Datei gefunden.').classes('text-red-500')
            return

        try:
            df = pd.read_csv(self.log_file, sep=";", decimal=",", encoding="utf-8")
            
            # Ensure Date is datetime
            df['DateObj'] = pd.to_datetime(df['Datum'], dayfirst=True)
            df['Week'] = df['DateObj'].dt.isocalendar().week
            df['Year'] = df['DateObj'].dt.isocalendar().year
            
            # Sort by Year desc, Week desc, Date desc, PSP asc (Newest first)
            df = df.sort_values(by=['Year', 'Week', 'DateObj', 'PSP'], ascending=[False, False, False, True])
            
            # Helper for German Weekdays
            german_weekdays = {
                'Monday': 'Montag', 'Tuesday': 'Dienstag', 'Wednesday': 'Mittwoch',
                'Thursday': 'Donnerstag', 'Friday': 'Freitag', 'Saturday': 'Samstag', 'Sunday': 'Sonntag'
            }

            with self.analysis_container:
                # Group by Year+Week
                for (year_val, week_val), week_group in df.groupby(['Year', 'Week'], sort=False):
                    week_hours = week_group['Zeit'].sum()
                    
                    # Calculate Start (Monday) and End (Sunday) of the week from any date in that week
                    any_date = week_group['DateObj'].iloc[0]
                    start_of_week = any_date - pd.Timedelta(days=any_date.weekday())
                    end_of_week = start_of_week + pd.Timedelta(days=6)
                    
                    kw_label = f"KW {week_val:02d} ({start_of_week.strftime('%d.%m.%Y')} - {end_of_week.strftime('%d.%m.%Y')}) | {week_hours:.2f} h"
                    
                    with ui.expansion(kw_label).props('dense header-class="bg-blue-100 dark:bg-blue-900 rounded-t"').classes('w-full mb-1 border border-blue-200 dark:border-blue-800 rounded shadow-sm text-sm'):
                        
                        # Group by Date within Week
                        for date_val, date_group in week_group.groupby('Datum', sort=False):
                            date_hours = date_group['Zeit'].sum()
                            
                            # Determine weekday name
                            en_name = date_group['DateObj'].iloc[0].strftime("%A")
                            de_name = german_weekdays.get(en_name, en_name)
                            
                            day_label = f"{de_name}, {date_val} ({date_hours:.2f} h)"
                            
                            with ui.expansion(day_label).props('dense header-class="bg-gray-50 dark:bg-gray-800"').classes('w-full border-t border-gray-200 dark:border-gray-700 p-0'):
                                
                                
                                
                                # Global Header Removed as per user request (data is self-explanatory)

                                # Group by PSP within Date
                                for psp_val, psp_group in date_group.groupby('PSP'):
                                    psp_hours = psp_group['Zeit'].sum()
                                    
                                    # Static Header for PSP (No Expansion)
                                    with ui.column().classes('w-full ml-4 border-l-2 border-primary pl-2 mt-2 mb-1'):
                                        ui.label(f'{psp_val} ({psp_hours:.2f} h)').classes('font-bold text-sm')
                                        
                                        # Detailed Table for this PSP
                                        cols = [
                                            {'name': 'Kunde', 'label': 'Kunde', 'field': 'Kunde', 'align': 'left', 'classes': 'w-1/3', 'headerClasses': 'hidden'},
                                            {'name': 'Zeit', 'label': 'Zeit (h)', 'field': 'Zeit', 'align': 'right', 'classes': 'w-1/3', 'headerClasses': 'hidden'},
                                            {'name': 'Kommentar', 'label': 'Kommentar', 'field': 'Kommentar', 'align': 'left', 'classes': 'w-1/3', 'headerClasses': 'hidden'},
                                        ]
                                        # Clean up records for JSON
                                        records = psp_group.to_dict('records')
                                        for record in records:
                                            # Remove temporary columns if they exist in the record dict
                                            for key in ['DateObj', 'Week', 'Year']:
                                                if key in record: del record[key]
                                        
                                        # hide-header is key here
                                        ui.table(columns=cols, rows=records).props('dense flat hide-bottom hide-header wrap-cells').classes('w-full')
        except Exception as e:
            with self.analysis_container:
                ui.label(f'Fehler bei der Auswertung: {e}').classes('text-red-500')

    def render_settings_list(self, title, section, placeholder, with_description=False):
        with ui.card().classes('w-full p-3 mb-2 border-[1px] no-shadow'):
            ui.label(title).classes('font-bold text-primary')
            
            # Container for list items
            item_container = ui.row().classes('w-full flex-wrap gap-2')
            
            def refresh_items():
                item_container.clear()
                if with_description:
                    # Get items as (key, value)
                    items = self.config.get_items(section)
                else:
                    # Get just keys
                    items = self.config.get_combobox_value(section)
                
                if not items:
                    with item_container:
                        ui.label('Keine Einträge').classes('text-gray-400 italic text-sm')
                        
                for item in items:
                    key = item[0] if with_description else item
                    val = item[1] if with_description and item[1] else None
                    
                    display_text = f"{key} ({val})" if val else key

                    with item_container:
                        # Chip with delete functionality
                        with ui.element('div').classes('bg-gray-100 dark:bg-gray-700 rounded-full px-3 py-1 text-sm flex items-center gap-2 border border-gray-300 dark:border-gray-600'):
                            ui.label(display_text)
                            ui.icon('close').classes('cursor-pointer text-gray-500 hover:text-red-500 text-xs').on('click', lambda _, i=key: remove_item(i))

            def remove_item(item_key):
                self.config.remove_item(section, item_key)
                ui.notify(f'"{item_key}" entfernt.', type='info')
                self.update_booking_options()
                refresh_items()

            def add_item():
                key_val = input_field.value.strip()
                desc_val = desc_input.value.strip() if with_description and desc_input else None
                
                if key_val:
                    self.config.add_item(section, key_val, desc_val)
                    input_field.value = ""
                    if desc_input: desc_input.value = ""
                    refresh_items()
                    self.update_booking_options()
                    ui.notify(f'"{key_val}" hinzugefügt.', type='positive')

            # Input row
            with ui.row().classes('w-full items-center gap-2 mt-2'):
                input_field = ui.input(placeholder=placeholder).props('dense').classes('flex-grow')
                desc_input = None
                if with_description:
                    desc_input = ui.input(placeholder="Beschreibung (optional)").props('dense').classes('flex-grow')
                
                ui.button(icon='add', on_click=add_item).props('dense flat round color=primary')

            # Initial population
            refresh_items()

    def _get_psp_options(self):
        """Helper to build PSP options dict with descriptions."""
        items = self.config.get_items("psp")
        options = {}
        for key, val in items:
            label = f"{key} ({val})" if val else key
            options[key] = label
        return options

    def update_booking_options(self):
        """Refreshes the dropdown options in the booking tab."""
        if self.psp_input:
            self.psp_input.options = self._get_psp_options()
            self.psp_input.update()
        
        if self.customer_input:
            self.customer_input.options = self.config.get_combobox_value("customer")
            self.customer_input.update()
            
        # For comment input using datalist, we need to rebuild the datalist
        # This is strictly not easily updatable without rebuilding the datalist element or clearing it
        # Since datalist is static in DOM, we might need a reference or just reload. 
        # For now, simplistic approach: notify user or just reload app? 
        # Actually, let's try to clear and re-add if we can find it.
        # But for 'ui.element("datalist")', we didn't save a ref. 
        # Let's save a ref to comment_datalist in setup_ui first.
        if hasattr(self, 'comment_datalist') and self.comment_datalist:
            self.comment_datalist.clear()
            with self.comment_datalist:
                 for opt in self.config.get_combobox_value("comments"):
                            ui.element('option').props(f'value="{opt}"')

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
    ui.run(native=True, window_size=(500, 600), title="Smart ESS - Noah Wollenhaupt", reload=False)

if __name__ == "__main__":
    run_app()
