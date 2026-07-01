import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="실시간 면접 일정 조율기", layout="wide")
st.title("🤝 실시간 다중 접속 면접 조율 시스템")

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
    # [구역 A] 방장 설정 구역 (날짜 지정 및 방 개설/삭제)
    # ----------------------------------------------------
    st.header("1. [방장 설정] 면접 후보 날짜 관리")
    st.write("새로운 면접 방을 만들거나 날짜를 조정할 수 있습니다.")
    
    new_room_name = st.text_input("💡 새로운 면접 조율 방 만들기 (영문/숫자 추천)", placeholder="예: developer_2026")
    if st.button("새로운 면접 방 주소 생성하기"):
        if new_room_name.strip():
            clean_room = new_room_name.strip()
            st.success(f"🎉 **새로운 면접 방이 준비되었습니다!**")
            st.write("아래 링크를 마우스로 드래그해서 복사한 뒤, 면접관들에게 공유하거나 주소창에 넣고 이동하세요:")
            st.code(f"?room={clean_room}")
            st.caption(f"ℹ️ 지금 보고 계신 주소창 맨 뒤에 위의 `?room={clean_room}`을 붙여서 이동하시면 새 방이 즉시 열립니다!")
        else:
            st.error("🚨 방 이름을 입력해 주세요.")

    # 💡 [기능 추가] 방장 전용 방 삭제/초기화 메뉴
    with st.expander("🗑️ [방장 전용] 현재 방 삭제 및 초기화"):
        st.warning(f"⚠️ 현재 `{room_id}` 방에 쌓인 면접관 투표 데이터와 확정 이력이 전부 영구 삭제됩니다.")
        confirm_delete = st.checkbox("네, 이 방의 데이터를 모두 삭제하는 것에 동의합니다.", key="del_confirm_check")
        
        if st.button("🚨 현재 방 데이터 완전히 삭제하기", type="primary"):
            if confirm_delete:
                # 데이터베이스에서 해당 방 삭제 또는 초기화
                if room_id == "default_room":
                    # 기본 방은 삭제하면 에러가 날 수 있으므로 백지 상태로 초기화
                    global_db["default_room"] = {
                        "dates": ["2026-07-15", "2026-07-16"],
                        "schedules": {},
                        "history": []
                    }
                else:
                    # 커스텀 방은 데이터베이스에서 완전히 제거
                    global_db.pop(room_id, None)
                
                st.success("💥 방이 성공적으로 삭제되었습니다! 메인 페이지로 복귀합니다.")
                
                # 주소창에서 파라미터를 지우고 기본 방으로 리다이렉트
                st.query_parameters.clear()
                st.rerun()
            else:
                st.error("🚨 삭제하려면 위의 '동의합니다' 체크박스에 먼저 체크해 주세요.")

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
    # [구역 B] 면접관 일정 입력
    # ----------------------------------------------------
    st.header("2. 면접관 일정 입력 / 수정")
    
    interviewer_name = st.text_input("👤 면접관 성함을 입력해 주세요 (필수)", placeholder="예: 홍길동 팀장").strip()
    
    if interviewer_name:
        is_existing = interviewer_name in room_data["schedules"]
        if is_existing:
            st.warning(f"📢 **{interviewer_name}**님은 이미 일정을 제출하셨습니다. 아래에서 일정을 수정한 뒤 다시 제출하거나 삭제할 수 있습니다.")
            existing_slots = room_data["schedules"][interviewer_name]
        else:
            st.info(f"🌱 **{interviewer_name}**님은 신규 등록 상태입니다. 가능한 시간을 선택해 주세요.")
            existing_slots = []
            
        st.write("⚠️ **본인이 참여 가능한 날짜와 시간을 모두 체크해 주세요.**")
        
        with st.form("interviewer_form", clear_on_submit=False):
            interviewer_choices = []
            
            for date in room_data["dates"]:
                st.subheader(f"📅 {date}")
                cols = st.columns(4)
                for i, slot in enumerate(time_slots):
                    with cols[i % 4]:
                        combined_slot = f"{date} [{slot}]"
                        is_checked = combined_slot in existing_slots
                        
                        if st.checkbox(slot, value=is_checked, key=f"{room_id}_{interviewer_name}_{combined_slot}"):
                            interviewer_choices.append(combined_slot)
            
            btn_col1, btn_col2 = st.columns([1, 4])
            with btn_col1:
                submit_btn = st.form_submit_button("일정 저장하기")
            
            if submit_btn:
                if not interviewer_choices:
                    st.warning("🚨 가능한 시간대를 최소 하나 이상 선택해 주세요.")
                else:
                    room_data["schedules"][interviewer_name] = interviewer_choices
                    st.success(f"✅ {interviewer_name}님의 일정이 성공적으로 수정/저장되었습니다!")
                    st.rerun()
                    
        if is_existing:
            if st.button("❌ 내 일정 전체 삭제(취소)하기", type="secondary"):
                del room_data["schedules"][interviewer_name]
                st.success(f"🗑️ {interviewer_name}님의 투표 데이터가 완전히 삭제되었습니다.")
                st.rerun()
    else:
        st.warning("💡 면접관 성함을 입력하시면 일정을 작성하거나 수정할 수 있는 체크박스가 나타납니다.")

with right_col:
    # ----------------------------------------------------
    # [구역 C] 실시간 결과 및 과거 이력
    # ----------------------------------------------------
    st.header("📊 실시간 취합 현황")
    
    if st.button("🔄 실시간 데이터 불러오기/새로고침"):
        st.rerun()
        
    if room_data["schedules"]:
        st.subheader("👥 면접관별 현재 투표 결과")
        for name, choices in room_data["schedules"].items():
            st.write(f"- **{name}**: {len(choices)}개 시간 선택 완료")
            with st.expander(f"{name}님이 선택한 상세 시간 보기"):
                st
