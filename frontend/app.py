import os
import random

import pandas as pd
import requests
import streamlit as st

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="위치 기반 데이터 시각화",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_data
def fetch_locations():
    try:
        response = requests.get(f"{BACKEND_URL}/locations", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ 백엔드 연결 실패: {e}")
        st.stop()

@st.cache_data
def generate_data(city, n_points, seed_value):
    if seed_value is not None:
        random.seed(seed_value)

    locations = fetch_locations()
    center = locations[city]

    df = pd.DataFrame(
        {
            "lat": [center["lat"] + random.uniform(-0.02, 0.02) for _ in range(n_points)],
            "lon": [center["lon"] + random.uniform(-0.02, 0.02) for _ in range(n_points)],
            "value": [random.randint(1, 100) for _ in range(n_points)],
        }
    )
    return df

st.title("📍 위치 기반 데이터 시각화")

with st.sidebar:
    st.header("⚙️ 설정")

    locations = fetch_locations()
    city = st.selectbox(
        "지역 선택",
        list(locations.keys()),
        help="분석할 도시를 선택하세요"
    )

    n_points = st.slider(
        "데이터 포인트 개수",
        min_value=10,
        max_value=500,
        value=50,
        step=10,
        help="생성할 랜덤 데이터의 개수"
    )

    use_seed = st.checkbox("고정 시드 사용", value=False)
    seed_value = None
    if use_seed:
        seed_value = st.number_input("시드값", value=42, step=1)

    st.divider()
    st.caption("💡 팁: 고정 시드를 사용하면 같은 데이터가 생성됩니다")

df = generate_data(city, n_points, seed_value)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📊 총 포인트", n_points)
with col2:
    st.metric("📈 평균값", f"{df['value'].mean():.1f}")
with col3:
    st.metric("📉 중앙값", f"{df['value'].median():.1f}")

st.divider()

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"🗺️ {city} 지도")
    st.map(df, latitude="lat", longitude="lon", size="value")

with col2:
    st.subheader("📊 값 분포")
    st.bar_chart(df["value"].value_counts().sort_index())

    st.subheader("📌 통계")
    stats_data = {
        "최댓값": df["value"].max(),
        "최솟값": df["value"].min(),
        "표준편차": f"{df['value'].std():.2f}",
        "사분위수(Q1)": df["value"].quantile(0.25),
        "사분위수(Q3)": df["value"].quantile(0.75),
    }
    for label, value in stats_data.items():
        st.write(f"**{label}:** {value}")

st.divider()

tab1, tab2, tab3 = st.tabs(["📋 데이터", "📈 상세 분석", "⬇️ 내보내기"])

with tab1:
    st.subheader("원본 데이터")

    col1, col2 = st.columns([2, 1])
    with col1:
        sort_by = st.selectbox("정렬 기준", ["위도", "경도", "값"])
        sort_map = {"위도": "lat", "경도": "lon", "값": "value"}
    with col2:
        sort_order = st.radio("정렬 순서", ["오름차순", "내림차순"], horizontal=True)

    ascending = sort_order == "오름차순"
    sorted_df = df.sort_values(by=sort_map[sort_by], ascending=ascending).reset_index(drop=True)
    sorted_df.index = sorted_df.index + 1
    st.dataframe(sorted_df, use_container_width=True)

with tab2:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 히스토그램")
        bins = st.slider("구간 수", 5, 50, 20)
        hist = pd.cut(df["value"], bins=bins).value_counts().sort_index()
        hist.index = hist.index.astype(str)
        st.bar_chart(hist)

    with col2:
        st.subheader("📈 누적분포")
        sorted_values = sorted(df["value"])
        cumulative = list(range(1, len(sorted_values) + 1))
        cumulative_df = pd.DataFrame({
            "값": sorted_values,
            "누적 개수": cumulative,
        })
        st.line_chart(cumulative_df.set_index("값"))

with tab3:
    st.subheader("데이터 다운로드")

    col1, col2 = st.columns(2)

    with col1:
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 CSV 다운로드",
            data=csv,
            file_name=f"{city}_data.csv",
            mime="text/csv",
        )

    with col2:
        json_str = df.to_json(orient="records", indent=2)
        st.download_button(
            label="📥 JSON 다운로드",
            data=json_str,
            file_name=f"{city}_data.json",
            mime="application/json",
        )
