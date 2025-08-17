import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

#Dashboard Configuration
st.set_page_config(page_title="Investment Dashboard", layout="wide")

st.title("My Portfolio Dashboard")
st.write("A simple dashboard to monitor my portfolio.")

#Stock Tickers
tickers = {
    "Applied Digital": "APLD",
    "Symbotic": "SYM",
    "Tesla": "TSLA",
    "Google": "GOOGL",
    "Nebius Group N.V": "NBIS",
}

#Sidebar for User Input
st.sidebar.header("Select a Stock")
selected_stock_name = st.sidebar.selectbox("Choose from your portfolio:", list(tickers.keys()))
selected_ticker = tickers[selected_stock_name]

# Add date range selector to sidebar
date_range = st.sidebar.selectbox(
    "Select Date Range",
    ["1 Month", "3 Months", "6 Months", "1 Year", "2 Years", "5 Years"],
    index=3  # Default to 1 Year
)

# Map to yfinance periods
range_map = {
    "1 Month": "1mo",
    "3 Months": "3mo",
    "6 Months": "6mo",
    "1 Year": "1y",
    "2 Years": "2y",
    "5 Years": "5y"
}

# --- Caching for Performance ---
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_stock_data(ticker, period):
    return yf.Ticker(ticker).history(period=period)

@st.cache_data(ttl=3600)
def get_company_info(ticker):
    return yf.Ticker(ticker).info

@st.cache_data(ttl=3600)
def get_company_news(ticker):
    return yf.Ticker(ticker).news

# --- Main Content Area with Tabs ---
tab1, tab2 = st.tabs(["Single Stock Analysis", "Portfolio Summary"])

with tab1:
    st.header(f"Displaying data for: {selected_stock_name} ({selected_ticker})")

    # --- Fetch and Display Price Chart ---
    st.subheader("Price Chart with Technical Indicators")
    
    try:
        hist_data = get_stock_data(selected_ticker, range_map[date_range])
        
        if not hist_data.empty:
            # Calculate Simple Moving Averages
            hist_data['SMA_20'] = hist_data['Close'].rolling(window=20).mean()
            hist_data['SMA_50'] = hist_data['Close'].rolling(window=50).mean()
            
            # Calculate RSI
            delta = hist_data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            hist_data['RSI'] = 100 - (100 / (1 + rs))
            
            # Create a Plotly figure with subplots
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, 
                              subplot_titles=('Price with Moving Averages', 'RSI'))
            
            # Add the main closing price line
            fig.add_trace(go.Scatter(
                x=hist_data.index, 
                y=hist_data['Close'], 
                mode='lines', 
                name='Close Price',
                line=dict(color='#1f77b4')
            ), row=1, col=1)
            
            # Add the moving averages
            fig.add_trace(go.Scatter(
                x=hist_data.index, 
                y=hist_data['SMA_20'], 
                mode='lines', 
                name='20-Day SMA', 
                line=dict(dash='dot', color='#ff7f0e')
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(
                x=hist_data.index, 
                y=hist_data['SMA_50'], 
                mode='lines', 
                name='50-Day SMA', 
                line=dict(dash='dash', color='#2ca02c')
            ), row=1, col=1)
            
            # Add RSI chart
            fig.add_trace(go.Scatter(
                x=hist_data.index, 
                y=hist_data['RSI'], 
                name='RSI',
                line=dict(color='#9467bd')
            ), row=2, col=1)
            
            # Add RSI reference lines
            fig.add_hline(y=30, row=2, col=1, line_dash="dash", line_color="red")
            fig.add_hline(y=70, row=2, col=1, line_dash="dash", line_color="red")
            
            fig.update_layout(
                height=600,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"No historical data available for {selected_ticker}. The stock may be delisted or suspended.")
    except Exception as e:
        st.error("Failed to fetch historical data. Please try again later.")
    
    # --- Company Information and News ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Company Profile")
        try:
            info = get_company_info(selected_ticker)
            
            # Display key info points
            st.write(f"**Sector:** {info.get('sector', 'N/A')}")
            st.write(f"**Industry:** {info.get('industry', 'N/A')}")
            st.write(f"**Website:** {info.get('website', 'N/A')}")
            st.write(f"**Market Cap:** ${info.get('marketCap', 0):,}")
            
            # Key metrics section
            st.markdown("---")
            st.subheader("Key Metrics")
            metrics = {
                'P/E Ratio': info.get('trailingPE'),
                'P/B Ratio': info.get('priceToBook'),
                'Dividend Yield': info.get('dividendYield'),
                '52 Week High': info.get('fiftyTwoWeekHigh'),
                '52 Week Low': info.get('fiftyTwoWeekLow')
            }
            
            for metric, value in metrics.items():
                if value is not None:
                    st.write(f"**{metric}:** {value:.2f}" if isinstance(value, float) else f"**{metric}:** {value}")
            
            st.markdown("---")
            st.write("**Business Summary:**")
            st.info(info.get('longBusinessSummary', 'No summary available.'))
            
        except Exception as e:
            st.error(f"Could not retrieve company information. Error: {e}")
    
    with col2:
        st.subheader("Recent News")
        try:
            news = get_company_news(selected_ticker)
            if news:
                for item in news[:5]:  # Display top 5 articles
                    with st.expander(item['title']):
                        st.write(f"**Publisher:** {item['publisher']}")
                        if 'providerPublishTime' in item:
                            st.write(f"**Published:** {pd.to_datetime(item['providerPublishTime'], unit='s').strftime('%Y-%m-%d %H:%M')}")
                        st.write(f"[Read more]({item['link']})")
            else:
                st.info("No recent news found for this company.")
        except Exception as e:
            st.warning("News feed temporarily unavailable.")

with tab2:
    st.subheader("Portfolio Overview")
    
    # Fetch data for all tickers
    portfolio_data = []
    for name, ticker in tickers.items():
        try:
            data = get_stock_data(ticker, '1d')['Close']
            if not data.empty:
                current_price = data.iloc[-1]
                prev_close = data.iloc[-2] if len(data) > 1 else current_price
                change = ((current_price - prev_close) / prev_close) * 100
                
                portfolio_data.append({
                    'Name': name,
                    'Ticker': ticker,
                    'Price': current_price,
                    'Change (%)': change,
                    'Last Updated': data.index[-1].strftime('%Y-%m-%d')
                })
            else:
                portfolio_data.append({
                    'Name': name,
                    'Ticker': ticker,
                    'Price': 'N/A',
                    'Change (%)': 'N/A',
                    'Last Updated': 'N/A'
                })
        except:
            portfolio_data.append({
                'Name': name,
                'Ticker': ticker,
                'Price': 'N/A',
                'Change (%)': 'N/A',
                'Last Updated': 'N/A'
            })
    
    df = pd.DataFrame(portfolio_data)
    
    # Apply color formatting to change percentage
    def color_change(val):
        if isinstance(val, (int, float)):
            color = 'red' if val < 0 else 'green'
            return f'color: {color}'
        return ''
    
    styled_df = df.style.format({
        'Price': '{:.2f}',
        'Change (%)': '{:.2f}%'
    }).applymap(color_change, subset=['Change (%)'])
    
    st.dataframe(styled_df, use_container_width=True, height=(len(df) + 1) * 35 + 3)
    
    # Add a simple portfolio performance chart
    st.subheader("Portfolio Performance")
    
    try:
        # Get 1-month performance for all tickers
        perf_data = []
        for name, ticker in tickers.items():
            try:
                data = get_stock_data(ticker, '1mo')['Close']
                if not data.empty and len(data) > 1:
                    perf = ((data.iloc[-1] - data.iloc[0]) / data.iloc[0]) * 100
                    perf_data.append({
                        'Ticker': ticker,
                        'Performance (%)': perf
                    })
            except:
                pass
        
        if perf_data:
            perf_df = pd.DataFrame(perf_data)
            fig = go.Figure()
            
            # Add bars with color based on performance
            fig.add_trace(go.Bar(
                x=perf_df['Ticker'],
                y=perf_df['Performance (%)'],
                marker_color=['green' if x >= 0 else 'red' for x in perf_df['Performance (%)']],
                text=perf_df['Performance (%)'].round(2).astype(str) + '%',
                textposition='auto'
            ))
            
            fig.update_layout(
                title='1-Month Performance',
                yaxis_title='Performance (%)',
                xaxis_title='Ticker',
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Could not load performance data for all stocks.")
    except Exception as e:
        st.warning(f"Failed to generate performance chart: {e}")