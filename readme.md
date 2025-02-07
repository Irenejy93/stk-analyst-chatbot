# Stock Analyst Chatbot

## Overview
<img width="774" alt="Image" src="https://github.com/user-attachments/assets/63f88e2f-8f3d-41f8-81e5-55f60be81c62" />

This project integrates multiple financial data sources and analyses to provide insights into stock market trends, earnings performance, and Reddit discussions about stocks. The chatbot is accessible via [Stock Analyst Chatbot](https://stk-analyst-chatbot-jdamhdaqsld9tw7d8ps8nj.streamlit.app/).

## Features

- **Yahoo Finance Integration**: Fetch earnings reports, consensus estimates, and compute EPS.
- **Reddit Analysis**: Identify trending stocks and summarize hot topics from `r/wallstreetbets`.
- **Function Calls Implementation**: A `function_call.py` script is used to retrieve stock-related data.
- **Streamlit UI**: A user-friendly web interface built with Streamlit.
- **Dynamic System Prompts**: The chatbot adjusts system prompts based on the requested function.
- **Real-time Insights**: Provides updated stock market analysis in real-time.

## Usage

1. **Enter a Stock Symbol**: Users can query earnings data, analyst consensus, or EPS calculations.
2. **Check Reddit Trends**: Input a stock keyword to analyze discussions and sentiment.
3. **Function Call Execution**: Uses `function_call.py` to fetch relevant stock or Reddit data.
4. **Interactive Chatbot Interface**: Utilizes Streamlit for a seamless experience.

## How It Works

- The `function_call.py` script is triggered for data retrieval from Yahoo Finance and Reddit.
- The OpenAI model processes and summarizes the data.
- The chatbot dynamically updates system prompts for tailored responses.

## Installation & Running Locally

1. Clone the repository:
   ```sh
   git clone https://github.com/your-repo/stock-analyst-chatbot.git
   cd stock-analyst-chatbot
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Run the Streamlit app:
   ```sh
   streamlit run function_call.py
   ```

## Deployment

This chatbot is deployed on Streamlit and can be accessed via: [Stock Analyst Chatbot](https://stk-analyst-chatbot-jdamhdaqsld9tw7d8ps8nj.streamlit.app/).

## Future Enhancements

- **Integration with Additional Data Sources**: Expanding to other financial APIs.
- **Sentiment Analysis**: Applying NLP to gauge market sentiment.
- **Advanced Charting**: Adding visualizations for earnings and Reddit trends.

