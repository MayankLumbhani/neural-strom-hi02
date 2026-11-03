import type { UiLanguage } from "@/lib/i18n";

export interface AnalyticsMessages {
  title: string;
  description: string;
  backToDashboard: string;
  logout: string;
  totalTickets: string;
  totalDescription: string;
  openTickets: string;
  openDescription: string;
  escalatedTickets: string;
  escalatedDescription: string;
  averageResolution: string;
  averageResolutionDescription: string;
  hoursValue: string;
  noResolutionTime: string;
  departmentTitle: string;
  statusTitle: string;
  languageTitle: string;
  count: string;
  category: string;
  noChartData: string;
  escalatedListTitle: string;
  noEscalatedTitle: string;
  noEscalatedDescription: string;
  showingRecent: string;
  ticket: string;
  department: string;
  location: string;
  filed: string;
  escalationLevel: string;
  loading: string;
  errorTitle: string;
  errorMessage: string;
  retry: string;
}

const translations: Record<UiLanguage, AnalyticsMessages> = {
  en: {
    title: "Admin analytics",
    description: "A summary of tickets across municipal departments.",
    backToDashboard: "Ticket dashboard",
    logout: "Sign out",
    totalTickets: "Total tickets",
    totalDescription: "All tickets in the service",
    openTickets: "Open tickets",
    openDescription: "Tickets not yet resolved",
    escalatedTickets: "Escalated tickets",
    escalatedDescription: "Tickets that need attention",
    averageResolution: "Average resolution time",
    averageResolutionDescription: "Calculated for resolved tickets",
    hoursValue: "{hours} hours",
    noResolutionTime: "No resolved tickets yet",
    departmentTitle: "Tickets by department",
    statusTitle: "Status breakdown",
    languageTitle: "Language mix",
    count: "Tickets",
    category: "Category",
    noChartData: "There is no ticket data to show yet.",
    escalatedListTitle: "Escalated ticket queue",
    noEscalatedTitle: "No escalated tickets",
    noEscalatedDescription: "Tickets that need attention will appear here.",
    showingRecent: "Showing {shown} of {total} escalated tickets.",
    ticket: "Ticket",
    department: "Department",
    location: "Location",
    filed: "Filed",
    escalationLevel: "Escalation level",
    loading: "Loading analytics",
    errorTitle: "Analytics could not be loaded",
    errorMessage: "Check your connection and try again.",
    retry: "Try again",
  },
  hi: {
    title: "प्रशासनिक आँकड़े",
    description: "नगर विभागों के सभी टिकटों का सारांश।",
    backToDashboard: "टिकट डैशबोर्ड",
    logout: "साइन आउट",
    totalTickets: "कुल टिकट",
    totalDescription: "सेवा के सभी टिकट",
    openTickets: "खुले टिकट",
    openDescription: "जिन टिकटों का समाधान नहीं हुआ",
    escalatedTickets: "आगे बढ़ाए गए टिकट",
    escalatedDescription: "जिन टिकटों पर ध्यान देना है",
    averageResolution: "औसत समाधान समय",
    averageResolutionDescription: "हल हुए टिकटों के आधार पर",
    hoursValue: "{hours} घंटे",
    noResolutionTime: "अभी कोई टिकट हल नहीं हुआ",
    departmentTitle: "विभाग के अनुसार टिकट",
    statusTitle: "स्थिति के अनुसार टिकट",
    languageTitle: "भाषा के अनुसार टिकट",
    count: "टिकट",
    category: "श्रेणी",
    noChartData: "दिखाने के लिए अभी टिकट डेटा नहीं है।",
    escalatedListTitle: "आगे बढ़ाए गए टिकटों की सूची",
    noEscalatedTitle: "कोई टिकट आगे नहीं बढ़ाया गया",
    noEscalatedDescription: "ध्यान देने वाले टिकट यहाँ दिखाई देंगे।",
    showingRecent: "{total} में से {shown} आगे बढ़ाए गए टिकट दिखाए जा रहे हैं।",
    ticket: "टिकट",
    department: "विभाग",
    location: "जगह",
    filed: "दर्ज",
    escalationLevel: "एस्केलेशन स्तर",
    loading: "आँकड़े लोड हो रहे हैं",
    errorTitle: "आँकड़े लोड नहीं हुए",
    errorMessage: "कनेक्शन जाँचकर फिर कोशिश करें।",
    retry: "फिर कोशिश करें",
  },
  gu: {
    title: "વહીવટી આંકડા",
    description: "નગરપાલિકાના તમામ વિભાગોની ટિકિટનો સારાંશ.",
    backToDashboard: "ટિકિટ ડૅશબોર્ડ",
    logout: "સાઇન આઉટ",
    totalTickets: "કુલ ટિકિટ",
    totalDescription: "સેવાની તમામ ટિકિટ",
    openTickets: "ચાલુ ટિકિટ",
    openDescription: "જે ટિકિટનો ઉકેલ આવ્યો નથી",
    escalatedTickets: "આગળ મોકલાયેલી ટિકિટ",
    escalatedDescription: "જે ટિકિટ પર ધ્યાન આપવું જરૂરી છે",
    averageResolution: "સરેરાશ ઉકેલ સમય",
    averageResolutionDescription: "ઉકેલાયેલી ટિકિટના આધારે",
    hoursValue: "{hours} કલાક",
    noResolutionTime: "હજુ કોઈ ટિકિટ ઉકેલાઈ નથી",
    departmentTitle: "વિભાગ પ્રમાણે ટિકિટ",
    statusTitle: "સ્થિતિ પ્રમાણે ટિકિટ",
    languageTitle: "ભાષા પ્રમાણે ટિકિટ",
    count: "ટિકિટ",
    category: "વિભાગ",
    noChartData: "હજુ બતાવવા માટે ટિકિટનો ડેટા નથી.",
    escalatedListTitle: "આગળ મોકલાયેલી ટિકિટની યાદી",
    noEscalatedTitle: "કોઈ ટિકિટ આગળ મોકલાઈ નથી",
    noEscalatedDescription: "ધ્યાન આપવાની ટિકિટ અહીં દેખાશે.",
    showingRecent: "{total}માંથી {shown} આગળ મોકલાયેલી ટિકિટ બતાવવામાં આવી રહી છે.",
    ticket: "ટિકિટ",
    department: "વિભાગ",
    location: "સ્થળ",
    filed: "નોંધણી",
    escalationLevel: "એસ્કેલેશન સ્તર",
    loading: "આંકડા લોડ થઈ રહ્યા છે",
    errorTitle: "આંકડા લોડ થઈ શક્યા નથી",
    errorMessage: "કનેક્શન તપાસીને ફરી પ્રયાસ કરો.",
    retry: "ફરી પ્રયાસ કરો",
  },
};

export function getAnalyticsMessages(language: UiLanguage): AnalyticsMessages {
  return translations[language];
}
