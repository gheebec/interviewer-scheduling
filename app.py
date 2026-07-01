import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 페이지 설정 및 다크/라이트 모드 대응 레이아웃
st.set_page_config(page_title="면접 일정 조율 시스템", layout="wide")

# 대제목 스타일 세련되게 변경
st.markdown("""
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        letter-spacing: -0.05rem;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.0rem;
        color: #666;
        margin-bottom: 2rem;
    }
    </style>
    <div class="main-title">인터뷰 스케줄러 : 실시간 일정 조율</div>
    <div class="sub-title">면접관들의 가능한 시간대를 취합하여 최적의 인터뷰 타임을 도출합니다.</div>
""", unsafe_allow_html=True)

# 2. 전역 공유 데이터베이스 캐시 유지
@st.cache_resource
def get_global_db():
    return {}

global_db = get_global_db()

# 3. URL 파라미터 감지
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

# 상단 알림 배너 디자인 슬림화
st.markdown(f"""
    <div style="background-color:rgba(28, 131, 225, 0.1); padding: 10px 15px; border-left: 4px solid #1c83e1; border-radius: 4px; margin-bottom: 25px; font-size: 0.9rem;">
        📊 <strong>현재 세션 ID:</strong> <code>{room_id}</code> | 외부 면접관 공유 시 현재 브라우저의 주소창 URL을 복사하여 전달하세요.
    </div>
""", unsafe_allow_html=True)

# 4. 화면 레이아웃 분할 (메인 작업 영역 / 사이드 보드 영역)
left_col, right_col = st.columns([1.8, 1.2], gap="large")

with left_col:
    # ----------------------------------------------------
    # [구역 A] 방장 설정 구역 (모던 카드로 감싸기)
    # ----------------------------------------------------
    st.markdown("### :material/settings: 1. 후보 일정 세팅 (워크스페이스 설정)")
    
    with st.container(border=True):
        # 방 개설 섹션 간소화 및 깔끔한 배치
        c1, c2 = st.columns([2, 1])
        with c1:
            new_room_name = st.text_input("새로운 조율 룸 생성", placeholder="예: tech_interview_2026", label_visibility="collapsed")
        with c2:
            create_btn = st.button("새로운 룸 링크 생성", use_container_width=True)
            
        if create_btn and new_room_name.strip():
            clean_room = new_room_name.strip()
            st.info("💡 **새 인터뷰 룸 코드:** 주소창 뒤에 아래 주소를 붙여 접속하세요.")
            st.code(f"?room={clean_room}", language="text")
            
        st.markdown("<div style='margin: 15px 0; border-top: 1px solid #eee;'></div>", unsafe_allow_html=True)
        
        # 달력 입력 UI
        chosen_dates = st.date_input(
            "인터뷰 후보 날짜 선택 (최대 5개 날짜 지정 가능)",
            value=[datetime.strptime(d, "%Y-%m-%d") for d in room_data["dates"]],
            min_value=datetime(2026, 1, 1),
            max_value=datetime(2026, 12, 31),
        )
        
        if isinstance(chosen_dates, (list, tuple)):
            room_data["dates"] = sorted([d.strftime("%Y-%m-%d") for d in chosen_dates])[:5]
        else:
            room_data["dates"] = [chosen_dates.strftime("%Y-%m-%d")]
            
        # 선택된 날짜 텍스트 칩(Chip) 스타일로 표시
        chips_html = "".join([f"<span style='background-color:#eee; padding:3px 8px; margin-right:5px; border-radius:12px; font-size:0.85rem;'>📅 {d}</span>" for d in room_data["dates"]])
        st.markdown(f"<div style='margin-top:10px;'>{chips_html}</div>", unsafe_allow_html=True)

        # 방 삭제 기능을 아코디언 메뉴로 하단 배치하여 시선 분산 방지
        with st.expander(":material/delete: 워크스페이스 데이터 리셋", expanded=False):
            st.caption("이 룸에 누적된 투표 내역과 확정 이력이 전부 초기화됩니다.")
            confirm_delete = st.checkbox("데이터 완전 삭제에 동의합니다.", key="del_confirm_check")
            if st.button("현재 룸 데이터 파기", type="primary", use_container_width=True):
                if confirm_delete:
                    if room_id == "default_room":
                        global_db["default_room"] = {"dates": ["2026-07-15", "2026-07-16"], "schedules": {}, "history": []}
                    else:
                        global_db.pop(room_id, None)
                    st.query_parameters.clear()
                    st.rerun()

    st.markdown("<div style='margin: 30px 0;'></div>", unsafe_allow_html=True)

    # ----------------------------------------------------
    # [구역 B] 면접관 일정 입력 (깔끔한 타임 플래너 형태로 변경)
    # ----------------------------------------------------
    st.markdown("### :material/edit_calendar: 2. 면접관 가용 시간 등록")
    
    with st.container(border=True):
        interviewer_name = st.text_input("면접관 성함", placeholder="이름을 입력하면 시간 선택 창이 활성화됩니다.", label_visibility="visible").strip()
        
        time_slots = [
            "09:00 - 10:00", "10:00 - 11:00", "11:00 - 12:00",
            "13:00 - 14:00", "14:00 - 15:00", "15:00 - 16:00",
            "16:00 - 17:00", "17:00 - 18:00"
        ]
        
        if interviewer_name:
            is_existing = interviewer_name in room_data["schedules"]
            if is_existing:
                st.markdown(f"""
                    <div style="background-color:rgba(255, 165, 0, 0.1); padding: 8px 12px; border-left: 4px solid orange; border-radius: 4px; font-size:0.85rem; margin-bottom:15px;">
                        🔄 <strong>{interviewer_name}</strong>님의 기존 등록 내역을 불러왔습니다. 수정 후 재저장 가능합니다.
                    </div>
                """, unsafe_allow_html=True)
                existing_slots = room_data["schedules"][interviewer_name]
            else:
                existing_
