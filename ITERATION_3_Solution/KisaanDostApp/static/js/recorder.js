
function convertUnicodeToText(unicodeString) {
  var textString = "";
  var unicodeArray = unicodeString.split("\\u");
  for (var i = 1; i < unicodeArray.length; i++) {
    textString += String.fromCharCode(parseInt(unicodeArray[i], 16));
  }
  return textString;
}





const recordButton = document.getElementById('recordButton');

// Initialize the MediaRecorder instance
let mediaRecorder = null;
let chunks = [];
let audioBlob = null;

recordButton.addEventListener('click', () => {
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    mediaRecorder.stop();
    return;
  }

  navigator.mediaDevices.getUserMedia({ audio: true })
    .then((stream) => {
      mediaRecorder = new MediaRecorder(stream);

      mediaRecorder.addEventListener('dataavailable', (event) => {
        chunks.push(event.data);
      });

      mediaRecorder.addEventListener('stop', () => {
        audioBlob = new Blob(chunks, { type: 'audio/wav' });
        chunks = [];

        // Send the audio blob to the server for transcription
        sendAudioToServer(audioBlob);
      });

      mediaRecorder.start();
    })
    .catch((error) => {
      console.error('Error accessing microphone:', error);
    });
});

// Send the recorded audio to the server for transcription
function sendAudioToServer(audioBlob) {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'audio.wav');

  fetch('/get', {
    method: 'POST',
    body: formData
  })
  .then(response => response.text())
  .then(transcription => {
    console.log('Transcription:', transcription);
    var textString = convertUnicodeToText(transcription);
    console.log('Converted text:', textString);
  })
  .catch(error => {
    console.error('Error transcribing audio:', error);
  });
}
