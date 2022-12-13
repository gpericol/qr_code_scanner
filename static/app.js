let waitScan = false;
$("#result").hide();

function onScanSuccess(decodedText, decodedResult) {
    if (waitScan){
        return;
    }

    waitScan = true;
    let  xhr = new XMLHttpRequest();
    xhr.open("POST", "/api", true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.send(JSON.stringify({ "text": decodedText }));
    // read result from server and show
    xhr.onloadend = function () {
        $("#result").show();
        $("#reader").hide();
        if (xhr.status == 200) {
            let result = JSON.parse(xhr.responseText);
            if (result.status == "OK") {
                $("#result").addClass("alert alert-success full");
                $("#result-button").addClass("btn btn-success");
            } else if(result.status == "OK?") { 
                $("#result").addClass("alert alert-warning full");
                $("#result-button").addClass("btn btn-warning");
            }
            else {
                $("#result").addClass("alert alert-danger full");
                $("#result-button").addClass("btn btn-danger");
            }
            $("#result-text").text(result.response);
        } 
    };
}

function resultOk() {
    $("#result").removeClass();
    $("#result").hide()
    $("#result-text").text("");
    $("#result-button").removeClass("");
    $("#reader").show();
    waitScan = false;
}
$("#result").on("click", resultOk);

let html5QrcodeScanner = new Html5QrcodeScanner("reader", { fps: 10});
html5QrcodeScanner.render(onScanSuccess);