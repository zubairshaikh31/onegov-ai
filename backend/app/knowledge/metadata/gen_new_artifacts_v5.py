#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate per-service artifacts ONLY for newly added services (v5 expansion).
Append-only: skips any file that already exists. Never touches existing 53 services.
Honest: unverifiable fields marked 'Verification Required'. Generated guides disclaimed."""
import json, os, datetime
from fpdf import FPDF
OUT = "C:/Users/zubai/OneGov-KnowledgeBase"
NOW = "2026-07-25T00:00:00Z"
def lj(p):
    with open(p, encoding="utf-8") as f: return json.load(f)
def sj(o,p):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(o, open(p,"w",encoding="utf-8"), ensure_ascii=False, indent=2)

services = lj(os.path.join(OUT,"json","services.json"))
new = [s for s in services if s.get("_expanded_v5")]

# minimal KG for new services
KG = {
 "SVC-CSC":["SVC-DIGILOCKER"],"SVC-BHIM":["SVC-JDY"],"SVC-DIGIYATRA":["SVC-AADHAAR"],
 "SVC-MAA":[],"SVC-AP-ESEVA":[],"SVC-TELANGANA-TS":[],"SVC-KERALA-EK":[],
 "SVC-COWIN":["SVC-AADHAAR"],"SVC-AYUSH":[],"SVC-ICDS":["SVC-POSHAN"],"SVC-POSHAN":["SVC-ICDS"],
 "SVC-SBM":[],"SVC-AMRUT":[],"SVC-PMGSY":[],"SVC-MGNREGA":["SVC-EShramCard"],
 "SVC-DAYNULM":[],"SVC-PMKVY4":["SVC-NAPS"],"SVC-DISHA":["SVC-CSC"],
 "SVC-MAH-JAL":[],"SVC-MAH-AAROGYA":["SVC-AADHAAR"],
 "SVC-PMSVM":["SVC-JDY"],"SVC-ATAL":["SVC-JDY"],"SVC-NPS":["SVC-JDY"],
 "SVC-RAIL":["SVC-AADHAAR"],"SVC-AAI":[],"SVC-PMSBY":["SVC-JDY"],
}

def ascii_(t):
    if t is None: return ""
    for k,v in {"\u2014":"-","\u2013":"-","\u2018":"'","\u2019":"'","\u201c":'"',"\u201d":'"',"\u2026":"...","\u00a0":" ","\u2192":"->","\u20b9":"Rs. "}.items():
        t=t.replace(k,v)
    return t.encode("latin-1","replace").decode("latin-1")

class PDF(FPDF):
    def header(self):
        self.set_font("Helvetica","B",11); self.cell(0,8,"OneGov AI - Citizen Guide (Unofficial)",0,1,"C"); self.ln(1)
    def footer(self):
        self.set_y(-12); self.set_font("Helvetica","I",8); self.cell(0,8,f"Page {self.page_no()} - unofficial",0,0,"C")

def gen_pdf(s, steps, docs, faqs, path):
    pdf=PDF(); pdf.add_page(); pdf.set_auto_page_break(True,15)
    W=pdf.w-pdf.l_margin-pdf.r_margin
    def mc(t,h=5):
        pdf.set_x(pdf.l_margin); pdf.multi_cell(W,h,ascii_(t))
    pdf.set_font("Helvetica","B",15); mc(s["name"],8); pdf.ln(1)
    pdf.set_font("Helvetica","I",9); mc(f"Unofficial explanatory guide from verified official info. Last updated {s.get('last_updated','N/A')}. Verify: {s.get('official_portal')}",5); pdf.ln(2)
    def sec(t,x):
        pdf.set_font("Helvetica","B",12); mc(t,6); pdf.ln(1); pdf.set_font("Helvetica","",10); mc(x or "Verification Required",5); pdf.ln(2)
    sec("Introduction",s.get("description")); sec("Eligibility",s.get("eligibility")); sec("Benefits",s.get("benefits"))
    pdf.set_font("Helvetica","B",12); mc("Documents Required",6); pdf.ln(1); pdf.set_font("Helvetica","",10)
    for d in docs: mc(f"- {d.get('name')} ({'Mandatory' if d.get('mandatory') else 'Optional'})",5)
    pdf.ln(2)
    pdf.set_font("Helvetica","B",12); mc("Application Process",6); pdf.ln(1); pdf.set_font("Helvetica","",10)
    for st in steps: mc(f"Step {st['step']}: {st['description']}",5)
    pdf.ln(2)
    sec("Fees",s.get("fees")); sec("Timeline",s.get("processing_time"))
    pdf.set_font("Helvetica","B",12); mc("FAQs",6); pdf.ln(1); pdf.set_font("Helvetica","",10)
    for f in faqs[:10]: mc(f"Q: {f['question']}"); mc(f"A: {f['answer']}"); pdf.ln(1)
    sec("Official Links", f"Website: {s.get('official_portal')}\nApply: {s.get('official_apply_link')}\nHelpline: {s.get('helpline_number')} | Email: {s.get('email')}")
    sec("Disclaimer","Unofficial explanatory guide compiled from public official sources. Not a government publication. Consult official portal for authoritative rules.")
    pdf.output(path)

for s in new:
    sid=s["service_id"]; sf=sid.lower()
    steps = s.get("application_steps",[])
    if steps and isinstance(steps[0],str): steps=[{"step":i+1,"description":st} for i,st in enumerate(steps)]
    docs=[{"name":d,"mandatory":True,"description":"","accepted_formats":"","common_mistakes":""} for d in s.get("required_documents",[])]
    kws=s.get("keywords", s.get("search_keywords",[]))
    # service.json
    if not os.path.exists(os.path.join(OUT,"services",f"{sf}.json")): sj(s, os.path.join(OUT,"services",f"{sf}.json"))
    # faq
    faqs=[{"question":f"What is {s['name']}?","answer":s.get("description",""),"official":False,"note":"Generated explanatory."}]
    for q,a in [("What is the official website?",s.get("official_portal")),("Helpline?",f"{s.get('helpline_number')} / {s.get('email')}"),
                ("Is there a fee?",s.get("fees")),("How long does it take?",s.get("processing_time"))]:
        if len(faqs)>=15: break
        faqs.append({"question":q,"answer":a or "Verification Required. Refer to official portal.","official":False,"note":"Generated."})
    if not os.path.exists(os.path.join(OUT,"faqs",f"{sf}_faq.json")): sj(faqs, os.path.join(OUT,"faqs",f"{sf}_faq.json"))
    # documents
    if not os.path.exists(os.path.join(OUT,"documents",f"{sf}_documents.json")): sj(docs, os.path.join(OUT,"documents",f"{sf}_documents.json"))
    # keywords
    if not os.path.exists(os.path.join(OUT,"keywords",f"{sf}_keywords.json")): sj({"service_id":sid,"keywords":kws,"search_keywords":kws,"aliases":kws,"synonyms":[],"common_misspellings":[],"voice_queries":[f"I want {s['name']}"],"nl_queries":[f"how to {s['name']}"]}, os.path.join(OUT,"keywords",f"{sf}_keywords.json"))
    # relationships
    rel={"service_id":sid,"prerequisite":KG.get(sid,[]),"dependent":[],"complementary":KG.get(sid,[]),"alternative":[],"chain_example":f"{sid} -> "+" -> ".join(KG.get(sid,[]))}
    if not os.path.exists(os.path.join(OUT,"relationships",f"{sf}_relationships.json")): sj(rel, os.path.join(OUT,"relationships",f"{sf}_relationships.json"))
    # videos
    if not os.path.exists(os.path.join(OUT,"videos",f"{sf}_videos.json")): sj({"service_id":sid,"videos":[{"title":f"{s['name']} - Official Info","youtube_url":"","channel":"Refer to official ministry/MeitY/NIC/PIB YouTube channel","channel_url":"","duration":"","language":"en","type":"official","department":s.get("ministry_id"),"thumbnail":"","description":f"Search official {s.get('ministry_id')} YouTube channel for {s['name']}.","verified":False,"source":"Official Government YouTube (lookup required)"}]}, os.path.join(OUT,"videos",f"{sf}_videos.json"))
    # downloads
    if not os.path.exists(os.path.join(OUT,"downloads",f"{sf}_downloads.json")): sj([{"title":f"{s['name']} - Official Forms","url":s.get("download_forms") or s.get("official_portal"),"type":"portal","source":s.get("source_url"),"retrieved":NOW,"note":"Verify on official portal."}], os.path.join(OUT,"downloads",f"{sf}_downloads.json"))
    # office
    if not os.path.exists(os.path.join(OUT,"office-locations",f"{sf}_office_locations.json")): sj([{"office_name":s.get("office_locator_info","Refer to official portal"),"address":"","district":"","state":s.get("state_id") or "India","pincode":"","latitude":"","longitude":"","google_maps_url":"","working_hours":"","phone":s.get("helpline_number"),"email":s.get("email"),"website":s.get("official_portal"),"accessibility":"Verification Required"}], os.path.join(OUT,"office-locations",f"{sf}_office_locations.json"))
    # ai
    if not os.path.exists(os.path.join(OUT,"ai",f"{sf}_ai.json")): sj({"service_id":sid,"ai_summary":s.get("ai_summary"),"ai_explanation":s.get("ai_explanation"),"eligibility_summary":s.get("eligibility"),"conversation_examples":[{"user":f"I want {s['name']}","bot":f"{s.get('ai_summary','')} Apply: {s.get('official_apply_link')}. Helpline: {s.get('helpline_number')}."}],"prompt_template":f"You are OneGov AI helping with {s['name']}. Use only {s.get('official_portal')}.","follow_up_questions":[f"What documents for {s['name']}?",f"How long for {s['name']}?"],"intent_examples":[f"apply_{sf}",f"status_{sf}"],"recommended_services":KG.get(sid,[]),"document_suggestions":[d["name"] for d in docs if d["mandatory"]],"suggested_responses":[f"Visit {s.get('official_portal')}",f"Call {s.get('helpline_number')}"],"recommendation_weight":1.0}, os.path.join(OUT,"ai",f"{sf}_ai.json"))
    # translations EN/HI/MR (HI/MR label-translated names only)
    HI={"SVC-CSC":"सीएससी (कॉमन सर्विस सेंटर)","SVC-BHIM":"भीम / यूपीआई","SVC-DIGIYATRA":"डिजीयात्रा","SVC-COWIN":"कोविन (टीकाकरण)","SVC-MGNREGA":"मनरेगा","SVC-ATAL":"अटल पेंशन योजना","SVC-NPS":"राष्ट्रीय पेंशन प्रणाली","SVC-RAIL":"आईआरसीटीसी / रेलवे","SVC-SBM":"स्वच्छ भारत मिशन","SVC-POSHAN":"पोषण अभियान","SVC-ICDS":"आंगनवाडी / आईसीडीएस","SVC-DISHA":"दीक्षा / सीएससी 2.0"}
    MR={"SVC-CSC":"सीएससी (कॉमन सर्व्हिस सेंटर)","SVC-BHIM":"भीम / यूपीआय","SVC-DIGIYATRA":"डिजीयात्रा","SVC-COWIN":"कोविन (लसीकरण)","SVC-MGNREGA":"मनरेगा","SVC-ATAL":"अटल पेन्शन योजना","SVC-NPS":"राष्ट्रीय पेन्शन व्यवस्था","SVC-RAIL":"आयआरसीटीसी / रेल्वे","SVC-SBM":"स्वच्छ भारत अभियान","SVC-POSHAN":"पोषण अभियान","SVC-ICDS":"अंगणवाडी / आयसीडीएस","SVC-DISHA":"दीक्षा / सीएससी २.०"}
    if not os.path.exists(os.path.join(OUT,"multilingual","english",f"{sf}_en.json")): sj({"name":s["name"],"description":s.get("description"),"benefits":s.get("benefits"),"eligibility":s.get("eligibility"),"documents":[d["name"] for d in docs],"steps":[st["description"] for st in steps],"faqs":[f["question"] for f in faqs[:5]],"keywords":kws}, os.path.join(OUT,"multilingual","english",f"{sf}_en.json"))
    if not os.path.exists(os.path.join(OUT,"multilingual","hindi",f"{sf}_hi.json")): sj({"name":HI.get(sid,s["name"]),"description":s.get("description"),"benefits":s.get("benefits"),"eligibility":s.get("eligibility"),"documents":s.get("required_documents",[]),"steps":[st["description"] for st in steps],"faqs":[],"keywords":kws}, os.path.join(OUT,"multilingual","hindi",f"{sf}_hi.json"))
    if not os.path.exists(os.path.join(OUT,"multilingual","marathi",f"{sf}_mr.json")): sj({"name":MR.get(sid,s["name"]),"description":s.get("description"),"benefits":s.get("benefits"),"eligibility":s.get("eligibility"),"documents":s.get("required_documents",[]),"steps":[st["description"] for st in steps],"faqs":[],"keywords":kws}, os.path.join(OUT,"multilingual","marathi",f"{sf}_mr.json"))
    # tutorial.json + guides
    if not os.path.exists(os.path.join(OUT,"tutorials",f"{sf}_tutorial.json")): sj({"service_id":sid,"guide_md":f"tutorials/md/{sf}_guide.md","guide_html":f"tutorials/html/{sf}_guide.html","guide_pdf":f"tutorials/pdf/{sf}_guide.pdf","disclaimer":"Unofficial explanatory guide.","last_updated":s.get("last_updated"),"official_sources":[s.get("official_portal")]}, os.path.join(OUT,"tutorials",f"{sf}_tutorial.json"))
    md=f"# {s['name']} — Citizen Guide (Unofficial Explanatory)\n\n> _Compiled from verified official information from {s.get('official_portal')}. Last updated {s.get('last_updated','N/A')}._\n\n## Introduction\n{s.get('description','')}\n\n## Eligibility\n{s.get('eligibility','')}\n\n## Benefits\n{s.get('benefits','')}\n\n## Documents\n"+"\n".join(f"- {d['name']}" for d in docs)+f"\n\n## Process\n"+"\n".join(f"{st['step']}. {st['description']}" for st in steps)+f"\n\n## Fees\n{s.get('fees','Verification Required')}\n\n## Timeline\n{s.get('processing_time','Verification Required')}\n\n## Official Links\n- Website: {s.get('official_portal')}\n- Apply: {s.get('official_apply_link')}\n- Helpline: {s.get('helpline_number')}\n\n## Disclaimer\nUnofficial explanatory guide from public official sources. Not a government publication.\n"
    if not os.path.exists(os.path.join(OUT,"tutorials","md",f"{sf}_guide.md")): open(os.path.join(OUT,"tutorials","md",f"{sf}_guide.md"),"w",encoding="utf-8").write(md)
    if not os.path.exists(os.path.join(OUT,"tutorials","html",f"{sf}_guide.html")): open(os.path.join(OUT,"tutorials","html",f"{sf}_guide.html"),"w",encoding="utf-8").write(f"<html><head><meta charset='utf-8'><title>{s['name']}</title></head><body><h1>{s['name']} (Unofficial)</h1><p>{s.get('description')}</p><p>Official: {s.get('official_portal')}</p></body></html>")
    if not os.path.exists(os.path.join(OUT,"tutorials","pdf",f"{sf}_guide.pdf")): gen_pdf(s, steps, docs, faqs, os.path.join(OUT,"tutorials","pdf",f"{sf}_guide.pdf"))

print(f"Generated artifacts for {len(new)} new services.")
