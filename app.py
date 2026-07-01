import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 페이지 및 기본 제목 설정 (가장 직관적인 순정 테마)
st.set_page_config(page_title="면접 일정 조율기", layout="centered")

st.title("🤝 실시간 다중 접속 면접 조율 시스템")
st.caption("면접관들의 가용 시간을 취합하여 전원 참석 가능한 최적의 시간대를 도출합니다.")

# 2. 전역 공유 데이터베이스 캐시
@st.cache_resource
def get_global_db():
    return {}

global_db = get_global_db()

# 3. URL 파라미터 방 ID 감지
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

# 현재 접속 방 안내 (직관적인 블루 톤 알림창)
st.info(f"🚪 **현재 접속 중인 조율 룸:** `{room_id}` | 🔗 이 주소창의 URL을 복사해서 다른 면접관들에게 공유하세요.")

st.divider()

# ----------------------------------------------------
# [SECTION 1] 실시간 조율 결과 리포트 (가장 먼저 확인하는 결과창)
# ----------------------------------------------------
st.subheader("💡 최적의 면접 시간대 추천")

if room_data["schedules"]:
    attendees = list(room_data["schedules"].keys())
    attendees_str = ", ".join([f"`{name}`" for name in attendees])
    st.markdown(f"**현재 참여 완료 ({len(attendees)}명):** {attendees_str}")
    
    # 교집합(모두 가능한 시간) 계산
    all_votes = list(room_data["schedules"].values())
    overlap_slots = set(all_votes[0])
    for vote in all_votes[1:]:
        overlap_slots = overlap_slots.intersection(set(vote))
        
    if overlap_slots:
        for slot in sorted(list(overlap_slots)):
            st.info(f"⏰ **{slot}** (모든 면접관 참여 가능)")
    else:
        st.error("🚨 현재 모든 면접관이 동시에 가능한 시간대가 없습니다. 일정을 조율해 주세요.")
else:
    st.info("아직 제출된 면접관 일정이 없습니다. 아래 양식에서 가용 시간을 등록해 주세요.")

if st.button("🔄 현황 실시간 새로고침", use_container_width=True):
    st.rerun()

st.divider()

# ----------------------------------------------------
# [SECTION 2] 면접관 일정 입력 및 수정 (메인 서식)
# ----------------------------------------------------
st.subheader("📝 나의 가용 시간 등록 및 수정")

# 💡 Anagram 오타를 깔끔하게 제거했습니다.
interviewer_name = st.text_input(
    "👤 면접관 성함을 입력해 주세요 (필수)", 
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
        st.warning(f"📢 **{interviewer_name}**님은 이미 일정을 제출하셨습니다. 아래에서 일정을 수정한 뒤 다시 제출하거나 삭제할 수 있습니다.")
        existing_slots = room_data["schedules"][interviewer_name]
    else:
        st.info(f"🌱 **{interviewer_name}**님은 신규 등록 상태입니다. 가능한 시간을 선택해 주세요.")
        existing_slots = []
        
    st.markdown("**⚠️ 본인이 참여 가능한 날짜와 시간을 모두 체크해 주세요.**")
    
    with st.container(border=True):
        with st.form("interviewer_form", clear_on_submit=False):
            interviewer_choices = []
            
            for date in room_data["dates"]:
                st.markdown(f"📅 **{date}**")
                cols = st.columns(4) # 원래대로 깔끔한 4열 배치 복구
                for i, slot in enumerate(time_slots):
                    with cols[i % 4]:
                        combined_slot = f"{date} [{slot}]"
                        is_checked = combined_slot in existing_slots
                        if st.checkbox(slot, value=is_checked, key=f"{room_id}_{interviewer_name}_{combined_slot}"):
                            interviewer_choices.append(combined_slot)
                st.write("") 
                
            submit_btn = st.form_submit_button("일정 저장하기")
            
            if submit_btn:
                if not interviewer_choices:
                    st.error("🚨 가능한 시간대를 하나 이상 선택한 후 저장해 주세요.")
                else:
                    room_data["schedules"][interviewer_name] = interviewer_choices
                    st.success("✅ 일정이 성공적으로 저장되었습니다!")
                    st.rerun()
                    
    if is_existing:
        if st.button("❌ 내 일정 전체 삭제(취소)하기", use_container_width=True):
            del room_data["schedules"][interviewer_name]
            st.success("🗑️ 데이터가 완전히 삭제되었습니다.")
            st.rerun()
else:
    st.caption("💡 성함을 적으시면 아래에 시간 선택 체크박스가 나타납니다.")

st.divider()

# ----------------------------------------------------
# [SECTION 3] 방장 전용 관리자 메뉴 (숨김 창 구조 유지)
# ----------------------------------------------------
with st.expander("⚙️ 방장 전용 관리자 메뉴 (후보 날짜 설정 / 룸 관리)"):
    st.markdown("### 📅 후보 날짜 관리")
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
        
    st.success(f"📌 현재 지정된 후보일: {', '.join(room_data['dates'])}")
    
    st.markdown("---")
    st.markdown("### 🛠️ 일정 확정 및 마감")
    confirm_title = st.text_input("면접 프로젝트 명칭", placeholder="예: 상반기_개발공채")
    confirm_dt = st.text_input("최종 확정된 일시", placeholder="예: 2026-07-15 14:00-15:00")
    if st.button("현재 조율 결과 확정 후 이력 보존", use_container_width=True):
        if confirm_title and confirm_dt:
            room_data["history"].append({
                "📋 면접 명칭": confirm_title,
                "📅 확정 일시": confirm_dt,
                "👥 참여 면접관": ", ".join(list(room_data["schedules"].keys()))
            })
            room_data["schedules"] = {}
            st.success("기록이 저장되었습니다!")
            st.rerun()

    st.markdown("---")
    st.markdown("### 💡 새로운 면접 룸 링크 개설")
    new_room_name = st.text_input("새로운 룸 이름 입력", placeholder="예: sales_2026")
    if st.button("새로운 룸 코드 생성", use_container_width=True) and new_room_name.strip():
        st.success("🎉 새로운 방 코드가 생성되었습니다!")
        st.code(f"?room={new_room_name.strip()}", language="text")
        st.caption("ℹ️ 현재 주소창 맨 뒤에 위 코드를 붙여 이동하시면 새 방이 열립니다.")

    st.markdown("---")
    # 💡 깔끔하게 고쳐진 방 삭제 안전장치 기능입니다.
    st.markdown("### 🗑️ 현재 룸 데이터 전체 파기")
    confirm_delete = st.checkbox("이 룸의 모든 투표 데이터와 확정 이력을 영구 삭제하는 것에 동의합니다.")
    if st.button("🚨 현재 룸 완전히 삭제하기", type="primary", use_container_width=True):
        if confirm_delete:
            if room_id == "default_room":
                global_db["default_room"] = {"dates": ["2026-07-15", "2026-07-16"], "schedules": {}, "history": []}
            else:
                global_db.pop(room_id, None)
            st.query_parameters.clear()
            st.success("방이 삭제되었습니다.")
            st.rerun()
        else:
            st.error("🚨 삭제하려면 위의 동의 체크박스에 먼저 체크해 주세요.")

st.divider()

# ----------------------------------------------------
# [SECTION 4] 최종 확정 이력 타임라인
# ----------------------------------------------------
st.subheader("📜 완료된 면접 확정 이력")
if room_data["history"]:
    st.dataframe(pd.DataFrame(room_data["history"]), use_container_width=True, hide_index=True)
else:
    st.caption("아직 완료된 면접 확정 이력이 없습니다.")
