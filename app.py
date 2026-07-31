import streamlit as st
import sqlite3
import os
from datetime import datetime, timedelta
import uuid
from PIL import Image

# 导入 streamlit-paste-button 库
from streamlit_paste_button import paste_image_button as pbutton

# 页面配置
st.set_page_config(
    page_title="study system",
    page_icon="📚",
    layout="centered"
)

# 初始化数据库和文件夹
def init_app():
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    
    conn = sqlite3.connect('wrong_questions.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_path TEXT NOT NULL,
            answer_path TEXT,
            knowledge_point TEXT,
            streak INTEGER DEFAULT 0,
            next_review_date DATE NOT NULL,
            status TEXT DEFAULT 'learning'
        )
    ''')
    conn.commit()
    conn.close()

# 保存图片到本地（支持文件上传对象）
def save_image(uploaded_file):
    if uploaded_file is not None:
        file_extension = uploaded_file.name.split('.')[-1]
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        file_path = os.path.join("uploads", unique_filename)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    return None

# 保存 PIL Image 到本地（支持粘贴的图片）
def save_pil_image(pil_image):
    if pil_image is None:
        return None
    unique_filename = f"{uuid.uuid4().hex}.png"
    file_path = os.path.join("uploads", unique_filename)
    pil_image.save(file_path)
    return file_path

# 添加错题到数据库
def add_card(image_path, answer_path, knowledge_point):
    conn = sqlite3.connect('wrong_questions.db')
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute('''
        INSERT INTO cards (image_path, answer_path, knowledge_point, streak, next_review_date, status)
        VALUES (?, ?, ?, 0, ?, 'learning')
    ''', (image_path, answer_path, knowledge_point, today))
    conn.commit()
    conn.close()

# 获取今日待复习卡片
def get_today_cards():
    conn = sqlite3.connect('wrong_questions.db')
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute('''
        SELECT id, image_path, answer_path, knowledge_point, streak
        FROM cards
        WHERE status = 'learning' AND next_review_date <= ?
        ORDER BY next_review_date
    ''', (today,))
    cards = c.fetchall()
    conn.close()
    return cards

# 更新卡片状态
def update_card_status(card_id, is_correct):
    conn = sqlite3.connect('wrong_questions.db')
    c = conn.cursor()
    c.execute('SELECT streak FROM cards WHERE id = ?', (card_id,))
    current_streak = c.fetchone()[0]
    today = datetime.now().strftime("%Y-%m-%d")
    
    if is_correct:
        new_streak = current_streak + 1
        if new_streak == 1:
            next_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        elif new_streak == 2:
            next_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        elif new_streak == 3:
            next_date = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")
        elif new_streak == 4:
            next_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        else:
            next_date = today
            status = 'mastered'
        
        if new_streak >= 5:
            c.execute('''
                UPDATE cards
                SET streak = ?, next_review_date = ?, status = ?
                WHERE id = ?
            ''', (new_streak, next_date, 'mastered', card_id))
        else:
            c.execute('''
                UPDATE cards
                SET streak = ?, next_review_date = ?
                WHERE id = ?
            ''', (new_streak, next_date, card_id))
    else:
        c.execute('''
            UPDATE cards
            SET streak = 0, next_review_date = ?
            WHERE id = ?
        ''', ((datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"), card_id))
    
    conn.commit()
    conn.close()

# 页面标题
st.title("📚 study system")

# 侧边栏导航
page = st.sidebar.selectbox(
    "选择功能",
    ["mistake input", "每日刷卡复习"]
)

# 初始化应用
init_app()

# 页面A：错题录入
if page == "mistake input":
    st.header("📝 mistake input")
    
    # 添加自定义CSS
    st.markdown("""
    <style>
    .paste-zone {
        border: 3px dashed #9C27B0;
        border-radius: 12px;
        padding: 40px 20px;
        text-align: center;
        background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
        cursor: pointer;
        transition: all 0.3s;
        margin: 10px 0;
        min-height: 150px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    .paste-zone:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 15px rgba(156, 39, 176, 0.3);
    }
    .paste-zone:focus {
        border-color: #7B1FA2;
        box-shadow: 0 0 20px rgba(156, 39, 176, 0.4);
        outline: none;
    }
    .paste-zone .icon {
        font-size: 48px;
    }
    .paste-zone .title {
        font-size: 16px;
        font-weight: 600;
        color: #4a148c;
        margin: 10px 0;
    }
    .paste-zone .subtitle {
        font-size: 13px;
        color: #6a1b9a;
    }
    .paste-zone kbd {
        background: #4a148c;
        color: white;
        padding: 4px 12px;
        border-radius: 5px;
        font-family: monospace;
        font-weight: bold;
    }
    .paste-status {
        margin-top: 10px;
        padding: 8px 15px;
        border-radius: 8px;
        font-size: 14px;
        display: none;
    }
    .paste-status.success {
        display: block;
        background-color: #c8e6c9;
        color: #1b5e20;
    }
    .paste-status.error {
        display: block;
        background-color: #ffcdd2;
        color: #b71c1c;
    }
    .paste-status.info {
        display: block;
        background-color: #bbdefb;
        color: #0d47a1;
    }
    .paste-btn {
        background: #7B1FA2;
        color: white;
        border: none;
        padding: 10px 30px;
        border-radius: 8px;
        font-size: 16px;
        cursor: pointer;
        margin-top: 10px;
    }
    .paste-btn:hover {
        background: #4A148C;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 初始化 session_state
    if 'pasted_question_data' not in st.session_state:
        st.session_state.pasted_question_data = None
    if 'pasted_answer_data' not in st.session_state:
        st.session_state.pasted_answer_data = None
    if 'uploaded_question_file' not in st.session_state:
        st.session_state.uploaded_question_file = None
    if 'uploaded_answer_file' not in st.session_state:
        st.session_state.uploaded_answer_file = None
    
    # 辅助函数：从 base64 数据解码图片
    def decode_pasted_image(base64_data):
        """从粘贴的 base64 数据解码为 PIL Image"""
        if not base64_data:
            return None
        try:
            import base64
            import io
            from PIL import Image
            
            if ',' in base64_data:
                base64_string = base64_data.split(',')[1]
            else:
                base64_string = base64_data
            
            image_bytes = base64.b64decode(base64_string)
            return Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            return None
    

    with st.form("add_card_form"):
        # ---- 错题图片部分 ----
        st.markdown("**📤 错题图片（必填）**")
        
        # 自定义粘贴区域（保持不变）
        paste_html_question = """
        <div id="paste-zone-question" class="paste-zone" tabindex="0">
            <div class="icon">📋</div>
            <div class="title">点击此区域，然后按 Ctrl+V / Cmd+V 粘贴截图</div>
            <div class="subtitle">
                支持 PNG、JPG、GIF 格式 | 点击后焦点在此，直接粘贴即可
            </div>
            <div id="paste-status-question" class="paste-status"></div>
        </div>
        
        <script>
        (function() {
            const zone = document.getElementById('paste-zone-question');
            const statusDiv = document.getElementById('paste-status-question');
            
            if (zone) {
                zone.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    this.focus();
                    showStatus('info', '✅ 已就绪，请粘贴图片 (Ctrl+V)');
                });
                
                document.addEventListener('paste', function(e) {
                    if (document.activeElement !== zone) return;
                    
                    const items = e.clipboardData.items;
                    let imageFound = false;
                    
                    for (let i = 0; i < items.length; i++) {
                        if (items[i].type.startsWith('image/')) {
                            imageFound = true;
                            const blob = items[i].getAsFile();
                            const reader = new FileReader();
                            
                            reader.onload = function(event) {
                                const imageData = event.target.result;
                                
                                // 显示预览
                                const previewContainer = zone.querySelector('.preview-container') || document.createElement('div');
                                previewContainer.className = 'preview-container';
                                previewContainer.style.marginTop = '15px';
                                previewContainer.style.width = '100%';
                                
                                const img = document.createElement('img');
                                img.src = imageData;
                                img.style.maxWidth = '100%';
                                img.style.maxHeight = '200px';
                                img.style.borderRadius = '8px';
                                img.style.boxShadow = '0 4px 8px rgba(0,0,0,0.2)';
                                
                                previewContainer.innerHTML = '';
                                previewContainer.appendChild(img);
                                
                                if (!zone.querySelector('.preview-container')) {
                                    zone.appendChild(previewContainer);
                                }
                                
                                showStatus('success', '✅ 图片粘贴成功！请点击下方"确认粘贴"按钮');
                                
                                // 保存数据到全局变量
                                window._pastedQuestionData = imageData;
                            };
                            
                            reader.readAsDataURL(blob);
                            break;
                        }
                    }
                    
                    if (!imageFound) {
                        showStatus('error', '❌ 剪贴板中没有图片，请先复制图片');
                    }
                });
                
                function showStatus(type, message) {
                    statusDiv.className = 'paste-status ' + type;
                    statusDiv.textContent = message;
                    statusDiv.style.display = 'block';
                }
            }
        })();
        </script>
        """
        
        st.components.v1.html(paste_html_question, height=280)
        
        # 修改：使用 form_submit_button 代替 button
        # 将原来两列布局中的按钮，改为使用 form_submit_button
        if st.form_submit_button("📥 确认粘贴并读取数据", key="confirm_question_paste"):
            # 这里不能直接读取 JavaScript 数据，需要通过 rerun 触发数据接收逻辑
            st.session_state._need_read_question_paste = True
            st.rerun()
        
        # 在按钮点击后读取粘贴数据（通过 JavaScript 的 postMessage）
        if st.session_state.get('_need_read_question_paste', False):
            st.markdown("""
            <script>
            (function() {
                if (window._pastedQuestionData) {
                    // 通过 postMessage 发送数据到 Streamlit
                    window.parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        value: window._pastedQuestionData
                    }, '*');
                    
                    // 清除标记，避免重复读取
                    window._pastedQuestionData = null;
                }
            })();
            </script>
            """, unsafe_allow_html=True)
            
            # 使用 st.text_input 作为数据接收器
            paste_receiver = st.text_input(
                "paste_receiver",
                key="paste_receiver_question",
                label_visibility="collapsed",
                value=""
            )
            
            # 如果有数据，保存到 session_state
            if paste_receiver:
                st.session_state.pasted_question_data = paste_receiver
                st.session_state._need_read_question_paste = False
                st.rerun()
        
        # 显示已粘贴的图片
        if st.session_state.pasted_question_data:
            img = decode_pasted_image(st.session_state.pasted_question_data)
            if img:
                st.success("✅ 错题图片已粘贴")
                st.image(img, caption="错题预览", use_container_width=True)
            else:
                st.warning("⚠️ 图片数据格式有误，请重新粘贴")
                st.session_state.pasted_question_data = None
        
        # 备选：文件上传
        with st.expander("📁 或者从文件选择（备选）"):
            question_file = st.file_uploader(
                "选择图片文件",
                type=['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'],
                label_visibility="collapsed",
                key="question_file_uploader"
            )
            if question_file is not None:
                st.success("✅ 文件已选择")
                st.session_state.uploaded_question_file = question_file
                img = Image.open(question_file)
                st.image(img, caption="预览", use_container_width=True)
        
        st.markdown("---")
        
        # ---- 解析图片部分（类似修改） ----
        st.markdown("**📤 解析图片（选填）**")
        
        paste_html_answer = """
        <div id="paste-zone-answer" class="paste-zone" tabindex="1">
            <div class="icon">📋</div>
            <div class="title">点击此区域，然后按 Ctrl+V / Cmd+V 粘贴截图</div>
            <div class="subtitle">
                支持 PNG、JPG、GIF 格式 | 点击后焦点在此，直接粘贴即可
            </div>
            <div id="paste-status-answer" class="paste-status"></div>
        </div>
        
        <script>
        (function() {
            const zone = document.getElementById('paste-zone-answer');
            const statusDiv = document.getElementById('paste-status-answer');
            
            if (zone) {
                zone.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    this.focus();
                    showStatus('info', '✅ 已就绪，请粘贴图片 (Ctrl+V)');
                });
                
                document.addEventListener('paste', function(e) {
                    if (document.activeElement !== zone) return;
                    
                    const items = e.clipboardData.items;
                    let imageFound = false;
                    
                    for (let i = 0; i < items.length; i++) {
                        if (items[i].type.startsWith('image/')) {
                            imageFound = true;
                            const blob = items[i].getAsFile();
                            const reader = new FileReader();
                            
                            reader.onload = function(event) {
                                const imageData = event.target.result;
                                
                                const previewContainer = zone.querySelector('.preview-container') || document.createElement('div');
                                previewContainer.className = 'preview-container';
                                previewContainer.style.marginTop = '15px';
                                previewContainer.style.width = '100%';
                                
                                const img = document.createElement('img');
                                img.src = imageData;
                                img.style.maxWidth = '100%';
                                img.style.maxHeight = '200px';
                                img.style.borderRadius = '8px';
                                img.style.boxShadow = '0 4px 8px rgba(0,0,0,0.2)';
                                
                                previewContainer.innerHTML = '';
                                previewContainer.appendChild(img);
                                
                                if (!zone.querySelector('.preview-container')) {
                                    zone.appendChild(previewContainer);
                                }
                                
                                showStatus('success', '✅ 图片粘贴成功！请点击下方"确认粘贴"按钮');
                                
                                window._pastedAnswerData = imageData;
                            };
                            
                            reader.readAsDataURL(blob);
                            break;
                        }
                    }
                    
                    if (!imageFound) {
                        showStatus('error', '❌ 剪贴板中没有图片，请先复制图片');
                    }
                });
                
                function showStatus(type, message) {
                    statusDiv.className = 'paste-status ' + type;
                    statusDiv.textContent = message;
                    statusDiv.style.display = 'block';
                }
            }
        })();
        </script>
        """
        
        st.components.v1.html(paste_html_answer, height=280)
        
        # 修改：使用 form_submit_button
        if st.form_submit_button("📥 确认粘贴并读取数据", key="confirm_answer_paste"):
            st.session_state._need_read_answer_paste = True
            st.rerun()
        
        if st.session_state.get('_need_read_answer_paste', False):
            st.markdown("""
            <script>
            (function() {
                if (window._pastedAnswerData) {
                    window.parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        value: window._pastedAnswerData
                    }, '*');
                    window._pastedAnswerData = null;
                }
            })();
            </script>
            """, unsafe_allow_html=True)
            
            paste_receiver_answer = st.text_input(
                "paste_receiver_answer",
                key="paste_receiver_answer",
                label_visibility="collapsed",
                value=""
            )
            
            if paste_receiver_answer:
                st.session_state.pasted_answer_data = paste_receiver_answer
                st.session_state._need_read_answer_paste = False
                st.rerun()
        
        if st.session_state.pasted_answer_data:
            img = decode_pasted_image(st.session_state.pasted_answer_data)
            if img:
                st.success("✅ 解析图片已粘贴")
                st.image(img, caption="解析预览", use_container_width=True)
            else:
                st.warning("⚠️ 图片数据格式有误，请重新粘贴")
                st.session_state.pasted_answer_data = None
        
        with st.expander("📁 或者从文件选择（备选）"):
            answer_file = st.file_uploader(
                "选择图片文件",
                type=['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'],
                label_visibility="collapsed",
                key="answer_file_uploader"
            )
            if answer_file is not None:
                st.success("✅ 文件已选择")
                st.session_state.uploaded_answer_file = answer_file
                img = Image.open(answer_file)
                st.image(img, caption="预览", use_container_width=True)
        
        st.markdown("---")
        
        # 知识点输入
        knowledge_point = st.text_input(
            "📌 知识点标签",
            placeholder="例如：分式方程-去分母",
        )
        
        # 真正的保存按钮（表单提交按钮）
        submitted = st.form_submit_button("💾 保存错题", use_container_width=True, type="primary")
        
        if submitted:
            # 获取图片
            final_question = None
            final_answer = None
            
            if st.session_state.pasted_question_data:
                img = decode_pasted_image(st.session_state.pasted_question_data)
                if img:
                    final_question = img
                else:
                    st.error("❌ 粘贴的错题图片数据无效，请重新粘贴或使用文件上传")
            
            if st.session_state.pasted_answer_data and final_question:
                img = decode_pasted_image(st.session_state.pasted_answer_data)
                if img:
                    final_answer = img
            
            if final_question is None and st.session_state.uploaded_question_file is not None:
                final_question = st.session_state.uploaded_question_file
            
            if final_answer is None and st.session_state.uploaded_answer_file is not None:
                final_answer = st.session_state.uploaded_answer_file
            
            if final_question is None:
                st.error("❌ 请上传错题图片！")
            elif not knowledge_point:
                st.error("❌ 请输入知识点标签！")
            else:
                if isinstance(final_question, Image.Image):
                    question_path = save_pil_image(final_question)
                else:
                    question_path = save_image(final_question)
                
                if final_answer is not None:
                    if isinstance(final_answer, Image.Image):
                        answer_path = save_pil_image(final_answer)
                    else:
                        answer_path = save_image(final_answer)
                else:
                    answer_path = None
                
                add_card(question_path, answer_path, knowledge_point)
                st.success("✅ 错题保存成功！")
                st.balloons()
                
                st.session_state.pasted_question_data = None
                st.session_state.pasted_answer_data = None
                st.session_state.uploaded_question_file = None
                st.session_state.uploaded_answer_file = None
                st.session_state._need_read_question_paste = False
                st.session_state._need_read_answer_paste = False
                st.rerun()




# 页面B：每日刷卡复习
else:
    st.header("🔄 每日刷卡复习")
    
    today_cards = get_today_cards()
    
    if not today_cards:
        st.success("🎉 太棒了！今天的错题已经全部复习完啦！")
        st.balloons()
    else:
        st.info(f"今日待复习题目数：{len(today_cards)}")
        
        if 'card_index' not in st.session_state:
            st.session_state.card_index = 0
        
        current_card = today_cards[st.session_state.card_index]
        card_id, image_path, answer_path, knowledge_point, streak = current_card
        
        with st.container():
            st.markdown("---")
            st.subheader(f"📌 知识点：{knowledge_point}")
            
            try:
                image = Image.open(image_path)
                st.image(image, use_container_width=True)
            except Exception as e:
                st.error(f"无法加载图片：{e}")
            
            with st.expander("📖 查看正确答案"):
                if answer_path:
                    try:
                        answer_image = Image.open(answer_path)
                        st.image(answer_image, use_container_width=True)
                    except Exception as e:
                        st.error(f"无法加载答案图片：{e}")
                else:
                    st.info("该题目未上传答案解析")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔴 做错了", use_container_width=True, type="primary"):
                    update_card_status(card_id, False)
                    st.success("已记录：做错了，明天再复习")
                    st.session_state.card_index += 1
                    if st.session_state.card_index >= len(today_cards):
                        st.session_state.card_index = 0
                    st.rerun()
            
            with col2:
                if st.button("🟢 做对了", use_container_width=True, type="primary"):
                    update_card_status(card_id, True)
                    conn = sqlite3.connect('wrong_questions.db')
                    c = conn.cursor()
                    c.execute('SELECT status FROM cards WHERE id = ?', (card_id,))
                    status = c.fetchone()[0]
                    conn.close()
                    
                    if status == 'mastered':
                        st.success("🎉 太棒了！该题已彻底掌握！")
                    else:
                        st.success("✅ 已记录：做对了，安排下次复习")
                    
                    st.session_state.card_index += 1
                    if st.session_state.card_index >= len(today_cards):
                        st.session_state.card_index = 0
                    st.rerun()
            
            st.markdown("---")