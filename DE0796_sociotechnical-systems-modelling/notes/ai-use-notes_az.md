# DE0796: süni intellekt (AI) haqqında qeydlər harada və necə yazılıb

Vəziyyət: 26 noyabr 2026. T4L və T5L hələ qaralamadır; son fayllar yığılanda bu siyahı
yenilənəcək (qeydin yeri və mətni dəyişmir, yalnız səhifə nömrəsi dəyişə bilər).

## 1. Müəllimə göndərilən fayllarda

Hər işdə **bir** qeyd var, həmişə sonda, istinad siyahısının altında, kursivlə.

| İş | Fayl | Yeri | Mətn |
|---|---|---|---|
| PR1 xülasə | `VagifAsgarli-PR1.pdf` | 2-ci səhifə, References-in altında | Note. Generative AI tools were used for information retrieval, drafting of the text and formatting the reference list: Claude (Anthropic). |
| PR1 təqdimat | `VagifAsgarli-PR1-presentation.pptx` | son slayd (12, "References (2/2)") | Note. Generative AI tools were used for information retrieval, drafting of the text and the slides, and formatting the reference list: Claude (Anthropic). |
| T4LPrim təqdimat | `VagifAsgarli-T4LPrim.pptx` | son slayd (10, "References (2/2)") | Note. Generative AI tools were used for information retrieval, for drawing the diagram, for drafting the text and for formatting the reference list: Claude (Anthropic). |
| T4L protokol | `VagifAsgarli-T4L.pdf` (hələ qaralama) | References-in altında, imza sətrindən əvvəl | Note. Generative AI tools were used for information retrieval, for designing and checking the model, for drafting the text and for formatting the reference list: Claude (Anthropic). |
| T4L təqdimat | `VagifAsgarli-T4L-presentation.pptx` (hələ qaralama) | son slayd (12, "References") | Note. Generative AI tools were used for information retrieval, for designing and checking the model, for drafting the text and the slides and for formatting the reference list: Claude (Anthropic). |
| T5L protokol | `vagif.asgarli-T5L.pdf` (hələ qaralama) | "4. References" bölməsinin sonunda | Note. Generative AI tools were used for information retrieval, for designing and checking the models, for drafting the text and for formatting the reference list: Claude (Anthropic). |
| T5L təqdimat | `vagif.asgarli-T5L-presentation.pptx` (hələ qaralama) | son slayd (13, "References") | Note. Generative AI tools were used for information retrieval, for designing and checking the models, for drafting the text and the slides and for formatting the reference list: Claude (Anthropic). |

Başqa heç bir yerdə (başlıq, mətn, şəkil altı, slayd qeydləri) AI haqqında söz yoxdur.

## 2. Müəllimin öz mətni ilə fərq

Müəllim bu qeydi yalnız **PR1 tapşırığında** tələb edir. Onun şablonundakı cümlə:

> Note. Generative AI tools were used for information retrieval and formatting the reference
> list: __________ (indicate the tools used, if applicable).

Mən iki şey etmişəm:

1. Boş yerə alətin adını yazmışam: `Claude (Anthropic)`.
2. Cümləyə `drafting of the text` sözlərini əlavə etmişəm, çünki mətnin hazırlanmasında da AI
   iştirak edib. Müəllimin cümləsi olduğu kimi qalsaydı, qeyd natamam olardı.

T4LPrim, T4L və T5L şablonlarında AI qeydi üçün sətir **yoxdur**. Oraya qeydi mən əlavə
etmişəm, PR1-dəki qaydaya uyğun, eyni formada.

## 3. Müəllimə göndərilməyən fayllarda (repoda, sənin üçün)

| Fayl | Nə yazılıb |
|---|---|
| `README.md` (kurs qovluğu) və hər işin `README.md` faylı | müəllim gecikmiş işləri 2 dekabra qədər qəbul edir və tam AI dəstəyi ilə hazırlanmasına icazə verib (sənin dediyin kimi yazılıb) |
| `notes/setup-for-vagif_az.md`, 5-ci bölmə | hər işin sonunda AI qeydi var, onu silmə |
| `notes/requirements-check_az.md`, açıq sual 2 | PR1 qeydinə `drafting of the text` əlavə olunmasının izahı |
| `pr1_summary-design/notes/explanation_az.md`, sual 14 | "AI-dan necə istifadə etmisən?" sualına cavab nümunəsi |
| `t4lprim_.../notes/defence-prep_az.md`, sual 11 | "Diaqramı nə ilə çəkmisən?" sualına cavab |
| `t4l_.../notes/defence-prep_az.md`, sual 14 | "Modeli nə ilə hazırlamısan?" sualına cavab |
| `t5l_.../notes/defence-prep_az.md` | "Süni intellektdən istifadə etmisən?" sualına cavab |

## 4. Fayl xüsusiyyətləri (sənəddə görünmür, File > Properties-də görünür)

Bunlar AI qeydi deyil, amma bilməyin yaxşıdır:

| Fayl | Müəllif (creator) | Son dəyişən | Qeyd |
|---|---|---|---|
| `VagifAsgarli-PR1.docx` / `.pdf` | Vagif Asgarli | Vagif Asgarli | əvvəl burada alətin adı ("python-docx") yazılmışdı, bu gün sənin adınla düzəldildi |
| təqdimatlar (`.pptx`) | Egils | Vagif Asgarli | müəllimin şablonundan yığıldığı üçün müəllif kimi şablonun sahibi qalır |
| protokollar (`.docx`) | Lietotajs | Vagif Asgarli | eyni səbəb: müəllimin şablonu |
| PDF-lər | | | "Producer: LibreOffice" (PDF-ə çevirən proqram) |
| `Yellowstone.stmx` | | | başlığında `RTU DE0796 T4L, Vagif Asgarli` və `yellowstone_model.py (XMILE 1.0 for STELLA)` yazılıb; STELLA-da açıb saxlayanda bu başlığı STELLA özü yenidən yazır |

## 5. Mənim mövqeyim

Müəllim PR1-də AI qeydini özü tələb edir və sənə AI ilə işləməyə icazə verib. Ona görə qeydlər
sənin əleyhinə deyil, əksinə, qaydaya uyğunluğu göstərir. Qeydin **mətnini** dəyişmək istəsən
(məsələn, daha qısa və ya müəllimin cümləsinə daha yaxın), de, birlikdə elə yazaq ki, yenə də
doğru olsun. Qiymətləndirilən işdən AI qeydini tam silmək və ya AI-dan istifadəni gizlətmək
isə mənim edəcəyim iş deyil.
