import sys
import os
import time
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog,
    QLineEdit, QTextEdit, QMessageBox
)
from PySide6.QtGui import QPixmap
from image_encryptor_lib import (
    hide_file_in_png, extract_files_from_png, select_any_file, select_png_file, select_encrypted_png_file, select_output_dir, generate_encryption_key
)

import locale
# get local language
import locale
langCode=locale.getlocale()[0].split("_")[0]
import json
languages=dict(json.load(open("./language.json","r",encoding='utf-8')))
if (not (langCode in languages.keys())):
    langCode="en"
lang=languages[langCode]

class PNGSteganographyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(lang[0])
        self.setGeometry(100, 100, 800, 600)
        main_layout = QVBoxLayout()
        self.image_label = QLabel(lang[1])
        self.image_label.setFixedSize(350, 250)
        self.image_label.setStyleSheet("border: 1px solid black;")
        main_layout.addWidget(self.image_label)
        self.key_input = QLineEdit(self)
        self.key_input.setPlaceholderText(lang[2])
        main_layout.addWidget(self.key_input)
        self.message_input = QTextEdit(self)
        self.message_input.setPlaceholderText(lang[3])
        self.message_input.textChanged.connect(self.clear_file_path)  # 输入信息时清空文件路径
        main_layout.addWidget(self.message_input)
        file_buttons_layout = QHBoxLayout()

        self.select_file_button = QPushButton(lang[4])
        self.select_file_button.clicked.connect(self.select_file)
        file_buttons_layout.addWidget(self.select_file_button)

        self.select_png_button = QPushButton(lang[5])
        self.select_png_button.clicked.connect(self.select_png)
        file_buttons_layout.addWidget(self.select_png_button)

        self.select_encrypted_png_button = QPushButton(lang[6])
        self.select_encrypted_png_button.clicked.connect(self.select_encrypted_png)
        file_buttons_layout.addWidget(self.select_encrypted_png_button)

        self.select_output_button = QPushButton(lang[7])
        self.select_output_button.clicked.connect(self.select_output)
        file_buttons_layout.addWidget(self.select_output_button)

        main_layout.addLayout(file_buttons_layout)
        operations_layout = QHBoxLayout()

        self.encrypt_button = QPushButton(lang[8])
        self.encrypt_button.clicked.connect(self.encrypt_png)
        operations_layout.addWidget(self.encrypt_button)

        self.decrypt_button = QPushButton(lang[9])
        self.decrypt_button.clicked.connect(self.decrypt_png)
        operations_layout.addWidget(self.decrypt_button)

        main_layout.addLayout(operations_layout)

        self.setLayout(main_layout)

        self.selected_file = None
        self.selected_png = None
        self.selected_encrypted_png = None
        self.output_directory = None

    def select_file(self):
        self.selected_file = select_any_file(lang[10])
        self.message_input.clear() 
        if self.selected_file:
            QMessageBox.information(self, lang[12], f"{lang[15]}: {self.selected_file}")
        else:
            QMessageBox.information(self, lang[13], lang[14])

    def select_png(self):
        self.selected_png = select_png_file(lang[5])
        self.display_image(self.selected_png)
        if self.selected_png:
            QMessageBox.information(self, lang[12], f"{lang[15]}: {self.selected_png}")
            self.selected_encrypted_png = None  
        else:
            if  self.display_image(self.selected_png) == 1:
                QMessageBox.information(self,lang[13], lang[16])
            QMessageBox.information(self, lang[13], lang[14])

    def select_encrypted_png(self):
        self.selected_encrypted_png = select_encrypted_png_file(lang[6])  
        self.display_image(self.selected_encrypted_png)
        if self.selected_encrypted_png:
            QMessageBox.information(self, lang[12], f"{lang[15]}: {self.selected_encrypted_png}")
            self.selected_png = None  
        else:
            QMessageBox.information(self, lang[13], lang[14])

    def select_output(self):
        self.output_directory = select_output_dir(lang[11])
        if self.output_directory:
            QMessageBox.information(self, lang[12], f"{lang[15]}: {self.output_directory}")
        else:
            QMessageBox.information(self, lang[13], lang[14])

    def encrypt_png(self):
        user_key = self.key_input.text().strip()
        if not user_key:
            user_key = 'furina'

        encryption_key = generate_encryption_key(user_key)

        if not self.selected_png:
            QMessageBox.warning(self, lang[13], lang[17])
            return
        if not self.output_directory:
            QMessageBox.warning(self, lang[13], lang[7])
            return
        if self.selected_file:
            data = self.selected_file
            judgment = 0
        else:
            data = self.message_input.toPlainText().strip()
            judgment = 1
            if not data:
                QMessageBox.warning(self, lang[13], lang[3])
                return

        output_png = os.path.join(self.output_directory, f"hidden_{int(time.time())}.png")
        hide_file_in_png(self.selected_png, data, output_png, encryption_key, judgment)

        self.display_image(output_png)
        QMessageBox.information(self, lang[12], f"{lang[18]}: {output_png}")

    def decrypt_png(self):
        user_key = self.key_input.text().strip()
        if not user_key:
            user_key = 'furina'

        encryption_key = generate_encryption_key(user_key)

        if not self.selected_encrypted_png:
            QMessageBox.warning(self, lang[13], lang[6])
            return
        if self.output_directory:
            QMessageBox.warning(self, lang[13],lang[7])
            return
        extract_files_from_png(self.selected_encrypted_png, self.output_directory, encryption_key)
        QMessageBox.information(self, lang[12], f"{lang[18]}: {self.output_directory}")

    def clear_file_path(self):
        if self.message_input.toPlainText():
            self.selected_file = None

    def display_image(self, image_path):
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            self.image_label.setPixmap(pixmap.scaled(self.image_label.width(), self.image_label.height()))
        else:
            self.image_label.setText(lang[1])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PNGSteganographyApp()
    window.show()
    sys.exit(app.exec())
