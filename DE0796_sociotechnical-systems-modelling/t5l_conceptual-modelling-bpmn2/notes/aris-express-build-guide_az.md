# T5L: BPMN2 diaqramını ArisExpress-də çəkmək üçün təlimat

Müəllimin qaydası: BPMN2 modeli **ArisExpress** mühitində hazırlanmalı, **adf** və **pdf**
formatında saxlanmalıdır. Protokoldakı şəkil də ArisExpress-dən olmalıdır. `.adf` faylını yalnız
proqramın özü yarada bilir, ona görə diaqramı ArisExpress-də çəkmək lazımdır. Model artıq
hazırdır və yoxlanılıb: sən onu aşağıdakı şəkilə və cədvəllərə baxaraq eynilə köçürürsən.
Təxmini vaxt: 1,5–2 saat.

Hazır nümunə şəkil (buna baxaraq çək):

- bütöv diaqram: [`outputs/figures/fig2_cyberflow_bpmn2_reference.png`](../outputs/figures/fig2_cyberflow_bpmn2_reference.png)
  (eyni şəklin `.svg` variantı böyüdəndə daha aydın görünür)
- böyüdülmüş hissələr: `fig2_reference_detail1_detection.png`, `fig2_reference_detail2_handling.png`,
  `fig2_reference_detail3_reporting.png` (eyni qovluqda)
- modelin özü BPMN 2.0 faylı kimi: [`tools/cyberflow_incident-handling.bpmn`](../tools/cyberflow_incident-handling.bpmn).
  Bu fayl ArisExpress üçün deyil, yalnız nümunədir.

> **Vacib qeyd: nə yoxlanılıb, nə yox.** ARIS Express 2.4j (sənin göndərdiyin `express.jnlp`)
> burada işə salındı, amma ilk açılışda **Activation Wizard** ARIS Community istifadəçi adını və
> parolunu tələb edir. Sənin hesabın məndə yoxdur və olmamalıdır, ona görə proqramın içinə
> girib diaqramı özüm çəkə bilmədim: **diaqramı sən çəkirsən**. Aşağıdakı adlar isə artıq
> təxmin deyil: simvol adlarını, menyu və pəncərə adlarını proqramın öz fayllarından və
> daxili köməyindən (Help) götürmüşəm. Yoxlaya bilmədiyim tək şey budur: hər düymə pəncərənin
> harasında durur və simvol panelində hansı simvollar ilk baxışda görünür. Tapmasan, 8-ci
> bölməyə bax. Müəllimin nümunə faylı (`materials/t5l_lecturer-demo_restaurant-visit.adf`)
> ArisExpress-də açılır: orada Pool, Task, Gateway, Message, Data object və Data store
> simvollarının necə göründüyünü görə bilərsən.

### İlk açılış (bir dəfə)

Proqram ilk dəfə açılanda **Activation Wizard** dörd addım göstərir:

1. **Welcome to ARIS Express**: `Next`.
2. **License agreement**: «I have read and accept the license agreement» işarəsini qoy, `Next`.
3. **Enter login data**: `User` və `Password` xanalarına ARIS Community hesabının (qeydiyyatdan
   keçdiyin `ariscommunity.com`) adını və parolunu yaz. İnternet lazımdır: məlumat HTTPS ilə
   ARIS Community-də yoxlanılır. Hesabın yoxdursa, eyni pəncərədə `Register now.` keçidi var.
4. **Select language**: `English` seç (bu təlimatdakı adlar ingiliscədir).

## 1. Diaqramda nə olmalıdır (müəllimin məcburi elementləri)

| Müəllimin tələbi | Bizim modeldə | Diaqramda yeri |
|---|---|---|
| Ən azı 2 Pool, biri bir neçə Swimlane ilə | 2 Pool: «Organisation (essential entity)» 4 Swimlane ilə, «CSIRT (CERT.LV)» | yuxarıda böyük Pool, aşağıda kiçik Pool |
| Ən azı 4 müxtəlif Event / Intermediate event | 5 növ, cəmi 11 hadisə: Start event (1), Message start event (1), Timer intermediate event (3), Message intermediate event (3), End event (3) | S1; CS1; TE1, TE2, TE3; ME1, CS2, CS3; E1, E2, CE |
| Bütün Gateway-lər: OR, AND, XOR | XOR: 1 (G1); AND: 2 (G2 ayırır, G3 birləşdirir); OR: 2 (G4 ayırır, G5 birləşdirir) | G1 Cybersecurity manager zolağında; G2, G3 SOC analyst zolağında; G4, G5 IT operations zolağında |
| Message və Data xətləri | 4 Message flow (M1–M4), 8 Data xətti (D1–D8) | iki Pool arasında qırıq xətlər; tapşırıqlarla sənədlər arasında nöqtəli xətlər |
| Bir neçə Data object | 4 Data object (DO1–DO4) və 1 Data store (iki dəfə çəkilib: DS1a, DS1b) | SOC analyst və Cybersecurity manager zolaqlarında |

Cəmi: 19 Task, 11 Event, 5 Gateway, 37 Sequence flow, 4 Message flow, 8 Data xətti.

## 2. Simvollar (ArisExpress, model tipi «BPMN diagram»)

| Cədvəldəki tip | Görünüşü | ArisExpress-də adı (proqramın fayllarından yoxlanıb) |
|---|---|---|
| Pool | böyük düzbucaqlı, solda şaquli ad | Pool |
| Swimlane | Pool-un içində üfüqi zolaq | Lane |
| Task | küncləri yumru düzbucaqlı | Task |
| Start event | nazik kənarlı dairə | Start event |
| Start event (Message) | nazik kənarlı dairə, içində zərf | Message start event |
| Intermediate event (Timer) | ikiqat kənarlı dairə, içində saat | Timer intermediate event |
| Intermediate event (Message, catch) | ikiqat kənarlı dairə, içində ağ zərf | Message intermediate event (catch) |
| End event | qalın kənarlı dairə | End event |
| Gateway XOR | romb, içində X | Exclusive gateway |
| Gateway AND | romb, içində + | Parallel gateway |
| Gateway OR | romb, içində dairə | Inclusive gateway |
| Data object | bir küncü qatlanmış vərəq | Data object |
| Data store | silindr | Data store |
| Sequence flow | bütöv xətt, ucu dolu ox | eyni Pool-un içində birləşdirəndə proqram özü seçir |
| Message flow | qırıq xətt, başında kiçik dairə, ucunda boş ox | iki Pool arasında birləşdirəndə proqram özü seçir |
| Data xətti (data association) | nöqtəli xətt, ucunda açıq ox | Task ilə Data object arasında birləşdirəndə proqram özü seçir |

Bu simvolların hamısı «BPMN diagram» model tipində icazə verilən simvollar siyahısında var:
növlü hadisələr ayrıca simvoldur (`Message start event`, `Timer intermediate event`,
`Message intermediate event (catch)`), üç Gateway də ayrıca simvoldur (`Exclusive gateway`,
`Parallel gateway`, `Inclusive gateway`). Simvol panelində (**Symbols** bar) hamısı ilk
baxışda görünməyə bilər. Obyektin yanında çıxan kiçik alətlər zolağına (mini toolbar) simvol
əlavə etmək üçün **Add symbols** pəncərəsi var: «Available symbols» siyahısında lazım olanı
iki dəfə bas və ya seçib `Add` bas. Heç cür tapmasan, adi `Intermediate event` qoy və adını
cədvəldəki kimi yaz: ad «Time limit: ...» olduğu üçün mənası aydındır, amma düzgün simvol
daha yaxşıdır.

## 3. Çəkmə ardıcıllığı

1. **Yeni model.** ArisExpress-i aç. **Home** səhifəsində «Model types» altında
   **BPMN diagram** seç (və ya əsas menyuda `New...`, açılan **New model** pəncərəsində
   «BPMN diagram»).
2. **Pool və Swimlane-lər.** Əvvəl böyük Pool qoy, adını yaz: `Organisation (essential entity)`.
   İçinə dörd Lane qoy, yuxarıdan aşağı bu ardıcıllıqla: `Employee`, `IT operations`,
   `SOC analyst`, `Cybersecurity manager (CISO)`. Zolaq əlavə etmək üçün proqramda **Add new
   lanes** pəncərəsi var: «Number of lanes» xanasında say, sonra «Add lanes below» (aşağıya)
   və ya «Add lanes above» (yuxarıya). Altına ikinci Pool qoy:
   `CSIRT (CERT.LV)` (zolaqsız). İki Pool arasında bir az boş yer saxla: Message flow-ların
   adları ora yazılır. IT operations zolağını digərlərindən hündür et (üç Task alt-alta durur).
3. **Elementlər.** 4-cü bölmədəki cədvəllə soldan sağa get, hər elementi öz zolağına qoy və
   adını cədvəldəki kimi yaz (ingiliscə, hərf-hərf). Yerləşməni nümunə şəkildən götür.
   Rahat yol: əvvəl bütün Task-ları, sonra Event-ləri, sonra Gateway-ləri qoy.
4. **Sequence flow-lar.** 5-ci bölmədəki cədvəllə F01-dən F37-yə qədər birləşdir. Hər birini
   çəkəndən sonra cədvəldə qeyd et ki, heç biri unudulmasın. G1-dən çıxan iki xəttin adını yaz:
   `Yes` və `No`.
5. **Message flow-lar.** M1–M4: yuxarı Pool-dakı Task-dan aşağı Pool-dakı Event-ə (M2 əksinə:
   aşağıdan yuxarı). Xəttin adını yaz (`Early warning`, `Feedback and guidance`,
   `Incident notification`, `Final report`). Müəllimin nümunəsindəki kimi xəttin üstünə zərf
   simvolu (Message) da qoya bilərsən, məcburi deyil.
6. **Data object-lər və Data xətləri.** DO1–DO4 və Data store-u (iki yerdə: T6-nın və T15-in
   altında, eyni adla `Procedure models`) qoy, sonra D1–D8 xətlərini çək. İstiqamətə diqqət et:
   Task → Data object «yaradır/yazır», Data object → Task «oxuyur».
7. **Səliqə.** Xətlər bir-birini kəsməməlidir (nümunədə heç bir kəsişmə yoxdur). Elementləri
   düzləndir, yazılar oxunaqlı olsun.
8. **Yoxlama.** 6-cı bölmədəki siyahı ilə yoxla.
9. **Saxlama.** 7-ci bölməyə bax.

## 4. Bütün elementlər

Tip adları ingiliscədir (2-ci bölmədəki cədvələ bax). Sıra: soldan sağa.

| ID | Type | Name | Pool / Swimlane |
|---|---|---|---|
| S1 | Start event | Suspicious activity noticed | Organisation (essential entity) / Employee |
| T1 | Task | Report the suspicious event | Organisation (essential entity) / Employee |
| T2 | Task | Register and classify the event | Organisation (essential entity) / SOC analyst |
| T4 | Task | Assess the significance | Organisation (essential entity) / Cybersecurity manager (CISO) |
| T5 | Task | Handle as a routine event | Organisation (essential entity) / SOC analyst |
| G1 | Gateway XOR (exclusive) | Significant incident? | Organisation (essential entity) / Cybersecurity manager (CISO) |
| E1 | End event | Routine event closed | Organisation (essential entity) / SOC analyst |
| T6 | Task | Activate the incident procedure | Organisation (essential entity) / Cybersecurity manager (CISO) |
| G2 | Gateway AND (parallel) | (no name) | Organisation (essential entity) / SOC analyst |
| G4 | Gateway OR (inclusive) | Which measures are needed? | Organisation (essential entity) / IT operations |
| TE1 | Intermediate event (Timer) | Time limit: 24 h after becoming aware | Organisation (essential entity) / Cybersecurity manager (CISO) |
| T7 | Task | Isolate the affected systems | Organisation (essential entity) / IT operations |
| T8 | Task | Block accounts and addresses | Organisation (essential entity) / IT operations |
| T9 | Task | Switch to backup systems | Organisation (essential entity) / IT operations |
| T10 | Task | Collect and preserve evidence | Organisation (essential entity) / SOC analyst |
| T11 | Task | Send the early warning | Organisation (essential entity) / Cybersecurity manager (CISO) |
| ME1 | Intermediate event (Message, catch) | Feedback and guidance received | Organisation (essential entity) / Cybersecurity manager (CISO) |
| G5 | Gateway OR (inclusive) | (no name) | Organisation (essential entity) / IT operations |
| G3 | Gateway AND (parallel) | (no name) | Organisation (essential entity) / SOC analyst |
| T12 | Task | Prepare the initial assessment | Organisation (essential entity) / SOC analyst |
| TE2 | Intermediate event (Timer) | Time limit: 72 h after becoming aware | Organisation (essential entity) / Cybersecurity manager (CISO) |
| T14 | Task | Remove the cause, restore services | Organisation (essential entity) / IT operations |
| T13 | Task | Send the incident notification | Organisation (essential entity) / Cybersecurity manager (CISO) |
| T15 | Task | Review and update the procedure model | Organisation (essential entity) / Cybersecurity manager (CISO) |
| TE3 | Intermediate event (Timer) | Time limit: one month after the notification | Organisation (essential entity) / Cybersecurity manager (CISO) |
| T16 | Task | Prepare and send the final report | Organisation (essential entity) / Cybersecurity manager (CISO) |
| E2 | End event | Incident closed | Organisation (essential entity) / Cybersecurity manager (CISO) |
| CS1 | Start event (Message) | Early warning received | CSIRT (CERT.LV) |
| C1 | Task | Register and assess the early warning | CSIRT (CERT.LV) |
| C2 | Task | Send feedback and guidance | CSIRT (CERT.LV) |
| CS2 | Intermediate event (Message, catch) | Incident notification received | CSIRT (CERT.LV) |
| C3 | Task | Assess the incident notification | CSIRT (CERT.LV) |
| CS3 | Intermediate event (Message, catch) | Final report received | CSIRT (CERT.LV) |
| C4 | Task | Evaluate the final report, close the case | CSIRT (CERT.LV) |
| CE | End event | Case closed | CSIRT (CERT.LV) |
| DO1 | Data object | Incident ticket | Organisation (essential entity) / SOC analyst |
| DS1a | Data store | Procedure models | Organisation (essential entity) / Cybersecurity manager (CISO) |
| DO2 | Data object | Evidence package | Organisation (essential entity) / SOC analyst |
| DO3 | Data object | Initial assessment | Organisation (essential entity) / SOC analyst |
| DS1b | Data store | Procedure models | Organisation (essential entity) / Cybersecurity manager (CISO) |
| DO4 | Data object | Final report | Organisation (essential entity) / Cybersecurity manager (CISO) |

## 5. Bütün birləşmələr

`From` sütunundakı elementdən `To` sütunundakı elementə xətt çək.

| ID | From | To | Type | Label |
|---|---|---|---|---|
| F01 | S1 Suspicious activity noticed | T1 Report the suspicious event | Sequence flow |  |
| F02 | T1 Report the suspicious event | T2 Register and classify the event | Sequence flow |  |
| F03 | T2 Register and classify the event | T4 Assess the significance | Sequence flow |  |
| F04 | T4 Assess the significance | G1 Significant incident? | Sequence flow |  |
| F05 | G1 Significant incident? | T5 Handle as a routine event | Sequence flow | No |
| F06 | T5 Handle as a routine event | E1 Routine event closed | Sequence flow |  |
| F07 | G1 Significant incident? | T6 Activate the incident procedure | Sequence flow | Yes |
| F08 | T6 Activate the incident procedure | G2 | Sequence flow |  |
| F09 | G2 | G4 Which measures are needed? | Sequence flow |  |
| F10 | G2 | T10 Collect and preserve evidence | Sequence flow |  |
| F11 | G2 | TE1 Time limit: 24 h after becoming aware | Sequence flow |  |
| F12 | G4 Which measures are needed? | T7 Isolate the affected systems | Sequence flow |  |
| F13 | G4 Which measures are needed? | T8 Block accounts and addresses | Sequence flow |  |
| F14 | G4 Which measures are needed? | T9 Switch to backup systems | Sequence flow |  |
| F15 | T7 Isolate the affected systems | G5 | Sequence flow |  |
| F16 | T8 Block accounts and addresses | G5 | Sequence flow |  |
| F17 | T9 Switch to backup systems | G5 | Sequence flow |  |
| F18 | TE1 Time limit: 24 h after becoming aware | T11 Send the early warning | Sequence flow |  |
| F19 | T11 Send the early warning | ME1 Feedback and guidance received | Sequence flow |  |
| F20 | G5 | G3 | Sequence flow |  |
| F21 | T10 Collect and preserve evidence | G3 | Sequence flow |  |
| F22 | ME1 Feedback and guidance received | G3 | Sequence flow |  |
| F23 | G3 | T12 Prepare the initial assessment | Sequence flow |  |
| F24 | T12 Prepare the initial assessment | TE2 Time limit: 72 h after becoming aware | Sequence flow |  |
| F25 | TE2 Time limit: 72 h after becoming aware | T13 Send the incident notification | Sequence flow |  |
| F26 | T13 Send the incident notification | T14 Remove the cause, restore services | Sequence flow |  |
| F27 | T14 Remove the cause, restore services | T15 Review and update the procedure model | Sequence flow |  |
| F28 | T15 Review and update the procedure model | TE3 Time limit: one month after the notification | Sequence flow |  |
| F29 | TE3 Time limit: one month after the notification | T16 Prepare and send the final report | Sequence flow |  |
| F30 | T16 Prepare and send the final report | E2 Incident closed | Sequence flow |  |
| F31 | CS1 Early warning received | C1 Register and assess the early warning | Sequence flow |  |
| F32 | C1 Register and assess the early warning | C2 Send feedback and guidance | Sequence flow |  |
| F33 | C2 Send feedback and guidance | CS2 Incident notification received | Sequence flow |  |
| F34 | CS2 Incident notification received | C3 Assess the incident notification | Sequence flow |  |
| F35 | C3 Assess the incident notification | CS3 Final report received | Sequence flow |  |
| F36 | CS3 Final report received | C4 Evaluate the final report, close the case | Sequence flow |  |
| F37 | C4 Evaluate the final report, close the case | CE Case closed | Sequence flow |  |
| M1 | T11 Send the early warning | CS1 Early warning received | Message flow | Early warning |
| M2 | C2 Send feedback and guidance | ME1 Feedback and guidance received | Message flow | Feedback and guidance |
| M3 | T13 Send the incident notification | CS2 Incident notification received | Message flow | Incident notification |
| M4 | T16 Prepare and send the final report | CS3 Final report received | Message flow | Final report |
| D1 | T2 Register and classify the event | DO1 Incident ticket | Data line (data association) | |
| D2 | DO1 Incident ticket | T4 Assess the significance | Data line (data association) | |
| D3 | DS1a Procedure models | T6 Activate the incident procedure | Data line (data association) | |
| D4 | T10 Collect and preserve evidence | DO2 Evidence package | Data line (data association) | |
| D5 | T12 Prepare the initial assessment | DO3 Initial assessment | Data line (data association) | |
| D6 | DO3 Initial assessment | T13 Send the incident notification | Data line (data association) | |
| D7 | T15 Review and update the procedure model | DS1b Procedure models | Data line (data association) | |
| D8 | T16 Prepare and send the final report | DO4 Final report | Data line (data association) | |

Xətlərin elementə hansı tərəfdən girdiyini nümunə şəkildən götür. Vacib olanlar:

- F05 (`No`): G1-in yuxarı ucundan düz yuxarı, T5-in altına.
- F08: T6-dan sağa, sonra yuxarı SOC analyst zolağına, G2-nin sol ucuna.
- G2 (AND): yuxarı ucdan G4-ə (IT operations), sağ ucdan T10-a, aşağı ucdan TE1-ə.
- G3 (AND): soldan T10, yuxarıdan G5, aşağıdan ME1 gəlir; sağdan T12-yə çıxır.
- F26: T13-ün üstündən düz yuxarı, T14-ün altına. F27: T14-dən sağa, sonra aşağı, T15-in üstünə.
- M1: T11-in altından aşağı, iki Pool arasında sola dönür, CS1-in üstünə enir.

## 6. Yoxlama siyahısı

- [ ] 2 Pool var; yuxarıdakında 4 Swimlane var, adlar düzdür.
- [ ] 19 Task, 11 Event, 5 Gateway var (4-cü bölmədəki cədvəldə 35 sətir + 6 Data sətri).
- [ ] 3 Timer hadisəsi saat simvolu ilə, 4 Message hadisəsi (CS1, ME1, CS2, CS3) zərf simvolu ilədir.
- [ ] G1 XOR (X), G2 və G3 AND (+), G4 və G5 OR (dairə) simvoludur.
- [ ] Hər Task-a bir xətt girir, bir xətt çıxır (Message və Data xətləri sayılmır).
- [ ] 37 Sequence flow, 4 Message flow, 8 Data xətti çəkilib.
- [ ] Heç bir Sequence flow Pool sərhədini keçmir; Pool-lar yalnız Message flow ilə bağlıdır.
- [ ] G1-dən çıxan xətlərdə `Yes` və `No` yazılıb; Message flow-ların adı yazılıb.
- [ ] Xətlər bir-birini kəsmir, yazılar oxunur.

## 7. Saxlamaq və göndərmək

1. **ADF.** Əsas menyuda `Save as...`: fayl adı `vagif.asgarli-T5L.adf` (ArisExpress-in öz
   formatı). Sonrakı dəyişikliklər üçün `Save`.
2. **PDF.** Əsas menyuda `Export` altında **`Graphic as PDF...`** əmri var (izahı: «Export
   graphic as PDF»). Fayl adı: `vagif.asgarli-T5L-model.pdf`. Eyni yerdə «Model information
   as PDF» də var, o bizə lazım deyil. PDF-i açıb yoxla: bütün diaqram görünməlidir. Əmri
   tapmasan: `Print...`, printer kimi «Microsoft Print to PDF», diaqram **bir səhifəyə**
   sığsın (landscape).
   Əlavə imkan: **Export graphic** pəncərəsi şəkli `PNG`, `JPG` və ya `EMF` kimi saxlayır;
   orada «Export entire graphic» seçimini et. PNG təqdimat üçün yaxşıdır, amma müəllimin
   istədiyi format PDF-dir.
3. Bu iki faylı mənə göndər (və ya Drive qovluğuna at). Mən PDF-dən şəkli çıxarıb protokola və
   təqdimata qoyacam, yekun `vagif.asgarli-T5L.pdf` protokolunu hazırlayacam.
4. İstəsən, təqdimat üçün diaqramın üç böyüdülmüş ekran şəklini də çək (sol hissə: aşkarlama;
   orta hissə: paralel işlər; sağ hissə: hesabatlar). Göndərməsən, şəkil avtomatik iki yerə
   bölünəcək.
5. Müəllimə göndərilənlər (`egils.ginters@rtu.lv`): protokol `vagif.asgarli-T5L.pdf`
   (imzalanmış), model `vagif.asgarli-T5L.adf` və `vagif.asgarli-T5L-model.pdf`, təqdimat
   `vagif.asgarli-T5L-presentation.pptx`.

Müdafiədə diaqramı ArisExpress-in özündə açıb göstərmək lazım ola bilər: faylı əvvəlcədən öz
kompüterində aç, böyütmə (zoom) ilə soldan sağa keçməyi məşq et.

## 8. Çətinlik olsa

- **Timer və ya Message simvolunu tapmırsan.** Simvol «BPMN diagram» tipində var (2-ci bölmə).
  **Symbols** panelini sona qədər sürüşdür; yoxdursa, **Add symbols** pəncərəsindən əlavə et.
  Alınmasa, adi `Intermediate event` qoy, adını yaz və mənə de: protokolda bunu qeyd edərik.
- **«BPMN modeling constraints» pəncərəsi çıxır.** Bu, elementi başqa Pool-a daşıyanda və ya
  xətt qaydanı pozanda görünür (Sequence flow Pool sərhədini keçə bilməz, Message flow isə
  yalnız müxtəlif Pool-lar arasında olur). `Cancel` bas (element yerinə qayıdır) və səhvi
  düzəlt. `Ignore constraints` basma: model BPMN qaydalarına uyğun olmaz.
- **Data store-u eyni adla ikinci dəfə qoymaq istəmir.** Birincini kopyala və yapışdır (Ctrl+C,
  Ctrl+V); adətən proqram eyni obyektin ikinci görünüşünü yaradır. Bu bizə lazım olandır: bir
  anbar, iki yerdə göstərilir. Alınmasa, eyni adla ikinci Data store qoymaq da olar.
- **Xətt səhv tiplə çəkilir.** Sequence flow yalnız eyni Pool-un içində, Message flow yalnız
  müxtəlif Pool-lar arasında olur. Səhv yerə birləşdirmisənsə, xətti sil və yenidən çək.
- **Diaqram çox enlidir.** Bu normaldır. Protokolda bütöv şəkil üfüqi səhifədə, sonra iki
  böyüdülmüş hissə kimi verilir.
