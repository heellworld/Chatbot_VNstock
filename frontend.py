import streamlit as st
from dags.src.chatbot import chatbot_agent

# Cấu hình trang
st.set_page_config(
    page_title="StockBot - Trợ lý Phân tích Tài chính",
    page_icon="📈",
    layout="wide"  # Sử dụng layout rộng để tối ưu không gian trò chuyện
)

# Khởi tạo session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "started" not in st.session_state:
    st.session_state.started = False

# Tiêu đề chính
st.title("StockBot 📈 - Trợ lý Phân tích Tài chính")

# Sidebar tối giản
with st.sidebar:
    st.caption("StockBot v1.0.0")
    if st.button("Xóa lịch sử trò chuyện"):
        st.session_state.messages = []
        st.session_state.started = False

# Khu vực trò chuyện
chat_container = st.container()

with chat_container:
    # Hiển thị lịch sử trò chuyện
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="👤" if message["role"] == "user" else "🤖"):
            st.markdown(message["content"])

# Thông báo chào mừng
if not st.session_state.started:
    welcome_message = """
    👋 Chào mừng đến với StockBot!
    
    Tôi là trợ lý AI chuyên phân tích tài chính và cổ phiếu trên thị trường Việt Nam.
    
    Hãy hỏi tôi về một mã chứng khoán để bắt đầu!
    """
    st.session_state.messages.append({"role": "assistant", "content": welcome_message})
    st.session_state.started = True

# Nhập câu hỏi
prompt = st.chat_input("Hỏi về phân tích cổ phiếu...")

if prompt:
    # Thêm câu hỏi người dùng vào lịch sử
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Hiển thị câu hỏi của người dùng
    with chat_container:
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
    
    # Gọi chatbot và hiển thị phản hồi
    try:
        response = chatbot_agent(prompt)
    except Exception as e:
        response = f"Đã xảy ra lỗi: {str(e)}"
    
    # Thêm phản hồi vào lịch sử trò chuyện
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Hiển thị phản hồi của bot
    with chat_container:
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(response)