import type { UiLanguage } from "@/lib/i18n";

export interface StatusMessages {
  serviceName: string;
  serviceDescription: string;
  languageLabel: string;
  backToChat: string;
  title: string;
  description: string;
  ticketIdLabel: string;
  ticketIdPlaceholder: string;
  checkStatus: string;
  checkingStatus: string;
  resultTitle: string;
  department: string;
  location: string;
  filedAt: string;
  updatedAt: string;
  copyId: string;
  copied: string;
  copyFailed: string;
  timeline: string;
  noEventsTitle: string;
  noEventsDescription: string;
  notFoundTitle: string;
  notFoundMessage: string;
  errorTitle: string;
  errorMessage: string;
  retry: string;
  emptyTitle: string;
  emptyDescription: string;
}

const translations: Record<UiLanguage, StatusMessages> = {
  en: {
    serviceName: "Furfuri Nagar Municipal Corporation",
    serviceDescription: "Citizen grievance service",
    languageLabel: "Interface language",
    backToChat: "Back to chat",
    title: "Check your ticket",
    description:
      "Enter the ticket ID you received when your complaint was filed.",
    ticketIdLabel: "Ticket ID",
    ticketIdPlaceholder: "For example, FMC-261103-AB12",
    checkStatus: "Check status",
    checkingStatus: "Checking status",
    resultTitle: "Ticket details",
    department: "Department",
    location: "Location",
    filedAt: "Filed at",
    updatedAt: "Last updated",
    copyId: "Copy ticket ID",
    copied: "Copied",
    copyFailed: "Could not copy the ticket ID.",
    timeline: "Public updates",
    noEventsTitle: "No updates yet",
    noEventsDescription: "Public ticket updates will appear here.",
    notFoundTitle: "Ticket not found",
    notFoundMessage:
      "Check the ticket ID and try again. You can find it in your filing confirmation.",
    errorTitle: "We could not check this ticket",
    errorMessage: "Check your connection, then try again.",
    retry: "Try again",
    emptyTitle: "Enter a ticket ID",
    emptyDescription: "Your ticket status and public updates will appear here.",
  },
  hi: {
    serviceName: "फुरफुरी नगर नगर निगम",
    serviceDescription: "नागरिक शिकायत सेवा",
    languageLabel: "इंटरफ़ेस की भाषा",
    backToChat: "चैट पर वापस जाएँ",
    title: "अपनी टिकट की स्थिति देखें",
    description: "शिकायत दर्ज होने पर मिली टिकट आईडी लिखें।",
    ticketIdLabel: "टिकट आईडी",
    ticketIdPlaceholder: "उदाहरण: FMC-261103-AB12",
    checkStatus: "स्थिति देखें",
    checkingStatus: "स्थिति जाँची जा रही है",
    resultTitle: "टिकट का विवरण",
    department: "विभाग",
    location: "जगह",
    filedAt: "दर्ज समय",
    updatedAt: "आखिरी अपडेट",
    copyId: "टिकट आईडी कॉपी करें",
    copied: "कॉपी हुआ",
    copyFailed: "टिकट आईडी कॉपी नहीं हो सकी।",
    timeline: "सार्वजनिक अपडेट",
    noEventsTitle: "अभी कोई अपडेट नहीं",
    noEventsDescription: "टिकट के सार्वजनिक अपडेट यहाँ दिखाई देंगे।",
    notFoundTitle: "टिकट नहीं मिला",
    notFoundMessage:
      "टिकट आईडी जाँचकर फिर कोशिश करें। यह शिकायत दर्ज होने की पुष्टि में है।",
    errorTitle: "टिकट की स्थिति नहीं देख सके",
    errorMessage: "कनेक्शन जाँचें और फिर कोशिश करें।",
    retry: "फिर कोशिश करें",
    emptyTitle: "टिकट आईडी लिखें",
    emptyDescription: "टिकट की स्थिति और सार्वजनिक अपडेट यहाँ दिखाई देंगे।",
  },
  gu: {
    serviceName: "ફુરફુરી નગર મહાનગરપાલિકા",
    serviceDescription: "નાગરિક ફરિયાદ સેવા",
    languageLabel: "ઇન્ટરફેસની ભાષા",
    backToChat: "ચેટ પર પાછા જાઓ",
    title: "તમારી ટિકિટની સ્થિતિ જુઓ",
    description: "ફરિયાદ નોંધાયા પછી મળેલી ટિકિટ આઈડી દાખલ કરો.",
    ticketIdLabel: "ટિકિટ આઈડી",
    ticketIdPlaceholder: "ઉદાહરણ: FMC-261103-AB12",
    checkStatus: "સ્થિતિ જુઓ",
    checkingStatus: "સ્થિતિ તપાસાઈ રહી છે",
    resultTitle: "ટિકિટની વિગતો",
    department: "વિભાગ",
    location: "સ્થળ",
    filedAt: "નોંધણી સમય",
    updatedAt: "છેલ્લે અપડેટ",
    copyId: "ટિકિટ આઈડી કૉપી કરો",
    copied: "કૉપી થયું",
    copyFailed: "ટિકિટ આઈડી કૉપી થઈ શકી નથી.",
    timeline: "જાહેર અપડેટ",
    noEventsTitle: "હજુ કોઈ અપડેટ નથી",
    noEventsDescription: "ટિકિટના જાહેર અપડેટ અહીં દેખાશે.",
    notFoundTitle: "ટિકિટ મળી નથી",
    notFoundMessage:
      "ટિકિટ આઈડી તપાસીને ફરી પ્રયાસ કરો. તે ફરિયાદ નોંધાવ્યાની પુષ્ટિમાં છે.",
    errorTitle: "ટિકિટની સ્થિતિ તપાસી શકાઈ નથી",
    errorMessage: "કનેક્શન તપાસીને ફરી પ્રયાસ કરો.",
    retry: "ફરી પ્રયાસ કરો",
    emptyTitle: "ટિકિટ આઈડી દાખલ કરો",
    emptyDescription: "ટિકિટની સ્થિતિ અને જાહેર અપડેટ અહીં દેખાશે.",
  },
};

export function getStatusMessages(language: UiLanguage): StatusMessages {
  return translations[language];
}
