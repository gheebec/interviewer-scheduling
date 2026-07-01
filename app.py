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
    # 💡 [버그 수정 완료] 안전하게 나눠서 마크다운을 빌드하도록 변경
    attendees_str = ", ".join([f"`{name}`" for name in attendees])
    st.markdown(f"**현재 참여자 ({len(attendees)}명):** {attendees_str}")
    
    all_votes = list(room_data["schedules"].values())
    overlap_slots = set(all_votes[0])
    for vote in all_votes[1:]:
        overlap_slots = overlap_slots.intersection(set(vote))
        
    if overlap_slots:
        for slot in sorted(list(overlap_slots)):
            st.info(f"👉 **{slot}** (모든 면접관 참여 가능)")
    else:
        st.warning("현재 모든 면접관이 동시에 가능한 시간대가 없습니다. 일정을 조율해 주세요.")
else:
    st.info("제출된 면접 일정이 없습니다. 아래 양식에서 가용 시간을 등록해 주세요.")

if st.button("🔄 현황 실시간 새로고침", use_container_width=True):
    st.rerun()

st.divider()

# ----------------------------------------------------
# [SECTION 2] 면접관 일정 등록 및 수정 양식
# ----------------------------------------------------
st.subheader("📝 나의 가용 시간 등록 및 수정")

interviewer_name = st.text_input(
    "1. 성함을 입력해 주세요.", 
    placeholder="예: 홍길동 팀장"
).strip()

time_slots = [
    "09:00 - 10:00", "10:00 - 11:00", "11:00 - 12:00",
    "13:00 - 14:00", "14:00 - 15:00", "15:00 - 16:00",
    "16:00 - 17:00", "17:00 - 18:00"
]

if interviewer_name:
    is_existing = interviewer_name in room_data["schedules"]
    if is_existing:
        st.caption(f"ℹ️ `{interviewer_name}`님은 이미 등록된 사용자입니다. 기존 선택 내역이 아래 자동 복원되었습니다.")
        existing_slots = room_data["schedules"][interviewer_name]
    else:
        existing_slots = []
        
    st.markdown("**2. 참여 가능한 시간대를 모두 선택해 주세요.**")
    
    with st.container(border=True):
        with st.form("interviewer_form", clear_on_submit=False):
            interviewer_choices = []
            
            for date in room_data["dates"]:
                st.markdown(f"📅 **{date}**")
                cols = st.columns(2)
                for i, slot in enumerate(time_slots):
                    with cols[i % 2]:
                        combined_slot = f"{date} [{slot}]"
                        is_checked = combined_slot in existing_slots
                        if st.checkbox(slot, value=is_checked, key=f"{room_id}_{interviewer_name}_{combined_slot}"):
                            interviewer_choices.append(combined_slot)
                st.write("") 
                
            submit_btn = st.form_submit_button("내 일정 저장하기", type="primary", use_container_width=True)
            
            if submit_btn:
                if not interviewer_choices:
                    st.error("가능한 시간대를 하나 이상 선택한 후 저장해 주세요.")
                else:
                    room_data["schedules"][interviewer_name] = interviewer_choices
                    st.success("일정이 정상적으로 저장되었습니다.")
                    st.rerun()
                    
    if is_existing:
        if st.button("❌ 내 등록 데이터 전체 삭제", use_container_width=True):
            del room_data["schedules"][interviewer_name]
            st.rerun()
else:
    st.caption("성함을 적으시면 아래에 시간 선택 체크박스가 나타납니다.")

st.divider()

# ----------------------------------------------------
# [SECTION 3] 방장 전용 관리자 메뉴
# ----------------------------------------------------
with st.expander("⚙️ 방장 전용 관리자 메뉴 (후보 날짜 설정 / 룸 관리)"):
    st.markdown("### 후보 날짜 관리")
    chosen_dates = st.date_input(
        "이 룸의 면접 후보 날짜 지정 (최대 5개)",
        value=[datetime.strptime(d, "%Y-%m-%d") for d in room_data["dates"]],
        min_value=datetime(2026, 1, 1),
        max_value=datetime(2026, 12, 31),
    )
    if isinstance(chosen_dates, (list, tuple)):
        room_data["dates"] = sorted([d.strftime("%Y-%m-%d") for d in chosen_dates])[:5]
    else:
        room_data["dates"] = [chosen_dates.strftime("%Y-%m-%d")]
        
    st.write(f"현재 지정된 후보일: {', '.join(room_data['dates'])}")
    
    st.markdown("---")
    st.markdown("### 일정 확정 및 마감")
    confirm_title = st.text_input("면접 프로젝트 명칭", placeholder="예: 상반기_개발공채")
    confirm_dt = st.text_input("최종 확정된 일시", placeholder="예: 2026-07-15 14:00-15:00")
    if st.button("현재 조율 결과 확정 후 이력 보존", use_container_width=True):
        if confirm_title and confirm_dt:
            room_data["history"].append({
                "면접 명칭": confirm_title,
                "확정 일시": confirm_dt,
                "참여 면접관": ", ".join(list(room_data["schedules"].keys()))
            })
            room_data["schedules"] = {}
            st.success("확정 데이터가 저장되었습니다.")
            st.rerun()

    st.markdown("---")
    st.markdown("### 새로운 면접 룸 링크 개설")
    new_room_name = st.text_input("새로운 룸 이름 입력", placeholder="예: sales_2026")
    if st.button("새로운 룸 코드 생성", use_container_width=True) and new_room_name.strip():
        st.code(f"?room={new_room_name.strip()}", language="text")

    st.markdown("---")
    st.markdown("### 현재 룸 데이터 전체 파기")
    confirm_delete = st.checkbox("이 룸의 모든 투표 데이터를 영구 삭제하는 것에 동의합니다.")
    if st.button("🚨 현재 룸 데이터 완전 파기", type="primary", use_container_width=True):
        if confirm_delete:
            if room_id == "default_room":
                global_db["default_room"] = {"dates": ["2026-07-15", "2026-07-16"], "schedules": {}, "history": []}
            else:
                global_db.pop(room_id, None)
            st.query_parameters.clear()
            st.rerun()

st.divider()

# ----------------------------------------------------
# [SECTION 4] 최종 확정 이력 타임라인
# ----------------------------------------------------
st.subheader("📜 완료된 면접 확정 이력")
if room_data["history"]:
    st.dataframe(pd.DataFrame(room_data["history"]), use_container_width=True, hide_index=True)
else:
    st.caption("아직 완료된 면접 확정 이력이 없습니다.")
