import pandas as pd
import fitz
import io
import time
import json
import os
import urllib.request
import praw
from datetime import datetime, timedelta
import yfinance as yf
import requests
from transformers import AutoTokenizer
import json
import re
import string
from vllm import LLM, SamplingParams
import streamlit as st

model_id = 'irene93/functioncall_stkissue'
llm = LLM(model=model_id)
tokenizer = AutoTokenizer.from_pretrained(model_id)



tools = [{"type": "function",
       "function":   {
        "name":'get_earnings',
        "description":'당신은 기업의 실적, 재무재표 또는 현금흐름을 가져오고 분석하는 로봇입니다.',
        'parameters':{
            "type":"object",
            "properties" :{
                "symbol":{'type':'string', "description": '실적 데이터를 찾고자 하는 기업의 symbol'},
                'analysis_type':{'type':'string', "description":"""기업의 재무 데이터에서 어떤 정보를 추출하고자 하는지 출력하는 파라미터입니다.
                매출 성장률, 순이익 성장률, 영업이익 성장률 과 같은 기업의 성장성을 요청할경우 'growth'라고 출력,
                얼마나 효율적으로 이익을 창출하는지 수익성과 관련한 질문일경우 'profitability' 출력,
                부채 수준과 재무 건전성과 관련한 질문일경우 'stability' 출력,
                현재 가치와 적정 주가와 관련한 질문일경우 'valuation' 출력,
                현금을 얼마나 잘 창출하는지 확인하여 재무건전성과 관련한 질문일경우 'cashflow' 출력,
                배당 정책과 주식 발행 내역과 관련한 질문일경우 'dividend' 출력,
                비용 절감 능력과 효율성과 관련한 질문일경우 'cost' 출력,
                그외의 재무,실적,현금흐름과 연관이있지만 파라미터를 찾을수없는경우 'NA'라고 출력합니다.

                """},
                "type_":{'type':'string', "description": "연간 데이터 일경우 'yearly' 아닐경우 'quarter' 이라고 표기"},
                "year":{'type':'string', "description": '데이터를 찾고자 하는 연도, 명시 하지 않을경우 가장 최근 연도 로 설정, 1월일경우 , 해당연도에 데이터가 입력되지않을수있음 따라서 최근연도-1 값을 연도라고 표기 '},
                "quarter":{'type':'string', "description": '데이터를 찾고자 하는 분기로 1~4로 이루어진 숫자, 마지막 또는 최근 분기일경우 또는 언급이 없을경우 -1 이라고 표기 '}
            },
            "required":['symbol', 'analysis_type','type_', 'year','quarter'],
            "additionalProperties": False
        },
             "strict": True
    }},
         {"type": "function",
       "function":   {
        "name":'get_consensus',
        "description":'당신은 기업의 (EPS) 컨센서스 데이터 또는, 매수/매도/홀드 의견 목표주가를 가져와서 분석하는 로봇입니다.',
        'parameters':{
            "type":"object",
            "properties" :{
                "symbol":{'type':'string', "description": ' 데이터를 찾고자 하는 기업의 symbol'},
                "year":{'type':'string', "description": '데이터를 찾고자 하는 연도, 명시 하지 않을경우 가장 최근 연도 로 설정, 1월일경우 , 해당연도에 데이터가 입력되지않을수있음 따라서 최근연도-1 값을 연도라고 표기 '},
                "quarter":{'type':'string', "description": '데이터를 찾고자 하는 분기로 1~4로 이루어진 숫자, 최근 또는 마지막일경우 -1 이라고 표기 '}
            },
            "required":['symbol', 'year','quarter'],
            "additionalProperties": False
        },
             "strict": True
    }},
        {"type": "function",
         "function":    {
        "name":'get_issues_summarized',
        "description":'당신은 특정 기업 또는 키워드의 이슈검색 챗봇입니다.',
        'parameters':{
            "type":"object",
            "properties" :{
                "keyword":{'type':'string', "description": '이슈/현황을 검색하고자 하는 회사명 또는 키워드 in English '},
                "days":{'type':'integer', "description": '검색하고자 하는 기간 예시: 하루, 일주일, 한달, 등등'}

            },
            "required":['keyword','days'],
            "additionalProperties": False
        },
             "strict": True
        }
    },
    {"type": "function",
       "function":   {
        "name":'get_reddit_hotissue',
        "description":'당신은 (금융)시장에서 핫한 이슈를 요약하는 챗봇입니다.',
        'parameters':{
            "type":"object",
            "properties" :{
                "days":{'type':'integer', "description": '검색하고자 하는 기간 예시: 하루, 일주일, 한달,일년 등 **질문에 언급이 없을경우 일주일로 지정'}

            },
            "required":['days'],
            "additionalProperties": False
        },
             "strict": True
    }}]


def get_issues_summarized(keyword ,days):
    redditid = 'mOOCYGbbZZ7_n-x6TucUwQ'
    reddit_pw = '2A3xDNKgeB4ld6wOEUfqOPsObU9WLw'

    # Reddit API 인증
    reddit = praw.Reddit(
        client_id=redditid,
        client_secret=reddit_pw,
        user_agent='test'
    )


    daysago = datetime.utcnow() - timedelta(days=7)
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
    ticker = yf.Ticker(symbol)
    # 목표주가
    try:
        target_price = ticker.analyst_price_targets
        # buysell = ticker.recommendations
    except:
        target_price='cannot get target price'
        # buysell = 'cannot get recommendations'
    api_key = 'd92779aed523de914055c6b543801a73'
    consensus_url = f'https://financialmodelingprep.com/api/v3/earnings-surprises/{symbol}?apikey={api_key}'
    consensus_response = requests.get(consensus_url).json()

    for consensus in consensus_response:
        consensus['year'] =consensus['date'][:4]
        consensus['EPS_surprise'] = ((consensus['actualEarningResult'] - consensus['estimatedEarning']) /
                                           consensus['estimatedEarning']) * 100


    year_consensus = [a for a in consensus_response if a['year']==year or a['year']==str(int(year)-1)   or a['year']==str(int(year)+1 ) ]
    if year_consensus:
        if quarter =='-1':
            result = [year_consensus[0]]
        else:
            result =  year_consensus
    else:

        result = consensus_response
    if not consensus_response:
        return '컨센서스 데이터를 찾을수 없습니다.'

    result.append({'target_price':target_price})
    return json.dumps(result)
    # return result

def get_earnings(symbol, analysis_type,type_,year, quarter):
    ticker = yf.Ticker(symbol)
    # 주가 데이터 가져오기
    try:
        current_price = ticker.history(period="1d")["Close"].iloc[-1]
    except:
        current_price= 'currently cannot get current price'

    # 재무제표 가져오기
    if type_=='yearly':
        balance_sheet = ticker.balance_sheet
        income_statement = ticker.financials
        cash_flow = ticker.cashflow  # 현금흐름표 가져오기
    else:
        balance_sheet = ticker.quarterly_balance_sheet
        income_statement = ticker.quarterly_financials
        cash_flow = ticker.quarterly_cashflow  # 현금흐름표 가져오기


    earnings = pd.concat([balance_sheet,income_statement])
    earnings = pd.concat([earnings, cash_flow])
    if earnings.empty :
        return "해당 기업의 재무 정보를 찾을수 없습니다."
    total_debt = earnings.T['Total Debt'] if 'Total Debt' in earnings.T.columns else 'None'
    net_debt =  earnings.T['Net Debt'] if 'Net Debt' in earnings.T.columns else 'None'
    total_liabilities = earnings.loc["Total Liabilities Net Minority Interest"].iloc[0]  # 총부채

    # growth 분석
    try:
        total_revenue = earnings.loc["Total Revenue"]
        net_income = earnings.loc["Net Income"]
        revenue_growth_QoQ = ((total_revenue.iloc[0] - total_revenue.iloc[1]) / total_revenue.iloc[1]) * 100  # 매출 성장률 QoQ
        net_income_growth_QoQ = ((net_income.iloc[0] - net_income.iloc[1]) / net_income.iloc[1]) * 100  # 순이익 성장률 QoQ
        normalized_ebitda = float(earnings.loc['Normalized EBITDA'].iloc[0])
        total_assets = float(earnings.loc['Total Assets'].iloc[0])
        invested_capital = float(earnings.loc['Invested Capital'].iloc[0])
        # Variables defined separately
        if analysis_type == 'growth':
            result_dic = {'revenue_growth_QoQ': revenue_growth_QoQ, 'net_income_growth_QoQ': net_income_growth_QoQ,'normalized_ebitda' : normalized_ebitda,'total_assets' : total_assets,'invested_capital':invested_capital}

        # 수익성 (profitability)


        elif analysis_type=='profitability':
            total_revenue = earnings.loc["Total Revenue"]
            gross_profit = earnings.loc['Gross Profit']
            gross_margin = gross_profit/total_revenue
            net_income = earnings.loc["Net Income"]
            net_margin = (net_income.iloc[0] / total_revenue.iloc[0]) * 100  # 순이익률
            stockholders_equity = earnings.loc["Stockholders Equity"].iloc[0]  # 자기자본
            total_assets = earnings.loc['Total Assets']
            roe = (net_income.iloc[0] / stockholders_equity) * 100  # ROE
            roa = (net_income.iloc[0] / total_assets) * 100  # ROA

            EBITDA = earnings.loc['EBITDA']
            EBITDA_margin = EBITDA/total_revenue

            result_dic = {'total_revenue': total_revenue, 'gross_profit': gross_profit,'gross_margin' : gross_margin,'net_income' : net_income,
                          'net_margin':net_margin, 'stockholders_equity':stockholders_equity,'total_assets':total_assets,'roe':roe,'roa':roa,
                         'EBITDA':EBITDA, 'EBITDA_margin':EBITDA_margin}



        elif analysis_type=='stability':
                  ## financial_stability 재무안정성
            debt_to_equity_ratio = total_liabilities / stockholders_equity  # 부채비율

            current_assets = earnings.loc['Current Assets']
            current_liabilities = earnings.loc['Current Liabilities'] # Current Assets / Current Liabilities 유동비율 계산 가능
            inventory = earnings.loc['Inventory'] if  'Inventory' in earnings.T.columns else 0  # (Current Assets - Inventory) / Current Liabilities 당좌 비율
            # (Current Assets - Inventory) / Current Liabilities 당좌 비율
            result_dic = {'debt_to_equity_ratio': debt_to_equity_ratio, 'total_debt': total_debt,'net_debt' : net_debt,
                          'current_assets' : current_assets,
                          'current_liabilities':current_liabilities, 'inventory':inventory}


        # valuation 분석

        # 주식 관련 정보 가져오기

        elif analysis_type=='valuation':
            shares_outstanding = ticker.info["sharesOutstanding"]  # 발행 주식 수
            net_income = income_statement.loc["Net Income"]
            total_assets = earnings.loc["Total Assets"].iloc[0]  # 총자산
            total_liabilities = earnings.loc["Total Liabilities Net Minority Interest"].iloc[0]  # 총부채
            book_value = total_assets - total_liabilities  # 순자산
            eps = net_income.iloc[0] / shares_outstanding  # 주당순이익 (EPS)
            pe_ratio = current_price / eps  # PER
            bvps = book_value / shares_outstanding  # 주당순자산가치
            pb_ratio = current_price / bvps  # PBR

            result_dic = {'shares_outstanding': shares_outstanding,'net_income': net_income.iloc[0],  # 첫 번째 값 사용
                'total_assets': total_assets,'total_liabilities': total_liabilities,'book_value': book_value,'eps': eps,
                'pe_ratio': pe_ratio,'bvps': bvps,'pb_ratio': pb_ratio}
        # cash_flow

        elif analysis_type=='cashflow':


            cash_and_cash_equivalents = earnings.loc["Cash And Cash Equivalents"].iloc[0]
            net_ppe = earnings.loc["Net PPE"].iloc[0]
            result_dic = {'cash_and_cash_equivalents': cash_and_cash_equivalents,'net_ppe': net_ppe}

        # 주식 배당 (Equity & Dividend)

        elif analysis_type=='dividend':
            ordinal_shares_number = earnings.T['Ordinary Shares Number']
            net_income = income_statement.T['Net Income']
            dividends = ticker.dividends
            result_dic = {'ordinal_shares_number': ordinal_shares_number,'net_income':net_income, 'dividends': dividends}


        ## 비용 구조 분석 비용 절감 능력과 효율성을


        elif analysis_type=='cost':
            cost_of_revenue = income_statement.loc['Cost Of Revenue']
            SG_A = income_statement.loc['Selling General And Administration']
            RnD = income_statement.loc['Research And Development']
            result_dic = {'cost_of_revenue': cost_of_revenue,'SG_A':SG_A, 'RnD': RnD}

        ##etc
        # stockholder_equity = earnings.T['Stockholders Equity']
        # longterm_debt = earnings.T['Long Term Debt']
        # total_cap =  earnings.T['Total Capitalization']


        # 예상 성장 값 계산

        elif analysis_type=='expectation':
            current_eps = ticker.info["trailingEps"]  # 현재 EPS
            eps_growth_rate = ticker.info["earningsGrowth"]  # EPS 예상 성장률
            current_net_income = ticker.financials.loc["Net Income"].iloc[0]  # 현재 순이익
            shares_outstanding = ticker.info["sharesOutstanding"]  # 발행 주식 수
            current_revenue = ticker.financials.loc["Total Revenue"].iloc[0]  # 현재 매출
            revenue_growth_rate = ticker.info["revenueGrowth"]  # 매출 성장률
            result_dic = {'current_eps': current_eps,'eps_growth_rate':eps_growth_rate, 'current_net_income': current_net_income,
                         'shares_outstanding':shares_outstanding, 'current_revenue': current_revenue,'revenue_growth_rate':revenue_growth_rate}

        else:
            print('elseelse')
            earningsdf = earnings.T.reset_index()
            earningsdf = earningsdf.rename(columns = {'index':'date'})
            earningsdf['date'] = earningsdf['date'].dt.strftime('%Y-%m-%d')
            result_dic = earningsdf.to_dict('records')
            if quarter=='-1':
              result_dic= result_dic[0]

    except:
        print('exceptexcept')
        earningsdf = earnings.T.reset_index()
        earningsdf = earningsdf.rename(columns = {'index':'date'})
        earningsdf['date'] = earningsdf['date'].dt.strftime('%Y-%m-%d')
        result_dic = earningsdf.to_dict('records')


        if quarter=='-1':
            result_dic= result_dic[0]
    return str(result_dic)


def get_response(messages):
    # 기본 시스템 메시지 추가
    template = string.Template("<|im_start|>system\n${system_content}<|im_end|>")
    
    prompts = template.safe_substitute({"system_content": messages[0]["content"]})
    
    # 유저 및 어시스턴트 메시지를 반복적으로 추가
    
    for msg in messages[1:]:
        if msg['role'] == 'user':
            prompts += f"<|im_start|>user\n{msg['content']}<|im_end|>"
        elif msg['role'] == 'assistant':
            prompts += f"<|im_start|>assistnat{msg['content']}<|im_end|>"
    
    
    # 최종 출력 확인"
    # print(prompt)
    
    # 샘플링 파라미터 설정
    sampling_params = SamplingParams(
        temperature=0,
        max_tokens=1024,
        stop=["<|im_end|>"],  # 문자열로 중지 토큰 지정
        repetition_penalty=1.0
    )
    
    # 생성
    outputs = llm.generate([prompts], sampling_params)
    
    # 결과 출력
    for output in outputs:
        print()
        return output.outputs[0].text
        
      
def call_function(name, args):
    if name == "get_issues_summarized":
        return get_issues_summarized(**args)
    if name == "get_reddit_hotissue":
        return get_reddit_hotissue(**args)
    if name == "get_consensus":
        return get_consensus(**args)
    if name == "get_earnings":
        return get_earnings(**args)


def query_qwen_model(system_prompt, question):
    full_messages = [{"role": "system", "content": system_prompt}]
    messages = full_messages
    messages.append({"role": "user", "content": question})
    response_message = get_response(messages)
    
    if '<tool_call>' in response_message:
        tool_call_message= {'role':'assistant','content':response_message}
        messages.append(tool_call_message)
        toolcall_pattern = r'<tool_call>(.*?)</tool_call>'
        tool_call_json = re.findall(toolcall_pattern, response_message, re.DOTALL)
        for tool_call_str in tool_call_json:

            tool_call =  json.loads(tool_call_str)

            function_name = tool_call['name']
            function_args = tool_call['arguments']

            function_response = call_function(function_name, function_args)
            tool_response = {'role':'user','content':'<tool_reponse>'+function_response+'</tool_reponse>'}
            messages.append(tool_response)
        
        final_message = get_response(messages)
    else:
        final_message = response_message
    return final_message


def main():
    st.title("기업 분석 리포트 Assistant ")
    system_prompt = """당신은 다양한 기능을 호출할 수 있는 AI 모델입니다. 사용자의 요청에 따라 특정 함수를 호출하고, 함수의 시그니처는 <tools></tools> XML 태그 내에 제공됩니다. 함수를 호출할 때는 함수에 필요한 정확한 값을 추정하지 말고 사용자가 제공한 값에 따라 함수를 실행해야 합니다.

        아래는 사용 가능한 함수들과 각각의 파라미터에 대한 설명입니다:

        get_issues_summarized

        설명: 특정 회사 또는 키워드에 대한 이슈를 검색하고 요약합니다.
        파라미터:
        keyword: 이슈/현황을 검색하고자 하는 회사명 또는 키워드.
        days: 검색하고자 하는 기간(일 단위 (integer)).

        get_reddit_hotissue

        설명: 금융시장에서 핫한 이슈를 요약합니다.
        파라미터:
        days: 검색하고자 하는 기간(일 단위).

        {name: get_earnings,
        설명: 기업의 재무재표 또는 현금흐름을 가져오고 분석합니다. 성장률과 같이 이전 년도 데이터가 필요한경우, 이전 년도 데이터도 한번 더 호출하세요
        파라미터:{symbol: 실적 데이터를 찾고자 하는 기업의 심볼.
        analysis_type: 분석 유형(growth, profitability, stability, valuation, cashflow, dividend, cost, NA).
        type_: 데이터 타입(yearly 또는 quarter).
        year: 데이터를 찾고자 하는 연도 (명시하지 않을경우, 데이터가 존재하는 최근 연도의 데이터를 참조합니다.).
        quarter: 데이터를 찾고자 하는 분기(명시하지않은 경우 최근 데이터를 조회하도록 -1 을 입력합니다).}}

        get_consensus

        설명: 기업의 EPS 컨센서스 데이터 또는 매수/매도/홀드 의견을 가져와서 분석합니다.
        파라미터:
        symbol: 데이터를 찾고자 하는 기업의 심볼.
        year: 데이터를 찾고자 하는 연도.
        quarter: 데이터를 찾고자 하는 분기.
        각 함수 호출 시, JSON 객체를 사용하여 함수 이름과 인자들을 <tool_call></tool_call> XML 태그 내에 명시해야 합니다. 함수 호출 예시는 다음과 같습니다:

        xml
        Copy
        <tool_call>
        {
            "name": "get_earnings",
            "arguments": {
                "symbol": "AAPL",
                "analysis_type": "growth",
                "type_": "yearly" ,
                "year": "2024",
                "quarter": "-1"
            }
        }
        </tool_call>
        각 함수의 인자 값을 정확하게 지정해 주세요. 특히, 연도와 분기를 설정할 때 현재 날짜가 1월이나 2월인 경우, 최근 연도의 데이터를 참조하도록 주의해야 합니다.
        **주의사항
        함수를 호출할때를 제외하고 한국어로 대답하세요.

        """
                  
    st.write("질문을 입력해주세요.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            

    if prompt := st.chat_input("특정 기업에 대한 실적 또는 현황에 대해 물어보세요!"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response_message = query_qwen_model(system_prompt, prompt)
            st.markdown(response_message)

        st.session_state.messages.append({"role": "assistant", "content": response_message})

if __name__ == "__main__":
    main()