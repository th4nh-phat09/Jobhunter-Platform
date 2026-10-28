# CLAUDE.md — Jobhunter-Platform

Hackathon MVP. Ưu tiên: chạy được demo > đúng > dễ đọc > đơn giản. YAGNI, không abstraction thừa.

Plan duy nhất để làm theo: [docs/plans/PLAN.md](docs/plans/PLAN.md) (cập nhật tại chỗ, mục 14 theo dõi tiến độ). Plan gốc để đối chiếu: [docs/plans/ai_hiring_operator_mvp_platform_workflow_plan.md](docs/plans/ai_hiring_operator_mvp_platform_workflow_plan.md).

## 1. Sản phẩm

Platform agentic AI cho tuyển dụng: Supervisor (LLM) điều phối các agent, mỗi agent tự suy nghĩ + gọi tool, tool gọi provider qua adapter.

```
UI -> Supervisor (LLM + guardrail) -> Filter / Interview / Schedule Agent (ReAct + tool)
                                          -> HiringProvider (mock -> OSS provider)
```

- Supervisor = điều phối, xử lý lỗi. Agent = nghiệp vụ. Tool = gọi provider. Provider = dữ liệu/chức năng. Không trộn trách nhiệm.
- Happy path Filter → Schedule → Interview (theo brainstorm whiteboard của team; plan gốc ghi khác, brainstorm thắng). Lệch thì supervisor quyết, trong guardrail.
- Guardrail cứng bằng code: bảng chuyển bước hợp lệ, giới hạn lượt/retry, tool ghi cần người duyệt, chỉ báo success khi provider xác nhận.
- Mỗi agent chỉ dùng tool trong allowlist.
- Provider nối hai chiều: platform gọi provider (tool, pull) và provider đẩy sự kiện về `POST /events` (push). Sự kiện phải xác thực + chống trùng theo `event_id`.
- Run có thể chờ nhiều ngày (`waiting`): state lưu DB, resume khi có duyệt/sự kiện, không giữ process.
- Đổi provider = thêm adapter theo `HiringProvider`, không sửa agent/workflow.
- "Export" = workflow definition (JSON), không phải executable.

## 2. Stack

Backend: Python 3.12+, FastAPI, LangGraph, Pydantic v2, pytest. Frontend: Vite + React + TS. State: SQLite + LangGraph SQLite checkpointer (run dài ngày phải sống sót qua restart). UI poll 1s. LLM qua env (`init_chat_model`).

## 3. Phân công team

- Owner repo này: UI + base agentic workflow + contract + export.
- Integration: dựng OSS provider + adapter.
- Product/Harness: product spec + harness. Spec quyết định rule nghiệp vụ; chưa có spec thì đánh dấu `# ASSUMPTION`.

## 4. Code dễ đọc cho người mới

Team có người mới với agentic AI. Code phải đọc là hiểu, sửa không sợ vỡ.

- Mỗi file 1 trách nhiệm, tên file nói rõ nó làm gì (`filter_agent.py`, `schedule_tools.py`). Không có file `utils.py` chứa đủ thứ.
- Chia theo thư mục vai trò: `contracts/`, `providers/`, `tools/`, `agents/`, `orchestrator/`, `runs/`, `api/`.
- File dài quá ~200 dòng thì tách.
- Đầu mỗi file có docstring 1–3 dòng: file này làm gì, nằm ở đâu trong luồng.
- Tên rõ nghĩa hơn tên ngắn. Type hint đầy đủ. Ưu tiên code thẳng, dễ trace, không dùng metaprogramming hay trick.
- Prompt của agent để thành hằng số đặt tên rõ, ở đầu file agent, không nhúng rải rác trong code.
- Mock data (`backend/mock_data/`) được commit, để cả team đọc hiểu và chạy lại demo. Mỗi file mock có chú thích ngắn nói nó mô phỏng cái gì.
- Khi hướng dẫn tạo file mới: luôn nói trước "file này làm gì, nằm ở đâu trong luồng" (overview), rồi mới đưa code. File code cũng có docstring overview ở đầu.
- Comment giải thích *vì sao*, không lặp lại *cái gì*.

## 5. Quy ước

- Chat: Vietnamese, giải thích dễ hiểu (owner là SWE nhưng mới với agentic AI). Code/identifier/comment: English.
- Làm từng agent trong scope riêng: agent nào chỉ định nghĩa dữ liệu/tool/test của agent đó, chạy ổn một mình (fixture) rồi mới nối với agent trước. Chưa tới lượt thì không định nghĩa trước. Không tự điền thứ tự/scope agent từ trí nhớ: đối chiếu brainstorm của team (PLAN.md mục 7).
- Verify trước khi báo xong. Không tuyên bố thành công khi chưa chạy.
- Không log secret/API key. Key để trong `.env`, có `.env.example`.
- Commit chỉ khi user yêu cầu.

## 6. Workflow làm việc

- Task nhiều bước: brainstorming -> writing-plans -> thực thi (skill `project-workflow`).
- Dài/sắp compact: `/checkpoint save`. Xong task: `/checkpoint done`.
- Plan lưu `docs/plans/`, spec lưu `docs/specs/`.
