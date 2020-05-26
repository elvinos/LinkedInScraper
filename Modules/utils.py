import re
import pyttsx3
from datetime import datetime
from selenium import webdriver


class HumanCheckException(Exception):
    """Human Check from Linkedin"""
    pass


class CannotProceedScrapingException(Exception):
    """Human Check from Linkedin during an headless mode execution"""
    pass


class Location:
    def __init__(self, city='N/A', country='N/A', location='N/A'):
        self.full_string = location
        self.city = city
        self.country = country

    def parse_string(self, location):
        self.full_string = location
        if ',' in location:
            # TODO: Probably useless try - except. To be checked.
            try:
                self.city = location.split(',')[0]
                self.country = location.split(',')[-1]
            except:
                pass

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)


class Company:
    def __init__(self, name='N/A', industry='N/A'):
        self.name = name
        self.industry = industry

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)


class Dates:
    def __init__(self, start_date='N/A', end_date='N/A'):
        self.start_date = start_date
        self.end_date = end_date

    def parse_date(self, date_range):
        try:
            if '–' in date_range:
                split_range = date_range.split('–')
                self.start_date = split_range[0].strip()
                self.end_date = split_range[1].strip()
                self.end_date = split_range[1].strip()
            elif ' – ' in date_range:
                split_range = date_range.split(' – ')
                self.start_date = split_range[0].strip()
                self.end_date = split_range[1].strip()
        except:
            self.start_date = date_range
            pass

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

class Role:
    def __init__(self, position='N/A', dates=Dates(), location=Location()):
        self.position = position
        self.dates = dates
        self.location = location

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)


class Job:
    def __init__(self, company=Company(), roles=None):
        if roles is None:
            roles = [Role()]
        self.company = company
        self.roles = roles

    def __set__(self, instance, value):
        self.instance = value

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

class Education:
    def __init__(self, school="N/A", dates=Dates(), deg_type="N/A", deg_sub="N/A", deg_desc="N/A"):
        self.school = school
        self.dates = dates
        self.deg_type = deg_type
        self.deg_sub = deg_sub
        self.deg_desc = deg_desc

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)


class Profile:
    def __init__(self, profile_link, profile_name="N/A", email="N/A", skills="N/A", jobs=None, education=None):
        self.profile_link = profile_link
        self.profile_name = profile_name
        self.email = email
        self.skills = skills
        if jobs is None:
            jobs = [Job()]
        if education is None:
            education = [Education()]
        self.jobs = jobs
        self.education = education


def linkedin_logout(browser):
    browser.get('https://www.linkedin.com/m/logout')


def linkedin_login(browser, username, password):
    browser.get('https://www.linkedin.com/uas/login')

    username_input = browser.find_element_by_id('username')
    username_input.send_keys(username)

    password_input = browser.find_element_by_id('password')
    password_input.send_keys(password)
    try:
        password_input.submit()
    except:
        pass


def chunks(lst, n):
    if n == 0:
        return [lst]
    """Yield successive n-sized chunks from lst."""
    return [lst[i:i + n] for i in range(0, len(lst), n)]


def is_url_valid(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None


def get_months_between_dates(date1, date2):
    if date1 < date2:
        diff = date2 - date1
    elif date1 > date2:
        diff = date1 - date2
    else:
        return 0

    return diff.days // 30


def boolean_to_string_xls(boolean_value):
    if boolean_value is None:
        return 'N/A'

    return 'X' if boolean_value else ''


def date_to_string_xls(date):
    if date is None:
        return 'N/A'

    return datetime.strftime(date, "%b-%y")


def message_to_user(message, config):
    print(message)

    if config.get('system', 'speak') == 'Y':
        engine = pyttsx3.init()
        engine.say(message)
        # engine.runAndWait()


def get_browser_options(headless_option, config):
    options = webdriver.ChromeOptions()

    options.add_argument('--no-sandbox')

    if headless_option:
        options.add_argument('--headless')

    options.add_argument('--disable-dev-shm-usage')

    if not config.get('system', 'chrome_path') == '':
        options.binary_location = r"" + config.get('system', 'chrome_path')

    return options
