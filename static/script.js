function command(com){
    const requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json'},
        body: JSON.stringify({'command':com}),
        mode: 'cors'
    };
    fetch("command/",requestOptions);
}

function GetAndDrawDirsAndFiles(onclick_func, multiple_selection){
    document.getElementById("panel").innerHTML="";
    const requestOptions = {
        method: 'GET',
        headers: { 'Content-Type': 'application/json'},
        mode: 'cors'
    };
    fetch("/getdirs/",requestOptions).then(res=> res.json()).then(data=>{
        dirs = data.dirs;
        for(var i=0;i<dirs.length;i++){
            if (dirs[i][0]!=='.'){
                const newDiv = document.createElement("div");
                newDiv.innerHTML = '📁';
                newDiv.classList.add("space");
                newDiv.classList.add("noselect");
                newDiv.onclick = change_dir(dirs[i],onclick_func, multiple_selection);
                const newContent = document.createTextNode(dirs[i]);
                newDiv.appendChild(newContent);
                const currentDiv = document.getElementById("panel");
                currentDiv.appendChild(newDiv);
            }
        }
        files = data.files;
        for(var i=0;i<files.length;i++){
            if (files[i][0]!=='.'){
                const newDiv = document.createElement("div");
                if (checkFileExtenshion(files[i],['.webm','.mkv','.avi','.mp4']))
                    newDiv.innerHTML = '🎞';
                else if (files[i].substr(files[i].length-4)==='.ass' || files[i].substr(files[i].length-4)==='.srt' )
                    newDiv.innerHTML = '📜';
                else
                    newDiv.innerHTML = '📄';
                newDiv.classList.add("space");
                newDiv.classList.add("noselect");
                newDiv.onclick = onclick_func(files[i],onclick_func, multiple_selection);
                newDiv.id = files[i];
                const newContent = document.createTextNode(files[i]);
                newDiv.appendChild(newContent);
                if (multiple_selection)
                {
                    selCounter = document.createElement("span");
                    newDiv.appendChild(selCounter);
                    selCounter.classList.add('select-counter');
                    selCounter.id = files[i]+"selCounter";
                }
                const currentDiv = document.getElementById("panel");
                currentDiv.appendChild(newDiv);
            }
        }
    });
}

function appendToPlaylist(){
    const requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json'},
        mode: 'cors',
        body: JSON.stringify({files:selected_files})
    };
    fetch("/appendtoplaylist/",requestOptions);
    window.location.href='/';
}

function playNow(){
    const requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json'},
        mode: 'cors',
        body: JSON.stringify({files:selected_files})
    };
    fetch("/playnow/",requestOptions);
    window.location.href='/';
}

function openFiles(){
    if (selected_files.length!==0){
        document.getElementById("files-panel").classList.add("display-none");
        document.getElementById("openChose").classList.remove("display-none");
    }
}

function checkFileExtenshion(filename,extensions){
    for(var i=0;i<extensions.length;i++)
        if(filename.substr(filename.length-extensions[i].length)==extensions[i])
            return true;
    return false;
}

function change_dir(dir,onclick_func, multiple_selection){
    if (selected_files.length!==0)
        document.getElementById("open-button").classList.add("not-active");
    selected_files = [];
    return function(){
        const requestOptions = {
            method: 'POST',
            headers: { 'Content-Type': 'application/json'},
            mode: 'cors',
            body: JSON.stringify({dir:dir})
        };
        fetch("/changedir/",requestOptions).then(res=> res.json()).then(data=>{
            if (data.type ==='dir'){
                GetAndDrawDirsAndFiles(onclick_func, multiple_selection);
            }else{
                window.location.href='/';
            }
        });
    };
}

function updateSeletionCounters(){
    var el = document.getElementsByClassName("select-counter");
    for (var i=0;i<el.length;i++){
        el[i].innerHTML = "";
    }
    for (var i=0;i<selected_files.length;i++){
        document.getElementById(selected_files[i]+"selCounter").innerHTML = String(i+1);
    }
}

function selectFile(file){
    return function(){
        i = selected_files.indexOf(file);
        if (i===-1){
            if (selected_files.length===0)
                document.getElementById("open-button").classList.remove("not-active");
            selected_files.push(file);
            document.getElementById(file).classList.add("blue-background");
        }else{
            selected_files.splice(i,1);
            document.getElementById(file).classList.remove("blue-background");
            if (selected_files.length===0)
                document.getElementById("open-button").classList.add("not-active");
        }
        updateSeletionCounters();
    };
}
selected_files = [];