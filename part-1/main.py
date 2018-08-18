from bs4 import BeautifulSoup
import sys
import os
import requests
import wget


LIMIT = 100
MAX_OFFSET = 4999901  # maximum offset (4,999,901+100-1 = 5,000,000 results)
FILE_SAVE_PATH = 'images/'
LOG_PATH = 'log.txt'

offset = 1
list_url = 'https://www.imdb.com/search/name?gender=male,female&count=100'

if not os.path.exists(FILE_SAVE_PATH):
    os.makedirs(FILE_SAVE_PATH)

while offset <= MAX_OFFSET:

    try:
        print('Loading list...')
        print('Offset:', offset, '\n')

        list = requests.get(list_url)
        print('List URL:', list_url, '\n')

        if list.status_code == 200:

            soup = BeautifulSoup(list.content, 'html.parser')
            next_list_url = soup.select('.lister-page-next.next-page')
            next_list_url = 'https://www.imdb.com' + next_list_url[0]['href']
            links = soup.select('h3.lister-item-header > a')

            for link in links:

                print('Loading actor''s page...')
                print('Actor:', link.text)

                actor_picture_save_path = None
                file_name = str(''.join('{:02x}'.format(ord(letter)) for letter in link.text)) + '.jpg'

                try:
                    actor_page_url = 'http://www.imdb.com' + link['href']
                    actor_page = requests.get(actor_page_url)

                    if actor_page.status_code == 200:

                        soup = BeautifulSoup(actor_page.content, 'html.parser')
                        actor_picture = soup.find('img', id='name-poster')

                        if actor_picture is not None:
                            actor_picture_source_url = actor_picture['src']
                            actor_picture_save_path = FILE_SAVE_PATH + file_name
                            wget.download(actor_picture_source_url, actor_picture_save_path, None)

                        else:
                            print('No image found')

                    else:
                        print(actor_page_url, 'HTTP status:', actor_page.status_code)

                    print('\n')
                except:
                    print('Unexpected error:', sys.exc_info()[0], '\n')

            log_file = open(LOG_PATH, 'w')
            log_file.write("Offset: " + str(offset) + '\n' + list_url + '\n\n')
            log_file.close()
            list_url = next_list_url

        else:
            print(list_url, 'HTTP status:', list.status_code, '\n')

    except:
        print('Unexpected error:', sys.exc_info()[0], '\n')
        pass

    offset += LIMIT
