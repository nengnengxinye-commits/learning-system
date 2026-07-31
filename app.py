import streamlit as st
import sqlite3
import os
from datetime import datetime, timedelta
import uuid
from PIL import Image

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
    
    # 简洁提示
    st.info("""
    📤 **上传方式：**
    - 点击下方区域选择图片文件
    - 支持拖拽上传
    """)
    
    with st.form("add_card_form"):
        # ---- 错题图片部分 ----
        st.markdown("**📤 错题图片（必填）**")
        question_file = st.file_uploader(
            "选择错题图片",
            type=['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'],
            accept_multiple_files=False,
            key="question_file_uploader"
        )
        
        if question_file is not None:
            st.success("✅ 错题图片已加载")
            img = Image.open(question_file)
            st.image(img, caption="错题预览", use_container_width=True)
        
        st.markdown("---")
        
        # ---- 解析图片部分 ----
        st.markdown("**📤 解析图片（选填）**")
        answer_file = st.file_uploader(
            "选择解析图片",
            type=['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'],
            accept_multiple_files=False,
            key="answer_file_uploader"
        )
        
        if answer_file is not None:
            st.success("✅ 解析图片已加载")
            img = Image.open(answer_file)
            st.image(img, caption="解析预览", use_container_width=True)
        
        st.markdown("---")
        
        # 知识点输入
        knowledge_point = st.text_input(
            "📌 知识点标签",
            placeholder="例如：分式方程-去分母",
        )
        
        submitted = st.form_submit_button("💾 保存错题", use_container_width=True, type="primary")
        
        if submitted:
            if question_file is None:
                st.error("❌ 请上传错题图片！")
            elif not knowledge_point:
                st.error("❌ 请输入知识点标签！")
            else:
                question_path = save_image(question_file)
                answer_path = save_image(answer_file) if answer_file else None
                add_card(question_path, answer_path, knowledge_point)
                st.success("✅ 错题保存成功！")
                st.balloons()
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
