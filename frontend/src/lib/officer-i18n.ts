import type { AdminTicketStatus } from "@/lib/api";
import type { UiLanguage } from "@/lib/i18n";

export interface OfficerMessages {
  serviceName: string;
  loginTitle: string;
  loginDescription: string;
  username: string;
  password: string;
  login: string;
  loggingIn: string;
  loginError: string;
  dashboardTitle: string;
  menu: string;
  closeMenu: string;
  ticketQueue: string;
  statusPage: string;
  analytics: string;
  signedInAs: string;
  administrator: string;
  logout: string;
  search: string;
  searchPlaceholder: string;
  statusFilter: string;
  allStatuses: string;
  dateFrom: string;
  dateTo: string;
  applyFilters: string;
  ticket: string;
  department: string;
  status: string;
  location: string;
  filed: string;
  escalation: string;
  openDetails: string;
  previous: string;
  next: string;
  page: string;
  emptyTitle: string;
  emptyDescription: string;
  loading: string;
  loadError: string;
  retry: string;
  detailTitle: string;
  complaint: string;
  language: string;
  timeline: string;
  noEvents: string;
  privateNote: string;
  publicNote: string;
  updateStatus: string;
  saveUpdate: string;
  saving: string;
  note: string;
  notePlaceholder: string;
  updateError: string;
  updateSuccess: string;
  close: string;
  backToChat: string;
  departments: Record<string, string>;
  statuses: Record<AdminTicketStatus, string>;
}

const translations: Record<UiLanguage, OfficerMessages> = {
  en: {
    serviceName: "Furfuri Nagar Municipal Corporation",
    loginTitle: "Staff login",
    loginDescription: "Sign in to manage municipal service tickets.",
    username: "Username",
    password: "Password",
    login: "Sign in",
    loggingIn: "Signing in",
    loginError: "Sign-in failed. Check your credentials and connection, then try again.",
    dashboardTitle: "Officer dashboard",
    menu: "Open dashboard navigation",
    closeMenu: "Close dashboard navigation",
    ticketQueue: "Ticket queue",
    statusPage: "Public ticket lookup",
    analytics: "Analytics",
    signedInAs: "Signed in",
    administrator: "Administrator",
    logout: "Sign out",
    search: "Search tickets",
    searchPlaceholder: "Ticket ID, complaint or location",
    statusFilter: "Filter by status",
    allStatuses: "All statuses",
    dateFrom: "Filed from",
    dateTo: "Filed through",
    applyFilters: "Apply filters",
    ticket: "Ticket",
    department: "Department",
    status: "Status",
    location: "Location",
    filed: "Filed",
    escalation: "Escalation",
    openDetails: "Open ticket details",
    previous: "Previous",
    next: "Next",
    page: "Page",
    emptyTitle: "No tickets found",
    emptyDescription: "Try changing or clearing the filters.",
    loading: "Loading tickets",
    loadError: "Tickets could not be loaded. Check your connection and retry.",
    retry: "Try again",
    detailTitle: "Ticket details",
    complaint: "Complaint",
    language: "Language",
    timeline: "Ticket history",
    noEvents: "No history is available.",
    privateNote: "Internal note",
    publicNote: "Show this note on the citizen status page",
    updateStatus: "Update status",
    saveUpdate: "Save update",
    saving: "Saving",
    note: "Note",
    notePlaceholder: "Add an update for this ticket",
    updateError: "The update could not be saved. Check the status and try again.",
    updateSuccess: "Ticket status updated.",
    close: "Close",
    backToChat: "Citizen chat",
    departments: {
      WATER: "Water Supply",
      ROADS: "Roads and Infrastructure",
      SANITATION: "Sanitation and Waste",
      ELECTRICITY: "Electricity",
      STREETLIGHT: "Street Lights",
      DRAINAGE: "Drainage and Sewage",
      HEALTH: "Public Health",
      TAX: "Property Tax and Billing",
      OTHER: "General or Unclear",
    },
    statuses: {
      FILED: "Filed",
      ASSIGNED: "Assigned",
      IN_PROGRESS: "In progress",
      RESOLVED: "Resolved",
      ESCALATED: "Escalated",
    },
  },
  hi: {
    serviceName: "फुरफुरी नगर नगर निगम",
    loginTitle: "कर्मचारी लॉगिन",
    loginDescription: "नगर सेवा टिकट प्रबंधित करने के लिए साइन इन करें।",
    username: "उपयोगकर्ता नाम",
    password: "पासवर्ड",
    login: "साइन इन करें",
    loggingIn: "साइन इन हो रहा है",
    loginError: "साइन इन नहीं हुआ। जानकारी और कनेक्शन जाँचकर फिर कोशिश करें।",
    dashboardTitle: "अधिकारी डैशबोर्ड",
    menu: "डैशबोर्ड नेविगेशन खोलें",
    closeMenu: "डैशबोर्ड नेविगेशन बंद करें",
    ticketQueue: "टिकट सूची",
    statusPage: "सार्वजनिक टिकट स्थिति",
    analytics: "आँकड़े",
    signedInAs: "साइन इन",
    administrator: "प्रशासक",
    logout: "साइन आउट",
    search: "टिकट खोजें",
    searchPlaceholder: "टिकट आईडी, शिकायत या जगह",
    statusFilter: "स्थिति से छाँटें",
    allStatuses: "सभी स्थितियाँ",
    dateFrom: "इस तारीख से",
    dateTo: "इस तारीख तक",
    applyFilters: "फ़िल्टर लागू करें",
    ticket: "टिकट",
    department: "विभाग",
    status: "स्थिति",
    location: "जगह",
    filed: "दर्ज",
    escalation: "एस्केलेशन",
    openDetails: "टिकट का विवरण खोलें",
    previous: "पिछला",
    next: "अगला",
    page: "पृष्ठ",
    emptyTitle: "कोई टिकट नहीं मिला",
    emptyDescription: "फ़िल्टर बदलें या हटाएँ।",
    loading: "टिकट लोड हो रहे हैं",
    loadError: "टिकट लोड नहीं हुए। कनेक्शन जाँचकर फिर कोशिश करें।",
    retry: "फिर कोशिश करें",
    detailTitle: "टिकट का विवरण",
    complaint: "शिकायत",
    language: "भाषा",
    timeline: "टिकट का इतिहास",
    noEvents: "कोई इतिहास उपलब्ध नहीं है।",
    privateNote: "आंतरिक टिप्पणी",
    publicNote: "यह टिप्पणी नागरिक की स्थिति पृष्ठ पर दिखाएँ",
    updateStatus: "स्थिति अपडेट करें",
    saveUpdate: "अपडेट सहेजें",
    saving: "सहेजा जा रहा है",
    note: "टिप्पणी",
    notePlaceholder: "टिकट के लिए अपडेट लिखें",
    updateError: "अपडेट सहेजा नहीं जा सका। स्थिति जाँचकर फिर कोशिश करें।",
    updateSuccess: "टिकट की स्थिति अपडेट हुई।",
    close: "बंद करें",
    backToChat: "नागरिक चैट",
    departments: {
      WATER: "जल आपूर्ति",
      ROADS: "सड़क एवं आधारभूत संरचना",
      SANITATION: "स्वच्छता एवं कचरा",
      ELECTRICITY: "बिजली",
      STREETLIGHT: "स्ट्रीट लाइट",
      DRAINAGE: "जल निकासी एवं सीवेज",
      HEALTH: "जन स्वास्थ्य",
      TAX: "संपत्ति कर एवं बिलिंग",
      OTHER: "सामान्य या अस्पष्ट",
    },
    statuses: {
      FILED: "दर्ज",
      ASSIGNED: "सौंपा गया",
      IN_PROGRESS: "कार्य जारी",
      RESOLVED: "हल हुआ",
      ESCALATED: "आगे बढ़ाया गया",
    },
  },
  gu: {
    serviceName: "ફુરફુરી નગર મહાનગરપાલિકા",
    loginTitle: "સ્ટાફ લૉગિન",
    loginDescription: "નગર સેવા ટિકિટ સંચાલિત કરવા સાઇન ઇન કરો.",
    username: "વપરાશકર્તા નામ",
    password: "પાસવર્ડ",
    login: "સાઇન ઇન કરો",
    loggingIn: "સાઇન ઇન થઈ રહ્યું છે",
    loginError: "સાઇન ઇન થઈ શક્યું નથી. વિગતો અને કનેક્શન તપાસીને ફરી પ્રયાસ કરો.",
    dashboardTitle: "અધિકારી ડૅશબોર્ડ",
    menu: "ડૅશબોર્ડ નેવિગેશન ખોલો",
    closeMenu: "ડૅશબોર્ડ નેવિગેશન બંધ કરો",
    ticketQueue: "ટિકિટ યાદી",
    statusPage: "જાહેર ટિકિટ સ્થિતિ",
    analytics: "આંકડા",
    signedInAs: "સાઇન ઇન",
    administrator: "વહીવટકર્તા",
    logout: "સાઇન આઉટ",
    search: "ટિકિટ શોધો",
    searchPlaceholder: "ટિકિટ આઈડી, ફરિયાદ અથવા સ્થળ",
    statusFilter: "સ્થિતિ પ્રમાણે ગાળો",
    allStatuses: "બધી સ્થિતિઓ",
    dateFrom: "આ તારીખથી",
    dateTo: "આ તારીખ સુધી",
    applyFilters: "ફિલ્ટર લાગુ કરો",
    ticket: "ટિકિટ",
    department: "વિભાગ",
    status: "સ્થિતિ",
    location: "સ્થળ",
    filed: "નોંધણી",
    escalation: "એસ્કેલેશન",
    openDetails: "ટિકિટની વિગતો ખોલો",
    previous: "પહેલાં",
    next: "આગળ",
    page: "પાનું",
    emptyTitle: "કોઈ ટિકિટ મળી નથી",
    emptyDescription: "ફિલ્ટર બદલો અથવા દૂર કરો.",
    loading: "ટિકિટ લોડ થઈ રહી છે",
    loadError: "ટિકિટ લોડ થઈ શકી નથી. કનેક્શન તપાસીને ફરી પ્રયાસ કરો.",
    retry: "ફરી પ્રયાસ કરો",
    detailTitle: "ટિકિટની વિગતો",
    complaint: "ફરિયાદ",
    language: "ભાષા",
    timeline: "ટિકિટનો ઇતિહાસ",
    noEvents: "કોઈ ઇતિહાસ ઉપલબ્ધ નથી.",
    privateNote: "આંતરિક નોંધ",
    publicNote: "આ નોંધ નાગરિકના સ્થિતિ પૃષ્ઠ પર બતાવો",
    updateStatus: "સ્થિતિ અપડેટ કરો",
    saveUpdate: "અપડેટ સાચવો",
    saving: "સાચવાઈ રહ્યું છે",
    note: "નોંધ",
    notePlaceholder: "આ ટિકિટ માટે અપડેટ લખો",
    updateError: "અપડેટ સાચવી શકાયું નથી. સ્થિતિ તપાસીને ફરી પ્રયાસ કરો.",
    updateSuccess: "ટિકિટની સ્થિતિ અપડેટ થઈ.",
    close: "બંધ કરો",
    backToChat: "નાગરિક ચેટ",
    departments: {
      WATER: "પાણી પુરવઠો",
      ROADS: "રસ્તા અને ઇન્ફ્રાસ્ટ્રક્ચર",
      SANITATION: "સફાઈ અને કચરો",
      ELECTRICITY: "વીજળી",
      STREETLIGHT: "સ્ટ્રીટ લાઇટ",
      DRAINAGE: "ગટર અને ગંદા પાણી",
      HEALTH: "જાહેર આરોગ્ય",
      TAX: "મિલકત વેરો અને બિલિંગ",
      OTHER: "સામાન્ય અથવા અસ્પષ્ટ",
    },
    statuses: {
      FILED: "નોંધાયેલ",
      ASSIGNED: "સોંપાયેલ",
      IN_PROGRESS: "કામ ચાલુ",
      RESOLVED: "ઉકેલાયેલ",
      ESCALATED: "આગળ મોકલાયેલ",
    },
  },
};

export function getOfficerMessages(language: UiLanguage): OfficerMessages {
  return translations[language];
}
