import streamlit as st
import pandas as pd
# import fitz
from openai import OpenAI
import io
import time
import json
from openai import OpenAI
import os
import urllib.request
import praw
from datetime import datetime, timedelta
import yfinance as yf
import requests


tools= [{"type": "function",
         "function":    {
        "name":'get_reddit_issues_summarized',
        "description":'당신은 특정 키워드의 이슈검색 챗봇입니다.',
        'parameters':{
            "type":"object",
            "properties" :{
                "keyword":{'type':'string', "description": '이슈/현황을 검색하고자 하는 회사명 또는 키워드 in English '},
                "days":{'type':'integer', "description": '검색하고자 하는 기간'}
                
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
        "description":'당신은 핫한 이슈 요약하는 챗봇입니다.',
        'parameters':{
            "type":"object",
            "properties" :{
                "days":{'type':'integer', "description": '검색하고자 하는 기간'}
                
            },
            "required":['days'],
            "additionalProperties": False
        },
             "strict": True
    }},
       {"type": "function",       
       "function":   {
        "name":'get_consensus',
        "description":'당신은 기업의 (EPS) 컨센서스 데이터를 가져와서 계산하는 로봇입니다.',
        'parameters':{
            "type":"object",
            "properties" :{
                "symbol":{'type':'string', "description": '컨센서스 데이터를 찾고자 하는 기업의 symbol'},
                "year":{'type':'string', "description": '컨센서스 데이터를 찾고자 하는 연도, 명시 하지 않을경우 가장 최근 연도 로 설정'},
                "quarter":{'type':'string', "description": '컨센서스 데이터를 찾고자 하는 분기로 1~4로 이루어진 숫자, 마지막 분기일경우 -1 이라고 표기 '}
            },
            "required":['symbol', 'year','quarter'],
            "additionalProperties": False
        },
             "strict": True
    }},
       {"type": "function",       
       "function":   {
        "name":'get_earnings',
        "description":'당신은 기업의 실적을 가져오고 분석하는 로봇입니다.',
        'parameters':{
            "type":"object",
            "properties" :{
                "symbol":{'type':'string', "description": '실적 데이터를 찾고자 하는 기업의 symbol'},
                "type_":{'type':'string', "description": "연간 실적데이터 일경우 'yearly' 아닐경우 'quarter' 이라고 표기"},
                "year":{'type':'string', "description": '실적 데이터를 찾고자 하는 연도, 명시 하지 않을경우 가장 최근 연도 로 설정'},
                "quarter":{'type':'string', "description": '실적 데이터를 찾고자 하는 분기로 1~4로 이루어진 숫자, 마지막 또는 최근 분기일경우 -1 이라고 표기 '}
            },
            "required":['symbol', 'type_','year','quarter'],
            "additionalProperties": False
        },
             "strict": True
    }}]


def load_file(file):
    if file.type == "text/csv":
        return pd.read_csv(file)
    elif file.type == "text/plain":
        return file.getvalue().decode("utf-8")
    elif file.type == "application/pdf":
        return extract_text_from_pdf(file)
    else:
        st.error("지원하지 않는 파일 형식입니다❎")
        return None

# def extract_text_from_pdf(file):
#     pdf_file = io.BytesIO(file.getvalue())
#     with fitz.open(stream=pdf_file, filetype="pdf") as doc:
#         text = ""
#         for page in doc:
#             text += page.get_text()
#     return text

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

    
    client = OpenAI()
    
    response = client.chat.completions.create(
      model="gpt-4o",
      messages=[
        {
          "role": "system",
          "content": f"The given data is title and body collected from reddit. 주어진 내용을 기반으로 {keyword} 주가에 영향을 미치는 가장 hot 한 이슈가 뭔지 요약해줘 한국어로 "
        },
        {
          "role": "user",
          "content": titleandbody }
      ],
      temperature=1,
      max_tokens=1024,
      top_p=1
    )
    return response.choices[0].message.content

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

    
    client = OpenAI()
    
    response = client.chat.completions.create(
      model="gpt-4o",
      messages=[
        {
          "role": "system",
          "content": f"The given data is title and body collected from reddit. 주어진 내용을 기반으로 최근 레딧 wallstreetbets에서 가장 hot 한 이슈가 뭔지 요약해줘 한국어로 "
        },
        {
          "role": "user",
          "content": titleandbody }
      ],
      temperature=1,
      max_tokens=1024,
      top_p=1
    )
    return response.choices[0].message.content

def get_consensus(symbol , year, quarter):

    api_key = 'd92779aed523de914055c6b543801a73'
    consensus_url = f'https://financialmodelingprep.com/api/v3/earnings-surprises/{symbol}?apikey={api_key}'
    consensus_response = requests.get(consensus_url).json()
    for consensus in consensus_response:
        consensus['year'] =consensus['date'][:4]
        if consensus['date'][5:7] == '05':
            consensus['quarter'] = '1'
        elif consensus['date'][5:7] == '08':
             consensus['quarter'] = '2'
        elif consensus['date'][5:7] == '11':
             consensus['quarter'] = '3'
        elif consensus['date'][5:7] == '02':
             consensus['quarter'] = '4'
            
        consensus['EPS_surprise'] = ((consensus['actualEarningResult'] - consensus['estimatedEarning']) / 
                                           consensus['estimatedEarning']) * 100
        
    
    year_consensus = [a for a in consensus_response if a['year']==year ]
    if quarter =='-1':
        return year_consensus[-1]
    else:
        
        year_quarter_consensus = [a for a in year_consensus if a['quarter'] == quarter][0]

        return year_quarter_consensus

def get_earnings(symbol, type_ ,year, quarter):
    ticker = yf.Ticker(symbol)
    if type_ == 'yearly':
        earnings = ticker.financials.T
    else:
    # 분기별 실적 데이터
        earnings = ticker.quarterly_financials.T
        
    earnings_df = earnings[['Total Revenue', 'Operating Income', 'Net Income','EBITDA']].reset_index()
    earnings_df.columns = ['date', 'revenue', 'operatingIncome', 'netIncome','EBITDA']
    earnings_df['date'] = earnings_df['date'].dt.strftime('%Y-%m-%d')

    # 매출 성장률 (QoQ)
    earnings_df['revenue_growth_QoQ'] = earnings_df['revenue'].pct_change(-1) * 100
    
    # 순이익 성장률 (QoQ)
    earnings_df['net_income_growth_QoQ'] = earnings_df['netIncome'].pct_change(-1) * 100
    
    # 영업이익률 (Operating Margin)
    earnings_df['operating_margin'] = (earnings_df['operatingIncome'] / earnings_df['revenue']) * 100
    
    # 순이익률 (Net Margin)
    earnings_df['net_margin'] = (earnings_df['netIncome'] / earnings_df['revenue']) * 100

    
    # 데이터프레임 출력
    earnings_dict = earnings_df.to_dict('records')

    if quarter =='-1':
        return earnings_dict[0]
    else:
        year_earnings = [a for a in earnings_dict if a['date'][:4] == year]
        if not year_earnings:
            return "해당 연도 실적은 제공되지 않습니다."
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
            return quarter_earning
        else:
            return year_earnings
        
def call_function(name, args):
    if name == "get_reddit_issues_summarized":
        return get_reddit_issues_summarized(**args)
    if name == "get_reddit_hotissue":
        return get_reddit_hotissue(**args)
    if name == "get_consensus":
        return get_consensus(**args)
    if name == "get_earnings":
        return get_earnings(**args)


def main():
    st.title("기업 분석 리포트 Assistant")
    st.write("질문을 입력해주세요.")

    if "messages" not in st.session_state:
        st.session_state.messages = []


    api_key = st.text_input("OpenAI API 키:", type="password")

    if api_key:
        client = OpenAI(api_key=api_key)
        st.write("키가 입력되었습니다")
        st.session_state.system_prompt = f"당신은 금융 챗봇입니다."
        

        if st.session_state.get('system_prompt') is not None:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            if prompt := st.chat_input("특정 기업에 대한 실적 또는 현황에 대해 물어보세요!"):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    full_response = ""
                    stream = query_openai_model(
                        client,
                        st.session_state.system_prompt,
                        st.session_state.messages
                    )
                    for chunk in stream:
                        if chunk.choices[0].delta.content is not None:
                            full_response += chunk.choices[0].delta.content
                            message_placeholder.markdown(full_response + "▌")
                    message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
        else:
            st.info(st.session_state.get('system_prompt'))

    else:
        st.warning("OpenAI API 키를 입력하세요.")

if __name__ == "__main__":
    main()
