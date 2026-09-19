# Báo Cáo Nhóm - Lab 7: Embedding & Vector Store

**Nhóm:** DDCC  
**Thành viên:** Nguyễn Đức Danh, Bùi Gia Chính, Lê Phan Việt Cường, Nguyễn Quang Duy

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong
> `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết
trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) - Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Georgetown University Library Policies & Services - quy định mượn tài liệu, course reserves, media, thiết
bị, interlibrary loan và quy định sử dụng thư viện.

**Tại sao nhóm chọn chủ đề này?**

Corpus tập trung vào một domain thống nhất nhưng có nhiều loại dịch vụ và nhiều nhóm người dùng (`student`, `faculty`,
`all`). Đặc biệt, chính sách mượn sách và course reserves có thông tin khác nhau theo đối tượng, phù hợp để đánh giá tác
động của metadata filtering và so sánh các chiến lược chunking trên cùng một corpus.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu                             | Nguồn (Source URL)                                                | Ngày lấy / Phiên bản    | Số ký tự sau clean | Metadata đã gán                                                                     |
|---|------------------------------------------|-------------------------------------------------------------------|-------------------------|-------------------:|-------------------------------------------------------------------------------------|
| 1 | Borrowing Books - Faculty                | https://library.georgetown.edu/policies/borrowing/materials/books | 2026-09-19 / not-stated |                287 | `audience=faculty`, `department=library`, `category=borrowing`, `language=en`       |
| 2 | Borrowing Books - Undergraduate Students | https://library.georgetown.edu/policies/borrowing/materials/books | 2026-09-19 / not-stated |                174 | `audience=student`, `department=library`, `category=borrowing`, `language=en`       |
| 3 | Borrowing Media                          | https://library.georgetown.edu/policies/borrowing/materials/media | 2026-09-19 / not-stated |               1192 | `audience=all`, `department=library`, `category=borrowing-media`, `language=en`     |
| 4 | Course Reserves Information for Faculty  | https://library.georgetown.edu/course-reserves/faculty            | 2026-09-19 / not-stated |               3971 | `audience=faculty`, `department=library`, `category=course-reserves`, `language=en` |
| 5 | Course Reserves Information for Students | https://library.georgetown.edu/course-reserves/students           | 2026-09-19 / not-stated |               1818 | `audience=student`, `department=library`, `category=course-reserves`, `language=en` |
| 6 | Equipment Loans                          | https://library.georgetown.edu/equipment                          | 2026-09-19 / not-stated |               2259 | `audience=all`, `department=library`, `category=equipment`, `language=en`           |
| 7 | Interlibrary and Consortium Loans        | https://library.georgetown.edu/loans                              | 2026-09-19 / not-stated |               3211 | `audience=all`, `department=library`, `category=interlibrary-loan`, `language=en`   |
| 8 | Library Use Policies                     | https://library.georgetown.edu/policies/library-use               | 2026-09-19 / not-stated |               2110 | `audience=all`, `department=library`, `category=library-use`, `language=en`         |

**Cách chuẩn hóa corpus**

- Hai tài liệu borrowing được tách theo audience từ cùng trang nguồn: `borrowing-books-undergraduate.md` chỉ giữ quy
  định dành cho undergraduate students; `borrowing-books-faculty.md` chỉ giữ các nhóm faculty.
- Các heading, bảng và danh sách được chuẩn hóa về Markdown để giảm nhiễu retrieval; menu, site title lặp, form artifact
  và navigation text đã được loại bỏ.
- Nội dung nguồn, số liệu, thời hạn và quy định được giữ theo tài liệu crawl; không tự tạo `document_version` khi nguồn
  không công bố.
- Mọi file dùng UTF-8, `doc_id` trùng với filename stem, và `sources.csv` giữ provenance 1-1.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**

- [x] Corpus có 8 tài liệu, nằm trong yêu cầu 5–10 tài liệu.
- [x] Các URL đã được crawler kiểm `robots.txt`; lượt crawl hoàn tất 8 saved, 0 skipped.
- [x] Corpus chỉ dùng nguồn công khai của Georgetown University Library.
- [x] Mỗi tài liệu có `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience`.
- [x] Mỗi tài liệu có thêm `department`, `category`, `language`.
- [x] `sources.csv` khớp 1-1 với 8 file `.md`.
- [x] `audience` có ít nhất hai giá trị khác nhau: `student`, `faculty`, `all`.
- [x] Các tài liệu đã được clean trước khi benchmark.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata    | Kiểu               | Ví dụ giá trị                                                       | Tại sao hữu ích cho retrieval?                                                           |
|--------------------|--------------------|---------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| `doc_id`           | `str`              | `borrowing-books-undergraduate`                                     | ID ổn định của document gốc; dùng để trace chunk và xóa toàn bộ chunks của một document. |
| `title`            | `str`              | `Borrowing Books - Undergraduate Students`                          | Giữ ngữ cảnh và giúp đọc/trace kết quả retrieval.                                        |
| `source_url`       | `str`              | `https://library.georgetown.edu/policies/borrowing/materials/books` | Provenance: truy vết kết quả về trang nguồn.                                             |
| `retrieved_at`     | `str (YYYY-MM-DD)` | `2026-09-19`                                                        | Ghi thời điểm thu thập corpus.                                                           |
| `document_version` | `str`              | `not-stated`                                                        | Theo dõi phiên bản nếu nguồn có nêu; dùng `not-stated` khi nguồn không công bố.          |
| `audience`         | `str`              | `student`, `faculty`, `all`                                         | Field filter bắt buộc của L3A; giúp lọc đúng nhóm người dùng trước similarity search.    |
| `department`       | `str`              | `library`                                                           | Xác định domain/đơn vị sở hữu chính sách.                                                |
| `category`         | `str`              | `borrowing`, `course-reserves`, `equipment`                         | Phân loại dịch vụ/chính sách và có thể dùng làm chiều filter bổ sung.                    |
| `language`         | `str`              | `en`                                                                | Theo dõi ngôn ngữ corpus và lựa chọn embedding phù hợp.                                  |

---

## 2. Thiết kế chiến lược (Strategy Design) - Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Baseline được chạy trên phần body đã loại YAML frontmatter với `chunk_size=700`.

| Tài liệu                        | Chiến lược (Strategy)            | Số lượng Chunk | Độ dài trung bình |
|---------------------------------|----------------------------------|---------------:|------------------:|
| `course-reserves-student`       | FixedSizeChunker (`fixed_size`)  |              3 |             639.7 |
| `course-reserves-student`       | SentenceChunker (`by_sentences`) |              7 |             257.9 |
| `course-reserves-student`       | RecursiveChunker (`recursive`)   |              3 |             605.0 |
| `equipment-loans`               | FixedSizeChunker (`fixed_size`)  |              4 |             602.2 |
| `equipment-loans`               | SentenceChunker (`by_sentences`) |              9 |             248.6 |
| `equipment-loans`               | RecursiveChunker (`recursive`)   |              4 |             563.2 |
| `interlibrary-consortium-loans` | FixedSizeChunker (`fixed_size`)  |              5 |             682.6 |
| `interlibrary-consortium-loans` | SentenceChunker (`by_sentences`) |              9 |             354.8 |
| `interlibrary-consortium-loans` | RecursiveChunker (`recursive`)   |              6 |             533.8 |

**Nhận xét baseline**

- `SentenceChunker` tạo nhiều chunk nhỏ nhất trên cả ba tài liệu, giúp giữ ranh giới câu nhưng làm tăng số lượng vector
  cần lưu và truy xuất.
- `FixedSizeChunker` tạo ít chunk hơn với độ dài trung bình lớn hơn, nhưng có thể cắt ngang ranh giới ngữ nghĩa của
  section/câu.
- `RecursiveChunker` giữ số chunk tương đối thấp trong khi ưu tiên các ranh giới paragraph, dòng và câu trước khi
  fallback sang cắt theo ký tự.

### Chiến lược của từng thành viên

**Nguyễn Đức Danh**

- **Loại chiến lược:** Heading-aware chunking + `RecursiveChunker` fallback.
- **Mô tả & lý do chọn:** Corpus Georgetown Library được chuẩn hóa dưới dạng Markdown với cấu trúc heading rõ ràng như
  `## Book Reserves`, `## Renewals`, `## Fines`, `### Recall Fines`. Chiến lược tách theo heading tận dụng chính cấu
  trúc ngữ nghĩa do tài liệu gốc cung cấp. Nếu một section vượt `chunk_size`, phần body được chia tiếp bằng
  `RecursiveChunker` và heading hierarchy được gắn lại vào từng child chunk để tránh mất ngữ cảnh.
- **Kết quả ingest CP5:** 8 documents → 36 chunks.

**Bùi Gia Chính**

- **Loại chiến lược:** Fixed-size chunking.
- **Mô tả & lý do chọn:** Dùng làm đối chứng đơn giản dựa trên kích thước cố định và overlap. Thành viên cần chạy
  benchmark riêng với cùng harness để có kết quả chính thức.

**Lê Phan Việt Cường**

- **Loại chiến lược:** Recursive chunking.
- **Mô tả & lý do chọn:** Ưu tiên các separator có ý nghĩa như paragraph, dòng và câu trước khi phải cắt theo ký tự.
  Thành viên cần chạy benchmark riêng với cùng harness để có kết quả chính thức.

**Nguyễn Quang Duy**

- **Loại chiến lược:** Sentence-based chunking.
- **Mô tả & lý do chọn:** Giữ ranh giới câu và nhóm nhiều câu thành một chunk. Thành viên cần chạy benchmark riêng với
  cùng harness để có kết quả chính thức.

### So Sánh Giữa Các Thành Viên

| Thành viên         | Chiến lược (Strategy)              | Embedding backend                                             | Số chunk | Điểm truy xuất (/10) | Điểm mạnh                                                                                 | Điểm yếu / lưu ý                                                                                                                                                         |
|--------------------|------------------------------------|---------------------------------------------------------------|---------:|---------------------:|-------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Nguyễn Đức Danh    | Heading-aware + Recursive fallback | `gemini-embedding-001`                                        |       36 |            **10/10** | Giữ heading/section context; 5/5 query có answer-bearing context trong top-3              | Q1 không filter bị faculty policy chiếm top-1; một số answer cần tổng hợp nhiều chunk                                                                                    |
| Lê Phan Việt Cường | Recursive                          | `gemini-embedding-001`                                        |       39 |            **10/10** | Boundary tự nhiên; 5/5 query retrieval thành công; Q1 đúng top-1 ngay cả khi không filter | Không bảo toàn heading hierarchy tường minh                                                                                                                              |
| Bùi Gia Chính      | Fixed-size                         | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |       30 |             **8/10** | Đơn giản, ít chunk, Q1/Q2/Q4/Q5 retrieval tốt                                             | Q3 thất bại ở content level: lấy được `at least 1 day in advance` nhưng thiếu `Reserve this item`; embedding backend khác nên không phải controlled comparison hoàn toàn |
| Nguyễn Quang Duy   | Sentence-based                     | Chưa nhận kết quả CP6                                         |        — |                    — | Strategy đã được phân công ở CP5                                                          | Chưa có benchmark result tại thời điểm tổng hợp báo cáo                                                                                                                  |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**

Trong các kết quả đã nhận, **Heading-aware + Recursive fallback** và **Recursive** cùng đạt **10/10**, nên chưa có cơ sở
để tuyên bố một chiến lược duy nhất thắng tuyệt đối. Heading-aware phù hợp rõ với corpus policy Markdown vì giữ được
heading/section context; Recursive lại cho kết quả rất cạnh tranh mà không cần phụ thuộc trực tiếp vào heading
hierarchy.

Fixed-size đạt **8/10** và failure ở Q3 cho thấy rủi ro của việc cắt theo kích thước: hai mẩu thông tin cần cho một gold
answer có thể nằm ở các vùng khác nhau và không cùng xuất hiện trong top-3 context. Tuy nhiên, Fixed-size được chạy bằng
`paraphrase-multilingual-MiniLM-L12-v2`, trong khi Danh và Cường dùng `gemini-embedding-001`, nên chênh lệch điểm không
thể quy hoàn toàn cho chunking strategy.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) - Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng và có thể kiểm chứng từ corpus. Câu Q1 bắt buộc dùng
> `metadata_filter={"audience": "student"}` để phân biệt borrowing policy của sinh viên với faculty.

| # | Câu hỏi (Query)                                                                   | Câu trả lời chuẩn (Gold Answer)                                                                                                                                       | Chunk/section chứa thông tin                                                                  |
|---|-----------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| 1 | How long can I borrow books?                                                      | Đối với undergraduate student: số sách không giới hạn và thời hạn mượn là 6 tuần.                                                                                     | `borrowing-books-undergraduate` - `## Georgetown Users`                                       |
| 2 | How many reserve items may a student borrow at one time?                          | Sinh viên được mượn tối đa 3 reserve items cùng một lúc.                                                                                                              | `course-reserves-student` - `## Book Reserves`                                                |
| 3 | How do I request library equipment, and how far in advance must I reserve it?     | Từ trang thiết bị, chọn “Reserve this item”, đăng nhập tài khoản thư viện và gửi request; reservation phải được thực hiện ít nhất 1 ngày trước.                       | `equipment-loans` - `## Requesting Equipment` và `## Media Equipment Checkout / Reservations` |
| 4 | How long do Interlibrary Loan requests usually take to arrive?                    | Thời gian giao trung bình của Interlibrary Loan là 7–14 ngày làm việc.                                                                                                | `interlibrary-consortium-loans` - `## Items from Other Locations`                             |
| 5 | Where is food allowed in Lauinger Library, and what kinds of food are prohibited? | Food chỉ được phép ở tầng 2 Lauinger Library; ví dụ thực phẩm bị cấm gồm pizza, hamburgers, fries, ice cream, hot subs và các loại đồ ăn có mùi, dầu mỡ hoặc bừa bộn. | `library-use-policy` - `## General Policies`                                                  |

### Tổng hợp chất lượng truy xuất của nhóm

| #        | Câu hỏi                                                                           | Heading-aware (Danh) | Recursive (Cường) | Fixed-size (Chính) | Kết luận từ kết quả đã có                                                     |
|----------|-----------------------------------------------------------------------------------|---------------------:|------------------:|-------------------:|-------------------------------------------------------------------------------|
| 1        | How long can I borrow books?                                                      |                  2/2 |               2/2 |                2/2 | Cả ba strategy lấy được answer; tác động metadata khác nhau giữa các strategy |
| 2        | How many reserve items may a student borrow at one time?                          |                  2/2 |               2/2 |                2/2 | Cả ba lấy được answer-bearing chunk                                           |
| 3        | How do I request library equipment, and how far in advance must I reserve it?     |                  2/2 |               2/2 |            **0/2** | Fixed-size lấy đúng `doc_id` nhưng thiếu một answer marker trong top-3        |
| 4        | How long do Interlibrary Loan requests usually take to arrive?                    |                  2/2 |               2/2 |                2/2 | Cả ba lấy đúng answer                                                         |
| 5        | Where is food allowed in Lauinger Library, and what kinds of food are prohibited? |                  2/2 |               2/2 |                2/2 | Cả ba lấy đúng answer                                                         |
| **Tổng** |                                                                                   |            **10/10** |         **10/10** |           **8/10** | Sentence-based chưa có kết quả                                                |

**Failure case nổi bật — Fixed-size / Q3**

Ở Q3, Fixed-size có `equipment-loans` trong top-3 nên nếu chỉ chấm theo `doc_id` sẽ bị coi nhầm là thành công. Tuy
nhiên, context retrieved chỉ chứa marker `at least 1 day in advance` và thiếu `Reserve this item`, nên không đủ để trả
lời đầy đủ gold answer. Đây là ví dụ trực tiếp cho cảnh báo của lab rằng **gold doc hit không đồng nghĩa answer-bearing
chunk hit**.

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**

Có, rõ nhất ở Q1 nhưng mức tác động phụ thuộc strategy. Với Heading-aware của Danh, khi **không filter**,
`borrowing-books-faculty` đứng top-1 (`0.7067`) và `borrowing-books-undergraduate` đứng top-2 (`0.7045`). Khi dùng
`metadata_filter={"audience": "student"}`, undergraduate policy trở thành top-1 và faculty policy bị loại khỏi candidate
set.

Với Recursive của Cường, undergraduate policy đã đứng top-1 ngay cả khi không filter (`0.7090`), còn faculty ở top-2
(`0.6962`); filter không đổi top-1 nhưng vẫn tăng precision bằng cách loại tài liệu sai audience. Fixed-size của Chính
cũng giữ undergraduate ở top-1 khi không filter. Như vậy metadata filtering vẫn hữu ích để ràng buộc candidate set,
nhưng mức cải thiện ranking phụ thuộc vào chunking và embedding backend.


---

## 4. Thuyết trình (Demo) & Bài học nhóm - Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**

1. **Đúng `doc_id` chưa đủ.** Fixed-size ở Q3 có gold document trong top-3 nhưng context thiếu marker
   `Reserve this item`, nên content-level evaluation cho 0/2. Đây là ví dụ rõ nhất về lý do phải chấm theo
   answer-bearing chunk.
2. **Metadata filtering có giá trị thực tế.** Ở Heading-aware Q1, không filter khiến faculty policy đứng top-1; filter
   `audience=student` đưa undergraduate policy lên top-1. Với Recursive và Fixed-size, top-1 vốn đã đúng nhưng filter
   vẫn tăng precision của candidate set.
3. **Heading-aware và Recursive đều phù hợp policy corpus.** Hai strategy đã nhận kết quả đều đạt 10/10. Heading-aware
   tận dụng cấu trúc tài liệu; Recursive giữ boundary tự nhiên mà không cần heading-specific logic.
4. **Một answer có thể cần nhiều chunk.** Q3 và Q5 ở Heading-aware cần tổng hợp từ nhiều chunk liên tiếp, nên top-k
   retrieval và agent grounding quan trọng hơn chỉ nhìn top-1.
5. **So sánh strategy phải kiểm soát embedding backend.** Fixed-size hiện dùng MiniLM local còn Heading-aware/Recursive
   dùng Gemini embedding; vì vậy chênh lệch 8/10 và 10/10 chỉ là quan sát trên các lượt chạy đã có, không phải bằng
   chứng nhân quả tuyệt đối do chunking.

**Bài học rút ra khi so sánh trong nhóm:**

Chunking ảnh hưởng trực tiếp tới việc một answer-bearing span có được giữ nguyên trong cùng chunk hay không. Các
strategy dựa trên boundary ngữ nghĩa như Heading-aware và Recursive cho kết quả ổn định trên corpus policy hiện tại. Tuy
nhiên, metadata schema và embedding backend cũng tác động mạnh tới ranking, nên một benchmark công bằng cần giữ corpus,
query, gold answer, top-k và embedding backend nhất quán.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**

- Giữ `audience` ở mọi chunk vì filter đã chứng minh có ích trên Q1.
- Giữ heading/section context trong policy documents.
- Với Fixed-size, cân nhắc overlap lớn hơn hoặc neighboring-chunk retrieval để giảm lỗi như Q3.
- Chuẩn hóa **một embedding backend duy nhất cho cả nhóm** trước khi benchmark để comparison chỉ phản ánh khác biệt
  chunking.
- Thêm answer markers/evidence strings ngay từ khi thiết kế benchmark để tránh chấm đúng chỉ vì `doc_id` trùng.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí                                 | Điểm tự đánh giá |
|------------------------------------------|-----------------:|
| Lựa chọn tài liệu (Document Set Quality) |          10 / 10 |
| Thiết kế chiến lược (Strategy Design)    |          13 / 15 |
| Chất lượng truy xuất (Retrieval Quality) |           9 / 10 |
| Thuyết trình (Demo)                      |            4 / 5 |
| **Tổng phần nhóm**                       |      **36 / 40** |
