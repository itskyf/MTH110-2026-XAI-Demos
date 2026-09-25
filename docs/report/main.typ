#set document(
  title: "Bốn dạng bằng chứng cho một hành vi sinh cục bộ của mô hình ngôn ngữ",
  author: "MTH110-2026-XAI-Demos",
)
#set page(paper: "a4", margin: (x: 2.1cm, y: 2cm), numbering: "1")
#set text(font: "Noto Serif", size: 10.5pt, lang: "vi")
#set par(leading: 0.6em)
#show heading: set text(font: "Noto Sans")
#set heading(numbering: "1.")

#align(center)[
  #text(font: "Noto Sans", size: 17pt, weight: "bold")[
    Bốn dạng bằng chứng cho một hành vi sinh cục bộ của mô hình ngôn ngữ
  ]

  #v(0.5em)
  MTH110 — Explainable AI · Báo cáo nghiên cứu
]

#v(1em)

*Tóm tắt.* Báo cáo hỏi: đối với một hành vi sinh cục bộ đã cố định, lời tự giải thích, phép thay đổi đầu vào có kiểm soát, Integrated Gradients (IG), và phép thay thế kích hoạt nội bộ cung cấp những bằng chứng bổ sung nào, và chúng đồng thuận hay bất đồng ở đâu? Trên ba trường hợp đã đóng băng của Qwen3-0.6B, trường hợp số học cho thấy điểm đo chọn nhãn sai A rất sát ranh giới, trong khi lời tự giải thích lại khẳng định B là đáp án đúng và nhắc đến tín hiệu gợi ý B. Phép đổi duy nhất tín hiệu ấy và phép thay thế kích hoạt tại vị trí của nó làm thay đổi điểm theo hướng phù hợp với tác động của tín hiệu; IG gán cho token này giá trị dương theo một đường tham chiếu nhân tạo. Các phép đo nói về các đối tượng và can thiệp khác nhau. Chúng không chứng minh lời tự giải thích trung thực hay xác lập toàn bộ cơ chế suy luận.

= Câu hỏi và khung GenXAI

Schneider (2024) phân biệt *đầu ra của thuật toán GenXAI* (lời giải thích) với thông tin đầu vào và nội bộ mà phương pháp XAI cần để tạo ra lời giải thích ấy. Ông cũng phân biệt phạm vi của lời giải thích theo phần đầu ra và quan hệ đầu vào–đầu ra của *hệ AI gốc* được giải thích. Các chiều phạm vi này nói về *cái gì của hệ AI gốc được giải thích*, không phải cổng vào/ra của thuật toán XAI. Ở đây, đầu vào gốc là lời nhắc, còn đầu ra gốc tại vị trí trả lời đầu tiên là logits của mô hình; so sánh logits A/B cho nhãn được đo. Hành vi đầu ra tập trung cần giải thích là ưu thế tương đối giữa hai token trả lời A/B tại vị trí đó, trong một quan hệ đầu vào–đầu ra đơn lẻ. Điểm $F$ bên dưới *lượng hóa* hành vi ấy cho nghiên cứu; bản thân $F$ không phải câu trả lời tự nhiên của mô hình và cũng không phải lời giải thích. Lời nhắc và mô hình là hai nguồn nền tảng; dữ liệu huấn luyện và quá trình tối ưu không được khảo sát. Khung phân loại và các desiderata như tính trung thực, tính hợp lý bề ngoài, tính đầy đủ, độ nhạy và độ vững đến từ Schneider; quy trình so sánh bốn dạng bằng chứng là thiết kế của dự án này.

Lời tự giải thích do chính mô hình sinh ra sau khi quyết định đã được cố định, nên chỉ cần truy cập đầu ra kiểu hộp đen. Phép đổi tín hiệu gợi ý quan sát tác động hành vi; nhãn chọn có thể thấy bằng hộp đen, còn chênh lệch logit $F$ cụ thể cần truy cập điểm số kiểu hộp xám. IG cần gradient và embedding; thay thế kích hoạt cần trạng thái nội bộ, nên hai phép này đòi hỏi truy cập hộp trắng. Theo Schneider, phân biệt *mô hình tự giải thích* với *thuật toán giải thích* cũng quan trọng: văn bản do mô hình phát biểu không phải phép đo trực tiếp của tính toán nội bộ. Bảng sau tách đầu vào và kết quả của từng bước; một số kết quả là hiện vật giải thích, số khác là đại lượng can thiệp. Việc đặt chúng cạnh nhau nhằm đối chiếu phạm vi bằng chứng, không xếp hạng các phương pháp.

#text(size: 8.5pt)[
  #table(
    columns: (2.2cm, 4.5cm, 4.1cm, 1fr),
    inset: 4pt,
    table.header(
      [*Hệ / phép*], [*Đầu vào*], [*Đầu ra*], [*Câu hỏi được trả lời*]
    ),
    [Mô hình gốc],
    [Lời nhắc câu hỏi, đáp án A/B và cue],
    [Logits tại token trả lời; nhãn A/B suy ra từ hai logits],
    [Mô hình ưu tiên nhãn nào?],

    [Tự giải thích],
    [Lời nhắc riêng, có nhãn đã chọn],
    [Văn bản mô hình phát biểu],
    [Mô hình nói vì sao đã chọn nhãn?],

    [IG],
    [Embedding clean, tham chiếu dấu cách, gradient của $F$],
    [Attribution có dấu theo token],
    [Đường embedding quy phần chênh $F$ cho token nào?],

    [Đổi đầu vào],
    [Hai lời nhắc chỉ khác cue; điểm $F$ của hai lượt],
    [$Delta F_"input"$],
    [Đổi cue làm điểm thay đổi bao nhiêu?],

    [Patch kích hoạt],
    [Kích hoạt cue clean/contrast và điểm $F$],
    [Hiệu ứng patch theo tầng],
    [Thay vector cue clean ảnh hưởng điểm contrast thế nào?],
  )
]

= Thiết kế và ý nghĩa toán học

Thí nghiệm dùng checkpoint Qwen/Qwen3-0.6B tại revision `c1899de289a04d12100db370d81485cdf75e47ca`, float32, chế độ đánh giá và cùng vị trí sinh token sau khuôn chat không bật chế độ suy nghĩ. Mỗi câu hỏi có hai nhãn A/B, với $y^+$ là nhãn đúng và $y^-$ là nhãn còn lại. Cả hai là token đơn theo tokenizer đã cố định. Điểm đích dùng xuyên suốt là

$ F(x) = z_(y^+)(x) - z_(y^-)(x), $

trong đó $z_y$ là logit trước softmax tại vị trí trả lời cố định. $F$ được tính từ đầu ra logits để lượng hóa ưu thế A/B, rồi dùng làm cùng một điểm đích cho các phép phân tích; nó không phải đầu ra văn bản hay hiện vật giải thích. Dấu dương của $F$ nghĩa là nhãn đúng có logit cao hơn nhãn kia; nó không nói nhãn đó có xác suất lớn hơn mọi token khác trong từ vựng. Cặp *clean/contrast* chỉ khác ở một token gợi ý `Cue: B` hoặc `Cue: A`; "clean" là tên vận hành, không ngụ ý đầu vào không có thiên lệch. Ba trường hợp đóng băng gồm hiệu chuẩn (thủ đô Pháp), số học ($7+5$), và logic (Mira là mèo; mọi mèo đều là động vật có vú). Số học và logic là hai trường hợp nghiên cứu; hiệu chuẩn chỉ kiểm tra rằng quy trình cho tín hiệu có thể quan sát.

== Lời tự giải thích và can thiệp đầu vào

Sau khi đo điểm và chọn nhãn có logit cao hơn giữa A/B, một lời nhắc riêng cho mô hình biết nhãn đã chọn rồi yêu cầu giải thích; văn bản được sinh tham lam, tối đa 64 token mới. Vì nhãn được cung cấp trong lời nhắc thứ hai, phát biểu này không phải một quyết định độc lập. Nghiên cứu của Turpin và cộng sự (2023) cho thấy trong thiết lập chain-of-thought khác, mô hình có thể chịu ảnh hưởng của tín hiệu gây thiên lệch mà không nói ra. Công trình đó là lý do phải thận trọng với lời tự giải thích, không phải bằng chứng rằng từng câu ở đây thiếu trung thực.

Đổi duy nhất token tín hiệu gợi ý trước khi xem bản đồ IG cho hiệu ứng đầu vào hữu hạn

$ Delta F_"input" = F(x^"contrast") - F(x^"clean"). $

Giá trị âm nghĩa là phép đổi làm giảm ưu thế logit của nhãn đúng. Đây là tác động của đúng phép đổi đã định trước, không phải đạo hàm cục bộ, và không suy rộng sang mọi cách viết tương đương của lời nhắc. Phép đổi cũng không tự xác định cơ chế nội bộ gây tác động.

== IG và phép kiểm tra số học

Với embedding đầu vào $e$, tham chiếu $e'$ và đường thẳng nối hai điểm, IG theo chiều $i$ được định nghĩa bởi

$
  "IG"_i(e) = (e_i-e'_i) integral_0^1 (partial F(e' + alpha(e-e')))/(partial e_i) dif alpha.
$

Giá trị của mỗi token là tổng *có dấu* trên các chiều embedding của token đó, không phải trị tuyệt đối hay chuẩn vector. Cách tính dùng quy tắc trung điểm Riemann với 1024 bước. Embedding của token cấu trúc khuôn chat giữ nguyên; mỗi vị trí nội dung người dùng dùng embedding của token dấu cách thông thường làm tham chiếu, đồng thời giữ chiều dài chuỗi, attention mask và vị trí. Đây là tham chiếu embedding nhân tạo, không phải lời nhắc rỗng tự nhiên; các điểm trung gian trên đường thẳng cũng không nhất thiết biểu diễn văn bản hợp lệ. Theo Sundararajan và cộng sự (2017), IG và tính đầy đủ gắn với hàm đích và điểm tham chiếu đã chọn. Vì thế giá trị IG ở đây mô tả đóng góp dọc đường từ $e'$ đến đầu vào clean, không trực tiếp đo hiệu ứng đổi cue sang nhãn khác.

Phép kiểm tra số học so sánh $sum_i "IG"_i$ với $F(e)-F(e')$. Phần dư được lưu theo chiều $sum_i "IG"_i - (F(e)-F(e'))$; với ba trường hợp lần lượt là $-0.000072$, $0.000189$ và $0.002356$ (hiệu chuẩn, số học, logic). Chúng nhỏ so với chênh lệch đích tương ứng và cho thấy tích phân số hội tụ hợp lý ở các trường hợp này. Không có ngưỡng đạt/trượt tùy ý, và phần dư nhỏ không kiểm định tính trung thực của lời giải thích. Handoff ở Issue #1 ghi nhận tham chiếu zero-embedding ban đầu không ổn định về tính đầy đủ; trước khi xem kết quả attribution của lựa chọn thay thế, nghiên cứu đã định trước tham chiếu embedding dấu cách, kiểm tra hội tụ rồi đóng băng nó. Do vậy baseline là một phần của câu hỏi attribution, không phải tham số có thể đổi theo từng ví dụ để được biểu đồ đẹp hơn.

== Thay thế kích hoạt

Tại mỗi tầng decoder $ell$, thí nghiệm lấy toàn bộ vector đầu ra residual stream ở vị trí token cue từ lượt clean, thay đúng vector đó vào lượt contrast, rồi tính lại $F$. Hiệu ứng là

$
  Delta F_(ell,k)^"patch" = F(x^"contrast"; "do"(h_(ell,k) = h_(ell,k)^"clean")) - F(x^"contrast"),
$

với $k$ là vị trí cue đã căn chỉnh. Dấu dương nghĩa là can thiệp clean-to-contrast làm điểm nghiêng về nhãn đúng so với lượt contrast chưa patch. Theo Heimersheim và Nanda (2024), diễn giải activation patching phụ thuộc cách chọn lượt nguồn, lượt nhận, vị trí và metric. Kết quả ở đây là hiệu ứng nhân quả của *can thiệp đã nêu* trong cặp đầu vào này; nó không chứng minh vector ấy là cần thiết, không tách được một mạch hoàn chỉnh, và hiệu ứng yếu ở tầng muộn không chứng minh cue đã hết ảnh hưởng vì thông tin có thể đã lan sang vị trí khác.

= Kết quả: cùng một trường hợp, bốn phạm vi bằng chứng

@comparison đặt cùng bốn quan sát của trường hợp số học. Lượt clean dùng `Cue: B`, nhưng điểm $F(x^"clean")=-0.043$ hơi ưu tiên A, nhãn sai so với phép tính $7+5=12$. Lời tự giải thích được ghi nguyên từ lượt hỏi riêng lại nói "The correct answer is B) 12" và "Cue: B is correct". Mâu thuẫn trực tiếp giữa nhãn *đã đo/chọn* A và lời giải thích B là kết quả của hồ sơ đóng băng; không nên "sửa" câu chữ của mô hình hay suy diễn rằng lời này mô tả nguyên nhân của lựa chọn A.

Đổi cue từ B sang A cho $F(x^"contrast")=-4.478$ và $Delta F_"input"=-4.435$: nhãn sai A vẫn được ưu tiên, nhưng mạnh hơn. Cue trên đầu vào clean có IG dương $0.839$, đồng thời các token khác cũng có đóng góp dương hoặc âm đáng kể; không được đọc cue như nguyên nhân duy nhất. Patch ở các tầng đầu tăng $F$ của lượt contrast khoảng $4.4$, gần đảo ngược hiệu ứng đầu vào đã đo; hiệu ứng giảm về gần không ở các tầng cuối. Cả hai can thiệp chỉ nói về đúng token cue và hướng thay đổi đã đóng băng. Sự tương ứng về dấu giữa IG cue, đổi đầu vào và patch là bằng chứng hội tụ về liên quan của cue đối với $F$, trong khi lời tự giải thích không khớp lựa chọn đã đo. Không dạng nào đơn lẻ xác định được toàn bộ thuật toán mà mô hình dùng.

@ig-all giữ toàn bộ attribution token có dấu của ba trường hợp, thay vì chỉ lấy giá trị cue. @patch-all giữ toàn bộ sweep theo tầng. Chúng cho phép kiểm tra phần nào của trường hợp số học khác với trường hợp logic và xem những hiệu ứng yếu, âm hoặc gần không thay vì chỉ giữ đỉnh đường cong.

#page(flipped: true)[
  #figure(
    image("figures/arithmetic-case-comparison.svg", width: 100%),
    caption: [Đối chiếu trường hợp số học từ `v1.0.0/frozen.json`: hai lượt của mô hình gốc cho logits, lựa chọn đo được và điểm $F$ suy ra; các lượt giải thích/can thiệp dùng thông tin khác nhau và cho các dạng bằng chứng khác nhau. IG có dấu trên đầu vào clean theo tham chiếu embedding dấu cách; patch thay vector cue clean vào lượt contrast tại từng tầng. Các kết quả không hợp thành điểm trung thực.],
  ) <comparison>
]

#figure(
  image("figures/integrated-gradients-token-attribution.svg", width: 100%),
  caption: [IG có dấu theo token của ba trường hợp. Vạch xanh đánh dấu vị trí cue đã cố định; giá trị dựa trên đường embedding từ tham chiếu dấu cách đến đầu vào clean. Nguồn: phân tích tất định từ `v1.0.0/frozen.json`.],
) <ig-all>

#figure(
  image("figures/activation-patching-layer-effects.svg", width: 90%),
  caption: [Hiệu ứng clean-to-contrast khi thay vector residual stream tại cue ở từng tầng decoder, đo bằng cùng $F$. Đường cong chỉ mô tả can thiệp này; nguồn: phân tích tất định từ `v1.0.0/frozen.json`.],
) <patch-all>

= So sánh và giới hạn suy luận

Ở trường hợp logic, lượt clean chọn đúng A với $F=2.826$, còn cue B ở lượt contrast đảo dấu ưu thế thành $F=-1.412$, cho $Delta F_"input"=-4.237$. Lời tự giải thích nêu suy luận "mọi mèo đều là động vật có vú" mà không nhắc cue. IG của cue là $0.096$, dương nhưng không nổi trội trên bản đồ token; patch các tầng đầu vẫn làm điểm tăng rõ, rồi yếu đi ở cuối sweep. Đây là khác biệt giữa độ nhạy dọc đường embedding, hiệu ứng đổi đầu vào hữu hạn và hiệu ứng thay kích hoạt nội bộ. Việc lời giải thích bỏ qua cue không tự nó chứng minh lời giải thích thiếu trung thực: câu nói có thể chọn mô tả phần nội dung suy luận, còn thí nghiệm đo một đại lượng và một cue hẹp hơn.

Ở trường hợp hiệu chuẩn, lượt clean chọn đúng A với $F=12.459$; đổi cue đưa $F$ xuống $1.074$ ($Delta F_"input"=-11.385$) nhưng không đổi nhãn A/B được chọn. IG cue dương $0.651$ và patch sớm đưa điểm contrast về phía clean. Lời tự giải thích chỉ nêu Paris là thủ đô Pháp. Trường hợp này cho thấy quy trình phát hiện được hiệu ứng cue mà không cần đảo nhãn; nó là kiểm tra tham chiếu, không phải bằng chứng về tỷ lệ tổng quát hóa trong các bài toán kiến thức.

Các phát hiện đều ở mức ba trường hợp đã chọn trước, một mô hình, một checkpoint, một điểm logit A/B và một cặp cue mỗi trường hợp. Phạm vi này không cho phép ước lượng độ chính xác trên quần thể, đánh giá độ trung thực bằng điểm số, hoặc kết luận mô hình "thực sự suy nghĩ" theo văn bản tự giải thích. Tính hợp lý bề ngoài không bảo đảm tính trung thực; attribution không đồng nhất với cơ chế nhân quả; độ nhạy vi phân dọc đường IG không đồng nhất với hiệu ứng đổi đầu vào hữu hạn; patch dương chỉ chứng minh tác động của phép thay thế cụ thể. Đồng thuận giữa các dạng bằng chứng giúp định vị câu hỏi tiếp theo nhưng không là chứng minh toàn bộ cơ chế; bất đồng cũng không tự động làm một phương pháp thất bại.

= Nguồn và khả năng tái lập

- Schneider, J. (2024). _Explainable Generative AI (GenXAI): A Survey, Conceptualization, and Research Agenda._ Bản nguồn LaTeX cục bộ `references/sn-article.tex`, arXiv:2404.09554. Khung khái niệm, taxonomy và desiderata.
- Sundararajan, M., Taly, A., & Yan, Q. (2017). #link("https://proceedings.mlr.press/v70/sundararajan17a.html")[_Axiomatic Attribution for Deep Networks._] ICML 34. Định nghĩa và tính đầy đủ của IG.
- Turpin, M., Michael, J., Perez, E., & Bowman, S. R. (2023). #link("https://proceedings.neurips.cc/paper_files/paper/2023/hash/ed3fea9033a80fea1376299fa7863f4a-Abstract.html")[_Language Models Don't Always Say What They Think._] NeurIPS 36. Bằng chứng thực nghiệm về giới hạn của lời giải thích chain-of-thought; Schneider dẫn công trình này là năm 2024.
- Heimersheim, S., & Nanda, N. (2024). #link("https://arxiv.org/abs/2404.15255")[_How to use and interpret activation patching._] Hướng can thiệp và giới hạn diễn giải patching.
- Nguồn kết quả: #link("https://github.com/itskyf/MTH110-2026-XAI-Demos/releases/tag/v1.0.0")[`v1.0.0/frozen.json`], giao thức `docs/research/protocol.md`, và mã phân tích `src/mth110/analysis.py`. Chạy `bash scripts/fetch_frozen.sh` rồi `pixi run --locked python -m mth110.analysis` để kiểm tra số và sinh lại hình. Handoff về baseline được ghi tại #link("https://github.com/itskyf/MTH110-2026-XAI-Demos/issues/1#issuecomment-5819709379")[Issue #1].
