# CLAUDE.md — Jobhunter-Platform

Hackathon MVP. Ưu tiên: chạy được demo > đúng > đơn giản. YAGNI, không abstraction thừa.

## 1. Sản phẩm

Platform chạy workflow nhiều AI agent theo luồng CỐ ĐỊNH cho tuyển dụng, nối provider bên ngoài qua adapter.

```
UI Platform -> Orchestrator -> Filter Agent -> Interview Agent -> Schedule Agent
                                    |  (tool/API qua adapter)
                           Integration/Provider Layer (OSS giả lập ATS, ứng viên, lịch)
```

- Provider = nguồn dữ liệu/chức năng. Agent = xử lý nghiệp vụ. Orchestrator = điều phối. Không trộn trách nhiệm.
- MVP: orchestrator do platform thực thi. "Export" = workflow definition (JSON), không phải executable.
- Contract agent chung: `input`, `output` (structured), `tools`, `status` (success|failed|needs_human), `error`.
- Đổi provider = đổi adapter, không sửa workflow.

## 2. Phân công team

- Tui (owner repo này): UI platform + base workflow cố định + contract agent + export definition.
- Integration: dựng OSS provider + adapter.
- Product/Harness: product spec + harness test workflow. Spec quyết định rẽ nhánh/tiêu chí; workflow tối ưu sau theo spec.

## 3. Quy ước

- Ngôn ngữ chat: Vietnamese. Code/identifier: English.
- Chưa chốt stack -> hỏi trước khi chọn (xem docs/plan khi có).
- Điểm chưa chốt: workflow chạy trong provider hay orchestrator platform (MVP giả định: platform).
- Verify trước khi báo xong. Không tuyên bố thành công khi chưa chạy.
- Commit chỉ khi user yêu cầu.

## 4. Workflow làm việc

- Task nhiều bước: brainstorming -> writing-plans -> thực thi (skill `project-workflow`).
- Dài/sắp compact: `/checkpoint save`. Xong task: `/checkpoint done`.
- Plan lưu `docs/plans/`, spec lưu `docs/specs/`.
