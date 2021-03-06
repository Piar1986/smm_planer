from __future__ import print_function
import pickle
import os.path
import re
import datetime
import time
import requests
import telegram
import vk_api
import tempfile
from urllib.parse import urlparse
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pathvalidate import sanitize_filename
from dotenv import load_dotenv


SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

WEEK_DAYS = {
    'понедельник': 0,
    'вторник': 1,
    'среда': 2,
    'четверг': 3,
    'пятница': 4,
    'суббота': 5,
    'воскресение': 6,
}


def post_facebook(access_token, group_id, filepath, text):
    if filepath:
        url = f"https://graph.facebook.com/{group_id}/photos"
        params = {
            'access_token':access_token,
            'caption':text,
        }
        with open(filepath, 'rb') as file:
            files = {
                'photo': file,
            }
            response = requests.post(url, params=params, files=files)
            response.raise_for_status()
        return
 
    url = f"https://graph.facebook.com/{group_id}/feed"
    params = {
        'access_token':access_token,
        'message':text,
    }
    response = requests.post(url, params=params)
    response.raise_for_status()

    
def post_telegram(bot_token, chat_id, filepath, text):
    bot = telegram.Bot(token=bot_token)
    
    if filepath:
        with open(filepath, 'rb') as file:
            bot.send_photo(chat_id=chat_id, photo=file)

    if text:
        bot.send_message(chat_id=chat_id, text=text)


def post_vkontakte(login, password, group_id, album_id, filepath, text):
    vk_session = vk_api.VkApi(login, password)
    vk_session.auth()
    vk = vk_session.get_api()
    upload = vk_api.VkUpload(vk_session)
    
    attachments = ''
    if filepath:
        photo = upload.photo(
            filepath,
            album_id=album_id,
            group_id=group_id
        )
    
        owner_id = photo[0]['owner_id']
        media_id = photo[0]['id']
        attachments=f"photo{owner_id}_{media_id}"

    vk.wall.post(
        owner_id=f"-{group_id}",
        attachments=attachments,
        message=text,
        )


def extract_file_id(text):
    #https://www.w3resource.com/python-exercises/re/python-re-exercise-42.php
    url = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)[0]
    parse_result = urlparse(url)
    file_id = parse_result.query[3:]
    return file_id


def get_file_title(file_id, drive):
    file = drive.CreateFile({'id': file_id})
    file.FetchMetadata(fields='title')
    file_title = file['title']
    return file_title


def download_image(file_id, file_title, drive, folder):
    filepath = os.path.join(folder, file_title)
    file = drive.CreateFile({'id': file_id})
    file.GetContentFile(filepath)
    return filepath


def download_txt(file_id, file_title, drive, folder):
    filepath = os.path.join(folder, sanitize_filename(file_title + '.txt'))
    file = drive.CreateFile({'id': file_id})
    file.GetContentFile(filepath, mimetype='text/plain')
    return filepath


def get_tag_status(tag):
    tag_status = False
    tag_normalize = tag.strip().lower()
    if tag_normalize=='да':
        tag_status = True
    return tag_status


def publish_post(
    post,
    facebook_access_token,
    facebook_group_id,
    telegram_bot_token,
    telegram_chat_id,
    vk_login,
    vk_password,
    vk_access_token,
    vk_group_id,
    vk_album_id,
    drive
    ):

    article_text = ''
    image_address = None
    vk_publication = post['vk_publication']
    telegram_publication = post['telegram_publication']
    facebook_publication = post['facebook_publication']
    article_file_id = post['article_file_id']
    image_file_id = post['image_file_id']

    with tempfile.TemporaryDirectory() as tmpdirname:

        if image_file_id:
            image_file_title = get_file_title(image_file_id, drive)
            image_address = download_image(image_file_id, image_file_title, drive, tmpdirname)
    
        if article_file_id:
            article_file_title = get_file_title(article_file_id, drive)
            article_filepath = download_txt(article_file_id, article_file_title, drive, tmpdirname)
    
            with open(article_filepath, 'r', encoding='utf8') as file:
                article_text = file.read()
            
        if vk_publication:
            post_vkontakte(
                vk_login,
                vk_password, 
                vk_group_id, 
                vk_album_id, 
                image_address,
                article_text,
            )
            
        if telegram_publication:
            post_telegram(
                telegram_bot_token,
                telegram_chat_id, 
                image_address,
                article_text,
            )
            
        if facebook_publication:
            post_facebook(
                facebook_access_token,
                facebook_group_id, 
                image_address,
                article_text,
            )
        

def get_post_publication_details(post, row_number, drive):

    post_publication_details = []
    article_file_id = None
    image_file_id = None

    vk_tag, telegram_tag, facebook_tag, publication_week_day_name, publication_hour, article_link, image_link, is_published_tag = post
    
    vk_publication = get_tag_status(vk_tag)
    telegram_publication = get_tag_status(telegram_tag)
    facebook_publication = get_tag_status(facebook_tag)
    is_published = get_tag_status(is_published_tag)
        
    if article_link:
        article_file_id = extract_file_id(article_link)
    
    if image_link:
        image_file_id = extract_file_id(image_link)
        
    publication_week_day = WEEK_DAYS[publication_week_day_name]

    post_publication_details = {
        'vk_publication': vk_publication,
        'telegram_publication': telegram_publication,
        'facebook_publication': facebook_publication,
        'publication_week_day': publication_week_day,
        'publication_hour': publication_hour,
        'article_file_id': article_file_id,
        'image_file_id': image_file_id,
        'is_published': is_published,
        'row_number': row_number,
    }
    
    return post_publication_details


def load_token_pickle():

    creds = None
    
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds


def find_posts_for_publication(posts):
    posts_for_publication = []
    today = datetime.datetime.today()
    today_week_day = today.weekday()
    today_hour = today.hour

    for post in posts:
        if today_week_day==post['publication_week_day'] and today_hour==post['publication_hour']:
            posts_for_publication.append(post)
    
    return posts_for_publication


def get_all_posts(creds, spreadsheet_id, range_name):
    service = build('sheets', 'v4', credentials=creds)
    request = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, 
        range=range_name, 
        valueRenderOption='FORMULA',
        )
    all_posts = request.execute()['values']
    return all_posts


def tag_published_post(creds, spreadsheet_id, row_number):    
    service = build('sheets', 'v4', credentials=creds)
    body = {
        'values': [['да']]
    }     
    request = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id, 
        range=f"Лист1!H{row_number}", 
        valueInputOption='USER_ENTERED',
        body=body,
        ).execute()


def main():
    load_dotenv()

    spreadsheet_id = os.getenv('SPREADSHEET_ID')
    range_name = os.getenv('RANGE_NAME')
    row_start_number = int(os.getenv('ROW_START_NUMBER'))

    facebook_access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
    facebook_group_id = os.getenv('FACEBOOK_GROUP_ID')

    telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

    vk_login = os.getenv('VK_LOGIN')
    vk_password = os.getenv('VK_PASSWORD')
    vk_access_token = os.getenv('VK_ACCESS_TOKEN')
    vk_group_id = os.getenv('VK_GROUP_ID')
    vk_album_id = os.getenv('VK_ALBUM_ID')

    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)

    creds = load_token_pickle()
    
    while True:
        not_published_posts = []
        all_posts = get_all_posts(creds, spreadsheet_id, range_name)
        
        for row_number, post in enumerate(all_posts, row_start_number):
            post_publication_details = get_post_publication_details(post, row_number, drive)
            post_is_published = post_publication_details['is_published']
            if post_is_published:
                continue
            not_published_posts.append(post_publication_details)
            
        posts_for_publication = find_posts_for_publication(not_published_posts)
    
        if not posts_for_publication:
            continue

        for post in posts_for_publication:
            publish_post(
                post,
                facebook_access_token,
                facebook_group_id,
                telegram_bot_token,
                telegram_chat_id,
                vk_login,
                vk_password,
                vk_access_token,
                vk_group_id,
                vk_album_id,
                drive
                )
            post_row_number = post['row_number']
            tag_published_post(creds, spreadsheet_id, post_row_number)
    
        time.sleep(300)


if __name__ == '__main__':
    main()