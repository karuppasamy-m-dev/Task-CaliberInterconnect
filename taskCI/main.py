from kivymd.app import MDApp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.uix.datatables import MDDataTable
from kivy.metrics import dp
from kivy.uix.textinput import TextInput
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.filemanager import MDFileManager
from kivy.uix.image import Image
import requests
import json


FLASK_SERVER = "http://127.0.0.1:5000"


class FileUploadScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = MDBoxLayout(orientation='vertical', spacing=20, padding=20)

        self.label = MDLabel(
            text="Select a CSV/Excel file to upload",
            halign="center",
            theme_text_color="Secondary"
        )

        self.file_manager = MDFileManager(exit_manager=self.exit_manager, select_path=self.select_path)
        self.selected_file_label = MDLabel(
            text="No file selected",
            halign="center",
            theme_text_color="Hint"
        )

        self.upload_btn = MDRaisedButton(
            text="Choose File",
            pos_hint={"center_x": 0.5},
            on_release=self.open_file_manager
        )

        self.submit_btn = MDRaisedButton(
            text="Upload",
            pos_hint={"center_x": 0.5},
            md_bg_color=(0, 0.6, 1, 1),
            on_release=self.upload_file
        )

        self.layout.add_widget(self.label)
        self.layout.add_widget(self.selected_file_label)
        self.layout.add_widget(self.upload_btn)
        self.layout.add_widget(self.submit_btn)
        self.add_widget(self.layout)

    def open_file_manager(self, instance):
        self.file_manager.show("/")

    def select_path(self, path):
        self.selected_file_label.text = f"Selected: {path}"
        self.file_path = path
        self.exit_manager()

    def exit_manager(self, *args):
        self.file_manager.close()

    def upload_file(self, instance):
        try:
            if not hasattr(self, 'file_path'):
                self.selected_file_label.text = "Please select a file first!"
                self.selected_file_label.theme_text_color = "Error"
                return

            with open(self.file_path, 'rb') as file:
                files = {'file': file}
                response = requests.post(f"{FLASK_SERVER}/upload", files=files)
                result = response.json()

            if response.status_code == 200:
                self.manager.current = 'data_screen'
            else:
                self.selected_file_label.text = result.get("error", "Upload failed!")
                self.selected_file_label.theme_text_color = "Error"

        except requests.exceptions.RequestException as e:
            self.selected_file_label.text = f"Server error: {str(e)}"
            self.selected_file_label.theme_text_color = "Error"

        except Exception as e:
            self.selected_file_label.text = f"An unexpected error occurred: {str(e)}"
            self.selected_file_label.theme_text_color = "Error"


# Data Display Screen
class DataScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')
        self.search_input = TextInput(hint_text="Search", size_hint=(1, 0.1))
        self.search_input.bind(text=self.filter_data)
        self.table = None
        self.data = []  # Store full dataset

        self.layout.add_widget(self.search_input)
        self.add_widget(self.layout)

    def on_enter(self):
        self.display_data()

    def display_data(self):
        response = requests.get(f"{FLASK_SERVER}/data")
        if response.status_code == 200:
            self.data = json.loads(response.json().get("data", "[]"))
            self.layout.clear_widgets()

            back_btn = Button(text="Back", size_hint=(1, 0.1))
            back_btn.bind(on_press=self.clear_data_on_back)
            self.layout.add_widget(back_btn)
            self.layout.add_widget(self.search_input)

            if self.data:
                self.create_table(self.data)
            else:
                self.layout.add_widget(Button(text="No data available"))

    def clear_data_on_back(self, instance):
        self.data = []  # Clears the data
        self.layout.clear_widgets()  # Optional: Clears the layout widgets
        self.manager.current = 'upload_screen'  # Switches to the upload screen

    def create_table(self, data):
        if self.table:
            self.layout.remove_widget(self.table)

        headers = list(data[0].keys()) if data else []
        column_data = [(header, dp(30)) for header in headers]

        row_data = []
        for item in data:
            row = []
            for col in headers:
                value = str(item[col])
                # If the value is an image URL, add a clickable button
                if value.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    row.append(f'[color=#0000FF]{value}[/color]')  # Add a clickable color to the image URL
                else:
                    row.append(value)
            row_data.append(row)

        self.table = MDDataTable(
            size_hint=(1, 0.9),
            use_pagination=True,
            column_data=column_data,
            row_data=row_data
        )

        self.layout.add_widget(self.table)

    def filter_data(self, instance, text):
        filtered_data = [row for row in self.data if any(text.lower() in str(value).lower() for value in row.values())]
        self.create_table(filtered_data)

# Main App
class MyApp(MDApp):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(FileUploadScreen(name='upload_screen'))
        sm.add_widget(DataScreen(name='data_screen'))
        return sm


if __name__ == '__main__':
    MyApp().run()
