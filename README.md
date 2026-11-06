# Sổ kiểm soát quán nhậu

Ứng dụng nội bộ để đối soát doanh thu CUKCUK với tiền thực nhận, theo dõi thu chi, nhập xuất tồn, kiểm kê bia/thuốc/nước chấm/gia vị, phân ca và ghi sự cố order.

Quy trình hiện tại: một chi nhánh, tám nhân viên phục vụ order bằng CUKCUK trên điện thoại, năm nhân viên bếp nhận bill in, tiếp thực bưng món. Ứng dụng này bổ sung kiểm soát; không thay thế order CUKCUK. Khi tạo tài khoản, chọn cả vai trò quyền truy cập và bộ phận làm việc.

## Chạy thử

Yêu cầu Python 3.11 trở lên. Tại thư mục dự án:

    python app.py

Mở http://127.0.0.1:8000 trên cùng máy. Lần đầu tạo mật khẩu cho tài khoản chủ quán tên đăng nhập owner. Dữ liệu được lưu tại data/restaurant.db và không đi kèm mã nguồn.

Nếu không đăng nhập được, dùng tên đăng nhập `owner` và đúng mật khẩu đã đặt khi tạo tài khoản (chữ hoa/chữ thường có phân biệt). Nếu quên mật khẩu, mở PowerShell tương tác trong thư mục dự án rồi chạy `python reset_owner_password.py`. Gõ mật khẩu mới hai lần; ký tự sẽ không hiện trên màn hình. Lệnh chỉ đổi mật khẩu của tài khoản `owner`, xóa các phiên đăng nhập cũ và giữ nguyên dữ liệu quán. Không đưa mật khẩu vào tham số dòng lệnh hay gửi qua chat.

Để kiểm thử:

    python -m unittest discover -s tests -v

## Cài trên máy mới

Cài Python 3.11 trở lên, tải mã nguồn về rồi chạy `python caidat.py`. Lệnh tạo cơ sở dữ liệu SQLite trống từ `schema.sql` và khởi động ứng dụng tại http://127.0.0.1:8000. Lần đầu mở ứng dụng, tạo tài khoản chủ quán. Bộ cài không chép dữ liệu của máy cũ, không cần MySQL và không ghi đè cơ sở dữ liệu đã tồn tại. Biến môi trường CUKCUK cần thiết lập riêng trên máy mới nếu muốn gọi API. Khi thay đổi cấu trúc bảng trong mã nguồn, chạy `python generate_schema.py` để cập nhật `schema.sql` trước khi phát hành.

## Quy trình mỗi ngày

1. Tạo tài khoản và phân ca cho nhân viên.
2. Mở ca tiền, nhập tiền mặt đầu ca.
3. Tạo danh mục hàng; ghi nhập hàng bằng phiếu. Đặt tồn tối thiểu cho bia, thuốc và vật tư cần cảnh báo.
4. Ghi mọi khoản thu chi ngoài bill với lý do và mã chứng từ.
5. Cuối ca nhập tổng doanh thu CUKCUK hoặc tải CSV chuẩn hóa. Chỉ dùng một nguồn tổng doanh thu cho một ca. Nếu dùng CSV, kiểm tra file đủ toàn bộ bill trước khi khóa ca.
6. Nhập tiền mặt đếm và chuyển khoản thực nhận. Xem chênh lệch, ghi lý do rồi quản lý khóa ca.
7. Kiểm kê hàng trọng yếu. Phiếu chênh lệch chỉ đổi tồn sổ khi quản lý duyệt.
8. Xem giờ công, sự cố order và báo cáo CSV để họp vận hành.

## CSV bán hàng

Ứng dụng cung cấp file mẫu trong tab Nhập CUKCUK. Cột bắt buộc: source_row_id, item_code, quantity, amount, method. Mỗi dòng bán phải có mã dòng duy nhất; method là cash hoặc bank; amount là số nguyên VND. item_code có thể để trống cho dòng chỉ ghi doanh thu, nhưng bia/thuốc cần mã hàng đã tạo để tự trừ kho. Nhập lại cùng mã dòng trong cùng ca được bỏ qua; mã đã thuộc ca khác bị từ chối.

Định dạng này là mẫu trung gian của ứng dụng, chưa phải khẳng định định dạng xuất của CUKCUK. Cần một file xuất đã ẩn dữ liệu nhạy cảm để làm bộ chuyển đổi chính xác.

## Đồng bộ hóa đơn qua API CUKCUK

Tại CUKCUK quản lý, vào **Ứng dụng > API**, tạo mã kết nối và cho phép kết nối. Cần AppID, Domain và Secret Key. Chương trình tự chọn chi nhánh nếu API trả đúng một chi nhánh đang hoạt động; nếu có nhiều chi nhánh thì đặt thêm BranchId. Chỉ đặt các giá trị này trong biến môi trường của máy chạy ứng dụng; không ghi vào mã nguồn hoặc gửi qua chat.

Trong PowerShell, đặt 3 biến môi trường cho phiên làm việc (`$env:CUKCUK_APP_ID`, `$env:CUKCUK_DOMAIN`, `$env:CUKCUK_SECRET_KEY`); `CUKCUK_BRANCH_ID` chỉ cần khi có nhiều chi nhánh. Sau đó chạy:

```powershell
python cukcuk_sync.py --from 2026-10-01 --to 2026-10-31
```

Lệnh chỉ gọi API đọc hóa đơn, tối đa 100 hóa đơn mỗi trang. Chạy lại cùng kỳ an toàn: hóa đơn được cập nhật theo mã CUKCUK. Ứng dụng lưu mã, ngày, trạng thái, tên bàn, tổng tiền, món, số lượng và đơn vị bán; không lưu tên/số điện thoại khách, số tài khoản hoặc thông tin thẻ. Mở tab **Nhập CUKCUK** để xem các mặt hàng bán trực tiếp, món bán nhiều và doanh thu theo ngày. Mã hàng CUKCUK phải trùng mã trong kho để phân nhóm hàng. Dữ liệu API không tự ghi xuất kho để tránh trừ hai lần khi đã nhập CSV.

Trong **Kho > 1. Bia, nước, đồ ăn kèm, thuốc > Thống kê theo ngày**, chọn ngày, tuần hoặc tháng để xem từng ngày kinh doanh. Bộ lọc chỉ đọc dữ liệu đã lưu, không gọi CUKCUK. Chọn một ngày sẽ mở chi tiết sẵn; tuần/tháng mở từng ngày bằng cách bấm dòng ngày. Hóa đơn đồng bộ trước khi ứng dụng lưu đơn vị bán cần chạy lại lệnh đồng bộ cho kỳ đó để tính đúng số đã bán và chênh lệch.

## Chấm công ở máy chung

Tạo lịch làm và tài khoản nhân viên trước. Quản lý đặt PIN 6–8 số riêng cho từng người ở tab **Nhân viên**. Đặt biến môi trường `KIOSK_DEVICE_KEY` trên máy chủ thành chuỗi bí mật ngẫu nhiên từ 32 ký tự, rồi khởi động lại `app.py`. Mở `/kiosk` trên máy chung, nhập khóa thiết bị một lần khi mở trang; nhân viên nhập tài khoản, PIN và chọn chấm vào/ra. Giờ chấm lấy từ máy chủ và được gắn với ca đã phân. Không đặt máy này ngoài mạng nội bộ; nếu truy cập qua mạng, triển khai HTTPS trước khi dùng thật. PIN không chứng minh ai đang đứng trước máy: quản lý vẫn cần kiểm tra ca và xử lý trường hợp chấm hộ.

## Đối chiếu kho cuối ngày

Trong tab **Kho**, tạo mã hàng bán trực tiếp trùng `ItemCode` CUKCUK. Với nguyên liệu, khai báo định mức bằng mã món CUKCUK, nguyên liệu và lượng dùng cho một món theo đơn vị kho. Ghi số đếm **đầu ngày**, nhập hàng và hao hụt/biếu bằng phiếu kho, đồng bộ hóa đơn CUKCUK, rồi ghi số đếm **cuối ngày**. Báo cáo tính:

`Tồn dự kiến = tồn đầu + nhập/trả − hao hụt/biếu − bia/thuốc đã bán − nguyên liệu theo định mức món đã bán`

`Chênh lệch = số đếm cuối − tồn dự kiến`

Hóa đơn đang mở/chưa thu và hàng đã đưa ra bàn nhưng chưa thanh toán chưa nằm trong số đã bán của báo cáo này. Cần kiểm riêng trước khi kết luận thất thoát. Định mức phải đầy đủ, đúng đơn vị và cập nhật khi đổi công thức; nước chấm dùng tùy ý không thể suy ra chính xác bằng công thức. Dự báo lượng cần nhập ngày mai theo thứ/ngày mưa nắng chưa có đủ dữ liệu để vận hành đáng tin cậy.

Ngày kinh doanh mặc định bắt đầu lúc 05:00 sáng theo giờ Việt Nam để ca đêm sau nửa đêm vẫn thuộc ngày trước. Có thể đổi bằng biến môi trường `BUSINESS_DAY_CUTOFF_HOUR` (0–12) trước khi chạy ứng dụng. Ngày ghi số kiểm phải là ngày kinh doanh này.

## Quy trình KDS và báo hết món

Vì quán đã có KDS, bếp nên dùng chức năng **Báo hết/Báo còn** trong CUKCUK; hệ thống CUKCUK thông báo tới phục vụ và quản lý. Chỉ báo còn khi thực sự có hàng trở lại, không tự xóa tất cả thông báo hết món cuối ca. Thiết lập thời gian đổi màu order/món quá hạn trong KDS, yêu cầu bếp bấm hoàn thành/trả món và tiếp thực xác nhận món đã bưng. Xem khả năng thông báo giọng nói của phiên bản CUKCUK đang dùng trước khi làm loa đọc món riêng. API hóa đơn hiện dùng không cung cấp dòng sự kiện KDS để ứng dụng này phát nhắc món theo thời gian thực.

## Màn hình đọc và nhắc món cho tiếp thực

 Chương trình `order_monitor.py` trên máy quản lý đọc API danh sách order và chi tiết món CUKCUK theo chu kỳ. Máy tính bảng Android chạy ứng dụng trong `android-runner/` để đọc tiếng Việt cả khi chuyển sang CUKCUK. Trang `/runner` vẫn dùng được trên trình duyệt khi thử tại máy quản lý. Mặc định nhắc sau 15 phút tính từ lúc hệ thống lần đầu thấy món, lặp lại mỗi 5 phút nếu món còn chờ; có thể đổi bằng `RUNNER_LATE_MINUTES` và `RUNNER_REPEAT_MINUTES`. Máy quản lý đọc CUKCUK mặc định mỗi 30 giây (`RUNNER_POLL_SECONDS`, tối thiểu 5 giây), app Android đọc hàng đợi từ máy quản lý mỗi 5 giây. Khi có order mới hoặc tăng số phần, app đọc số phần mới thêm và tổng chưa ra của từng món trên tất cả các bàn, không đọc bàn: “Có thêm 3 phần mì xào. Tổng chưa ra 5 phần mì xào”. Nếu toàn bộ số phần là món mới, app chỉ đọc câu tổng. Hai bàn cùng gọi một món trong một lượt đồng bộ chỉ tạo một câu tổng. Hàng đợi trên màn hình vẫn giữ số bàn để bưng món đúng nơi. Tổng chưa ra bao gồm cả phần bếp đang chế biến; API hiện chưa cho ứng dụng biết bếp đã bắt đầu làm bao nhiêu phần.

 Đổi chu kỳ gọi CUKCUK bằng cách đặt `$env:RUNNER_POLL_SECONDS = "30"` trong PowerShell trước khi chạy lại `python order_monitor.py` (hợp lệ 5–300 giây). Khi API lỗi, chương trình tự giãn thời gian gọi lại theo cấp số nhân, tối đa 5 phút; khi thành công sẽ trở về chu kỳ đã đặt. Mỗi lượt quét dùng ít nhất một request danh sách (thêm request nếu phân trang) và một request chi tiết cho mỗi order đang theo dõi. Cần tính tổng request trước khi giảm chu kỳ và hỏi MISA về giới hạn tần suất nếu muốn chạy rất nhanh trong giờ cao điểm. Chu kỳ app Android hỏi máy quản lý chỉnh ngay trên màn hình app, mặc định 5 giây, hợp lệ 2–60 giây; bấm **Bắt đầu đọc món** để áp dụng. Máy quản lý chỉ xác định món hoàn thành sau khi gọi API CUKCUK và thấy trạng thái phù hợp; app Android chỉ nhận kết quả đó rồi phát tiếng. Nếu cần nhận order tức thời để bếp bắt đầu nấu, dùng thông báo trực tiếp trên CUKCUK Bếp/bar; tính năng giọng nói của CUKCUK R56 cần kiểm tra phiên bản/tài khoản vì tài liệu MISA ghi thí điểm cho một số khách hàng.

1. Đặt `RUNNER_DEVICE_KEY` là chuỗi bí mật ngẫu nhiên dài ít nhất 32 ký tự cho tiến trình `python app.py`, rồi khởi động ứng dụng. Khóa này dùng để cho phép máy tính bảng xem và xác nhận món; không dùng Secret Key CUKCUK trên máy tính bảng.
2. Ở một cửa sổ PowerShell khác, đặt `CUKCUK_APP_ID`, `CUKCUK_DOMAIN`, `CUKCUK_SECRET_KEY` và `CUKCUK_BRANCH_ID` nếu cần, rồi chạy `python order_monitor.py`. Có thể chạy `python order_monitor.py --once` để kiểm tra một lượt.
 3. Mở dự án `android-runner/` trong Android Studio, đợi Gradle đồng bộ rồi Build APK và cài lên máy tính bảng Android. Trong app nhập `https://<máy-chủ>:8000` và `RUNNER_DEVICE_KEY`, bấm **Bắt đầu đọc món** và **Thử giọng nói**. Sau đó có thể chuyển sang CUKCUK; ứng dụng có thông báo thường trực khi đang theo dõi. Cần cài giọng Text-to-Speech tiếng Việt trên máy tính bảng.

 Khi cho máy tính bảng truy cập qua mạng, đặt `RESTAURANT_HOST` thành địa chỉ LAN của máy chủ và cung cấp chứng chỉ/khóa TLS bằng `RESTAURANT_TLS_CERT` và `RESTAURANT_TLS_KEY` trước khi chạy `app.py`. Chứng chỉ phải được Android tin cậy và khớp tên máy trong URL; app không cho phép HTTP. Trình duyệt `/runner` có thể thử trên máy quản lý tại `http://127.0.0.1:8000/runner`, nhưng có thể ngừng phát khi mở CUKCUK. Cần thử dịch vụ nền, giọng tiếng Việt, Wi-Fi và chế độ tiết kiệm pin trên chính máy tính bảng sẽ dùng.

 **Chỉ một thao tác trên KDS:** đặt `RUNNER_COMPLETION_MODE=kds` cho cả `app.py` và `order_monitor.py` sau khi xác minh mã trạng thái; đặt `CUKCUK_KDS_DONE_STATUSES` trên tiến trình monitor thành mã đã xác minh. Dùng `probe_kds_status.py` với `CUKCUK_TEST_ORDER_ID` của một order thử chỉ có một món: chạy một lần, bấm hoàn thành/trả món trên KDS, rồi nhấn Enter. Chương trình chỉ in số dòng theo mã `Status`, không in món/khách. Nếu mã không đổi, API công khai không đủ dữ liệu để tự dừng nhắc theo KDS; cần MISA xác nhận API/sự kiện tương ứng. Khi trạng thái KDS được xác nhận qua API, app so sánh hàng đợi cũ và mới theo từng dòng order, gộp các phần cùng món vừa ra và đọc “Đã ra 1 phần bò nướng. Còn 1 phần”, không đọc số bàn. Món bị hủy không được đọc là đã ra. Ở chế độ KDS, không có nút **Đã phục vụ** trong ứng dụng này và máy chủ từ chối thao tác đó. Bếp bấm hoàn thành nghĩa là món đã chế biến xong, không chứng minh món đã đến bàn. Việc ra món từng phần của cùng một dòng order vẫn cần thử trên API thực tế.

 Lần đầu khởi động, món đã có từ trước được đưa vào danh sách nhưng không đọc hàng loạt. Nếu mất kết nối CUKCUK, ứng dụng báo lỗi và không thể phát hiện món mới đến khi kết nối lại. Thời gian chờ bắt đầu khi tiến trình lần đầu thấy món qua API, không phải thời gian bếp nhận bill.

## Kiểm kê web theo bốn nhóm

Trong tab **Kho**, chọn một trong bốn nhóm: hàng bán trực tiếp; đồ khô và gia vị; rau; đá và than. Tạo mặt hàng với mã trùng mã món trong CUKCUK nếu muốn đối chiếu số đã bán. Mã là khóa ghép dữ liệu, tên hiển thị có thể khác. Ghi nhập, hao hụt, biếu và số đếm thực tế bằng các biểu mẫu ở cuối trang.

Tab đầu có bảng **Kiểm nhanh cả danh sách**: chọn ngày và đầu/cuối ngày, nhập số thực đếm cho từng mã hàng (kể cả 0), bấm **Kiểm tra số liệu**, xem lại rồi bấm **Hoàn tất**. Máy chủ chỉ lưu khi danh sách đủ tất cả mặt hàng đang hoạt động trong sáu nhóm. Số đã lưu không bị thay thế âm thầm; nếu cần sửa phải xác minh chênh lệch trước.

Phần **Hàng trên hóa đơn theo bàn** lấy số lượng đã tính tiền từ hóa đơn CUKCUK đồng bộ và nhóm theo mã hàng, tên bàn. Bấm từng mặt hàng để xem các bàn. MISA có `TableName` và `Quantity` trên hóa đơn, nhưng tài liệu API công khai không có lịch sử số lượng gọi rồi hủy/trả cho từng món. Vì vậy web để “Đã gọi” và “Trả/hủy” ở trạng thái chưa có dữ liệu, không suy ra 0 hay khẳng định số đã tính tiền là lượng thực sự tiêu thụ. Hóa đơn cũ đã đồng bộ trước khi thêm cột bàn cần đồng bộ lại để điền tên bàn.

Mỗi mặt hàng dùng một đơn vị tính thống nhất. Nếu nhập bia theo thùng nhưng bán theo lon, quy đổi sang lon trước khi ghi nhập; tương tự nước theo két/chai và gia vị theo kg/g. Ghi riêng hàng biếu, trả, hỏng và dùng nội bộ để giải thích chênh lệch.

- **Bia, rượu, nước, bánh tráng, đậu phộng, thuốc:** ghi số đầu và cuối ngày; đồng bộ hóa đơn đã thu bằng `python cukcuk_sync.py --from YYYY-MM-DD --to YYYY-MM-DD`, gồm cả sáng hôm sau nếu quán đóng sau nửa đêm. Xem số bán, tồn dự kiến và chênh lệch trong bảng đối chiếu. Danh mục ban đầu từ ảnh CUKCUK hiện có 39 mặt hàng đang hoạt động; chạy `python seed_menu_catalog.py` để cập nhật danh mục. Ba mã CLNLCD, DHNTB và BORAMUKICH là món bếp nên không nằm trong danh mục này. Mã bánh tráng, đậu phộng và thuốc cần bổ sung khi có dữ liệu CUKCUK. Nút **Lấy danh sách bàn từ CUKCUK** hiển thị mọi bàn có order đang mở, kể cả bàn chưa gọi mặt hàng nào trong các nhóm theo dõi; từng cột cho biết có/chưa có và số lượng. Bánh tráng và đậu phộng được đánh dấu là hai món bắt buộc; thiếu bia/nước/thuốc chỉ là thông tin để quản lý xem xét. Nếu có ca thu ngân đang mở, chỉ lấy order tạo từ đầu ca; nếu chưa mở ca, hiển thị các order đang mở. Kết quả lưu tạm 60 giây, danh mục CUKCUK lưu tạm 6 giờ. Máy chạy web cần các biến kết nối CUKCUK giống lệnh đồng bộ. Danh sách bàn quét các order thay đổi trong 48 giờ gần nhất; nếu có bàn mở lâu hơn cần kiểm tra trực tiếp trên CUKCUK. Order ghép nhiều bàn chỉ hiển thị nhãn bàn ghép vì API không chỉ rõ mỗi món thuộc bàn nào. Mã CUKCUK chưa ghép kho phải được kiểm tra trước khi kết luận bàn thiếu món. Hóa đơn chưa tự tạo phiếu xuất kho để tránh cộng trùng với CSV nhập thủ công.
- **Đồ khô, gia vị, nước chấm:** kiểm theo tuần hoặc kiểm đột xuất. Có thể khai định mức món để xem tiêu hao dự kiến; khi thiếu định mức hoặc thiếu hóa đơn đồng bộ, bảng không kết luận chênh lệch.
- **Rau:** ghi nhập, rau hỏng và số đếm hằng ngày; định mức món chỉ dùng để so sánh, không tự thay đổi số kho.
- **Đá, than:** tạo mặt hàng nhóm đá hoặc than, rồi ghi lượng dùng thực tế trong ngày. Đây là thống kê sử dụng, không tự trừ theo món. Mỗi mặt hàng chỉ ghi một lần cho một ngày; nhập lại cùng ngày sẽ báo trùng để người quản lý kiểm tra.

Không dùng chênh lệch làm căn cứ trừ lương tự động. Xác minh trả hàng, biếu, hỏng, đơn hủy và sai đơn vị tính trước khi kết luận thất thoát. Giữ định lượng và chất lượng món theo công thức của bếp.

## Tab 1: bàn đang mở và kiểm hàng theo thùng

- Mở tab **Kho → 1. Bia, nước, đồ ăn kèm, thuốc** để tải order bàn đang mở từ CUKCUK. Chỉ gọi API khi mở tab hoặc bấm **Tải lại bàn đang mở**; không có lịch gọi mỗi 10 phút. Màu đỏ: bàn chưa gọi bia hay nước; màu cam: thiếu bánh tráng hoặc đậu phộng; bấm tên bàn để xem số lượng từng nhóm, kể cả 0. API đơn hàng lấy các thay đổi trong 48 giờ gần nhất, nên bàn mở lâu hơn cần kiểm tra trực tiếp trên CUKCUK.
- **Kiểm tra hàng** chỉ nhận ngày hiện tại. Mốc đầu ngày là số thùng nhập hôm nay; mốc cuối ngày là số thùng còn thực tế. Rượu được quy đổi 12 chai/thùng. Tồn sau nhập = số kiểm cuối hôm trước + số nhập hôm nay. Nếu không có số kiểm hôm trước, hệ thống tính 0; ngày đầu cần nhập cả hàng tồn ban đầu vào số nhận đầu ngày.
- Bảng mặt hàng tự hiện khi mở tab. Mốc đầu ngày chỉ hiện nút **Nhập hàng**; mốc cuối ngày chỉ hiện nút **Kiểm hàng**. Rượu được đếm trực tiếp theo chai. HUDA chai (hai mã) là 20 chai/thùng; Budweiser lon là 28 lon/thùng; quy cách còn trống mặc định 24 đơn vị/thùng. Nhấp một lần vào **Số lon(chai)/thùng**, **Tồn hôm trước** hoặc **Nhập hôm nay** để sửa và rời ô để lưu. Mỗi lần bấm nút tăng/giảm thay đổi 1 đơn vị; ô số chưa có dữ liệu hiển thị 0. Số nhập hôm nay trong bảng đối chiếu là số lon/chai, phải chia hết cho quy cách thùng. Budweiser chai, BIA SÀI GÒN, Hoegaarden và Hoegaarden Rosee được ẩn khỏi danh mục đang hoạt động nhưng giữ dữ liệu cũ. Chỉ chủ quán/quản lý sửa số đã lưu; lịch sử sửa được ghi audit.
- **Tồn kho và thất thoát** dùng hóa đơn CUKCUK đã thu. Chênh lệch 0 màu xanh; khác 0 đến 24 đơn vị màu cam; trên 24 đơn vị màu đỏ. Khi chưa đồng bộ đủ ngày kinh doanh và sáng hôm sau, chênh lệch chưa được kết luận.

## Giới hạn bản đầu

- CUKCUK tiếp tục xử lý order, KDS và thu ngân. Kết nối API đọc hóa đơn và danh sách order đang mở khi người quản lý yêu cầu; chưa đối chiếu giao dịch thực nhận theo từng phương thức ngân hàng hoặc nhắc món trực tiếp từ KDS.
- Ảnh hóa đơn mẫu cho biết món và tổng tiền nhưng không xác nhận tiền đã thực nhận theo phương thức nào. Để đối soát, cần báo cáo hình thức thanh toán CUKCUK cùng tiền đếm/sao kê thực tế.
- Lỗi order được ghi nhận và xác minh thủ công; số chênh lệch không tự động quy trách nhiệm nhân viên.
- Chấm công bằng nút trong ứng dụng, chưa xác minh vị trí hay thiết bị.
- Ứng dụng mặc định chỉ nghe trên 127.0.0.1. Muốn dùng nhiều thiết bị cần triển khai sau HTTPS trong mạng nội bộ và sao lưu định kỳ.
- Dữ liệu là báo cáo vận hành, không thay thế hồ sơ kế toán/thuế. Dừng ứng dụng trước khi sao chép data/restaurant.db để sao lưu thủ công.

Đặc tả và kế hoạch nằm trong specs/001-restaurant-control. Các giả định cần bạn xác nhận nằm ở cuối spec.md.
Quy trình đầu ca, bàn giao món và cuối ca nằm trong specs/001-restaurant-control/operating-process.md.
