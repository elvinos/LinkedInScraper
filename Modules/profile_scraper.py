import traceback
from threading import Thread

from pyvirtualdisplay import Display

from Modules.utils import Profile, Location, Job, Company, Dates, Role, Education, CannotProceedScrapingException
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import numpy as np
from Modules.utils import linkedin_login, is_url_valid, HumanCheckException, message_to_user, get_browser_options, \
    linkedin_logout

"""
UPDATE Wait time here:
"""

pause_time = 3
scroll_time = 1

""""""

class ScrapingResult:
    def __init__(self, arg):
        if isinstance(arg, Profile):
            self.profile = arg
            self.message = None
        else:
            self.profile = None
            self.message = arg

    def is_error(self):
        return self.profile is None


class ProfileScraper(Thread):

    def __init__(self, identifier, entries, config, headless_option):

        Thread.__init__(self)

        self._id = identifier

        print(f"Scraper #{self._id}: Setting up the browser environment...")

        self.entries = entries

        self.results = []

        options = Options()
        options.add_experimental_option(
                                "excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.headless = headless_option

        # Creation of a new instance of Chrome
        self.browser = webdriver.Chrome(executable_path=config.get(
                                                           'system', 'driver'),
                                        chrome_options=options)

        self.industries_dict = {}

        self.config = config

        self.headless_option = headless_option

        self.interrupted = False

    def parse_entry(self, entry):
        # This function supports data as:
        #
        #   https://www.linkedin.com/in/federicohaag ==> parse name, email, last job
        #
        #   https://www.linkedin.com/in/federicohaag:::01/01/1730 ==> parse name, email, last job
        #   and also produces a "job history summary" returning if the person was working while studying,
        #   and how fast she/he got a job after the graduation.
        #   As graduation date is used the one passed as parameter, NOT the date it could be on LinkedIn

        profile_linkedin_url = entry

        if not profile_linkedin_url[-1] == '/':
            profile_linkedin_url += '/'

        return profile_linkedin_url

    def scrap_profile(self, profile_linkedin_url):
        rand = True

        if not is_url_valid(profile_linkedin_url):
            return ScrapingResult('BadFormattedLink')

        # Scraping of the profile may fail due to human check forced by LinkedIn
        try:
            # Setting of the delay (seconds) between operations that need to be sure loading of page is ended
            if rand:
                global pause_time
                global scroll_time
                
                loading_pause_time = np.random.randint(1, pause_time)
                loading_scroll_time = np.random.randint(1, scroll_time)
            else:
                loading_pause_time = 2
                loading_scroll_time = 1

            # Opening of the profile page
            self.browser.get(profile_linkedin_url)

            if not str(self.browser.current_url).strip() == profile_linkedin_url.strip():
                if self.browser.current_url == 'https://www.linkedin.com/in/unavailable/':
                    return ScrapingResult('ProfileUnavailable')
                else:
                    raise HumanCheckException

            # Loading the entire page (LinkedIn loads content asynchronously based on your scrolling)
            window_height = self.browser.execute_script("return window.innerHeight")
            scrolls = 1
            while scrolls * window_height < self.browser.execute_script("return document.body.offsetHeight"):
                self.browser.execute_script(f"window.scrollTo(0, {window_height * scrolls});")
                time.sleep(loading_scroll_time)
                scrolls += 1

            try:
                self.browser.execute_script(
                    "document.getElementsByClassName('pv-profile-section__see-more-inline')[0].click()")
                time.sleep(loading_pause_time)
            except:
                pass

            try:
                self.browser.execute_script(
                    "document.getElementsByClassName('pv-profile-section__see-more-inline')[1].click()")
                time.sleep(loading_pause_time)
            except:
                pass

            try:
                self.browser.execute_script(
                    "document.getElementsByClassName('pv-profile-section__see-more-inline')[2].click()")
                time.sleep(loading_pause_time)
            except:
                pass

            # Parsing of the page html structure
            soup = BeautifulSoup(self.browser.page_source, 'lxml')

            # Create a Profile Object and fill with data

            profile = Profile(profile_linkedin_url)
            # Scraping the Name (using soup)
            try:
                name_div = soup.find('div', {'class': 'flex-1 mr5'})
                name_loc = name_div.find_all('ul')
                profile_name = name_loc[0].find('li').get_text().strip()  # Not used
                profile.profile_name = profile_name
            except:
                pass
            jobs = self.get_jobs()

            if len(jobs) > 0:
                profile.jobs = jobs

            education = self.get_education()

            if len(education) > 0:
                profile.education = education

            return ScrapingResult(
                profile
            )
        except HumanCheckException:

            if self.headless_option:
                raise CannotProceedScrapingException

            linkedin_logout(self.browser)

            linkedin_login(self.browser, self.config.get('linkedin', 'username'),
                           self.config.get('linkedin', 'password'))

            while self.browser.current_url != 'https://www.linkedin.com/feed/':
                message_to_user('Please execute manual check', self.config)
                time.sleep(30)

            return self.scrap_profile(profile_linkedin_url)

    def get_profile_info(self):
        """Gets Profile info"""
        # try:
        #     name_div = soup.find('div', {'class': 'flex-1 mr5'})
        #     name_loc = name_div.find_all('ul')
        #     name_job = name_div.find_all('h2')
        #     profile_name = name_loc[0].find('li').get_text().strip()  # Not used
        #     # profile_job_full = name_job[0].get_text().strip()
        #     # profile_current_role = profile_job_full.split('at')[0].strip()
        #     # profile_current_comp = profile_job_full.split('at')[1].strip()
        #     # location = name_loc[1].find('li').get_text().strip()
        #
        # except:
        #     return ScrapingResult('ERROR IN DISPLAY')



    def get_jobs(self):
        jobs = []
        # Get all the job positions
        try:
            job_positions = self.browser.find_element_by_id('experience-section').find_elements_by_class_name(
                'pv-entity__position-group-pager')
        except:
            job_positions = []

        # Parsing the job positions
        if len(job_positions) > 0:

            # Parse job positions to extract relative the data ranges
            for job_position in job_positions:
                job_obj = Job()
                # Get the date range of the job position
                try:
                    # Check for multiple roles:
                    role_list = []
                    if job_position.find_elements_by_tag_name('ul'):
                        try:
                            job_comp_name = job_position.find_element_by_class_name(
                                'pv-entity__company-summary-info').find_elements_by_tag_name('span')[1].text
                            job_obj.company = Company(job_comp_name)
                        except:
                            pass
                        roles = job_position.find_elements_by_tag_name('li')
                        for role in roles:
                            role_list.append(self.get_role(role))
                    else:
                        try:
                            job_comp_name = job_position.find_element_by_class_name(
                                'pv-entity__secondary-title').text
                            job_obj.company = Company(job_comp_name)
                        except:
                            pass
                        role_list.append(self.get_role(job_position))
                except:
                    pass

                job_obj.roles = role_list
                jobs.append(job_obj)

        # for job in jobs:
        #     print(job.company)
        #     for role in job.roles:
        #         print(role)
        #         print(role.location)
        #         print(role.dates)
        return jobs

    def get_role(self, role):
        role_obj = Role()
        date_obj = Dates()
        loc_obj = Location()
        try:
            date_range_element = role.find_element_by_class_name('pv-entity__date-range')
            date_range_spans = date_range_element.find_elements_by_tag_name('span')
            role_date_range = date_range_spans[1].text
            date_obj.parse_date(role_date_range)
        except:
            pass

        multi = False
        try:
            if role.find_element_by_class_name('pv-entity__role-container'):
                # Multi role job
                sum_class = role.find_element_by_class_name('pv-entity__role-container')
                role_position = sum_class.find_elements_by_tag_name('h3')[0].find_elements_by_tag_name('span')[1].text
                role_obj.position = role_position
                multi = True
        except:
            pass

        try:
            if not multi:
            # Single role job
                role_position = role.find_elements_by_tag_name('h3')[0].text
                role_obj.position = role_position
        except:
            pass

        try:
            role_loc = role.find_element_by_class_name(
                'pv-entity__location').find_elements_by_tag_name('span')[1].text
            loc_obj.parse_string(role_loc)
        except:
            pass

        role_obj.dates = date_obj
        role_obj.location = loc_obj
        return role_obj

    def get_education(self):
        education = []
        try:
            education_s = self.browser.find_element_by_id(
                'education-section').find_elements_by_class_name(
                'pv-education-entity')
        except:
            education_s = []

        if len(education_s) > 0:
            for edu_s in education_s:
                edu = Education()
                try:
                    school_name = edu_s.find_elements_by_class_name('pv-entity__school-name')[0].text
                    edu.school = school_name
                except:
                    pass
                try:
                    degree_dates = edu_s.find_elements_by_class_name('pv-entity__dates')[0].find_elements_by_tag_name('span')[1].text
                    date_obj = Dates()
                    date_obj.parse_date(degree_dates)
                    edu.dates = date_obj
                except:
                    pass
                try:
                    degree_type = edu_s.find_elements_by_class_name(
                        'pv-entity__degree-name')[0].find_elements_by_tag_name('span')[1].text
                    edu.deg_type = degree_type
                except:
                    pass
                try:
                    degree_sub = edu_s.find_elements_by_class_name(
                        'pv-entity__fos')[0].find_elements_by_tag_name('span')[1].text
                    edu.deg_sub = degree_sub
                except:
                    pass
                try:
                    degree_desc = edu_s.find_elements_by_class_name('pv-entity__extra-details')[0].text
                    edu.deg_desc = degree_desc
                except:
                    pass
                education.append(edu)

        # for edu in education:
        #     print(edu)
        #     print(edu.dates)
        return education


    def get_skills(self):
        """ Gets Skills"""
    #     # Parsing skills
    #     try:
    #         self.browser.execute_script(
    #             "document.getElementsByClassName('pv-skills-section__additional-skills')[0].click()")
    #         time.sleep(self.loading_pause_time)
    #     except:
    #         pass
    #
    #     try:
    #         skills = self.browser.execute_script(
    #             "return (function(){els = document.getElementsByClassName('pv-skill-category-entity');results = [];for (var i=0; i < els.length; i++){results.push(els[i].getElementsByClassName('pv-skill-category-entity__name-text')[0].innerText);}return results;})()")
    #     except:
    #         skills = []
    #
    #     return skills


    def get_email(self):
        """Gets an email address"""
        # Scraping the Email Address from Contact Info (email)

        # > click on 'Contact info' link on the page
        # self.browser.execute_script(
        #     "(function(){try{for(i in document.getElementsByTagName('a')){let el = document.getElementsByTagName('a')[i]; "
        #     "if(el.innerHTML.includes('Contact info')){el.click();}}}catch(e){}})()")
        # time.sleep(loading_pause_time)
        #
        # # > gets email from the 'Contact info' popup
        # try:
        #     email = self.browser.execute_script(
        #         "return (function(){try{for (i in document.getElementsByClassName('pv-contact-info__contact-type')){ let "
        #         "el = "
        #         "document.getElementsByClassName('pv-contact-info__contact-type')[i]; if(el.className.includes("
        #         "'ci-email')){ "
        #         "return el.children[2].children[0].innerText; } }} catch(e){return '';}})()")
        #
        #     self.browser.execute_script("document.getElementsByClassName('artdeco-modal__dismiss')[0].click()")
        # except:
        #     email = 'N/A'

    def run(self):

        print(f"Scraper #{self._id}: Executing LinkedIn login...")

        # Doing login on LinkedIn
        linkedin_login(self.browser, self.config.get('linkedin', 'username'), self.config.get('linkedin', 'password'))

        while self.browser.current_url != 'https://www.linkedin.com/feed/':
            message_to_user('Please execute manual check', self.config)
            time.sleep(30)

        start_time = time.time()

        count = 0

        for entry in self.entries:
            # time.sleep(np.random.randint(0, 3))

            count += 1

            # Print statistics about ending time of the script
            if count > 1:
                time_left = ((time.time() - start_time) / count) * (len(self.entries) - count + 1)
                ending_in = time.strftime("%H:%M:%S", time.gmtime(time_left))
            else:
                ending_in = "Unknown time"

            print(f"Scraper #{self._id}: Scraping profile {count} / {len(self.entries)} - {ending_in} left")

            try:
                linkedin_url = self.parse_entry(entry)
                scraping_result = self.scrap_profile(linkedin_url)
                self.results.append(scraping_result)

            except CannotProceedScrapingException:
                self.results.append(ScrapingResult('TerminatedDueToHumanCheckError'))
                self.interrupted = True
                break

            except:
                with open("../errlog.txt", "a") as errlog:
                    traceback.print_exc(file=errlog)
                self.results.append(ScrapingResult('GenericError'))

        # Closing the Chrome instance
        self.browser.quit()

        end_time = time.time()
        elapsed_time = time.strftime('%H:%M:%S', time.gmtime(end_time - start_time))

        print(f"Scraper #{self._id}: Parsed {count} / {len(self.entries)} profiles in {elapsed_time}")
