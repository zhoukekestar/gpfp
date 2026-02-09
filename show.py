import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import akshare as ak
from datetime import datetime

# 设置中文字体支持
matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'STHeiti']
matplotlib.rcParams['axes.unicode_minus'] = False


df_2025 = pd.read_excel("./datasets/eq_20251231.xlsx")
df_2024 = pd.read_excel("./datasets/eq_20241231.xlsx")
df_2023 = pd.read_excel("./datasets/eq_20231231.xlsx")
df_2022 = pd.read_excel("./datasets/eq_20221231.xlsx")
df_2021 = pd.read_excel("./datasets/eq_20211231.xlsx")
df_2020 = pd.read_excel("./datasets/eq_20201231.xlsx")
df_2019 = pd.read_excel("./datasets/eq_20191231.xlsx")
df_2018 = pd.read_excel("./datasets/eq_20181231.xlsx")
df_2017 = pd.read_excel("./datasets/eq_20171231.xlsx")
df_2016 = pd.read_excel("./datasets/eq_20161231.xlsx")
df_2015 = pd.read_excel("./datasets/eq_20151231.xlsx")

df_2025['year'] = 2025
df_2024['year'] = 2024
df_2023['year'] = 2023
df_2022['year'] = 2022
df_2021['year'] = 2021
df_2020['year'] = 2020
df_2019['year'] = 2019
df_2018['year'] = 2018
df_2017['year'] = 2017
df_2016['year'] = 2016
df_2015['year'] = 2015

df = pd.concat([
    df_2025,
    df_2024,
    df_2023,
    df_2022,
    df_2021,
    df_2020,
    df_2019,
    df_2018,
    df_2017,
    df_2016,
    df_2015,
])

def get_stock_price_data(ticker, start_date="20150101", end_date="20251231", max_retries=3):
    """
    获取股票每年最后一个交易日的收盘价
    
    参数:
        ticker: 股票代码（如腾讯 "00700"）
        start_date: 开始日期 (YYYYMMDD格式)
        end_date: 结束日期 (YYYYMMDD格式)
        max_retries: 最大重试次数
    
    返回:
        DataFrame 包含年份和收盘价
    """
    import time
    
    for attempt in range(max_retries):
        try:
            print(f"正在获取股票 {ticker} 的数据... (尝试 {attempt + 1}/{max_retries})")
            stock_data = ak.stock_hk_hist(symbol=ticker, period="monthly", 
                                          start_date=start_date, end_date=end_date, 
                                          adjust="qfq")
            
            if stock_data is None or stock_data.empty:
                print(f"股票 {ticker} 返回空数据")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return None
            
            stock_data['日期'] = pd.to_datetime(stock_data['日期'])
            stock_data.set_index('日期', inplace=True)
            
            # 获取每年最后一个交易日的数据
            yearly_last_day = stock_data.resample('YE').last()
            yearly_last_day['year'] = yearly_last_day.index.year
            
            result = yearly_last_day[['year', '收盘']].reset_index(drop=True)
            print(f"成功获取股票 {ticker} 的数据！")
            return result
            
        except Exception as e:
            print(f"获取股票数据失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print(f"等待 3 秒后重试...")
                time.sleep(3)
            else:
                print(f"已达到最大重试次数，放弃获取股票 {ticker} 的数据")
                return None


def plot_ownership_trend_enhanced(df, company_name, stock_ticker=None, figsize=(16, 10)):
    """
    绘制公司持股比例、市值、股票价格和持股数量的叠加趋势图
    
    参数:
        df: 主数据框（包含 Name, year, Ownership, Market Value(USD) 等列）
        company_name: 公司名称
        stock_ticker: 股票代码（可选，用于获取股价数据计算持股数量）
        figsize: 图表大小
    """
    company_data = df[df['Name'] == company_name]
    
    if company_data.empty:
        print(f"未找到公司: {company_name}")
        return
    
    company_data_sorted = company_data.sort_values('year')
    
    # 如果提供了股票代码，获取股价数据并计算持股数量
    stock_quantity_data = None
    if stock_ticker:
        stock_price_data = get_stock_price_data(stock_ticker)
        if stock_price_data is not None:
            merged_data = company_data_sorted.merge(
                stock_price_data, 
                on='year', 
                how='inner'
            )
            # 计算持股数量（百万股）
            merged_data['股票数量_百万股'] = merged_data['Market Value(USD)'] / merged_data['收盘']
            stock_quantity_data = merged_data
    
    # 创建图表 - 使用2x1子图布局
    fig = plt.figure(figsize=figsize)
    gs = fig.add_gridspec(2, 1, height_ratios=[3, 2], hspace=0.3)
    
    # ========== 上半部分：持股比例和市值 ==========
    ax1 = fig.add_subplot(gs[0])
    
    # 第一个Y轴：持股比例
    color1 = '#1f77b4'
    ax1.set_ylabel('持股比例 (%)', fontsize=12, fontweight='bold', color=color1)
    line1 = ax1.plot(company_data_sorted['year'], company_data_sorted['Ownership'], 
                     marker='o', linewidth=2.5, markersize=8, color=color1, 
                     label='持股比例', zorder=3)
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, alpha=0.3, zorder=0)
    
    # 在持股比例上标注数值
    for _, row in company_data_sorted.iterrows():
        ax1.annotate(f"{row['Ownership']:.3f}%", 
                     xy=(row['year'], row['Ownership']),
                     xytext=(0, 10), textcoords='offset points',
                     ha='center', fontsize=8, color=color1, fontweight='bold')
    
    # 第二个Y轴：市值
    ax2 = ax1.twinx()
    color2 = '#ff7f0e'
    ax2.set_ylabel('市值 (USD 百万)', fontsize=12, fontweight='bold', color=color2)
    line2 = ax2.plot(company_data_sorted['year'], company_data_sorted['Market Value(USD)'], 
                     marker='s', linewidth=2.5, markersize=8, color=color2, 
                     label='市值', zorder=2)
    ax2.tick_params(axis='y', labelcolor=color2)
    
    # 在市值上标注数值
    for _, row in company_data_sorted.iterrows():
        ax2.annotate(f"${row['Market Value(USD)']:.0f}M", 
                     xy=(row['year'], row['Market Value(USD)']),
                     xytext=(0, -20), textcoords='offset points',
                     ha='center', fontsize=8, color=color2, fontweight='bold')
    
    # 合并图例
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left', fontsize=10, framealpha=0.9)
    
    # 设置X轴
    ax1.set_xticks(company_data_sorted['year'])
    ax1.set_xticklabels([])
    
    # ========== 下半部分：股票价格和持股数量 ==========
    if stock_quantity_data is not None:
        ax3 = fig.add_subplot(gs[1])
        
        # 第三个Y轴：股票价格
        color3 = '#d62728'
        ax3.set_xlabel('年份', fontsize=12, fontweight='bold')
        ax3.set_ylabel('股票价格 (HKD)', fontsize=12, fontweight='bold', color=color3)
        line3 = ax3.plot(stock_quantity_data['year'], stock_quantity_data['收盘'], 
                         marker='D', linewidth=2.5, markersize=8, color=color3, 
                         label='股票价格', zorder=3)
        ax3.tick_params(axis='y', labelcolor=color3)
        ax3.grid(True, alpha=0.3, zorder=0)
        
        # 在股票价格上标注数值
        for _, row in stock_quantity_data.iterrows():
            ax3.annotate(f"¥{row['收盘']:.2f}", 
                         xy=(row['year'], row['收盘']),
                         xytext=(0, 10), textcoords='offset points',
                         ha='center', fontsize=8, color=color3, fontweight='bold')
        
        # 第四个Y轴：持股数量
        ax4 = ax3.twinx()
        color4 = '#2ca02c'
        ax4.set_ylabel('持股数量 (百万股)', fontsize=12, fontweight='bold', color=color4)
        line4 = ax4.plot(stock_quantity_data['year'], stock_quantity_data['股票数量_百万股'], 
                         marker='^', linewidth=2.5, markersize=8, color=color4, 
                         label='持股数量', zorder=2)
        ax4.tick_params(axis='y', labelcolor=color4)
        
        # 在持股数量上标注数值
        for _, row in stock_quantity_data.iterrows():
            ax4.annotate(f"{row['股票数量_百万股']:.1f}M", 
                         xy=(row['year'], row['股票数量_百万股']),
                         xytext=(0, -20), textcoords='offset points',
                         ha='center', fontsize=8, color=color4, fontweight='bold')
        
        # 合并图例
        lines_bottom = line3 + line4
        labels_bottom = [l.get_label() for l in lines_bottom]
        ax3.legend(lines_bottom, labels_bottom, loc='upper left', fontsize=10, framealpha=0.9)
        
        # 设置X轴
        ax3.set_xticks(stock_quantity_data['year'])
        ax3.set_xticklabels(stock_quantity_data['year'].astype(int))
    else:
        # 如果没有股价数据，只显示上半部分
        ax1.set_xlabel('年份', fontsize=12, fontweight='bold')
        ax1.set_xticklabels(company_data_sorted['year'].astype(int))
    
    # 设置总标题
    fig.suptitle(f'GPFG 持有{company_name}投资分析 (2015-2025)', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    plt.show()
    
    # 打印详细数据表
    print(f"\n{'='*100}")
    print(f"GPFG 持有{company_name}详细数据")
    print(f"{'='*100}")
    
    if stock_quantity_data is not None:
        print(f"{'年份':<8} {'持股比例(%)':<15} {'市值(USD M)':<18} {'股价(HKD)':<15} {'持股数量(M股)':<15}")
        print(f"{'-'*100}")
        for _, row in stock_quantity_data.iterrows():
            print(f"{int(row['year']):<8} {row['Ownership']:<15.4f} {row['Market Value(USD)']:<18.0f} "
                  f"{row['收盘']:<15.2f} {row['股票数量_百万股']:<15.2f}")
    else:
        print(f"{'年份':<8} {'持股比例(%)':<15} {'市值(USD M)':<18}")
        print(f"{'-'*100}")
        for _, row in company_data_sorted.iterrows():
            print(f"{int(row['year']):<8} {row['Ownership']:<15.4f} {row['Market Value(USD)']:<18.0f}")
    
    print(f"{'='*100}\n")



# ============================================================================
# 批量绘制所有重点公司的投资分析图表
# ============================================================================
# 定义公司列表及其股票代码（港股/A股）
companies_with_tickers = [
    ('Tencent Holdings Ltd', '00700'),  # 腾讯控股
    # ('Alibaba Group Holding Ltd', '09988'),  # 阿里巴巴
    # ('PDD Holdings Inc', None),  # 拼多多（美股）
    # ('Ping An Insurance Group Co of China Ltd', '02318'),  # 平安保险
    # ('Xiaomi Corp', '01810'),  # 小米集团
    # ('China Construction Bank Corp', '00939'),  # 建设银行
    # ('Meituan', '03690'),  # 美团
    # ('Contemporary Amperex Technology Co Ltd', None),  # 宁德时代（A股）
    # ('Industrial & Commercial Bank of China Ltd', '01398'),  # 工商银行
    # ('Trip.com Group Ltd', '09961'),  # 携程
    # ('NAURA Technology Group Co Ltd', None),  # 北方华创（A股）
    # ('Pop Mart International Group Ltd', '09992'),  # 泡玛特
    # ('NetEase Inc', '09999'),  # 网易
    # ('Luxshare Precision Industry Co Ltd', None),  # 立讯精密（A股）
    # ('BYD Co Ltd', '01211'),  # 比亚迪
    # ('China Merchants Bank Co Ltd', '03968'),  # 招商银行
    # ('New Oriental Education & Technology Group Inc', '09901'),  # 新东方
    # ('Baidu Inc', '09888'),  # 百度
    # ('Bank of China Ltd', '03988'),  # 中国银行
    # ('Full Truck Alliance Co Ltd', '02777'),  # 满帮
    # ('Bilibili Inc', '09626'),  # 哔哩哔哩
    # ('Giant Network Group Co Ltd', None),  # 巨人网络（A股）
    # ('JD.com Inc', '09618'),  # 京东
    # ('BeOne Medicines Ltd', None),  # BeOne Medicines
    # ('China Pacific Insurance Group Co Ltd', '02601'),  # 中国太保
    # ('Midea Group Co Ltd', None),  # 美的集团（A股）
    # ('Ningbo Deye Technology Co Ltd', None),  # 德业股份（A股）
    # ('China Life Insurance Co Ltd', '02628'),  # 中国人寿
    # ('Yum China Holdings Inc', None),  # 百胜中国（美股）
]

for (company, stock) in companies_with_tickers:
    plot_ownership_trend_enhanced(df, company_name=company, stock_ticker=stock)

