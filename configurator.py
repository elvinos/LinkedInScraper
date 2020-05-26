import os
from configparser import ConfigParser
from sys import platform

import pyttsx3

config = ConfigParser()

config.add_section('system')
config.add_section('linkedin')
config.add_section('profiles_data')

print("Welcome to the configuration process.")

try:
    print("Performing some system checks...")
    engine = pyttsx3.init()
    engine.say(' ')
    engine.runAndWait()
    config.set('system', 'speak', 'Y')
except OSError:
    config.set('system', 'speak', 'N')

if platform.lower() == "linux":
    driver = 'Linux/chromedriver'
    config.set('system',
               'os',
               'linux')
elif platform.lower() == "darwin":
    driver = 'MacOS/chromedriver'
    config.set('system', 'os', 'macos')
elif platform.lower() == "windows":
    driver = 'Windows/chromedriver.exe'
    config.set('system', 'os', 'windows')
else:
    this_os = ""
    while this_os not in ["Linux", "MacOS", "Windows"]:
        print("Insert 'Linux' or 'MacOS' or 'Windows' based on this OS.")
        print("> ", end="")
        this_os = input()
    if this_os == "Linux":
        driver = 'Linux/chromedriver'
        config.set('system', 'os', 'linux')
    elif this_os == "MacOS":
        driver = 'MacOS/chromedriver'
        config.set('system', 'os', 'macos')
    else:
        driver = 'Windows/chromedriver.exe'
        config.set('system', 'os', 'windows')

config.set('system', 'driver', os.path.join(os.path.abspath(os.path.dirname(__file__)), driver))

linkedin_username = ""
while linkedin_username == "":
    print("Insert linkedin username.")
    print("> ", end="")
    linkedin_username = input()
config.set('linkedin', 'username', linkedin_username)

linkedin_password = ""
while linkedin_password == "":
    print("Insert linkedin password.")
    print("> ", end="")
    linkedin_password = input()
config.set('linkedin', 'password', linkedin_password)

print("Insert the system path to Chrome of the current device")
if config.get('system', 'os') == 'linux':
    print("Suggested: /usr/bin/google-chrome-stable")
if config.get('system', 'os') == 'macos':
    print("Suggested: leave blank")
if config.get('system', 'os') == 'windows':
    print("If you don't know it, try leaving it blank, but expect with a high probability some errors will occur.")

print("> ", end="")
config.set('system', 'chrome_path', input())

print("Insert the name of the .txt file that contains people profile urls.")
print("Notice: It doesn't matter if it doesn't exist right now. The profiles data files is there as an example")
print("Leave blank for default option (Input/profiles_data.txt)")
print("> ", end="")
input_file_name = input()
input_file_name = input_file_name if not input_file_name == "" else "Input/profiles_data.txt"
config.set('profiles_data', 'input_file_name', input_file_name)
with open(input_file_name, "w"):
    pass

print("Insert the name of the .xlsx file that will contain the results of the scraping by profile url.")
print("Leave blank for default option (ScrapedData/results_profiles.xlsx)")
print("> ", end="")
output_file_name = input()
output_file_name = output_file_name if not output_file_name == "" else "ScrapedData/results_profiles.xlsx"
config.set('profiles_data', 'output_file_name', output_file_name)

print("Do you want to append to it the timestamp in order to prevent to overwrite past results?")
print("Y for yes, N for no")
print("Leave blank for default option (Y)")
print("> ", end="")
append_timestamp = input()
append_timestamp = append_timestamp if not append_timestamp == "" else "Y"
config.set('profiles_data', 'append_timestamp', append_timestamp)


print("How many threads do you want to be spawn maximum?")
print("Leave blank for default option (4)")
print("> ", end="")
max_threads = input()
max_threads = max_threads if not max_threads == "" else "4"
config.set("system", "max_threads", max_threads)

with open('config.ini', 'w') as f:
    config.write(f)

print("")
print("Configuration completed. You can now do scraping.")
print("To scrape profile by url: execute scrape.py")
