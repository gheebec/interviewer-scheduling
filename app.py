import streamlit as st
import pandas as pd

# 🚨 반드시 이 명령어가 Streamlit 명령어 중 가장 맨 위에 와야 합니다!
st.set_page_config(page_title="면접관 일정 조율기", layout="centered")

st.title("🤝 면접관 일정 조율 앱 (1단계)")
st.write("면접관들의 일정을 취합하여 모두가 가능한 시간대를 찾아냅니다.")

# 1. 면접 기본 설정 (방장 설정 구역)
st.header("1. 면접 기본 설정")
col1, col2 = st.columns(2)
with col1:
    interview_date = st.date_input("면접 진행 날짜 선택")
with col2:
    time_slots = [
        "09:00 - 10:00", "10:00 - 11:00", "11:00 - 12:00",
        "13:00 - 14:00", "14:00 - 15:00", "15:00 - 16:00",
        "16:00 - 17:00", "17:00 - 18:00"
    ]
    st.caption("기본 시간 단위: 1시간 단위 (오전 9시 ~ 오후 6시)")

# 데이터 저장을 위한 세션 상태 초기화 (데이터베이스 대용)
if "interviewer_schedules" not in st.session_state:
    st.session_state.interviewer_schedules = {}

# 2. 면접관별 일정 입력 구역
st.header("2. 면접관 일정 입력")
with st.form("schedule_form", clear_on_submit=True):
    interviewer_name = st.text_input("면접관 이름 입력", placeholder="예: 홍길동 팀장")
    st.write(f"📅 **{interview_date}** 에 면접이 가능한 시간을 모두 선택해 주세요:")
    
    # 체크박스로 가능한 시간 선택
    selected_slots = []
    cols = st.columns(2)
    for i, slot in enumerate(time_slots):
        with cols[i % 2]:
            if st.checkbox(slot, key=f"slot_{i}"):
                selected_slots.append(slot)
                
    submit_btn = st.form_submit_button("일정 제출하기")
    
    if submit_btn:
        if not interviewer_name:
            st.error("면접관 이름을 입력해 주세요.")
        elif not selected_slots:
            st.warning("가능한 시간대를 최소 하나 이상 선택해 주세요.")
        else:
            st.session_state.interviewer_schedules[interviewer_name] = selected_slots
            st.success(f"✅ {interviewer_name}님의 일정이 등록되었습니다!")

# 3. 결과 확인 구역
st.header("3. 조율 결과 (모두 가능한 시간)")

if st.session_state.interviewer_schedules:
    # 참여 현황 표시
    st.subheader("👥 현재 참여 현황")
    for name, slots in st.session_state.interviewer_schedules.items():
        st.write(f"- **{name}**: {', '.join(slots)}")
        
    # 모두 가능한 시간대 계산 (교집합)
    all_schedules = list(st.session_state.interviewer_schedules.values())
    overlap_slots = set(all_schedules[0])
    for schedule in all_schedules[1:]:
        overlap_slots = overlap_slots.intersection(set(schedule))
        
    st.subheader("🎉 최종 추천 시간대")
    if overlap_slots:
        sorted_slots = sorted(list(overlap_slots), key=lambda x: time_slots.index(x))
        for slot in sorted_slots:
            st.info(f"⏰ **{slot}** -> 모든 면접관 참여 가능")
        st.success(f"💡 이 {len(sorted_slots)}개의 시간대를 기반으로 피면접자(지원자)에게 선택 링크를 보내면 됩니다!")
    else:
        st.error("🚨 모든 면접관이 동시에 가능한 시간대가 없습니다. 일정을 재조정해 주세요.")
        
    # 초기화 버튼
    if st.button("데이터 전체 초기화"):
        st.session_state.interviewer_schedules = {}
        st.rerun()
else:
    st.info("아직 입력된 일정이 없습니다. 면접관 일정을 먼저 입력해 주세요.")
