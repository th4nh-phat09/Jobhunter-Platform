# Jobhunter-Platform

Platform agentic AI cho tuyển dụng (hackathon MVP). Các agent điều phối quy trình tuyển dụng, lấy dữ liệu từ provider bên ngoài (ATS, lịch, mail) qua một lớp adapter.

Luồng dự kiến theo brainstorm của team: **Filter → Schedule → Interview**.

## Trạng thái hiện tại

| Phần | Trạng thái |
|---|---|
| Filter Agent (lọc ứng viên, chạy với mock provider) | Xong |
| Schedule Agent | Chưa làm |
| Interview Agent | Chưa làm |
| Supervisor, lưu state bền vững, API, UI | Chưa làm |
| Provider thật (OSS) | Chờ team integration |

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
    ├── mock_data/                # dữ liệu GIẢ mô phỏng ATS, có commit (xem README trong đó)
    │   ├── README.md
    │   ├── jobs.json
    │   └── candidates.json
    ├── app/
    │   ├── contracts/            # kiểu dữ liệu dùng chung
    │   │   ├── domain.py         #   Job, Candidate
    │   │   └── results.py        #   kết quả của Filter
    │   ├── providers/            # ranh giới với provider bên ngoài
    │   │   ├── base.py           #   HiringProvider: provider phải có những hàm gì + các loại lỗi
    │   │   └── mock.py           #   MockProvider: đọc mock_data, có chế độ giả lập provider sập
    │   ├── tools/
    │   │   └── filter_tools.py   #   tool chỉ đọc của Filter (allowlist)
    │   └── agents/
    │       ├── llm.py            #   tạo LLM OpenAI từ biến môi trường
    │       └── filter_agent.py   #   prompt + chạy agent + kiểm tra kết quả
    └── tests/                    # pytest
```

## Luồng dữ liệu (phần đã có)

```
Filter Agent (LLM, vòng ReAct)
   └─ gọi tool (filter_tools.py, chỉ đọc)
        └─ gọi HiringProvider (providers/base.py)
             ├─ MockProvider  → đọc mock_data/   (hiện tại)
             └─ adapter ATS thật                  (team integration, sau này)
```

Agent và tool chỉ biết `HiringProvider`, không biết provider cụ thể. Đổi provider = thêm một adapter, không sửa agent.

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
```

## Cho team integration

Để nối provider thật, viết một class có đủ các hàm của `HiringProvider` trong [backend/app/providers/base.py](backend/app/providers/base.py):

- `get_job(job_id) -> Job`
- `list_candidates(job_id) -> list[Candidate]`
- `get_candidate(candidate_id) -> Candidate`

Quy ước:
- Chuyển dữ liệu của provider về model trong `contracts/domain.py`; chi tiết riêng của provider chỉ nằm trong adapter.
- Lỗi phải ném đúng loại: `ProviderUnavailable` (không kết nối được), `NotFound` (không có bản ghi).
- URL, credential qua biến môi trường.

Các hàm cho Schedule và Interview sẽ được thêm vào interface khi hai agent đó được làm.

## Cho team harness

- Mock data: [backend/mock_data/README.md](backend/mock_data/README.md) giải thích từng ứng viên đại diện cho tình huống nào (chắc đạt, chắc rớt, mập mờ).
- Rule lọc hiện là bản nháp (đánh dấu `# ASSUMPTION` trong code), chờ product spec để chốt. Sửa ở `SYSTEM_PROMPT` trong [backend/app/agents/filter_agent.py](backend/app/agents/filter_agent.py).
- Kết quả của Filter: mỗi ứng viên một quyết định `pass` / `reject` / `needs_human` kèm lý do; trạng thái chung `success` / `needs_human` / `failed`.
