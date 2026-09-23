import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import pandas as pd
import requests
import io
import re
import json
import os
import uuid
import random
import time
import base64
from datetime import datetime, timezone, timedelta

st.set_page_config(
    page_title="BC Tech Ai Assistant", 
    layout="centered", 
    initial_sidebar_state="expanded"
)

# Custom Modern Chat Bubbles Styles with Full Capsule Rounded Chat Input Box
st.markdown("""
<style>
    #MainMenu, footer {visibility: hidden !important;}
    header {visibility: visible !important;}
    
    .stApp > header {background-color: transparent;}
    [data-testid="stDecoration"] {display: none !important;}
    [data-testid="stStatusWidget"] {display: none !important; visibility: hidden !important;}
    
    .block-container {padding-top: 1.5rem; max-width: 780px;}
    
    /* Full Capsule Round Shape for Chat Input Container and Box */
    [data-testid="stChatInput"] {
        border-radius: 50px !important;
        background-color: transparent !important;
    }
    
    [data-testid="stChatInput"] > div {
        border-radius: 50px !important;
        border: 1px solid #dfe1e5 !important;
        background-color: #f8f9fa !important;
        box-shadow: 0 2px 8px rgba(32,33,36,0.12) !important;
        padding-left: 10px !important;
        padding-right: 6px !important;
    }
    
    [data-testid="stChatInput"] > div:focus-within {
        box-shadow: 0 4px 12px rgba(32,33,36,0.22) !important;
        border-color: #4285F4 !important;
        background-color: #ffffff !important;
    }
    
    div[data-baseweb="input"] {
        border-radius: 50px !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    /* Target User messages to align to Right cleanly */
    [data-testid="stChatMessage"]:has(div.st-emotion-cache-1c7y2kd),
    [data-testid="stChatMessage"]:has(img[alt="user"]) {
        flex-direction: row-reverse;
        text-align: right;
    }
    
    [data-testid="stChatMessage"] {
        padding: 1.2rem;
        border-radius: 16px;
        margin-bottom: 16px;
    }
    
    /* Sidebar Recent Buttons */
    section[data-testid="stSidebar"] div[data-testid="stExpander"] .stButton>button {
        width: 100% !important;
        float: none !important;
        border-radius: 8px !important;
        padding: 8px 12px !important;
        font-size: 13px !important;
        text-align: left !important;
        justify-content: flex-start !important;
        background-color: #ffffff !important;
        border: 1px solid #dadce0 !important;
        color: #1a73e8 !important;
        font-weight: 500 !important;
        cursor: pointer !important;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        margin-bottom: 6px;
    }
    section[data-testid="stSidebar"] div[data-testid="stExpander"] .stButton>button:hover {
        background-color: #e8f0fe !important;
        border-color: #4285f4 !important;
        color: #1967d2 !important;
    }
    
    #new_chat_btn_wrap button {
        border-radius: 20px !important;
        padding: 8px 16px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        float: none !important;
        width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)

# --- BULLET-PROOF PERSISTENT STORAGE DB MANAGER ---
DB_FILE = "bctech_chat_storage.json"
PAPERS_META_FILE = "bctech_papers_store.json"
BACKUP_PAPERS_FILE = "bctech_papers_backup.json"
GAME_ROOMS_FILE = "bctech_game_rooms.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_db(db):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_papers_db():
    data = {}
    if os.path.exists(PAPERS_META_FILE):
        try:
            with open(PAPERS_META_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    
    if not data and os.path.exists(BACKUP_PAPERS_FILE):
        try:
            with open(BACKUP_PAPERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            with open(PAPERS_META_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    return data

def save_papers_db(papers_db):
    try:
        with open(PAPERS_META_FILE, "w", encoding="utf-8") as f:
            json.dump(papers_db, f, ensure_ascii=False, indent=2)
        with open(BACKUP_PAPERS_FILE, "w", encoding="utf-8") as f:
            json.dump(papers_db, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_room_store():
    if os.path.exists(GAME_ROOMS_FILE):
        try:
            with open(GAME_ROOMS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_room_store(rooms):
    try:
        with open(GAME_ROOMS_FILE, "w", encoding="utf-8") as f:
            json.dump(rooms, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

if "papers_data" not in st.session_state:
    st.session_state.papers_data = load_papers_db()
else:
    disk_papers = load_papers_db()
    if disk_papers and not st.session_state.papers_data:
        st.session_state.papers_data = disk_papers

if "game_state" not in st.session_state:
    st.session_state.game_state = "IDLE"

if "active_room_code" not in st.session_state:
    st.session_state.active_room_code = None

if "player_role" not in st.session_state:
    st.session_state.player_role = None

query_params = st.query_params
if "room_code" in query_params and query_params["room_code"] and st.session_state.game_state == "IDLE":
    r_code = query_params["room_code"].strip().upper()
    all_rooms = load_room_store()
    if r_code in all_rooms:
        st.session_state.active_room_code = r_code
        st.session_state.game_state = all_rooms[r_code].get("game_state", "PLAYING")
        if "role" in query_params:
            st.session_state.player_role = query_params["role"]

# EXPANDED 5 CATEGORIES QUESTION BANK (FULL 75+ QUESTIONS)
QUESTION_BANK = {
    "Basic Computer & Internet": {
        "pool_1": [
            {"q": "कंप्यूटर में किसी फाइल को कॉपी करने की शॉर्टकट की क्या है?", "options": ["Ctrl + C", "Ctrl + V", "Ctrl + X", "Ctrl + S"], "answer": "Ctrl + C"},
            {"q": "WWW का पूरा नाम क्या है?", "options": ["World Wide Web", "World Web Wide", "Web World Wide", "Wide World Web"], "answer": "World Wide Web"},
            {"q": "इनमें से कौन सा एक आउटपुट डिवाइस है?", "options": ["कीबोर्ड", "माउस", "मॉनिटर", "स्कैनर"], "answer": "मॉनिटर"},
            {"q": "कंप्यूटर का दिमाग किसे कहा जाता है?", "options": ["RAM", "CPU", "Hard Disk", "Monitor"], "answer": "CPU"},
            {"q": "इंटरनेट का जनक किसे कहा जाता है?", "options": ["विंट सर्फ", "बिल गेट्स", "स्टीव जॉब्स", "मार्क जुकरबर्ग"], "answer": "विंट सर्फ"},
            {"q": "ईमेल भेजने के लिए किस प्रोटोकॉल का उपयोग किया जाता है?", "options": ["FTP", "SMTP", "HTTP", "TCP"], "answer": "SMTP"},
            {"q": "एक गीगाबाइट में कितने मेगाबाइट होते हैं?", "options": ["1024 KB", "1024 MB", "512 MB", "2048 MB"], "answer": "1024 MB"},
            {"q": "कंप्यूटर में रीसायकल बिन का क्या काम है?", "options": ["फाइल डिलीट करना", "डिलीट की गई फाइलें स्टोर करना", "वायरस स्कैन करना", "इंटरनेट चलाना"], "answer": "डिलीट की गई फाइलें स्टोर करना"},
            {"q": "विंडोज किस प्रकार का सॉफ्टवेयर है?", "options": ["ऑपरेटिंग सिस्टम", "वर्ड प्रोसेसर", "एंटीवायरस", "वेब ब्राउज़र"], "answer": "ऑपरेटिंग सिस्टम"},
            {"q": "कंप्यूटर की मुख्य मेमोरी कौन सी होती है?", "options": ["CD-ROM", "Hard Disk", "RAM", "Pen Drive"], "answer": "RAM"},
            {"q": "कीबोर्ड किस प्रकार का डिवाइस है?", "options": ["इनपुट", "आउटपुट", "स्टोरेज", "प्रोसेसिंग"], "answer": "इनपुट"},
            {"q": "MS Word किस प्रकार का सॉफ्टवेयर है?", "options": ["वर्ड प्रोसेसर", "स्प्रेडशीट", "डेटाबेस", "ऑपरेटिंग सिस्टम"], "answer": "वर्ड प्रोसेसर"},
            {"q": "पहला इलेक्ट्रॉनिक कंप्यूटर कौन सा था?", "options": ["ENIAC", "UNIVAC", "ABACUS", "PARAM"], "answer": "ENIAC"},
            {"q": "पेन ड्राइव को अन्य किस नाम से जाना जाता है?", "options": ["फ्लैश ड्राइव", "हार्ड डिस्क", "फ्लॉपी डिस्क", "सीडी"], "answer": "फ्लैश ड्राइव"},
            {"q": "Google क्या है?", "options": ["सर्च इंजन", "वेब ब्राउज़र", "ऑपरेटिंग सिस्टम", "वायरस"], "answer": "सर्च इंजन"},
            {"q": "LAN का पूरा नाम क्या है?", "options": ["Local Area Network", "Large Area Network", "Local Array Net", "Linked Access Network"], "answer": "Local Area Network"},
            {"q": "IP Address कितने बिट का होता है (IPv4)?", "options": ["32 bit", "64 bit", "128 bit", "16 bit"], "answer": "32 bit"},
            {"q": "कंप्यूटर बूटिंग का क्या अर्थ है?", "options": ["स्टार्ट करना", "बंद करना", "रिस्टार्ट करना", "फॉर्मेट करना"], "answer": "स्टार्ट करना"},
            {"q": "MS Excel में रो और कॉलम के मिलने से क्या बनता है?", "options": ["सेल (Cell)", "टेबल", "फार्मूला", "शीट"], "answer": "सेल (Cell)"},
            {"q": "शॉर्टकट की Ctrl + V का उपयोग किसके लिए होता है?", "options": ["पेस्ट करने के लिए", "कॉपी करने के लिए", "कट करने के लिए", "सेव करने के लिए"], "answer": "पेस्ट करने के लिए"},
            {"q": "कंप्यूटर का आविष्कार किसने किया था?", "options": ["चार्ल्स बैबेज", "बिल गेट्स", "एलन ट्यूरिंग", "ब्लेस पास्कल"], "answer": "चार्ल्स बैबेज"},
            {"q": "वेबसाइट का मुख्य पेज क्या कहलाता है?", "options": ["होम पेज", "मास्टर पेज", "फर्स्ट पेज", "वेब पेज"], "answer": "होम पेज"},
            {"q": "PDF का पूरा नाम क्या है?", "options": ["Portable Document Format", "Public Document File", "Print Data Format", "Published Doc File"], "answer": "Portable Document Format"},
            {"q": "कीबोर्ड में कुल कितने फंक्शन की होती हैं?", "options": ["10", "12", "14", "16"], "answer": "12"},
            {"q": "कंप्यूटर की सबसे छोटी इकाई क्या है?", "options": ["बिट (Bit)", "बाइट (Byte)", "किलोबाईट", "मेगाबाईट"], "answer": "बिट (Bit)"}
        ],
        "pool_2": [
            {"q": "RAM का पूरा नाम क्या है?", "options": ["Random Access Memory", "Read Access Memory", "Run Active Memory", "Rapid Access Memory"], "answer": "Random Access Memory"},
            {"q": "ROM किस प्रकार की मेमोरी है?", "options": ["Non-Volatile", "Volatile", "Temporary", "Dynamic"], "answer": "Non-Volatile"},
            {"q": "कंप्यूटर की स्पीड किसमें मापी जाती है?", "options": ["Hertz (Hz)", "Bits", "Bytes", "Watts"], "answer": "Hertz (Hz)"},
            {"q": "इनमें से कौन सा इनपुट डिवाइस है?", "options": ["माउस", "प्रिंटर", "स्पीकर", "प्रोजेक्टर"], "answer": "माउस"},
            {"q": "कंप्यूटर का कौन सा भाग गणना (calculation) करता है?", "options": ["ALU", "CU", "RAM", "ROM"], "answer": "ALU"},
            {"q": "एक बाइट में कितने बिट होते हैं?", "options": ["8", "4", "16", "32"], "answer": "8"},
            {"q": "Linux क्या है?", "options": ["ऑपरेटिंग सिस्टम", "एप्लीकेशन सॉफ्टवेयर", "वेब ब्राउज़र", "वायरस"], "answer": "ऑपरेटिंग सिस्टम"},
            {"q": "USB का पूरा नाम क्या है?", "options": ["Universal Serial Bus", "United Serial Bus", "Universal System Bus", "Unicyclic Serial Bus"], "answer": "Universal Serial Bus"},
            {"q": "फाइल सेव करने की शॉर्टकट की क्या है?", "options": ["Ctrl + S", "Ctrl + P", "Ctrl + C", "Ctrl + O"], "answer": "Ctrl + S"},
            {"q": "MS PowerPoint का उपयोग किसके लिए होता है?", "options": ["प्रस्तुतीकरण (Presentation)", "डेटाबेस", "स्प्रेडशीट", "वर्ड प्रोसेसिंग"], "answer": "प्रस्तुतीकरण (Presentation)"},
            {"q": "इंटरनेट पर डेटा ट्रांसफर के लिए कौन सा प्रोटोकॉल मुख्य है?", "options": ["TCP/IP", "FTP", "SMTP", "HTTP"], "answer": "TCP/IP"},
            {"q": "वाइफाइ (WiFi) का पूरा नाम क्या है?", "options": ["Wireless Fidelity", "Wired Fidelity", "Wireless Field", "Wide Fidelity"], "answer": "Wireless Fidelity"},
            {"q": "कंप्यूटर स्क्रीन पर दिखने वाली छोटी तस्वीर क्या कहलाती है?", "options": ["आइकन (Icon)", "पिक्स", "पिक्सेल", "विंडो"], "answer": "आइकन (Icon)"},
            {"q": "टास्क मैनेजर खोलने की शॉर्टकट की क्या है?", "options": ["Ctrl + Shift + Esc", "Alt + F4", "Ctrl + Alt + Delete", "Ctrl + Esc"], "answer": "Ctrl + Shift + Esc"},
            {"q": "कम्प्यूटर में वायरस क्या होता है?", "options": ["एक हानिकारक प्रोग्राम", "हार्डवेयर खराबी", "फैन की समस्या", "इंटरनेट स्लो होना"], "answer": "एक हानिकारक प्रोग्राम"},
            {"q": "ब्लूटूथ (Bluetooth) किस तकनीक पर काम करता है?", "options": ["Radio Waves", "Infrared", "Laser", "Sound Waves"], "answer": "Radio Waves"},
            {"q": "कर्सर की बाईं ओर के अक्षर को मिटाने के लिए किस की का प्रयोग होता है?", "options": ["Backspace", "Delete", "Spacebar", "Enter"], "answer": "Backspace"},
            {"q": "कर्सर की दाईं ओर के अक्षर को मिटाने के लिए किस की का प्रयोग होता है?", "options": ["Delete", "Backspace", "Shift", "Esc"], "answer": "Delete"},
            {"q": "फायरवॉल (Firewall) का उपयोग किसके लिए किया जाता है?", "options": ["सुरक्षा (Security)", "स्पीड बढ़ाना", "कूलिंग", "चार्जिंग"], "answer": "सुरक्षा (Security)"},
            {"q": "किसी फोल्डर का नाम बदलने के लिए कौन सी की दबाई जाती है?", "options": ["F2", "F5", "F1", "F12"], "answer": "F2"},
            {"q": "ऑल सेलेक्ट करने की शॉर्टकट की क्या है?", "options": ["Ctrl + A", "Ctrl + S", "Ctrl + F", "Ctrl + P"], "answer": "Ctrl + A"},
            {"q": "कंप्यूटर सिस्टम को रीस्टार्ट करने की शॉर्टकट की क्या है?", "options": ["Ctrl + Alt + Del", "Ctrl + F4", "Alt + Tab", "Ctrl + R"], "answer": "Ctrl + Alt + Del"},
            {"q": "स्पैम (Spam) किससे संबंधित है?", "options": ["अवांछित ईमेल", "वायरस", "हार्डवेयर", "गेमिंग"], "answer": "अवांछित ईमेल"},
            {"q": "डब्ल्यूडब्ल्यूडब्ल्यू (WWW) के आविष्कारक कौन हैं?", "options": ["टिम बर्नर्स-ली", "बिल गेट्स", "स्टेव जॉब्स", "मार्क जुकरबर्ग"], "answer": "टिम बर्नर्स-ली"},
            {"q": "पहला वेब ब्राउज़र कौन सा था?", "options": ["WorldWideWeb", "Mosaic", "Internet Explorer", "Netscape"], "answer": "WorldWideWeb"}
        ],
        "pool_3": [
            {"q": "कंप्यूटर की भौतिक बनावट क्या कहलाती है?", "options": ["हार्डवेयर", "सॉफ्टवेयर", "फर्मवेयर", "ह्यूमनवेयर"], "answer": "हार्डवेयर"},
            {"q": "वेबसाइट के एड्रेस को क्या कहते हैं?", "options": ["URL", "IP", "HTML", "HTTP"], "answer": "URL"},
            {"q": "बायोस (BIOS) कहाँ स्टोर होता है?", "options": ["ROM", "RAM", "Hard Disk", "Cache"], "answer": "ROM"},
            {"q": "डेटाबेस को मैनेज करने वाले सॉफ्टवेयर को क्या कहते हैं?", "options": ["DBMS", "OS", "Compiler", "Assembler"], "answer": "DBMS"},
            {"q": "कैश मेमोरी (Cache Memory) कहाँ होती है?", "options": ["CPU और RAM के बीच", "Hard Disk में", "Monitor में", "Keyboard में"], "answer": "CPU और RAM के बीच"},
            {"q": "एक टेराबाइट (TB) कितने जीबी के बराबर होता है?", "options": ["1024 GB", "512 GB", "2048 GB", "100 GB"], "answer": "1024 GB"},
            {"q": "कंप्यूटर में बैकअप का क्या अर्थ है?", "options": ["डेटा की कॉपी सुरक्षित रखना", "सिस्टम बंद करना", "वायरस हटाना", "फॉर्मेट करना"], "answer": "डेटा की कॉपी सुरक्षित रखना"},
            {"q": "इंटरनेट ब्राउज़र में नई टैब खोलने की शॉर्टकट की क्या है?", "options": ["Ctrl + T", "Ctrl + N", "Ctrl + W", "Ctrl + Shift + N"], "answer": "Ctrl + T"},
            {"q": "प्रिंट प्रीव्यू देखने की शॉर्टकट की क्या है?", "options": ["Ctrl + F2", "Ctrl + P", "Ctrl + Shift + P", "F12"], "answer": "Ctrl + F2"},
            {"q": "फाइंड (Find) करने की शॉर्टकट की क्या है?", "options": ["Ctrl + F", "Ctrl + H", "Ctrl + S", "Ctrl + R"], "answer": "Ctrl + F"},
            {"q": "रिप्लेस (Replace) करने की शॉर्टकट की क्या है?", "options": ["Ctrl + H", "Ctrl + F", "Ctrl + R", "Ctrl + G"], "answer": "Ctrl + H"},
            {"q": "डेटा को व्यवस्थित (Sort) करने की प्रक्रिया क्या कहलाती है?", "options": ["सॉर्टिंग", "सर्चिंग", "मर्जिंग", "फिल्टरिंग"], "answer": "सॉर्टिंग"},
            {"q": "माइक्रoprocessor किस पीढ़ी (Generation) का है?", "options": ["चौथी पीढ़ी", "पहली पीढ़ी", "दूसरी पीढ़ी", "तीसरी पीढ़ी"], "answer": "चौथी पीढ़ी"},
            {"q": "प्रथम गणना यंत्र (Calculating Machine) कौन सा था?", "options": ["अबेकस (Abacus)", "कैलकुलेटर", "नेपियर बोन", "पास्कलाइन"], "answer": "अबेकस (Abacus)"},
            {"q": "कंप्यूटर बूटिंग के दौरान कौन सा प्रोग्राम चलता है?", "options": ["POST", "BIOS", "DOS", "OS"], "answer": "POST"},
            {"q": "किस मेमोरी को रीफ्रेश करने की आवश्यकता होती है?", "options": ["DRAM", "SRAM", "ROM", "Cache"], "answer": "DRAM"},
            {"q": "डॉट मैट्रिक्स किसका एक प्रकार है?", "options": ["प्रिंटर", "माउस", "स्कैनर", "कीबोर्ड"], "answer": "प्रिंटर"},
            {"q": "ऑप्टिकल डिस्क का उदाहरण कौन सा है?", "options": ["CD-ROM", "Hard Disk", "Floppy Disk", "RAM"], "answer": "CD-ROM"},
            {"q": "कंप्यूटर नेटवर्क में 'Hub' क्या है?", "options": ["नेटवर्किंग डिवाइस", "सॉफ्टवेयर", "वायरस", "केबल"], "answer": "नेटवर्किंग डिवाइस"},
            {"q": "किस पोर्ट को माउस और कीबोर्ड के लिए पारंपरिक रूप से उपयोग किया जाता था?", "options": ["PS/2 Port", "USB Port", "HDMI Port", "VGA Port"], "answer": "PS/2 Port"},
            {"q": "वेब पेज किस भाषा में लिखे जाते हैं?", "options": ["HTML", "C++", "Python", "Java"], "answer": "HTML"},
            {"q": "कंप्यूटर बन्द करने की प्रक्रिया को क्या कहते हैं?", "options": ["शट डाउन (Shut Down)", "लॉग आउट", "रीस्टार्ट", "स्लीप"], "answer": "शट डाउन (Shut Down)"},
            {"q": "जीयूआई (GUI) का पूर्ण रूप क्या है?", "options": ["Graphical User Interface", "General User Interaction", "Global User Internet", "Graphical Unified Interaction"], "answer": "Graphical User Interface"},
            {"q": "सीडी (CD) की स्टोरेज क्षमता सामान्यतः कितनी होती है?", "options": ["700 MB", "4.7 GB", "1.44 MB", "10 GB"], "answer": "700 MB"},
            {"q": "डीवीडी (DVD) की स्टोरेज क्षमता सामान्यतः कितनी होती है?", "options": ["4.7 GB", "700 MB", "500 MB", "1 TB"], "answer": "4.7 GB"}
        ]
    },
    "Graphic Designing: CorelDraw": {
        "pool_1": [
            {"q": "CorelDraw में किसी ऑब्जेक्ट को ग्रुप करने के लिए कौन सी शॉर्टकट की है?", "options": ["Ctrl + G", "Ctrl + U", "Ctrl + D", "Ctrl + F4"], "answer": "Ctrl + G"},
            {"q": "CorelDraw किस प्रकार का सॉफ्टवेयर है?", "options": ["वेक्टर ग्राफिक सॉफ्टवेयर", "रास्टर ग्राफिक सॉफ्टवेयर", "वर्ड प्रोसेसिंग", "स्प्रेडशीट"], "answer": "वेक्टर ग्राफिक सॉफ्टवेयर"},
            {"q": "CorelDraw फाइल का डिफॉल्ट एक्सटेंशन क्या होता है?", "options": [".cdr", ".psd", ".ai", ".doc"], "answer": ".cdr"},
            {"q": "किसी ऑब्जेक्ट की डुप्लीकेट कॉपी बनाने की शॉर्टकट की क्या है?", "options": ["Ctrl + C", "Ctrl + D", "Ctrl + V", "Ctrl + B"], "answer": "Ctrl + D"},
            {"q": "CorelDraw में टेक्स्ट को आर्टिस्टिक से पैराग्राफ में बदलने के लिए क्या शॉर्टकट है?", "options": ["Ctrl + F2", "Ctrl + F8", "Ctrl + F9", "Ctrl + F11"], "answer": "Ctrl + F8"},
            {"q": "दो ऑब्जेक्ट्स को वेल्ड करने का मुख्य कार्य क्या होता है?", "options": ["अलग करना", "जोड़ना", "काटना", "डिलीट करना"], "answer": "जोड़ना"},
            {"q": "CorelDraw में ज़ूम इन करने के लिए कौन सी शॉर्टकट की होती है?", "options": ["F2", "F3", "F4", "F9"], "answer": "F2"},
            {"q": "पूरे पेज को स्क्रीन पर फिट करने के लिए कौन सी की दबाई जाती है?", "options": ["F3", "F4", "F8", "F12"], "answer": "F4"},
            {"q": "CorelDraw में कलर पैलेट को ऑन या ऑफ करने के लिए कहाँ जाते हैं?", "options": ["View > Color Palette", "File > Open", "Edit > Copy", "Effects > Lens"], "answer": "View > Color Palette"},
            {"q": "पॉलीगन टूल से न्यूनतम कितनी भुजाओं का शेप बना सकते हैं?", "options": ["2", "3", "4", "5"], "answer": "3"},
            {"q": "CorelDraw में सेव करने की शॉर्टकट की क्या है?", "options": ["Ctrl + S", "Ctrl + N", "Ctrl + O", "Ctrl + P"], "answer": "Ctrl + S"},
            {"q": "इम्पोर्ट करने की शॉर्टकट की क्या है?", "options": ["Ctrl + I", "Ctrl + E", "Ctrl + C", "Ctrl + V"], "answer": "Ctrl + I"},
            {"q": "एक्सपोर्ट करने की शॉर्टकट की क्या है?", "options": ["Ctrl + E", "Ctrl + I", "Ctrl + S", "Ctrl + X"], "answer": "Ctrl + E"},
            {"q": "रेक्टेंगल ड्रा करने के लिए कौन सा शॉर्टकट की है?", "options": ["F6", "F7", "F8", "M"], "answer": "F6"},
            {"q": "सर्कल टूल की शॉर्टकट की क्या है?", "options": ["F7", "F6", "C", "E"], "answer": "F7"},
            {"q": "कर्व में बदलने की शॉर्टकट की क्या है?", "options": ["Ctrl + Q", "Ctrl + W", "Ctrl + E", "Ctrl + R"], "answer": "Ctrl + Q"},
            {"q": "ऑब्जेक्ट को अनग्रुप करने की शॉर्टकट की क्या है?", "options": ["Ctrl + U", "Ctrl + G", "Ctrl + K", "Ctrl + B"], "answer": "Ctrl + U"},
            {"q": "कंबाइन करने की शॉर्टकट की क्या है?", "options": ["Ctrl + L", "Ctrl + K", "Ctrl + G", "Ctrl + U"], "answer": "Ctrl + L"},
            {"q": "फुल स्क्रीन प्रीव्यू देखने के लिए कौन सी की दबाई जाती है?", "options": ["F9", "F3", "F4", "F2"], "answer": "F9"},
            {"q": "पेज सेटअप या ऑप्शन विंडो खोलने की शॉर्टकट की क्या है?", "options": ["Ctrl + J", "Ctrl + P", "Ctrl + T", "Ctrl + M"], "answer": "Ctrl + J"},
            {"q": "पिन्ट करने की शॉर्टकट की क्या है?", "options": ["Ctrl + P", "Ctrl + S", "Ctrl + N", "Ctrl + O"], "answer": "Ctrl + P"},
            {"q": "CorelDraw में किसी ऑब्जेक्ट को लॉक करने के लिए क्या किया जाता है?", "options": ["Right Click > Lock Object", "Ctrl + L", "Ctrl + K", "Alt + L"], "answer": "Right Click > Lock Object"},
            {"q": "फ्रीहैंड टूल का उपयोग किस लिए होता है?", "options": ["फ्री हैंड ड्राइंग के लिए", "सर्कल बनाने के लिए", "कलर भरने के लिए", "टेक्स्ट लिखने के लिए"], "answer": "फ्री हैंड ड्राइंग के लिए"},
            {"q": "CorelDraw में पेज ओरिएंटेशन कितने प्रकार के होते हैं?", "options": ["2 (Portrait & Landscape)", "3", "4", "1"], "answer": "2 (Portrait & Landscape)"},
            {"q": "किसी ऑब्जेक्ट को डिलीट करने की शॉर्टकट की क्या है?", "options": ["Delete", "Backspace", "Ctrl + D", "Alt + D"], "answer": "Delete"}
        ],
        "pool_2": [
            {"q": "CorelDraw में F12 की का उपयोग किस लिए होता है?", "options": ["Outline Pen Dialog", "Fill Dialog", "Zoom", "Grid Setup"], "answer": "Outline Pen Dialog"},
            {"q": "Shift + Page Down का उपयोग CorelDraw में क्या है?", "options": ["Send Object to Back", "Bring to Front", "Delete Object", "Group Object"], "answer": "Send Object to Back"},
            {"q": "Shift + Page Up का उपयोग CorelDraw में क्या है?", "options": ["Bring to Front", "Send to Back", "Group", "Ungroup"], "answer": "Bring to Front"},
            {"q": "CorelDraw में 'Bezier Tool' का मुख्य उपयोग क्या है?", "options": ["कस्टम वेक्टर पाथ और शेप बनाना", "कलर भरना", "टेक्स्ट लिखना", "इमेज क्रॉप करना"], "answer": "कस्टम वेक्टर पाथ और शेप बनाना"},
            {"q": "CorelDraw में 'PowerClip' का उपयोग किस लिए होता है?", "options": ["किसी ऑब्जेक्ट को दूसरे शेप के अंदर फिट करना", "छोटा करना", "कॉपी करना", "डिलीट करना"], "answer": "किसी ऑब्जेक्ट को दूसरे शेप के अंदर फिट करना"},
            {"q": "CorelDraw में 'Intersects' कमांड का क्या कार्य है?", "options": ["दो ऑब्जेक्ट्स के कॉमन हिस्से को निकालना", "जोड़ना", "काटना", "अलग करना"], "answer": "दो ऑब्जेक्ट्स के कॉमन हिस्से को निकालना"},
            {"q": "CorelDraw में ग्रिड (Grid) ऑन करने की शॉर्टकट की क्या है?", "options": ["Ctrl + Y", "Ctrl + G", "Ctrl + Shift + G", "F7"], "answer": "Ctrl + Y"},
            {"q": "CorelDraw में गाइडलाइन (Guideline) लाने के लिए कहाँ क्लिक करते हैं?", "options": ["Ruler से खींचकर", "View menu", "Edit menu", "File menu"], "answer": "Ruler से खींचकर"},
            {"q": "CorelDraw में 'Artistic Text' की विशेषता क्या है?", "options": ["स्पेशल इफेक्ट्स और डिजाइनिंग में आसानी", "लंबा पैराग्राफ लिखना", "टेबल बनाना", "कलर करना"], "answer": "स्पेशल इफेक्ट्स और डिजाइनिंग में आसानी"},
            {"q": "CorelDraw में 'Paragraph Text' किसके लिए उपयुक्त है?", "options": ["लंबे आर्टिकल और डॉक्यूमेंट", "लोगो", "सिंबल", "बटन"], "answer": "लंबे आर्टिकल और डॉक्यूमेंट"},
            {"q": "CorelDraw में 'Shape Tool' की शॉर्टकट की क्या है?", "options": ["F10", "F6", "F7", "F8"], "answer": "F10"},
            {"q": "CorelDraw में 'Pick Tool' की शॉर्टकट की क्या है?", "options": ["Spacebar", "F1", "F5", "F9"], "answer": "Spacebar"},
            {"q": "CorelDraw में 'Eraser Tool' की शॉर्टकट की क्या है?", "options": ["X", "E", "Z", "C"], "answer": "X"},
            {"q": "CorelDraw में 'Knife Tool' किस काम आता है?", "options": ["ऑब्जेक्ट को काटने के लिए", "जोड़ने के लिए", "घुमाने के लिए", "रंग भरने के लिए"], "answer": "ऑब्जेक्ट को काटने के लिए"},
            {"q": "CorelDraw में 'Zoom Tool' की शॉर्टकट की क्या है?", "options": ["Z", "F2", "F3", "H"], "answer": "Z"},
            {"q": "CorelDraw में 'Pan (Hand) Tool' की शॉर्टकट की क्या है?", "options": ["H", "Z", "P", "M"], "answer": "H"},
            {"q": "CorelDraw में किसी शेप को रोटेट करने के लिए क्या करते हैं?", "options": ["दो बार क्लिक करके हैंडल घुमाना", "डबल क्लिक", "राइट क्लिक", "ड्रैग करना"], "answer": "दो बार क्लिक करके हैंडल घुमाना"},
            {"q": "CorelDraw में 'Mirror Horizontally' का क्या असर होता है?", "options": ["ऑब्जेक्ट क्षैतिज पलटना", "ऊपर-नीचे पलटना", "बड़ा करना", "छोटा करना"], "answer": "ऑब्जेक्ट क्षैतिज पलटना"},
            {"q": "CorelDraw में 'Mirror Vertically' का क्या असर होता है?", "options": ["ऑब्जेक्ट लंबवत पलटना", "बाएं-दाएं पलटना", "घुमाना", "मिटाना"], "answer": "ऑब्जेक्ट लंबवत पलटना"},
            {"q": "CorelDraw में 'F11' की दबाने पर क्या खुलता है?", "options": ["Fountain Fill Dialog", "Outline Dialog", "Print Dialog", "Options"], "answer": "Fountain Fill Dialog"},
            {"q": "CorelDraw में 'F12' से क्या होता है?", "options": ["Outline Pen Dialog", "Fill Dialog", "Grid Setup", "Save"], "answer": "Outline Pen Dialog"},
            {"q": "CorelDraw में 'Shift + F2' का उपयोग किसके लिए होता है?", "options": ["Selected objects पर ज़ूम करना", "पूरा पेज देखना", "आउट करना", "इन करना"], "answer": "Selected objects पर ज़ूम करना"},
            {"q": "CorelDraw में 'F4' का उपयोग किसके लिए होता है?", "options": ["सभी ऑब्जेक्ट्स को स्क्रीन पर फिट करना", "ज़ूम इन", "ज़ूम आउट", "सेव"], "answer": "सभी ऑब्जेक्ट्स को स्क्रीन पर फिट करना"},
            {"q": "CorelDraw में 'F3' का उपयोग किसके लिए होता है?", "options": ["Zoom Out", "Zoom In", "Full Screen", "Exit"], "answer": "Zoom Out"},
            {"q": "CorelDraw में डिफ़ॉल्ट यूनिट क्या होती है?", "options": ["इंच (Inches)", "मिलीमीटर", "पिक्सल्स", "सेंटीमीटर"], "answer": "इंच (Inches)"}
        ],
        "pool_3": [
            {"q": "CorelDraw में 'Contour Tool' का क्या काम है?", "options": ["ऑब्जेक्ट के चारों ओर शेड या लेयर बनाना", "काटना", "वेल्ड करना", "डिलीट करना"], "answer": "ऑब्जेक्ट के चारों ओर शेड या लेयर बनाना"},
            {"q": "CorelDraw में 'Blend Tool' का उपयोग किस लिए होता है?", "options": ["दो आकृतियों को आपस में मिलाना / ट्रांजिशन बनाना", "कट करना", "रंग उड़ना", "सेव करना"], "answer": "दो आकृतियों को आपस में मिलाना / ट्रांजिशन बनाना"},
            {"q": "CorelDraw में 'Distort Tool' क्या करता है?", "options": ["शेप को विकृत या डिस्टॉर्ट करना", "सीधा करना", "कलर भरना", "लॉक करना"], "answer": "शेप को विकृत या डिस्टॉर्ट करना"},
            {"q": "CorelDraw में 'Envelope Tool' का क्या कार्य है?", "options": ["टेक्स्ट या शेप के नोड्स को फ्रेम अनुसार मोड़ना", "बंद करना", "प्रिंट करना", "बॉर्डर देना"], "answer": "टेक्स्ट या शेप के नोड्स को फ्रेम अनुसार मोड़ना"},
            {"q": "CorelDraw में 'Extrude Tool' से क्या बनता है?", "options": ["3D इफेक्ट", "2D इफेक्ट", "ट्रांसपेरेंसी", "शैडो"], "answer": "3D इफेक्ट"},
            {"q": "CorelDraw में 'Drop Shadow Tool' किस लिए है?", "options": ["छाया (Shadow) देने के लिए", "उजाला करने के लिए", "कटिंग", "ग्रुपिंग"], "answer": "छाया (Shadow) देने के लिए"},
            {"q": "CorelDraw में 'Transparency Tool' का क्या अर्थ है?", "options": ["पारदर्शिता (Transparency) देना", "रंग गाढ़ा करना", "साइज बढ़ाना", "रोटेट करना"], "answer": "पारदर्शिता (Transparency) देना"},
            {"q": "CorelDraw में 'Eyedropper Tool' से क्या करते हैं?", "options": ["कलर सैंपल कॉपी करना", "ज़ूम", "क्रॉप", "लाइन खींचना"], "answer": "कलर सैंपल कॉपी करना"},
            {"q": "CorelDraw में 'Paintbucket Tool' का क्या काम है?", "options": ["कलर फिल करना", "पेंट करना", "इरेज़ करना", "सेलेक्ट करना"], "answer": "कलर फिल करना"},
            {"q": "CorelDraw में 'Interactive Fill Tool' की शॉर्टकट की क्या है?", "options": ["G", "F", "I", "M"], "answer": "G"},
            {"q": "CorelDraw में 'Mesh Fill Tool' की शॉर्टकट की क्या है?", "options": ["M", "F", "G", "N"], "answer": "M"},
            {"q": "CorelDraw में 'Smart Fill Tool' क्या करता है?", "options": ["बंद एरिया में नया रंग भरा ऑब्जेक्ट बनाना", "डिलीट करना", "लॉक करना", "ग्रुप करना"], "answer": "बंद एरिया में नया रंग भरा ऑब्जेक्ट बनाना"},
            {"q": "CorelDraw में 'Ruler' लाने की शॉर्टकट की क्या होती है?", "options": ["Ctrl + Shift + R (या View से)", "Alt + R", "F1", "F2"], "answer": "Ctrl + Shift + R (या View से)"},
            {"q": "CorelDraw में 'Dockers' पैनल खोलने के लिए शॉर्टकट क्या है?", "options": ["Ctrl + F7", "Ctrl + F3", "Ctrl + F8", "Ctrl + F2"], "answer": "Ctrl + F3"},
            {"q": "CorelDraw में 'Object Manager' डॉकर की शॉर्टकट की क्या है?", "options": ["Ctrl + F7", "Ctrl + F2", "Ctrl + F5", "Ctrl + F9"], "answer": "Ctrl + F7"},
            {"q": "CorelDraw में 'Symbol Manager' की शॉर्टकट की क्या है?", "options": ["Ctrl + F3", "Ctrl + F11", "Ctrl + F9", "Ctrl + F6"], "answer": "Ctrl + F11"},
            {"q": "CorelDraw में 'Transformation' डॉकर की शॉर्टकट की क्या है?", "options": ["Alt + F7", "Ctrl + F7", "Alt + F9", "Ctrl + F5"], "answer": "Alt + F7"},
            {"q": "CorelDraw में 'Align and Distribute' विंडो की शॉर्टकट की क्या है?", "options": ["Ctrl + E", "Ctrl + A", "Ctrl + L", "Ctrl + C"], "answer": "Ctrl + E"},
            {"q": "CorelDraw में किसी ऑब्जेक्ट को लेफ्ट एलाइन करने की शॉर्टकट की क्या है?", "options": ["L", "R", "T", "B"], "answer": "L"},
            {"q": "CorelDraw में किसी ऑब्जेक्ट को राइट एलाइन करने की शॉर्टकट की क्या है?", "options": ["R", "L", "C", "E"], "answer": "R"},
            {"q": "CorelDraw में टॉप एलाइन करने के लिए कौन सी की दबाते हैं?", "options": ["T", "B", "L", "R"], "answer": "T"},
            {"q": "CorelDraw में बॉटम एलाइन करने के लिए कौन सी की दबाते हैं?", "options": ["B", "T", "C", "E"], "answer": "B"},
            {"q": "CorelDraw में सेंटर हॉरिजॉन्टली एलाइन करने की शॉर्टकट की क्या है?", "options": ["C", "E", "L", "R"], "answer": "C"},
            {"q": "CorelDraw में सेंटर वर्टिकली एलाइन करने की शॉर्टकट की क्या है?", "options": ["E", "C", "T", "B"], "answer": "E"},
            {"q": "CorelDraw में पेज के सेंटर में ऑब्जेक्ट लाने के लिए कौन सी की प्रेस करते हैं?", "options": ["P", "C", "E", "Z"], "answer": "P"}
        ]
    },
    "Graphic Designing: Photoshop": {
        "pool_1": [
            {"q": "Adobe Photoshop किस प्रकार का सॉफ्टवेयर है?", "options": ["रास्टर / पिक्सेल बेस्ड एडिटिंग", "वेक्टर ग्राफिक्स", "डेटाबेस", "प्रेजेंटेशन"], "answer": "रास्टर / पिक्सेल बेस्ड एडिटिंग"},
            {"q": "Photoshop फाइल का डिफ़ॉल्ट एक्सटेंशन क्या होता है?", "options": [".psd", ".cdr", ".png", ".jpg"], "answer": ".psd"},
            {"q": "नया डॉक्यूमेंट बनाने की शॉर्टकट की क्या है?", "options": ["Ctrl + N", "Ctrl + O", "Ctrl + S", "Ctrl + P"], "answer": "Ctrl + N"},
            {"q": "किसी लेयर को फ्री ट्रांसफॉर्म करने की शॉर्टकट की क्या है?", "options": ["Ctrl + T", "Ctrl + F", "Ctrl + L", "Ctrl + Shift + N"], "answer": "Ctrl + T"},
            {"q": "Photoshop में मैजिक वैंड टूल का उपयोग किसके लिए होता है?", "options": ["कलर सिलेक्शन के लिए", "ब्रश चलाने के लिए", "क्रॉप करने के लिए", "टेक्स्ट लिखने के लिए"], "answer": "कलर सिलेक्शन के लिए"},
            {"q": "इमेज को क्रॉप करने के लिए कीबोर्ड शॉर्टकट क्या है?", "options": ["C key", "M key", "V key", "B key"], "answer": "C key"},
            {"q": "सिलेक्शन को डी-सेलेक्ट करने की शॉर्टकट की क्या है?", "options": ["Ctrl + D", "Ctrl + A", "Ctrl + Shift + D", "Ctrl + Alt + S"], "answer": "Ctrl + D"},
            {"q": "फ़ोटोशॉप में ब्रश टूल की शॉर्टकट की क्या होती है?", "options": ["B", "P", "S", "E"], "answer": "B"},
            {"q": "आईड्रॉपर टूल का मुख्य कार्य क्या है?", "options": ["कलर सैंपल पिक करना", "ज़ूम करना", "इमेज घुमाना", "ब्रश का साइज बढ़ाना"], "answer": "कलर सैंपल पिक करना"},
            {"q": "क्विक हीलिंग ब्रश टूल की शॉर्टकट की क्या है?", "options": ["J", "H", "K", "L"], "answer": "J"},
            {"q": "नई लेयर बनाने की शॉर्टकट की क्या है?", "options": ["Ctrl + Shift + N", "Ctrl + N", "Ctrl + L", "Ctrl + Alt + N"], "answer": "Ctrl + Shift + N"},
            {"q": "लेयर को मर्ज करने की शॉर्टकट की क्या है?", "options": ["Ctrl + E", "Ctrl + M", "Ctrl + G", "Ctrl + Shift + E"], "answer": "Ctrl + E"},
            {"q": "फॉरग्राउंड और बैकग्राउंड कलर रीसेट करने की शॉर्टकट की क्या है?", "options": ["D", "X", "C", "S"], "answer": "D"},
            {"q": "कलर इनवर्ट करने की शॉर्टकट की क्या है?", "options": ["Ctrl + I", "Ctrl + Shift + I", "Ctrl + U", "Ctrl + B"], "answer": "Ctrl + I"},
            {"q": "लेवल विंडो खोलने की शॉर्टकट की क्या है?", "options": ["Ctrl + L", "Ctrl + M", "Ctrl + B", "Ctrl + T"], "answer": "Ctrl + L"},
            {"q": "कर्व्स विंडो खोलने की शॉर्टकट की क्या है?", "options": ["Ctrl + M", "Ctrl + L", "Ctrl + C", "Ctrl + V"], "answer": "Ctrl + M"},
            {"q": "मूव टूल की शॉर्टकट की क्या है?", "options": ["V", "M", "C", "H"], "answer": "V"},
            {"q": "लेस्सो टूल की शॉर्टकट की क्या है?", "options": ["L", "M", "W", "V"], "answer": "L"},
            {"q": "इरेज़र टूल की शॉर्टकट की क्या है?", "options": ["E", "B", "R", "S"], "answer": "E"},
            {"q": "टेक्स्ट टूल की शॉर्टकट की क्या है?", "options": ["T", "M", "V", "P"], "answer": "T"},
            {"q": "हैंड टूल की शॉर्टकट की क्या है?", "options": ["H", "Z", "V", "C"], "answer": "H"},
            {"q": "फ़ोटोशॉप में ज़ूम इन करने की शॉर्टकट की क्या है?", "options": ["Ctrl + Plus (+)", "Ctrl + Minus (-)", "Ctrl + 0", "Ctrl + T"], "answer": "Ctrl + Plus (+)"},
            {"q": "किसी लेयर की डुप्लीकेट बनाने की शॉर्टकट की क्या है?", "options": ["Ctrl + J", "Ctrl + C", "Ctrl + D", "Ctrl + V"], "answer": "Ctrl + J"},
            {"q": "हिस्टोरियल ब्रश टूल का उपयोग किस लिए होता है?", "options": ["पुराने स्टेट पर रिस्टोर करने के लिए", "कलर भरने के लिए", "क्रॉप करने के लिए", "डिलीट करने के लिए"], "answer": "पुराने स्टेट पर रिस्टोर करने के लिए"},
            {"q": "Photoshop में 'Opacity' का क्या अर्थ है?", "options": ["पारदर्शिता (Transparency)", "ब्राइटनेस", "कलर", "साइज"], "answer": "पारदर्शिता (Transparency)"}
        ],
        "pool_2": [
            {"q": "Photoshop में 'Hue/Saturation' की शॉर्टकट की क्या है?", "options": ["Ctrl + U", "Ctrl + M", "Ctrl + L", "Ctrl + B"], "answer": "Ctrl + U"},
            {"q": "Photoshop में 'Color Balance' की शॉर्टकट की क्या है?", "options": ["Ctrl + B", "Ctrl + U", "Ctrl + M", "Ctrl + I"], "answer": "Ctrl + B"},
            {"q": "Photoshop में 'Desaturate' (ब्लैक एंड व्हाइट करना) की शॉर्टकट की क्या है?", "options": ["Ctrl + Shift + U", "Ctrl + U", "Ctrl + Alt + U", "Ctrl + Shift + B"], "answer": "Ctrl + Shift + U"},
            {"q": "Photoshop में 'Quick Selection Tool' की शॉर्टकट की क्या है?", "options": ["W", "M", "L", "V"], "answer": "W"},
            {"q": "Photoshop में 'Gradient Tool' की शॉर्टकट की क्या है?", "options": ["G", "B", "P", "K"], "answer": "G"},
            {"q": "Photoshop में 'Pen Tool' की शॉर्टकट की क्या है?", "options": ["P", "B", "T", "M"], "answer": "P"},
            {"q": "Photoshop में 'Rectangle Tool' की शॉर्टकट की क्या है?", "options": ["U", "R", "M", "P"], "answer": "U"},
            {"q": "Photoshop में 'Blur Tool' का क्या काम है?", "options": ["इमेज के हिस्से को धुंधला करना", "साफ करना", "ब्राइट करना", "डार्क करना"], "answer": "इमेज के हिस्से को धुंधला करना"},
            {"q": "Photoshop में 'Sharpen Tool' क्या करता है?", "options": ["इमेज को शार्प और क्लियर करता है", "ब्लर करता है", "डिलीट करता है", "रोटेट करता है"], "answer": "इमेज को शार्प और क्लियर करता है"},
            {"q": "Photoshop में 'Smudge Tool' का क्या कार्य है?", "options": ["रंगों को आपस में रगड़ना या फैलाना", "काटना", "भरना", "मिटाना"], "answer": "रंगों को आपस में रगड़ना या फैलाना"},
            {"q": "Photoshop में 'Dodge Tool' से क्या होता है?", "options": ["इमेज का हिस्सा ब्राइट (उजला) होता है", "डार्क होता है", "ब्लर होता है", "क्रॉप होता है"], "answer": "इमेज का हिस्सा ब्राइट (उजला) होता है"},
            {"q": "Photoshop में 'Burn Tool' से क्या होता है?", "options": ["इमेज का हिस्सा डार्क (अंधेरा) होता है", "ब्राइट होता है", "बड़ा होता है", "छोटा होता है"], "answer": "इमेज का हिस्सा डार्क (अंधेरा) होता है"},
            {"q": "Photoshop में 'Sponge Tool' का क्या कार्य है?", "options": ["सैचुरेशन बढ़ाना या घटाना", "क्रॉप करना", "सेव करना", "प्रिंट करना"], "answer": "सैचुरेशन बढ़ाना या घटाना"},
            {"q": "Photoshop में 'History Panel' का क्या उपयोग है?", "options": ["पिछले किए गए स्टेप्स पर वापस जाना (Undo actions)", "सेव करना", "कलर देखना", "साइज देखना"], "answer": "पिछले किए गए स्टेप्स पर वापस जाना (Undo actions)"},
            {"q": "Photoshop में 'Actions Panel' किस लिए होता है?", "options": ["ऑटोमेटेड टास्क रिकॉर्ड और प्ले करने के लिए", "ड्राइंग के लिए", "कटिंग के लिए", "प्रिंटिंग के लिए"], "answer": "ऑटोमेटेड टास्क रिकॉर्ड और प्ले करने के लिए"},
            {"q": "Photoshop में 'Layer Mask' का मुख्य लाभ क्या है?", "options": ["नुकसान पहुँचाए बिना (Non-destructively) पिक्सल्स छिपाना", "लेयर डिलीट करना", "कलर बदलना", "साइज बढ़ाना"], "answer": "नुकसान पहुँचाए बिना (Non-destructively) पिक्सल्स छिपाना"},
            {"q": "Photoshop में 'Smart Object' की क्या खूबी है?", "options": ["ओरिजिनल क्वालिटी सुरक्षित रखना", "फाइल बड़ी करना", "कलर उड़ाना", "लॉक करना"], "answer": "ओरिजिनल क्वालिटी सुरक्षित रखना"},
            {"q": "Photoshop में 'Blending Modes' का उपयोग कहाँ होता है?", "options": ["लेयर्स को अलग-अलग तरीकों से मिलाने के लिए", "सेव करने के लिए", "क्रॉप करने के लिए", "ब्रश चलाने के लिए"], "answer": "लेयर्स को अलग-अलग तरीकों से मिलाने के लिए"},
            {"q": "Photoshop में 'Content-Aware Fill' क्या करता है?", "options": ["आसपास के पिक्सल्स के हिसाब से ऑब्जेक्ट गायब करना", "कलर भरना", "ब्राइट करना", "क्रॉप करना"], "answer": "आसपास के पिक्सल्स के हिसाब से ऑब्जेक्ट गायब करना"},
            {"q": "Photoshop में 'Spot Healing Brush' की शॉर्टकट की क्या है?", "options": ["J", "B", "S", "E"], "answer": "J"},
            {"q": "Photoshop में 'Clone Stamp Tool' की शॉर्टकट की क्या है?", "options": ["S", "C", "B", "P"], "answer": "S"},
            {"q": "Photoshop में 'Pattern Stamp Tool' किस काम आता है?", "options": ["पैटर्न पेंट करने के लिए", "सॉलिड कलर भरने के लिए", "क्रॉप करने के लिए", "इरेज़ करने के लिए"], "answer": "पैटर्न पेंट करने के लिए"},
            {"q": "Photoshop में 'Magic Eraser Tool' क्या करता है?", "options": ["एक जैसे रंग वाले पिक्सल्स को एक क्लिक में मिटाना", "पूरा पेज मिटाना", "ब्रश चलाना", "क्रॉप करना"], "answer": "एक जैसे रंग वाले पिक्सल्स को एक क्लिक में मिटाना"},
            {"q": "Photoshop में 'Background Eraser Tool' का क्या उपयोग है?", "options": ["बैकग्राउंड इरेज़ करना", "फॉरग्राउंड मिटाना", "टेक्स्ट लिखना", "सेव करना"], "answer": "बैकग्राउंड इरेज़ करना"},
            {"q": "Photoshop में 'Art History Brush' क्या करता है?", "options": ["हिस्टोरिकल स्टेट को आर्टिस्टिक स्ट्रोक से पेंट करना", "डिलीट करना", "क्रॉप", "सेव"], "answer": "हिस्टोरियल स्टेट को आर्टिस्टिक स्ट्रोक से पेंट करना"}
        ],
        "pool_3": [
            {"q": "Photoshop में 'Path Selection Tool' की शॉर्टकट की क्या है?", "options": ["A", "P", "V", "M"], "answer": "A"},
            {"q": "Photoshop में 'Direct Selection Tool' की शॉर्टकट की क्या है?", "options": ["A", "P", "S", "D"], "answer": "A"},
            {"q": "Photoshop में 'Line Tool' किस कैटेगरी में आता है?", "options": ["Shape Tools", "Brush Tools", "Selection Tools", "Crop Tools"], "answer": "Shape Tools"},
            {"q": "Photoshop में 'Custom Shape Tool' से क्या बना सकते हैं?", "options": ["प्री-मेड शेप्स और सिम्बल्स", "केवल सर्कल", "केवल लाइन", "टेक्स्ट"], "answer": "प्री-मेड शेप्स और सिम्बल्स"},
            {"q": "Photoshop में '3D Material Drop Tool' किस लिए होता है?", "options": ["3D मेटेरियल अप्लाई करना", "2D पेंटिंग", "क्रॉप", "ज़ूम"], "answer": "3D मेटेरियल अप्लाई करना"},
            {"q": "Photoshop में 'Rotate View Tool' की शॉर्टकट की क्या है?", "options": ["R", "V", "H", "Z"], "answer": "R"},
            {"q": "Photoshop में 'Slice Tool' का उपयोग कहाँ होता है?", "options": ["वेब डिज़ाइन के लिए इमेज काटने में", "प्रिंटिंग में", "वीडियो एडिटिंग में", "ऑडियो में"], "answer": "वेब डिज़ाइन के लिए इमेज काटने में"},
            {"q": "Photoshop में 'Slice Select Tool' किस काम आता है?", "options": ["कटे हुए स्लाइस को सेलेक्ट करने के लिए", "डिलीट करने के लिए", "कलर बदलने के लिए", "सेव करने के लिए"], "answer": "कटे हुए स्लाइस को सेलेक्ट करने के लिए"},
            {"q": "Photoshop में 'Notes Tool' का क्या कार्य है?", "options": ["इमेज पर नोट्स या कमेंट जोड़ना", "म्यूजिक जोड़ना", "प्रिंट करना", "शेयर करना"], "answer": "इमेज पर नोट्स या कमेंट जोड़ना"},
            {"q": "Photoshop में 'Count Tool' किस लिए होता है?", "options": ["इमेज में ऑब्जेक्ट्स की गिनती करने के लिए", "साइज मापने के लिए", "कलर गिनने के लिए", "लेयर गिनने के लिए"], "answer": "इमेज में ऑब्जेक्ट्स की गिनती करने के लिए"},
            {"q": "Photoshop में 'Rulers' ऑन/ऑफ करने की शॉर्टकट की क्या है?", "options": ["Ctrl + R", "Ctrl + U", "Ctrl + T", "Ctrl + P"], "answer": "Ctrl + R"},
            {"q": "Photoshop में 'Show/Hide Extras' की शॉर्टकट की क्या है?", "options": ["Ctrl + H", "Ctrl + F", "Ctrl + D", "Ctrl + B"], "answer": "Ctrl + H"},
            {"q": "Photoshop में 'Snap' ऑन/ऑफ करने की शॉर्टकट की क्या है?", "options": ["Ctrl + ;", "Ctrl + '", "Ctrl + R", "Ctrl + Shift + S"], "answer": "Ctrl + ;"},
            {"q": "Photoshop में 'Lock Guides' की शॉर्टकट की क्या है?", "options": ["Ctrl + Alt + ;", "Ctrl + ;", "Ctrl + L", "Ctrl + Shift + L"], "answer": "Ctrl + Alt + ;"},
            {"q": "Photoshop में 'Invert Selection' की शॉर्टकट की क्या है?", "options": ["Ctrl + Shift + I", "Ctrl + I", "Ctrl + Alt + I", "Ctrl + D"], "answer": "Ctrl + Shift + I"},
            {"q": "Photoshop में 'Feather Selection' की शॉर्टकट की क्या है?", "options": ["Shift + F6", "Ctrl + F6", "Alt + F6", "F6"], "answer": "Shift + F6"},
            {"q": "Photoshop में 'Color Range' कमांड कहाँ मिलती है?", "options": ["Select > Color Range", "Edit > Color", "View > Range", "Filter > Color"], "answer": "Select > Color Range"},
            {"q": "Photoshop में 'Refine Edge / Select and Mask' का उपयोग क्यों होता है?", "options": ["बालों और बारीक किनारों के सिलेक्शन को सुधारने के लिए", "कलर भरने के लिए", "इमेज बड़ी करने के लिए", "क्रॉप करने के लिए"], "answer": "बालों और बारीक किनारों के सिलेक्शन को सुधारने के लिए"},
            {"q": "Photoshop में 'Liquify Filter' किस काम आता है?", "options": ["इमेज के अंगों को मोड़ने, खींचने या पतला करने के लिए", "ब्लर करने के लिए", "शार्प करने के लिए", "डार्क करने के लिए"], "answer": "इमेज के अंगों को मोड़ने, खींचने या पतला करने के लिए"},
            {"q": "Photoshop में 'Vanishing Point Filter' का क्या कार्य है?", "options": ["परस्पेक्टिव प्लेन पर पेंट या क्लोन करना", "इमेज घुमाना", "क्रॉप करना", "सेव करना"], "answer": "परस्पेक्टिव प्लेन पर पेंट या क्लोन करना"},
            {"q": "Photoshop में 'Adaptive Wide Angle' फिल्टर क्या करता है?", "options": ["वाइड-एंगल लेंस की डिस्टॉर्शन ठीक करना", "क्रॉप करना", "रोटेट करना", "ब्राइट करना"], "answer": "वाइड-एंगल लेंस की डिस्टॉर्शन ठीक करना"},
            {"q": "Photoshop में 'Camera Raw Filter' का उपयोग किसके लिए होता है?", "options": ["प्रोफेशनल फोटोग्राफिक कलर करेक्शन और एडिटिंग", "टेक्स्ट लिखने के लिए", "ब्रश चलाने के लिए", "इरेज़ करने के लिए"], "answer": "प्रोफेशनल फोटोग्राफिक कलर करेक्शन और एडिटिंग"},
            {"q": "Photoshop में 'Lens Correction' फिल्टर का क्या कार्य है?", "options": ["लेंस की कमियों और विरूपण को ठीक करना", "साइज बढ़ाना", "कलर बढ़ाना", "क्रॉप करना"], "answer": "लेंस की कमियों और विरूपण को ठीक करना"},
            {"q": "Photoshop में 'Smart Sharpen' फिल्टर क्या करता है?", "options": ["बेहतर और कंट्रोलड शार्पटेनिंग देना", "ब्लर करना", "डिलीट करना", "लॉक करना"], "answer": "बेहतर और कंट्रोलड शार्पटेनिंग देना"},
            {"q": "Photoshop में 'Blur Gallery' में किस तरह के ब्लर मिलते हैं?", "options": ["Iris, Tilt-Shift, Field Blur", "केवल Gaussian", "केवल Motion", "केवल Radial"], "answer": "Iris, Tilt-Shift, Field Blur"}
        ]
    },
    "Accounting & Tally Prime": {
        "pool_1": [
            {"q": "Tally Prime में कंट्रा वाउचर की शॉर्टकट की क्या है?", "options": ["F4", "F5", "F6", "F7"], "answer": "F4"},
            {"q": "भुगतान वाउचर के लिए कौन सी फंक्शन की का उपयोग होता है?", "options": ["F4", "F5", "F6", "F7"], "answer": "F5"},
            {"q": "प्राप्ति वाउचर की शॉर्टकट की क्या है?", "options": ["F4", "F5", "F6", "F8"], "answer": "F6"},
            {"q": "Tally में कंपनी को बंद करने की शॉर्टकट की क्या है?", "options": ["Alt + F1", "Ctrl + F1", "Alt + F3", "Ctrl + Alt + C"], "answer": "Alt + F1"},
            {"q": "Tally Prime में लेजर बनाने के लिए किस शॉर्टकट का उपयोग किया जाता है?", "options": ["Gateway of Tally > Create > Ledger", "Accounts Info > Ledger", "Inventory Info > Ledger", "Display > Ledger"], "answer": "Gateway of Tally > Create > Ledger"},
            {"q": "बिक्री वाउचर की शॉर्टकट की क्या है?", "options": ["F7", "F8", "F9", "F5"], "answer": "F8"},
            {"q": "खरीद वाउचर की शॉर्टकट की क्या है?", "options": ["F7", "F8", "F9", "F4"], "answer": "F9"},
            {"q": "जर्नल वाउचर की शॉर्टकट की क्या है?", "options": ["F5", "F6", "F7", "F8"], "answer": "F7"},
            {"q": "Tally में Trial Balance देखने के लिए शॉर्टकट क्या है?", "options": ["Gateway of Tally > Balance Sheet", "Gateway of Tally > Display More Reports > Trial Balance", "F11", "F12"], "answer": "Gateway of Tally > Balance Sheet"},
            {"q": "क्रेडिट नोट की शॉर्टकट की क्या होती है?", "options": ["Alt + F6", "Ctrl + F6", "Alt + F8", "Ctrl + F8"], "answer": "Alt + F6"},
            {"q": "डेबिट नोट की शॉर्टकट की क्या होती है?", "options": ["Alt + F5", "Ctrl + F5", "Alt + F7", "Ctrl + F7"], "answer": "Alt + F5"},
            {"q": "Tally में कंपनी अल्टर करने के लिए कहाँ जाते हैं?", "options": ["Gateway of Tally > Alter", "Gateway of Tally > Company > Alter", "F3", "Alt + C"], "answer": "Gateway of Tally > Company > Alter"},
            {"q": "स्टॉक समरी देखने के लिए मुख्य मेनू में क्या चुनते हैं?", "options": ["Stock Summary", "Balance Sheet", "Profit & Loss", "Display"], "answer": "Stock Summary"},
            {"q": "Tally में फीचर्स खोलने की शॉर्टकट की क्या है?", "options": ["F11", "F12", "Alt + F1", "Ctrl + F11"], "answer": "F11"},
            {"q": "Tally में कॉन्फ़िगरेशन की शॉर्टकट की क्या है?", "options": ["F12", "F11", "Ctrl + F12", "Alt + F12"], "answer": "F12"},
            {"q": "प्रॉफिट एंड लॉस अकाउंट देखने के लिए शॉर्टकट क्या है?", "options": ["Gateway of Tally > Profit & Loss A/c", "Balance Sheet", "Trial Balance", "Display"], "answer": "Gateway of Tally > Profit & Loss A/c"},
            {"q": "नया लेजर बनाते समय ग्रुप सिलेक्ट करने के लिए लिस्ट कहाँ से आती है?", "options": ["List of Groups", "Ledger Accounts", "Primary Groups", "Inventory Info"], "answer": "List of Groups"},
            {"q": "Tally में बैंक रिकॉन्सिलेशन की शॉर्टकट की क्या है?", "options": ["F5 से बैंक रिपोर्ट में जाकर", "Alt + R", "Ctrl + R", "F12"], "answer": "F5 से बैंक रिपोर्ट में जाकर"},
            {"q": "क्विकली लेजर या वाउचर डिलीट करने की शॉर्टकट की क्या है?", "options": ["Alt + D", "Ctrl + D", "Shift + Delete", "Del"], "answer": "Alt + D"},
            {"q": "Tally Prime से बाहर आने के लिए कौन सी की दबाते हैं?", "options": ["Esc", "Alt + F4", "Ctrl + Q", "Enter"], "answer": "Esc"},
            {"q": "कैश और प्रॉफिट/लॉस अकाउंट Tally द्वारा डिफ़ॉल्ट रूप से कितने बने होते हैं?", "options": ["2", "1", "3", "4"], "answer": "2"},
            {"q": "Tally में GST रिपोर्ट देखने के लिए मुख्य रूप से कहाँ जाते हैं?", "options": ["Gateway of Tally > Display More Reports > GST Reports", "Balance Sheet", "Profit & Loss", "Accounts Info"], "answer": "Gateway of Tally > Display More Reports > GST Reports"},
            {"q": "Tally में बैकअप लेने का विकल्प कहाँ होता है?", "options": ["Gateway of Tally > Company > Back up", "F11", "F12", "Tools"], "answer": "Gateway of Tally > Company > Back up"},
            {"q": "Tally में किसी रिपोर्ट को प्रिंट करने की शॉर्टकट की क्या है?", "options": ["Alt + P", "Ctrl + P", "F12", "Ctrl + S"], "answer": "Alt + P"},
            {"q": "Tally में कंपनी रीस्टोर करने के लिए क्या चुनते हैं?", "options": ["Restore", "Backup", "Select", "Create"], "answer": "Restore"}
        ],
        "pool_2": [
            {"q": "Tally Prime में किसी वाउचर को डुप्लीकेट करने की शॉर्टकट की क्या है?", "options": ["Alt + 2", "Alt + D", "Alt + C", "Ctrl + D"], "answer": "Alt + 2"},
            {"q": "Tally Prime में किसी वाउचर को कैंसिल करने की शॉर्टकट की क्या है?", "options": ["Alt + X", "Alt + C", "Alt + V", "Ctrl + C"], "answer": "Alt + X"},
            {"q": "Tally Prime में वाउचर की प्रविष्टि के दौरान नई लेजर बनाने की शॉर्टकट की क्या है?", "options": ["Alt + C", "Ctrl + C", "Alt + N", "F3"], "answer": "Alt + C"},
            {"q": "Tally में 'Day Book' देखने के लिए शॉर्टकट क्या है?", "options": ["Display More Reports > Day Book", "Balance Sheet", "Trial Balance", "Accounts Info"], "answer": "Display More Reports > Day Book"},
            {"q": "Tally में 'Ratio Analysis' रिपोर्ट कहाँ मिलती है?", "options": ["Gateway of Tally > Ratio Analysis", "Balance Sheet", "Profit & Loss", "Display"], "answer": "Gateway of Tally > Ratio Analysis"},
            {"q": "Tally में 'Bill-wise Details' किसके लिए उपयोग होती है?", "options": ["उधार लेन-देन और बिल ट्रैकिंग (Sundry Debtors/Creditors)", "नकद बिक्री", "स्टॉक", "सैलरी"], "answer": "उधार लेन-देन और बिल ट्रैकिंग (Sundry Debtors/Creditors)"},
            {"q": "Tally Prime में 'Go To' फीचर की शॉर्टकट की क्या है?", "options": ["Alt + G", "Ctrl + G", "F12", "Alt + F1"], "answer": "Alt + G"},
            {"q": "Tally Prime में 'Switch To' फीचर की शॉर्टकट की क्या है?", "options": ["Ctrl + G", "Alt + G", "Alt + S", "Ctrl + S"], "answer": "Ctrl + G"},
            {"q": "Tally में 'Godown' या लोकेशन का फीचर किस उद्देश्य से होता है?", "options": ["गोदामवार स्टॉक प्रबंधन के लिए", "कैश प्रबंधन", "बैंक रिकॉन्सिलेशन", "जीएसटी फाइलिंग"], "answer": "गोदामवार स्टॉक प्रबंधन के लिए"},
            {"q": "Tally में 'Batch-wise Details' का उपयोग किसलिए होता है?", "options": ["मैन्युफैक्चरिंग और एक्सपायरी डेट ट्रैक करने के लिए", "कर्मचारियों के लिए", "सैलरी के लिए", "लोन के लिए"], "answer": "मैन्युफैक्चरिंग और एक्सपायरी डेट ट्रैक करने के लिए"},
            {"q": "Tally में 'Price Levels' का क्या उपयोग है?", "options": ["विभिन्न ग्राहकों के लिए अलग मूल्य सूची तय करना", "डिस्ककाउंट देना", "टैक्स लगाना", "ब्याज जोड़ना"], "answer": "विभिन्न ग्राहकों के लिए अलग मूल्य सूची तय करना"},
            {"q": "Tally में 'Cost Centres' का उपयोग किसके लिए होता है?", "options": ["लागत और आय का हिसाब रखने के लिए", "स्टॉक गिनने के लिए", "बैंक खाता जोड़ने के लिए", "बैलेंस शीट देखने के लिए"], "answer": "लागत और आय का हिसाब रखने के लिए"},
            {"q": "Tally में 'Interest Calculation' का मुख्य कार्य क्या है?", "options": ["उधार पर ब्याज की गणना करना", "छूट देना", "कमीशन जोड़ना", "जीएसटी निकालना"], "answer": "उधार पर ब्याज की गणना करना"},
            {"q": "Tally में 'Payroll' फीचर किसके लिए होता है?", "options": ["कर्मचारी वेतन और उपस्थिति (Salary & Attendance)", "बैंक लेन-देन", "स्टॉक एंट्री", "जीएसटी रिपोर्ट"], "answer": "कर्मचारी वेतन और उपस्थिति (Salary & Attendance)"},
            {"q": "Tally में 'Budgets' का क्या उपयोग है?", "options": ["वित्तीय नियंत्रण और योजना बनाने के लिए", "बिल बनाने के लिए", "टैक्स चुकाने के लिए", "खाता बंद करने के लिए"], "answer": "वित्तीय नियंत्रण और योजना बनाने के लिए"},
            {"q": "Tally में 'Order Processing' में कौन से ऑर्डर शामिल हैं?", "options": ["Purchase & Sales Order", "Receipt & Payment", "Contra & Journal", "Debit & Credit Note"], "answer": "Purchase & Sales Order"},
            {"q": "Tally में 'Debit Note' वाउचर का उपयोग कब होता है?", "options": ["खरीद वापस करने पर (Purchase Return)", "बिक्री वापसी", "नकद प्राप्ति", "भुगतान"], "answer": "खरीद वापस करने पर (Purchase Return)"},
            {"q": "Tally में 'Credit Note' वाउचर का उपयोग कब होता है?", "options": ["बिका हुआ माल वापस मिलने पर (Sales Return)", "खरीद वापसी", "खर्च", "आय"], "answer": "बिका हुआ माल वापस मिलने पर (Sales Return)"},
            {"q": "Tally में 'Memorandum Voucher' किस प्रकार का वाउचर है?", "options": ["नॉन-अकाउंटिंग वाउचर (याददाश्त के लिए)", "ओरिजिनल अकाउंटिंग", "कैश वाउचर", "बैंक वाउचर"], "answer": "नॉन-अकाउंटिंग वाउचर (याददाश्त के लिए)"},
            {"q": "Tally में 'Reversing Journal' वाउचर का उपयोग किसके लिए होता है?", "options": ["एंटीसिपेटेड एन्ट्रीज और एडजस्टमेंट के लिए", "दैनिक बिक्री", "स्टॉक एंट्री", "सैलरी"], "answer": "एंटीसिपेटेड एन्ट्रीज और एडजस्टमेंट के लिए"},
            {"q": "Tally Prime में कंपनी का डेटा किस फोल्डर में मुख्य रूप से स्टोर होता है?", "options": ["Data Folder", "System 32", "Program Files", "Temp Folder"], "answer": "Data Folder"},
            {"q": "Tally में 'OD A/c' या 'Bank Overdraft' किस ग्रुप में आता है?", "options": ["Loans (Liability)", "Current Assets", "Capital A/c", "Direct Expenses"], "answer": "Loans (Liability)"},
            {"q": "Tally में 'Outstanding' रिपोर्ट क्या दर्शाती है?", "options": ["बकाया लेन-देन (लेनदार और देनदार)", "कुल संपत्ति", "शुद्ध लाभ", "स्टॉक मूल्य"], "answer": "बकाया लेन-देन (लेनदार और देनदार)"},
            {"q": "Tally में 'Cash Flow' स्टेटमेंट क्या दिखाता है?", "options": ["नकद का आना और जाना", "केवल लाभ", "केवल हानि", "स्टॉक की स्थिति"], "answer": "नकद का आना और जाना"},
            {"q": "Tally में 'Fund Flow' स्टेटमेंट क्या दर्शाता है?", "options": ["फंड के स्त्रोत और उपयोग", "केवल बैंक बैलेंस", "सैलरी का विवरण", "जीएसटी"], "answer": "फंड के स्त्रोत और उपयोग"}
        ],
        "pool_3": [
            {"q": "Tally Prime में 'Company Features' (F11) में मुख्य रूप से क्या सेट करते हैं?", "options": ["Accounting, Inventory & Taxation features", "Windows settings", "Printer settings", "User password"], "answer": "Accounting, Inventory & Taxation features"},
            {"q": "Tally Prime में 'Security Control' का उपयोग क्यों किया जाता है?", "options": ["पासवर्ड और यूजर एक्सेस सुरक्षित करने के लिए", "डेटा डिलीट करने के लिए", "स्पीड बढ़ाने के लिए", "बैकअप लेने के लिए"], "answer": "पासवर्ड और यूजर एक्सेस सुरक्षित करने के लिए"},
            {"q": "Tally में 'Tally Vault Password' क्या सुरक्षा देता है?", "options": ["डेटा एंक्रिप्शन और उच्च सुरक्षा", "केवल व्यू", "केवल प्रिंट", "कुछ नहीं"], "answer": "डेटा एंक्रिप्शन और उच्च सुरक्षा"},
            {"q": "Tally Prime में 'Export' करने की शॉर्टकट की क्या है?", "options": ["Alt + E", "Alt + P", "Ctrl + E", "Ctrl + P"], "answer": "Alt + E"},
            {"q": "Tally Prime में 'Import' करने का विकल्प कहाँ होता है?", "options": ["Alt + O (Import)", "Alt + I", "Ctrl + I", "F12"], "answer": "Alt + O (Import)"},
            {"q": "Tally Prime में 'E-Way Bill' जनरेट करने की सुविधा किसके साथ जुड़ी है?", "options": ["GST Compliance", "TDS", "Payroll", "Bank Reconciliation"], "answer": "GST Compliance"},
            {"q": "Tally में TDS (Tax Deducted at Source) का संबंध किससे है?", "options": ["स्रोत पर कर कटौती", "जीएसटी", "बिक्री कर", "आयात शुल्क"], "answer": "स्रोत पर कर कटौती"},
            {"q": "Tally में TCS (Tax Collected at Source) का संबंध किससे है?", "options": ["संग्रह पर कर", "वेतन", "स्टॉक", "लोन"], "answer": "संग्रह पर कर"},
            {"q": "Tally में 'GST Return' रिपोर्ट मुख्य रूप से किस फॉर्म में देखी जाती है?", "options": ["GSTR-1, GSTR-3B", "Form 16", "ITR-1", "Balance Sheet"], "answer": "GSTR-1, GSTR-3B"},
            {"q": "Tally में 'Stock Category' और 'Stock Group' में क्या अंतर है?", "options": ["Category वर्गीकरण का अतिरिक्त स्तर है", "दोनों एक हैं", "कोई अंतर नहीं", "ग्रुप केवल नाम है"], "answer": "Category वर्गीकरण का अतिरिक्त स्तर है"},
            {"q": "Tally में 'Units of Measurement' (जैसे Pcs, Kg) क्यों बनाए जाते हैं?", "options": ["स्टॉक मापने के लिए", "कैश गिनने के लिए", "लेजर के लिए", "वाउचर के लिए"], "answer": "स्टॉक मापने के लिए"},
            {"q": "Tally में 'Godown Summary' से क्या पता चलता है?", "options": ["किस गोदाम में कितना स्टॉक है", "किस बैंक में कितना पैसा है", "किस ग्राहक से कितना लेना है", "कितना प्रॉफिट है"], "answer": "किस गोदाम में कितना स्टॉक है"},
            {"q": "Tally में 'Cost Category' और 'Cost Centre' में क्या संबंध है?", "options": ["Cost Category के अंदर Cost Centre बनाए जाते हैं", "दोनों अलग सॉफ्टवेयर हैं", "कोई संबंध नहीं", "केवल नाम हैं"], "answer": "Cost Category के अंदर Cost Centre बनाए जाते हैं"},
            {"q": "Tally Prime में रिपोर्ट देखते समय किसी विशेष अवधि (Period) बदलने की शॉर्टकट की क्या है?", "options": ["Alt + F2", "F2", "Alt + F1", "Ctrl + F2"], "answer": "Alt + F2"},
            {"q": "Tally Prime में करंट डेट बदलने की शॉर्टकट की क्या है?", "options": ["F2", "Alt + F2", "F5", "F6"], "answer": "F2"},
            {"q": "Tally Prime में वाउचर की तारीख बदलने की शॉर्टकट की क्या है?", "options": ["F2", "F3", "F4", "F7"], "answer": "F2"},
            {"q": "Tally में 'Multi-Currency' का क्या उपयोग है?", "options": ["विदेशी मुद्राओं (Foreign Currency) में लेन-देन", "केवल भारतीय रुपए", "गोल्ड ट्रेडिंग", "लोन"], "answer": "विदेशी मुद्राओं (Foreign Currency) में लेन-देन"},
            {"q": "Tally में 'Check Printing' का कॉन्फ़िगरेशन कहाँ से सेट होता है?", "options": ["लेजर या वाउचर प्रिंटिंग से", "कंट्रा वाउचर", "बैलेंस शीट", "डे बुक"], "answer": "लेजर या वाउचर प्रिंटिंग से"},
            {"q": "Tally में 'Post-dated Voucher' (PDC) का क्या अर्थ है?", "options": ["भविष्य की तारीख का वाउचर", "बीता हुआ वाउचर", "रद्द वाउचर", "कैश वाउचर"], "answer": "भविष्य की तारीख का वाउचर"},
            {"q": "Tally में 'Optional Voucher' किस श्रेणी में आता है?", "options": ["मेमोरेंडम की तरह नॉन-इफेक्टिव वाउचर", "ओरिजिनल", "कैश", "बैंक"], "answer": "मेमोरेंडम की तरह नॉन-इफेक्टिव वाउचर"},
            {"q": "Tally में 'Columnar Report' का क्या अर्थ है?", "options": ["स्तंभों (Columns) के रूप में तुलनात्मक रिपोर्ट", "साधारण रिपोर्ट", "ग्राफ", "चार्ट"], "answer": "स्तंभों (Columns) के रूप में तुलनात्मक रिपोर्ट"},
            {"q": "Tally Prime का इंटरफेस पुराने Tally.ERP 9 से कैसा है?", "options": ["अधिक आधुनिक और सरल (Modern & Simplified)", "कठिन", "समान", "धीमा"], "answer": "अधिक आधुनिक और सरल (Modern & Simplified)"},
            {"q": "Tally Prime में किसी रिपोर्ट को रीफ्रेश या पुनः लोड करने के लिए क्या करते हैं?", "options": ["ऑटोमेटिक अपडेट होता है / F5", "रिस्टार्ट", "डिलीट", "कुछ नहीं"], "answer": "ऑटोमेटिक अपडेट होता है / F5"},
            {"q": "Tally में 'Statistics' रिपोर्ट क्या दिखाती है?", "options": ["कुल वाउचर और लेजर की संख्या", "प्रॉफिट", "लॉस", "स्टॉक"], "answer": "कुल वाउचर और लेजर की संख्या"},
            {"q": "Tally में 'Trial Balance' किन खातों का योग होता है?", "options": ["सभी लेजर खातों के डेबिट और क्रेडिट शेष", "केवल कैश", "केवल बैंक", "केवल सेल्स"], "answer": "सभी लेजर खातों के डेबिट और क्रेडिट शेष"}
        ]
    },
    "Web Development & Programming": {
        "pool_1": [
            {"q": "वेब पेज पर सबसे बड़ी हेडिंग दिखाने के लिए कौन सा HTML टैग उपयोग होता है?", "options": ["<h1>", "<h6>", "<head>", "<heading>"], "answer": "<h1>"},
            {"q": "CSS का पूरा नाम क्या है?", "options": ["Cascading Style Sheets", "Computer Style Sheets", "Creative Style System", "Colorful Style Sheet"], "answer": "Cascading Style Sheets"},
            {"q": "HTML दस्तावेज में लिंक बनाने के लिए किस टैग का उपयोग होता है?", "options": ["<a>", "<link>", "<href>", "<url>"], "answer": "<a>"},
            {"q": "इनमें से कौन सी एक प्रोग्रामिंग भाषा है?", "options": ["HTML", "CSS", "Python", "XML"], "answer": "Python"},
            {"q": "वेब पेज पर इमेज दिखाने के लिए किस टैग का इस्तेमाल होता है?", "options": ["<img>", "<image>", "<pic>", "<src>"], "answer": "<img>"},
            {"q": "JavaScript में किसी वेरिएबल को घोषित करने के लिए कौन सा कीवर्ड प्रयोग होता है?", "options": ["var", "let", "const", "उपरोक्त सभी (All of these)"], "answer": "उपरोक्त सभी (All of these)"},
            {"q": "HTML का नवीनतम संस्करण कौन सा है?", "options": ["HTML4", "HTML5", "HTML X", "HTML 2.0"], "answer": "HTML5"},
            {"q": "CSS में टेक्स्ट का कलर बदलने के लिए किस प्रॉपर्टी का उपयोग होता है?", "options": ["color", "text-color", "font-color", "background-color"], "answer": "color"},
            {"q": "वेबसाइट का मुख्य पृष्ठ क्या कहलाता है?", "options": ["होम पेज (Home Page)", "मास्टर पेज", "फर्स्ट पेज", "वेब पेज"], "answer": "होम पेज (Home Page)"},
            {"q": "लाइन ब्रेक देने के लिए HTML में कौन सा टैग उपयोग होता है?", "options": ["<br>", "<lb>", "<break>", "<hr>"], "answer": "<br>"},
            {"q": "HTML का पूर्ण रूप क्या है?", "options": ["Hyper Text Markup Language", "High Text Machine Language", "Hyperlinks and Text Markup", "Home Tool Markup Language"], "answer": "Hyper Text Markup Language"},
            {"q": "JavaScript किस प्रकार की भाषा है?", "options": ["स्क्रिप्टिंग भाषा (Scripting Language)", "मशीन भाषा", "असेम्बली भाषा", "डेटाबेस भाषा"], "answer": "स्क्रिप्टिंग भाषा (Scripting Language)"},
            {"q": "CSS का उपयोग किस लिए होता है?", "options": ["वेबपेज को डिज़ाइन और स्टाइल करने के लिए", "डेटा स्टोर करने के लिए", "लॉजिक लिखने के लिए", "सर्वर चलाने के लिए"], "answer": "वेबपेज को डिज़ाइन और स्टाइल करने के लिए"},
            {"q": "Python में कमेंट लिखने के लिए किस चिन्ह का उपयोग होता है?", "options": ["#", "//", "/*", "<!--"], "answer": "#"},
            {"q": "इनमें से कौन सा टैग HTML में टेबल बनाने के लिए उपयोग होता है?", "options": ["<table>", "<tab>", "<tr>", "<td>"], "answer": "<table>"},
            {"q": "वेब पेज पर बैकग्राउंड कलर बदलने के लिए CSS में किस प्रॉपर्टी का उपयोग होता है?", "options": ["background-color", "color", "bg-color", "image-color"], "answer": "background-color"},
            {"q": "Python भाषा का विकास किसने किया था?", "options": ["Guido van Rossum", "Dennis Ritchie", "James Gosling", "Bjarne Stroustrup"], "answer": "Guido van Rossum"},
            {"q": "HTML में अनऑर्डर्ड लिस्ट के लिए कौन सा टैग होता है?", "options": ["<ul>", "<ol>", "<li>", "<list>"], "answer": "<ul>"},
            {"q": "किसी एलिमेंट की आईडी को CSS में दर्शाने के लिए किस चिन्ह का प्रयोग करते हैं?", "options": ["#", ".", "*", "$"], "answer": "#"},
            {"q": "CSS क्लास को दर्शाने के लिए किस चिन्ह का प्रयोग होता है?", "options": [".", "#", "@", "&"], "answer": "."},
            {"q": "वेब ब्राउज़र का मुख्य कार्य क्या है?", "options": ["वेबपेज रेंडर और दिखाना", "कोडिंग लिखना", "वायरस बनाना", "डेटा स्टोर करना"], "answer": "वेब ब्राउज़र का मुख्य कार्य क्या है?"},
            {"q": "JavaScript में कंसोल पर प्रिंट करने के लिए क्या लिखते हैं?", "options": ["console.log()", "print()", "echo()", "printf()"], "answer": "console.log()"},
            {"q": "HTML में पैराग्राफ लिखने के लिए कौन सा टैग उपयोग होता है?", "options": ["<p>", "<para>", "<pg>", "<text>"], "answer": "<p>"},
            {"q": "CSS में बॉर्डर रेडियस का उपयोग किस लिए होता है?", "options": ["कोनों को गोल करने के लिए", "बॉर्डर का रंग बदलने के लिए", "साइज बढ़ाने के लिए", "शेडो देने के लिए"], "answer": "कोनों को गोल करने के लिए"},
            {"q": "Python में लिस्ट (List) को किस कोष्ठक से दर्शाया जाता है?", "options": ["ब्रेसिज़ { }", "ब्रैकेट्स [ ]", "पैंथेसिस ( )", "एंगेल ब्रैकेट्स < >"], "answer": "ब्रैकेट्स [ ]"}
        ],
        "pool_2": [
            {"q": "HTML में फॉर्म (Form) बनाने के लिए किस टैग का उपयोग होता है?", "options": ["<form>", "<input>", "<button>", "<fieldset>"], "answer": "<form>"},
            {"q": "HTML में इनपुट फील्ड का प्रकार तय करने के लिए किस एट्रिब्यूट का उपयोग होता है?", "options": ["type", "name", "value", "id"], "answer": "type"},
            {"q": "CSS में किसी एलिमेंट का फॉन्ट साइज बदलने की प्रॉपर्टी क्या है?", "options": ["font-size", "text-size", "size", "font-style"], "answer": "font-size"},
            {"q": "CSS में मार्जिन (Margin) और पैडिंग (Padding) में मुख्य अंतर क्या है?", "options": ["मार्जिन बाहर की जगह छोड़ता है, पैडिंग अंदर की", "दोनों अंदर की जगह छोड़ते हैं", "कोई अंतर नहीं", "पैडिंग बाहर की जगह छोड़ती है"], "answer": "मार्जिन बाहर की जगह छोड़ता है, पैडिंग अंदर की"},
            {"q": "JavaScript में ऐरे (Array) को किस कोष्ठक में लिखा जाता है?", "options": ["Square brackets [ ]", "Curly braces { }", "Parentheses ( )", "Angle brackets < >"], "answer": "Square brackets [ ]"},
            {"q": "JavaScript में ऑब्जेक्ट (Object) को किस कोष्ठक में लिखा जाता है?", "options": ["Curly braces { }", "Square brackets [ ]", "Parentheses ( )", "Angle brackets < >"], "answer": "Curly braces { }"},
            {"q": "Python में फंक्शन परिभाषित (Define) करने के लिए किस कीवर्ड का उपयोग होता है?", "options": ["def", "function", "fun", "define"], "answer": "def"},
            {"q": "Python में लूप चलाने के लिए कौन सा कीवर्ड उपयोग होता है?", "options": ["for और while", "loop और repeat", "do और until", "iterate"], "answer": "for और while"},
            {"q": "HTML5 में वीडियो जोड़ने के लिए किस टैग का उपयोग होता है?", "options": ["<video>", "<media>", "<movie>", "<play>"], "answer": "<video>"},
            {"q": "HTML5 में ऑडियो जोड़ने के लिए किस टैग का उपयोग होता है?", "options": ["<audio>", "<sound>", "<music>", "<mp3>"], "answer": "<audio>"},
            {"q": "CSS Flexbox का मुख्य उपयोग किसके लिए होता है?", "options": ["एक आयामी (1D) रेस्पॉन्सिव लेआउट बनाने के लिए", "टेक्स्ट कलर बदलने के लिए", "एनिमेशन के लिए", "डेटाबेस कनेक्ट करने के लिए"], "answer": "एक आयामी (1D) रेस्पॉन्सिव लेआउट बनाने के लिए"},
            {"q": "CSS Grid का मुख्य उपयोग किसके लिए होता है?", "options": ["द्वि-आयामी (2D) लेआउट ग्रिड बनाने के लिए", "फॉन्ट बदलने के लिए", "बॉर्डर गोल करने के लिए", "लिंक बनाने के लिए"], "answer": "द्वि-आयामी (2D) लेआउट ग्रिड बनाने के लिए"},
            {"q": "JavaScript में किसी स्ट्रिंग की लंबाई (Length) निकालने के लिए किस प्रॉपर्टी का उपयोग होता है?", "options": [".length", ".size", ".count", ".index"], "answer": ".length"},
            {"q": "JavaScript में प्रॉम्प्ट (Prompt) बॉक्स क्या काम करता है?", "options": ["यूज़र से इनपुट लेने के लिए", "अलर्ट दिखाने के लिए", "कंसोल प्रिंट करने के लिए", "एरर दिखाने के लिए"], "answer": "यूज़र से इनपुट लेने के लिए"},
            {"q": "Python में स्ट्रिंग को लोअरकेस में बदलने के लिए किस मेथड का उपयोग होता है?", "options": [".lower()", ".lowercase()", ".down()", ".small()"], "answer": ".lower()"},
            {"q": "Python में स्ट्रिंग को अपरकेस में बदलने के लिए किस मेथड का उपयोग होता है?", "options": [".upper()", ".uppercase()", ".up()", ".big()"], "answer": ".upper()"},
            {"q": "HTML में कमेंट लिखने का सही तरीका क्या है?", "options": ["<!-- comment -->", "// comment", "/* comment */", "# comment"], "answer": "<!-- comment -->"},
            {"q": "CSS में कमेंट लिखने का सही तरीका क्या है?", "options": ["/* comment */", "// comment", "<!-- comment -->", "# comment"], "answer": "/* comment */"},
            {"q": "JavaScript में सिंगल लाइन कमेंट के लिए क्या उपयोग होता है?", "options": ["// comment", "/* comment */", "<!-- comment -->", "# comment"], "answer": "// comment"},
            {"q": "Python में डिक्शनरी (Dictionary) किस फॉर्मेट में डेटा स्टोर करती है?", "options": ["Key-Value pair", "Index number", "Only values", "Only keys"], "answer": "Key-Value pair"},
            {"q": "HTML में किसी इमेज का अल्टरनेटिव टेक्स्ट दिखाने के लिए कौन सा एट्रिब्यूट होता है?", "options": ["alt", "title", "src", "href"], "answer": "alt"},
            {"q": "CSS में डिस्प्ले प्रॉपर्टी की कौन सी वैल्यू एलिमेंट को पूरी तरह छुपा देती है?", "options": ["display: none;", "visibility: hidden;", "opacity: 0;", "display: block;"], "answer": "display: none;"},
            {"q": "JavaScript में 'NaN' का क्या अर्थ है?", "options": ["Not a Number", "Not a Name", "Null and None", "Network and Node"], "answer": "Not a Number"},
            {"q": "Python में कंडीशनल स्टेटमेंट के लिए कौन से कीवर्ड्स उपयोग होते हैं?", "options": ["if, elif, else", "switch, case", "when, then", "check, otherwise"], "answer": "if, elif, else"},
            {"q": "वेब डेवलपमेंट में DOM का पूर्ण रूप क्या है?", "options": ["Document Object Model", "Data Oriented Model", "Digital Online Method", "Display Object Management"], "answer": "Document Object Model"}
        ],
        "pool_3": [
            {"q": "JavaScript में 'Strict Mode' लागू करने के लिए क्या लिखा जाता है?", "options": ["'use strict';", "'strict mode';", "use strict = true;", "enable strict;"], "answer": "'use strict';"},
            {"q": "JavaScript में एयरो फंक्शन (Arrow Function) का सिंटैक्स कैसा होता है?", "options": ["() => {}", "function() -> {}", "-> {}", "f() {}"], "answer": "() => {}"},
            {"q": "Python में किसी फाइल को पढ़ने (Read) के लिए किस मोड का उपयोग होता है?", "options": ["'r'", "'w'", "'a'", "'x'"], "answer": "'r'"},
            {"q": "Python में किसी फाइल में डेटा लिखने (Write) के लिए किस मोड का उपयोग होता है?", "options": ["'w'", "'r'", "'d'", "'read'"], "answer": "'w'"},
            {"q": "HTML5 में लोकल स्टोरेज (Local Storage) की क्या विशेषता है?", "options": ["ब्राउज़र बंद होने के बाद भी डेटा सेव रहता है", "पेज रिफ्रेश पर उड़ जाता है", "सर्वर पर सेव होता है", "केवल 1 सेकंड रहता है"], "answer": "ब्राउज़र बंद होने के बाद भी डेटा सेव रहता है"},
            {"q": "CSS में 'z-index' प्रॉपर्टी का उपयोग किसके लिए होता है?", "options": ["एलिमेंट की स्टैकिंग ऑर्डर (आगे या पीछे दिखाना) तय करने के लिए", "जूम करने के लिए", "रोटेट करने के लिए", "कलर बदलने के लिए"], "answer": "एलिमेंट की स्टैकिंग ऑर्डर (आगे या पीछे दिखाना) तय करने के लिए"},
            {"q": "JavaScript में 'JSON.stringify()' का क्या कार्य है?", "options": ["JavaScript ऑब्जेक्ट को JSON स्ट्रिंग में बदलना", "JSON को ऑब्जेक्ट में बदलना", "कंसोल प्रिंट करना", "एरर दूर करना"], "answer": "JavaScript ऑब्जेक्ट को JSON स्ट्रिंग में बदलना"},
            {"q": "JavaScript में 'JSON.parse()' का क्या कार्य है?", "options": ["JSON स्ट्रिंग को JavaScript ऑब्जेक्ट में बदलना", "ऑब्जेक्ट को स्ट्रिंग में बदलना", "पर्स्ड करना", "डिलीट करना"], "answer": "JSON स्ट्रिंग को JavaScript ऑब्जेक्ट में बदलना"},
            {"q": "Python में 'lambda' फंक्शन क्या कहलाता है?", "options": ["गुमनाम या एनोनिमस (Anonymous) फंक्शन", "बड़ा फंक्शन", "इम्पोर्ट फंक्शन", "क्लास"], "answer": "गुमनाम या एनोनिमस (Anonymous) फंक्शन"},
            {"q": "HTML में 'Viewport' मेटा टैग का उपयोग किस लिए होता है?", "options": ["मोबाइल और विभिन्न स्क्रीन साइज के लिए रेस्पॉन्सिव बनाने हेतु", "कलर बदलने हेतु", "फास्ट लोड करने हेतु", "लिंक हेतु"], "answer": "मोबाइल और विभिन्न स्क्रीन साइज के लिए रेस्पॉन्सिव बनाने हेतु"},
            {"q": "CSS में 'Media Queries' का उपयोग किसके लिए होता है?", "options": ["अलग-अलग स्क्रीन साइज के हिसाब से डिजाइन बदलने (Responsive Design) के लिए", "वीडियो चलाने के लिए", "ऑडियो के लिए", "प्रिन्ट के लिए"], "answer": "अलग-अलग स्क्रीन साइज के हिसाब से डिजाइन बदलने (Responsive Design) के लिए"},
            {"q": "JavaScript में asynchronous operations के लिए मुख्य रूप से क्या उपयोग होता है?", "options": ["Promises और Async/Await", "Loops", "Variables", "Arrays"], "answer": "Promises और Async/Await"},
            {"q": "Python में एक्सेप्शन हैंडलिंग (Error Handling) के लिए कौन से ब्लॉक होते हैं?", "options": ["try, except, finally", "catch, throw", "error, fix", "bug, debug"], "answer": "try, except, finally"},
            {"q": "HTML में ड्रॉप-डाउन लिस्ट बनाने के लिए किस टैग का उपयोग होता है?", "options": ["<select> और <option>", "<dropdown>", "<list>", "<input type='list'>"], "answer": "<select> और <option>"},
            {"q": "CSS में 'Position: fixed;' का क्या प्रभाव होता है?", "options": ["पेज स्क्रॉल होने पर भी एलिमेंट अपनी जगह स्थिर रहता है", "गायब हो जाता है", "मूव करता है", "बड़ा होता है"], "answer": "पेज स्क्रॉल होने पर भी एलिमेंट अपनी जगह स्थिर रहता है"},
            {"q": "JavaScript में किसी एलिमेंट की क्लास जोड़ने के लिए क्या उपयोग होता है?", "options": ["element.classList.add()", "element.class.append()", "element.addClass()", "element.push()"], "answer": "element.classList.add()"},
            {"q": "Python में किसी मॉड्यूल या लाइब्रेरी को जोड़ने के लिए किस कीवर्ड का उपयोग होता है?", "options": ["import", "include", "require", "using"], "answer": "import"},
            {"q": "HTML5 में 'Semantic' टैग्स के उदाहरण कौन से हैं?", "options": ["<header>, <footer>, <article>", "<div>, <span>", "<b>, <i>", "<center>, <font>"], "answer": "<header>, <footer>, <article>"},
            {"q": "CSS में 'Transition' का उपयोग किस लिए होता है?", "options": ["प्रॉपर्टी बदलने पर स्मूथ एनिमेशन या प्रभाव देने के लिए", "पेज पलटने के लिए", "साइज फिक्स करने के लिए", "कलर उड़ाने के लिए"], "answer": "प्रॉपर्टी बदलने पर स्मूथ एनिमेशन या प्रभाव देने के लिए"},
            {"q": "JavaScript में 'setTimeout()' फंक्शन का क्या काम है?", "options": ["निर्धारित समय बाद किसी कार्य को एक बार निष्पादित करना", "लगातार लوب चलाना", "रोकना", "रिफ्रेश करना"], "answer": "निर्धारित समय बाद किसी कार्य को एक बार निष्पादित करना"},
            {"q": "Python में टुपल (Tuple) और लिस्ट (List) में मुख्य अंतर क्या है?", "options": ["टुपल बदला नहीं जा सकता (Immutable), लिस्ट बदली जा सकती है", "कोई अंतर नहीं", "लिस्ट बड़ी होती है", "टुपल में नंबर नहीं होते"], "answer": "टुपल बदला नहीं जा सकता (Immutable), लिस्ट बदली जा सकती है"},
            {"q": "HTML में किसी टेक्स्ट को बोल्ड करने के लिए <b> के अलावा कौन सा आधुनिक टैग प्रयुक्त होता है?", "options": ["<strong>", "<bld>", "<emp>", "<big>"], "answer": "<strong>"},
            {"q": "CSS में 'Rem' यूनिट किस पर आधारित होती है?", "options": ["रूट (Root/HTML) एलिमेंट के फॉन्ट साइज पर", "पेरेंट एलिमेंट पर", "स्क्रीन विड्थ पर", "पिक्सल्स पर"], "answer": "रूट (Root/HTML) एलिमेंट के फॉन्ट साइज पर"},
            {"q": "JavaScript में 'Event Listener' क्या सुनता है?", "options": ["यूज़र के एक्शंस (जैसे click, hover, keypress)", "म्यूजिक", "सर्वर की आवाज", "एरर"], "answer": "यूज़र के एक्शंस (जैसे click, hover, keypress)"},
            {"q": "Python में 'self' कीवर्ड का उपयोग कहाँ होता है?", "options": ["क्लास के इंस्टेंस (Object) को संदर्भित करने के लिए", "फंक्शन रोकने के लिए", "इम्पोर्ट के लिए", "लूप के लिए"], "answer": "क्लास के इंस्टेंस (Object) को संदर्भित करने के लिए"}
        ]
    }
}

query_params = st.query_params
if "chat_id" not in query_params or not query_params["chat_id"]:
    current_chat_id = str(uuid.uuid4())
    st.query_params["chat_id"] = current_chat_id
else:
    current_chat_id = query_params["chat_id"]

db_data = load_db()
if current_chat_id not in db_data:
    db_data[current_chat_id] = {
        "messages": [],
        "recent_chats": [],
        "current_language": "HINDI",
        "last_mentioned_name": None
    }
    save_db(db_data)

if "messages" not in st.session_state:
    st.session_state.messages = db_data[current_chat_id]["messages"]
if "recent_chats" not in st.session_state:
    st.session_state.recent_chats = db_data[current_chat_id]["recent_chats"]
if "current_language" not in st.session_state:
    st.session_state.current_language = db_data[current_chat_id]["current_language"]
if "last_mentioned_name" not in st.session_state:
    st.session_state.last_mentioned_name = db_data[current_chat_id]["last_mentioned_name"]

def persist_current_state():
    db = load_db()
    if current_chat_id not in db:
        db[current_chat_id] = {}
    db[current_chat_id]["messages"] = st.session_state.messages
    db[current_chat_id]["recent_chats"] = st.session_state.recent_chats
    db[current_chat_id]["current_language"] = st.session_state.current_language
    db[current_chat_id]["last_mentioned_name"] = st.session_state.last_mentioned_name
    save_db(db)

def remove_emojis(text):
    return re.sub(
        r'[\U00010000-\U0010ffff]|[\u2600-\u27BF]|[\uD800-\uDBFF][\uDC00-\uDFFF]|[\U0001f300-\U0001f5ff]|[\U0001f600-\U0001f64f]|[\U0001f680-\U0001f6ff]|[\u2600-\u26ff]|[\u2700-\u27bf]|[\U0001f900-\U0001f9ff]|[\U0001fa70-\U0001faff]|[\u231a-\u231b]|[\u23e9-\u23ec]|[\u23f0]|[\u23f3]|[\u25aa-\u25ab]|[\u25b6]|[\u25c0]|[\u25fb-\u25fe]|[\u2600-\u27ef]|[\u2b50]|[\u2b55]|[\u3030]|[\u303d]|[\u3297]|[\u3299]',
        '',
        text
    )

def render_voice_and_copy_toolbar(text_to_speak, unique_id, lang_code="hi-IN"):
    clean_speech_text = remove_emojis(text_to_speak)
    json_speech = json.dumps(clean_speech_text)
    json_copy = json.dumps(text_to_speak)
    
    html_toolbar = f"""
    <html>
    <head>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background: transparent;
            display: flex;
            justify-content: flex-end;
            align-items: center;
            gap: 8px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}
        .action-btn {{
            border-radius: 16px;
            padding: 3px 12px;
            font-size: 12px;
            border: 1px solid #dadce0;
            background-color: #f8f9fa;
            color: #3c4043;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            transition: all 0.2s ease;
        }}
        .action-btn:hover {{
            background-color: #e8eaed;
            color: #202124;
        }}
    </style>
    </head>
    <body>
        <button class="action-btn" id="speak_{unique_id}" onclick="toggleSpeak()">
            🔊 Read Aloud
        </button>
        <button class="action-btn" id="copy_{unique_id}" onclick="doCopy()">
            📋 Copy
        </button>
        <script>
            let utterance_{unique_id} = null;

            function toggleSpeak() {{
                const btn = document.getElementById('speak_{unique_id}');
                
                if (window.speechSynthesis.speaking) {{
                    window.speechSynthesis.cancel();
                    btn.innerHTML = '🔊 Read Aloud';
                    return;
                }}

                const text = {json_speech};
                if ('speechSynthesis' in window) {{
                    utterance_{unique_id} = new SpeechSynthesisUtterance(text);
                    utterance_{unique_id}.lang = '{lang_code}';
                    utterance_{unique_id}.rate = 0.93; 
                    utterance_{unique_id}.pitch = 1.0; 

                    const voices = window.speechSynthesis.getVoices();
                    const targetLang = '{lang_code}'.substring(0, 2);
                    
                    let bestVoice = voices.find(v => v.lang.includes(targetLang) && (v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('Microsoft')));
                    if (!bestVoice) {{
                        bestVoice = voices.find(v => v.lang.includes(targetLang));
                    }}
                    if (bestVoice) {{
                        utterance_{unique_id}.voice = bestVoice;
                    }}
                    
                    btn.innerHTML = '⏹️ Stop';
                    
                    utterance_{unique_id}.onend = function() {{
                        btn.innerHTML = '🔊 Read Aloud';
                    }};
                    utterance_{unique_id}.onerror = function() {{
                        btn.innerHTML = '🔊 Read Aloud';
                    }};
                    
                    window.speechSynthesis.speak(utterance_{unique_id});
                }} else {{
                    alert('Text-to-speech is not supported in this browser.');
                }}
            }}

            if ('speechSynthesis' in window) {{
                window.speechSynthesis.onvoiceschanged = function() {{
                    window.speechSynthesis.getVoices();
                }};
            }}

            function doCopy() {{
                const text = {json_copy};
                if (navigator.clipboard && window.isSecureContext) {{
                    navigator.clipboard.writeText(text).then(showSuccess);
                }} else {{
                    const ta = document.createElement('textarea');
                    ta.value = text;
                    ta.style.position = 'fixed';
                    ta.style.left = '-9999px';
                    document.body.appendChild(ta);
                    ta.select();
                    document.execCommand('copy');
                    document.body.removeChild(ta);
                    showSuccess();
                }}
            }}
            function showSuccess() {{
                const b = document.getElementById('copy_{unique_id}');
                b.innerHTML = '✓ Copied!';
                b.style.backgroundColor = '#e6f4ea';
                b.style.color = '#137333';
                b.style.borderColor = '#ceead6';
                setTimeout(() => {{
                    b.innerHTML = '📋 Copy';
                    b.style.backgroundColor = '#f8f9fa';
                    b.style.color = '#3c4043';
                    b.style.borderColor = '#dadce0';
                }}, 2000);
            }}
        </script>
    </body>
    </html>
    """
    components.html(html_toolbar, height=35)

def run_aerial_celebration():
    st.balloons()
    anim_js = """
    <script>
    const parentDoc = window.parent.document;
    for(let i = 0; i < 45; i++) {
        let el = parentDoc.createElement('div');
        el.innerText = ['🎆', '✨', '🏮', '🚀', '⭐', '🎉'][Math.floor(Math.random() * 6)];
        el.style.position = 'fixed';
        el.style.left = Math.random() * 95 + 'vw';
        el.style.bottom = '-50px';
        el.style.fontSize = (Math.random() * 24 + 20) + 'px';
        el.style.zIndex = '999999';
        el.style.transition = 'all ' + (Math.random() * 1.8 + 1.2) + 's cubic-bezier(0.25, 1, 0.5, 1)';
        el.style.opacity = '1';
        el.style.pointerEvents = 'none';
        parentDoc.body.appendChild(el);

        setTimeout(() => {
            el.style.bottom = (Math.random() * 55 + 40) + 'vh';
            el.style.transform = 'scale(' + (Math.random() * 1.5 + 1) + ') rotate(' + (Math.random() * 360) + 'deg)';
        }, 30);

        setTimeout(() => {
            el.style.opacity = '0';
        }, 2200);

        setTimeout(() => {
            el.remove();
        }, 3200);
    }
    </script>
    """
    components.html(anim_js, height=0)

def on_new_chat_clicked():
    if st.session_state.messages:
        user_queries = [m["content"] for m in st.session_state.messages if m["role"] == "user"]
        title_text = user_queries[-1] if user_queries else "Chat"
        short_title = (title_text[:22] + "..") if len(title_text) > 22 else title_text
        
        new_entry = {
            "title": short_title,
            "messages": list(st.session_state.messages)
        }
        st.session_state.recent_chats.insert(0, new_entry)
        st.session_state.recent_chats = st.session_state.recent_chats[:3]

    st.session_state.messages = []
    st.session_state.current_language = "HINDI"
    st.session_state.last_mentioned_name = None
    st.session_state.game_state = "IDLE"
    st.session_state.active_room_code = None
    
    new_id = str(uuid.uuid4())
    st.query_params["chat_id"] = new_id
    persist_current_state()

def restore_chat(idx):
    if idx < len(st.session_state.recent_chats):
        st.session_state.messages = list(st.session_state.recent_chats[idx]["messages"])
        st.session_state.game_state = "IDLE"
        persist_current_state()

def clean_val_display(val):
    if pd.isna(val) or str(val).strip() == "" or str(val).strip().lower() == "nan":
        return "N/A"
    try:
        f = float(val)
        if f.is_integer():
            return str(int(f))
        return str(f)
    except Exception:
        return str(val).strip()

# Sidebar - Admin Panel with Safe Paper Handling
with st.sidebar:
    st.markdown("### 🎓 BC Tech Ai Assistant")
    st.markdown('<div id="new_chat_btn_wrap">', unsafe_allow_html=True)
    if st.button("➕ New Chat", key="side_new_chat_btn", on_click=on_new_chat_clicked):
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    with st.expander("🕒 Recent (Last 3)", expanded=True):
        if st.session_state.recent_chats:
            for i, item in enumerate(st.session_state.recent_chats):
                st.button(
                    f"💬 {item['title']}", 
                    key=f"btn_restore_{i}",
                    on_click=restore_chat,
                    args=(i,)
                )
        else:
            st.caption("No recent chats yet.")

    st.markdown("---")
    st.markdown("### 🔒 Teacher / Admin Panel")
    with st.expander("📁 Upload & Manage Papers", expanded=False):
        admin_pass = st.text_input("Enter Password", type="password", key="admin_pass_input")
        if admin_pass == "bctech1AA@":
            st.success("Access Granted!")
            uploaded_file = st.file_uploader("Upload Question Paper (PDF / JPG / PNG)", type=["pdf", "jpg", "jpeg", "png"])
            
            if uploaded_file is not None:
                original_filename = uploaded_file.name
                base_name = os.path.splitext(original_filename)[0]
                st.info(f"Detected Paper Name: **{base_name}**")
                
                if st.button("Upload & Save Paper"):
                    p_key = base_name.strip().lower()
                    file_bytes = uploaded_file.getvalue()
                    encoded_file = base64.b64encode(file_bytes).decode("utf-8")
                    
                    file_ext = os.path.splitext(original_filename)[1].lower()
                    mimetype = "application/pdf" if file_ext == ".pdf" else (f"image/{file_ext[1:]}" if file_ext in [".jpg", ".jpeg", ".png"] else "application/octet-stream")

                    st.session_state.papers_data[p_key] = {
                        "display_name": base_name,
                        "filename": original_filename,
                        "data_b64": encoded_file,
                        "mime": mimetype,
                        "locked": True
                    }
                    save_papers_db(st.session_state.papers_data)
                    st.success(f"Paper '{base_name}' successfully saved permanently!")
            
            if st.session_state.papers_data:
                st.markdown("**Existing Papers Status:**")
                for pk, p_info in list(st.session_state.papers_data.items()):
                    d_name = p_info.get("display_name", pk)
                    is_locked = p_info.get("locked", True)
                    status_str = "🔒 Locked" if is_locked else "🟢 Unlocked"
                    
                    st.text(f"{d_name} ({status_str})")
                    col_t, col_d = st.columns(2)
                    
                    if col_t.button("Toggle Lock", key=f"tog_{pk}"):
                        st.session_state.papers_data[pk]["locked"] = not is_locked
                        save_papers_db(st.session_state.papers_data)
                        st.rerun()
                        
                    if col_d.button("🗑️ Delete", key=f"del_{pk}"):
                        del st.session_state.papers_data[pk]
                        save_papers_db(st.session_state.papers_data)
                        st.success(f"Deleted '{d_name}' successfully!")
                        st.rerun()
        elif admin_pass != "":
            st.error("Incorrect Password!")

    st.markdown("---")
    st.markdown("🌐 [Official Website](https://sites.google.com/view/bctechcomputer)")
    st.markdown("📍 [Branch Location](https://sites.google.com/view/bctechcomputer/about-us)")

st.title("🎓 BC Tech Ai Assistant")

SHEET_ID = "1ES2A77U61GeS710Xfyc0dKIevUhzR2v7-aSjkr1R3tg"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

@st.cache_data(ttl=15)
def load_all_sheets_data():
    try:
        res = requests.get(EXCEL_URL, timeout=15)
        if res.status_code == 200 and len(res.content) > 100:
            excel_file = io.BytesIO(res.content)
            all_dfs = pd.read_excel(excel_file, sheet_name=None)
            combined_rows = []
            
            for sheet_name, df in all_dfs.items():
                if df is not None and not df.empty and len(df.columns) >= 2:
                    cols = list(df.columns)
                    first_col = cols[0]
                    second_col = cols[1]

                    clean_df = df[df[first_col].notna()].copy()
                    clean_df = clean_df[~clean_df[first_col].astype(str).str.lower().str.contains("batch time", na=False)]
                    clean_df = clean_df[clean_df[first_col].astype(str).str.strip() != ""]
                    
                    clean_df[second_col] = clean_df[second_col].ffill()
                    
                    for _, row in clean_df.iterrows():
                        student_name = str(row[first_col]).strip()
                        name_words = sorted(student_name.lower().split())
                        name_signature = " ".join(name_words)
                        
                        raw_exam = str(row[second_col]).strip() if pd.notna(row[second_col]) else "Course"
                        exam_val = raw_exam.capitalize() if raw_exam.lower() != "nan" else "Course"
                        
                        record = {
                            "Student_Name_Std": student_name,
                            "Name_Signature_Std": name_signature,
                            "Exam_Std": exam_val,
                            "_Sheet_Tab": sheet_name
                        }
                        
                        for idx, c in enumerate(cols[2:], start=1):
                            val = row[c]
                            c_name = str(c).strip()
                            if "unnamed" in c_name.lower():
                                c_name = f"Marks_{idx}"
                            record[c_name] = clean_val_display(val)
                            
                        combined_rows.append(record)
                        
            if combined_rows:
                return pd.DataFrame(combined_rows), None
    except Exception as err:
        return None, str(err)
        
    return None, "Sheet data unavailable"

def update_language_state(text):
    text_clean = text.strip().lower()
    
    if any('\u0A80' <= ch <= '\u0AFF' for ch in text):
        st.session_state.current_language = "GUJARATI"
        return "GUJARATI"
        
    if any('\u0900' <= ch <= '\u097F' for ch in text):
        st.session_state.current_language = "HINDI"
        return "HINDI"
    
    hindi_romanized = [
        "kaise", "kaisa", "kaisi", "kaha", "kahan", "kya", "hain", "ho", "hu", "mera", 
        "meri", "karo", "batao", "bata do", "aap", "tum", "kaun", "kisne", "kyu", "kyon",
        "kab", "mein", "main", "hai", "kya hai", "kon hai", "kaha ke hai", "ka bhi", "kare", "show", "dekh", "samay", "time", "date", "tarikh", "open", "class", "batch", "chalu", "band", "timing"
    ]
    words = text_clean.split()
    
    english_indicators = ["my name is", "what is", "how are", "hello", "hi", "where is", "can you", "thank you", "result of", "timing", "batch", "class"]
    if any(ind in text_clean for ind in english_indicators) and not any(w in hindi_romanized for w in words):
        st.session_state.current_language = "ENGLISH"
        return "ENGLISH"
        
    if any(w in hindi_romanized for w in words):
        st.session_state.current_language = "HINDI"
        return "HINDI"
        
    english_common = ["name", "is", "the", "and", "you", "your", "what", "where", "how", "am", "time", "date", "open", "timing", "batch", "class"]
    if any(w in english_common for w in words) and not any(w in hindi_romanized for w in words):
        st.session_state.current_language = "ENGLISH"
        return "ENGLISH"
        
    return st.session_state.current_language

def is_greeting(text):
    text_clean = text.lower().strip().replace("!", "").replace(".", "")
    greetings = ["hi", "hello", "hey", "hii", "hiii", "namaste", "kem cho", "kem chho", "halo", "हेलो", "નમસ્ते"]
    return text_clean in greetings

def check_is_name_intro(text):
    t = text.lower().strip()
    result_intent_words = ["result", "marks", "exam", "score", "reult", "rizalt", "marksheet", "show", "kare", "ka bhi", "bhi", "dekh"]
    if any(w in t for w in result_intent_words):
        return False
        
    name_triggers = ["mera naam", "my name is", "maru naam", "hu mara naam", "naam hai", "name is", "i am", "mein hu", "hu ", "maaru naam"]
    if any(p in t for p in name_triggers) or t.startswith("naam "):
        return True
    return False

def check_is_branch_intent(text):
    text = text.lower()
    branch_keywords = [
        "branch", "address", "location", "kaha par hai", "kaha hai", "kidhar hai", 
        "kahan hai", "bctech kaha", "bc tech kaha", "ક્યાં છે", "ક્યાં આવેલું", "સરનામું", "લોકેશન", "શાખા", "पता", "कहाँ है", "लोकेशन"
    ]
    return any(kw in text for kw in branch_keywords)

def check_is_creator_intent(text):
    text = text.lower()
    creator_keywords = ["kisne banaya", "kisne bnaya", "who made you", "who created you", "aapko kisne banaya", "ko kisne banaya"]
    return any(kw in text for kw in creator_keywords)

def check_is_where_from(text):
    text = text.lower().strip()
    where_keywords = ["aap kaha se ho", "tum kaha se ho", "where are you from", "kaha se ho", "apka office kaha hai", "kaise ho", "kya हाल है"]
    return any(kw in text for kw in where_keywords)

def search_student_all_sheets(query_text, df):
    if check_is_name_intro(query_text):
        return []

    if df is None or df.empty or "Student_Name_Std" not in df.columns:
        return []
    
    clean_q = query_text.strip().lower()
    block_list = ["or", "aur", "hi", "hello", "ok", "yes", "no", "hey", "kya", "hai", "a", "an", "the"]
    if clean_q in block_list or len(clean_q) <= 2:
        return []

    if "priya mam" in clean_q or "umesh sir" in clean_q or "sanjay sir" in clean_q or "ajay sir" in clean_q:
        return []

    img_triggers = ["image", "photo", "picture", "wallpaper", "banao", "create", "generate", "tasveer", "draw", "bana do"]
    if any(t in clean_q for t in img_triggers):
        return []

    fillers = [
        "result", "marks", "marx", "kya", "hai", "check", "batao", "bata do", "mera", "meri", "ka", "ki", "ko",
        "dekho", "please", "sir", "bctech", "mujhko", "dekhna", "nam", "naam", "name",
        "show", "chhe", "che", "maru", "maro", "nu", "no", "na", "joiyu", "jovu", "aapo", "mam", "sir", "karo", "kar do", "kare", "dekh", "dikha",
        "મારું", "મારુ", "નામ", "આપો", "છે", "જોવું", "રીઝલ્ટ", "રિઝલ્ટ", "પરિણામ", "ka result", "ka marks", "hai", "my", "is", "ka bhi", "bhi"
    ]
    
    query_clean_words = [w for w in clean_q.split() if w not in fillers]
    search_query_str = " ".join(query_clean_words).strip()
    
    if not search_query_str or len(search_query_str) <= 2:
        return []

    matched = df[df["Student_Name_Std"].astype(str).str.lower().apply(lambda x: any(w == search_query_str or search_query_str in x.split() for w in x.split()))]

    if matched.empty:
        matched = df[df["Student_Name_Std"].astype(str).str.lower().str.contains(r'\b' + re.escape(search_query_str) + r'\b', na=False)]

    if matched.empty:
        matched = df[df["Student_Name_Std"].astype(str).str.lower().str.contains(re.escape(search_query_str), na=False)]

    if matched.empty:
        words = [w for w in query_clean_words if len(w) >= 2]
        if words:
            user_search_signature = " ".join(sorted(list(set(words))))
            matched = df[df["Name_Signature_Std"].astype(str) == user_search_signature]

    if not matched.empty:
        return matched.to_dict(orient="records")
    return []

def clean_ai_response(text):
    if not text:
        return ""
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    cleaned = re.sub(r"<think>.*", "", cleaned, flags=re.DOTALL)
    return cleaned.strip()

BRANCH_LINK = "https://sites.google.com/view/bctechcomputer/about-us"

KNOWLEDGE_BASE = f"""
About Bctech Computer Education:
- Institute: Bctech Computer Education
- Official Branch & Location Info Link: {BRANCH_LINK}
- Main Offerings: Professional computer training, practical learning, ISO certified courses, job assistance.
- Popular Courses (Strict Rule: NEVER mention duration in months or course fees/prices):
  1. बेसिक कंप्यूटर (Basic Computer) - Topics: Windows, MS Office, इंटरनेट
  2. ग्राफिक डिज़ाइन (Graphic Designing: CorelDraw, Photoshop, Illustrator) - Topics: लोगो डिज़ाइन, बैनर, फोटो एडिटिंग
  3. एकाउंटिंग & टैली प्राइम (Accounting & Tally Prime) - Topics: बुनियादी लेखा, टैली में लेन-देन
  4. वेब डेवलपमेंट (Web Development) - Topics: HTML, CSS, JavaScript, WordPress
  5. प्रोग्रामिंग (Programming: Python / C++) - Topics: बेसिक से एडवांस, प्रोजेक्ट वर्क
- Location/Address: Surat, Gujarat, India.
- Institute Timing (Class Open & Close Time): Class opens at 7:00 AM and remains active/open until 8:30 PM.
- Batch Timings: 
  - Morning Batches: 7:00 AM to 10:00 AM (Each batch is 1 hour long).
  - Regular/Other Batches: 10:00 AM to 8:30 PM (Each batch is 1.5 hours / 1 hour 30 minutes long).
"""

# Render chat history with Read Aloud & Copy buttons
for idx, msg in enumerate(st.session_state.messages):
    is_user = (msg["role"] == "user")
    with st.chat_message(msg["role"], avatar="👤" if is_user else "🤖"):
        st.write(msg["content"])
        if not is_user:
            lang_code = "hi-IN" if st.session_state.current_language == "HINDI" else ("gu-IN" if st.session_state.current_language == "GUJARATI" else "en-US")
            render_voice_and_copy_toolbar(msg["content"], f"hist_{idx}", lang_code)

query = st.chat_input("Ask...")

if query:
    clean_q_lower = query.strip().lower()
    lang = update_language_state(query)
    
    if "play game" in clean_q_lower or "quiz" in clean_q_lower or "game" in clean_q_lower:
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user", avatar="👤"):
            st.write(query)
        st.session_state.game_state = "CREATING"
        bot_reply = "बहुत बढ़िया! 🧠 BC Tech Brain Battle शुरू करने के लिए नीचे दिए गए Battle Zone से अपना बैटल ज़ोन बनाएं या जुड़ें।"
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(bot_reply)
        persist_current_state()
        st.rerun()

    paper_requested = None
    for pk, p_info in st.session_state.papers_data.items():
        d_name_lower = p_info.get("display_name", pk).lower()
        if d_name_lower in clean_q_lower:
            paper_requested = pk
            break

    if paper_requested:
        p_info = st.session_state.papers_data[paper_requested]
        d_name = p_info.get("display_name", paper_requested)
        is_locked = p_info.get("locked", False)

        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user", avatar="👤"):
            st.write(query)

        with st.chat_message("assistant", avatar="🤖"):
            if is_locked:
                reply = "⏳ This question paper is currently unavailable. Please ask your teacher for access."
                st.write(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
                render_voice_and_copy_toolbar(reply, f"locked_p_{len(st.session_state.messages)}", "hi-IN")
            elif "data_b64" not in p_info:
                reply = f"⚠️ The paper '{d_name}' file data is missing. Please re-upload it from the Admin panel."
                st.write(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            else:
                st.write(f"📂 Here is your requested paper: **{d_name}**")
                mtype = p_info.get("mime", "")
                try:
                    raw_bytes = base64.b64decode(p_info["data_b64"])
                    if "image/" in mtype:
                        st.image(raw_bytes, caption=d_name, use_container_width=True)
                        reply = f"Displayed large image paper: {d_name}"
                    else:
                        st.download_button(
                            label=f"📂 Open Paper: {d_name}",
                            data=raw_bytes,
                            file_name=p_info.get("filename", f"{d_name}.pdf"),
                            mime="application/pdf",
                            key=f"view_btn_{paper_requested}_{len(st.session_state.messages)}"
                        )
                        reply = f"Generated paper view button for: {d_name}"
                except Exception as e:
                    reply = f"Error loading file for {d_name}: {e}"
                    st.error(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
        persist_current_state()

    else:
        if clean_q_lower in ["or", "aur", "hi", "hello", "ok", "hey", "h", "k"]:
            st.session_state.messages.append({"role": "user", "content": query})
            with st.chat_message("user", avatar="👤"):
                st.write(query)
            with st.chat_message("assistant", avatar="🤖"):
                if lang == "HINDI":
                    reply = "हाँ, बताइए! मैं आपकी क्या मदद कर सकता हूँ? 😊"
                elif lang == "GUJARATI":
                    reply = "હા, જણાવો! હું આપને કેવી રીતે મદદ કરી શકું? 😊"
                else:
                    reply = "Yes, please tell me! How can I help you? 😊"
                st.write(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
                lang_code = "hi-IN" if lang == "HINDI" else ("gu-IN" if lang == "GUJARATI" else "en-US")
                render_voice_and_copy_toolbar(reply, f"hard_block_{len(st.session_state.messages)}", lang_code)
            persist_current_state()
        else:
            st.session_state.messages.append({"role": "user", "content": query})
            
            with st.chat_message("user", avatar="👤"):
                st.write(query)

            df_sheet, err = load_all_sheets_data()
            
            with st.chat_message("assistant", avatar="🤖"):
                if err:
                    st.error(f"Sheet Error: Google Sheet access nahi ho pa rahi ({err}).")
                
                elif check_is_name_intro(query):
                    name_match = re.search(r"(?:mera naam|my name is|maru naam|hu mara naam|naam hai|name is|i am|hu|maaru naam)\s+([a-zA-Z\u0900-\u097F]+)", query, re.IGNORECASE)
                    if not name_match:
                        words = [w for w in query.split() if w.lower() not in ["mera", "naam", "hai", "is", "my", "name", "hu", "i", "am", "ka", "ki"]]
                        username = words[0].capitalize() if words else "User"
                    else:
                        username = name_match.group(1).capitalize()
                    
                    st.session_state.last_mentioned_name = username.lower()

                    if lang == "GUJARATI":
                        reply = f"નમસ્તે {username}! BC Tech માં આપનું સ્વાગત છે. જણાવો, હું આપને કેવી રીતે મદદ કરી શકું? 😊"
                    elif lang == "HINDI":
                        reply = f"नमस्ते {username}! BC Tech Computer Education में आपका स्वागत है। बताइए, मैं आपकी कैसे मदद कर सकता हूँ? 😊"
                    else:
                        reply = f"Hello {username}! Welcome to BC Tech Computer Education. How can I help you today? 😊"
                    st.write(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    lang_code = "hi-IN" if lang == "HINDI" else ("gu-IN" if lang == "GUJARATI" else "en-US")
                    render_voice_and_copy_toolbar(reply, f"name_reply_{len(st.session_state.messages)}", lang_code)

                elif check_is_where_from(query):
                    if lang == "GUJARATI":
                        reply = "હું BC Tech Computer Education નો અસિસ્ટન્ટ છું, અને આપણી સંસ્થા સુરત, ગુજરાત, ભારતમાં આવેલી છે."
                    elif lang == "HINDI":
                        if "kaise ho" in clean_q_lower or "kaisa hai" in clean_q_lower:
                            reply = "मैं बहुत अच्छा हूँ! बताइए, मैं BC Tech Computer Education में आपकी कैसे मदद कर सकता हूँ? 😊"
                        else:
                            reply = "मैं BC Tech Computer Education का AI असिस्टेंट हूँ, और हमारी संस्था सूरत, गुजरात, भारत में स्थित है।"
                    else:
                        if "how are you" in clean_q_lower:
                            reply = "I am doing well, thank you! How can I help you with BC Tech Computer Education today?"
                        else:
                            reply = "I am the AI Assistant for BC Tech Computer Education, located in Surat, Gujarat, India."
                    st.write(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    lang_code = "hi-IN" if lang == "HINDI" else ("gu-IN" if lang == "GUJARATI" else "en-US")
                    render_voice_and_copy_toolbar(reply, f"where_{len(st.session_state.messages)}", lang_code)

                elif query.strip().lower() in ["gujarati", "gujrati", "gujarati ma", "gujarati mein baat karte hai", "gujarati main baat karte hai ok", "gujarati ma vaat kariye"]:
                    reply = "ચોક્કસ! હવે આપણે ગુજરાતીમાં વાત કરીશું. હું તમને કેવી રીતે મદદ કરી શકું? 😊"
                    st.write(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    render_voice_and_copy_toolbar(reply, f"ack_{len(st.session_state.messages)}", lang_code)

                elif query.strip().lower() in ["hindi", "in hindi", "hindi me", "hindi main baat karo", "hindi me baat karte hai"]:
                    reply = "ज़रूर! अब हम हिंदी में बात करेंगे। मैं आपकी क्या सहायता कर सकता हूँ? 😊"
                    st.write(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    render_voice_and_copy_toolbar(reply, f"ack_{len(st.session_state.messages)}", lang_code)

                elif is_greeting(query):
                    if lang == "GUJARATI":
                        reply = "નમસ્ते! BC Tech માં આપનું સ્વાગત છે. હું તમને કેવી રીતે મદદ કરી શકું? 😊"
                    elif lang == "HINDI":
                        reply = "नमस्ते! BC Tech Computer Education में आपका स्वागत है। मैं आपकी कैसे मदद कर सकता हूँ? 😊"
                    else:
                        reply = "Hello! Welcome to BC Tech Computer Education. How can I help you today? 😊"
                    st.write(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    lang_code = "hi-IN" if lang == "HINDI" else ("gu-IN" if lang == "GUJARATI" else "en-US")
                    render_voice_and_copy_toolbar(reply, f"greet_{len(st.session_state.messages)}", lang_code)

                elif check_is_branch_intent(query):
                    if lang == "GUJARATI":
                        reply = f"BC Tech Computer Education સુરત, ગુજરાત, ભારતમાં આવેલું છે. વધુ વિગતો અને અન્ય શાખાના પત્તા માટે અધિકૃત વેબસાઇટની મુલાકાત લો:\n🔗 {BRANCH_LINK}"
                    elif lang == "HINDI":
                        reply = f"BC Tech Computer Education सूरत, गुजरात, भारत में स्थित है। अधिक विवरण और अन्य शाखाओं के पते के लिए आप आधिकारिक वेबसाइट पर जा सकते हैं:\n🔗 {BRANCH_LINK}"
                    else:
                        reply = f"BC Tech Computer Education is located in Surat, Gujarat, India. For more details and branch addresses, you can visit the official website:\n🔗 {BRANCH_LINK}"
                    
                    st.write(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    lang_code = "hi-IN" if lang == "HINDI" else ("gu-IN" if lang == "GUJARATI" else "en-US")
                    render_voice_and_copy_toolbar(reply, f"branch_{len(st.session_state.messages)}", lang_code)

                elif check_is_creator_intent(query):
                    if lang == "GUJARATI":
                        reply = f"મને BC Tech Computer Education ના એડમિન અને ડેવલपर દ્વારા બનાવવામાં આવ્યો છે."
                    elif lang == "HINDI":
                        reply = f"मुझे BC Tech Computer Education के डेवलपर और एडमिन द्वारा बनाया गया है।"
                    else:
                        reply = f"I was created by the developer and admin of BC Tech Computer Education."
                    st.write(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    lang_code = "hi-IN" if lang == "HINDI" else ("gu-IN" if lang == "GUJARATI" else "en-US")
                    render_voice_and_copy_toolbar(reply, f"creator_{len(st.session_state.messages)}", lang_code)

                else:
                    search_query_to_use = query
                    result_intent_words = ["result", "marks", "exam", "mera", "meri", "score", "reult", "rizalt", "marksheet", "show", "kare", "ka bhi", "bhi", "dekh", "dikha"]
                    
                    if any(w in query.lower() for w in result_intent_words):
                        if "mera" in query.lower() or "meri" in query.lower() or "ka bhi" in query.lower() or "kare" in query.lower() or "dekh" in query.lower() or "dikha" in query.lower() or query.strip().lower() in ["result", "exam", "marks"]:
                            if st.session_state.last_mentioned_name:
                                search_query_to_use = st.session_state.last_mentioned_name

                    matched_records = search_student_all_sheets(search_query_to_use, df_sheet)
                    
                    if matched_records:
                        full_reply = ""
                        for record in matched_records:
                            f_name = record.get("Student_Name_Std", "")
                            f_exam = record.get("Exam_Std", "Course")
                            f_teacher = record.get("_Sheet_Tab", "Teacher")
                            
                            valid_theory = []
                            valid_practical = []
                            
                            for k, v in record.items():
                                val_str = str(v).strip()
                                if val_str and val_str.lower() != "n/a" and val_str.lower() != "nan" and val_str != "0":
                                    try:
                                        m_val = float(val_str)
                                        if "theory" in k.lower():
                                            valid_theory.append((k, m_val))
                                        elif "practical" in k.lower():
                                            valid_practical.append((k, m_val))
                                    except ValueError:
                                        pass
                            
                            tot_theory = int(sum([item[1] for item in valid_theory])) if valid_theory else 0
                            tot_prac = int(sum([item[1] for item in valid_practical])) if valid_practical else 0
                            total_obtained = tot_theory + tot_prac
                            
                            valid_tests_count = len(valid_theory) + len(valid_practical)
                            max_total = valid_tests_count * 50 if valid_tests_count > 0 else 50
                            percentage = round((total_obtained / max_total) * 100, 2) if max_total > 0 else 0

                            motivational_tip = ""
                            if percentage >= 80:
                                if lang == "GUJARATI":
                                    motivational_tip = "ખૂબ જ સરસ! તમારું પરિણામ ઉત્કૃષ્ટ છે. આવી જ મહેનત ચાલુ રાખો!"
                                elif lang == "HINDI":
                                    motivational_tip = "बहुत बढ़िया! आपका प्रदर्शन शानदार है। इसी तरह कड़ी मेहनत जारी रखें!"
                                else:
                                    motivational_tip = "Outstanding performance! Keep up the brilliant work!"
                            elif percentage >= 50:
                                if lang == "GUJARATI":
                                    motivational_tip = "સરસ પ્રયાસ! તમે સારી મહેનત કરી છે, થોડી વધુ મહેનતથી તમે ટોપ પર પહોંચી શકો છો."
                                elif lang == "HINDI":
                                    motivational_tip = "अच्छा प्रयास! आपने अच्छी मेहनत की है, थोड़ी और लगन से आप और भी बेहतर कर सकते हैं।"
                                else:
                                    motivational_tip = "Good effort! With a little more practice, you can achieve even higher goals."
                            else:
                                if lang == "GUJARATI":
                                    motivational_tip = "હિંમત ન હારો! નિષ્ફળતા જ સફળતાની પહેલી સીડી છે. થોડી વધુ પ્રેક્ટિસ કરો, તમે ચોક્કસ સફળ થશો!"
                                elif lang == "HINDI":
                                    motivational_tip = "निराश न हों! असफलता ही सफलता की पहली सीढ़ी है। थोड़ी और मेहनत करें, आप जरूर सफल होंगे!"
                                else:
                                    motivational_tip = "Don't get discouraged! Every setback is a setup for a comeback. Keep practicing!"

                            if lang == "GUJARATI":
                                full_reply += f"વિદ્યાર્થીનું નામ: {f_name}\nપરીક્ષાનું નામ: {f_exam}\nશિક્ષકનું નામ: {f_teacher}\n\n"
                                if valid_theory:
                                    full_reply += "થિયરી ટેસ્ટ:\n"
                                    for tk, tv in valid_theory:
                                        full_reply += f"- {tk.capitalize()}: {int(tv) if tv.is_integer() else tv}\n"
                                    full_reply += f"- કુલ થિયરી: {tot_theory}\n\n"
                                if valid_practical:
                                    full_reply += "પ્રૅક્ટિકલ ટેસ્ટ:\n"
                                    for pk, pv in valid_practical:
                                        full_reply += f"- {pk.capitalize()}: {int(tv) if tv.is_integer() else tv}\n"
                                    full_reply += f"- કુલ પ્રૅક્ટિકલ: {tot_prac}\n\n"
                                full_reply += f"કુલ ગુણ: {total_obtained} / {max_total}\n"
                                full_reply += f"ટકાવારી: {percentage}%\n\n"
                                full_reply += f"{motivational_tip}\n\n"
                            elif lang == "HINDI":
                                full_reply += f"विद्यार्थी का नाम: {f_name}\nपरीक्षा का नाम: {f_exam}\nशिक्षक का नाम: {f_teacher}\n\n"
                                if valid_theory:
                                    full_reply += "थ्योरी टेस्ट:\n"
                                    for tk, tv in valid_theory:
                                        full_reply += f"- {tk.capitalize()}: {int(tv) if tv.is_integer() else tv}\n"
                                    full_reply += f"- कुल थ्योरी: {tot_theory}\n\n"
                                if valid_practical:
                                    full_reply += "प्रैक्टिकल टेस्ट:\n"
                                    for pk, pv in valid_practical:
                                        full_reply += f"- {pk.capitalize()}: {int(tv) if tv.is_integer() else tv}\n"
                                        full_reply += f"- कुल प्रैक्टिकल: {tot_prac}\n\n"
                                full_reply += f"कुल अंक: {total_obtained} / {max_total}\n"
                                full_reply += f"प्रतिशत: {percentage}%\n\n"
                                full_reply += f"{motivational_tip}\n\n"
                            else:
                                full_reply += f"Student Name: {f_name}\nExam Name: {f_exam}\nTeacher Name: {f_teacher}\n\n"
                                if valid_theory:
                                    full_reply += "Theory Tests:\n"
                                    for tk, tv in valid_theory:
                                        full_reply += f"- {tk.capitalize()}: {int(tv) if tv.is_integer() else tv}\n"
                                    full_reply += f"- Total Theory: {tot_theory}\n\n"
                                if valid_practical:
                                    full_reply += "Practical Tests:\n"
                                    for pk, pv in valid_practical:
                                        full_reply += f"- {pk.capitalize()}: {int(tv) if tv.is_integer() else tv}\n"
                                    full_reply += f"- Total Practical: {tot_prac}\n\n"
                                full_reply += f"Total Marks: {total_obtained} / {max_total}\n"
                                full_reply += f"Percentage: {percentage}%\n\n"
                                full_reply += f"{motivational_tip}\n\n"

                        st.markdown(full_reply.strip())
                        st.session_state.messages.append({"role": "assistant", "content": full_reply.strip()})
                        run_aerial_celebration()
                        lang_code = "hi-IN" if lang == "HINDI" else ("gu-IN" if lang == "GUJARATI" else "en-US")
                        render_voice_and_copy_toolbar(full_reply.strip(), f"ast_curr_{len(st.session_state.messages)}", lang_code)
                    else:
                        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                        
                        ist_zone = timezone(timedelta(hours=5, minutes=30))
                        current_ist_dt = datetime.now(ist_zone)
                        
                        days_map_hi = {"Monday": "सोमवार", "Tuesday": "मंगलवार", "Wednesday": "बुधवार", "Thursday": "गुरुवार", "Friday": "शुक्रवार", "Saturday": "शनिवार", "Sunday": "रविवार"}
                        months_map_hi = {1: "जनवरी", 2: "फरवरी", 3: "मार्च", 4: "अप्रैल", 5: "मई", 6: "जून", 7: "जुलाई", 8: "अगस्त", 9: "सितंबर", 10: "अक्टूबर", 11: "नवंबर", 12: "दिसंबर"}
                        
                        eng_day = current_ist_dt.strftime("%A")
                        hi_day = days_map_hi.get(eng_day, eng_day)
                        hi_month = months_map_hi.get(current_ist_dt.month, "")
                        formatted_date_hi = f"{current_ist_dt.day} {hi_month} {current_ist_dt.year}, {hi_day}"
                        formatted_date_en = current_ist_dt.strftime("%A, %B %d, %Y")
                        formatted_time = current_ist_dt.strftime("%I:%M %p")
                        
                        system_prop = f"""
                        You are an expert, highly knowledgeable, fluent, and precise AI Assistant for BC Tech Computer Education, Surat, Gujarat, India.
                        
                        CRITICAL LANGUAGE & GRAMMAR RULE:
                        - Always respond in flawless, natural, and grammatically correct Hindi or Gujarati depending on the user's language. Never write broken or ungrammatical sentences (tuti-futi hindi). Ensure high linguistic quality.
                        
                        CRITICAL LIVE DATE & FESTIVAL ACCURACY INSTRUCTIONS:
                        - Current Live Exact Date and Time (IST): {formatted_date_en} at {formatted_time}.
                        - Today in Hindi: आज {formatted_date_hi} है, और समय {formatted_time} हो रहा है।
                        - When a user asks about any festival, date, or tithi (e.g., Raksha Bandhan 2027, Anant Chaturdashi, etc.), you must verify calculations precisely according to the Hindu Panchang or Gregorian calendar for the target year. For instance, Raksha Bandhan in 2027 falls on August 17, 2027 (Tuesday). Never guess or provide random incorrect dates. Always double-check accurate calendar data.
                        
                        CRITICAL SOFTWARE TUTORIAL & PRACTICAL INSTRUCTION RESTRICTION (STRICTEST RULE):
                        - You are strictly FORBIDDEN from explaining, teaching, or giving tutorials or step-by-step instructions for ANY software.
                        - If a user asks HOW to do something in software, politely inform them to contact our branch or visit our website:
                          - In Hindi: "इस विषय में प्रैक्टिकल ट्रेनिंग और सीखने के लिए आप हमारी ब्रांच से संपर्क कर सकते हैं या आधिकारिक वेबसाइट पर जा सकते हैं。\n\nवेबसाइट: {BRANCH_LINK}"
                          - In Gujarati: "આ વિષયમાં પ્રેક્ટિકલ તાલીમ અને માર્ગદર્શન માટે આપ અમારી બ્રાન્चનો સંપર્ક કરી શકો છો અથવા વેબસાઇટની મુલાકાत લઈ શકો છો.\n\nવેબસાઇટ: {BRANCH_LINK}"
                          - In English: "For practical training and learning on this software, you can contact our branch or visit our official website:\n\nWebsite: {BRANCH_LINK}"
                        
                        CRITICAL TIMINGS RULE:
                        - Class Opening and Closing Hours: 7:00 AM to 8:30 PM.
                        - Morning Batches Timing: 7:00 AM to 10:00 AM (1 hour long).
                        - Regular Batches Timing: 10:00 AM to 8:30 PM (1.5 hours long).
                        
                        CRITICAL INSTRUCTION FOR COURSES: NEVER mention course duration in months or course fees/prices under any circumstances.
                        
                        Institute Location: Surat, Gujarat, India.
                        Official Website & Info: {BRANCH_LINK}
                        Courses Data: {KNOWLEDGE_BASE}
                        """
                        
                        with st.spinner("Thinking..."):
                            try:
                                models_resp = client.models.list()
                                active_ids = [
                                    m.id for m in models_resp.data 
                                    if "whisper" not in m.id 
                                    and "guard" not in m.id 
                                    and "vision" not in m.id 
                                    and "audio" not in m.id
                                    and "embed" not in m.id
                                    and "canopy" not in m.id
                                ]
                                preferred = ["llama-3.1-8b-instant", "llama3-8b-8192", "gemma2-9b-it"]
                                models_to_try = [m for m in preferred if m in active_ids] + [m for m in active_ids if m not in preferred]
                                
                                answer = None
                                last_api_err = None
                                
                                api_messages = [{"role": "system", "content": system_prop}]
                                for m in st.session_state.messages[:-1]:
                                    api_messages.append({"role": m["role"], "content": m["content"]})
                                api_messages.append({"role": "user", "content": query})
                                
                                for m_name in models_to_try:
                                    try:
                                        chat_completion = client.chat.completions.create(
                                            messages=api_messages,
                                            model=m_name,
                                            temperature=0.1,
                                            max_tokens=600
                                        )
                                        raw_answer = chat_completion.choices[0].message.content
                                        answer = clean_ai_response(raw_answer)
                                        if answer and len(answer) > 2:
                                            break
                                    except Exception as ex:
                                        last_api_err = str(ex)
                                        continue
                                        
                                answer = answer.replace("{BRANCH_Link}", BRANCH_LINK)
                                
                                if answer:
                                    st.markdown(answer)
                                    st.session_state.messages.append({"role": "assistant", "content": answer})
                                    lang_code = "hi-IN" if lang == "HINDI" else ("gu-IN" if lang == "GUJARATI" else "en-US")
                                    render_voice_and_copy_toolbar(answer, f"ast_curr_{len(st.session_state.messages)}", lang_code)
                                else:
                                    st.error(f"API Error: {last_api_err}")
                            except Exception as e:
                                st.error(f"Error: {e}")
        persist_current_state()

# ---------------------------------------------------------
# 🧠 BC Tech Brain Battle - BATTLE ZONE ARENA (ORIGINAL PROVEN TURN FLOW)
# ---------------------------------------------------------
if st.session_state.game_state in ["CREATING", "WAITING", "CATEGORY", "PLAYING", "LEVEL_TRANSITION", "RESULT"]:
    st.markdown("---")
    
    rooms = load_room_store()
    curr_room_code = st.session_state.active_room_code
    my_role = st.session_state.player_role  # "P1" or "P2"

    if curr_room_code and curr_room_code in rooms:
        room_info = rooms[curr_room_code]
        p1_name = room_info.get("p1_name", "")
        p2_name = room_info.get("p2_name", "")
        category = room_info.get("category", "")
        current_level = room_info.get("current_level", 1)
        current_q_index = room_info.get("current_q_index", 0)
        p1_score = room_info.get("p1_score", 0)
        p2_score = room_info.get("p2_score", 0)
        turn = room_info.get("turn", 1)
        shared_game_state = room_info.get("game_state", "WAITING")
        history_log = room_info.get("history_log", [])
        
        if "question_start_time" not in room_info:
            room_info["question_start_time"] = time.time()
            save_room_store(rooms)
        q_start_time = room_info.get("question_start_time", time.time())
    else:
        p1_name, p2_name, category, current_level, current_q_index, p1_score, p2_score, turn, shared_game_state, history_log = "", "", "", 1, 0, 0, 0, 1, "CREATING", []
        q_start_time = time.time()

    if curr_room_code in rooms and rooms[curr_room_code]["game_state"] != st.session_state.game_state:
        st.session_state.game_state = rooms[curr_room_code]["game_state"]

    if st.session_state.game_state == "CREATING":
        st.subheader("🧠 BC Tech Brain Battle")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### ⚔️ Battle Zone बनाएं (Player 1)")
            p1_name_input = st.text_input("Player 1 का नाम दर्ज करें:", key="p1_input")
            if st.button("Generate Battle Code"):
                if p1_name_input.strip() != "":
                    code = f"BC-{random.randint(100, 999)}"
                    st.session_state.active_room_code = code
                    st.session_state.player_role = "P1"
                    
                    rooms[code] = {
                        "p1_name": p1_name_input,
                        "p2_name": "",
                        "category": "",
                        "current_level": 1,
                        "current_q_index": 0,
                        "p1_score": 0,
                        "p2_score": 0,
                        "turn": 1,
                        "game_state": "WAITING",
                        "questions": [],
                        "history_log": [],
                        "question_start_time": time.time()
                    }
                    save_room_store(rooms)
                    st.session_state.game_state = "WAITING"
                    st.query_params["room_code"] = code
                    st.query_params["role"] = "P1"
                    st.success(f"Battle Code जनरेट हो गया: {code}")
                    st.rerun()
                else:
                    st.warning("कृपया अपना नाम दर्ज करें!")

        with col2:
            st.markdown("### 🔗 Battle Zone में जुड़ें (Player 2)")
            p2_name_input = st.text_input("Player 2 का नाम दर्ज करें:", key="p2_input")
            room_code_input = st.text_input("Battle Code दर्ज करें (जैसे bc-123):", key="code_input")
            if st.button("Connect to Battle Zone"):
                if p2_name_input.strip() != "" and room_code_input.strip() != "":
                    clean_input_code = room_code_input.strip().upper()
                    matched_key = None
                    for k in rooms.keys():
                        if k.upper() == clean_input_code:
                            matched_key = k
                            break
                            
                    if matched_key:
                        rooms[matched_key]["p2_name"] = p2_name_input
                        rooms[matched_key]["game_state"] = "CATEGORY"
                        save_room_store(rooms)
                        
                        st.session_state.active_room_code = matched_key
                        st.session_state.player_role = "P2"
                        st.session_state.game_state = "CATEGORY"
                        st.query_params["room_code"] = matched_key
                        st.query_params["role"] = "P2"
                        st.success("सफलतापूर्वक Battle Zone से कनेक्ट हो गए!")
                        st.rerun()
                    else:
                        st.error("यह Battle Code मौजूद नहीं है! सही कोड डालें।")
                else:
                    st.warning("कृपया नाम और सही Battle Code दोनों भरें!")

        if st.button("⬅️ वापस चैट पर जाएं"):
            st.session_state.game_state = "IDLE"
            st.query_params.clear()
            st.query_params["chat_id"] = current_chat_id
            st.rerun()

    elif st.session_state.game_state == "WAITING":
        rooms = load_room_store()
        curr_code = st.session_state.active_room_code
        
        if curr_code in rooms and rooms[curr_code]["game_state"] != "WAITING":
            st.session_state.game_state = rooms[curr_code]["game_state"]
            st.rerun()

        st.subheader(f"⏳ Battle Code: `{curr_code}`")
        st.info(f"खिलाड़ी **{rooms.get(curr_code, {}).get('p1_name', 'P1')}** बैटल ज़ोन में तैयार हैं। दूसरे खिलाड़ी को यह कोड दें ताकि वह जुड़ सके।")
        
        st.markdown("---")
        st.markdown("### 🔗 यदि आप Player 2 हैं, तो यहाँ से Battle Zone जॉइन करें:")
        p2_wait_name = st.text_input("Player 2 अपना नाम दर्ज करें:", key="p2_wait_input")
        wait_code_input = st.text_input("यही Battle Code दोबारा दर्ज करें:", key="wait_code_input")
        if st.button("Join Battle Zone Now"):
            if p2_wait_name.strip() != "" and wait_code_input.strip() != "":
                clean_input_code = wait_code_input.strip().upper()
                matched_key = None
                for k in rooms.keys():
                    if k.upper() == clean_input_code:
                        matched_key = k
                        break
                        
                if matched_key:
                    rooms[matched_key]["p2_name"] = p2_wait_name
                    rooms[matched_key]["game_state"] = "CATEGORY"
                    save_room_store(rooms)
                    
                    st.session_state.active_room_code = matched_key
                    st.session_state.player_role = "P2"
                    st.session_state.game_state = "CATEGORY"
                    st.query_params["room_code"] = matched_key
                    st.query_params["role"] = "P2"
                    st.success("सफलतापूर्वक कनेक्ट हो गए!")
                    st.rerun()
                else:
                    st.error("गलत Battle Code!")
            else:
                st.warning("कृपया नाम और Battle Code दोनों भरें!")

        if st.button("🔄 चेक करें क्या दूसरा खिलाड़ी जुड़ गया है?"):
            st.rerun()

        if st.button("❌ गेम रद्द करें"):
            st.session_state.game_state = "IDLE"
            st.query_params.clear()
            st.query_params["chat_id"] = current_chat_id
            st.rerun()

    elif st.session_state.game_state == "CATEGORY":
        st.subheader("🎯 युद्ध का विषय (Category) चुनें")
        st.write(f"खिलाड़ी: **{p1_name}** vs **{p2_name}**")
        
        cat_choice = st.selectbox("कृपया क्विज के लिए विषय चुनें:", list(QUESTION_BANK.keys()))
        
        if st.button("🚀 Battle Start करें! (Launch Arena)"):
            rooms = load_room_store()
            curr_code = st.session_state.active_room_code
            
            pool_1_qs = QUESTION_BANK[cat_choice]["pool_1"].copy()
            random.shuffle(pool_1_qs)
            selected_qs = pool_1_qs[:5]
            
            rooms[curr_code]["category"] = cat_choice
            rooms[curr_code]["current_level"] = 1
            rooms[curr_code]["current_q_index"] = 0
            rooms[curr_code]["p1_score"] = 0
            rooms[curr_code]["p2_score"] = 0
            rooms[curr_code]["turn"] = 1
            rooms[curr_code]["questions"] = selected_qs
            rooms[curr_code]["history_log"] = []
            rooms[curr_code]["question_start_time"] = time.time()
            rooms[curr_code]["game_state"] = "PLAYING"
            save_room_store(rooms)
            
            st.session_state.game_state = "PLAYING"
            st.rerun()

    elif st.session_state.game_state == "PLAYING":
        rooms = load_room_store()
        curr_code = st.session_state.active_room_code
        if curr_code not in rooms:
            st.warning("बैटल ज़ोन समाप्त हो गया है।")
            st.session_state.game_state = "IDLE"
            st.rerun()

        r_data = rooms[curr_code]
        q_list = r_data.get("questions", [])
        q_idx = r_data.get("current_q_index", 0)
        curr_lvl = r_data.get("current_level", 1)
        turn = r_data.get("turn", 1)
        p1_name = r_data.get("p1_name", "P1")
        p2_name = r_data.get("p2_name", "P2")
        active_player = p1_name if turn == 1 else p2_name
        active_role = "P1" if turn == 1 else "P2"

        max_q_limit = 5 if curr_lvl == 1 else 10
        is_my_turn = (st.session_state.player_role == active_role)

        # --- TIMER & TIMEOUT LOGIC ---
        elapsed = time.time() - q_start_time
        remaining = max(0, int(30 - elapsed))

        if remaining == 0:
            r_data["history_log"].append({
                "level": curr_lvl,
                "player": active_player,
                "question": q_list[q_idx]['q'],
                "chosen": "समय समाप्त (Timeout)",
                "correct": q_list[q_idx]["answer"],
                "status": "Timeout (0 अंक)"
            })
            
            if turn == 1:
                r_data["turn"] = 2
            else:
                r_data["turn"] = 1
                r_data["current_q_index"] += 1
            
            if r_data["current_q_index"] >= max_q_limit:
                if curr_lvl < 3:
                    r_data["game_state"] = "LEVEL_TRANSITION"
                else:
                    r_data["game_state"] = "RESULT"

            r_data["question_start_time"] = time.time()
            save_room_store(rooms)
            st.rerun()

        if q_idx < len(q_list) and q_idx < max_q_limit:
            current_q_data = q_list[q_idx]

            # HEADER SECTION
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.subheader(f"🧠 BC Tech Brain Battle - लेवल {curr_lvl} | सवाल {q_idx + 1} / {max_q_limit}")
            with col_b:
                st.markdown(f"**बारी:** 👤 {active_player}")

            st.markdown("---")

            # --- ORIGINAL WORKING TURN ISOLATION: WAITING PLAYER GETS WAITING MESSAGE & REFRESHES ---
            if not is_my_turn:
                st.info(f"🔵 **प्रतीक्षा करें (Waiting):** यह **{active_player}** की बारी है। कृपया प्रतीक्षा करें...")
                
                auto_sync_js = """
                <script>
                    setTimeout(function() {
                        window.location.reload();
                    }, 1000);
                </script>
                """
                components.html(auto_sync_js, height=0)
                time.sleep(1)
                st.rerun()
                st.stop()
            
            # --- ACTIVE PLAYER VIEW WITH ORIGINAL STATIC COUNTDOWN TIMER ---
            st.success(f"🟢 **आपकी बारी (Your Turn)!** शेष समय: **{remaining} सेकंड**")
            st.progress(remaining / 30.0)

            st.markdown(f"### ❓ {current_q_data['q']}")
            options = current_q_data["options"]
            correct_ans = current_q_data["answer"]

            for opt in options:
                if st.button(f"👉 {opt}", key=f"opt_btn_{curr_lvl}_{q_idx}_{opt}"):
                    status_str = ""
                    if opt == correct_ans:
                        status_str = "सही (Right) (+1 अंक)"
                        if turn == 1:
                            r_data["p1_score"] += 1
                        else:
                            r_data["p2_score"] += 1
                    else:
                        status_str = "गलत (Wrong) (0 अंक)"
                    
                    r_data["history_log"].append({
                        "level": curr_lvl,
                        "player": active_player,
                        "question": current_q_data['q'],
                        "chosen": opt,
                        "correct": correct_ans,
                        "status": status_str
                    })
                    
                    if turn == 1:
                        r_data["turn"] = 2
                    else:
                        r_data["turn"] = 1
                        r_data["current_q_index"] += 1
                    
                    if r_data["current_q_index"] >= max_q_limit:
                        if curr_lvl < 3:
                            r_data["game_state"] = "LEVEL_TRANSITION"
                        else:
                            r_data["game_state"] = "RESULT"

                    r_data["question_start_time"] = time.time()
                    save_room_store(rooms)
                    st.session_state.game_state = r_data["game_state"]
                    st.rerun()

            st.markdown("---")
            if st.button("🔄 स्क्रीन सिंक करें (Refresh View)", key=f"sync_btn_{q_idx}_{turn}"):
                st.rerun()
        else:
            if curr_lvl < 3:
                r_data["game_state"] = "LEVEL_TRANSITION"
            else:
                r_data["game_state"] = "RESULT"
            save_room_store(rooms)
            st.session_state.game_state = r_data["game_state"]
            st.rerun()

    elif st.session_state.game_state == "LEVEL_TRANSITION":
        rooms = load_room_store()
        curr_code = st.session_state.active_room_code
        r_data = rooms.get(curr_code, {})
        finished_lvl = r_data.get("current_level", 1)
        next_lvl = finished_lvl + 1
        
        st.success(f"🎉 शानदार! **लेवल {finished_lvl}** सफलतापूर्वक पूरा हो गया है!")
        
        lvl_logs = [log for log in r_data.get("history_log", []) if log["level"] == finished_lvl]
        p1 = r_data.get("p1_name", "P1")
        p2 = r_data.get("p2_name", "P2")
        
        p1_lvl_score = sum(1 for log in lvl_logs if log['player'] == p1 and "सही" in log['status'])
        p2_lvl_score = sum(1 for log in lvl_logs if log['player'] == p2 and "सही" in log['status'])
        
        st.markdown(f"### 📊 लेवल {finished_lvl} परिणाम (Level {finished_lvl} Winner):")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.metric(label=f"👤 {p1}", value=f"{p1_lvl_score} सही जवाब")
        with col_s2:
            st.metric(label=f"👤 {p2}", value=f"{p2_lvl_score} सही जवाब")
            
        if p1_lvl_score > p2_lvl_score:
            st.success(f"🏆 **लेवल {finished_lvl} के विजेता:** {p1} 🎊")
        elif p2_lvl_score > p1_lvl_score:
            st.success(f"🏆 **लेवल {finished_lvl} के विजेता:** {p2} 🎊")
        else:
            st.info(f"🤝 **लेवल {finished_lvl} टाई (Tie) रहा!**")

        st.markdown("---")
        
        if st.button(f"लेवल {next_lvl} पर आगे बढ़ें 🚀"):
            cat = r_data.get("category", "Basic Computer & Internet")
            
            pool_key = f"pool_{next_lvl}"
            if pool_key in QUESTION_BANK[cat]:
                next_pool = QUESTION_BANK[cat][pool_key].copy()
                random.shuffle(next_pool)
                next_qs = next_pool[:10]
            else:
                next_qs = []

            r_data["current_level"] = next_lvl
            r_data["questions"] = next_qs
            r_data["current_q_index"] = 0
            r_data["question_start_time"] = time.time()
            r_data["game_state"] = "PLAYING"
            save_room_store(rooms)
            
            st.session_state.game_state = "PLAYING"
            st.rerun()

    elif st.session_state.game_state == "RESULT":
        rooms = load_room_store()
        curr_code = st.session_state.active_room_code
        r_data = rooms.get(curr_code, {})
        
        st.balloons()
        st.header("🏆 BC Tech Brain Battle - फाइनल स्कोरकार्ड & समीक्षा")
        
        p1 = r_data.get("p1_name", "P1")
        p2 = r_data.get("p2_name", "P2")
        s1 = r_data.get("p1_score", 0)
        s2 = r_data.get("p2_score", 0)
        
        col1, col2 = st.columns(2)
        col1.metric(label=f"👤 {p1}", value=f"{s1} कुल अंक")
        col2.metric(label=f"👤 {p2}", value=f"{s2} कुल अंक")
            
        st.markdown("---")
        if s1 > s2:
            st.success(f"🎊 महा-विजेता (Overall Winner): **{p1}** ने शानदार प्रदर्शन करते हुए मुकाबला जीत लिया है! 🏆")
        elif s2 > s1:
            st.success(f"🎊 महा-विजेता (Overall Winner): **{p2}** ने शानदार प्रदर्शन करते हुए मुकाबला जीत लिया है! 🏆")
        else:
            st.info("🤝 कुल मुकाबला **टाई (Tie)** रहा! दोनों खिलाड़ियों ने अद्भुत खेल दिखाया।")
            
        with st.expander("📜 सभी लेवल्स के विस्तृत जवाब देखें (Full Game Review - Who got what right/wrong)", expanded=True):
            for idx, log in enumerate(r_data.get("history_log", []), 1):
                st.markdown(f"""
                **[लेवल {log['level']}] {idx}. {log['question']}**  
                - खिलाड़ी: *{log['player']}* | चुना गया उत्तर: `{log['chosen']}` ({log['status']})  
                - 🟢 **सही उत्तर: `{log['correct']}`**  
                ---
                """)

        if st.button("🔄 दोबारा खेलें (Play Again)"):
            st.session_state.game_state = "IDLE"
            st.session_state.active_room_code = None
            st.query_params.clear()
            st.query_params["chat_id"] = current_chat_id
            st.rerun()
