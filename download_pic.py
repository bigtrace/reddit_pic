import pycurl
import io
import os
import pandas as pd
import re
import json
import requests
from urllib.parse import urlencode, quote_plus
import pickle
import time
import lxml.html
import time
import random
from pandas.tseries.offsets import BDay
import time
import smtplib
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os
from pathlib import Path

g_login = GoogleAuth()

g_login.LoadCredentialsFile("mycreds.txt")
if g_login.credentials is None:
    # Authenticate if they're not there
    g_login.LocalWebserverAuth()
elif g_login.access_token_expired:
    # Refresh them if expired
    g_login.Refresh()
else:
    # Initialize the saved creds
    g_login.Authorize()
# Save the current credentials to a file
g_login.SaveCredentialsFile("mycreds.txt")
#g_login.LocalWebserverAuth()
drive = GoogleDrive(g_login)


Path(r"image").mkdir(exist_ok=True)
current_directory = os.getcwd()
output_dir= os.path.join(current_directory,'image')

fileList = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()

fileID='1yXhfaz9H7-5e3ukwcmvmr8yvJFlYeoL_'



# get file ID from folder name
# for file in fileList:
#   print('Title: %s, ID: %s' % (file['title'], file['id']))
#   # Get the folder ID that you want
#   if(file['title'] == "reddit_pic"):
#       fileID = file['id']




c = pycurl.Curl()
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
c.setopt(pycurl.USERAGENT, USER_AGENT)
c.setopt(c.FOLLOWLOCATION, 1)
c.setopt(pycurl.FAILONERROR, True)
c.setopt(pycurl.SSL_VERIFYPEER, False)
c.setopt(pycurl.USERAGENT, USER_AGENT)
c.setopt(pycurl.VERBOSE, 0)

loggin_url = 'https://www.porn.com/pics/asiansgonewild'

c.setopt(pycurl.URL, loggin_url)
buffer = io.BytesIO()
c.setopt(c.WRITEFUNCTION, buffer.write)
c.perform()
body = buffer.getvalue().decode('utf-8', 'ignore')
# doc = lxml.html.fromstring(body)
# table_category = doc.xpath("//div[@class='list-pics__item']")

first_post_id = re.search(r'"id":"(.{6})","author":', body).group(1)
post_url = 'https://www.porn.com/wp-admin/admin-ajax.php'


def download_posts(first_post_id,page):
    #saved_files = os.listdir(output_dir)
    #exists_id = [re.search(r'-\[(.{6})\].', each).group(1) for each in saved_files]
    exist_img = drive.ListFile({'q': f"'{fileID}' in parents and trashed=false"}).GetList()
    exists_id = [each['title'] for each in exist_img]
    exists_id = [re.search(r'-\[(.{6})\].', each).group(1) for each in exists_id]

    data_form = {
        'path': '/r/asiansgonewild/hot.json',
        'action': 'reddit_proxy',
        'limit': 30,
        'after': f't3_{first_post_id}',
        'pager_page_id': page,
    }
    data_post = urlencode(data_form)

    buffer = io.BytesIO()
    c.setopt(pycurl.URL, post_url)
    c.setopt(pycurl.POST, 1)

    c.setopt(pycurl.POSTFIELDS, data_post)
    c.setopt(c.WRITEFUNCTION, buffer.write)
    c.setopt(pycurl.VERBOSE, 0)
    c.perform()
    data = buffer.getvalue().decode('utf-8', 'ignore')
    posts = json.loads(data)['posts']


    for each in posts:
        DOWNLOADED_FLAG = True
        author = each['author']
        id = each['id']
        if id in exists_id:
            print(f'----already saved this {id}----')
            continue

        if each['post_hint']=='rich:video':

            try:
                html_video = each['media']['html']
                video_url_id = re.search(r'https://redgifs.com/ifr/(.*)" frameborder',html_video).group(1)
                video_url = f'https://www.redgifs.com/ifr/{video_url_id}'
                print(f'video_url: {video_url}')

                resp = requests.get(video_url).text
                resp_lxml = lxml.html.fromstring(resp)
                urls = resp_lxml.xpath(f"//*[@id='video-{video_url_id}']/source/@src")
                url_hd = [each_url for each_url in urls if '.mp4' in each_url and '-mobile' not in each_url]
                print(f'url_hd: {url_hd}')
                response = requests.get(url_hd[0])
                filename = os.path.join(output_dir,f"[{author}]-[{id}].mp4")
                file = open(filename, "wb")
                file.write(response.content)
                file.close()
            except:
                print(f"[{author}]-[{id}].mp4 failed!")
                DOWNLOADED_FLAG = False

        elif each['post_hint']=='image':
            url_img = each['url']
            response = requests.get(url_img)
            print(f'url_img: {url_img}')
            filename = os.path.join(output_dir,f"[{author}]-[{id}].jpg")
            file = open(filename, "wb")
            file.write(response.content)
            file.close()

        pause_seconds = random.randint(5,8)
        print(f'pause scraping by {pause_seconds}')
        time.sleep(pause_seconds)
        #--------
        # try:
        if DOWNLOADED_FLAG :
            img_to_upload = filename
            with open(img_to_upload, "r") as file:
                file_drive = drive.CreateFile({'parents': [{'id': fileID}], 'title': os.path.basename(file.name)})
                file_drive.SetContentFile(img_to_upload)
                file_drive.Upload()
                file_drive.content.close()


                print(f'{img_to_upload} uploading successfully!')
            os.unlink(img_to_upload)
        # except:
        #     print(f'{img_to_upload} uploading failed!')



    return id,page+1

page = 1
for each in range(10):

    print(f'page： {page}')
    first_post_id,page = download_posts(first_post_id,page)