let audio1 = new Audio(
  "https://s3-us-west-2.amazonaws.com/s.cdpn.io/242518/clickUp.mp3"
);
function chatOpen() {
  document.getElementById("chat-open").style.display = "none";
  document.getElementById("chat-close").style.display = "block";
  document.getElementById("chat-window1").style.display = "block";

  audio1.load();
  audio1.play();
}
// function chatClose() {
//   document.getElementById("chat-open").style.display = "block";
//   document.getElementById("chat-close").style.display = "none";
//   document.getElementById("chat-window1").style.display = "none";
//   document.getElementById("chat-window2").style.display = "none";

//   audio1.load();
//   audio1.play();
// }
// function openConversation() {
//   document.getElementById("chat-window2").style.display = "block";
//   document.getElementById("chat-window1").style.display = "none";

//   audio1.load();
//   audio1.play();
// }

//Gets the text from the input box(user)
function userResponse() {

  console.log("response");
  let userText = document.getElementById("textInput").value;
  console.log(userText);
  if (userText == "") {
    alert("Please type something!");
  } else {
    document.getElementById("messageBox").innerHTML += `<div class="first-chat">
      <p>${userText}</p>

    </div>`;
    let audio3 = new Audio(
      "https://prodigits.co.uk/content/ringtones/tone/2020/alert/preview/4331e9c25345461.mp3"
    );
    audio3.load();
    audio3.play();
    dt = { 'msg': userText }
    document.getElementById("textInput").value = "";
    var objDiv = document.getElementById("messageBox");
    objDiv.scrollTop = objDiv.scrollHeight;

    setTimeout(() => {
      adminResponse(dt);
    }, 1000);
  }
}

//admin Respononse to user's message
function adminResponse(dt) {

  let d = new Date();
  let timestamp = d.toLocaleString();

  console.log(JSON.stringify(dt))

  fetch('http://127.0.0.1:5000/get', { method: 'POST', mode: 'no-cors', body: JSON.stringify(dt) })
    .then(response => response.json())
    .then(json => {
      console.log(json)
        document.getElementById("messageBox").innerHTML +=
          `<div class="yo">
          <div class="circle" id="circle-mar"></div>
          <p class="res">${json['response']}</p>      
          <p class="timestamp">${timestamp}</p>
        </div>`;

        let messageBox = document.getElementById("messageBox");
        let latestMessage = messageBox.lastElementChild;
        latestMessage.scrollIntoView();

      document.getElementById("textInput").style.backgroundColor = "#ffffff";

      let audio3 = new Audio(
        "https://downloadwap.com/content2/mp3-ringtones/tone/2020/alert/preview/56de9c2d5169679.mp3"
      );
      audio3.load();
      audio3.play();

    })
    .catch((error) => {
      console.log(error);
    });
  // Scroll the message box to the bottom
  var objDiv = document.getElementById("messageBox");
  objDiv.scrollTop = objDiv.scrollHeight;

  document.getElementById('textInput').scrollIntoView({ behavior: 'smooth' });


}

//press enter on keyboard and send message
addEventListener("keypress", (e) => {
  if (e.keyCode === 13) {

    const e = document.getElementById("textInput");
    if (e === document.activeElement) {
      console.log("event listener");
      userResponse();
    }
  }
});
