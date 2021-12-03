function link(target) {
    window.location.href=target;
}
function copy_url() {
    var copyText = document.getElementById("settings-page");
    copyText.select();
    document.execCommand("copy");
    alert("Copied the text: " + copyText.value);
}

window.addEventListener('beforeunload', (event) => {
    // Cancel the event as stated by the standard.
    event.preventDefault();
    // Chrome requires returnValue to be set.
    event.returnValue = '';
});

const url_form  = document.getElementById("url");
url_form.oninput = function() {
    document.getElementById("submit-btn").disabled = false;
};

async function update() {
    document.getElementById("submit-btn").disabled = true;
    document.getElementById("dl-btn").disabled = true;
    document.getElementById("pbar-area").innerHTML = "";
    var thumb_area = document.getElementById('thumb-area');

    // Clear previous data
    thumb_area.innerHTML = "";

    var url = document.getElementById('url').value;
    var session_id = document.getElementById('session_id').value;

    let thumbs = await eel.get_data(url, session_id)();

    for(var i=0; i<thumbs.length; i++) {
        var li = document.createElement("li");
        var div = document.createElement("div");
        if(thumbs[i][1] == "img"){
            div.class = "image-box";
            // HTMLImageElement オブジェクトを作成する
            var img = document.createElement("img");
            img.src = thumbs[i][3];
            img.id  = thumbs[i][2];
            img.class = "image";
            div.appendChild(img);
        }else{
            var file_url = document.createElement("a");
            file_url.href = thumbs[i][3];
            file_url.text = thumbs[i][2];
            file_url.target = "_blank";
            div.appendChild(file_url);
        }
        li.appendChild(div);
        thumb_area.appendChild(li);
    }
    document.getElementById("dl-btn").disabled = false;
    document.getElementById("submit-btn").disabled = false;
}

async function download(){
    document.getElementById("submit-btn").disabled = true;
    document.getElementById("dl-btn").disabled = true;

    let subdir_name = document.getElementById('subdir_name').value;
    let root_dir = document.getElementById('root_dir').value;

    var filename = document.getElementById('filename').value;
    var pbar = document.createElement("progress");
    pbar.value = 0;
    pbar.id = "pbar";
    pbar.max = "100";
    pbar.textContent = "0%"
    var ptext = document.createElement("div");
    ptext.id = "ptext";
    document.getElementById("pbar-area").innerHTML = "";
    document.getElementById("pbar-area").appendChild(pbar);
    document.getElementById("pbar-area").appendChild(ptext);

    await eel.download(root_dir, subdir_name, filename);
    document.getElementById("submit-btn").disabled = false;
    writeSettings();
}

eel.expose(set_progress_bar);
function set_progress_bar(value, str_value){
    if(value < 0){
        document.getElementById("ptext").textContent = "ERROR!! 再起動してください";
    }
    document.getElementById("ptext").textContent = "";
    document.getElementById("pbar").value = value;
    document.getElementById("pbar").textContent = str_value;
    if (value == 100) {
        document.getElementById("ptext").textContent = "Finished!!";
    }
}

function tipCheck(){
    tips_check = document.getElementById("tips_checkbox");
    var tips = document.getElementsByClassName("tips");
    if (tips_check.checked == true) {
        for(var i=0; i<tips.length; i++) {
            tips[i].style.display = 'block';
        }
    } else{
        for(var i=0; i<tips.length; i++) {
            tips[i].style.display = 'none';
        }
    }
}

window.onload = function(){
    readSettings();
}
async function readSettings(){
    var settings = await eel.read_settings()();
    console.log(settings)
    var body = document.getElementById("main");
    body.style.backgroundColor = settings.bg_color;
    body.style.color = settings.font_color;
    document.getElementById('session_id').value = settings.session_id;
    document.getElementById('filename').value = settings.filename;
    document.getElementById('tips_checkbox').checked = settings.hint_disp;
    document.getElementById('root_dir').value = settings.output_dir;
    document.getElementById('subdir_name').value = settings.subdir_name;
    tipCheck();
}

function writeSettings(){
    var hint_disp = document.getElementById('tips_checkbox').checked;
    eel.write_settings(hint_disp);
}

async function select_dir(){
    const root_dir = await eel.selectFolder()();
    document.getElementById('root_dir').value = root_dir;
}
