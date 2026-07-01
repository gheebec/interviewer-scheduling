import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="실시간 면접 일정 조율기", layout="wide")
st.title("🤝 실시간 다중 접속 면접 조율 시스템 (수정/취소 지원)")

# 2. 전 세계 사용자가 실시간으로 공유할 전역 데이터베이스 공간 생성 (서버 메모리 공유 캐시)
@st.cache_resource
def get_global_db():
    return {}

global_db = get_global_db()

# 3. 최신 표준 문법으로 URL 주소 파라미터(?room=방이름) 감지 및 방 생성
try:
    room_id = st.query_parameters.get("room", "default_room")
except Exception:
    room_id = "default_room"

# 해당 방의 데이터 공간이 없다면 초기화
if room_id not in global_db:
    global_db[room_id] = {
        "dates": ["2026-07-15", "2026-07-16"], # 기본 후보 날짜
        "schedules": {},
        "history": []
    }

room_data = global_db[room_id]

# 상단 안내 바
st.info(f"🚪 **현재 접속 중인 면접 조율 방:** `{room_id}` | 🔗 이 인터넷 주소창의 URL을 그대로 복사해서 면접관들에게 공유하세요!")

# 4. 화면 레이아웃 분할
left_col, right_col = st.columns([2, 1])

with left_col:
    # ----------------------------------------------------
    # [구역 A] 방장 설정 구역 (날짜 지정 및 방 개설)
    # ----------------------------------------------------
    st.header("1. [방장 설정] 면접 후보 날짜 관리")
    st.write("새로운 면접 방을 만들거나 날짜를 조정할 수 있습니다.")
    
    # 새로운 방 이름 입력하여 링크 생성하기
    new_room_name = st.text_input("💡 새로운 면접 조율 방 만들기 (영문/숫자 추천)", placeholder="예: developer_2026")
    if st.button("새로운 면접 방 주소 생성하기"):
        if new_room_name.strip():
            st.success(f"아래 주소를 복사해서 사용하세요!\n\n`https://내앱주소.streamlit.app/?room={new_room_name.strip()}`")
            st.caption("주의: 현재 페이지 주소창에 위 주소를 입력해 이동하시면 새 방이 열립니다.")

    st.write("---")
    # 날짜 다중 선택 달력
    chosen_dates = st.date_input(
        "이 방의 면접 후보 날짜를 선택해 주세요 (최대 5개)",
        value=[datetime.strptime(d, "%Y-%m-%d") for d in room_data["dates"]],
        min_value=datetime(2026, 1, 1),
        max_value=datetime(2026, 12, 31),
    )
    
    if isinstance(chosen_dates, (list, tuple)):
        room_data["dates"] = sorted([d.strftime("%Y-%m-%d") for d in chosen_dates])[:5]
    else:
        room_data["dates"] = [chosen_dates.strftime("%Y-%m-%d")]

    st.success(f"📌 저장된 후보 날짜: {', '.join(room_data['dates'])}")
    
    time_slots = [
        "09:00 - 10:00", "10:00 - 11:00", "11:00 - 12:00",
        "13:00 - 14:00", "14:00 - 15:00", "15:00 - 16:00",
        "16:00 - 17:00", "17:00 - 18:00"
    ]

    # ----------------------------------------------------
    # [구역 B] 면접관 일정 입력 (수정 및 취소 로직 반영)
    # ----------------------------------------------------
    st.header("2. 면접관 일정 입력 / 수정")
    
    # 💡 [핵심] 이름을 먼저 입력받아 기존 데이터가 있는지 실시간 조회
    interviewer_name = st.text_input(" 👤 면접관 성함을 입력해 주세요 (필수)", placeholder="예: 홍길동 팀장").strip()
    
    if interviewer_name:
        # 이미 등록된 면접관인지 확인
        is_existing = interviewer_name in room_data["schedules"]
        if is_existing:
            st.warning(f"📢 **{interviewer_name}**님은 이미 일정을 제출하셨습니다. 아래에서 일정을 수정한 뒤 다시 제출하거나 삭제할 수 있습니다.")
            existing_slots = room_data["schedules"][interviewer_name]
        else:
            st.info(f"🌱 **{interviewer_name}**님은 신규 등록 상태입니다. 가능한 시간을 선택해 주세요.")
            existing_slots = []
            
        st.write("⚠️ **본인이 참여 가능한 날짜와 시간을 모두 체크해 주세요.**")
        
        # 폼(Form) 시작
        with st.form("interviewer_form", clear_on_submit=False):
            interviewer_choices = []
            
            for date in room_data["dates"]:
                st.subheader(f"📅 {date}")
                cols = st.columns(4)
                for i, slot in enumerate(time_slots):
                    with cols[i % 4]:
                        combined_slot = f"{date} [{slot}]"
                        
                        # 💡 [기능 추가] 기존에 골랐던 시간대라면 기본 체크박스를 True(선택됨)로 설정!
                        is_checked = combined_slot in existing_slots
                        
                        if st.checkbox(slot, value=is_checked, key=f"{room_id}_{interviewer_name}_{combined_slot}"):
                            interviewer_choices.append(combined_slot)
            
            # 버튼 레이아웃 나누기 (제출 / 삭제)
            btn_col1, btn_col2 = st.columns([1, 4])
            with btn_col1:
                submit_btn = st.form_submit_button("일정 저장하기")
            
            if submit_btn:
                if not interviewer_choices:
                    st.warning("🚨 가능한 시간대를 최소 하나 이상 선택해 주세요. (아예 취소하려면 폼 밖의 일정 삭제 버튼을 이용해 주세요.)")
                else:
                    room_data["schedules"][interviewer_name] = interviewer_choices
                    st.success(f"✅ {interviewer_name}님의 일정이 성공적으로 수정/저장되었습니다!")
                    st.rerun()
                    
        # 💡 [취소 기능] 폼 외부에서 안전하게 내 일정 전체 삭제하기
        if is_existing:
            if st.button("❌ 내 일정 전체 삭제(취소)하기", type="secondary"):
                del room_data["schedules"][interviewer_name]
                st.success(f"🗑️ {interviewer_name}님의 투표 데이터가 완전히 삭제되었습니다.")
                st.rerun()
    else:
        st.warning("💡 면접관 성함을 입력하시면 일정을 작성하거나 수정할 수 있는 체크박스가 나타납니다.")

with right_col:
    # ----------------------------------------------------
    # [구역 C] 실시간 결과 및 과거 이력 (방장 모니터링)
    # ----------------------------------------------------
    st.header("📊 실시간 취합 현황")
    
    if st.button("🔄 실시간 데이터 불러오기/새로고침"):
        st.rerun()
        
    if room_data["schedules"]:
        st.subheader("👥 면접관별 현재 투표 결과")
        for name, choices in room_data["schedules"].items():
            st.write(f"- **{name}**: {len(choices)}개 시간 선택 완료")
            with st.expander(f"{name}님이 선택한 상세 시간 보기"):
                st.caption(", ".join(choices))
                
        # 교집합 계산
        all_votes = list(room_data["schedules"].values())
        overlap_slots = set(all_votes[0])
        for vote in all_votes[1:]:
            overlap_slots = overlap_slots.intersection(set(vote))
            
        st.subheader("🎉 모두 가능한 황금 시간대")
        if overlap_slots:
            for slot in sorted(list(overlap_slots)):
                st.info(f"⏰ {slot}")
        else:
            st.error("🚨 전원 일치하는 시간이 없습니다.")
            
        # 일정 확정 및 누적
        st.write("---")
        with st.expander("🛠️ 현재 일정 확정 및 마감"):
            confirm_title = st.text_input("면접 명칭 입력")
            confirm_dt = st.text_input("최종 확정 일시 (예: 2026-07-15 10:00)")
            if st.button("확정 후 과거 기록에 누적"):
                if confirm_title and confirm_dt:
                    room_data["history"].append({
                        "📋 면접 명칭": confirm_title,
                        "📅 확정 일시": confirm_dt,
                        "👥 면접관": ", ".join(list(room_data["schedules"].keys()))
                    })
                    room_data["schedules"] = {} # 현재 투표 리셋
                    st.success("확정 기록 완료!")
                    st.rerun()
    else:
        st.info("아직 제출된 면접관 일정이 없습니다.")

    # 과거 히스토리 누적 표
    st.write("---")
    st.header("📜 이 방의 확정 이력")
    if room_data["history"]:
        st.dataframe(pd.DataFrame(room_data["history"]), use_container_width=True, hide_index=True)
    else:
        st.caption("아직 이 방에서 확정된 과거 이력이 없습니다.")
