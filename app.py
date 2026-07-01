%%writefile app.py
import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 페이지 기본 설정
st.set_page_config(page_title="스마트 면접 일정 조율기", layout="wide")

st.title("🤝 면접관 일정 조율 및 기록 앱 (1단계 업그레이드)")
st.write("여러 날짜와 시간대를 관리하고, 면접관별 투표 현황 및 과거 이력을 기록합니다.")

# 2. 데이터 저장을 위한 임시 세션 상태 초기화
# (주의: Streamlit Cloud 서버가 리셋되면 초기화됩니다. 실서비스 적용 시 DB 연동 필요)
if "interviewer_schedules" not in st.session_state:
    st.session_state.interviewer_schedules = {}

if "past_history" not in st.session_state:
    # 예시용 과거 기록 데이터
    st.session_state.past_history = [
        {"📋 면접 명칭": "2026년 상반기 개발자 공채", "📅 확정 날짜": "2026-07-10", "⏰ 확정 시간대": "14:00 - 15:00", "👥 참여 면접관": "김팀장, 박파트장"},
        {"📋 면접 명칭": "마케팅 인턴 면접", "📅 확정 날짜": "2026-07-12", "⏰ 확정 시간대": "10:00 - 11:00", "👥 참여 면접관": "이이사, 최팀장"}
    ]

# 3. 화면 레이아웃 분할 (좌측: 입력 및 조율 / 우측: 과거 기록 보존)
left_col, right_col = st.columns([2, 1])

with left_col:
    # ----------------------------------------------------
    # [구역 A] 면접 기본 세팅 (날짜 복수 선택 가능)
    # ----------------------------------------------------
    st.header("1. 기본 면접 후보 일정 설정")
    
    # 여러 날짜를 쉼표나 달력으로 복수 선택할 수 없어서, 멀티 셀렉트 형식으로 날짜 지정
    available_dates = st.multiselect(
        "면접 진행이 가능한 후보 날짜들을 모두 선택하세요.",
        ["2026-07-15", "2026-07-16", "2026-07-17", "2026-07-20", "2026-07-21"],
        default=["2026-07-15", "2026-07-16"]
    )
    
    time_slots = [
        "09:00 - 10:00", "10:00 - 11:00", "11:00 - 12:00",
        "13:00 - 14:00", "14:00 - 15:00", "15:00 - 16:00",
        "16:00 - 17:00", "17:00 - 18:00"
    ]
    
    st.info("💡 위의 후보 날짜와 아래 시간대를 조합하여 면접관들이 투표하게 됩니다.")

    # ----------------------------------------------------
    # [구역 B] 면접관 일정 입력 (이름 입력 필수화)
    # ----------------------------------------------------
    st.header("2. 면접관 일정 입력")
    
    with st.form("interviewer_form", clear_on_submit=True):
        # 🚨 이름 입력 필수화
        interviewer_name = st.text_input("👤 면접관 성함을 입력해 주세요 (필수)", placeholder="예: 홍길동 팀장")
        
        st.write("⚠️ **본인이 참여 가능한 날짜와 시간을 모두 체크해 주세요.**")
        
        # 날짜별로 시간대를 선택할 수 있는 다중 체크박스 생성
        interviewer_choices = []
        if available_dates:
            for date in available_dates:
                st.subheader(f"📅 {date}")
                cols = st.columns(4) # 4열로 예쁘게 배치
                for i, slot in enumerate(time_slots):
                    with cols[i % 4]:
                        # 각 날짜+시간 조합마다 고유한 체크박스 생성
                        combined_slot = f"{date} [{slot}]"
                        if st.checkbox(slot, key=f"{interviewer_name}_{combined_slot}"):
                            interviewer_choices.append(combined_slot)
        else:
            st.warning("먼저 '1. 기본 면접 후보 일정 설정'에서 날짜를 최소 하나 이상 선택해 주세요.")
            
        submit_btn = st.form_submit_button("일정 제출하기")
        
        if submit_btn:
            if not interviewer_name.strip():
                st.error("🚨 이름이 입력되지 않았습니다! 이름을 적어야 일정을 제출할 수 있습니다.")
            elif not interviewer_choices:
                st.warning("🚨 가능한 시간대를 최소 하나 이상 선택해 주세요.")
            else:
                # 면접관 이름을 Key값으로 하여 선택한 일정 리스트 저장
                st.session_state.interviewer_schedules[interviewer_name.strip()] = interviewer_choices
                st.success(f"✅ {interviewer_name}님의 일정이 성공적으로 등록되었습니다!")

    # ----------------------------------------------------
    # [구역 C] 실시간 집계 및 황금 시간대 도출
    # ----------------------------------------------------
    st.header("3. 실시간 조율 결과")
    
    if st.session_state.interviewer_schedules:
        st.subheader("👥 면접관별 투표 현황 (누가 언제 되나요?)")
        # 누가 언제 되는지 리스트로 명확하게 출력
        for name, choices in st.session_state.interviewer_schedules.items():
            st.write(f"- **{name}** 면접관님: {', '.join(choices) if choices else '가능한 시간 없음'}")
            
        # 모든 참여 면접관의 교집합(모두 가능한 시간) 계산
        all_votes = list(st.session_state.interviewer_schedules.values())
        if all_votes:
            overlap_slots = set(all_votes[0])
            for vote in all_votes[1:]:
                overlap_slots = overlap_slots.intersection(set(vote))
                
            st.subheader("🎉 모두 참여 가능한 황금 시간대 추천")
            if overlap_slots:
                # 보기 좋게 정렬하여 출력
                for slot in sorted(list(overlap_slots)):
                    st.info(f"⏰ **{slot}** ➡️ 모든 면접관 참여 가능!")
                st.balloons() # 축하 풍선 이펙트
            else:
                st.error("🚨 현재 모든 면접관이 동시에 가능한 시간대가 없습니다. 일정을 조율하거나 후보 날짜를 늘려주세요.")
                
        # 현재 스케줄을 확정 짓고 과거 기록으로 보낼 수 있는 관리자 기능
        st.write("---")
        st.subheader("🛠️ 관리자 일정 확정 메뉴")
        with st.expander("현재 일정을 확정하고 기록에 남기기"):
            confirm_title = st.text_input("면접 프로젝트 명칭", placeholder="예: 2026 하반기 인턴 면접")
            confirm_datetime = st.text_input("확정된 날짜 및 시간", placeholder="예: 2026-07-15 14:00 - 15:00")
            
            if st.button("이 일정을 과거 기록에 저장하고 현재 투표 초기화"):
                if confirm_title and confirm_datetime:
                    # 과거 기록 배열에 추가
                    new_history = {
                        "📋 면접 명칭": confirm_title,
                        "📅 확정 날짜": confirm_datetime.split()[0] if len(confirm_datetime.split()) > 0 else "-",
                        "⏰ 확정 시간대": " ".join(confirm_datetime.split()[1:]) if len(confirm_datetime.split()) > 1 else "-",
                        "👥 참여 면접관": ", ".join(list(st.session_state.interviewer_schedules.keys()))
                    }
                    st.session_state.past_history.append(new_history)
                    # 현재 투표 데이터 초기화
                    st.session_state.interviewer_schedules = {}
                    st.success("기록이 저장되었습니다! 페이지를 새로고침합니다.")
                    st.rerun()
                else:
                    st.error("명칭과 확정된 일정을 모두 입력해 주세요.")
    else:
        st.info("아직 면접관들의 입력 데이터가 없습니다. 주소를 공유하여 입력을 유도해 주세요.")

with right_col:
    # ----------------------------------------------------
    # [구역 D] 과거에 했던 스케줄링 기록실
    # ----------------------------------------------------
    st.header("📜 과거 스케줄링 이력")
    st.write("기존에 조율이 완료되어 확정되었던 면접 이력 목록입니다.")
    
    if st.session_state.past_history:
        # 데이터프레임(표) 형태로 깔끔하게 시각화
        df_history = pd.DataFrame(st.session_state.past_history)
        st.dataframe(df_history, use_container_width=True, hide_index=True)
    else:
        st.caption("저장된 과거 기록이 없습니다.")
        
    if st.button("현재 투표 데이터만 강제 리셋"):
        st.session_state.interviewer_schedules = {}
        st.rerun()
