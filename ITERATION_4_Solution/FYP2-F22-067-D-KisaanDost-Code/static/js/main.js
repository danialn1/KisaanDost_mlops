//nav menu
function myFunction() {
  var element = document.getElementById("myDIV");
  console.log("main JS");
  element.classList.toggle("show");
}

const language = {
  ur: {
    title: "سوال پوچھیئے",
    greeting: "ہیلو {{ email }}!",
    menu: "مینو",
    chatbot: "چیٹ بوٹ",
    about: "ہمارے بارے میں",
    contact: "ہم سے رابطہ کریں",
    login: "لاگ ان کریں",
    signup: "شمولیت حاصل کریں",
    signout: "خارج ہوجائیے"
  },
  en: {
    title: "Ask a Question",
    greeting: "Hello {{ email }}!",
    menu: "Menu",
    chatbot: "Chatbot",
    about: "About us",
    contact: "Contact us",
    login: "Login",
    signup: "Sign up",
    signout: "Sign out"
  }
};


function updateTranslation() {
  // Get the current language
  var language = getCurrentLanguage();
  
  // Get all elements with the `data-i18n` attribute
  var elements = document.querySelectorAll('[data-i18n]');
  
  // Loop through each element
  elements.forEach(function(element) {
    // Get the key for the translation
    var key = element.getAttribute('data-i18n');
    
    // Set the innerHTML of the element to the corresponding translation
    element.innerHTML = translations[language][key];
  });
}

