import type { UiLanguage } from "@/lib/i18n";

export interface ChatExample {
  label: string;
  text: string;
  language: string;
}

export interface ChatMessages {
  serviceName: string;
  serviceDescription: string;
  statusLink: string;
  languageLabel: string;
  welcomeTitle: string;
  welcomeDescription: string;
  examplesLabel: string;
  examples: [ChatExample, ChatExample, ChatExample];
  composerLabel: string;
  placeholder: string;
  send: string;
  sending: string;
  typing: string;
  wakingUp: string;
  errorTitle: string;
  genericError: string;
  tooLongError: string;
  rateLimitError: string;
  fontError: string;
  experimentalNote: string;
  ticketTitle: string;
  department: string;
  location: string;
  filedAt: string;
  copyId: string;
  copied: string;
  copyFailed: string;
}

const translations: Record<UiLanguage, ChatMessages> = {
  en: {
    serviceName: "Furfuri Nagar Municipal Corporation",
    serviceDescription: "Citizen grievance service",
    statusLink: "Check ticket status",
    languageLabel: "Interface language",
    welcomeTitle: "How can we help?",
    welcomeDescription:
      "Describe a municipal problem in your own words. We will guide you through the next steps.",
    examplesLabel: "Choose an example or type your complaint",
    examples: [
      {
        label: "Gujarati example",
        text: "અમારા વિસ્તારમાં બે દિવસથી નળમાં પાણી આવતું નથી. વોર્ડ ૦૪.",
        language: "gu",
      },
      {
        label: "Hinglish example",
        text: "Mere area mein do din se paani nahi aa raha, Neem Chowk ke paas.",
        language: "hinglish",
      },
      {
        label: "Unclear problem",
        text: "Something is wrong near the park.",
        language: "en",
      },
    ],
    composerLabel: "Complaint",
    placeholder: "Type your complaint in any supported language",
    send: "Send complaint",
    sending: "Sending message",
    typing: "The service is preparing a reply",
    wakingUp:
      "The service is starting up. This can take up to a minute. Please wait while we reconnect.",
    errorTitle: "We could not send your message",
    genericError:
      "Your text is still here. Check your connection, then review it before sending again.",
    tooLongError: "This message is too long. Shorten it and try again.",
    rateLimitError: "Too many messages were sent. Wait a moment, then try again.",
    fontError:
      "Some script fonts could not load. Your message is still available in the system font.",
    experimentalNote: "Support for this language is experimental.",
    ticketTitle: "Your complaint has been filed",
    department: "Department",
    location: "Location",
    filedAt: "Filed at",
    copyId: "Copy ticket ID",
    copied: "Copied",
    copyFailed: "Could not copy the ticket ID.",
  },
  hi: {
    serviceName: "फुरफुरी नगर नगर निगम",
    serviceDescription: "नागरिक शिकायत सेवा",
    statusLink: "टिकट की स्थिति देखें",
    languageLabel: "इंटरफ़ेस की भाषा",
    welcomeTitle: "हम आपकी कैसे मदद कर सकते हैं?",
    welcomeDescription:
      "नगरपालिका की समस्या अपने शब्दों में बताएँ। हम आगे के चरणों में आपका मार्गदर्शन करेंगे।",
    examplesLabel: "उदाहरण चुनें या अपनी शिकायत लिखें",
    examples: [
      {
        label: "गुजराती उदाहरण",
        text: "અમારા વિસ્તારમાં બે દિવસથી નળમાં પાણી આવતું નથી. વોર્ડ ૦૪.",
        language: "gu",
      },
      {
        label: "हिंग्लिश उदाहरण",
        text: "Mere area mein do din se paani nahi aa raha, Neem Chowk ke paas.",
        language: "hinglish",
      },
      {
        label: "अस्पष्ट समस्या",
        text: "पार्क के पास कुछ समस्या है।",
        language: "hi",
      },
    ],
    composerLabel: "शिकायत",
    placeholder: "किसी भी समर्थित भाषा में शिकायत लिखें",
    send: "शिकायत भेजें",
    sending: "संदेश भेज रहे हैं",
    typing: "सेवा जवाब तैयार कर रही है",
    wakingUp:
      "सेवा शुरू हो रही है। इसमें एक मिनट तक लग सकता है। कृपया जुड़ने तक प्रतीक्षा करें।",
    errorTitle: "आपका संदेश नहीं भेजा जा सका",
    genericError:
      "आपका संदेश यहाँ सुरक्षित है। कनेक्शन जाँचें और दोबारा भेजने से पहले उसे देख लें।",
    tooLongError: "यह संदेश बहुत लंबा है। इसे छोटा करके फिर भेजें।",
    rateLimitError: "बहुत सारे संदेश भेजे गए हैं। थोड़ी देर बाद फिर कोशिश करें।",
    fontError:
      "कुछ लिपियों के फ़ॉन्ट लोड नहीं हुए। आपका संदेश सिस्टम फ़ॉन्ट में दिख रहा है।",
    experimentalNote: "इस भाषा के लिए सहायता प्रायोगिक है।",
    ticketTitle: "आपकी शिकायत दर्ज हो गई है",
    department: "विभाग",
    location: "जगह",
    filedAt: "दर्ज समय",
    copyId: "टिकट आईडी कॉपी करें",
    copied: "कॉपी हुआ",
    copyFailed: "टिकट आईडी कॉपी नहीं हो सकी।",
  },
  gu: {
    serviceName: "ફુરફુરી નગર મહાનગરપાલિકા",
    serviceDescription: "નાગરિક ફરિયાદ સેવા",
    statusLink: "ટિકિટની સ્થિતિ જુઓ",
    languageLabel: "ઇન્ટરફેસની ભાષા",
    welcomeTitle: "અમે તમારી કેવી રીતે મદદ કરી શકીએ?",
    welcomeDescription:
      "નગરપાલિકાની સમસ્યા તમારા શબ્દોમાં જણાવો. આગળ શું કરવું તે અમે સમજાવીશું.",
    examplesLabel: "ઉદાહરણ પસંદ કરો અથવા તમારી ફરિયાદ લખો",
    examples: [
      {
        label: "ગુજરાતી ઉદાહરણ",
        text: "અમારા વિસ્તારમાં બે દિવસથી નળમાં પાણી આવતું નથી. વોર્ડ ૦૪.",
        language: "gu",
      },
      {
        label: "હિંગ્લિશ ઉદાહરણ",
        text: "Mere area mein do din se paani nahi aa raha, Neem Chowk ke paas.",
        language: "hinglish",
      },
      {
        label: "અસ્પષ્ટ સમસ્યા",
        text: "પાર્ક પાસે કંઈક સમસ્યા છે.",
        language: "gu",
      },
    ],
    composerLabel: "ફરિયાદ",
    placeholder: "કોઈપણ સમર્થિત ભાષામાં ફરિયાદ લખો",
    send: "ફરિયાદ મોકલો",
    sending: "સંદેશ મોકલાઈ રહ્યો છે",
    typing: "સેવા જવાબ તૈયાર કરી રહી છે",
    wakingUp:
      "સેવા શરૂ થઈ રહી છે. તેમાં એક મિનિટ લાગી શકે છે. ફરી જોડાઈએ ત્યાં સુધી રાહ જુઓ.",
    errorTitle: "તમારો સંદેશ મોકલી શકાયો નથી",
    genericError:
      "તમારો સંદેશ અહીં જ છે. કનેક્શન તપાસો અને ફરી મોકલતા પહેલાં તેને જોઈ લો.",
    tooLongError: "આ સંદેશ ઘણો લાંબો છે. ટૂંકો કરીને ફરી પ્રયાસ કરો.",
    rateLimitError: "ઘણા બધા સંદેશ મોકલાયા છે. થોડી વાર પછી ફરી પ્રયાસ કરો.",
    fontError:
      "કેટલીક લિપિના ફોન્ટ લોડ થયા નથી. તમારો સંદેશ સિસ્ટમ ફોન્ટમાં દેખાશે.",
    experimentalNote: "આ ભાષા માટેનો આધાર પ્રાયોગિક છે.",
    ticketTitle: "તમારી ફરિયાદ નોંધાઈ ગઈ છે",
    department: "વિભાગ",
    location: "સ્થળ",
    filedAt: "નોંધણી સમય",
    copyId: "ટિકિટ આઈડી કૉપી કરો",
    copied: "કૉપી થયું",
    copyFailed: "ટિકિટ આઈડી કૉપી થઈ શકી નથી.",
  },
};

/** Return chat interface copy for the selected Tier 1 UI language. */
export function getChatMessages(language: UiLanguage): ChatMessages {
  return translations[language];
}
