# Mock data

Dữ liệu GIẢ mô phỏng một ATS, dùng để dev/test khi chưa có provider thật.
Được commit để cả team đọc hiểu và chạy lại demo. Provider thật sẽ thay thế
nguồn dữ liệu này, nhưng agent không đổi (xem `app/providers/base.py`).

## jobs.json
Một tin tuyển dụng: Backend Engineer (Python). Yêu cầu: python, fastapi, sql, tối thiểu 3 năm.

## candidates.json
6 ứng viên đã nộp vào job `j1`. Mỗi người cố ý đại diện một tình huống để test Filter Agent:

| id | Tên | Tình huống |
|---|---|---|
| c1 | Nguyen Van An | Chắc đạt: đủ skill, 5 năm |
| c2 | Tran Thi Binh | Chắc đạt: đủ skill, 4 năm |
| c3 | Le Van Cuong | Chắc rớt: mới 1 năm kinh nghiệm |
| c4 | Pham Thi Dung | Chắc rớt: không biết Python (Java) |
| c5 | Hoang Van Em | Mập mờ: đúng 3 năm, dùng Django thay FastAPI |
| c6 | Vo Thi Phuong | Mập mờ: 8 năm nhưng 3 năm gần nhất làm quản lý, ít code |

Dữ liệu là bản nháp (ASSUMPTION), sẽ đổi theo product spec.

## interview/
Buổi phỏng vấn giả lập cho Interview Agent (job `j1`), tạo bằng `python -m scripts.generate_mock_interview strong|weak`
(LLM viết kịch bản, OpenAI TTS đọc: techlead giọng nam, candidate giọng nữ).

| File | Mô phỏng |
|---|---|
| `j1_strong.wav` / `.json` | Candidate junior trả lời tốt. JSON = kịch bản gốc (đáp án để so transcript) |
| `j1_weak.wav` / `.json` | Candidate trả lời mơ hồ, nhầm PUT/POST và INNER/LEFT JOIN |
| `rubric_j1.json` | Barem nháp 5 tiêu chí, có mốc điểm (ASSUMPTION, thay bằng barem của team) |
