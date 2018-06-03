from bs4 import BeautifulSoup
import sys
import os
import requests
import wget


LIMIT = 50
MAX_OFFSET = 99951  # maximum offset allowed by IMDb (99,951+50-1 = 100,000 results)
FILE_SAVE_PATH = 'images/'

offset = 1

if not os.path.exists(FILE_SAVE_PATH):
    os.makedirs(FILE_SAVE_PATH)

while offset <= MAX_OFFSET:

    try:
        print('Loading list...')
        print('Offset:', offset, '\n')

        list_url = 'http://www.imdb.com/search/name?gender=male,female&start=' + str(offset)
        list = requests.get(list_url)

        if list.status_code == 200:

            soup = BeautifulSoup(list.content, 'html.parser')
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

        else:
            print(list_url, 'HTTP status:', list.status_code, '\n')

    except:
        print('Unexpected error:', sys.exc_info()[0], '\n')
        pass

    offset += LIMIT
