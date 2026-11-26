# T5L müdafiəyə hazırlıq: izah və ehtimal olunan suallar

Bu sənəd T5L işini (CyberFlow məqsəd sisteminin CLD-si və BPMN2 modeli) başa düşmək və müəllimə
izah etmək üçündür. Terminləri müəllimin işlətdiyi kimi saxla: *goal system*, *Causal Loops
Diagram (CLD)*, *reinforced* və *balanced* loops, *Pool*, *Swimlanes*, *Events / Intermediate
events*, *Gateways (OR, AND, XOR)*, *Message and Data lines*, *Data objects*.

## 1. Bir dəqiqəlik xülasə (ingiliscə deyə biləcəyin mətn)

> My goal system is CyberFlow, from my PR1 topic "Application of BPMN 2.0 Diagrams in Modelling
> Cybersecurity Procedures". It is a BPMN 2.0-based method and model repository for the
> incident-handling procedures of a medium-sized Latvian organisation that is subject to NIS2.
> First I drew the Causal Loops Diagram of the goal system: it has 14 variables and five feedback
> loops, two balanced and three reinforced. Then I described the operation of the system in
> BPMN2: the handling of one significant cyber incident. The model has two Pools, the organisation
> with four Swimlanes and the CSIRT, eleven events of five kinds, the three Gateways XOR, AND and
> OR, four Message flows and data objects with data lines. The model was drawn in ArisExpress.

## 2. Məqsəd sistemi (goal system) nədir

**CyberFlow**: kiberinsidentləri idarə etmə prosedurlarını BPMN 2.0 diaqramları ilə təsvir edən
metod və model anbarı (repository). Orta ölçülü, NIS2 direktivinə tabe olan Latviya təşkilatı
üçündür.

- **Niyə lazımdır:** prosedurlar (playbook-lar) hələ də əsasən mətn kimi yazılır. Bir
  araşdırmada 147 mütəxəssisin playbook-larının 76,7%-i mətn əsaslı idi (Schlette et al., 2024).
  Qanun isə az vaxt verir: əhəmiyyətli insident barədə CSIRT-ə **24 saat** ərzində *early
  warning*, **72 saat** ərzində *incident notification*, bildirişdən sonra **bir ay** ərzində
  *final report* göndərilməlidir (NIS2, Article 23(4); Latviyanın Milli Kibertəhlükəsizlik
  Qanunu, Section 34). CERT.LV 2025-ci ildə 2 982 insidenti əl ilə emal edib.
- **Sosiotexniki sistemdir:** sosial hissə insanlardır (işçi, SOC analitiki, kibertəhlükəsizlik
  meneceri, İT əməliyyatları) və milli CSIRT (CERT.LV). Texniki hissə BPMN 2.0 prosedur
  modelləri, onların anbarı və modelləşdirmə qaydalarıdır.
- **Məqsəd:** hər iştirakçı proseduru eyni cür başa düşsün, prosedur səhvləri azalsın, qanuni
  müddətlər pozulmasın.

## 3. CLD-ni necə oxumaq

Şəkil: `outputs/figures/fig1_cyberflow_cld.png`. İşarələr müəllimin şablonundakı kimidir:

- mavi ox, «+»: iki dəyişən **eyni istiqamətdə** dəyişir (biri artanda o biri də artır);
- qırmızı ox, «−»: **əks istiqamətdə** dəyişir (biri artanda o biri azalır);
- oxun üstündə iki cizgi: təsir **gecikmə** (delay) ilə gəlir;
- dairəvi ox və hərf: **R** = reinforced (gücləndirən) loop, **B** = balanced (tarazlayan) loop;
- kursivlə yazılanlar: xarici təsirlər (sistemdən kənardan gəlir).

**Loop-un növünü necə təyin edirsən:** loop-dakı «−» oxlarını say. Cüt sayda (0, 2) olarsa
reinforced, tək sayda (1) olarsa balanced. Bunu `tools/check_cld.py` də yoxlayır.

| Loop | Yol | «−» sayı | Mənası |
|---|---|---|---|
| **B1** loss-driven improvement | Incident losses → Management support → Procedure models → Staff understanding → (−) Procedural errors → Response time → Incident losses | 1 | İtkilər artanda rəhbərlik dəstək verir, modellər yaxşılaşır, işçilər rolunu yaxşı bilir, səhv azalır, cavab sürətlənir, itki azalır. Sistem itkiyə reaksiya verir, amma gecikmə ilə. |
| **B2** maintenance limit | Procedure models → Maintenance workload → (−) Procedure models | 1 | Model çoxaldıqca onları yeniləmək işi artır; iş çox olanda modellər köhnəlir. Anbarın böyüməsini məhdudlaşdırır. |
| **R1** learning | Procedure models → Use of the models → Lessons learned → Procedure models | 0 | Yaxşı model real insidentdə işlədilir, hər istifadədən sonra dərs çıxarılır, dərs modeli yaxşılaşdırır. Əks istiqamətdə də işləyir: işlədilməyən model yaxşılaşmır. |
| **R2** workload spiral | Procedural errors → Analyst workload → Procedural errors | 0 | Səhv təkrar iş yaradır, yüklənmiş analitik daha çox səhv edir. Zərərli dairə. |
| **R3** cooperation with the CSIRT | Response time → (−) Timely notification → CSIRT guidance → (−) Response time | 2 | Cavab tez olanda bildiriş vaxtında gedir, CSIRT rəy və məsləhət verir (NIS2, Article 23(5)), bu da cavabı daha da sürətləndirir. Gecikmə əks effekt verir. |

Xarici təsirlər: *Cyber threats* itkiləri artırır; *NIS2 and national law* rəhbərlik dəstəyini
artırır.

**Sabitlik (müəllim soruşa bilər):** müəllimin T4 mühazirəsindəki qayda: «Reinforcing loops must
be balanced, otherwise the system will be unstable». Bizdə R1-in böyüməsini B2 məhdudlaşdırır;
R2 və ya R3 zərərli istiqamətdə işləyəndə cavab vaxtı və itkilər artır, bu da B1-i işə salır.

## 4. BPMN2 diaqramında addım-addım gəzinti

Şəkil: `outputs/figures/fig2_cyberflow_bpmn2_reference.png` (yekun variant ArisExpress-dən).
Diaqram **bir əhəmiyyətli kiberinsidentin idarə olunmasını** göstərir.

**İki Pool:** «Organisation (essential entity)» (4 Swimlane: Employee, IT operations, SOC
analyst, Cybersecurity manager (CISO)) və «CSIRT (CERT.LV)». Pool ayrı iştirakçıdır, Swimlane
Pool-un içindəki roldur.

1. **Start event** «Suspicious activity noticed»: işçi şübhəli hal görür və xəbər verir (Task
   «Report the suspicious event»).
2. SOC analitiki hadisəni qeydə alır və təsnif edir; **Data object** «Incident ticket» yaranır.
3. Kibertəhlükəsizlik meneceri əhəmiyyəti qiymətləndirir. **Gateway XOR** «Significant
   incident?»: yalnız bir yol seçilir. *No*: adi hadisə kimi bağlanır (End event «Routine event
   closed»). *Yes*: insident proseduru işə salınır; prosedur **Data store** «Procedure models»-dən
   oxunur.
4. **Gateway AND**: üç iş **paralel** başlayır:
   - İT əməliyyatları zərəri məhdudlaşdırır. **Gateway OR** «Which measures are needed?»: üç
     tədbirdən **biri, ikisi və ya hamısı** seçilir (sistemləri təcrid et; hesabları və ünvanları
     blokla; ehtiyat sistemlərə keç). İkinci OR onları birləşdirir.
   - SOC analitiki sübutları toplayır və qoruyur (Data object «Evidence package»).
   - Menecer **24 saat** müddətində (Timer event) *early warning* göndərir (Message flow CSIRT-ə)
     və CSIRT-in rəyini gözləyir (Message intermediate event «Feedback and guidance received»).
   İkinci **Gateway AND** hər üç qol bitənə qədər gözləyir.
5. SOC analitiki ilkin qiymətləndirməni hazırlayır (Data object «Initial assessment»).
6. Menecer **72 saat** müddətində (Timer event) *incident notification* göndərir (Message flow).
7. İT əməliyyatları səbəbi aradan qaldırır və xidmətləri bərpa edir.
8. Menecer insidenti nəzərdən keçirir və prosedur modelini yeniləyir (Data store «Procedure
   models»-ə yazır). Bu, CLD-dəki R1 (learning) loop-unun BPMN2-dəki izidir.
9. **Bir ay** müddətində (Timer event) *final report* hazırlanıb göndərilir (Data object, Message
   flow). **End event** «Incident closed».

**CSIRT Pool-u:** Message start event «Early warning received» → xəbərdarlığı qeydə alır və
qiymətləndirir → rəy və məsləhət göndərir → Message event «Incident notification received» →
bildirişi qiymətləndirir → Message event «Final report received» → yekun hesabatı
qiymətləndirir, işi bağlayır → End event «Case closed».

## 5. Hər element niyə oradadır

| Element | Niyə |
|---|---|
| 2 Pool | Təşkilat və CSIRT ayrı iştirakçılardır; aralarında yalnız mesaj mübadiləsi var (qanun bunu tələb edir). |
| 4 Swimlane | Hər tapşırığın bir məsul rolu olsun: CLD-dəki «Staff understanding of roles and steps». «Cybersecurity manager» rolu Latviya qanununun 25-ci bölməsində nəzərdə tutulub. |
| XOR | Qərar: insident əhəmiyyətlidir, ya yox (NIS2, Article 23(3) meyarları). Yalnız bir cavab ola bilər. |
| AND | Zərərin məhdudlaşdırılması, sübutların toplanması və xəbərdarlıq eyni vaxtda getməlidir; 24 saat gözləmək olmaz. |
| OR | Hansı texniki tədbirin lazım olduğu insidentdən asılıdır: bir və ya bir neçəsi. |
| Timer events | Üç qanuni müddət: 24 saat, 72 saat, bir ay. |
| Message events və Message flows | Pool-lar arasında əlaqə: early warning, feedback and guidance, incident notification, final report. |
| Data objects | Proses zamanı yaranan sənədlər: Incident ticket, Evidence package, Initial assessment, Final report. |
| Data store (iki dəfə) | Prosedur modellərinin anbarı: əvvəldə oxunur, sonda yenilənir. Eyni anbardır, xətlər kəsişməsin deyə iki yerdə çəkilib. |

## 6. CLD-dən BPMN2-yə keçid (protokolun 2a bəndi və nəticələr)

- CLD **dəyişənləri** və onların təsirini göstərir («niyə?»), BPMN2 **fəaliyyətləri** və onların
  ardıcıllığını göstərir («necə, kim, nə vaxt?»). Ona görə birbaşa çevirmək olmur.
- 14 dəyişəndən 11-ni prosesin bir yerinə bağlamaq mümkün oldu (protokolda Table 2). Üçünün
  (Procedural errors, Analyst workload, Management support) BPMN2 elementi yoxdur: bunlar
  prosesin addımı deyil, onun nə dərəcədə yaxşı icra olunduğunu göstərir.
- **Əks əlaqə loop-ları BPMN2-də görünmür.** Proses start-dan end-ə gedir; R1 kimi loop yalnız
  çoxlu insidentdən sonra bağlanır. Dolayı göstərilib: sonda Data store yenilənir, növbəti
  insident onu oxuyur.
- **Rahat tərəfi:** CLD sistemin sərhədini və iştirakçıları artıq müəyyən etmişdi (CSIRT ikinci
  Pool oldu, R3-ün oxları Message flow oldu, «Response time» Timer-lərə işarə etdi).
- **Əsas çətinlik:** CLD-də rollar, ardıcıllıq, şərtlər, müddətlər və sənədlər yoxdur; onları
  qanundan və insident idarəetmə tövsiyələrindən götürmək lazım gəldi.
- **Vaxt:** «24 saatdan gec olmayaraq» gözləmə vaxtı deyil; BPMN-in qeyri-müəyyən vaxtlı işləri
  zəif dəstəkləməsi müəllimin T5 mühazirəsində də çatışmazlıq kimi göstərilir.

## 7. Ehtimal olunan suallar və qısa cavablar

**BPMN2 nədir?**
Business Process Model and Notation, 2.0 versiyası (OMG, 2011-ci ilin yanvarı; ISO 19510).
Metodologiya deyil, qrafik notasiyadır. Prosesi Pool/Swimlane ilə «xüsusiyyətə görə», Gateway
ilə «şərtə görə» paralelləşdirir.

**CLD ilə BPMN2-nin fərqi nədir?**
CLD səbəb-nəticə əlaqələrini və əks əlaqələri göstərir, başlanğıcı və sonu yoxdur, budaqlanma və
paralellik göstərilmir. BPMN2 fəaliyyətləri, icraçıları, ardıcıllığı və şərtləri göstərir, start
və end hadisəsi var, amma loop-lar görünmür.

**XOR, OR və AND arasında fərq nədir?**
XOR: çıxışlardan **yalnız biri** (bəli/yox qərarı). AND: **hamısı** paralel. OR: **bir və ya
bir neçəsi**. Birləşdirəndə: AND hamısını gözləyir, OR aktiv olan qolları gözləyir, XOR
gələn ilk qolu buraxır.

**Niyə XOR-un birləşdirən cütü yoxdur?**
«No» qolu öz End event-i ilə bitir, ona görə birləşdirməyə ehtiyac yoxdur. AND və OR isə
bölündükdən sonra eyni tipli Gateway ilə bağlanır.

**Timer event-lər niyə göndərmə tapşırığından əvvəldir? Proses 24 saat gözləyir?**
Xeyr. Bu konseptual modeldə Timer müddətin **son həddini** göstərir: mesaj bu vaxta qədər
getməlidir. İcra olunan modeldə bu, tapşırığa bağlanmış (boundary) Timer və eskalasiya yolu ilə
göstərilərdi. Bunu nəticələrdə çətinlik kimi yazmışam.

**Sequence flow ilə Message flow-un fərqi?**
Sequence flow bir Pool-un içində işlərin ardıcıllığıdır (bütöv xətt). Message flow müxtəlif
Pool-lar arasında məlumat mübadiləsidir (qırıq xətt). Sequence flow Pool sərhədini keçə bilməz.

**Data object ilə Data store-un fərqi?**
Data object prosesin bir icrası zamanı mövcud olan sənəddir (məsələn, Incident ticket). Data
store prosesdən asılı olmayaraq qalan anbardır (Procedure models).

**Niyə CSIRT ayrıca Pool-dur, Swimlane deyil?**
CSIRT başqa təşkilatdır (CERT.LV), öz prosesi var. Müstəqil iştirakçılar ayrı Pool olur və
yalnız mesajla əlaqə saxlayır.

**Niyə «Cybersecurity manager»?**
Latviyanın Milli Kibertəhlükəsizlik Qanunu (Section 25) hər subyektdə kibertəhlükəsizlik
menecerinin təyin olunmasını tələb edir. Bu, CISO roluna uyğundur.

**«Significant incident» nədir?**
NIS2, Article 23(3): xidmətlərin ciddi pozulmasına və ya maliyyə itkisinə səbəb olan (ola bilən),
yaxud başqa şəxslərə əhəmiyyətli ziyan vuran (vura bilən) insident.

**CSIRT nə cavab verir?**
NIS2, Article 23(5): early warning alandan sonra mümkün qədər 24 saat ərzində ilkin rəy, sorğu
olarsa tədbirlər üzrə məsləhət. Latviya qanununda Section 35.

**CLD-də hansı loop-lar reinforced-dir və sistem sabitdirmi?**
R1, R2, R3 reinforced; B1, B2 balanced. Reinforced loop-lar balanced loop-larla tarazlanır
(R1-i B2, R2 və R3-ü B1), ona görə sistem nəzarətdən çıxmır; amma B1 gecikmə ilə işlədiyi üçün
dalğalanma ola bilər.

**Loop-un növünü necə yoxladın?**
Hər loop-da mənfi oxları saydım: cüt say reinforced, tək say balanced.

**Modelin düzgünlüyünü necə yoxladın?**
Hər Sequence flow öz Pool-unun içində qalır; Message flow-lar müxtəlif Pool-ları birləşdirir;
hər element start-dan end-ə gedən yolun üstündədir; AND və OR bölünmələri eyni tipli Gateway
ilə bağlanır; xətlər kəsişmir.

**BPMN2-nin çatışmazlıqları?**
Müəllimin T5 mühazirəsindən: stoxastik və ya vaxtı qeyri-müəyyən tapşırıqları zəif dəstəkləyir;
ətraflı çertyoj çox böyük olur (buna görə choreography notasiyası var).

**Niyə məhz bu proses seçildi?**
CLD-dəki beş loop-un hamısı insidentin idarə olunmasından keçir: modellərin istifadəsi (R1),
səhvlər və yük (R2), cavab vaxtı və CSIRT (R3, B1), modellərin yenilənməsi (B2).

**Süni intellektdən istifadə etmisən?**
Düzünü de: müəllim işi tam AI dəstəyi ilə hazırlamağa icazə verib; model və mətn AI köməyi ilə
hazırlanıb, sən isə hər elementi izah edə bilirsən. Diaqramı ArisExpress-də özün çəkmisənsə, bunu
da de.

## 8. Müdafiədən əvvəl

- [ ] ArisExpress-də `vagif.asgarli-T5L.adf` açılır; zoom ilə soldan sağa keçməyi məşq et.
- [ ] Təqdimatı bir dəfə ucadan danış (5–7 dəqiqə).
- [ ] 3-cü bölmədəki beş loop-u şəkildə barmaqla göstərə bilirsən.
- [ ] XOR, AND, OR-un diaqramda harada olduğunu və niyə olduğunu deyə bilirsən.
- [ ] Üç müddəti (24 saat, 72 saat, bir ay) və onların mənbəyini (NIS2 Article 23(4); Latviya
      qanunu Section 34) yadda saxla.
- [ ] Protokol imzalanıb.
