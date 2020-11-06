// Enter servbot ip address here
const ADDRESS = "ws://localhost:6789/"


var value = document.querySelector('.value'),
    users = document.querySelector('.users'),
    error = document.querySelector('.error'),
    keystate = document.querySelector('.keystate'),
    controls = document.querySelector('.controls'),
    keysEnable = document.querySelector('.enable_button'),
    keysDisable = document.querySelector('.disable_button'),
    confirm = document.querySelector('#confirm'),
    login = document.querySelector('.login'),
    adminKey = document.querySelector('#adminkey'),
    key1 = document.querySelector('#key1'),
    key2 = document.querySelector('#key2'),
    users1 = document.querySelector('#users1'),
    users2 = document.querySelector('#users2'),
    token = "",
    buttons = ["up", "down", "left", "right", 
               "A","B","C","X","Y","Z", "esc"],
    s_id =[".session1 #buttons ", ".session2 #buttons "],           
    websocket = new WebSocket(ADDRESS);

keydown = function (btn, pl) {
    if (token != ""){
        websocket.send(JSON.stringify({action: "btn" + pl, btn : buttons[btn], value: 1, token : token}));
    }
}

keyup = function (btn, pl) {
    if (token != ""){
        websocket.send(JSON.stringify({action: "btn" + pl, btn : buttons[btn], value: 0, token : token}));
    }
}

enableKeys = function () {
    if (users.textContent !== 'Not logged in') {
        console.log(JSON.stringify({action: 'Enable',token: token}))
        websocket.send(JSON.stringify({action: 'Enable',token: token}));
    }
}

disableKeys = function () {
    if (users.textContent !== 'Not logged in') {
        websocket.send(JSON.stringify({action: 'Disable',token: token}));
    }
}

resetSession = function () {
    if (confirm.value === "Yes"){
        console.log("Kill clients");
        websocket.send(JSON.stringify({action: 'KILL clients', token: token}));
    }
    confirm.value = "No";
}

connect = function () {
    name = document.querySelector('#username').value;
    secret = document.querySelector('#Secret').value;
    console.log("Form returned:");
    console.log(name + ' ' + secret);
    token = secret;
    websocket.send(JSON.stringify({action: 'ADMIN', user: name, token: token}));
}

websocket.onmessage = function (event) {
    data = JSON.parse(event.data);
    console.log("Message value: " + data.value);
    console.log("Message value: " + data.value[0]);
    console.log("Message value: " + data.value[1]);
    console.log("Message id: " + data.id);
    switch (data.type) {
        case 'keystate':
            console.log("Data : " + data.value)
            if (data.value) {
                keystate.textContent = "ENABLED"
            }else {
                keystate.textContent = "DISABLED"
            }
            break;
        case 'users':
            console.log(data);
            text = "";
            for (let i = 0; i < data.value.length; i++ ) {
                if (i == 0) {
                    text += data.value[i].toString();
                }else {
                    text += " , "  + data.value[i].toString();
                }
            }
            if (data.value.length == 0) {
                text = "--";
            }
            if (data.id === 0) {
                users1.textContent = (text);
            }else if (data.id === 1) {
                users2.textContent = (text);
            }else {
                login.style.display = "none";
                controls.style.display = "block";
                users.textContent = (text);                                
            }
            break;
        
        case 'tokens':
            key1.textContent = data.value[0].toString();
            key2.textContent = data.value[1].toString();
            adminKey.textContent = data.value[2].toString();
            break;
        case 'state':
            for (let i = 0; i < data.value.length; i++ ) {
                console.log("Button value: " + i + " = " + data.value[i])
                if (data.value[i] == "1") {
                    console.log("CYAN")
                    document.querySelector(s_id[data.id] + '.' + buttons[i]).style.backgroundColor = "cyan";
                    
                } else {
                    document.querySelector(s_id[data.id] + '.' + buttons[i]).style.backgroundColor = "white";
                    
                }
            }
            break;
        default:
            console.error(
                "unsupported event", data);
    }
};
websocket.onclose = function (event) {
    console.log('Connection closed');
    login.style.display = "none";
    controls.style.display = "none";
    users.textContent = "Connection closed";
};
websocket.onerror = function(evt) {
    users.textContent = "Connection error, try refresh";
    console.log(evt);
};