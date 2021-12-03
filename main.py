import eel
import sys
import os
import downloader
from PIL import Image
import base64
from io import BytesIO
import re
import yaml
from pathlib import Path
import tkinter
import tkinter.filedialog as filedialog
from datetime import datetime

post_data = None
config_file = "settings.yml"

settings = {
    "bg_color": "#eeeeff",
    "font_color": "#000000",
    "session_id": "",
    "hint_disp": True,
    "filename": "[post_id]_[file_id]",
    "window_size": [1000, 800],
    "output_dir": "output",
    "subdir_name": "[fanclub_name]（[creator_name]）/[posted_short]_[title]",
    "port": 8080
}

@eel.expose
def selectFolder():
    root = tkinter.Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    directory_path = filedialog.askdirectory()
    return str(directory_path)

@eel.expose
def read_settings():
    global settings
    try:
        with open(config_file, "r+") as f:
            settings = yaml.load(f, Loader=yaml.SafeLoader)
    except:
        with open(config_file, "w") as f:
            yaml.dump(settings, f)
    return settings

@eel.expose
def write_settings(hint_disp):
    global settings
    settings["hint_disp"] = bool(hint_disp)
    try:
        with open(config_file, "w") as f:
            yaml.dump(settings, f)
    except:
        with open("log.txt", "w") as f:
            f.write("Settings save error.")

def onCloseWindow(page, sockets):
    print(sockets)
    print(page + 'が閉じられました。プログラムを終了します。')
    sys.exit(0)


@eel.expose
def get_data(url, s_id):
    global post_data, settings
    session_id = s_id
    settings["session_id"] = s_id
    try:
        post_data = downloader.scraping(url, session_id)
    except:
        return []
    data = []
    ## thumb + posted contents
    all_thumbs_data = [post_data["thumb"]] if post_data.get("thumb") != None else []
    all_thumbs_data += post_data["contents"]
    for i, con in enumerate(all_thumbs_data):
        name = str(post_data["post_id"]) + "_" + str(con["file_id"])
        print(name)
        if con["file_type"] == "image":
            img = con["thumb"].copy()
            buffered = BytesIO()
            img.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8').replace('\n', '')
            img_src = "data:image/jpeg;base64," + img_str
            buffered.close()
            d = [i, "img", name, img_src]
        else:
            d = [i, "text", name, con["file_url"]]
        data.append(d)
    return data


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


@eel.expose
def download(root_dir, subdir_name, filename_format):
    global post_data, settings
    small_post_data = post_data.copy()
    if "contents" in list(small_post_data.keys()):
        small_post_data.pop("contents")
    if "thumb" in list(small_post_data.keys()):
        small_post_data.pop("thumb")

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
    try:
        for i, con in enumerate([post_data["thumb"]]+post_data["contents"]):
            if con != None:
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
                res = downloader.download(con["file_url"], output_path, settings["session_id"])
                progress = int(round((i+1)*100 / len(post_data["contents"])))
                eel.set_progress_bar(progress, "%d"%(progress)+"%")
        eel.set_progress_bar(100, "100%")
    except:
        eel.set_progress_bar(-1, "ERROR!!")

if __name__ == "__main__":
    settings = read_settings()
    size = settings["window_size"]
    eel.init("web")
    # eel.start("main.html", close_callback=onCloseWindow, mode="chrome-app")
    eel.start("main.html", close_callback=onCloseWindow, size=size, port=settings["port"])