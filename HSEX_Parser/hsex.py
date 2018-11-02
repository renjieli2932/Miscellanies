import requests
import io
import os
from bs4 import BeautifulSoup as bs
import time  # Set delay to avoid anti-mirroring mechanism
from tqdm import tqdm


def download(url):
    os.chdir('/Users/renjieli/Downloads/Hsex')
    with requests.Session() as VideoScraper:
        raw = VideoScraper.get(url)
        content = bs(raw.text,'lxml')
        videourl = content.find('meta',itemprop="video")
        videourl = videourl['content']
        videourl = videourl[1:-2]
        imageurl = content.find('meta',itemprop='image')
        imageurl = imageurl['content']
        title = content.find('meta',itemprop='name')
        title = title['content']
        os.mkdir(title)
        os.chdir('/Users/renjieli/Downloads/Hsex/'+title)
        image = requests.get(imageurl)
        with open('image.jpg','wb') as f:
            f.write(image.content)
        video = requests.get(videourl)
        print('Connected!')
        with open('video.mp4','wb') as f:
            f.write(video.content)
            print('Download Finish!')



def writelist(link):
    os.chdir('/Users/renjieli/Downloads/Hsex')
    with open('list.txt','a') as f:
        for url in link:
            f.write(url +'\n')

def retrieve():
    os.chdir('/Users/renjieli/Downloads/Hsex')
    with open('list.txt', 'r') as f:
        retrieve_data = f.read()
    return retrieve_data

with requests.Session() as scraper:
    first_time_run = True
    url = "https://hsex.tv/hot_list.htm"
    rooturl = "https://hsex.tv/" # used to parse video links
    raw = scraper.get(url) # rawdata from requests
    content = bs(raw.text,'lxml')
    titles = content.find_all(class_='caption title')
    link = []
    title_name = []
    for title in titles:
        href = title.find('a')
        link.append(href['href'])
        title_name.append(href.get_text())

    print(link)
    if not first_time_run:
        downloaded = retrieve()  # retrieve the videos that have been downloaded
    else:
        downloaded = []

    for videourl in link:
        if videourl in downloaded:
            link.remove(videourl)
            print('Existed..Pass')
            continue
        else:
            absurl = rooturl + videourl
            download(absurl)

    writelist(link)








