import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 페이지 기본 설정
st.set_page_config(page_title="스마트 면접 일정 조율기", layout="wide")

st.title("🤝 면접관 일정 조율 및 기록 앱 (날짜 커스텀 버전)")
st.write("방장이 직접 면접 후보 날짜를 지정하고, 면접관들의 일정을 취합합니다.")

# 2. 데이터 저장을 위한 임시 세션 상태 초기화
if "interviewer_schedules" not in st.session_state:
    st.session_state.interviewer_schedules = {}

if "past_history" not in st.session_state:
    st.session_state.past_history = [
        {"📋 면접 명칭": "2026년 상반기 개발자 공채", "📅 확정 날짜": "2026-07-10", "⏰ 확정 시간대": "14:00 - 15:00", "👥 참여 면접관": "김팀장, 박파트장"},
    ]

# 3. 화면 레이아웃 분할
left_col, right_col = st.columns([2, 1])

with left_col:
    # ----------------------------------------------------
    # [구역 A] 방장의 면접 후보 날짜 설정 (최대 5개)
    # ----------------------------------------------------
    st.header("1. [방장 설정] 면접 후보 날짜 지정")
    st.write("면접을 진행할 후보 날짜를 **최대 5개**까지 선택해 주세요.")
    
    # 달력 아이콘을 통해 날짜를 복수 선택할 수 있는 st.date_input (무조건 2026년 기준)
    chosen_dates = st.date_input(
        "날짜를 클릭하여 추가하세요 (최대 5개 선택 가능)",
        value=[datetime(2026, 7, 15)], # 기본 시작일 예시
        min_value=datetime(2026, 1, 1),
        max_value=datetime(2026, 12, 31),
    )
    
    # date_input은 리스트나 튜플 형태로 값을 반환하므로 리스트로 변환 및 정렬
    if isinstance(chosen_dates, (list, tuple)):
        available_dates = sorted([d.strftime("%Y-%m-%d") for d in chosen_dates])
    else:
        available_dates = [chosen_dates.strftime("%Y-%m-%d")]
        
    # 최대 5개 제한 및 경고 문구
    if len(available_dates) > 5:
        st.error("🚨 날짜는 최대 5개까지만 선택 가능합니다! 뒤의 날짜는 제외됩니다.")
        available_dates = available_dates[:5]
        
    # 현재 선택된 날짜 보기 좋게 출력
    st.success(f"📌 현재 지정된 후보 날짜 ({len(available_dates)}개): {', '.join(available_dates)}")
    
    time_slots = [
        "09:00 - 10:00", "10:00 - 11:00", "11:00 - 12:00",
        "13:00 - 14:00", "14:00 - 15:00", "15:00 - 16:00",
        "16:00 - 17:00", "17:00 - 18:00"
    ]

    # ----------------------------------------------------
    # [구역 B] 면접관 일정 입력 (이름 입력 필수화)
    # ----------------------------------------------------
    st.header("2. 면접관 일정 입력")
    
    with st.form("interviewer_form", clear_on_submit=True):
        interviewer_name = st.text_input("👤 면접관 성함을 입력해 주세요 (필수)", placeholder="예: 홍길동 팀장")
        st.write("⚠️ **본인이 참여 가능한 날짜와 시간을 모두 체크해 주세요.**")
        
        interviewer_choices = []
        if available_dates:
            for date in available_dates:
                st.subheader(f"📅 {date}")
                cols = st.columns(4) # 4열 배치
                for i, slot in enumerate(time_slots):
                    with cols[i % 4]:
                        combined_slot = f"{date} [{slot}]"
                        if st.checkbox(slot, key=f"{interviewer_name}_{combined_slot}"):
                            interviewer_choices.append(combined_slot)
        else:
            st.warning("위의 달력에서 면접 후보 날짜를 먼저 선택해 주세요.")
            
        submit_btn = st.form_submit_button("일정 제출하기")
        
        if submit_btn:
            if not interviewer_name.strip():
                st.error("🚨 이름이 입력되지 않았습니다! 이름을 적어야 일정을 제출할 수 있습니다.")
            elif not interviewer_choices:
                st.warning("🚨 가능한 시간대를 최소 하나 이상 선택해 주세요.")
            else:
                st.session_state.interviewer_schedules[interviewer_name.strip()] = interviewer_choices
                st.success(f"✅ {interviewer_name}님의 일정이 성공적으로 등록되었습니다!")

    # ----------------------------------------------------
    # [구역 C] 실시간 집계 및 황금 시간대 도출
    # ----------------------------------------------------
    st.header("3. 실시간 조율 결과")
    
    if st.session_state.interviewer_schedules:
        st.subheader("👥 면접관별 투표 현황")
        for name, choices in st.session_state.interviewer_schedules.items():
            st.write(f"- **{name}** 면접관님: {', '.join(choices) if choices else '가능한 시간 없음'}")
            
        all_votes = list(st.session_state.interviewer_schedules.values())
        if all_votes:
            overlap_slots = set(all_votes[0])
            for vote in all_votes[1:]:
                overlap_slots = overlap_slots.intersection(set(vote))
                
            st.subheader("🎉 모두 참여 가능한 황금 시간대 추천")
            if overlap_slots:
                for slot in sorted(list(overlap_slots)):
                    st.info(f"⏰ **{slot}** ➡️ 모든 면접관 참여 가능!")
                st.balloons()
            else:
                st.error("🚨 현재 모든 면접관이 동시에 가능한 시간대가 없습니다. 일정을 재조정해 주세요.")
                
        st.write("---")
        st.subheader("🛠️ 관리자 일정 확정 메뉴")
        with st.expander("현재 일정을 확정하고 기록에 남기기"):
            confirm_title = st.text_input("면접 프로젝트 명칭", placeholder="예: 2026 하반기 인턴 면접")
            confirm_datetime = st.text_input("확정된 날짜 및 시간", placeholder="예: 2026-07-15 14:00 - 15:00")
            
            if st.button("이 일정을 과거 기록에 저장하고 현재 투표 초기화"):
                if confirm_title and confirm_datetime:
                    new_history = {
                        "📋 면접 명칭": confirm_title,
                        "📅 확정 날짜": confirm_datetime.split()[0] if len(confirm_datetime.split()) > 0 else "-",
                        "⏰ 확정 시간대": " ".join(confirm_datetime.split()[1:]) if len(confirm_datetime.split()) > 1 else "-",
                        "👥 참여 면접관": ", ".join(list(st.session_state.interviewer_schedules.keys()))
                    }
                    st.session_state.past_history.append(new_history)
                    st.session_state.interviewer_schedules = {}
                    st.success("기록이 저장되었습니다!")
                    st.rerun()
                else:
                    st.error("명칭과 확정된 일정을 모두 입력해 주세요.")
    else:
        st.info("아직 면접관들의 입력 데이터가 없습니다.")

with right_col:
    # ----------------------------------------------------
    # [구역 D] 과거에 했던 스케줄링 기록실
    # ----------------------------------------------------
    st.header("📜 과거 스케줄링 이력")
    
    if st.session_state.past_history:
        df_history = pd.DataFrame(st.session_state.past_history)
        st.dataframe(df_history, use_container_width=True, hide_index=True)
    else:
        st.caption("저장된 과거 기록이 없습니다.")
        
    if st.button("현재 투표 데이터만 강제 리셋"):
        st.session_state.interviewer_schedules = {}
        st.rerun()
