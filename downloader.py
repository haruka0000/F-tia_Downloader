import os
import requests
import time
from bs4 import BeautifulSoup
import json
from configparser import ConfigParser
from http.cookiejar import CookieJar
from urllib.parse import urljoin, urlparse
from urllib.request import build_opener, HTTPCookieProcessor
import io
from datetime import datetime
from PIL import Image
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36"
}

FANTIA_URL_PREFIX = 'https://fantia.jp/'
FANTIA_API_ENDPOINT = urljoin(FANTIA_URL_PREFIX, '/api/v1/')

def scraping(url, session_id):
    url = url.replace(FANTIA_URL_PREFIX, FANTIA_API_ENDPOINT)
    cookies = {'_session_id': session_id.strip()}

    # スクレイピング対象の URL にリクエストを送り JSON を取得する
    try:
        res = requests.get(url, cookies=cookies, headers=headers)
    except:
        return None
    res_dict = json.loads(res.text)

    posted_at = datetime.strptime(res_dict['post']["posted_at"], '%a, %d %b %Y %H:%M:%S %z')
    post_data = {
        "fanclub_name":     res_dict['post']["fanclub"]["fanclub_name"],
        "creator_name":     res_dict['post']["fanclub"]["creator_name"],
        "title":            res_dict['post']["title"],
        "posted_full":      posted_at.strftime('%Y%m%d%H%M%S'),
        "posted_short":     posted_at.strftime("%Y%m%d"),
        "posted_time":      posted_at.strftime("%H%M%S"),
        "posted_hour":      posted_at.strftime("%H"),
        "posted_min":       posted_at.strftime("%M"),
        "posted_sec":       posted_at.strftime("%S"),
        "posted_day":       posted_at.strftime("%d"),
        "posted_month":     posted_at.strftime("%m"),
        "posted_year":      posted_at.strftime("%Y"),
        "post_id":          url.split("/")[-1],
        "thumb":            None,
        "contents":         []
    }

    if res_dict["post"].get("thumb") != None:
        ## Thumbnails
        post_data["thumb"] = {}
        post_data["thumb"]["file_type"] = "image"
        post_data["thumb"]["file_id"]   = "thumb"
        post_data["thumb"]["thumb_url"] = res_dict["post"]["thumb"]["thumb"]
        post_data["thumb"]["file_url"]  = res_dict["post"]["thumb"]["original"]
        post_data["thumb"]["thumb"]     = download_thumb_img(post_data["thumb"]["thumb_url"], session_id, interval_sec=0.1)
        post_data["thumb"]["fmt"]       = str(post_data["thumb"]["file_url"]).split(".")[-1].split("?")[0]

    if res_dict['post'].get('post_contents') != None:
        ## contents
        post_contents   = res_dict['post']['post_contents']
        for content in post_contents:
            if content.get('visible_status') in {"visible"}:
                ## For photos
                if content.get("category") == "photo_gallery":
                    post_photos = content.get('post_content_photos')
                    if post_photos != None:
                        for photo in post_photos:
                            con_dict = {}
                            con_dict["file_type"] = "image"
                            con_dict["file_id"] = photo['show_original_uri'].split("/")[-1]
                            org_uri_res         = requests.get(urljoin(FANTIA_URL_PREFIX, photo['show_original_uri']), cookies=cookies)
                            soup                = BeautifulSoup(org_uri_res.content, 'lxml')
                            con_dict["file_url"] = soup.img.get("src")
                            con_dict["thumb_url"] = photo['url']['thumb']
                            con_dict["fmt"]     = str(con_dict["file_url"]).split(".")[-1].split("?")[0]
                            con_dict["thumb"] = download_thumb_img(con_dict["thumb_url"], session_id, interval_sec=0.1)
                            post_data["contents"].append(con_dict.copy())

                ## For Files
                elif content.get("category") == "file":
                    con_dict = {}
                    con_dict["file_type"] = "other"
                    con_dict["file_id"]     = content.get("download_uri").split("/")[-1]
                    con_dict["file_url"]    = urljoin(FANTIA_URL_PREFIX, content.get("download_uri"))
                    con_dict["org_filename"]    = content.get("filename").split(".")[0]
                    con_dict["fmt"]         = content.get("filename").split(".")[-1]
                    con_dict["thumb"] = con_dict["org_filename"]+"."+con_dict["fmt"]
                    post_data["contents"].append(con_dict.copy())

    return post_data


def download(url, output_path, session_id=None, interval_sec=0.5):
    time.sleep(interval_sec)
    cookies = {'_session_id': session_id.strip()}
    try:
        res = requests.get(url, cookies=cookies)
        with open(output_path, 'wb') as download_file:
            download_file.write(res.content)
        return True
    except:
        return False

def download_thumb_img(url, session_id=None, interval_sec=2):
    cookies = {'_session_id': session_id.strip()}
    try:
        res = requests.get(url, cookies=cookies)
        thumb_img = Image.open(io.BytesIO(res.content))
        thumb_img = thumb_img.convert('RGB')
    except:
        blank = Image.new("RGB", (256,256), color=(73, 109, 137))
        thumb_img = blank
    return thumb_img
