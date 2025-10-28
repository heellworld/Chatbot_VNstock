from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
import pandas as pd
import numpy as np
from ....config.database import engine

class StockAnalyzer:
    """Lớp để phân tích dữ liệu chứng khoán từ cơ sở dữ liệu PostgreSQL."""
    
    def __init__(self, engine):
        """
        Khởi tạo lớp StockAnalyzer.
        
        Args:
            engine: SQLAlchemy engine để kết nối đến cơ sở dữ liệu PostgreSQL.
        """
        self.engine = engine
    
    def analyze_stock_price_summary(self, stock_symbol: str, year: Optional[int] = None, 
                                   quarter: Optional[int] = None) -> pd.DataFrame:
        """
        Phân tích tổng hợp giá chứng khoán theo mã.
        
        Args:
            stock_symbol: Mã chứng khoán cần phân tích (ví dụ: 'ACB').
            year: Năm cần phân tích (mặc định là None - lấy tất cả các năm).
            quarter: Quý cần phân tích (mặc định là None - lấy tất cả các quý).
            
        Returns:
            pd.DataFrame: Bảng dữ liệu chứa thông tin tổng hợp giá của mã chứng khoán.
        """
        query = """
        SELECT * FROM vw_StockPriceSummary
        WHERE "StockSymbol" = :stock_symbol
        """
        
        params = {"stock_symbol": stock_symbol}
        
        if year is not None:
            query += ' AND "Year" = :year'
            params["year"] = year
            
        if quarter is not None:
            query += ' AND "Quarter" = :quarter'
            params["quarter"] = quarter
            
        query += ' ORDER BY "Year" DESC, "Month" DESC'
        
        with Session(self.engine) as session:
            result = pd.read_sql(text(query), session.connection(), params=params)
        
        if result.empty:
            print(f"Không tìm thấy dữ liệu phân tích giá cho mã {stock_symbol}")
            return pd.DataFrame()
        
        # Phân tích bổ sung nếu có dữ liệu
        if not result.empty:
            # Tính tỷ lệ biến động giá trung bình theo tháng
            result["PriceVolatility"] = (result["MaxPrice"] - result["MinPrice"]) / result["AvgClosePrice"] * 100
            
            # Xác định tháng có khối lượng giao dịch lớn nhất
            max_volume_month = result.loc[result["TotalVolume"].idxmax()]
            
            # Tính tỷ lệ tăng trưởng tích lũy nếu có nhiều hơn 1 tháng
            if len(result) > 1:
                result = result.sort_values(by=["Year", "Month"])
                first_month_price = result.iloc[0]["MonthStartPrice"]
                last_month_price = result.iloc[-1]["MonthEndPrice"]
                cumulative_growth = (last_month_price - first_month_price) / first_month_price * 100
                print(f"Tăng trưởng tích lũy của {stock_symbol}: {cumulative_growth:.2f}%")
                print(f"Tháng có khối lượng giao dịch lớn nhất: {max_volume_month['Month']}/{max_volume_month['Year']} "
                      f"với {max_volume_month['TotalVolume']:,} cổ phiếu")
        
        return result
    
    def analyze_quarterly_financial_ratios(self, stock_symbol: str, year: Optional[int] = None,
                                         ratio_type: Optional[str] = None) -> pd.DataFrame:
        """
        Phân tích các chỉ số tài chính theo quý của một mã chứng khoán.
        
        Args:
            stock_symbol: Mã chứng khoán cần phân tích (ví dụ: 'ACB').
            year: Năm cần phân tích (mặc định là None - lấy tất cả các năm).
            ratio_type: Loại chỉ số tài chính (ví dụ: 'P/E', 'ROA', 'ROE').
                        Mặc định là None - lấy tất cả các loại.
        
        Returns:
            pd.DataFrame: Bảng dữ liệu chứa các chỉ số tài chính theo quý.
        """
        query = """
        SELECT * FROM vw_QuarterlyFinancialRatios
        WHERE "StockSymbol" = :stock_symbol
        """
        
        params = {"stock_symbol": stock_symbol}
        
        if year is not None:
            query += ' AND "Year" = :year'
            params["year"] = year
            
        if ratio_type is not None:
            query += ' AND "RatioName" = :ratio_type'
            params["ratio_type"] = ratio_type
            
        query += ' ORDER BY "Year" DESC, "Quarter" DESC, "RatioName", "RatioType"'
        
        with Session(self.engine) as session:
            result = pd.read_sql(text(query), session.connection(), params=params)
        
        if result.empty:
            print(f"Không tìm thấy dữ liệu chỉ số tài chính cho mã {stock_symbol}")
            return pd.DataFrame()
        
        # Phân tích bổ sung nếu có dữ liệu
        if not result.empty:
            # Tạo pivot table để dễ dàng phân tích theo thời gian
            pivot_result = result.pivot_table(
                index=["Year", "Quarter"],
                columns=["RatioName"],
                values="RatioValue",
                aggfunc='first'
            ).reset_index()
            
            print(f"Phân tích chỉ số tài chính cho {stock_symbol}:")
            # Nhóm các chỉ số theo loại
            ratios_by_type = result.groupby("RatioName")["RatioType"].unique()
            for r_type, ratios in ratios_by_type.items():
                print(f"\n{r_type} Ratios: {', '.join(ratios)}")
            
            return pivot_result
        
        return result
    
    def analyze_stock_price_movement(self, stock_symbol: str, from_date: Optional[str] = None, 
                                    to_date: Optional[str] = None) -> pd.DataFrame:
        """
        Phân tích biến động giá của một mã chứng khoán dựa trên view vw_StockPriceMovement.
        
        Args:
            stock_symbol: Mã chứng khoán cần phân tích (ví dụ: 'ACB').
            from_date: Ngày bắt đầu phân tích (định dạng 'YYYY-MM-DD'). Mặc định là None.
            to_date: Ngày kết thúc phân tích (định dạng 'YYYY-MM-DD'). Mặc định là None.
            
        Returns:
            pd.DataFrame: Bảng dữ liệu chứa thông tin biến động giá và các chỉ báo bổ sung.
        """
        # Tạo truy vấn SQL để lấy dữ liệu từ view
        query = """
        SELECT * FROM vw_StockPriceMovement
        WHERE "StockSymbol" = :stock_symbol
        """
        
        params = {"stock_symbol": stock_symbol}
        
        # Thêm điều kiện lọc theo ngày nếu có
        if from_date is not None:
            query += ' AND "Date" >= :from_date'
            params["from_date"] = from_date
            
        if to_date is not None:
            query += ' AND "Date" <= :to_date'
            params["to_date"] = to_date
            
        query += ' ORDER BY "Date" DESC'
        
        # Thực thi truy vấn
        with Session(self.engine) as session:
            result = pd.read_sql(text(query), session.connection(), params=params)
        
        # Kiểm tra dữ liệu rỗng
        if result.empty:
            print(f"Không tìm thấy dữ liệu biến động giá cho mã {stock_symbol}")
            return pd.DataFrame()
        
        # Phân tích dữ liệu nếu có
        if not result.empty:
            # Tính các thông số thống kê từ DailyChangePercent
            avg_daily_change = result["DailyChangePercent"].mean()
            std_daily_change = result["DailyChangePercent"].std()
            max_daily_gain = result["DailyChangePercent"].max()
            max_daily_loss = result["DailyChangePercent"].min()
            
            # Đếm số ngày tăng, giảm, không đổi
            days_up = len(result[result["DailyChangePercent"] > 0])
            days_down = len(result[result["DailyChangePercent"] < 0])
            days_unchanged = len(result[result["DailyChangePercent"] == 0])
            
            # In thông tin phân tích
            print(f"Phân tích biến động giá của {stock_symbol}:")
            print(f"Biến động trung bình hàng ngày: {avg_daily_change:.2f}%")
            print(f"Độ biến động (std): {std_daily_change:.2f}%")
            print(f"Tăng mạnh nhất: {max_daily_gain:.2f}%")
            print(f"Giảm mạnh nhất: {max_daily_loss:.2f}%")
            print(f"Số ngày tăng/giảm/đứng giá: {days_up}/{days_down}/{days_unchanged}")
            
            # Sắp xếp theo ngày tăng dần để tính toán các chỉ báo
            result = result.sort_values("Date")
            
            # Tính MA10 và MA30 từ CurrentPrice
            result["MA10"] = result["CurrentPrice"].rolling(window=10, min_periods=1).mean()
            result["MA30"] = result["CurrentPrice"].rolling(window=30, min_periods=1).mean()
            
            # Tạo tín hiệu MA
            result["MA_Signal"] = np.where(result["MA10"] > result["MA30"], "Bullish", "Bearish")
            
            # Tính RSI (14 ngày) từ CurrentPrice
            delta = result["CurrentPrice"].diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            
            avg_gain = gain.rolling(window=14, min_periods=1).mean()
            avg_loss = loss.rolling(window=14, min_periods=1).mean()
            rs = avg_gain / avg_loss
            result["RSI"] = 100 - (100 / (1 + rs))
            
            # Sắp xếp lại theo ngày giảm dần
            result = result.sort_values("Date", ascending=False)
            
            # Phân tích RSI hiện tại
            current_rsi = result["RSI"].iloc[0]
            if not pd.isna(current_rsi):
                print(f"RSI hiện tại: {current_rsi:.2f}")
                if current_rsi > 70:
                    print("Trạng thái: Có thể quá mua (Overbought)")
                elif current_rsi < 30:
                    print("Trạng thái: Có thể quá bán (Oversold)")
                else:
                    print("Trạng thái: Trung tính")
        
        return result
    
    def analyze_vn30_performance(self, stock_symbol: Optional[str] = None, 
                               top_n: int = 5, period: str = 'month') -> pd.DataFrame:
        """
        Phân tích hiệu suất của các mã trong VN30, có thể lọc theo một mã cụ thể.
        
        Args:
            stock_symbol: Mã chứng khoán cần phân tích (mặc định là None - phân tích tất cả VN30).
            top_n: Số lượng mã có hiệu suất tốt nhất cần trả về (mặc định là 5).
            period: Khoảng thời gian phân tích ('month', 'quarter', 'year'). Mặc định là 'month'.
            
        Returns:
            pd.DataFrame: Bảng dữ liệu chứa thông tin hiệu suất của các mã trong VN30.
        """
        # Xác định điều kiện thời gian dựa trên period
        if period == 'month':
            period_clause = 'AND dt."Month" = (SELECT MAX("Month") FROM vw_VN30Performance WHERE "Year" = (SELECT MAX("Year") FROM vw_VN30Performance))'
        elif period == 'quarter':
            period_clause = 'AND dt."Quarter" = (SELECT MAX("Quarter") FROM vw_VN30Performance WHERE "Year" = (SELECT MAX("Year") FROM vw_VN30Performance))'
        elif period == 'year':
            period_clause = 'AND dt."Year" = (SELECT MAX("Year") FROM vw_VN30Performance)'
        else:
            period_clause = ''  # Lấy tất cả dữ liệu
        
        query = f"""
        WITH latest_prices AS (
            SELECT 
                "StockSymbol",
                "Industry",
                "Close" AS "Latest_Close",
                "Date" AS "Latest_Date",
                "YTDReturn",
                "MA10",
                "MA30"
            FROM vw_VN30Performance vp
            JOIN (
                SELECT "StockSymbol", MAX("Date") AS max_date
                FROM vw_VN30Performance
                GROUP BY "StockSymbol"
            ) latest ON vp."StockSymbol" = latest."StockSymbol" AND vp."Date" = latest.max_date
        ),
        period_performance AS (
            SELECT 
                "StockSymbol",
                FIRST_VALUE("Close") OVER (PARTITION BY "StockSymbol" ORDER BY "Date") AS "Period_Start_Price",
                LAST_VALUE("Close") OVER (
                    PARTITION BY "StockSymbol" 
                    ORDER BY "Date"
                    RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                ) AS "Period_End_Price",
                SUM("Volume") OVER (PARTITION BY "StockSymbol") AS "Total_Period_Volume",
                COUNT(*) OVER (PARTITION BY "StockSymbol") AS "Trading_Days",
                COUNT(*) FILTER (WHERE "DailyReturn" > 0) OVER (PARTITION BY "StockSymbol") AS "Up_Days",
                COUNT(*) FILTER (WHERE "DailyReturn" < 0) OVER (PARTITION BY "StockSymbol") AS "Down_Days",
                AVG("DailyReturn") OVER (PARTITION BY "StockSymbol") AS "Avg_Daily_Return",
                STDDEV("DailyReturn") OVER (PARTITION BY "StockSymbol") AS "Return_StdDev"
            FROM vw_VN30Performance vp
            WHERE 1=1 {period_clause}
        )
        SELECT 
            pp."StockSymbol",
            lp."Industry",
            lp."Latest_Close",
            lp."Latest_Date",
            pp."Period_Start_Price",
            pp."Period_End_Price",
            ROUND(
                (pp."Period_End_Price" - pp."Period_Start_Price") / 
                NULLIF(pp."Period_Start_Price", 0) * 100, 
                2
            ) AS "Period_Return_Percent",
            pp."Total_Period_Volume",
            pp."Trading_Days",
            pp."Up_Days",
            pp."Down_Days",
            ROUND(pp."Avg_Daily_Return", 2) AS "Avg_Daily_Return",
            ROUND(pp."Return_StdDev", 2) AS "Return_StdDev",
            ROUND(
                pp."Avg_Daily_Return" / NULLIF(pp."Return_StdDev", 0), 
                4
            ) AS "Sharpe_Ratio",
            lp."YTDReturn",
            CASE 
                WHEN lp."MA10" > lp."MA30" THEN 'Bullish'
                WHEN lp."MA10" < lp."MA30" THEN 'Bearish'
                ELSE 'Neutral'
            END AS "Trend"
        FROM 
            period_performance pp
        JOIN 
            latest_prices lp ON pp."StockSymbol" = lp."StockSymbol"
        """
        
        params = {}
        
        if stock_symbol is not None:
            query += ' WHERE pp."StockSymbol" = :stock_symbol'
            params["stock_symbol"] = stock_symbol
        else:
            query += ' ORDER BY "Period_Return_Percent" DESC LIMIT :top_n'
            params["top_n"] = top_n
        
        with Session(self.engine) as session:
            result = pd.read_sql(text(query), session.connection(), params=params)
        
        if result.empty:
            print(f"Không tìm thấy dữ liệu hiệu suất VN30")
            return pd.DataFrame()
        
        # Phân tích bổ sung nếu có dữ liệu
        if not result.empty:
            print(f"Phân tích hiệu suất VN30{' cho ' + stock_symbol if stock_symbol else ''}:")
            avg_return = result["Period_Return_Percent"].mean()
            print(f"Hiệu suất trung bình: {avg_return:.2f}%")
            
            if stock_symbol:
                stock_data = result.iloc[0]
                print(f"Hiệu suất của {stock_symbol} trong kỳ: {stock_data['Period_Return_Percent']:.2f}%")
                print(f"Tỷ lệ ngày tăng/giảm: {stock_data['Up_Days']}/{stock_data['Down_Days']}")
                print(f"Xu hướng hiện tại: {stock_data['Trend']}")
                print(f"Ngành: {stock_data['Industry']}")
            else:
                industry_performance = result.groupby("Industry")["Period_Return_Percent"].mean().sort_values(ascending=False)
                print("\nHiệu suất theo ngành:")
                for industry, perf in industry_performance.items():
                    print(f"{industry}: {perf:.2f}%")
        
        return result


# # Ví dụ sử dụng:
# if __name__ == "__main__":
#     # # Phân tích tổng hợp giá chứng khoán ACB
#     # price_summary = analyze_stock_price_summary("ACB", 2025, 2)
#     # print(price_summary)
    # analyzer = StockAnalyzer(engine)
    # # Phân tích chỉ số tài chính của ACB năm 2023
    # financial_ratios = analyzer.analyze_quarterly_financial_ratios("FPT", 2025, "P/E")
    # print(financial_ratios)

#     # Phân tích biến động giá của ACB
#     price_movement = analyze_stock_price_movement("ACB", from_date="2025-04-01", to_date="2025-04-10")
#     print(price_movement)    

#     # # Phân tích hiệu suất của ACB trong VN30
#     # vn30_performance = analyze_vn30_performance("ACB")
#     # print(vn30_performance)

#     # # Phân tích top 5 mã có hiệu suất tốt nhất trong VN30 tháng gần nhất
#     # top_performers = analyze_vn30_performance(top_n=5, period="month")
#     # print(top_performers)
