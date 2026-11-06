# Tác vụ: Kiểm kê hàng bán trực tiếp

- [x] T036 Quy đổi đơn vị CUKCUK trong bảng Tồn kho và thất thoát trước khi tính chênh lệch.
- [x] T037 Không tính chênh lệch khi thiếu đơn vị bán; kiểm thử bán theo thùng và thiếu đơn vị.

- [x] T035 Khóa ba tab kho chưa hoàn thiện, ghi nhãn “Chưa triển khai” và chỉ cho thao tác tab hàng bán trực tiếp.
- [x] T033 Đồng bộ màu năm nhóm hàng và phân tách ba mục của tab kiểm kê.
- [x] T034 Rà soát tên trùng trên danh mục CUKCUK thật bằng API chỉ đọc và báo cáo mã tương ứng.

- [x] T030 Cho nhập số lẻ ở mốc đầu ngày trên giao diện và API, kiểm tra phép quy đổi.
- [x] T031 Chỉ giữ DG, DAUPHONG, COCA, HUCH, BH trong danh mục hoạt động cho năm mặt hàng trùng đã xác nhận.
- [x] T032 Quy mã bí danh từ CUKCUK về mã chính trong bàn mở, hóa đơn và báo cáo; giữ nguyên dữ liệu lịch sử.

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/inventory-views.md](contracts/inventory-views.md)

## Phase 1 — Setup

- [x] T001 Đối chiếu mã và trạng thái các mặt hàng đang có với [spec.md](spec.md) trong `menu_catalog.py`, `seed_menu_catalog.py` và dữ liệu thử.

## Phase 2 — Foundational

- [x] T002 Thêm BATR, DAUPHONG và DAPH vào nhóm kiểm kê đúng trong `menu_catalog.py` và `seed_menu_catalog.py`, không xóa lịch sử mã cũ.
- [x] T003 Bảo đảm `app.py` phân biệt danh mục CUKCUK chưa ánh xạ với số lượng thật bằng 0 khi trả dữ liệu bàn đang mở.

## Phase 3 — User Story 1: Bàn đang thiếu hàng kèm (P1)

**Goal**: Bàn đã gọi một trong hai mã đậu phộng được tính là có đậu phộng; bàn chưa ánh xạ được không bị kết luận thiếu sai.

**Independent Test**: Dùng order giả lập có BATR, DAUPHONG, DAPH, bàn ghép, bàn đóng và mã lạ; số lượng, màu và trạng thái đúng đặc tả.

- [x] T004 [US1] Cập nhật phép tổng hợp theo mã gốc và nhóm hàng trong `table_merchandise.py`.
- [x] T005 [US1] Hiển thị trạng thái chưa xác định và giữ mã gốc trong chi tiết bàn tại `static/app.js`.
- [x] T006 [US1] Kiểm tra dữ liệu bàn thiếu, bàn có hai mã đậu phộng và mã chưa ánh xạ trong `tests/test_table_merchandise.py`.

## Phase 4 — User Story 2: Nhập và kiểm hàng theo ngày (P1)

**Goal**: Ba mã mới có thể nhập/kiểm đúng quy cách; màn hình sửa một lần nhấp, giữ độ rộng và chỉ người có quyền sửa.

**Independent Test**: Nhập, kiểm, sửa quy cách và số chuyển sang trên dữ liệu thử; bảng và nhật ký cập nhật, không có phiếu ngày quá khứ.

- [x] T007 [US2] Kiểm tra quy cách mặc định 24 và quy tắc ngày hiện tại cho ba mã mới trong `app.py`, `seed_menu_catalog.py` và `tests/test_inventory_groups.py`.
- [x] T008 [US2] Xác minh ô nhập nền xanh, bước tăng 1, số 0 mặc định và thao tác một nhấp trong `static/app.js`, `static/style.css` và `static/index.html`.

## Phase 5 — User Story 3: Đối chiếu và trả/hủy (P1)

**Goal**: Chi tiết bán theo bàn có thể đối chiếu tổng; trả/hủy không có nguồn đáng tin cậy hiện “Chưa có dữ liệu”.

**Independent Test**: Từ nhiều hóa đơn thử cùng mặt hàng, tổng theo bàn khớp tổng bán; không có lịch sử hủy dòng thì không hiện 0 hoặc số ước tính.

- [x] T009 [US3] Bổ sung trạng thái không có dữ liệu trả/hủy vào dữ liệu chi tiết của `app.py`, giữ số bán thực có.
- [x] T010 [US3] Trình bày cột trả/hủy và chi tiết theo bàn đúng hợp đồng tại `static/app.js`.
- [x] T011 [US3] Xác minh tổng theo bàn và giới hạn trả/hủy bằng dữ liệu thử trong `tests/test_inventory_groups.py`.

## Final Phase — Polish & Cross-Cutting

- [x] T012 Cập nhật hướng dẫn vận hành và giới hạn nguồn CUKCUK trong `README.md`.
- [ ] T013 Chạy kịch bản trong `quickstart.md` với kết nối CUKCUK của quán; bộ kiểm thử Python (41 bài), kiểm tra cú pháp JavaScript và kiểm tra trang nội bộ đã đạt. Máy hiện chưa có cấu hình kết nối CUKCUK để xác minh dữ liệu thật.

## Phase 6 — Các yêu cầu đã chốt sau vòng làm rõ

- [x] T014 [US1] Đổi quy tắc cảnh báo đỏ sang chỉ thiếu bia trong `table_merchandise.py`, `static/app.js` và kiểm tra bàn có rượu/nước nhưng chưa có bia.
- [x] T015 [US2] Hủy hướng gắn kho với ca thu ngân theo yêu cầu mới; đặc tả 007 dùng ngày quản lý chọn và cho nhập số khi thuận tiện.
- [x] T016 [US2] Bổ sung số chai/lon lẻ ở kiểm cuối ca, kiểm tra 0 ≤ số lẻ < quy cách, tính đơn vị = thùng × quy cách + số lẻ; giữ nguyên ý nghĩa số kiểm lịch sử khi chuyển dữ liệu cũ.
- [ ] T017 [US2] Cho lưu số kiểm khi còn bàn mở; hoàn tất kiểm tra bàn mở ở cả giao diện và đường tính kết quả để không hiển thị chênh lệch cuối cùng khi chưa xác minh được.
- [ ] T018 [US3] Cho lưu số kiểm khi hóa đơn ca chưa đồng bộ đủ, gắn trạng thái chờ và chỉ tính chênh lệch khi đồng bộ đủ; không hiển thị 0 hoặc màu thất thoát trong lúc chờ.
- [ ] T019 [US2] Giới hạn toàn bộ thao tác nhập, sửa số kho và quy cách cho chủ quán/quản lý; lưu lịch sử người, thời điểm và giá trị thay đổi.
- [ ] T020 [US1–US3] Hoàn tất giao diện và kiểm thử ngày quản lý chọn, bàn còn mở, đồng bộ thiếu, tồn có chai lẻ, phân quyền và báo cáo từng mặt hàng theo đặc tả 007.
- [ ] T021 [US1–US3] Cập nhật README và chạy lại kịch bản `quickstart.md`; hoàn thành T013 khi có kết nối CUKCUK thực tế.

## Phase 7 — Nhóm hàng và thuốc (2026-11-06)

- [x] T022 [US2] Thêm TNn/TM vào danh mục đang dùng và dữ liệu kho hiện tại, giữ mã nội bộ để đối chiếu CUKCUK.
- [x] T023 [US2] Xếp bốn nhóm trên màn kiểm hàng, đặt nhãn và nút Thêm mới theo nhóm; ẩn cột mã ở bảng kết quả.
- [x] T024 [US2–US3] Đổi giá trị chưa có dữ liệu trong bảng kiểm kê và chi tiết bàn thành “-”, giữ số 0 cho giá trị đã xác nhận.
- [x] T025 [US2] Kiểm tra lại giao diện, cú pháp và luồng thêm hàng; cập nhật trạng thái các tác vụ trên.
- [x] T026 [US2] Đổi thuốc sang đơn vị gói, quy đổi một cây bằng 10 gói, đổi nhãn nhập/kiểm và xác minh lại dữ liệu hiện có.
- [x] T027 [US2] Tách Nước khỏi Món phụ theo mã nhóm CUKCUK, giữ bánh tráng và đậu phộng cùng nhóm Món phụ.
- [x] T028 [US2] Thu gọn năm nhóm nhập hàng, nhấp mở/đóng giữ số đang nhập và tìm kiếm tự mở nhóm khớp.
- [x] T029 [US2] Kiểm tra giao diện, cú pháp JavaScript và các bài kiểm thử liên quan.

## Dependencies

T001 → T002/T003 → T004–T006 (US1). T002 → T007–T008 (US2). T003 và T004 → T009–T011 (US3). T012–T013 sau các câu chuyện liên quan.

## Parallel Execution Examples

Sau T002/T003, phần trình bày của US2 trong `static/style.css` có thể được kiểm tra độc lập với dữ liệu hóa đơn của US3 trong `app.py`. Các thay đổi cùng `static/app.js` được thực hiện tuần tự để tránh ghi đè.

## Implementation Strategy

Hoàn thành US1 trước để chủ quán thấy bàn thiếu hàng kèm chính xác; tiếp đó xác minh US2 đang có; cuối cùng hoàn thiện chi tiết trả/hủy của US3. Mỗi phần được kiểm tra độc lập bằng dữ liệu giả lập trước khi dùng dữ liệu quán.
