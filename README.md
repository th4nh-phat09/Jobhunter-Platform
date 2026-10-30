# Jobhunter-Platform

Platform agentic AI cho tuyển dụng (hackathon MVP). Các agent điều phối quy trình tuyển dụng, lấy dữ liệu từ provider bên ngoài (ATS, lịch, mail) qua một lớp adapter.

Luồng dự kiến theo brainstorm của team: **Filter → Schedule → Interview**.

## Trạng thái hiện tại

| Phần | Trạng thái |
|---|---|
| Filter Agent (lọc ứng viên, chạy với mock provider) | Xong |
| Schedule Agent: đọc dữ liệu, đề xuất slot, guardrail | Xong standalone |
| Schedule execution: calendar event, email, Slack | Chưa làm |
| Interview Agent: live transcript (AssemblyAI) + follow-up + chấm barem, có UI demo | Xong standalone |
| Supervisor, lưu state bền vững, API, UI | Chưa làm |
| HR system/provider thật | Chờ team integration |

Kế hoạch đầy đủ và tiến độ từng bước: [docs/plans/PLAN.md](docs/plans/PLAN.md). Quy ước làm việc: [CLAUDE.md](CLAUDE.md).

## Cấu trúc thư mục

```
.
├── README.md
├── CLAUDE.md                     # quy ước code + bối cảnh cho Claude Code
├── docs/plans/
│   ├── PLAN.md                   # plan đang làm theo, có bảng tiến độ
│   └── ai_hiring_operator_mvp_platform_workflow_plan.md   # plan gốc (tiếng Anh)
└── backend/
    ├── requirements.txt
    ├── .env.example              # mẫu biến môi trường (key thật để trong .env, không commit)
    ├── mock_data/                # dữ liệu GIẢ mô phỏng HR system + calendar
    │   ├── README.md
    │   ├── jobs.json             # job, duration, mentor được phép
    │   ├── candidates.json       # ứng viên
    │   ├── mentors.json          # techlead/interviewer
    │   ├── slots.json            # availability giả
    │   └── shortlist.json        # input giả của Schedule
    ├── app/
    │   ├── contracts/            # kiểu dữ liệu dùng chung
    │   │   ├── domain.py         #   Job, Candidate, Mentor, Slot
    │   │   ├── results.py         #   kết quả của Filter
    │   │   ├── schedule.py        #   proposal xếp lịch
    │   │   └── schedule_results.py #  kết quả đã validate của Schedule
    │   ├── providers/            # ranh giới với provider bên ngoài
    │   │   ├── base.py            #   HiringProvider contract
    │   │   └── mock.py            #   MockProvider đọc mock_data
    │   ├── tools/                # tool allowlist cho từng agent
    │   │   ├── filter_tools.py
    │   │   └── schedule_tools.py  #   tool đọc của Schedule
    │   └── agents/
    │       ├── llm.py            #   tạo LLM OpenAI từ biến môi trường
    │       ├── filter_agent.py   #   Filter Agent
    │       └── schedule_agent.py #   đề xuất slot + guardrail
    └── tests/                    # pytest
```

## Luồng dữ liệu hiện tại

### Filter

```
Filter Agent (LLM, vòng ReAct)
   └─ filter_tools.py (read-only allowlist)
        └─ HiringProvider
             ├─ MockProvider  → đọc mock_data/
             └─ adapter HR thật → chờ team integration
```

### Schedule standalone

```
shortlist.json (fixture từ Filter)
   └─ Schedule Agent (LLM, vòng ReAct)
        ├─ schedule_tools.py: đọc job, candidate, mentor, availability
        ├─ MockProvider: đọc jobs/candidates/mentors/slots.json
        └─ ScheduleProposal
             └─ code guardrail
                  └─ ScheduleResult: success / needs_human / failed
```

Schedule hiện mới **đề xuất slot**. Proposal phase đã có 46 test pass và chạy được với model thật. Chưa tạo calendar event, chưa gửi email, chưa báo Slack.

Agent và tool chỉ biết `HiringProvider`, không biết provider cụ thể. Đổi provider = thêm adapter, không sửa agent.

## Chạy thử

Yêu cầu: Python 3.12+. Lệnh dưới là Git Bash; đứng trong `backend/`.

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate          # Windows Git Bash. PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

cp .env.example .env                   # rồi mở .env, điền OPENAI_API_KEY (không dán key vào chat/commit)

python -m pytest -q                    # test offline; test gọi OpenAI thật tự bỏ qua nếu không có key
python -m app.agents.filter_agent      # chạy Filter Agent thật trên mock data (cần key, tốn token)
python -m app.agents.schedule_agent    # chạy Schedule Agent thật: đề xuất slot (cần key, tốn token)
```

## Cho team integration

Để nối provider HR thật, viết một class có đủ các hàm của `HiringProvider` trong [backend/app/providers/base.py](backend/app/providers/base.py):

- `get_job(job_id) -> Job` — phải có `interview_duration_minutes`, `mentor_ids`
- `list_candidates(job_id) -> list[Candidate]`
- `get_candidate(candidate_id) -> Candidate`
- `list_interviewers(job_id) -> list[Mentor]`
- `get_availability(mentor_id) -> list[Slot]`

Adapter phải map dữ liệu HR system về model nội bộ trong `contracts/domain.py`; chi tiết API riêng chỉ nằm trong adapter. Lỗi phải ném đúng loại: `ProviderUnavailable` hoặc `NotFound`. URL và credential lấy từ biến môi trường.

Sau khi provider đọc chạy ổn, mới thêm các method ghi cho bước thực thi:
`create_interview`, `notify_candidate`, `notify_recruiter`.

Schedule Agent không biết provider cụ thể. Đổi `MockProvider` sang adapter HR thật = thay object truyền vào `run_schedule_agent()`, không sửa prompt/guardrail.

## Cho team harness

- Mock data: [backend/mock_data/README.md](backend/mock_data/README.md) giải thích từng ứng viên đại diện cho tình huống nào (chắc đạt, chắc rớt, mập mờ).
- Rule lọc hiện là bản nháp (đánh dấu `# ASSUMPTION` trong code), chờ product spec để chốt. Sửa ở `SYSTEM_PROMPT` trong [backend/app/agents/filter_agent.py](backend/app/agents/filter_agent.py).
- Kết quả của Filter: mỗi ứng viên một quyết định `pass` / `reject` / `needs_human` kèm lý do; trạng thái chung `success` / `needs_human` / `failed`.
