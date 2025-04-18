import requests
import yfinance as yf
import praw 
from datetime import datetime,timedelta
import pandas as pd


def get_stock_price(symbol):
    """
    주어진 주식 심볼의 최신 종가를 반환하는 함수

    :param symbol: 주식 심볼 (예: 'AAPL' for Apple Inc.)
    :return: 소수점 둘째 자리까지 반올림된 최신 종가
    """
    ticker = yf.Ticker(symbol)
    todays_data = ticker.history(period='1d')
    return round(todays_data['Close'].iloc[0], 2)

def query_openai_model(client, system_prompt, messages):
    tool_check = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,)
    tool_check_messege = tool_check.choices[0].message
    if tool_check_messege.tool_calls:
        tool_call = tool_check.choices[0].message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        name = tool_call.function.name
        result = call_function(name, args)
        tool_chatmessage = messages + [tool_check.choices[0].message]
        # append model's function call message
        tool_chatmessage.append({                               # append result message
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": str(result)
        })
        
        stream = client.chat.completions.create(
            model="gpt-4o",
            messages=tool_chatmessage,
            stream=True
        )
    else:

        full_messages = [{"role": "system", "content": system_prompt}] + messages
        stream = client.chat.completions.create(
            model="gpt-4o",
            messages=full_messages,
            stream=True
        )
    return stream

def get_reddit_issues_summarized(keyword ,days):
    redditid = 'mOOCYGbbZZ7_n-x6TucUwQ'
    reddit_pw = '2A3xDNKgeB4ld6wOEUfqOPsObU9WLw'
    
    # Reddit API 인증
    reddit = praw.Reddit(
        client_id=redditid, 
        client_secret=reddit_pw, 
        user_agent='test'
    )
    
    
    daysago = datetime.utcnow() - timedelta(days=days)
    subreddit = reddit.subreddit('wallstreetbets')
    
    posts_data = []
    
    for post in subreddit.search(keyword, sort='hot', limit=500):  # 최근 500개 게시글 확인
        post_date = datetime.utcfromtimestamp(post.created_utc)
        if post_date >= daysago:
            posts_data.append(
                'title :'+ post.title+'\n'+
                'body :' + post.selftext)
    titleandbody = '\n\n'.join(posts_data)

    return titleandbody

def get_reddit_hotissue(days):
    redditid = 'mOOCYGbbZZ7_n-x6TucUwQ'
    reddit_pw = '2A3xDNKgeB4ld6wOEUfqOPsObU9WLw'
    
    # Reddit API 인증
    reddit = praw.Reddit(
        client_id=redditid, 
        client_secret=reddit_pw, 
        user_agent='test'
    )
    
    
    daysago = datetime.utcnow() - timedelta(days=days)
    subreddit = reddit.subreddit('wallstreetbets')
    
    posts_data = []
    for post in subreddit.hot(limit=500):
        post_date = datetime.utcfromtimestamp(post.created_utc)
        if post_date >= daysago:
            posts_data.append(
                'title :'+ post.title+'\n'+
                'body :' + post.selftext)
    titleandbody = '\n\n'.join(posts_data)

    return titleandbody

def get_consensus(symbol , year, quarter):

    api_key = 'd92779aed523de914055c6b543801a73'
    consensus_url = f'https://financialmodelingprep.com/api/v3/earnings-surprises/{symbol}?apikey={api_key}'
    consensus_response = requests.get(consensus_url).json()
    if quarter =='-1':
        return json.dumps(consensus_response[0])
    for consensus in consensus_response:
        consensus['year'] =consensus['date'][:4]
        if consensus['date'][5:7] == '05':
            consensus['quarter'] = '1'
        elif consensus['date'][5:7] == '08':
             consensus['quarter'] = '2'
        elif consensus['date'][5:7] == '11' or consensus['date'][5:7] == '10' :
             consensus['quarter'] = '3'
        elif consensus['date'][5:7] == '02':
             consensus['quarter'] = '4'
             consensus['year'] = str(int(year) -1)
            
        consensus['EPS_surprise'] = ((consensus['actualEarningResult'] - consensus['estimatedEarning']) / 
                                           consensus['estimatedEarning']) * 100
        

    year_consensus = [a for a in consensus_response if a['year']==year ]
    if year_consensus:
        if quarter =='-1':
            return json.dumps(year_consensus[-1])
        else:
            
            year_quarter_consensus = [a for a in year_consensus if a['quarter'] == quarter][0]
            return json.dumps(
                year_quarter_consensus
            )
    else:
        return '컨센서스 데이터를 찾을수 없습니다.'
        
def get_earnings(symbol, type_ ,year, quarter, analysis_type):
    financial_columns = {
    "financial_analysis": [
        "Net Income", "Stockholders Equity", "Total Assets",
        "Operating Income", "Total Revenue"
    ],
    "growth_analysis": [
        "Total Revenue", "revenue_growth_QoQ", "Net Income",
        "net_income_growth_QoQ", "EBITDA"
    ],
    "stock_price_analysis": [
        "eps", "Basic EPS", "pe_ratio", "pb_ratio", "bvps"
    ],
    "quarterly_earnings": [
        "Operating Income", "Net Income",
        "revenue_growth_QoQ", "net_income_growth_QoQ"
    ],
    "stock_price_volatility": [
        "pe_ratio"
    ],
    "return_analysis": [
        "Diluted EPS", "Net Income"
    ],
    "earnings_forecast": [
        "eps", "net_income_growth_QoQ", "Net Income",
        "Basic Average Shares"
    ],
    "debt_ratios": [
        "Total Liabilities Net Minority Interest",
        "Stockholders Equity", "Total Assets"
    ],
    "cash_flow_analysis": [
        "Cash And Cash Equivalents", "Net PPE", "Cash Equivalents"
    ],
    "revenue_sources": [
        "Cost Of Revenue", "Total Revenue", "Operating Income"
    ],
    "interest_coverage_ratio": [
        "EBIT", "Interest Expense"
        ]
    }
    
    

    ticker = yf.Ticker(symbol)
    
    # 주가 데이터 가져오기
    current_price = ticker.history(period="1d")["Close"].iloc[-1]
    
    # 재무제표 가져오기
    balance_sheet = ticker.balance_sheet
    income_statement = ticker.financials
    
    earnings = pd.concat([balance_sheet,income_statement]).T
    # 데이터프레임 출력
    
    earnings_df = earnings.reset_index()
    earnings_df = earnings_df.rename(columns={'index':'date'})
    earnings_df['date'] = pd.to_datetime(earnings_df['date']).dt.strftime('%Y-%m-%d')
    
    earnings_df['revenue_growth_QoQ'] = earnings_df['Total Revenue'].pct_change(-1) * 100
    earnings_df['net_income_growth_QoQ'] = earnings_df['Operating Income'].pct_change(-1) * 100
    earnings_df['operating_margin'] = (earnings_df['Operating Income'] / earnings_df['Total Revenue']) * 100
    earnings_df['net_margin'] = (earnings_df['Net Income'] / earnings_df['Total Revenue']) * 100
    
    # 주식 정보 및 주요 재무 비율 계산
    shares_outstanding = ticker.info["sharesOutstanding"]
    total_assets = balance_sheet.loc["Total Assets"]
    total_liabilities = balance_sheet.loc["Total Liabilities Net Minority Interest"]
    net_income = income_statement.loc["Net Income"]

    book_value = total_assets - total_liabilities 
    eps = net_income / shares_outstanding  # 주당순이익
    pe_ratio = current_price / eps  # PER
    bvps = book_value / shares_outstanding  # 주당순자산가치
    pb_ratio = current_price / bvps  # PBR
    roe = (net_income / book_value) * 100  # ROE
    roa = (net_income / total_assets) * 100  # ROA
    debt_to_equity_ratio = total_liabilities / book_value  # 부채비율
    
    
    
list(total_assets - total_liabilities)
    earnings_df['book_value'] = book_value
    eps = net_income / shares_outstanding
    earnings_df['eps']  = list(eps)
    earnings_df['pe_ratio'] = list(current_price / eps)
    earnings_df['bvps'] = list(book_value / shares_outstanding)
    earnings_df['pb_ratio']  = list(current_price / bvps)
    earnings_df['roe'] = list((net_income / book_value) * 100)
    earnings_df['roa'] = list((net_income / total_assets) * 100)
    earnings_df['debt_to_equity_ratio'] = list(total_liabilities / book_value)

    if analysis_type in financial_columns.keys():
        column_names = financial_columns[analysis_type]
        earnings_df = earnings_df[column_names]

    earnings_dict = earnings_df.to_dict('records')


    if quarter =='-1':
        return json.dumps(earnings_dict[0])
    else:
        year_earnings = [a for a in earnings_dict if a['date'][:4] == year]
        if not year_earnings:
            return json.dumps(earnings_dict)
        for each in year_earnings:
            if each['date'][5:7] =='03':
                each['quarter'] ='1'
            if each['date'][5:7] =='06':
                each['quarter'] ='2'
            if each['date'][5:7] =='09':
                each['quarter'] ='3'
            if each['date'][5:7] =='12':
                each['quarter'] ='4'
        quarter_earning = [a for a in year_earnings if a['quarter'] == quarter]
        if quarter_earning:
            return json.dumps(quarter_earning)
        else:
            return json.dumps(year_earnings)
            
        
def call_function(name, args):
    if name == "get_reddit_issues_summarized":
        return get_reddit_issues_summarized(**args)
    if name == "get_reddit_hotissue":
        return get_reddit_hotissue(**args)
    if name == "get_consensus":
        return get_consensus(**args)
    if name == "get_earnings":
        return get_earnings(**args)
