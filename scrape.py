import sys
import time
import xlsxwriter
from configparser import ConfigParser
import pickle

from Modules.profile_scraper import ProfileScraper
from Modules.utils import message_to_user, chunks


def scrape():
    # Loading of configurations
    config = ConfigParser()
    config.read('config.ini')

    headless_option = len(sys.argv) >= 2 and sys.argv[1] == 'HEADLESS'

    entries = []
    for entry in open(config.get('profiles_data', 'input_file_name'), "r"):
        entries.append(entry.strip())

    if len(entries) == 0:
        print("Please provide an input.")
        sys.exit(0)

    if headless_option:
        grouped_entries = chunks(entries, len(entries) // int(config.get('system', 'max_threads')))
    else:
        grouped_entries = [entries]

    if len(grouped_entries) > 1:
        print(f"Starting {len(grouped_entries)} parallel scrapers.")
    else:
        print("Starting scraping...")

        scrapers = []
        for entries_group in grouped_entries:
            scrapers.append(ProfileScraper(len(scrapers) + 1, entries_group, config, headless_option))
    try:
        for scraper in scrapers:
            scraper.start()

        for scraper in scrapers:
            scraper.join()

        scraping_results = []
        for scraper in scrapers:
            scraping_results.extend(scraper.results)

        write_to_work_book(scraping_results, config)
        if any(scraper.interrupted for scraper in scrapers):
            message_to_user(
                "The scraping didnt end correctly due to Human Check. The excel file was generated but it will "
                "contain some entries reporting an error string.", config)
        else:
            message_to_user('Scraping successfully ended.', config)
    except:
        for scraper in scrapers:
            scraper.join()

        scraping_results = []
        for scraper in scrapers:
            scraping_results.extend(scraper.results)

        write_to_work_book(scraping_results, config)
        message_to_user("Scraping was interrupted - results scraped have been saved")


def write_to_work_book(scraping_results, config):
    # Generation of XLS file with profiles data
    output_file_name = config.get('profiles_data', 'output_file_name')
    if config.get('profiles_data', 'append_timestamp') == 'Y':
        output_file_name_splitted = output_file_name.split('.')
        output_file_name = "".join(output_file_name_splitted[0:-1]) + "_" + str(int(time.time())) + "." + \
                           output_file_name_splitted[-1]

    pik_name = output_file_name.split('.xlsx')[0] + '.pkl'
    with open(pik_name, 'wb') as f:
        pickle.dump(scraping_results, f)

    workbook = xlsxwriter.Workbook(output_file_name)
    worksheet = workbook.add_worksheet()

    profile_headers = ['Link', 'Name']

    job_headers = []
    n_jobs = 15
    for n in range(n_jobs):
        i = str(n + 1)
        job_headers.append('Company_%s' % i)
        job_headers.append('Position_%s' % i)
        job_headers.append('Location_%s' % i)
        job_headers.append('Start_%s' % i)
        job_headers.append('End_%s' % i)

    edu_headers = []
    n_edu = 6
    for n in range(n_edu):
        i = str(n + 1)
        edu_headers.append('School_%s' % i)
        edu_headers.append('Start_school_%s' % i)
        edu_headers.append('End_school_%s' % i)
        edu_headers.append('Degree_type_%s' % i)
        edu_headers.append('Degree_sub_%s' % i)
        edu_headers.append('Degree_desc_%s' % i)

    headers = profile_headers + job_headers + edu_headers

    # Set the headers of xls file
    for h in range(len(headers)):
        worksheet.write(0, h, headers[h])

    for i in range(len(scraping_results)):

        scraping_result = scraping_results[i]

        if scraping_result.is_error():
            data = ['Error_' + scraping_result.message] * len(headers)
        else:
            p = scraping_result.profile
            prof_info_data = [p.profile_link, p.profile_name]
            job_data = []
            for job in p.jobs:
                for role in job.roles:
                    job_data.append(job.company.name)
                    job_data.append(role.position)
                    job_data.append(role.location.full_string)
                    job_data.append(role.dates.start_date)
                    job_data.append(role.dates.end_date)

            j_len = len(job_data)
            job_data = job_data + ((len(job_headers) - j_len) * [""])

            edu_data = []

            for ed in p.education:
                edu_data.append(ed.school)
                edu_data.append(ed.dates.start_date)
                edu_data.append(ed.dates.end_date)
                edu_data.append(ed.deg_type)
                edu_data.append(ed.deg_sub)
                edu_data.append(ed.deg_desc)

            edu_data = edu_data + ((len(edu_headers) - len(edu_data)) * [""])

            data = prof_info_data + job_data + edu_data

        for j in range(len(data)):
            worksheet.write(i + 1, j, data[j])

    workbook.close()


if __name__ == "__main__":
    # execute only if run as a script
    scrape()
