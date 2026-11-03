import type { TicketStatus } from "@/components/ui/status-badge";

export interface DesignMessages {
  title: string;
  description: string;
  languageLabel: string;
  languageEnglish: string;
  languageHindi: string;
  languageGujarati: string;
  buttons: string;
  primary: string;
  secondary: string;
  ghost: string;
  danger: string;
  loading: string;
  forms: string;
  fieldLabel: string;
  fieldValue: string;
  fieldError: string;
  textAreaLabel: string;
  textAreaValue: string;
  card: string;
  cardTitle: string;
  cardText: string;
  statuses: Record<TicketStatus, string>;
  chat: string;
  citizenMessage: string;
  botMessage: string;
  quickReplies: string;
  quickReplyOne: string;
  quickReplyTwo: string;
  ticket: string;
  department: string;
  departmentValue: string;
  location: string;
  locationValue: string;
  filedAt: string;
  filedAtValue: string;
  copyId: string;
  copied: string;
  copyFailed: string;
  table: string;
  ticketId: string;
  status: string;
  drawer: string;
  openDrawer: string;
  closeDrawer: string;
  drawerText: string;
  emptyState: string;
  emptyTitle: string;
  emptyDescription: string;
  emptyAction: string;
  errorState: string;
  errorTitle: string;
  errorMessage: string;
  retry: string;
  retryNotice: string;
  loadingState: string;
  selectedReply: string;
  previewOnly: string;
}

const messages = {
  en: {
    title: "Furfuri Nagar Municipal Corporation",
    description: "The frontend scaffold is ready for the citizen service.",
    languageLabel: "Preview language",
    languageEnglish: "English",
    languageHindi: "हिन्दी",
    languageGujarati: "ગુજરાતી",
    buttons: "Buttons",
    primary: "Submit complaint",
    secondary: "Check status",
    ghost: "More details",
    danger: "Remove draft",
    loading: "Sending message",
    forms: "Labeled form controls",
    fieldLabel: "Public ticket ID",
    fieldValue: "FMC-261103-AB12",
    fieldError: "Enter a ticket ID to continue.",
    textAreaLabel: "Complaint details",
    textAreaValue: "Water has not reached our lane since yesterday.",
    card: "Card",
    cardTitle: "Public service update",
    cardText: "This panel uses the shared surface, border and shadow tokens.",
    statuses: {
      Filed: "Filed",
      Assigned: "Assigned",
      "In Progress": "In Progress",
      Resolved: "Resolved",
      Escalated: "Escalated",
    },
    chat: "Chat bubbles",
    citizenMessage: "Please repair the street light near Neem Chowk.",
    botMessage: "Your message is ready to be sent to the right team.",
    quickReplies: "Quick replies",
    quickReplyOne: "Yes, that is correct",
    quickReplyTwo: "I need to add a location",
    ticket: "Ticket card",
    department: "Department",
    departmentValue: "Water Supply",
    location: "Location",
    locationValue: "Ward 04, Neem Chowk",
    filedAt: "Filed at",
    filedAtValue: "3 Nov 2026",
    copyId: "Copy ID",
    copied: "Copied",
    copyFailed: "Could not copy the ticket ID.",
    table: "Responsive table",
    ticketId: "Ticket ID",
    status: "Status",
    drawer: "Drawer",
    openDrawer: "Open details drawer",
    closeDrawer: "Close drawer",
    drawerText: "This accessible panel closes with Escape or its close button.",
    emptyState: "Empty state",
    emptyTitle: "No tickets to show",
    emptyDescription: "New requests will appear here when they are filed.",
    emptyAction: "Start a request",
    errorState: "Error state",
    errorTitle: "Could not load this view",
    errorMessage: "Check your connection, then try again.",
    retry: "Try again",
    retryNotice: "This is a preview; no request was sent.",
    loadingState: "Loading skeleton",
    selectedReply: "Selected reply",
    previewOnly: "Component preview only",
  },
  hi: {
    title: "फुरफुरी नगर नगर निगम",
    description: "नागरिक सेवा के लिए फ्रंटएंड तैयार है।",
    languageLabel: "पूर्वावलोकन की भाषा",
    languageEnglish: "English",
    languageHindi: "हिन्दी",
    languageGujarati: "ગુજરાતી",
    buttons: "बटन",
    primary: "शिकायत भेजें",
    secondary: "स्थिति देखें",
    ghost: "और जानकारी",
    danger: "मसौदा हटाएँ",
    loading: "संदेश भेज रहे हैं",
    forms: "लेबल वाले फ़ॉर्म फ़ील्ड",
    fieldLabel: "सार्वजनिक टिकट आईडी",
    fieldValue: "FMC-261103-AB12",
    fieldError: "आगे बढ़ने के लिए टिकट आईडी लिखें।",
    textAreaLabel: "शिकायत का विवरण",
    textAreaValue: "कल से हमारी गली में पानी नहीं आया है।",
    card: "कार्ड",
    cardTitle: "नगर सेवा अपडेट",
    cardText: "यह पैनल साझा सतह, बॉर्डर और शैडो टोकन का उपयोग करता है।",
    statuses: {
      Filed: "दर्ज",
      Assigned: "सौंपा गया",
      "In Progress": "काम जारी",
      Resolved: "समाधान हुआ",
      Escalated: "बढ़ाया गया",
    },
    chat: "चैट संदेश",
    citizenMessage: "नीम चौक के पास की स्ट्रीट लाइट ठीक करें।",
    botMessage: "आपका संदेश सही विभाग को भेजने के लिए तैयार है।",
    quickReplies: "त्वरित जवाब",
    quickReplyOne: "हाँ, यह सही है",
    quickReplyTwo: "मुझे जगह बतानी है",
    ticket: "टिकट कार्ड",
    department: "विभाग",
    departmentValue: "जल आपूर्ति",
    location: "जगह",
    locationValue: "वार्ड ०४, नीम चौक",
    filedAt: "दर्ज समय",
    filedAtValue: "३ नवम्बर २०२६",
    copyId: "आईडी कॉपी करें",
    copied: "कॉपी हुआ",
    copyFailed: "टिकट आईडी कॉपी नहीं हो सकी।",
    table: "अनुकूल तालिका",
    ticketId: "टिकट आईडी",
    status: "स्थिति",
    drawer: "ड्रॉअर",
    openDrawer: "विवरण खोलें",
    closeDrawer: "ड्रॉअर बंद करें",
    drawerText: "यह पैनल Escape कुंजी या बंद बटन से बंद होता है।",
    emptyState: "खाली स्थिति",
    emptyTitle: "दिखाने के लिए कोई टिकट नहीं",
    emptyDescription: "नई शिकायतें दर्ज होने पर यहाँ दिखाई देंगी।",
    emptyAction: "नई शिकायत करें",
    errorState: "त्रुटि स्थिति",
    errorTitle: "यह जानकारी लोड नहीं हुई",
    errorMessage: "कनेक्शन जाँचें और फिर कोशिश करें।",
    retry: "फिर कोशिश करें",
    retryNotice: "यह केवल पूर्वावलोकन है; कोई अनुरोध नहीं भेजा गया।",
    loadingState: "लोडिंग संकेत",
    selectedReply: "चुना गया जवाब",
    previewOnly: "केवल घटक पूर्वावलोकन",
  },
  gu: {
    title: "ફુરફુરી નગર મહાનગરપાલિકા",
    description: "નાગરિક સેવા માટે ફ્રન્ટએન્ડ તૈયાર છે.",
    languageLabel: "પૂર્વાવલોકનની ભાષા",
    languageEnglish: "English",
    languageHindi: "हिन्दी",
    languageGujarati: "ગુજરાતી",
    buttons: "બટનો",
    primary: "ફરિયાદ મોકલો",
    secondary: "સ્થિતિ તપાસો",
    ghost: "વધુ વિગતો",
    danger: "મસદ્દો દૂર કરો",
    loading: "સંદેશ મોકલાઈ રહ્યો છે",
    forms: "લેબલવાળા ફોર્મ નિયંત્રણો",
    fieldLabel: "જાહેર ટિકિટ આઈડી",
    fieldValue: "FMC-261103-AB12",
    fieldError: "આગળ વધવા માટે ટિકિટ આઈડી દાખલ કરો.",
    textAreaLabel: "ફરિયાદની વિગતો",
    textAreaValue: "ગઈકાલથી અમારી શેરીમાં પાણી આવ્યું નથી.",
    card: "કાર્ડ",
    cardTitle: "નાગરિક સેવા અપડેટ",
    cardText: "આ પેનલ શેર કરેલા સપાટી, બોર્ડર અને શેડો ટોકન વાપરે છે.",
    statuses: {
      Filed: "નોંધાઈ",
      Assigned: "સોંપાયેલ",
      "In Progress": "કામ ચાલુ",
      Resolved: "ઉકેલાયેલ",
      Escalated: "એસ્કલેટ થયેલ",
    },
    chat: "ચેટ સંદેશા",
    citizenMessage: "નીમ ચોક પાસેની સ્ટ્રીટ લાઇટ ઠીક કરો.",
    botMessage: "તમારો સંદેશ યોગ્ય વિભાગને મોકલવા તૈયાર છે.",
    quickReplies: "ઝડપી જવાબો",
    quickReplyOne: "હા, આ સાચું છે",
    quickReplyTwo: "મારે સ્થળ ઉમેરવું છે",
    ticket: "ટિકિટ કાર્ડ",
    department: "વિભાગ",
    departmentValue: "પાણી પુરવઠો",
    location: "સ્થળ",
    locationValue: "વોર્ડ ૦૪, નીમ ચોક",
    filedAt: "નોંધણી સમય",
    filedAtValue: "૦૩ નવેમ્બર ૨૦૨૬",
    copyId: "આઈડી કૉપી કરો",
    copied: "કૉપી થયું",
    copyFailed: "ટિકિટ આઈડી કૉપી થઈ શકી નથી.",
    table: "અનુકૂળ કોષ્ટક",
    ticketId: "ટિકિટ આઈડી",
    status: "સ્થિતિ",
    drawer: "ડ્રોઅર",
    openDrawer: "વિગતો ખોલો",
    closeDrawer: "ડ્રોઅર બંધ કરો",
    drawerText: "આ પેનલ Escape કી અથવા બંધ બટનથી બંધ થાય છે.",
    emptyState: "ખાલી સ્થિતિ",
    emptyTitle: "દેખાડવા માટે કોઈ ટિકિટ નથી",
    emptyDescription: "નવી ફરિયાદો નોંધાયા પછી અહીં દેખાશે.",
    emptyAction: "નવી ફરિયાદ કરો",
    errorState: "ભૂલની સ્થિતિ",
    errorTitle: "આ માહિતી લોડ થઈ શકી નથી",
    errorMessage: "કનેક્શન તપાસીને ફરી પ્રયાસ કરો.",
    retry: "ફરી પ્રયાસ કરો",
    retryNotice: "આ માત્ર પૂર્વાવલોકન છે; કોઈ વિનંતી મોકલાઈ નથી.",
    loadingState: "લોડિંગ સંકેત",
    selectedReply: "પસંદ કરેલો જવાબ",
    previewOnly: "માત્ર ઘટક પૂર્વાવલોકન",
  },
} satisfies Record<string, DesignMessages>;

export type UiLanguage = keyof typeof messages;

export const UI_LANGUAGES: readonly { code: UiLanguage; label: string }[] = [
  { code: "en", label: "English" },
  { code: "hi", label: "हिन्दी" },
  { code: "gu", label: "ગુજરાતી" },
];

export function resolveUiLanguage(browserLanguage: string): UiLanguage {
  const languageCode = browserLanguage.split("-")[0]?.toLowerCase();
  return isUiLanguage(languageCode) ? languageCode : "en";
}

export function getDesignMessages(language: UiLanguage): DesignMessages {
  return messages[language];
}

function isUiLanguage(languageCode: string | undefined): languageCode is UiLanguage {
  return languageCode !== undefined && Object.hasOwn(messages, languageCode);
}
