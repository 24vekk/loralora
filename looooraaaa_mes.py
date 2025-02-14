from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
import serial
import serial.tools.list_ports
import threading
import sys

class LoRaMessenger(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = 10
        self.padding = [20, 20, 20, 20]

        # Выбор COM-порта
        self.com_port_label = Label(text="Select COM Port:", size_hint_y=0.1)
        self.add_widget(self.com_port_label)

        self.com_port_spinner = Spinner(
            text="Select Port",
            values=self.get_available_com_ports(),
            size_hint_y=0.1
        )
        self.com_port_spinner.bind(text=self.on_com_port_selected)
        self.add_widget(self.com_port_spinner)

        # Поле для имени пользователя
        self.username_field = TextInput(
            hint_text="Enter your name",
            multiline=False,
            size_hint_y=0.1
        )
        self.add_widget(self.username_field)

        # Область чата
        self.chat_area = Label(
            text="Chat Area",
            size_hint_y=0.6,
            halign="left",
            valign="top",
            markup=True
        )
        self.chat_area.bind(size=self.chat_area.setter("text_size"))
        self.add_widget(self.chat_area)

        # Поле ввода сообщения
        self.input_field = TextInput(
            hint_text="Enter message",
            multiline=False,
            size_hint_y=0.15
        )
        self.add_widget(self.input_field)

        # Кнопка отправки
        self.send_button = Button(
            text="Send",
            size_hint_y=0.15
        )
        self.send_button.bind(on_press=self.on_send_button_pressed)
        self.add_widget(self.send_button)

        # Флаг для управления потоками
        self.running = True

        # Переменная для COM-порта
        self.usb_serial = None

    def get_available_com_ports(self):
        """Получает список доступных COM-портов."""
        return [port.device for port in serial.tools.list_ports.comports()]

    def on_com_port_selected(self, instance, value):
        """Обработчик выбора COM-порта."""
        if value != "Select Port":
            try:
                self.usb_serial = serial.Serial(value, 9600, timeout=1)
                print(f"Connected to {value}")
                Clock.schedule_interval(self.receive_messages, 1)
            except (serial.SerialException, OSError) as e:
                print(f"Failed to connect to {value}: {e}")
                self.usb_serial = None

    def on_send_button_pressed(self, instance):
        """Обработчик нажатия кнопки Send."""
        if self.usb_serial is not None and self.usb_serial.is_open:
            threading.Thread(target=self.send_message).start()
        else:
            print("No COM port selected or connected!")

    def send_message(self):
        """Отправляет сообщение через COM-порт в фоновом потоке."""
        if not self.running:
            return

        username = self.username_field.text.strip()
        message = self.input_field.text.strip()

        if username and message and self.usb_serial:
            full_message = f"{username}: {message}"
            self.update_chat(f"[color=33cc33]{full_message}[/color]\n")

            try:
                self.usb_serial.write((full_message + '\n').encode('utf-8'))
            except Exception as e:
                print(f"Error sending message: {e}")

            self.input_field.text = ""

    def receive_messages(self, dt):
        """Прием сообщений из COM-порта."""
        if not self.running or self.usb_serial is None or not self.usb_serial.is_open:
            return

        if self.usb_serial.in_waiting > 0:
            try:
                message = self.usb_serial.readline().decode('utf-8').strip()
                if message:
                    self.update_chat(f"[color=3333ff]{message}[/color]\n")
            except Exception as e:
                print(f"Error receiving message: {e}")

    def update_chat(self, message):
        """Обновляет область чата."""
        self.chat_area.text += message
        self.chat_area.texture_update()

    def stop_threads(self):
        """Останавливает все фоновые потоки."""
        self.running = False
        if self.usb_serial and self.usb_serial.is_open:
            self.usb_serial.close()


class LoRaMessengerApp(App):
    def build(self):
        self.messenger = LoRaMessenger()
        return self.messenger

    def on_stop(self):
        """Метод вызывается при закрытии приложения."""
        print("Stopping application...")
        self.messenger.stop_threads()
        print("Application stopped.")


if __name__ == "__main__":
    try:
        LoRaMessengerApp().run()
    except KeyboardInterrupt:
        print("Application interrupted by user.")
        sys.exit(0)