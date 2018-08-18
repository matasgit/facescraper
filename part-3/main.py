from bs4 import BeautifulSoup
import sys
import os
import requests
import wget
import cv2
import shutil
import math


def add_padding(padding, image_width, image_height, x, y, w, h):
    if x - padding < 0:
        x = 0
        w = w + (padding * 2)
        if w > image_width:
            w = image_width
    elif (w + x) + padding > image_width:
        x = x - padding - (padding - (image_width - (w + x)))
        w = w + (padding * 2)
        if x < 0:
            x = 0
    else:
        x = x - padding
        w = w + (padding * 2)

    if y - padding < 0:
        y = 0
        h = h + (padding * 2)
        if h > image_height:
            h = image_height
    elif (h + y) + padding > image_height:
        y = y - padding - (padding - (image_height - (h + y)))
        h = h + (padding * 2)
        if y < 0:
            y = 0
    else:
        y = y - padding
        h = h + (padding * 2)

    return x, y, w, h


LIMIT = 100
MAX_OFFSET = 4999901  # maximum offset (4,999,901+100-1 = 5,000,000 results)
FILE_SAVE_PATH = 'images/'
FACE_FILE_SAVE_PATH = 'images/faces/'
UNRESOLVED_FILE_SAVE_PATH = 'images/unresolved/'
LOG_PATH = 'log.txt'
FACE_SIZE = 120  # pixels
FACE_PADDING = 20  # percent
DISPLAY_PICTURES = True  # set this to True for easier debugging

offset = 1
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
total_success = 0
list_url = 'https://www.imdb.com/search/name?gender=male,female&count=100'

if not os.path.exists(FILE_SAVE_PATH):
    os.makedirs(FILE_SAVE_PATH)

if not os.path.exists(FACE_FILE_SAVE_PATH):
    os.makedirs(FACE_FILE_SAVE_PATH)

if not os.path.exists(UNRESOLVED_FILE_SAVE_PATH):
    os.makedirs(UNRESOLVED_FILE_SAVE_PATH)

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

                image = None
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

                            image = cv2.imread(actor_picture_save_path)
                            image_height, image_width, channels = image.shape
                            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

                            faces = face_cascade.detectMultiScale(
                                gray,
                                scaleFactor=1.1,
                                minNeighbors=5,
                                minSize=(30, 30)
                            )

                            if len(faces) != 1:
                                print('None or too many faces')
                                shutil.copyfile(actor_picture_save_path, UNRESOLVED_FILE_SAVE_PATH + file_name)
                                os.remove(actor_picture_save_path)
                                if DISPLAY_PICTURES:
                                    cv2.imshow('Face scraper - original', image)
                            else:
                                for (x, y, w, h) in faces:
                                    if DISPLAY_PICTURES:
                                        image_temp = image.copy()
                                        cv2.rectangle(image_temp, (x, y), (x + w, y + h), (0, 255, 0), 1)

                                    if w > FACE_SIZE or h > FACE_SIZE:
                                        padding = math.ceil(((w * FACE_PADDING) / 100) / 2)
                                        x, y, w, h = add_padding(padding, image_width, image_height, x, y, w, h)

                                    elif w < FACE_SIZE or h < FACE_SIZE:
                                        padding = math.ceil((FACE_SIZE - w) / 2)
                                        x, y, w, h = add_padding(padding, image_width, image_height, x, y, w, h)

                                    # else no padding needed

                                    if w == h:
                                        image_face = image[y: y + h, x: x + w]

                                        interpolation = None
                                        if w > FACE_SIZE or h > FACE_SIZE:
                                            interpolation = cv2.INTER_AREA
                                        elif w < FACE_SIZE or h < FACE_SIZE:
                                            interpolation = cv2.INTER_CUBIC

                                        if interpolation:
                                            image_face = cv2.resize(image_face, (FACE_SIZE, FACE_SIZE), interpolation)

                                        if DISPLAY_PICTURES:
                                            cv2.rectangle(image_temp, (x, y), (x + w, y + h), (255, 0, 0), 1)
                                            cv2.imshow('Face scraper - original', image_temp)
                                            cv2.imshow('Face scraper - face', image_face)

                                        cv2.imwrite(FACE_FILE_SAVE_PATH + file_name, image_face)
                                        total_success = total_success + 1
                                        print('Success (total {})'.format(total_success))
                                    else:
                                        print('Not a rectangular anymore... something went wrong')
                                        shutil.copyfile(actor_picture_save_path, UNRESOLVED_FILE_SAVE_PATH + file_name)
                                        os.remove(actor_picture_save_path)
                                        if DISPLAY_PICTURES:
                                            cv2.imshow('Face scraper - original', image)

                            if DISPLAY_PICTURES:
                                cv2.waitKey(0)
                                cv2.destroyAllWindows()

                        else:
                            print('No image found')

                    else:
                        print(actor_page_url, 'HTTP status:', actor_page.status_code)

                    print('\n')
                except:
                    print('Unexpected error:', sys.exc_info()[0], '\n')
                    if os.path.exists(actor_picture_save_path):
                        shutil.copyfile(actor_picture_save_path, UNRESOLVED_FILE_SAVE_PATH + file_name)
                        os.remove(actor_picture_save_path)
                    pass

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

print('Done (total {})'.format(total_success))
