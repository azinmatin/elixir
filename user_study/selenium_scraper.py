from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from pyvirtualdisplay import Display
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import os
import time
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import json


class SeleniumScraper:
    def __init__(self):
        display = Display(visible=0, size=(800, 800))
        display.start()
        os.environ["PATH"] = "YOUR PATHS"
        capa = DesiredCapabilities.FIREFOX
        self.browser = webdriver.Firefox(capabilities=capa)

    def close(self):
        self.browser.quit()

    def page_scroll(self, end=False, count=2):
        r = 0
        scroll_script = 'window.scrollTo(0, document.body.scrollHeight);var ' \
                        'lenOfPage=document.body.scrollHeight;return lenOfPage;'
        try:
            lenOfPage = self.browser.execute_script(scroll_script)
            if end:
                count = 10000000
            match = False
            while r < count and not match:
                lastCount = lenOfPage
                time.sleep(1)
                lenOfPage = self.browser.execute_script(scroll_script)
                r += 1
                if lastCount == lenOfPage:
                    match = True
        except:
            print "error in scrolling"

    def movielens_login(self, login_page, user_name, password):
        self.browser.get(login_page)
        time.sleep(5)
        print('opened the login page')
        username_elem = self.browser.find_element_by_xpath('//input[@formcontrolname="userName"]')
        password_elem = self.browser.find_element_by_xpath('//input[@formcontrolname="password"]')
        username_elem.send_keys(user_name)
        password_elem.send_keys(password)
        login_attempt = self.browser.find_element_by_xpath("//button[(@type='submit')]")
        ActionChains(self.browser).move_to_element(login_attempt).perform()
        login_attempt.click()
        time.sleep(10)
        print ('login finished')
        print(self.browser.current_url)

    def movie_page_scraper(self, movie_link):
        self.browser.get(movie_link)
        time.sleep(2)
        self.page_scroll(end=True)
        # name
        elements = self.browser.find_elements_by_xpath("//h1[@class='movie-title']")
        name = ''
        if len(elements) > 0:
            name = elements[0].text

        # year movie-attr
        year = -1
        elements = self.browser.find_elements_by_xpath("//ul[@class='movie-attr']/li")
        if len(elements) > 0:
            year_text = elements[0].text
            if year_text.isdigit():
                year = int(year_text)

        # genres
        genres = []
        elements = self.browser.find_elements_by_xpath\
            ("//div[contains(@class, 'movie-highlights')]//a[@uisref='exploreGenreShortcut']/b")
        for elem in elements:
            genres.append(elem.text)

        # cast and directors
        cast = []
        directors = []
        elements = self.browser.find_elements_by_xpath("//div[@class='heading-and-data']")
        for elem in elements:
            field_desc_elems = elem.find_elements_by_xpath(".//div[@class='movie-details-heading']")
            if len(field_desc_elems) > 0:
                field_desc = field_desc_elems[0].text
                field_names_elems = elem.find_elements_by_xpath("./span/a")
                for person_elem in field_names_elems:
                    person_name = person_elem.text
                    if field_desc == 'Cast':
                        cast.append(person_name)
                    if field_desc == 'Directors':
                        directors.append(person_name)

        # description
        description = ''
        elements = self.browser.find_elements_by_xpath("//p[@class='lead plot-summary']")
        if len(elements) > 0:
            description = elements[0].text

        # tags
        tags = {}
        elements = self.browser.find_elements_by_xpath("//div[@class='movie-details-block']//div[@class='tag']")
        for elem in elements:
            tag_count = -1
            tag_name = ''
            count_elements = elem.find_elements_by_xpath(".//span[@class='tag-app-count']")
            if len(count_elements) > 0:
                tag_count = int(count_elements[0].text[1:])
            name_elements = elem.find_elements_by_xpath(".//a[@uisref='base.tagPage']/span")
            if len(name_elements) > 0:
                tag_name = name_elements[0].text
            if tag_name != '' and tag_count > 0:
                tags[tag_name] = tag_count

        info = {'name': name, 'genres': genres, 'tags': tags, 'description': description, 'cast': cast, 'directors':
            directors, 'year': year, 'link': movie_link}
        return info


if __name__ == "__main__":
    sc = SeleniumScraper()
    login_link = 'https://movielens.org/login'
    user_name = 'YOUR USERNAME'
    password = 'YOUR PASSWORD'
    sc.movielens_login(login_link, user_name, password)

    dataset = 'movielens-user-study-data'
    path = 'YOUR PATH'
    movies_files = 'items.txt'
    movies_features_file = 'movies_features.txt'
    links = []
    with open(path + movies_files, 'r') as f_in:
        next(f_in)
        for line in f_in:
            tabs = line.strip().split('\t')
            link = tabs[0]
            links.append(link)
    infos = []
    try:
        for link in links:
            info = sc.movie_page_scraper(link)
            time.sleep(2)
            print info
            infos.append(info)
        sc.close()
    except Exception as e:
        print e

    # writing infos
    with open(path + movies_features_file, 'w') as fout:
        json.dump(infos, fout)


