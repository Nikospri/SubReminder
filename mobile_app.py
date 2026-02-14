from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import ThreeLineIconListItem, IconLeftWidget
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.menu import MDDropdownMenu
from kivy.lang import Builder
import json
import os
from datetime import datetime, timedelta
import calendar

try:
    from plyer import notification
except ImportError:
    notification = None

# --- KV Layout (Η εμφάνιση της εφαρμογής) ---
KV = '''
<AddDialogContent>:
    orientation: "vertical"
    spacing: "12dp"
    size_hint_y: None
    height: "280dp"

    MDTextField:
        id: name
        hint_text: "Όνομα Υπηρεσίας"
    
    MDTextField:
        id: price
        hint_text: "Ποσό (€)"
        input_filter: "float"

    MDTextField:
        id: date
        hint_text: "Ημερομηνία (DD/MM/YYYY)"

    MDTextField:
        id: period
        hint_text: "Τύπος (Μηνιαία, Ετήσια...)"
        on_focus: if self.focus: app.menu_period.open()

MDBoxLayout:
    orientation: "vertical"

    MDTopAppBar:
        title: "SubReminder"
        right_action_items: [["theme-light-dark", lambda x: app.toggle_theme()]]

    MDScrollView:
        MDList:
            id: container

    MDFloatingActionButton:
        icon: "plus"
        pos_hint: {"right": .95, "y": .05}
        on_release: app.show_add_dialog()
'''

DATA_FILE = "subscriptions.json"

class AddDialogContent(MDBoxLayout):
    pass

class SubTrackerApp(MDApp):
    dialog = None
    editing_sub = None

    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        return Builder.load_string(KV)

    def on_start(self):
        # Καθορισμός σωστής διαδρομής για Android/Windows
        self.data_path = os.path.join(self.user_data_dir, DATA_FILE)
        
        self.subscriptions = []
        self.load_data()
        self.refresh_list()
        self.check_notifications()
        
        # Ρύθμιση μενού επιλογής περιόδου
        self.menu_items = [
            {"viewclass": "OneLineListItem", "text": "Μηνιαία", "on_release": lambda x="Μηνιαία": self.set_period(x)},
            {"viewclass": "OneLineListItem", "text": "Ετήσια", "on_release": lambda x="Ετήσια": self.set_period(x)},
            {"viewclass": "OneLineListItem", "text": "Εβδομαδιαία", "on_release": lambda x="Εβδομαδιαία": self.set_period(x)},
            {"viewclass": "OneLineListItem", "text": "Εφάπαξ", "on_release": lambda x="Εφάπαξ": self.set_period(x)},
        ]

    def set_period(self, text_item):
        self.dialog_content.ids.period.text = text_item
        self.menu_period.dismiss()

    def toggle_theme(self):
        self.theme_cls.theme_style = "Dark" if self.theme_cls.theme_style == "Light" else "Light"

    def check_notifications(self):
        """Ελέγχει για συνδρομές που λήγουν και στέλνει ειδοποίηση."""
        if not notification: return
        
        due_soon = []
        today = datetime.now().date()
        for sub in self.subscriptions:
            try:
                try:
                    d = datetime.strptime(sub['date'], "%d/%m/%Y").date()
                except ValueError:
                    d = datetime.strptime(sub['date'], "%Y-%m-%d").date()
                
                diff = (d - today).days
                if 0 <= diff <= 3:
                    due_soon.append(f"{sub['name']}")
            except:
                pass
        
        if due_soon:
            notification.notify(
                title="SubReminder",
                message=f"Λήγουν σύντομα: {', '.join(due_soon)}",
                app_name="SubReminder",
                timeout=10
            )

    # --- ΔΙΑΧΕΙΡΙΣΗ ΔΕΔΟΜΕΝΩΝ ---
    def load_data(self):
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    self.subscriptions = json.load(f)
            except:
                self.subscriptions = []

    def save_data(self):
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump(self.subscriptions, f, ensure_ascii=False, indent=4)

    def refresh_list(self):
        self.root.ids.container.clear_widgets()
        
        # Ταξινόμηση
        def sort_key(sub):
            try:
                return datetime.strptime(sub['date'], "%d/%m/%Y")
            except ValueError:
                try:
                    return datetime.strptime(sub['date'], "%Y-%m-%d")
                except ValueError:
                    return datetime.max
        self.subscriptions.sort(key=sort_key)

        for sub in self.subscriptions:
            self.create_list_item(sub)

    def create_list_item(self, sub):
        # Υπολογισμός ημερών
        status_text = ""
        icon_color = self.theme_cls.primary_color
        
        try:
            try:
                due_date = datetime.strptime(sub['date'], "%d/%m/%Y").date()
            except ValueError:
                due_date = datetime.strptime(sub['date'], "%Y-%m-%d").date()
            
            today = datetime.now().date()
            diff = (due_date - today).days
            
            if diff < 0:
                status_text = f"[color=FF0000]Έληξε ({abs(diff)} μέρες)[/color]"
                icon_color = (1, 0, 0, 1)
            elif diff == 0:
                status_text = "[color=FF0000]Πληρωμή Σήμερα![/color]"
                icon_color = (1, 0, 0, 1)
            elif diff <= 3:
                status_text = f"[color=FF9800]Λήγει σε {diff} μέρες[/color]"
                icon_color = (1, 0.6, 0, 1)
            else:
                status_text = f"[color=4CAF50]Ενεργή ({diff} μέρες)[/color]"
                icon_color = (0, 0.8, 0, 1)
        except:
            status_text = "Άγνωστη ημερομηνία"

        period = sub.get('period', 'Μηνιαία')
        
        item = ThreeLineIconListItem(
            text=sub['name'],
            secondary_text=f"{sub['price']}€ - {period}",
            tertiary_text=status_text,
            on_release=lambda x: self.show_options_dialog(sub)
        )
        icon = IconLeftWidget(icon="credit-card", theme_text_color="Custom", text_color=icon_color)
        item.add_widget(icon)
        self.root.ids.container.add_widget(item)

    # --- DIALOGS ---
    def show_add_dialog(self):
        self.editing_sub = None
        self.dialog_content = AddDialogContent()
        # Προεπιλογή ημερομηνίας
        self.dialog_content.ids.date.text = datetime.now().strftime("%d/%m/%Y")
        
        # Ρύθμιση μενού για το συγκεκριμένο πεδίο
        self.menu_period = MDDropdownMenu(
            caller=self.dialog_content.ids.period,
            items=self.menu_items,
            width_mult=4,
        )

        self.dialog = MDDialog(
            title="Νέα Συνδρομή",
            type="custom",
            content_cls=self.dialog_content,
            buttons=[
                MDFlatButton(text="ΑΚΥΡΟ", on_release=self.close_dialog),
                MDFlatButton(text="ΑΠΟΘΗΚΕΥΣΗ", on_release=self.save_subscription),
            ],
        )
        self.dialog.open()

    def close_dialog(self, *args):
        if self.dialog:
            self.dialog.dismiss()

    def save_subscription(self, *args):
        name = self.dialog_content.ids.name.text
        price = self.dialog_content.ids.price.text
        date_str = self.dialog_content.ids.date.text
        period = self.dialog_content.ids.period.text or "Μηνιαία"

        if not name or not price:
            return # Απλή επικύρωση

        # Υπολογισμός επόμενης ημερομηνίας (μόνο αν είναι νέα εγγραφή)
        final_date = date_str
        if not self.editing_sub and period != 'Εφάπαξ':
            try:
                try:
                    start_date = datetime.strptime(date_str, "%d/%m/%Y").date()
                    fmt = "%d/%m/%Y"
                except ValueError:
                    start_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    fmt = "%Y-%m-%d"
                
                next_date = start_date
                if period == 'Μηνιαία':
                    m = start_date.month + 1
                    y = start_date.year
                    if m > 12: m, y = 1, y + 1
                    d = min(start_date.day, calendar.monthrange(y, m)[1])
                    next_date = start_date.replace(year=y, month=m, day=d)
                elif period == 'Ετήσια':
                    next_date = start_date.replace(year=start_date.year + 1)
                elif period == 'Εβδομαδιαία':
                    next_date = start_date + timedelta(days=7)
                
                final_date = next_date.strftime(fmt)
            except:
                pass

        if self.editing_sub:
            self.editing_sub['name'] = name
            self.editing_sub['price'] = price
            self.editing_sub['date'] = date_str # Στην επεξεργασία κρατάμε αυτό που έγραψε
            self.editing_sub['period'] = period
            self.editing_sub = None
        else:
            self.subscriptions.append({"name": name, "price": price, "date": final_date, "period": period})
        
        self.save_data()
        self.refresh_list()
        self.close_dialog()

    def show_options_dialog(self, sub):
        self.selected_sub = sub
        self.ops_dialog = MDDialog(
            title=sub['name'],
            text=f"Ποσό: {sub['price']}€\nΛήξη: {sub['date']}",
            buttons=[
                MDFlatButton(text="ΕΠΕΞΕΡΓΑΣΙΑ", theme_text_color="Custom", text_color=(0, 0, 1, 1), on_release=lambda x: self.show_edit_dialog(sub)),
                MDFlatButton(text="ΔΙΑΓΡΑΦΗ", theme_text_color="Error", on_release=lambda x: self.delete_sub(sub)),
                MDFlatButton(text="ΑΝΑΝΕΩΣΗ", theme_text_color="Custom", text_color=(0, 0.7, 0, 1), on_release=lambda x: self.renew_sub(sub)),
                MDFlatButton(text="ΚΛΕΙΣΙΜΟ", on_release=lambda x: self.ops_dialog.dismiss()),
            ],
        )
        self.ops_dialog.open()

    def show_edit_dialog(self, sub):
        self.ops_dialog.dismiss()
        self.editing_sub = sub
        self.dialog_content = AddDialogContent()
        
        self.dialog_content.ids.name.text = sub['name']
        self.dialog_content.ids.price.text = sub['price']
        self.dialog_content.ids.date.text = sub['date']
        self.dialog_content.ids.period.text = sub.get('period', 'Μηνιαία')

        self.menu_period = MDDropdownMenu(
            caller=self.dialog_content.ids.period,
            items=self.menu_items,
            width_mult=4,
        )

        self.dialog = MDDialog(
            title="Επεξεργασία",
            type="custom",
            content_cls=self.dialog_content,
            buttons=[
                MDFlatButton(text="ΑΚΥΡΟ", on_release=self.close_dialog),
                MDFlatButton(text="ΑΠΟΘΗΚΕΥΣΗ", on_release=self.save_subscription),
            ],
        )
        self.dialog.open()

    def delete_sub(self, sub):
        self.subscriptions.remove(sub)
        self.save_data()
        self.refresh_list()
        self.ops_dialog.dismiss()

    def renew_sub(self, sub):
        # Λογική ανανέωσης (ίδια με assd.py)
        try:
            try:
                current_date = datetime.strptime(sub['date'], "%d/%m/%Y").date()
                fmt = "%d/%m/%Y"
            except ValueError:
                current_date = datetime.strptime(sub['date'], "%Y-%m-%d").date()
                fmt = "%Y-%m-%d"
            
            period = sub.get('period', 'Μηνιαία')
            
            if period == 'Ετήσια':
                new_date = current_date.replace(year=current_date.year + 1)
            elif period == 'Εβδομαδιαία':
                new_date = current_date + timedelta(days=7)
            elif period == 'Εφάπαξ':
                return
            else: # Μηνιαία
                m = current_date.month + 1
                y = current_date.year
                if m > 12: m, y = 1, y + 1
                d = min(current_date.day, calendar.monthrange(y, m)[1])
                new_date = current_date.replace(year=y, month=m, day=d)

            sub['date'] = new_date.strftime(fmt)
            self.save_data()
            self.refresh_list()
            self.ops_dialog.dismiss()
        except:
            pass

if __name__ == "__main__":
    SubTrackerApp().run()
