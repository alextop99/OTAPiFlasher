settingsFile = '''{
    "server" : "",
    "port" : ,
    "username" : "",
    "password" : "",
    "topic" : "",
    "qos" : 1
}'''

def settingsMissing():
    f = open("settings.json", "w")
    f.write(settingsFile)
    f.close()