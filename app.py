import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="면접 일정 조율기", layout="centered")

# 🎨 [비주얼 업그레이드] 배경색, 폰트, 크기, 여백 전면 코딩
st.markdown("""
    <style>
    /* 1. 전체 앱의 배경색과 기본 폰트 설정 (눈이 편안한 샌드 화이트) */
    .stApp {
        background-color: #fcfbf9;
    }
    
    /* 2. 전체 폰트를 현대적인 고딕체(Pretendard/Noto Sans)로 통합 및 자간 조절 */
    html, body, [class*="css"], .stMarkdown, p, span, label {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
        font-size: 15px !important;
        color: #2c302e !important; /* 완전 검은색 대신 고급스러운 다크 그레이 */
        letter-spacing: -0.02em !important; /* 글자 간격을 좁혀 가독성 향상 */
        line-height: 1.6 !important; /* 줄간격 확보 */
    }
    
    /* 3. 대제목(Title) 디자인 세련되게 변경 */
    h1 {
        font-size: 2.4rem !important;
        font-weight: 800 !important;
        color: #1a2a3a !important; /* 신뢰감을 주는 딥 네이비 */
        padding-top: 1rem !important;
        padding-bottom: 0.2rem !important;
    }
    
    /* 4. 중제목(Subheader) 디자인 */
    h3 {
        font-size: 1.4rem !important;
        font-weight: 700 !important;
        color: #2b4560 !important;
        margin-top: 2rem !important;
        margin-bottom: 0.8rem !important;
    }
    
    /* 5. 입력창(텍스트 입력, 버튼 등) 라운딩 및 테두리 정돈 */
    .stTextInput div div input {
        background-color: #ffffff !important;
        border-radius: 8px !important;
        border: 1px solid #e2e8f0 !important;
        padding: 10px 14px !important;
        font-size: 15px !important;
    }
    
    /* 6. 체크박스 영역 간격 확보 및 가독성 케어 */
    [data-testid="stCheckbox"] {
        background-color: #ffffff;
        padding: 12px 16px !important;
        border-radius: 8px !important;
        border: 1px solid #f1f3f5 !important;
        margin-bottom: 8px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    
    /* 7. 메인 저장 버튼 디자인 강조 (토스 스타일 벨벳 블루) */
    .stButton button[kind="primary"] {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 12px 0px !important;
        border: none !important;
        transition: background-color 0.2s;
    }
    .stButton button[kind="primary"]:hover {
        background-color: #1d4ed8 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 2. 메인 컨텐츠 및 데이터 처리 로직 시작
# ----------------------------------------------------
st.title("면접 일정 조율 시스템")
st.caption("면접관 가용 시간을 취합하여 전원 참석 가능한 최적의 시간대를 도출합니다.")

@st.cache_resource
def get_global_db():
    return {}

global_db = get_global_db()

try:
    room_id = st.query_parameters.get("room", "default_room")
except Exception:
    room_id = "default_room"

if room_id not in global_db:
    global_db[room_id] = {
        "dates": ["2026-07-15", "2026-07-16"],
        "schedules": {},
        "history": []
    }

room_data = global_db[room_id]

st.write("")
st.markdown(f"📍 **현재 접속 룸:** `{room_id}`")
st.caption("🔗 이 주소창의 URL을 복사하여 공유하면 다른 사람들과 실시간으로 연결됩니다.")
st.divider()

# ----------------------------------------------------
# [SECTION 1] 최적의 조율 결과창 (모두 가능한 시간 추천)
# ----------------------------------------------------
st.subheader("💡 최적의 면접 시간대 추천")

if room_data["schedules"]:
    attendees = list(room_data["schedules"].keys())
    st.markdown(f"**현재 참여자 ({len(attendees)}
