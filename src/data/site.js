export const SITE = {
  name: "DPS & Co, Chartered Accountants",
  short: "DPS & Co",
  domain: "https://dpsca.in",
  phone: "+91 22 4978 5313",
  phoneAlt: "+91 99694 90502",
  email: "info@dpsca.in", // [VERIFY — masked on the live site]
  street: "1903, 19th Floor, Naman Midtown, 'A' Wing, Senapati Bapat Marg, Prabhadevi (Elphinstone Road West)",
  locality: "Mumbai",
  region: "Maharashtra",
  postal: "400013",
  founded: "2016",
  areas: ["Mumbai", "Thane", "Navi Mumbai"],
  mapsEmbed: "https://www.google.com/maps?q=Naman+Midtown,+Senapati+Bapat+Marg,+Prabhadevi,+Mumbai+400013&output=embed",
};

export const NAV = [
  ["Home", "/"],
  ["Practices", "/practices/"],
  ["Industries", "/industries/"],
  ["Resources", "/resources/"],
  ["About", "/about/"],
];

export const ORG_SCHEMA = {
  "@context": "https://schema.org",
  "@type": ["AccountingService", "LocalBusiness"],
  name: SITE.name, url: SITE.domain, telephone: SITE.phone, email: SITE.email,
  foundingDate: SITE.founded,
  address: {
    "@type": "PostalAddress", streetAddress: SITE.street,
    addressLocality: SITE.locality, addressRegion: SITE.region,
    postalCode: SITE.postal, addressCountry: "IN",
  },
  areaServed: SITE.areas,
};

export const TODAY = new Date().toISOString().slice(0, 10);
