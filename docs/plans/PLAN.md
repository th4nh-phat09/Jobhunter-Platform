# PLAN — AI Hiring Operator MVP: Platform UI + Base Agentic Workflow

> **Đây là plan duy nhất để làm theo.** Nguồn gốc: [ai_hiring_operator_mvp_platform_workflow_plan.md](ai_hiring_operator_mvp_platform_workflow_plan.md) (plan gốc, tiếng Anh, giữ nguyên để đối chiếu).
> Plan này = plan gốc (dịch, rút gọn) + các nâng cấp đã chốt với owner: Supervisor LLM, agent có tool (ReAct), hai chiều pull/push với provider, state bền vững cho run dài ngày.
> Cập nhật plan tại chỗ khi làm tới đâu hiểu thêm tới đó. Mục 14 theo dõi tiến độ.

## 1. Bối cảnh và nguyên tắc

Team xây **AI Hiring Operator**: không phải ATS mới, không phải chatbot HR. Nó điều phối công việc tuyển dụng giữa các provider bên ngoài thông qua workflow agent.

- Platform sở hữu workflow tuyển dụng; Orchestrator/Supervisor điều phối các agent theo brainstorm whiteboard của team: **Filter → Schedule → Interview** (lọc → xếp lịch → phỏng vấn thật). Plan gốc ghi Interview trước Schedule, brainstorm của team thắng.
- Integration teammate dựng provider mô phỏng từ GitHub open-source. Harness teammate viết product spec + test harness. Owner repo này làm **Platform UI + base workflow/runtime + ranh giới nối provider**.
- Workflow tối ưu dần theo product spec và kết quả harness.
- **Nguyên tắc sản phẩm:** mỗi ứng viên luôn có một bước tiếp theo rõ ràng. Trạng thái nhìn thấy được. Quyết định tuyển dụng theo tiêu chí rõ + người duyệt khi cần.

## 2. Phạm vi

**Trong phạm vi:** UI hiện workflow + trạng thái run; workflow Filter → Interview → Schedule; Supervisor + agent có tool; contract input/output; ranh giới provider (mock trước, OSS sau); run/step state, lỗi, log hiển thị trên UI; lưu state bền vững; nhận sự kiện từ provider; export workflow definition.

**Ngoài phạm vi (không làm nếu spec không yêu cầu):** workflow builder kéo-thả, agent/graph tuỳ ý do user tạo, multi-tenant enterprise, ATS đầy đủ, tích hợp provider thương mại thật, memory/fine-tune nâng cao, Kubernetes/microservice mỗi agent, observability đầy đủ, quyết định tuyển dụng tự động không qua duyệt.

## 3. Mô hình agentic (ví von phòng HR)

| Hệ thống | Ngoài đời | Vai trò |
|---|---|---|
| Supervisor (orchestrator) | Trưởng phòng HR | Đọc state, chọn bước tiếp, xử lý khi agent báo lỗi |
| Agent | Nhân viên chuyên môn | Tự suy nghĩ + gọi tool (vòng ReAct), trả kết quả có cấu trúc |
| Tool | Phần mềm nhân viên dùng | Hàm gọi provider (ATS, lịch, mail) |
| Provider | Hệ thống bên ngoài | Nguồn dữ liệu/chức năng thật |
| Guardrail | Quy định công ty | Luật cứng bằng code, LLM không vượt được |

Vòng ReAct của agent: **nghĩ → gọi tool → xem kết quả → nghĩ tiếp → trả kết quả có cấu trúc**. Dùng tool-calling native của LLM + structured output (Pydantic), không parse text `ACTION:`/`HANDOFF:` như repo MiAI tham khảo.

> **Lệch có chủ đích so với plan gốc:** plan gốc nói "agent không được ngầm điều khiển cả workflow". Ở đây Supervisor LLM được chọn bước khi lệch happy path, nhưng chỉ trong guardrail cứng (mục 8). Cần báo team integration + harness.

## 4. Kiến trúc và luồng

```
                       Platform UI
        Workflow · Trạng thái run · Chi tiết step · Duyệt
                           │  HTTP (poll 1s)
                  ┌────────▼─────────┐
   Provider ────► │  API  (FastAPI)  │ ◄──── POST /events  (provider → platform)
   (push)         └────────┬─────────┘
                           │ start / resume run
              ┌────────────▼─────────────┐
              │ Supervisor (LLM+guardrail)│◄──► SQLite: runs, events, checkpoints
              └──┬─────────┬──────────┬──┘
              Filter    Schedule    Interview   Human (duyệt trên UI)
              (ReAct)    (ReAct)    (ReAct)
                 └── tool ──► HiringProvider (mock → OSS) ──┘   (platform → provider, pull)
```

- Một app Python, các agent là module, không tách microservice.
- **UI không chứa logic workflow, không là nguồn sự thật.** Backend sở hữu state; UI chỉ hiển thị.
- Happy path: load data → Filter → Schedule → Interview → kết thúc. Lệch (lỗi, 0 ứng viên, hồ sơ mập mờ, provider sập) thì Supervisor quyết trong luật.
- Whiteboard vẽ mũi tên hai chiều giữa các agent (vd Interview xong có thể quay lại Schedule để dời lịch). Chưa chốt ở đây, xử lý khi tới bước nối agent.
- **Phần từ mục 5 trở xuống (Supervisor, guardrail, API, state) là hướng dự kiến, chưa chốt chi tiết.** Chốt khi tới bước đó, sau khi các agent trước đã chạy được.

## 5. Ranh giới provider: hai chiều

| Chiều | Ai gọi ai | Ví dụ | Cơ chế |
|---|---|---|---|
| **Pull** | Platform → Provider | Đọc job/ứng viên/lịch, đặt lịch, gửi mail | Tool của agent → `HiringProvider` (adapter) |
| **Push** | Provider → Platform | Có đơn ứng tuyển mới, ứng viên trả lời, lịch bị huỷ/đổi | Webhook `POST /events`; nếu provider không có webhook thì adapter polling định kỳ |

Interface nội bộ `HiringProvider` (chỉ làm method MVP cần, đổi tên theo provider thật):
`get_job`, `list_candidates`, `get_candidate`, `list_interviewers`, `get_availability`, `create_interview`, `get_interview`, `notify_candidate`.

Luật tích hợp:
- Mapping riêng provider nằm trong adapter; ra ngoài adapter chỉ thấy schema nội bộ (`contracts/domain.py`).
- Base URL, credential, webhook secret qua biến môi trường.
- Provider lỗi/từ chối → trả lỗi tường minh. **Không báo thành công khi provider chưa xác nhận.**
- Retry không được tạo trùng: dùng idempotency key nếu provider hỗ trợ, không thì check-before-create.
- Mock chỉ dùng dev/test, gắn nhãn rõ. Demo cuối chạy qua provider thật đã chọn.
- **Sự kiện đến:** xác thực bằng secret; chống trùng theo `event_id` (provider hay gửi lại); gắn vào run theo khoá tương quan (`interview_id` / `candidate_id`); không xác định được run thì lưu lại + báo, không bỏ.
- Lúc mock: có `POST /dev/simulate-event` để test chiều push.

Cần chốt với integration teammate: OSS nào, chạy thế nào, API nào, có webhook không, seed/reset dữ liệu, hành động nào chỉ đọc/ghi, auth + port + env, response thành công/lỗi.

## 6. Run dài ngày: state bền vững

Quy trình tuyển dụng kéo dài ngày/tuần/tháng (chờ người duyệt, chờ ứng viên trả lời, chờ tới ngày phỏng vấn). Vì vậy:

- **Run không giữ process chạy khi chờ.** Chờ thì run "đỗ" trong DB; có sự kiện thì nạp state lên chạy tiếp.
- Trạng thái chờ: `RunStatus.waiting` + `waiting_for` (`human_approval` | `candidate_reply` | `provider_event` | `scheduled_time`).
- Ba thứ đánh thức run: (1) UI duyệt/từ chối, (2) sự kiện provider `POST /events`, (3) hẹn giờ (làm sau MVP, có chỗ để cắm).
- **Lưu:** SQLite (một file, zero setup, đủ MVP; sau đổi Postgres không sửa agent).
  - Bảng `runs` (id, status, waiting_for, updated_at, data JSON) → UI đọc.
  - Bảng `events` (event_id PK, nhận lúc nào, đã xử lý chưa) → chống trùng.
  - Checkpoint graph: LangGraph SQLite checkpointer → pause/resume (`interrupt`) sống sót qua restart. Giai đoạn đầu dùng checkpointer in-memory, đổi sang SQLite ở bước 6.
- Restart server → run đang `waiting` vẫn còn, resume được. Đây là tiêu chí nghiệm thu.
- Log: không ghi secret/credential/dữ liệu cá nhân thừa.

## 7. Agent và tool (nháp, chốt theo spec và API provider thật)

Mỗi agent chỉ thấy tool trong allowlist của nó.

Scope lấy từ whiteboard brainstorm của team. Tool là nháp, chốt khi tới lượt từng agent.

| Agent | Scope (whiteboard) | Tool nháp | Loại |
|---|---|---|---|
| Filter | Lọc shortlist cho các role. Nguồn = danh sách ứng viên **đã nộp sẵn trong ATS** (provider), không tự tìm CV. "Alert HR" đã gạch, không làm | `get_job`, `list_candidates`, `get_candidate_profile` | đọc |
| Schedule | Gửi mail, xem lịch (calendar), theo dõi ứng viên (track candidates) | `get_availability`, `create_interview`, `notify_candidate`, ... | **ghi** (cần duyệt) |
| Interview | Câu hỏi do AI sinh, voice interview, transcript, so sánh ứng viên | **Chưa chốt.** Voice + transcript là scope lớn, cần quyết có làm trong MVP không | ? |

Chưa định nghĩa chi tiết tool, contract hay dữ liệu của Schedule và Interview. Làm tới lượt mới chốt.

Quy tắc nghiệp vụ cụ thể (tiêu chí lọc, loại phỏng vấn...) theo product spec; chưa có thì đánh dấu `# ASSUMPTION`.

## 8. Xử lý lỗi và guardrail

**Tầng 1 — trong agent:** slot bị lấy → lấy lịch lại chọn slot khác; interviewer kín → tìm người cùng skill; tool lỗi tạm → thử lại 1 lần.

**Tầng 2 — Supervisor:** đọc state, chọn 1 action: `call_agent(X)` | `retry_agent(X, hint)` | `ask_human(reason)` | `finish(result)`.

| Tình huống | Kết quả |
|---|---|
| 0 ứng viên qua lọc | `finish` "không có ứng viên", không đặt lịch |
| Hồ sơ mập mờ | Hồ sơ rõ đi tiếp, hồ sơ mập mờ → người duyệt |
| Không có lịch trống tuần này | `ask_human` hoặc gọi lại Schedule kèm gợi ý |
| Provider sập | `blocked`, ghi rõ lý do, không báo thành công giả |

**Guardrail (code cứng, LLM không vượt được):**
1. Bảng chuyển bước hợp lệ (vd Schedule chỉ chạy khi đã có ứng viên qua Filter; Interview chỉ chạy khi lịch đã được provider xác nhận). Chọn sai → từ chối, bắt chọn lại.
2. Giới hạn: ~15 lượt supervisor/run, 2 retry/agent, N vòng ReAct/agent. Hết → `needs_human`.
3. Tool ghi (`create_interview`, `notify_candidate`) chờ người duyệt trên UI (`interrupt`).
4. Chỉ báo thành công khi provider xác nhận.
5. Agent chỉ dùng tool trong allowlist.

## 9. Contract (nháp, chốt với harness owner)

- `AgentStatus`: success | needs_human | blocked | failed
- `StepStatus`: pending | running | success | needs_human | blocked | failed | skipped
- `RunStatus`: running | **waiting** | completed | needs_human | blocked | failed
- `AgentResult[T]`: `status`, `data: T`, `summary`, `warnings[]`, `error`, `requires_human_action`
- `StepRecord`: `step_id`, `agent`, `status`, `started_at`, `ended_at`, `summary`, `output`, `error`, `tool_calls[]` (+ lượt suy nghĩ tóm tắt)
- `Run`: `run_id`, `workflow_id`, `workflow_version`, `status`, `waiting_for`, `current_step`, `job_id`, `steps[]`, `created_at`, `updated_at`, `completed_at`
- `Event` (provider → platform): `event_id`, `type`, `occurred_at`, `correlation` (interview_id/candidate_id), `payload`

## 10. API

| Method | Path | Việc |
|---|---|---|
| GET | `/workflow` | Definition (agents, tool, version) để UI vẽ |
| GET | `/workflow/export` | JSON definition cho team/provider |
| POST | `/runs` | Bắt đầu run `{job_id}` → `run_id` |
| GET | `/runs` , `/runs/{id}` | Danh sách / chi tiết (UI poll 1s) |
| POST | `/runs/{id}/approval` | Duyệt/từ chối tool ghi `{approved, note}` |
| POST | `/events` | Provider đẩy sự kiện (secret + chống trùng) |
| POST | `/dev/simulate-event` | Giả lập sự kiện provider (chỉ mock/dev) |

## 11. Cấu trúc thư mục

Mỗi file 1 trách nhiệm, tên nói rõ (xem quy ước ở CLAUDE.md).

```
backend/
  app/
    contracts/   enums.py · domain.py · results.py · run.py · events.py
    providers/   base.py (Protocol) · mock.py (đọc mock_data, có chế độ lỗi)
    tools/       hiring_tools.py · interview_tools.py · schedule_tools.py
    agents/      llm.py · filter_agent.py · interview_agent.py · schedule_agent.py
    orchestrator/ supervisor.py · guardrails.py · graph.py
    runs/        store.py (SQLite) · runner.py (start/resume)
    events/      handler.py (xác thực, chống trùng, gắn vào run)
    api/         main.py
  mock_data/     jobs.json · candidates.json · interviewers.json · calendar.json
  data/          *.db (SQLite, không commit)
  tests/
frontend/src/    api.ts · components/ (WorkflowView, RunProgress, StepDetail, ApprovalPanel) · App.tsx
```

## 12. UI tối thiểu

- **Workflow overview:** tên, mô tả, chuỗi agent cố định, nút Run, trạng thái run.
- **Run progress:** các step theo thứ tự với trạng thái (Pending / Running / Succeeded / Needs human / Waiting / Blocked / Failed / Skipped).
- **Run details:** job + ứng viên, tóm tắt + kết quả có cấu trúc từng agent, từng lượt tool call và kết quả, lỗi/cảnh báo, timestamp.
- **Approval panel:** hiện hành động sắp làm (đặt lịch/gửi mail) + nút Duyệt/Từ chối.
- **Result view:** recruiter hiểu được: chuyện gì xảy ra với ứng viên, dừng ở đâu, đã làm gì, bước tiếp theo.
- Không lộ prompt thô/credential. Refresh/mở lại không mất run đang xem. Có trạng thái loading/rỗng/lỗi.

## 13. Stack

| Phần | Chọn |
|---|---|
| Backend | Python 3.12+, FastAPI, LangGraph, Pydantic v2 |
| LLM | `init_chat_model`, model qua env (đổi OpenAI/Claude/Gemini không sửa code) |
| State | SQLite + LangGraph SQLite checkpointer |
| Frontend | Vite + React + TS, poll 1s |
| Test | pytest |

## 14. Các bước triển khai và tiến độ

**Quy tắc: làm từng agent trong scope riêng của nó.** Mỗi agent tự có dữ liệu, tool, test riêng, chạy ổn một mình (input bằng fixture) rồi mới nối với agent trước. Nối xong chạy ổn mới qua agent tiếp. Chưa tới lượt agent nào thì không định nghĩa dữ liệu/tool/contract của agent đó. Supervisor chỉ làm sau khi có ít nhất 2 agent nối được với nhau; trước đó nối tạm bằng hàm gọi tuần tự.

Owner tự gõ code theo hướng dẫn từng bước; sau mỗi bước cập nhật plan nếu hiểu thêm.

| # | Việc | Cần LLM | Trạng thái |
|---|---|---|---|
| 1 | **Filter standalone** (chỉ scope Filter): venv, `domain.py` chỉ có Job + Candidate, mock job/ứng viên (commit, có chú thích), tool đọc, Filter Agent, test | Có từ đoạn agent | **đang làm** (venv xong) |
| 2 | **Schedule standalone**: input = shortlist giả bằng fixture; mock calendar + mail + track; tool ghi + bước duyệt (`interrupt`); thêm dữ liệu Schedule vào domain lúc này | Có | |
| 3 | **Nối Filter → Schedule** (hàm tuần tự tạm, chưa Supervisor) | Có | |
| 4 | **Interview standalone**: chốt scope trước (có voice/transcript không?) | Có | |
| 5 | **Nối Schedule → Interview**, rồi xử lý mũi tên hai chiều (dời lịch) | Có | |
| 6 | Supervisor + guardrail, test kịch bản fail | Có | |
| 7 | Lưu bền vững SQLite + resume sau restart | Không | |
| 8 | API + `/events` + `/dev/simulate-event` | Không | |
| 9 | UI | Không | |
| 10 | Export definition | Không | |
| 11 | Harness + demo + nối OSS provider thật (viết `providers/<oss>.py`, chọn bằng `PROVIDER=mock\|<oss>`) | Có | |

## 15. Definition of Done

- [ ] UI hiện workflow cố định, bắt đầu được run, hiện step/tool call/lỗi.
- [ ] Filter → Schedule → Interview chạy đúng; Supervisor xử lý được các ca lệch.
- [ ] Mỗi agent có contract + allowlist tool; output validate trước khi truyền tiếp.
- [ ] Tool ghi chờ người duyệt; chỉ báo thành công khi provider xác nhận; retry không đặt trùng.
- [ ] Run `waiting` sống sót qua restart và resume được (duyệt UI + sự kiện provider).
- [ ] Sự kiện provider trùng không xử lý hai lần.
- [ ] Qua harness: happy path + không ứng viên + provider sập + đặt lịch bị từ chối (+ needs_human nếu spec yêu cầu).
- [ ] Chi tiết riêng provider chỉ nằm trong adapter.
- [ ] Đồng đội chạy được demo theo hướng dẫn; có seed + reset.

## 16. Rủi ro và đường lùi

| Rủi ro | Giảm bằng |
|---|---|
| Supervisor LLM chọn loạn | Guardrail cứng + giới hạn lượt |
| Output LLM không ổn định, khó test | Structured output; test từng agent riêng, mock LLM khi test logic |
| Demo chết vì LLM/mạng | Chạy thử trước; Filter có thể có chế độ rule-based dự phòng |
| Trễ hackathon | Làm từng agent một; cắt scope được |
| Lệch spec | Đánh dấu `# ASSUMPTION`, chốt khi có spec |
| Tool provider thật khác mock | Chốt tool cuối theo API OSS thật |

**Đường lùi:** thay Supervisor bằng luồng cố định + rẽ nhánh theo rule, chỉ đổi file trong `orchestrator/`; agent và tool giữ nguyên. Không có hẹn giờ/nhắc → run chờ mãi, chấp nhận ở MVP.

## 17. Còn mở (cần chốt, không đoán)

- LLM provider + ai giữ API key (cần từ bước 2).
- Provider OSS nào, có webhook không (quyết định push hay polling).
- Run theo **job** (cả lô ứng viên) hay theo **ứng viên**? Run dài ngày thì theo ứng viên tự nhiên hơn, nhưng plan gốc theo job. Chờ product spec.
- Schema job/ứng viên/phỏng vấn, rule lọc, loại phỏng vấn: chờ product spec.
- Hẹn giờ/nhắc/timeout cho run chờ lâu: sau MVP.
- Auth cho demo: tạm không; `/events` luôn có secret.
- Workflow chạy trong provider hay platform: MVP giả định platform.
