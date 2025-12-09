import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
from groq import Groq
from dotenv import load_dotenv

# Load API key securely
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("🚨 API Key is missing! Set it in Streamlit Secrets or a .env file.")
    st.stop()

# Init Groq client
client = Groq(api_key=GROQ_API_KEY)

# Streamlit App Settings
st.set_page_config(page_title="Personal Finance AI Dashboard", page_icon="💸", layout="wide")
st.title("💸 Personal Finance & Investment AI Dashboard")
st.write("Kelola pemasukan, pengeluaran, tabungan, dan investasi dengan bantuan AI!")

# Model selector
selected_model = st.selectbox(
    "🤖 Pilih Model AI",
    ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "mixtral-8x7b-32768"],
    index=0
)

# File uploader
uploaded_file = st.file_uploader("📂 Upload Data Keuangan (Excel)", type=["xlsx"])

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    required_columns = ["Category", "Amount"]
    if not all(col in df.columns for col in required_columns):
        st.error("⚠️ File harus memiliki kolom: Category & Amount!")
        st.stop()

    st.subheader("📊 Data Keuangan")
    st.dataframe(df)

    # Financial Summary
    total_income = df[df["Category"] == "Income"]["Amount"].sum()
    total_expense = df[df["Category"] == "Expense"]["Amount"].sum()
    net_cash = total_income - total_expense

    st.markdown(f"""
    ### 💡 Kesimpulan Bulan Ini
    - **Total Income:** Rp {total_income:,.0f}
    - **Total Expense:** Rp {total_expense:,.0f}
    - **Net Cash:** Rp {net_cash:,.0f}
    """)

    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        fig_pie = px.pie(df[df["Category"]=="Expense"], names="Detail", values="Amount",
                         title="🍽️ Pengeluaran berdasarkan kategori")
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        monthly = df.groupby("Month")["Amount"].sum().reset_index()
        fig_line = px.line(monthly, x="Month", y="Amount",
                           title="📈 Tren Keuangan Bulanan")
        st.plotly_chart(fig_line, use_container_width=True)

    # AI Insights
    st.subheader("🤖 AI Personal Finance Advisor")

    df_preview = df.head(20).to_string(index=False)

    try:
        summary_prompt = f"""
        Berikut data keuangan pribadi seseorang:
        {df_preview}

        Buatkan analisis kondisi finansial:
        - Apakah pengeluaran sudah sehat?
        - Apakah ada potensi tabungan yang bisa ditingkatkan?
        - Saran manajemen keuangan pribadi yang mudah diterapkan.
        """

        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a finance expert for personal money management."},
                {"role": "user", "content": summary_prompt}
            ],
            model=selected_model,
        )

        st.markdown("**AI Insight:**")
        st.write(response.choices[0].message.content)

    except Exception as e:
        st.error(f"⚠️ AI request failed: {e}")

    # Chat Advisor
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.subheader("💬 Tanya AI tentang Keuanganmu")
    user_query = st.text_input("Ajukan pertanyaan keuangan (tabungan, investasi, pengeluaran, dll)")

    col_send, col_reset = st.columns([4, 1])
    send_btn = col_send.button("Send")
    reset_btn = col_reset.button("🔄 Reset Chat")

    if reset_btn:
        st.session_state.chat_history.clear()
        st.success("Chat history cleared!")

    if send_btn and user_query:
        try:
            chat_response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Kamu adalah penasihat keuangan pribadi."},
                    *st.session_state.chat_history,
                    {"role": "user", "content": f"Data:\n{df_preview}\n\nPertanyaan: {user_query}"}
                ],
                model=selected_model,
            )

            ai_answer = chat_response.choices[0].message.content

            st.session_state.chat_history.append({"role": "user", "content": user_query})
            st.session_state.chat_history.append({"role": "assistant", "content": ai_answer})
        except Exception as e:
            st.error(f"⚠️ {e}")

    for msg in st.session_state.chat_history:
        speaker = "👤 You" if msg["role"] == "user" else "🤖 Advisor"
        st.markdown(f"**{speaker}:** {msg['content']}")
