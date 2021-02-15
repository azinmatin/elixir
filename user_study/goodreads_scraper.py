import oauth2 as oauth
import time
import json

from bs4 import BeautifulSoup


def book_page_scrape(client, book_url):
    response, content = client.request(book_url, 'GET')
    soup = BeautifulSoup(content, "html.parser")

    elems = soup.select('h1[id="bookTitle"]')
    title = ""
    if len(elems) > 0:
        title = elems[0].text.strip()

    elems = soup.select('div[id="details"] > div[class="row"]')
    year = None
    t_page = None
    if len(elems) > 0:
        t_page = elems[0].text.strip()
    else:
        print 'tpage found', book_url
    if len(elems) > 1:
        year = elems[1].text.strip()[17:-1].split('\n')[0]
    else:
        print 'year not found', book_url

    tags = {}
    elems = soup.select('div[class="elementList "]')
    for elem in elems:
        tags_elems = elem.select('a[class="actionLinkLite bookPageGenreLink"]')
        h_tags = []
        if len(tags_elems) > 0:
            for sub_elem in tags_elems:
                tag_name = sub_elem.text.strip()
                h_tags.append(tag_name)
        n_follow = 0
        count_elems = elem.select('a[rel="nofollow"]')
        if len(count_elems) > 0:
            count_text = count_elems[0].text[:-6].strip()
            count_text = count_text.replace(',', '')
            n_follow = int(count_text)
        if n_follow > 0 and len(h_tags) != 0:
            for tag_name in h_tags:
                if tag_name in tags and tag_name != h_tags[-1]:
                    continue
                tags[tag_name] = n_follow

    # last element elementList elementListLast
    elems = soup.select('div[class="elementList elementListLast"]')
    if len(elems) > 0:
        tag_name = ''
        tags_elems = elems[0].select('a[class="actionLinkLite bookPageGenreLink"]')
        if len(tags_elems) > 0:
            tag_name = tags_elems[-1].text.strip()
        n_follow = 0
        count_elems = elems[0].select('a[rel="nofollow"]')
        if len(count_elems) > 0:
            count_text = count_elems[0].text.strip().split(' ')[0]
            count_text = count_text.replace(',', '')
            n_follow = int(count_text)
        if n_follow > 0 and tag_name != '':
            tags[tag_name] = n_follow

    authors = []
    elems = soup.select('a[class="authorName"] > span')
    for elem in elems:
        authors.append(elem.text.strip())

    # ------ TO DO
    # scrape book description
    print 'scrape description -----------'

    book_info = {'title': title, 'tags': tags, 'authors': authors, 'year': year, 'link': book_url, 'extra_info': t_page}
    return book_info


def scrape_book_desc(link):
    response, content = client.request(link, 'GET')
    soup = BeautifulSoup(content, "html.parser")
    elems = soup.select('div[id="descriptionContainer"] > div[id="description"] > span')
    book_description = ''
    if len(elems) > 0:
        book_description = elems[0].text.strip().replace('\n', '')
        book_description = book_description.replace('\t', '')
    return book_description


if __name__ == "__main__":
    path = 'YOUR_PATH'
    key = "YOUR_KEY"
    secret = "YOUR_SECRET"
    base_url = 'http://www.goodreads.com'
    access_token = "YOUR_ACCESS_TOKEN"
    access_token_secret = "YOUR_ACCESS_TOCKEN_SECRET"
    consumer = oauth.Consumer(key=key, secret=secret)
    token = oauth.Token(access_token, access_token_secret)
    client = oauth.Client(consumer, token)
    book_features_file = 'books_features.txt'
    links = []
    link_file = 'books_links.txt'
    with open(path + link_file, 'r') as f_in:
        next(f_in)
        for line in f_in:
            tabs = line.strip().split('\t')
            link = tabs[0]
            links.append(link)
    infos = []
    try:
        counter = 0
        for link in links:
            book_info = book_page_scrape(client, link)
            time.sleep(1)
            print book_info
            counter += 1
            infos.append(book_info)
            print counter, 'finished'
    except Exception as e:
        print e

    # writing infos
    with open(path + book_features_file, 'w') as fout:
        json.dump(infos, fout)

    # ---- book description ----
    # try:
    #     book_desc = {}
    #     counter = 0
    #     for link in links:
    #         book_desc[link] = scrape_book_desc(link)
    #         time.sleep(1)
    #         print book_desc[link]
    #         counter +=1
    #         print counter, 'finished'
    # except Exception as e:
    #     print e
    #
    # # writing infos
    # with open(path + 'books_descriptions.txt', 'w') as f_out:
    #     f_out.write('book_url\tbook_description')
    #     counter = 0
    #     for link in book_desc:
    #         f_out.write('\n')
    #         f_out.write(link + '\t' + book_desc[link].encode('utf-8'))
    #         counter += 1
    #         print counter, 'finished'



