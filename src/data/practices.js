import { ICONS } from "./icons.js";

export const PRACTICES = [
  {
    slug: "advisory", name: "Advisory", eyebrow: "Strategy & finance", icon: ICONS["trending-up"],
    title: "Advisory Services in Mumbai | DPS & Co",
    desc: "Business advisory, management consultancy, transaction support, due diligence and CFO services in Mumbai.",
    intro: "Our advisory practice supports business decisions beyond compliance — from structuring and tax efficiency within the law to transaction support and outsourced finance leadership.",
    items: [
      ["Business Advisory", "/services/business-advisory/"],
      ["Management Consultancy", ""],
      ["Tax Optimization", ""],
      ["Transaction Support", ""],
      ["Due Diligence", ""],
      ["CFO Services", "/services/business-advisory/"],
    ],
    related: [["Business Advisory", "/services/business-advisory/"], ["Company Incorporation", "/services/company-incorporation/"]],
  },
  {
    slug: "tax-regulatory", name: "Tax & Regulatory", eyebrow: "Direct & indirect tax", icon: ICONS["receipt"],
    title: "Tax & Regulatory Services in Mumbai | DPS & Co",
    desc: "Direct and indirect tax advisory, GST and income tax compliance, company law and outsourcing in Mumbai.",
    intro: "We handle the full direct and indirect tax lifecycle — advisory, planning, and routine compliance — alongside company law and outsourcing support.",
    items: [
      ["Direct Tax Advisory", "/services/income-tax-filing/"],
      ["Indirect Tax Advisory (GST)", "/services/gst-registration/"],
      ["Tax Planning", ""],
      ["Tax Compliance (GST & TDS)", "/services/gst-return-filing/"],
      ["Company Law Services", "/services/company-incorporation/"],
      ["Accounting & Outsourcing", "/services/accounting-outsourcing/"],
    ],
    related: [["GST Registration", "/services/gst-registration/"], ["Income Tax Filing", "/services/income-tax-filing/"], ["TDS Return Filing", "/services/tds-return-filing/"]],
  },
  {
    slug: "litigation", name: "Litigation Support", eyebrow: "Disputes & representation", icon: ICONS["scale"],
    title: "Tax Litigation Support in Mumbai | DPS & Co",
    desc: "Support for direct and indirect tax disputes — strategy, drafting, filing and representation — in Mumbai.",
    intro: "We support clients through tax disputes end to end: framing strategy, drafting and filing submissions, and appearing before the authorities, coordinating with counsel where matters go beyond a Chartered Accountant's scope.",
    items: [
      ["Direct Tax Litigation Support", "/services/tax-litigation/"],
      ["Indirect Tax Litigation Support", "/services/tax-litigation/"],
      ["Framing Strategy", ""],
      ["Drafting & Filing", ""],
      ["Appearance", ""],
      ["Coordinating with Counsels", ""],
    ],
    related: [["Tax Litigation Support", "/services/tax-litigation/"], ["Income Tax Filing", "/services/income-tax-filing/"]],
  },
  {
    slug: "audit-assurance", name: "Audit & Assurance", eyebrow: "Independent assurance", icon: ICONS["shield-check"],
    title: "Audit & Assurance Services in Mumbai | DPS & Co",
    desc: "Statutory and tax audit, internal audit, IFC review, inspections, compliance and stock audit in Mumbai.",
    intro: "Our assurance practice provides independent examination and review — statutory and tax audit, internal audit, and specialised reviews — each scoped to the applicable law.",
    items: [
      ["Statutory / Tax Audit", "/services/audit-assurance/"],
      ["Internal Audit", "/services/audit-assurance/"],
      ["Internal Financial Controls Review", ""],
      ["Inspections", ""],
      ["Compliance Audits", ""],
      ["Stock Audit", ""],
    ],
    related: [["Audit & Assurance", "/services/audit-assurance/"], ["Business Advisory", "/services/business-advisory/"]],
  },
];
