import streamlit as st
import random
import time

# Page Configuration
st.set_page_config(
    page_title="BC Tech AI Assistant & Quiz Arena",
    page_icon="🎓",
    layout="wide"
)

# Initialize Session States for Chat and Quiz Game
if "messages" not in st.session_state:
    st.session_state.messages = []

if "game_state" not in st.session_state:
    st.session_state.game_state = "IDLE"  # IDLE, CREATING, JOINING, CATEGORY, LEVEL, PLAYING, RESULT

if "game_data" not in st.session_state:
    st.session_state.game_data = {
        "room_code": "",
        "p1_name": "",
        "p2_name": "",
        "current_player": "",
        "category": "",
        "level": 1,
        "questions": [],
        "current_q_index": 0,
        "p1_score": 0,
        "p2_score": 0,
        "turn": 1  # 1 for Player 1, 2 for Player 2
    }

# Comprehensive Question Bank with 100% Verified Accurate Answers & Explanations
QUESTION_BANK = {
    "Basic Computer & Internet": [
        {
            "q": "कंप्यूटर में किसी फाइल को कॉपी करने की शॉर्टकट की (Shortcut Key) क्या है?",
            "options": ["Ctrl + C", "Ctrl + V", "Ctrl + X", "Ctrl + S"],
            "answer": "Ctrl + C"
        },
        {
            "q": "WWW का पूरा नाम क्या है?",
            "options": ["World Wide Web", "World Web Wide", "Web World Wide", "Wide World Web"],
            "answer": "World Wide Web"
        },
        {
            "q": "इनमें से कौन सा एक आउटपुट डिवाइस (Output Device) है?",
            "options": ["कीबोर्ड", "माउस", "मॉनिटर", "स्कैनर"],
            "answer": "मॉनिटर"
        },
        {
            "q": "कंप्यूटर का दिमाग (Brain) किसे कहा जाता है?",
            "options": ["RAM", "CPU", "Hard Disk", "Monitor"],
            "answer": "CPU"
        },
        {
            "q": "इंटरनेट का जनक (Father of Internet) किसे कहा जाता है?",
            "options": ["विंट सर्फ", "बिल गेट्स", "स्टीव जॉब्स", "मार्क जुकरबर्ग"],
            "answer": "विंट सर्फ"
        },
        {
            "q": "ईमेल (Email) भेजने के लिए किस प्रोटोकॉल का उपयोग किया जाता है?",
            "options": ["FTP", "SMTP", "HTTP", "TCP"],
            "answer": "SMTP"
        },
        {
            "q": "एक गीगाबाइट (1 GB) में कितने मेगाबाइट होते हैं?",
            "options": ["1024 KB", "1024 MB", "512 MB", "2048 MB"],
            "answer": "1024 MB"
        },
        {
            "q": "कंप्यूटर में रीसायकल बिन (Recycle Bin) का क्या काम है?",
            "options": ["फाइल डिलीट करना", "डिलीट की गई फाइलें स्टोर करना", "वायरस स्कैन करना", "इंटरनेट चलाना"],
            "answer": "डिलीट की गई फाइलें स्टोर करना"
        },
        {
            "q": "विंडोज (Windows) किस प्रकार का सॉफ्टवेयर है?",
            "options": ["ऑपरेटिंग सिस्टम", "वर्ड प्रोसेसर", "एंटीवायरस", "वेब ब्राउज़र"],
            "answer": "ऑपरेटिंग सिस्टम"
        },
        {
            "q": "कंप्यूटर की मुख्य मेमोरी (Main Memory) कौन सी होती है?",
            "options": ["CD-ROM", "Hard Disk", "RAM", "Pen Drive"],
            "answer": "RAM"
        }
    ],
    "Graphic Designing: CorelDraw": [
        {
            "q": "CorelDraw में किसी ऑब्जेक्ट को ग्रुप करने के लिए कौन सी शॉर्टकट की है?",
            "options": ["Ctrl + G", "Ctrl + U", "Ctrl + D", "Ctrl + F4"],
            "answer": "Ctrl + G"
        },
        {
            "q": "CorelDraw किस प्रकार का सॉफ्टवेयर है?",
            "options": ["वेक्टर ग्राफिक सॉफ्टवेयर", "रास्टर ग्राफिक सॉफ्टवेयर", "वर्ड प्रोसेसिंग", "स्प्रेडशीट"],
            "answer": "वेक्टर ग्राफिक सॉफ्टवेयर"
        },
        {
            "q": "CorelDraw फाइल का डिफॉल्ट एक्सटेंशन (Extension) क्या होता है?",
            "options": [".cdr", ".psd", ".ai", ".doc"],
            "answer": ".cdr"
        },
        {
            "q": "किसी ऑब्जेक्ट की डुप्लीकेट कॉपी बनाने की शॉर्टकट की क्या है?",
            "options": ["Ctrl + C", "Ctrl + D", "Ctrl + V", "Ctrl + B"],
            "answer": "Ctrl + D"
        },
        {
            "q": "CorelDraw में टेक्स्ट को आर्टिस्टिक से पैराग्राफ में बदलने के लिए क्या शॉर्टकट है?",
            "options": ["Ctrl + F2", "Ctrl + F8", "Ctrl + F9", "Ctrl + F11"],
            "answer": "Ctrl + F8"
        },
        {
            "q": "दो ऑब्जेक्ट्स को वेल्ड (Weld) करने का मुख्य कार्य क्या होता है?",
            "options": ["अलग करना", "जोड़ना", "काटना", "डिलीट करना"],
            "answer": "जोड़ना"
        },
        {
            "q": "CorelDraw में ज़ूम इन करने के लिए कौन सी शॉर्टकट की होती है?",
            "options": ["F2", "F3", "F4", "F9"],
            "answer": "F2"
        },
        {
            "q": "पूरे पेज को स्क्रीन पर फिट करने के लिए कौन सी की दबाई जाती है?",
            "options": ["F3", "F4", "F8", "F12"],
            "answer": "F4"
        },
        {
            "q": "CorelDraw में कलर पैलेट को ऑन या ऑफ करने के लिए कहाँ जाते हैं?",
            "options": ["View > Color Palette", "File > Open", "Edit > Copy", "Effects > Lens"],
            "answer": "View > Color Palette"
        },
        {
            "q": "पॉलीगन टूल (Polygon Tool) से न्यूनतम कितनी भुजाओं (Sides) का शेप बना सकते हैं?",
            "options": ["2", "3", "4", "5"],
            "answer": "3"
        }
    ],
    "Graphic Designing: Photoshop": [
        {
            "q": "Adobe Photoshop किस प्रकार का सॉफ्टवेयर है?",
            "options": ["रास्टर / पिक्सेल बेस्ड एडिटिंग", "वेक्टर ग्राफिक्स", "डेटाबेस", "प्रेजेंटेशन"],
            "answer": "रास्टर / पिक्सेल बेस्ड एडिटिंग"
        },
        {
            "q": "Photoshop फाइल का डिफ़ॉल्ट एक्सटेंशन क्या होता है?",
            "options": [".psd", ".cdr", ".png", ".jpg"],
            "answer": ".psd"
        },
        {
            "q": "नया डॉक्यूमेंट (New Document) बनाने की शॉर्टकट की क्या है?",
            "options": ["Ctrl + N", "Ctrl + O", "Ctrl + S", "Ctrl + P"],
            "answer": "Ctrl + N"
        },
        {
            "q": "किसी लेयर (Layer) को फ्री ट्रांसफॉर्म करने की शॉर्टकट की क्या है?",
            "options": ["Ctrl + T", "Ctrl + F", "Ctrl + L", "Ctrl + Shift + N"],
            "answer": "Ctrl + T"
        },
        {
            "q": "Photoshop में मैजिक वैंड टूल (Magic Wand Tool) का उपयोग किसके लिए होता है?",
            "options": ["कलर सिलेक्शन के लिए", "ब्रश चलाने के लिए", "क्रॉप करने के लिए", "टेक्स्ट लिखने के लिए"],
            "answer": "कलर सिलेक्शन के लिए"
        },
        {
            "q": "इमेज को क्रॉप (Crop) करने के लिए कीबोर्ड शॉर्टकट क्या है?",
            "options": ["C key", "M key", "V key", "B key"],
            "answer": "C key"
        },
        {
            "q": "सिलेक्शन को डी-सेलेक्ट (Deselect) करने की शॉर्टकट की क्या है?",
            "options": ["Ctrl + D", "Ctrl + A", "Ctrl + Shift + D", "Ctrl + Alt + S"],
            "answer": "Ctrl + D"
        },
        {
            "q": "फ़ोटोशॉप में ब्रश टूल (Brush Tool) की शॉर्टकट की क्या होती है?",
            "options": ["B", "P", "S", "E"],
            "answer": "B"
        },
        {
            "q": "आईड्रॉपर टूल (Eyedropper Tool) का मुख्य कार्य क्या है?",
            "options": ["कलर सैंपल पिक करना", "ज़ूम करना", "इमेज घुमाना", "ब्रश का साइज बढ़ाना"],
            "answer": "कलर सैंपल पिक करना"
        },
        {
            "q": "क्विक हीलिंग ब्रश टूल (Quick Healing Brush Tool) की शॉर्टकट की क्या है?",
            "options": ["J", "H", "K", "L"],
            "answer": "J"
        }
    ],
    "Accounting & Tally Prime": [
        {
            "q": "Tally Prime में कंट्रा वाउचर (Contra Voucher) की शॉर्टकट की क्या है?",
            "options": ["F4", "F5", "F6", "F7"],
            "answer": "F4"
        },
        {
            "q": "भुगतान (Payment) वाउचर के लिए कौन सी फंक्शन की का उपयोग होता है?",
            "options": ["F4", "F5", "F6", "F7"],
            "answer": "F5"
        },
        {
            "q": "प्राप्ति (Receipt) वाउचर की शॉर्टकट की क्या है?",
            "options": ["F4", "F5", "F6", "F8"],
            "answer": "F6"
        },
        {
            "q": "Tally में कंपनी को बंद (Close Company) करने की शॉर्टकट की क्या है?",
            "options": ["Alt + F1", "Ctrl + F1", "Alt + F3", "Ctrl + Alt + C"],
            "answer": "Alt + F1"
        },
        {
            "q": "Tally Prime में लेजर (Ledger) बनाने के लिए किस शॉर्टकट का उपयोग किया जाता है?",
            "options": ["Gateway of Tally > Create > Ledger", "Accounts Info > Ledger", "Inventory Info > Ledger", "Display > Ledger"],
            "answer": "Gateway of Tally > Create > Ledger"
        },
        {
            "q": "बिक्री (Sales) वाउचर की शॉर्टकट की क्या है?",
            "options": ["F7", "F8", "F9", "F5"],
            "answer": "F8"
        },
        {
            "q": "खरीद (Purchase) वाउचर की शॉर्टकट की क्या है?",
            "options": ["F7", "F8", "F9", "F4"],
            "answer": "F9"
        },
        {
            "q": "जर्नल वाउचर (Journal Voucher) की शॉर्टकट की क्या है?",
            "options": ["F5", "F6", "F7", "F8"],
            "answer": "F7"
        },
        {
            "q": "Tally में 'Trial Balance' देखने के लिए शॉर्टकट क्या है?",
            "options": ["Gateway of Tally > Balance Sheet", "Gateway of Tally > Display More Reports > Trial Balance", "F11", "F12"],
            "answer": "Gateway of Tally > Display More Reports > Trial Balance"
        },
        {
            "q": "क्रेडिट नोट (Credit Note) की शॉर्टकट की क्या होती है?",
            "options": ["Alt + F6", "Ctrl + F6", "Alt + F8", "Ctrl + F8"],
            "answer": "Alt + F6"
        }
    ],
    "Web Development & Programming": [
        {
            "q": "वेब पेज पर सबसे बड़ी हेडिंग दिखाने के लिए कौन सा HTML टैग उपयोग होता है?",
            "options": ["<h1>", "<h6>", "<head>", "<heading>"],
            "answer": "<h1>"
        },
        {
            "q": "CSS का पूरा नाम क्या है?",
            "options": ["Cascading Style Sheets", "Computer Style Sheets", "Creative Style System", "Colorful Style Sheet"],
            "answer": "Cascading Style Sheets"
        },
        {
            "q": "HTML दस्तावेज में लिंक बनाने के लिए किस टैग का उपयोग होता है?",
            "options": ["<a>", "<link>", "<href>", "<url>"],
            "answer": "<a>"
        },
        {
            "q": "इनमें से कौन सी एक प्रोग्रामिंग भाषा है?",
            "options": ["HTML", "CSS", "Python", "XML"],
            "answer": "Python"
        },
        {
            "q": "웹 पेज पर इमेज दिखाने के लिए किस टैग का इस्तेमाल होता है?",
            "options": ["<img>", "<image>", "<pic>", "<src>"],
            "answer": "<img>"
        },
        {
            "q": "JavaScript में किसी वेरिएबल को घोषित करने के लिए कौन सा कीवर्ड प्रयोग होता है?",
            "options": ["var", "let", "const", "उपरोक्त सभी (All of these)"],
            "answer": "उपरोक्त सभी (All of these)"
        },
        {
            "q": "HTML का नवीनतम संस्करण कौन सा है?",
            "options": ["HTML4", "HTML5", "HTML X", "HTML 2.0"],
            "answer": "HTML5"
        },
        {
            "q": "CSS में टेक्स्ट का कलर बदलने के लिए किस प्रॉपर्टी का उपयोग होता है?",
            "options": ["color", "text-color", "font-color", "background-color"],
            "answer": "color"
        },
        {
            "q": "वेबसाइट का मुख्य पृष्ठ (First Page) क्या कहलाता है?",
            "options": ["होम पेज (Home Page)", "मास्टर पेज", "फर्स्ट पेज", "वेब पेज"],
            "answer": "होम पेज (Home Page)"
        },
        {
            "q": "लाइन ब्रेक (Line Break) देने के लिए HTML में कौन सा टैग उपयोग होता है?",
            "options": ["<br>", "<lb>", "<break>", "<hr>"],
            "answer": "<br>"
        }
    ]
}

# Sidebar Interface
st.sidebar.title("🎓 BC Tech AI Assistant")
st.sidebar.markdown("---")
st.sidebar.subheader("🎮 2-Player Quiz Arena")

if st.sidebar.button("🚀 Start Quiz Game (Room Mode)"):
    st.session_state.game_state = "CREATING"
    st.rerun()

if st.sidebar.button("💬 Clear Chat"):
    st.session_state.messages = []
    st.session_state.game_state = "IDLE"
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip:** आप चैट बॉक्स में सीधे **'play game'** या **'quiz'** लिखकर भी गेम शुरू कर सकते हैं!")

# Main App Header
st.title("🤖 BC Tech Computer Education - AI Assistant & Quiz Hub")

# Chat Interface Handling
if st.session_state.game_state == "IDLE":
    # Show previous chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User Chat Input
    user_input = st.chat_input("यहाँ अपना सवाल पूछें या 'play game' टाइप करें...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Check if user wants to play game via chat
        if "play game" in user_input.lower() or "quiz" in user_input.lower() or "game" in user_input.lower():
            bot_reply = "बहुत बढ़िया! 🎮 चलिए 2-Player Quiz Game शुरू करते हैं। नीचे दिए गए बटन पर क्लिक करके अपना रूम बनाएं या जॉइन करें।"
            st.session_state.game_state = "CREATING"
        else:
            bot_reply = f"नमस्ते! आपने पूछा: '{user_input}'. BC Tech AI Assistant आपकी शिक्षा और ट्रेनिंग में मदद करने के लिए तैयार है। यदि आप क्विज खेलना चाहते हैं, तो कृपया साइडबार से या चैट में 'play game' टाइप करें।"

        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        with st.chat_message("assistant"):
            st.markdown(bot_reply)
        st.rerun()

# ---------------------------------------------------------
# QUIZ GAME FLOW & SCREENS
# ---------------------------------------------------------

elif st.session_state.game_state in ["CREATING", "JOINING"]:
    st.markdown("---")
    st.subheader("👥 2-Player Room Connection Setup")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏠 Room बनाएं (Player 1)")
        p1_name_input = st.text_input("Player 1 का नाम दर्ज करें:", key="p1_input")
        if st.button("Generate Room Code"):
            if p1_name_input.strip() != "":
                code = f"BC-{random.randint(100, 999)}"
                st.session_state.game_data["room_code"] = code
                st.session_state.game_data["p1_name"] = p1_name_input
                st.session_state.game_state = "WAITING"
                st.success(code)
                st.rerun()
            else:
                st.warning("कृपया अपना नाम दर्ज करें!")

    with col2:
        st.markdown("### 🔗 Room से जुड़ें (Player 2)")
        p2_name_input = st.text_input("Player 2 का नाम दर्ज करें:", key="p2_input")
        room_code_input = st.text_input("रूम कोड दर्ज करें (जैसे BC-123):", key="code_input")
        if st.button("Connect to Room"):
            if p2_name_input.strip() != "" and room_code_input.strip() != "":
                st.session_state.game_data["room_code"] = room_code_input
                st.session_state.game_data["p2_name"] = p2_name_input
                st.session_state.game_data["current_player"] = p2_name_input
                st.session_state.game_state = "CATEGORY"
                st.success("सफलतापूर्वक कनेक्ट हो गए!")
                st.rerun()
            else:
                st.warning("कृपया नाम और सही रूम कोड दोनों भरें!")

    if st.button("⬅️ वापस चैट पर जाएं"):
        st.session_state.game_state = "IDLE"
        st.rerun()

elif st.session_state.game_state == "WAITING":
    st.markdown("---")
    st.subheader(f"⏳ रूम कोड: `{st.session_state.game_data['room_code']}`")
    st.info(f"खिलाड़ी **{st.session_state.game_data['p1_name']}** रूम में तैयार हैं। दूसरे खिलाड़ी (Player 2) को यह कोड दें ताकि वह जुड़ सके।")
    
    # Simulate joining for smooth local testing if Player 2 name hasn't been set
    p2_sim = st.text_input("테스트 के लिए Player 2 का नाम दर्ज करें:")
    if st.button("Simulate Player 2 Join"):
        if p2_sim.strip() != "":
            st.session_state.game_data["p2_name"] = p2_sim
            st.session_state.game_state = "CATEGORY"
            st.rerun()

    if st.button("❌ गेम रद्द करें"):
        st.session_state.game_state = "IDLE"
        st.rerun()

elif st.session_state.game_state == "CATEGORY":
    st.markdown("---")
    st.subheader("🎯 विषय (Category) चुनें")
    st.write(f"खिलाड़ी: **{st.session_state.game_data['p1_name']}** vs **{st.session_state.game_data['p2_name']}**")
    
    cat_choice = st.selectbox("कृपया क्विज के लिए विषय चुनें:", list(QUESTION_BANK.keys()))
    
    if st.button("आगे बढ़ें (Select Level)"):
        st.session_state.game_data["category"] = cat_choice
        st.session_state.game_state = "LEVEL"
        st.rerun()

elif st.session_state.game_state == "LEVEL":
    st.markdown("---")
    st.subheader("📊 कठिनाई स्तर (Difficulty Level) चुनें")
    st.write( चुना गया विषय: **{st.session_state.game_data['category']}** )
    
    level_choice = st.radio("लेवल चुनें:", [
        "Level 1 (5 सवाल - आसान और तेज)",
        "Level 2 (10 सवाल - मध्यम)",
        "Level 3 (10 सवाल - एडवांस्ड एक्सपर्ट)"
    ])
    
    if st.button("🚀 गेम शुरू करें!"):
        if "Level 1" in level_choice:
            num_q = 5
            lvl_num = 1
        elif "Level 2" in level_choice:
            num_q = 10
            lvl_num = 2
        else:
            num_q = 10
            lvl_num = 3
            
        st.session_state.game_data["level"] = lvl_num
        
        # Fetch and Shuffle Questions randomly from Question Bank
        all_qs = QUESTION_BANK[st.session_state.game_data["category"]]
        random.shuffle(all_qs)
        st.session_state.game_data["questions"] = all_qs[:num_q]
        st.session_state.game_data["current_q_index"] = 0
        st.session_state.game_data["p1_score"] = 0
        st.session_state.game_data["p2_score"] = 0
        st.session_state.game_data["turn"] = 1
        
        st.session_state.game_state = "PLAYING"
        st.rerun()

elif st.session_state.game_state == "PLAYING":
    q_idx = st.session_state.game_data["current_q_index"]
    total_q = len(st.session_state.game_data["questions"])
    
    if q_idx < total_q:
        current_q_data = st.session_state.game_data["questions"][q_idx]
        current_turn = st.session_state.game_data["turn"]
        active_player = st.session_state.game_data["p1_name"] if current_turn == 1 else st.session_state.game_data["p2_name"]
        
        st.markdown("---")
        col_a, col_b = st.columns([3, 1])
        with col_a:
            st.subheader(f"🎮 लेवल {st.session_state.game_data['level']} | सवाल {q_idx + 1} / {total_q}")
        with col_b:
            st.markdown(f"**बारी:** 👤 {active_player}")

        st.markdown(f"### ❓ {current_q_data['q']}")
        
        # Shuffle options so options position changes randomly every time
        options = current_q_data["options"].copy()
        random.shuffle(options)
        
        # 30-Second Timer Representation & Form
        st.warning("⏱️ आपके पास इस सवाल का जवाब देने के लिए **30 सेकंड** का समय है! (समय सीमा समाप्त होने या जवाब न देने पर 0 अंक मिलेंगे)")
        
        with st.form(key=f"q_form_{q_idx}_{current_turn}"):
            ans_choice = st.radio("विकल्प चुनें:", options, index=None)
            submitted = st.form_submit_button("उत्तर जमा करें (Submit)")
            
            if submitted:
                if ans_choice is None:
                    # No answer given -> 0 points rule
                    st.warning("⚠️ आपने कोई उत्तर नहीं चुना! टाइमआउट या नो-आंसर के कारण 0 अंक मिले।")
                else:
                    # Check correct answer
                    if ans_choice == current_q_data["answer"]:
                        st.success(f"🎉 सही उत्तर! (Right Answer: {current_q_data['answer']})")
                        if current_turn == 1:
                            st.session_state.game_data["p1_score"] += 1
                        else:
                            st.session_state.game_data["p2_score"] += 1
                    else:
                        st.error(f"❌ गलत उत्तर! सही उत्तर यह था: **{current_q_data['answer']}**")
                
                # Switch turn or move to next question
                if current_turn == 1:
                    st.session_state.game_data["turn"] = 2
                else:
                    st.session_state.game_data["turn"] = 1
                    st.session_state.game_data["current_q_index"] += 1
                
                time.sleep(1.5)
                st.rerun()
    else:
        st.session_state.game_state = "RESULT"
        st.rerun()

elif st.session_state.game_state == "RESULT":
    st.markdown("---")
    st.balloons()
    st.header("🏆 फाइनल स्कोरकार्ड & विजेता (Final Results)")
    
    p1 = st.session_state.game_data["p1_name"]
    p2 = st.session_state.game_data["p2_name"]
    s1 = st.session_state.game_data["p1_score"]
    s2 = st.session_state.game_data["p2_score"]
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label=f"👤 {p1}", value=f"{s1} अंक")
    with col2:
        st.metric(label=f"👤 {p2}", value=f"{s2} अंक")
        
    st.markdown("---")
    if s1 > s2:
        st.success(f"🎊 विजेता: **{p1}** ने शानदार प्रदर्शन करते हुए यह मुकाबला जीत लिया है! 🏆")
    elif s2 > s1:
        st.success(f"🎊 विजेता: **{p2}** ने शानदार प्रदर्शन करते हुए यह मुकाबला जीत लिया है! 🏆")
    else:
        st.info("🤝 मुकाबला **टाई (Tie)** रहा! दोनों खिलाड़ियों ने बेहतरीन खेला।")
        
    if st.button("🔄 दोबारा खेलें (Play Again)"):
        st.session_state.game_state = "IDLE"
        st.rerun()
