from cmath import e
from faulthandler import disable
from tkinter import Image
from turtle import window_width
import PySimpleGUI as sg
import sys
import os
import re
import yaml
from pathlib import Path
from datetime import datetime
from io import BytesIO
from tqdm import tqdm
import downloader

config_file = "settings.yml"

settings = {
    'theme': 'TealMono',
    "session_id": "",
    "hint_disp": True,
    "filename": "[post_id]_[file_id]",
    "window_size": [1200, 800],
    "output_dir": "output",
    "subdir_name": "[fanclub_name]（[creator_name]）/[posted_short]_[title]",
    "font": ["", 12],
    "targets": ['image', 'blog_image', 'thumbnail', 'other']
}
tips=[
    'Cookieの取得が必須です．\nブラウザを起動し，左のリンクを開いて Cookie > _session_id > コンテンツ の文字列をSession IDにコピーしてください．\nchrome以外の場合は変更が必要です．（例: brave:, vivaldi:）',
    'Fantiaの投稿URLを入力し，Submitを押すとサムネイルが表示されます.\n動画やファイルの場合，ダウンロード可能なファイルのURLが表示されます．',
    'Output Folder 下のフォルダの命名規則です．\nデフォルトは「ファンクラブ名（クリエイター名）/投稿日」になります．\n/でフォルダ階層を示します．',
    '各ファイルの命名規則です．予約語を組み合わせてください．',
    'サムネイル，ブログ内の画像，画像以外（動画や圧縮ファイル）を\nダウンロード対象とするかを指定できます．'
]
name_tags = [
    ['ファンクラブ名', '[fanclub_name]', ''],
    ['クリエイター名', '[creator_name]', ''],
    ['投稿日', '[posted_XXX]', '※XXXは時間の予約語を参照'],
    ['タイトル', '[title]', ''],
    ['投稿番号', '[post_id]', ''],
    ['ファイル名', '[file_id]', '※Sub Folder Naming Rule には使用不可'],
    ['ダウンロード時刻', '[now_XXX]', '※XXXは時間の予約語を参照'],
    ['時間の予約語', '', '例：[now_short]', ],
    ['YYYYMMDDhhmmss',  'full',   '（例：2021/07/16/ 01:06:00 → 20210716010600）'],
    ['YYYYMMDD',        'short',  '（例：2021/07/16/ → 20210716）'],
    ['hhmmss',          'time',   '（例：01:06:00 → 010600）'],
    ['その他',          'year, month, day, hour, min, sec', '[now_year], [posted_year]']
]
def read_settings():
    global settings
    try:
        with open(config_file, "r+") as f:
            settings = yaml.load(f, Loader=yaml.SafeLoader)
    except:
        with open(config_file, "w") as f:
            yaml.dump(settings, f)
    return settings

def write_settings():
    global settings
    try:
        with open(config_file, "w") as f:
            yaml.dump(settings, f)
    except:
        with open("log.txt", "w") as f:
            f.write("Settings save error.")

def get_layout(contents=[], is_first=False, size_label=(20,1), size_box=(50,1), url=""):
    font = settings['font']
    font_small = (font[0], int(font[1]*0.9))
    layout = [
        [sg.Text('F-tia Downloader', font=(font[0], int(font[1]*2)), size=(30, 1))],
        [sg.Text('Color Theme:', size=size_label, font=font), sg.Combo(values=sg.theme_list(), size=(20, 1), key='_theme_', enable_events=True, readonly=True, default_value=settings['theme'], )],
        [sg.Checkbox("Tips", key='_cb-hint_', enable_events=True, default=settings['hint_disp'])],
        [sg.Text('Setting Page:',               size=size_label, font=font),
         sg.Input('chrome://settings/cookies/detail?site=fantia.jp', disabled=True, font=font, size=size_box),
         sg.Text(tips[0], key='_tips-00_', size=(55,4), font=font_small, visible=settings['hint_disp'])],
        [sg.Text('Session ID:',                 size=size_label, font=font), 
         sg.Input(do_not_clear=True,            size=size_box, font=font, key='_sid_',    default_text=settings['session_id']),],
        [sg.Text('POST URL:',                   size=size_label, font=font), 
         sg.Input(do_not_clear=True,            size=size_box, font=font, key='_url_',    default_text=url),
         sg.Text(tips[1], key='_tips-01_', size=(55,4), font=font_small, visible=settings['hint_disp'])],
        [sg.Text('Output Folder:',              size=size_label, font=font), 
         sg.Input(do_not_clear=True,            size=(size_box[0]-10, size_box[1]), font=font, key='_dir_',    default_text=settings['output_dir']),
         sg.FolderBrowse(key="_select-dir_",      size=(8, size_box[1]))],
        [sg.Text('Naming Rule(sub folder):',    size=size_label, font=font), 
         sg.Input(do_not_clear=True,            size=size_box, font=font, key='_subdirname_', default_text=settings['subdir_name']),
         sg.Text(tips[2], key='_tips-02_', size=(55,4), font=font_small, visible=settings['hint_disp'])],
        [sg.Text('Naming Rule(file):',          size=size_label, font=font), 
         sg.Input(do_not_clear=True,            size=size_box, font=font, key='_filename_', default_text=settings['filename']),
         sg.Text(tips[3], key='_tips-03_', size=(55,4), font=font_small, visible=settings['hint_disp'])],
        [sg.Text('', size=(1,1), font=font_small),
         sg.Table(name_tags, headings=['予約語一覧', 'Tag', '備考'], key='_tb-01_', font=font_small, col_widths=[20, 25, 50], auto_size_columns=False, visible=settings['hint_disp'])],
        [sg.Checkbox("Thumbnail image", key='_cb-thumb_',       default='thumbnail' in settings['targets']),
         sg.Checkbox("Blog images",     key='_cb-blogimg_',     default='blog_image' in settings['targets']),
         sg.Checkbox("Other files",     key='_cb-other_',       default='other' in settings['targets']),
         sg.Text(tips[4], key='_tips-04_', size=(80,2), font=font_small, visible=settings['hint_disp'])],
        [sg.Button('Submit',    key='_submit_',     font=font,      disabled=False),
         sg.Button('Download',  key='_download_',   font=font,      disabled=is_first),
         sg.Button('Exit',      font=font)],
        [sg.ProgressBar(100, orientation='h', size=(40, 10), key='_progressbar_'), sg.Text('', font=font, key='_progress_')],
        [sg.Text('', key='_message_', font=font)]
    ]
    if contents != []:
        thumb_area_size = (settings['window_size'][0]-50, settings['window_size'][1]-50)
        layout+=[[sg.Column(contents, scrollable=True , vertical_scroll_only=True, size=thumb_area_size)]]
    return layout

def get_thmbs(post_data, col=2):
    ## thumb + posted contents
    all_thumbs_data = [post_data["thumb"]] if post_data.get("thumb") != None else []
    all_thumbs_data += post_data['blog_images']
    all_thumbs_data += post_data["contents"]
    thumbs = []
    row = []
    for i, con in enumerate(all_thumbs_data):
        name = str(post_data["post_id"]) + "_" + str(con["file_id"])
        if con["file_type"] in settings["targets"]:
            if con["file_type"] in ["image", "thumbnail", "blog_image"]:
                pil_img = con["thumb"].convert('RGB')
                pil_img.thumbnail(thumb_size)
                bio = BytesIO()
                pil_img.save(bio, format="PNG")
                del pil_img
                row.append(sg.Image(data=bio.getvalue()))
            else:
                row.append(sg.Text(con["file_url"], size=(20,10), font=settings["font"]))
        if len(row) >= col or i >= len(all_thumbs_data)-1 and row != []:
            thumbs.append(row)
            row = []
    return thumbs

def prepare_filename(name, post_dict, is_dir=False):
    now = datetime.now()
    time_dict = {
        "now_full":     now.strftime("%Y%m%d%H%M%S"),
        "now_short":    now.strftime("%Y%m%d"),
        "now_time":     now.strftime("%H%M%S"),
        "now_hour":     now.strftime("%H"),
        "now_min":      now.strftime("%M"),
        "now_sec":      now.strftime("%S"),
        "now_day":      now.strftime("%d"),
        "now_month":    now.strftime("%m"),
        "now_year":     now.strftime("%Y")
    }

    filename = name[:]
    if is_dir:
        path_names = filename.split("/")
    else:
        path_names = [filename]
    post_tags = list(post_dict.keys())
    date_tags = list(time_dict.keys())
    tags = post_tags + date_tags

    # print(path_names)
    new_path_names = []
    for pname in path_names:
        for tag in tags:
            if "[%s]"%tag in filename:
                tag_str = "[%s]"%tag
                if tag in date_tags:
                    v = time_dict[tag]
                else:
                    v = re.sub(r'[\\/:*?"<>|]+', '-', post_dict[tag])
                pname = pname.replace(tag_str, v)
        pname = re.sub(r'[\\/:*?"<>|]+', '', pname)
        new_path_names.append(pname)
    new_name = os.path.join(*new_path_names)
    # print(new_name)
    return new_name


def prepare_dl(post_data, values):
    global settings
    small_post_data = post_data.copy()
    if "contents" in small_post_data:
        small_post_data.pop("contents")
    if "thumb" in small_post_data:
        small_post_data.pop("thumb")
    if "blog_images" in small_post_data:
        small_post_data.pop("blog_images")


    root_dir = values['_dir_']
    subdir_name = values['_subdirname_']
    filename_format = values['_filename_']

    settings["subdir_name"] = str(subdir_name)
    root_dir = Path(str(root_dir))
    subdir_name = prepare_filename(str(subdir_name), small_post_data, is_dir=True)
    settings["output_dir"] = str(root_dir)

    ## Make output_dir
    output_dir = root_dir / subdir_name
    filenames = []
    try:
        os.makedirs(output_dir, exist_ok=True)
    except:
        exit()
    dl_list = post_data["contents"]
    if "blog_image" in settings["targets"]:
        dl_list = post_data["blog_images"] + dl_list
    if "thumbnail" in settings["targets"]:
        dl_list = [post_data["thumb"]] + dl_list

    contents = []
    for i, con in enumerate(dl_list):
        if con != None:
            if con['file_type'] in settings["targets"]:
                tmp_con = con.copy()
                tmp_con.update(small_post_data)
                filename = prepare_filename(filename_format, tmp_con)
                org_filename = filename[:]
                count = 0
                while filename in filenames:
                    count += 1
                    filename = org_filename.split(".")[0] + "_%02d"%(count)
                filenames.append(filename)
                filename = filename + "." + con["fmt"]
                output_path = output_dir / filename
                contents.append((con["file_url"], output_path))
    return contents


if __name__ == '__main__':
    read_settings()
    sg.theme(settings['theme'])
    window_title = "F-tia Downloader"
    thumb_size = (256, 256)
    layout = get_layout(is_first=True)
    location = (50,50)
    window = sg.Window('Window Title', location=location, size=settings['window_size']).Layout(layout)
    side_margin = 10
    col = (settings['window_size'][0]-2*side_margin) // thumb_size[0]

    post_data = None
    targets = set(settings['targets'])
    while True:
        event, values = window.Read()
        location = window.CurrentLocation()
        if event == '_theme_':
            settings['theme'] = values['_theme_']
            print(values['_theme_'])
            sg.theme(values['_theme_'])
        if event == '_cb-hint_':
            settings['hint_disp'] = values['_cb-hint_']
            for i in range(len(tips)):
                window['_tips-%02d_'%i].Update(visible=values['_cb-hint_'])
            window['_tb-01_'].Update(visible=values['_cb-hint_'])
        if event is None or event == 'Exit':
            settings['session_id'] = values['_sid_']
            settings['subdir_name'] = values['_subdirname_']
            settings['filename'] = values['_filename_']
            settings['output_dir'] = values['_dir_']
            settings['hint_disp'] = values['_cb-hint_']
            write_settings()
            break
        if event == '_submit_':
            settings['session_id'] = values['_sid_']
            settings['subdir_name'] = values['_subdirname_']
            settings['filename'] = values['_filename_']
            settings['output_dir'] = values['_dir_']
            if values['_cb-thumb_']:
                targets.add('thumbnail')
            else:
                targets.discard('thumbnail')
            if values['_cb-blogimg_']:
                targets.add('blog_image')
            else:
                targets.discard('blog_image')
            if values['_cb-other_']:
                targets.add('other')
            else:
                targets.discard('other')
            settings['targets'] = list(targets)

            try:
                post_data = downloader.scraping(values['_url_'], settings['session_id'])
            except:
                post_data = []

            if post_data != [] and post_data !=None:
                thumbs = get_thmbs(post_data, col)
                layout = get_layout(thumbs, url=values['_url_'])
                window_new = sg.Window(window_title, location=location, size=settings['window_size']).Layout(layout)
                window.Close()
                window = window_new
            else:
                window['_message_'].Update("Nothing found...")

        if event == '_download_':
            window['_progress_'].Update("Downloading...")
            window['_submit_'].Update(disabled=True)
            window['_download_'].Update(disabled=True)
            pbar = window['_progressbar_']
            dl_contents = prepare_dl(post_data, values)
            step = 100 // len(list(dl_contents))
            for i, (url, outpath) in enumerate(tqdm(dl_contents)):
                try:
                    downloader.download(url, outpath, settings['session_id'])
                except:
                    print("ERROR: Download failed.", url)
                pbar.UpdateBar((i+1)*step)
            pbar.UpdateBar(100)
            window['_progress_'].Update("Finished!")
            window['_download_'].Update(disabled=False)
            window['_submit_'].Update(disabled=False)
    window.Close()