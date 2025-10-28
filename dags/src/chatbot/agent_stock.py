import logging
import os
import pandas as pd
from typing import Optional, Dict, List
from dotenv import load_dotenv
import nest_asyncio
from llama_index.core.tools import QueryEngineTool, FunctionTool
from llama_index.core.agent import ReActAgent, FunctionCallingAgent
from llama_index.core.chat_engine import SimpleChatEngine
from ...config.database import engine
from ...config.models_llm import llm_gpt4o
from .index_to_vectostore import load_data_vectostore, load_indexs
from .function_calling.function import StockAnalyzer

# Thiết lập cơ bản
load_dotenv()
nest_asyncio.apply()

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Danh sách mã chứng khoán VN30
# VN30_SYMBOLS = ["ACB", "BID", "BVH", "CTG", "FPT", "HPG", "BCM", "GAS", "GVR", "HDB", 
#                 "MBB", "MSN", "MWG", "PLX", "POW", "SAB", "SHB", "SSB", "SSI", "STB",
#                 "TCB", "TPB", "VCB", "VHM", "VIB", "VIC", "VJC", "VNM", "VPB", "LPB"]
VN30_SYMBOLS = ["ACB", "BID", "BVH", "CTG", "FPT"]
# System Prompts cho từng loại chuyên gia
STOCK_NEWS_RESEARCHER_PROMPT = """
Bạn là chuyên gia phân tích tin tức kinh tế vĩ mô với hơn 10 năm kinh nghiệm.

**VAI TRÒ:** Chuyên gia phân tích tin tức kinh tế vĩ mô và chính sách, tập trung vào tác động của các sự kiện toàn cầu đối với thị trường tài chính.

**MỤC TIÊU:** Xác định, sàng lọc và tóm tắt các tin tức quan trọng về chính sách kinh tế và các sự kiện vĩ mô có khả năng ảnh hưởng đến tâm lý thị trường.

**PHONG CÁCH LÀM VIỆC:**
- Phân tích nhanh chóng các diễn biến toàn cầu
- Tập trung vào các tuyên bố từ ngân hàng trung ương, chỉ số kinh tế vĩ mô
- Ưu tiên độ chính xác, tính thời sự và tác động tiềm năng đến thị trường Việt Nam

**NHIỆM VỤ:** Khi được yêu cầu, hãy phân tích bối cảnh vĩ mô ảnh hưởng đến thị trường chứng khoán Việt Nam.
"""

FUNDAMENTAL_ANALYST_PROMPT = """
Bạn là chuyên gia phân tích định giá doanh nghiệp với kinh nghiệm tại quỹ đầu tư tổ chức.

**VAI TRÒ:** Chuyên gia phân tích định giá doanh nghiệp, chuyên so sánh hiệu suất tài chính và định giá cổ phiếu so với các chuẩn ngành.

**MỤC TIÊU:** Phân tích báo cáo tài chính chuyên sâu để đánh giá sức khỏe tài chính, tiềm năng tăng trưởng, và xác định giá trị thực của doanh nghiệp.

**CÔNG CỤ PHÂN TÍCH:**
- Các chỉ số: P/E, P/B, ROE, ROA, D/E, EPS, EV/EBITDA
- So sánh với trung bình ngành
- Phân tích tăng trưởng doanh thu và lợi nhuận
- Đánh giá biên lợi nhuận

**CÁCH ĐÁNH GIÁ:**
- P/E so với trung bình ngành (14.07 cho VN)
- ROE > 15% là tốt, ROE > 20% là xuất sắc
- D/E < 1.0 là an toàn, D/E > 2.0 cần cảnh báo
- Tăng trưởng doanh thu ổn định qua các quý/năm

**KẾT LUẬN:** Luôn đưa ra nhận định rõ ràng: RẺ / ĐẮT / HỢP LÝ
"""

TECHNICAL_ANALYST_PROMPT = """
Bạn là nhà phân tích kỹ thuật chuyên nghiệp với phong cách kỷ luật và dựa trên tín hiệu xác nhận.

**VAI TRÒ:** Nhà phân tích kỹ thuật chuyên sử dụng biểu đồ và chỉ báo để phát hiện xu hướng thị trường, điểm đảo chiều, và tín hiệu giao dịch.

**MỤC TIÊU:** Đọc và giải thích hành vi giá thông qua biểu đồ và chỉ báo kỹ thuật, xác định điểm vào/ra lệnh tối ưu.

**CÔNG CỤ PHÂN TÍCH:**
- Chỉ báo động lượng: RSI, MACD, Stochastic
- Chỉ báo xu hướng: SMA, EMA, Bollinger Bands
- Phân tích khối lượng: Volume, OBV
- Xác định vùng hỗ trợ/kháng cự

**CÁCH ĐÁNH GIÁ:**
- RSI > 70: Quá mua, RSI < 30: Quá bán
- MACD cắt lên: Tín hiệu tăng, MACD cắt xuống: Tín hiệu giảm
- Giá trên SMA20: Xu hướng tăng ngắn hạn
- Volume tăng kèm giá tăng: Xác nhận xu hướng

**KẾT LUẬN:** Luôn đưa ra nhận định xu hướng: TĂNG / GIẢM / ĐI NGANG
"""

INVESTMENT_STRATEGIST_PROMPT = """
Bạn là cố vấn chiến lược đầu tư với nền tảng quản lý danh mục chuyên nghiệp.

**VAI TRÒ:** Cố vấn chiến lược đầu tư chuyên kết hợp phân tích cơ bản, kỹ thuật và vĩ mô để đưa ra khuyến nghị đầu tư tổng thể.

**MỤC TIÊU:** Tổng hợp dữ liệu đa chiều để đề xuất các chiến lược phù hợp với bối cảnh thị trường, tối ưu hóa lợi nhuận điều chỉnh theo rủi ro.

**NGUYÊN TẮC RA QUYẾT ĐỊNH:**
1. **Phân tích vĩ mô:** Đánh giá môi trường kinh tế, chính sách, tình hình địa chính trị
2. **Phân tích cơ bản:** Sức khỏe tài chính, định giá, triển vọng ngành
3. **Phân tích kỹ thuật:** Xu hướng giá, tín hiệu mua/bán, timing
4. **Quản lý rủi ro:** Đánh giá rủi ro/lợi nhuận, đa dạng hóa

**KHUYẾN NGHỊ:**
- **MUA:** Khi cả 3 yếu tố đều tích cực hoặc 2/3 rất tích cực
- **BÁN:** Khi cả 3 yếu tố đều tiêu cực hoặc 2/3 rất tiêu cực  
- **GIỮ:** Khi tín hiệu trái chiều hoặc cần chờ thêm thông tin

**ĐỊNH DẠNG KẾT LUẬN:** Luôn kết thúc bằng **MUA** / **BÁN** / **GIỮ** và lý do cụ thể.
"""

# Prompt chính cho hệ thống tư vấn thông minh
INTELLIGENT_ADVISOR_PROMPT = """
Bạn là Hệ thống Tư vấn Đầu tư Thông minh VN30 - một AI được thiết kế để cung cấp lời khuyên đầu tư chứng khoán toàn diện và chính xác.

**KHẢ NĂNG CỦA BẠN:**
🔍 **Phân tích Đa chiều:** Kết hợp phân tích vĩ mô, cơ bản và kỹ thuật
📊 **Truy xuất Dữ liệu:** Truy cập báo cáo tài chính và dữ liệu thị trường realtime
🎯 **Tư vấn Cá nhân hóa:** Đưa ra khuyến nghị phù hợp với từng câu hỏi cụ thể

**QUY TRÌNH TỰ ĐỘNG CHỌN CÔNG CỤ:**

1. **PHÂN TÍCH CÂU HỎI:** Xác định loại thông tin người dùng cần:
   - Thông tin công ty/báo cáo tài chính → Sử dụng Query Engine Tools
   - Dữ liệu giá/chỉ số tài chính → Sử dụng Function Tools
   - Phân tích tổng hợp → Kết hợp nhiều công cụ

2. **CHỌN CHUYÊN GIA PHÙ HỢP:**
   - 📰 **Tin tức vĩ mô** → Stock News Researcher
   - 📈 **Phân tích cơ bản** → Fundamental Analyst  
   - 📉 **Phân tích kỹ thuật** → Technical Analyst
   - 🎯 **Khuyến nghị đầu tư** → Investment Strategist

3. **THU THẬP VÀ PHÂN TÍCH:**
   - Thu thập dữ liệu từ các nguồn phù hợp
   - Áp dụng góc nhìn chuyên gia tương ứng
   - Kiểm tra tính nhất quán và logic

4. **TỔNG HỢP VÀ TƯ VẤN:**
   - Kết hợp kết quả từ các chuyên gia
   - Đưa ra lời khuyên cân bằng và thực tế
   - Luôn có khuyến nghị rõ ràng: MUA/BÁN/GIỮ

**NGUYÊN TẮC HOẠT ĐỘNG:**
✅ **Tính chính xác:** Chỉ dựa trên dữ liệu có sẵn, không đoán mò
✅ **Tính toàn diện:** Xem xét nhiều góc độ trước khi khuyến nghị
✅ **Tính thực tế:** Đưa ra lời khuyên khả thi và có căn cứ
✅ **Quản lý rủi ro:** Luôn cảnh báo về rủi ro tiềm ẩn

**CÁCH TRẢ LỜI:**
- Sử dụng tiếng Việt rõ ràng, dễ hiểu
- Cấu trúc logic: Phân tích → Đánh giá → Khuyến nghị
- Luôn giải thích lý do cho từng kết luận
- Kết thúc bằng khuyến nghị cụ thể và điều kiện theo dõi

Hãy phân tích câu hỏi của người dùng và tự động chọn công cụ, chuyên gia phù hợp để đưa ra lời tư vấn tốt nhất.
"""

# Các hàm phân tích dữ liệu (giữ nguyên)
def analyze_stock_price_summary(stock_symbol: str, year: Optional[int] = None, 
                               quarter: Optional[int] = None) -> pd.DataFrame:
    """Phân tích tổng hợp giá chứng khoán theo mã cụ thể."""
    analyzer = StockAnalyzer(engine)
    return analyzer.analyze_stock_price_summary(stock_symbol, year, quarter)

def analyze_quarterly_financial_ratios(stock_symbol: str, year: Optional[int] = None, 
                                      ratio_type: Optional[str] = None) -> pd.DataFrame:
    """Phân tích chỉ số tài chính theo quý của một mã chứng khoán."""
    analyzer = StockAnalyzer(engine)
    return analyzer.analyze_quarterly_financial_ratios(stock_symbol, year, ratio_type)

def analyze_stock_price_movement(stock_symbol: str, from_date: Optional[str] = None, 
                                to_date: Optional[str] = None) -> pd.DataFrame:
    """Phân tích biến động giá của một mã chứng khoán."""
    analyzer = StockAnalyzer(engine)
    return analyzer.analyze_stock_price_movement(stock_symbol, from_date, to_date)

def analyze_vn30_performance(stock_symbol: Optional[str] = None, top_n: int = 5, 
                            period: str = 'month') -> pd.DataFrame:
    """Phân tích hiệu suất của các mã trong VN30."""
    analyzer = StockAnalyzer(engine)
    return analyzer.analyze_vn30_performance(stock_symbol, top_n, period)

def analyze_sector_comparison(stock_symbol: str) -> Dict:
    """So sánh mã chứng khoán với ngành."""
    analyzer = StockAnalyzer(engine)
    # Thêm logic so sánh với ngành
    return {"message": f"Phân tích so sánh {stock_symbol} với ngành"}

# Khởi tạo vector stores (giữ nguyên)
def initialize_vector_stores():
    """Khởi tạo vector store cho tất cả mã chứng khoán."""
    base_dir = r"D:\project\Chatbot_VNstock\data"
    for symbol in VN30_SYMBOLS:
        try:
            table_name = f"{symbol}_financials_report"
            logger.info(f"Đang xử lý: {symbol}")
            load_data_vectostore(table_name, base_dir)
        except Exception as e:
            logger.error(f"Lỗi xử lý {symbol}: {str(e)}")
            continue

# Tạo query engines (giữ nguyên nhưng cải thiện description)
def create_query_engines():
    """Tạo danh sách query engines cho tất cả mã chứng khoán."""
    query_engine_tools = []
    for symbol in VN30_SYMBOLS:
        try:
            table_name = f"{symbol}_financials_report"
            index = load_indexs(table_name)
            query_engine = index.as_query_engine(similarity_top_k=10, llm=llm_gpt4o)
            query_engine_tools.append(
                QueryEngineTool.from_defaults(
                    query_engine=query_engine,
                    name=f"financial_report_{symbol}",
                    description=f"""
                    Công cụ truy vấn báo cáo tài chính của {symbol}.
                    
                    SỬ DỤNG KHI:
                    - Cần thông tin về tình hình tài chính của {symbol}
                    - Phân tích doanh thu, lợi nhuận, tài sản, nợ của {symbol}
                    - So sánh hiệu quả kinh doanh qua các năm
                    - Đánh giá sức khỏe tài chính tổng thể
                    
                    KHÔNG SỬ DỤNG KHI:
                    - Cần dữ liệu giá cổ phiếu theo thời gian
                    - Cần chỉ số kỹ thuật (RSI, MACD, v.v.)
                    - So sánh hiệu suất với các mã khác
                    """
                )
            )
        except Exception as e:
            logger.warning(f"Không tải được {symbol}: {str(e)}")
            continue
    return query_engine_tools

# Phân loại loại câu hỏi
def classify_question_type(text: str) -> Dict[str, bool]:
    """Phân loại loại câu hỏi để chọn chuyên gia phù hợp."""
    text_lower = text.lower()
    
    # Keywords cho từng loại phân tích
    fundamental_keywords = ['pe', 'pb', 'roe', 'roa', 'eps', 'doanh thu', 'lợi nhuận', 'tài chính', 'báo cáo', 'định giá']
    technical_keywords = ['rsi', 'macd', 'sma', 'ema', 'xu hướng', 'tăng', 'giảm', 'kỹ thuật', 'biểu đồ']
    news_keywords = ['tin tức', 'vĩ mô', 'chính sách', 'kinh tế', 'thị trường', 'ảnh hưởng']
    comparison_keywords = ['so sánh', 'tốt nhất', 'xếp hạng', 'top', 'nên chọn']
    
    return {
        'fundamental': any(keyword in text_lower for keyword in fundamental_keywords),
        'technical': any(keyword in text_lower for keyword in technical_keywords),
        'news': any(keyword in text_lower for keyword in news_keywords),
        'comparison': any(keyword in text_lower for keyword in comparison_keywords),
        'investment_decision': any(word in text_lower for word in ['nên', 'mua', 'bán', 'đầu tư', 'khuyến nghị'])
    }

# Hàm tư vấn thông minh chính
def intelligent_stock_advisor(text: str):
    """Hệ thống tư vấn chứng khoán thông minh với khả năng tự động chọn công cụ."""
    
    logger.info(f"Câu hỏi: {text}")
    
    # Phân loại câu hỏi
    question_type = classify_question_type(text)
    logger.info(f"Loại câu hỏi: {question_type}")
    
    # Tạo các công cụ
    query_engine_tools = create_query_engines()
    
    function_tools = [
        FunctionTool.from_defaults(
            analyze_stock_price_summary,
            name="price_summary_tool",
            description="Truy xuất tóm tắt giá cổ phiếu theo mã, năm, quý. Sử dụng khi cần dữ liệu giá lịch sử."
        ),
        FunctionTool.from_defaults(
            analyze_quarterly_financial_ratios,
            name="financial_ratios_tool", 
            description="Truy xuất chỉ số tài chính (P/E, P/B, ROE, etc.) theo mã, năm. Sử dụng khi cần phân tích định giá."
        ),
        FunctionTool.from_defaults(
            analyze_stock_price_movement,
            name="price_movement_tool",
            description="Phân tích biến động giá theo khoảng thời gian. Sử dụng cho phân tích kỹ thuật."
        ),
        FunctionTool.from_defaults(
            analyze_vn30_performance,
            name="vn30_performance_tool",
            description="So sánh hiệu suất các mã VN30. Sử dụng khi cần xếp hạng hoặc so sánh."
        )
    ]
    
    all_tools = query_engine_tools + function_tools
    
    # Tạo agent chính thông minh
    main_agent = ReActAgent.from_tools(
        tools=all_tools,
        llm=llm_gpt4o,
        verbose=True,
        system_prompt=INTELLIGENT_ADVISOR_PROMPT
    )
    
    # Xây dựng prompt dựa trên loại câu hỏi
    enhanced_prompt = f"""
    **CÂU HỎI NGƯỜI DÙNG:** {text}
    
    **PHÂN TÍCH CÂU HỎI:**
    - Cần phân tích cơ bản: {'Có' if question_type['fundamental'] else 'Không'}
    - Cần phân tích kỹ thuật: {'Có' if question_type['technical'] else 'Không'}  
    - Cần tin tức vĩ mô: {'Có' if question_type['news'] else 'Không'}
    - Cần so sánh: {'Có' if question_type['comparison'] else 'Không'}
    - Cần khuyến nghị đầu tư: {'Có' if question_type['investment_decision'] else 'Không'}
    
    **HƯỚNG DẪN XỬ LÝ:**
    1. Xác định mã chứng khoán cần phân tích từ câu hỏi
    2. Chọn công cụ phù hợp:
       - Query Engine Tools: cho thông tin báo cáo tài chính
       - Function Tools: cho dữ liệu số và chỉ số
    3. Thu thập dữ liệu cần thiết
    4. Áp dụng góc nhìn chuyên gia phù hợp
    5. Đưa ra phân tích và khuyến nghị rõ ràng
    
    Hãy trả lời một cách toàn diện và chuyên nghiệp.
    """
    
    # Thực hiện phân tích
    try:
        response = main_agent.chat(enhanced_prompt)
        
        # Nếu cần khuyến nghị đầu tư, tạo thêm agent chuyên về khuyến nghị
        if question_type['investment_decision']:
            strategist_agent = SimpleChatEngine.from_defaults(
                llm=llm_gpt4o,
                system_prompt=INVESTMENT_STRATEGIST_PROMPT
            )
            
            final_prompt = f"""
            **DỮ LIỆU PHÂN TÍCH:**
            {str(response)}
            
            **YÊU CẦU:** 
            Dựa trên dữ liệu trên, hãy đưa ra khuyến nghị đầu tư cuối cùng cho câu hỏi: "{text}"
            
            **ĐỊNH DẠNG TRÊND LỜI:**
            1. **Tóm tắt phân tích** (2-3 câu)
            2. **Đánh giá rủi ro** (1-2 câu)  
            3. **Khuyến nghị cuối cùng: MUA/BÁN/GIỮ** (in đậm)
            4. **Lý do và điều kiện theo dõi** (2-3 câu)
            """
            
            final_response = strategist_agent.chat(final_prompt)
            return str(final_response)
        
        return str(response)
        
    except Exception as e:
        logger.error(f"Lỗi trong quá trình phân tích: {str(e)}")
        return f"Xin lỗi, đã xảy ra lỗi trong quá trình phân tích: {str(e)}. Vui lòng thử lại hoặc điều chỉnh câu hỏi."

# Hàm wrapper cho việc sử dụng (giữ tương thích với code cũ)
def chatbot_agent(text: str):
    """Wrapper function để giữ tương thích với code cũ."""
    return intelligent_stock_advisor(text)

# # Ví dụ sử dụng
# if __name__ == "__main__":
#     # Test cases
#     test_questions = [
#         "Phân tích cơ bản cổ phiếu FPT",
#         "So sánh P/E của ACB và BID",
#         "Xu hướng giá HPG trong tháng này",
#         "Nên mua hay bán VCB bây giờ?",
#         "Top 5 cổ phiếu VN30 tăng mạnh nhất"
#     ]
    
#     print("🤖 VN30 Intelligent Stock Advisor")
#     print("=" * 50)
    
#     for i, question in enumerate(test_questions, 1):
#         print(f"\n📋 Test {i}: {question}")
#         print("-" * 30)
#         try:
#             answer = intelligent_stock_advisor(question)
#             print(f"💡 Trả lời: {answer[:200]}...")
#         except Exception as e:
#             print(f"❌ Lỗi: {str(e)}")
    
#     # Interactive mode
#     print("\n" + "="*50)
#     print("🔄 Chế độ tương tác (gõ 'exit' để thoát)")
    
#     while True:
#         user_input = input("\n👤 Câu hỏi của bạn: ")
#         if user_input.lower() == 'exit':
#             break
            
#         try:
#             response = intelligent_stock_advisor(user_input)
#             print(f"\n🤖 Tư vấn: {response}")
#         except Exception as e:
#             print(f"❌ Lỗi: {str(e)}")