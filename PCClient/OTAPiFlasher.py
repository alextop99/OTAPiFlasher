import paho.mqtt.client as paho
from paho import mqtt
from config import settings
from MQTTLib import *
from ClientLib import *
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QMessageBox, QDialogButtonBox, QFileDialog, QTextEdit
from PyQt5.QtCore import Qt
import time

server = ""
port = 0
username = ""
password = ""
topic = ""
qos = 0

filename = ""
client = None
outputText = ""
changedOutput = False

class AlertMessageBox(QMessageBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = self.layout()

        qt_msgboxex_icon_label = self.findChild(QLabel, "qt_msgboxex_icon_label")
        qt_msgboxex_icon_label.deleteLater()

        qt_msgbox_label = self.findChild(QLabel, "qt_msgbox_label")
        qt_msgbox_label.setAlignment(Qt.AlignCenter)
        grid_layout.removeWidget(qt_msgbox_label)

        qt_msgbox_buttonbox = self.findChild(QDialogButtonBox, "qt_msgbox_buttonbox")
        grid_layout.removeWidget(qt_msgbox_buttonbox)

        grid_layout.addWidget(qt_msgbox_label, 0, 0, alignment=Qt.AlignCenter)
        grid_layout.addWidget(qt_msgbox_buttonbox, 1, 0, alignment=Qt.AlignCenter)
        
def on_pingButton_clicked(client):
    global topic, qos
    pingResult = send_ping(client, topic, qos)
    alert = AlertMessageBox()
    alert.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    if pingResult:
        alert.setText('Ping Successful!')
    else:
        alert.setText('Ping Failed!\nPlease check both client and server settings as well as the on status of the server!')
    alert.exec()
    
def on_sendFileButton_clicked(client, outputTextBox):
    global topic, qos, filename, outputText, changedOutput
    
    if filename == "":
        alert = AlertMessageBox()
        alert.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        alert.setText('No file selected!')
        alert.exec()
        return
    
    pingResult = send_ping(client, topic, qos)
    if not pingResult:
        alert = AlertMessageBox()
        alert.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        alert.setText('Ping Failed!\nPlease check both client and server settings as well as the on status of the server!')
        alert.exec()
        return
    
    send_header(client, filename, topic, qos)
    filehash = send_file(client, filename, topic, qos)
    send_end(client, filename, filehash, topic, qos)
    res = waitForResult()
    if not res:
        alert = AlertMessageBox()
        alert.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        alert.setText('Upload Failed!\nPlease check the selected file!')
        alert.exec()
        return
    
    alert = AlertMessageBox()
    alert.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    alert.setText('File upload successful!\nPlease check the log!')
    alert.exec()
    
    while not changedOutput: 
        time.sleep(10)
    
    outputTextBox.setText(outputText)
    
def on_chooseFileButton_clicked(dlg, filenameTextBox):
    global filename
    filenames = []
    if dlg.exec_():
        filenames = dlg.selectedFiles()
        filename =  filenames[0]
        filenameTextBox.setText(filename)
        
def changeOutputText(text):
    global outputText, changedOutput
    outputText = text
    changedOutput = True

def startClient():
    global server, port, username, password, topic, qos, client
    client = paho.Client(client_id="", userdata={'changeOutputText': changeOutputText}, protocol=paho.MQTTv5)

    client.puback_flag=False
    client.mid_value=None
    client.on_message = on_message
    client.on_publish = on_publish

    client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
    client.username_pw_set(username, password)
    client.connect(server, port)

    client.loop_start()
    
    client.subscribe(topic, qos)

def GUI():
    global topic, qos, filename, client, server, username, port
    app = QApplication([])
    app.setApplicationName("OTA Pi Flasher")
    window = QWidget()
    
    window.setWindowTitle("OTA Pi Flasher")
    
    dlg = QFileDialog()
    dlg.setFileMode(QFileDialog.AnyFile)
    
    filenameTextBox  = QTextEdit()
    filenameTextBox.setMaximumSize(400, 30)
    filenameTextBox.setReadOnly(True)
    filenameTextBox.setText(filename)
    
    chooseFileButton = QPushButton("Choose")
    chooseFileButton.clicked.connect(lambda: on_chooseFileButton_clicked(dlg, filenameTextBox))
    
    chooseFileDialogLayout = QHBoxLayout()
    chooseFileDialogLayout.addWidget(filenameTextBox)
    chooseFileDialogLayout.addWidget(chooseFileButton)
    
    bottomButtonlayout = QHBoxLayout()
    pingButton = QPushButton('Ping')
    pingButton.clicked.connect(lambda: on_pingButton_clicked(client))
    
    outputTextBox  = QTextEdit()
    outputTextBox.setReadOnly(True)
    outputTextBox.setText(outputText)
    outputTextBox.setMinimumSize(600, 400)
    sendFileButton = QPushButton('Send File')
    sendFileButton.clicked.connect(lambda: on_sendFileButton_clicked(client, outputTextBox))
    bottomButtonlayout.addWidget(pingButton)
    bottomButtonlayout.addWidget(sendFileButton)
    
    currentConfigLabel = QLabel()
    currentConfigLabel.setText("Current configuration:")
    currentConfigLabel.setStyleSheet("font-weight: bold")
    
    serverLabel = QLabel()
    serverLabel.setText("SERVER")
    serverTextBox  = QTextEdit()
    serverTextBox.setMaximumSize(400, 30)
    serverTextBox.setReadOnly(True)
    serverTextBox.setText(server)
    
    portLabel = QLabel()
    portLabel.setText("PORT")
    portTextBox  = QTextEdit()
    portTextBox.setMaximumSize(600, 30)
    portTextBox.setReadOnly(True)
    portTextBox.setText(str(port))
    
    usernameLabel = QLabel()
    usernameLabel.setText("USERNAME")
    usernameTextBox  = QTextEdit()
    usernameTextBox.setMaximumSize(600, 30)
    usernameTextBox.setReadOnly(True)
    usernameTextBox.setText(username)
    
    topicLabel = QLabel()
    topicLabel.setText("TOPIC")
    topicTextBox  = QTextEdit()
    topicTextBox.setMaximumSize(600, 30)
    topicTextBox.setReadOnly(True)
    topicTextBox.setText(topic)
    
    fileDialogLabel = QLabel()
    fileDialogLabel.setText("File Upload Dialog:")
    fileDialogLabel.setStyleSheet("font-weight: bold")
    logLabel = QLabel()
    logLabel.setText("Log output:")
    logLabel.setStyleSheet("font-weight: bold")
    overallLayout = QVBoxLayout()
    overallLayout.addWidget(currentConfigLabel)
    overallLayout.addWidget(serverLabel)
    overallLayout.addWidget(serverTextBox)
    overallLayout.addWidget(portLabel)
    overallLayout.addWidget(portTextBox)
    overallLayout.addWidget(usernameLabel)
    overallLayout.addWidget(usernameTextBox)
    overallLayout.addWidget(topicLabel)
    overallLayout.addWidget(topicTextBox)
    overallLayout.addWidget(fileDialogLabel)
    overallLayout.addLayout(chooseFileDialogLayout)
    overallLayout.addLayout(bottomButtonlayout)
    overallLayout.addWidget(logLabel)
    overallLayout.addWidget(outputTextBox)
    
    window.setLayout(overallLayout)
    window.show()
    app.exec_()

# Main function
def main():
    global server, port, username, password, topic, qos, client
    try:
        ## Server config
        server = settings.server
        port = settings.port

        ## User config
        username = settings.username
        password = settings.password

        ## Device config
        topic = settings.topic
        qos = settings.qos
    except:
        print("Settings file missing, please complete the file settings.json from the demo created!")
        settingsMissing()
        return
    
    startClient()
    
    GUI()
    
    client.disconnect()
    client.loop_stop()
    
    
if __name__ == "__main__":
    main()