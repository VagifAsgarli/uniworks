# DE0796: nə hazırdır və səndən nə lazımdır (son tarix: 2 dekabr 2026)

Müəllim dörd işi istəyir: **PR1**, **T4LPrim**, **T4L**, **T5L**. Hamısı
`egils.ginters@rtu.lv` ünvanına göndərilir və sonra müdafiə olunur.

## Qısa vəziyyət (26 noyabr)

| İş | Vəziyyət | Səndən nə lazımdır |
|---|---|---|
| PR1 (xülasə + təqdimat) | **hazırdır** | oxu, göndər |
| T4LPrim (Yellowstone CLD təqdimatı) | **hazırdır** | oxu, göndər |
| T4L (STELLA modeli, protokol, təqdimat) | model, təlimat və qaralamalar hazırdır | STELLA-da modeli aç/qur, 9 ekran şəkli çək, mənə göndər |
| T5L (BPMN2 modeli, protokol, təqdimat) | dizayn, təlimat və qaralamalar hazırdır | diaqram ARIS Express-də olmalıdır (`.adf` + `.pdf`), mənə göndər |

T4L və T5L-də son fayllar sənin şəkillərindən və ARIS faylından sonra yığılır. Buna görə
**bu iki işi 30 noyabra qədər** et ki, son variantı yığmağa vaxt qalsın.

---

## 1. PR1: hazırdır

| Fayl | Yeri |
|---|---|
| Xülasə (göndərilən) | `pr1_summary-design/outputs/submission/VagifAsgarli-PR1.pdf` |
| Təqdimat (12 slayd) | `pr1_summary-design/outputs/submission/VagifAsgarli-PR1-presentation.pptx` |
| İzah, danışıq planı, suallar | `pr1_summary-design/notes/explanation_az.md` |

Sənin işin: izahı oxu. Xülasənin tarixi 30 noyabr 2026 yazılıb; başqa tarix istəsən, mənə de.

## 2. T4LPrim: hazırdır

| Fayl | Yeri |
|---|---|
| Təqdimat (göndərilən, 10 slayd) | `t4lprim_causal-loop-diagram-yellowstone/outputs/submission/VagifAsgarli-T4LPrim.pptx` |
| İzah, danışıq planı, suallar | `t4lprim_causal-loop-diagram-yellowstone/notes/defence-prep_az.md` |

## 3. T4L: STELLA

Müəllimin slaydlarındakı STELLA köhnə versiyadır (9, fayl `.STM`). İki yol var:

- **STELLA 9.0.4 quraşdırıcısı səndə və ya qrup yoldaşlarında varsa**: onu quraşdır. Modeli
  təlimatla əl ilə qurursan (1,5–2 saat). Fayl `.STM` olur, müəllimin istədiyi kimi.
- **Yoxdursa**: `https://www.iseesystems.com/store/products/stella-architect.aspx` səhifəsindən
  Stella Architect-in 30 günlük sınaq versiyasını quraşdır. Hazır faylı açırsan (30–40 dəqiqə).
  Fayl `.stmx` olur.

Addımlar:

1. Təlimatı aç: `t4l_system-dynamics-stella/notes/stella-guide_az.md`.
2. Modeli qur (A yolu) və ya aç (B yolu).
3. Cədvəldəki rəqəmləri təlimatın C bölməsi ilə tutuşdur.
4. Altı təcrübəni işlət və 9 ekran şəklini çək (adları təlimatın D bölməsində).
5. Modeli saxla (`VagifAsgarli-T4L.STM` və ya `.stmx`).
6. Şəkilləri və model faylını mənə göndər. Mən protokolu və təqdimatı son variantda yığıram.
7. İzahı oxu: `t4l_system-dynamics-stella/notes/defence-prep_az.md`. Müdafiədə modeli öz
   kompüterində STELLA-da işlədəcəksən.

Qaralamalara indi baxa bilərsən: `t4l_system-dynamics-stella/outputs/draft/`. Onlarda STELLA
şəkillərinin yerində mənim yoxlama hesabımdan gözlənilən qrafiklər var və üstündə "DRAFT"
yazılıb. **Qaralamanı müəllimə göndərmə.**

## 4. T5L: ARIS Express

Müəllim BPMN2 diaqramının ARIS Express-də çəkilməsini və `.adf` + `.pdf` kimi saxlanmasını
istəyir. `.adf` formatı bağlıdır, onu yalnız ARIS Express özü yaradır.

1. Öz kompüterində ARIS Express-i quraşdır (`https://ariscommunity.com/aris-express/download`,
   Windows variantı). Müdafiədə faylı açıb göstərmək üçün lazımdır.
2. Göndərdiyin `express.jnlp` faylı ilə mən proqramı burada işə salıb diaqramı çəkməyə
   çalışıram. Nəticəni ayrıca yazacam:
   - **Alınsa**: sənə hazır `vagif.asgarli-T5L-model.adf` və `.pdf` verirəm; sən faylı ARIS-də
     açıb düzgün göründüyünü yoxlayırsan.
   - **Alınmasa**: diaqramı təlimatla özün çəkirsən (təxminən 2 saat):
     `t5l_conceptual-modelling-bpmn2/notes/aris-express-build-guide_az.md`. Nümunə şəkil:
     `t5l_conceptual-modelling-bpmn2/outputs/figures/fig2_cyberflow_bpmn2_reference.png`.
     Sonra `.adf` və `.pdf` fayllarını mənə göndərirsən.
3. İzahı oxu: `t5l_conceptual-modelling-bpmn2/notes/defence-prep_az.md`.

Qaralamalar: `t5l_conceptual-modelling-bpmn2/outputs/draft/`. Onlardakı BPMN2 şəkli ARIS-dən
deyil, mənim nümunə çəkilişimdir və "DRAFT" yazılıb. **Qaralamanı müəllimə göndərmə.**

---

## 5. Göndərməzdən əvvəl

1. **Protokolları imzala.** T4L və T5L protokollarının sonunda "Signature" sətri var: çap et,
   imzala, skan edib PDF kimi göndər (və ya PDF-ə imzanın şəklini qoy).
2. **Fayl adları** (müəllimin qaydası ilə):

   | İş | Fayllar |
   |---|---|
   | PR1 | `VagifAsgarli-PR1.pdf`, `VagifAsgarli-PR1-presentation.pptx` |
   | T4LPrim | `VagifAsgarli-T4LPrim.pptx` |
   | T4L | `VagifAsgarli-T4L.pdf`, `VagifAsgarli-T4L.STM` (və ya `.stmx`), `VagifAsgarli-T4L.pptx` |
   | T5L | `vagif.asgarli-T5L.pdf`, `vagif.asgarli-T5L-model.adf`, `vagif.asgarli-T5L-model.pdf`, `vagif.asgarli-T5L-presentation.pptx` |

3. **Süni intellekt qeydi.** Hər işin sonunda "Note. Generative AI tools were used..." sətri
   var. Müəllim PR1-də bu qeydi özü tələb edir və sənə AI ilə işləməyə icazə verib; qeyd
   həqiqəti yazır, onu silmə.
4. **Məktub mətni (nümunə, özün göndər):**

   > Subject: DE0796 – overdue works PR1, T4LPrim, T4L, T5L – Vagif Asgarli (251ADM047)
   >
   > Dear Professor Ginters,
   >
   > As agreed, please find attached my works for Sociotechnical Systems Modelling: PR1 (summary
   > and presentation), T4LPrim (presentation), T4L (protocol, model and presentation) and T5L
   > (protocol, model in ADF and PDF, and presentation).
   >
   > I am ready to defend them at any time convenient for you.
   >
   > Kind regards,
   > Vagif Asgarli, 251ADM047

   Stella Architect ilə işləmisənsə, bu cümləni əlavə et: "The T4L model was built in Stella
   Architect, the current version of STELLA, which saves in STMX format."

## 6. Mənə yazmalı olduqların

- STELLA 9.0.4 quraşdırıcısı səndə və ya yoldaşlarında varmı? (Yoxdursa, Stella Architect ilə
  gedirik.)
- Kompüterin Windows-dur, yoxsa Mac?
- T4L şəkilləri və model faylı; T5L üçün (lazım olsa) `.adf` və `.pdf`.
