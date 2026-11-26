# PR1 izahı: xülasə və təqdimat (Vaqif üçün)

Bu qeyd müdafiəyə hazırlıq üçündür. Xülasə və slaydlar ingiliscədir; burada hər hissənin nə dediyini,
rəqəmlərin haradan gəldiyini və müəllimin verə biləcəyi sualları Azərbaycan dilində izah edirəm.
Cavabların ingiliscə qısa variantı da var, çünki müdafiə ingiliscə olacaq.

## 1. PR1 nədir və nə təhvil verilir

| Nə | Fayl | Qeyd |
|---|---|---|
| Xülasə (PR1, 16.09 sütunu) | `outputs/submission/VagifAsgarli-PR1.pdf` | 1-ci səhifə: xülasə (bir A4). 2-ci səhifə: References və AI qeydi. Müəllimin ünvanına e-poçtla göndərilir. |
| Təqdimat (PR1 Prez., 23.09 sütunu) | `outputs/submission/VagifAsgarli-PR1-presentation.pptx` | 12 slayd, müəllimin öz slayd dizaynında. Hər slaydın altında ingiliscə danışıq mətni (Notes) var. |

Mövzu müəllimin siyahısından sənə düşən mövzudur (251ADM047):
**"Application of BPMN 2.0 Diagrams in Modelling Cybersecurity Procedures"**.

Müəllim PR1 təqdimatı üçün ayrıca şablon, vaxt limiti və ya slayd sayı verməyib (tapşırıq faylında
yalnız xülasənin quruluşu var). Ona görə təqdimat xülasənin beş paraqrafını eyni ardıcıllıqla izləyir.

## 2. Xülasə paraqraf-paraqraf

Müəllimin şablonu beş paraqraf tələb edir. Hər birində nə yazılıb və niyə:

**1-ci paraqraf: mövzunun aktuallığı (dünya, Avropa, Latviya).** Müəllim üç səviyyə və rəqəmlər
istəyir. Dünya: bir məlumat sızmasının orta xərci 2026-cı ildə 4.99 milyon dollar olub, bu rekorddur
və bir il əvvəlkindən 12 % çoxdur (IBM). Avropa: ENISA 2025-ci ilin 8,257 insidentini təhlil edib,
onların 72.9 %-i "essential entities"-ə (vacib sektorların təşkilatları) aiddir; NIS2 direktivi bu
təşkilatlardan insidentlərin idarə olunmasını və ciddi insident barədə üç mərhələli hesabat tələb
edir: 24 saat ərzində erkən xəbərdarlıq, 72 saat ərzində bildiriş, bir ay ərzində yekun hesabat.
Latviya: eyni müddətlər 1 sentyabr 2024-dən qüvvədə olan Milli Kibertəhlükəsizlik Qanununda var;
CERT.LV 2025-ci ildə 2,982 insidenti əl ilə emal edib, bu 2024-dən 28 % çoxdur. Nəticə cümləsi:
belə müddətlərə yalnız hamının eyni cür başa düşdüyü prosedurla əməl etmək olar.

**2-ci paraqraf: problem və üç mövcud həll.** Problem: insidentə cavab prosedurları ("playbook")
hələ də əsasən adi mətn və ya konkret istehsalçının koduna bağlı formada yazılır, ona görə
birmənalı deyil, yoxlamaq, paylaşmaq və avtomatlaşdırmaq çətindir. Sübut: 1,217 açıq playbook və
147 mütəxəssislə aparılan araşdırmada mütəxəssislərin playbook-larının 76.7 %-i mətn idi, açıq
playbook-ları isə olduğu kimi istifadə etmək mümkün deyildi (Schlette et al., 2024); başqa
təcrübədə ekspertlər iki standart çərçivə ilə yazılmış 24 playbook-dan 11-ni real istifadə üçün
kifayət qədər detallı saymayıb (Stevens et al., 2022). Üç mövcud həll:

| Həll | Prinsipi | Üstünlüyü | Məhdudiyyəti |
|---|---|---|---|
| NIST SP 800-61 Revision 3 | Mətn şəklində tövsiyələr; prosedurları playbook kimi sənədləşdirməyi məsləhət görür | Çevikdir | Heç bir notasiya (qrafik dil) vermir, mətnin qeyri-müəyyənliyi qalır |
| CACAO Security Playbooks 2.0 | OASIS spesifikasiyası (27.11.2023): playbook JSON formatında, səkkiz addım növündən ibarət iş axını kimi yazılır | Maşın oxuya bilir, paylaşmaq olur | Öz qrafik notasiyası yoxdur; sadə playbook belə yüzlərlə sətir kod tutur |
| BPMN 2.0 və SecBPMN kimi təhlükəsizlik genişlənmələri | OMG-nin qrafik notasiyası; SecBPMN təhlükəsizlik annotasiyaları və sorğu dili əlavə edir | Menecer də, mühəndis də oxuya bilir; SecBPMN 50 fəaliyyətli prosesi 14.71 saniyəyə yoxlayıb | 1,400 mənbə içində cəmi 12 təhlükəsizlik genişlənməsi tapılıb; onlar standartın hissəsi deyil; biznes proseslərinə təhlükəsizlik tələbi yazır, cavab prosedurunun özünü təsvir etmir; modeli icra olunan iş axını ilə sinxron saxlamaq çətindir |

**3-cü paraqraf: yanaşma, məqsəd, vəzifələr, metodlar.** Yanaşma: heç bir genişlənmə işlətmədən,
yalnız standart BPMN 2.0 elementləri ilə prosedur çəkmək (pool, swimlane, timer event, message flow,
data object), belə ki modeli pulsuz alətlərdə çəkmək olsun. Məqsəd: **CyberFlow**-u hazırlamaq və
yoxlamaq. CyberFlow bizim təklif etdiyimiz addır: NIS2-yə tabe olan orta ölçülü Latviya təşkilatının
insident prosedurları üçün BPMN 2.0 əsaslı metod və model toplusu (repository). Beş vəzifə:
(1) hüquqi tələbləri və mövcud playbook formatlarını təhlil etmək; (2) rolları, müddətləri,
bildirişləri və sənədləri BPMN elementlərinə uyğunlaşdıran modelləşdirmə qaydaları yazmaq;
(3) "goal system"-in konseptual modelini (concept map, CLD) və üç tipik prosedurun BPMN modelini
(fişinq, ransomware, DoS) qurmaq; (4) modelləri notasiyaya və hüquqi tələblərə görə yoxlamaq
(verification); (5) "tabletop exercise"-də mətn versiyaları ilə müqayisə edib təsdiqləmək
(validation). Metodlar: ədəbiyyat təhlili, konseptual modelləşdirmə (concept map, CLD, ARIS
Express-də BPMN 2.0), ekspert rəyi, müqayisəli eksperiment.

**4-cü paraqraf: gözlənilən nəticələr və istifadəçilər.** Nəticələr: üç yoxlanmış prosedur modeli
(hər addımın məsul rolu var, üç hesabat müddəti açıq "event" kimi göstərilib), modelləşdirmə
qaydaları toplusu və təcrübədən ölçülmüş sübut. **"Ən azı 20 % az prosedur səhvi" bizim qoyduğumuz
hədəfdir, ölçülmüş nəticə deyil** (bax: sual 7). İstifadəçilər: vacib və əhəmiyyətli təşkilatların
CISO-ları və SOC komandaları (xüsusən avtomatlaşdırma platforması olmayanlar), auditorlar, CSIRT.
Faydası: kimin nəyi nə vaxt etdiyinin ortaq və birmənalı təsviri, yeni işçilərin daha tez
öyrədilməsi, uyğunluğun sənədli sübutu və avtomatlaşdırma üçün başlanğıc; IBM-ə görə təhlükəsizlikdə
AI və avtomatlaşdırmanı geniş işlədən təşkilatlarda sızma xərci 1.93 milyon dollar az olur.

**5-ci paraqraf: gələcək inkişaf.** Müəllim soruşur: həll problemi tam həll edirmi? Cavab: yox.
BPMN 2.0 simulyasiyanı, monitorinqi və təşkilati resurs modellərini əhatə etmir (OMG, 2011), yəni
model prosedurun məntiqini göstərir, amma onu icra etmir və cavab vaxtını proqnozlaşdırmır; qrafik
modelləri yalnız öyrədilmiş oxucular daha yaxşı başa düşür (Ottensooser et al., 2012); BPMN ilə
CACAO arasında uyğunluq birə-bir deyil (Zych et al., 2023). Gələcək iş: modelləri avtomatik CACAO
playbook-una çevirmək, cavab vaxtını system dynamics və diskret-hadisə modelləri ilə simulyasiya
etmək, başqa insident növləri və sektorlar əlavə etmək, qiymətləndirməni bir neçə təşkilatda
təkrarlamaq. (System dynamics və BPMN bu kursun T4 və T5 mövzularıdır, ona görə bu cümlə kursla
birbaşa bağlanır.)

**References və qeyd.** 15 mənbə APA 7 formatında, əlifba sırası ilə. Mətndəki hər fakt mötərizədə
istinadla verilib. Sonda müəllimin şablonundakı "Note" sətri doldurulub: generativ AI (Claude,
Anthropic) məlumat axtarışı, mətnin hazırlanması və istinad siyahısının formatlanması üçün
işlədilib. Bu qeyd düzdür və olduğu kimi qalmalıdır.

## 3. Terminlər

| Termin | İzah |
|---|---|
| BPMN 2.0 | Business Process Model and Notation: prosesləri çəkmək üçün qrafik dil, OMG (Object Management Group) standartı, 2011. Beş element qrupu var: flow objects (event, activity, gateway), data, connecting objects, swimlanes, artifacts. |
| Pool | Prosesin bir iştirakçısı: ayrı təşkilat və ya sistem (məsələn "Təşkilat" və "CSIRT"). Böyük düzbucaqlı. |
| Swimlane (lane) | Pool-un içindəki zolaq: bir rol və ya şöbə (işçi, SOC analitiki, insident meneceri, IT). Hər tapşırığın kimə aid olduğunu göstərir. |
| Sequence flow | Eyni pool daxilində addımların ardıcıllığı: bütöv ox. |
| Message flow | İki pool arasında mesaj: qırıq xətli ox. Bildirişlər (early warning, notification, final report) belə göstərilir. |
| Event | Hadisə: dairə. Start, intermediate, end. Timer event (saat işarəsi) müddəti göstərir: 24 saat, 72 saat, bir ay. |
| Gateway | Qərar və ya paralellik nöqtəsi: romb. XOR (yalnız bir yol), OR (bir və ya bir neçə yol), AND (hamısı paralel). |
| Data object | Sənəd və ya məlumat: küncü qatlanmış vərəq (insident bileti, sübut paketi, yekun hesabat). |
| Playbook | Müəyyən insident növündə kimin nə etməli olduğunu addım-addım yazan prosedur. |
| Incident handling | İnsidentin qarşısını almaq, aşkarlamaq, təhlil etmək, lokallaşdırmaq, cavab vermək və bərpa olunmaq üçün bütün hərəkət və prosedurlar (NIS2-nin tərifi). |
| NIS2 | Directive (EU) 2022/2555: Aİ-nin kibertəhlükəsizlik direktivi. Vacib ("essential") və əhəmiyyətli ("important") təşkilatlara risk idarəetməsi və insident hesabatı öhdəliyi qoyur. |
| Essential / important entities | NIS2-nin iki kateqoriyası: enerji, nəqliyyat, bank, səhiyyə, rəqəmsal infrastruktur kimi sektorların orta və böyük təşkilatları. |
| CSIRT | Computer Security Incident Response Team: insidentlərə cavab komandası. Təşkilat insident barədə milli CSIRT-ə məlumat verir. Latviyada bu işi CERT.LV görür. |
| CERT.LV | Latviyanın insidentlərə cavab qurumu; illik hesabatlarında insident statistikasını dərc edir. |
| NIST SP 800-61 Revision 3 | ABŞ Standartlar İnstitutunun insidentə cavab tövsiyələri (2025). Mətn sənədidir. |
| CACAO | Collaborative Automated Course of Action Operations: OASIS-in playbook standartı. Playbook JSON faylıdır, səkkiz addım növü var (start, end, action, playbook-action, parallel, if, while, switch). |
| OASIS | Açıq standartlar hazırlayan beynəlxalq təşkilat. |
| JSON | Maşın üçün rahat mətn formatı; insan üçün uzun və çətin oxunur. |
| SecBPMN | BPMN-in təhlükəsizlik genişlənməsi: biznes prosesinə təhlükəsizlik annotasiyaları əlavə edir və modeli sorğu dili ilə yoxlayır. Standartın hissəsi deyil. |
| Tabletop exercise | Masa arxası məşq: komanda uydurma insident ssenarisini prosedur üzrə addım-addım müzakirə edir, real sistemə toxunulmur. |
| CISO, SOC | Chief Information Security Officer (təhlükəsizlik rəhbəri); Security Operations Centre (təhlükəsizlik əməliyyatları mərkəzi). |
| Goal system | Kursun termini: layihədə qurulacaq məqsəd sistemi. Bizdə CyberFlow. T5L-də onun CLD-si və BPMN2 modeli çəkilir. |
| Concept map, CLD | Konsept xəritəsi (T3) və Causal Loops Diagram (T4): sistemin statik və dinamik konseptual təsviri. |
| APA 7 | İstinad formatı: mətndə (Müəllif, il), sonda əlifba sırası ilə siyahı. |

## 4. Rəqəmlər haradan gəlir

Bütün rəqəmlər mənbənin öz mətnində yoxlanıb. Müəllim "bu rəqəm haradandır?" soruşsa:

| Rəqəm | Nə deməkdir | Mənbə (References siyahısında) |
|---|---|---|
| USD 4.99 mln, +12 %, rekord | 2026-cı ildə bir məlumat sızmasının dünya üzrə orta xərci | IBM (2026), Cost of a Data Breach Report 2026 (hesabat 602 təşkilatın məlumatına əsaslanır) |
| USD 1.93 mln az | Təhlükəsizlikdə AI və avtomatlaşdırmanı geniş işlədən təşkilatlarda sızma xərcinin fərqi | IBM (2026) |
| 8,257 insident; 72.9 % | ENISA-nın 2025-ci il üzrə təhlil etdiyi insidentlər; essential entities-in payı | ENISA (2026), Threat Landscape 2026 |
| 24 saat, 72 saat, bir ay | Ciddi insident barədə erkən xəbərdarlıq, bildiriş və yekun hesabat müddətləri | Directive (EU) 2022/2555, 23-cü maddə, 4-cü bənd |
| 1 sentyabr 2024 | Latviya Milli Kibertəhlükəsizlik Qanununun qüvvəyə minməsi; eyni müddətlər 34-cü bölmədədir | Nacionālās kiberdrošības likums (2024) |
| 2,982 insident, +28 % | CERT.LV-nin 2025-ci ildə əl ilə emal etdiyi insidentlər, 2024 ilə müqayisə | CERT.LV (2026), 2025-ci ilin illik hesabatı |
| 1,217 playbook, 147 mütəxəssis, 76.7 % | Açıq playbook-ların və praktiklərin sorğusunun nəticəsi | Schlette et al. (2024) |
| 24-dən 11 | İki çərçivə (IACD və NIST) ilə yazılmış 12 + 12 playbook-dan ekspertlərin "kifayət qədər detallı deyil" saydıqları: 6 + 5 | Stevens et al. (2022) |
| 27 noyabr 2023, səkkiz addım növü | CACAO 2.0 Committee Specification 01-in tarixi və iş axınının addım növləri | Jordan & Thomson (2023) |
| "yüzlərlə sətir kod" | Sadə CACAO playbook-unun JSON həcmi | Zych et al. (2023) |
| 50 fəaliyyət, 14.71 saniyə | SecBPMN sorğu mühərrikinin bir prosesi yoxlama vaxtı | Salnitri et al. (2017) |
| 1,400 mənbə, 12 genişlənmə | Sistematik ədəbiyyat icmalının nəticəsi | Hornsteiner et al. (2022) |
| ən azı 20 % | **Bizim eksperiment üçün qoyduğumuz hədəf**, ədəbiyyatdan götürülməyib | öz hədəfimiz |

Qeyd: ENISA hesabatının PDF-də çap olunmuş DOI-si açılmır, ona görə References-də nəşrin rəsmi
səhifəsinin ünvanı verilib.

## 5. Təqdimat: slaydlar və danışıq planı (təxminən 4 dəqiqə)

Hər slaydın ingiliscə hazır mətni PowerPoint-də slaydın altındakı **Notes** hissəsindədir
(View → Notes). Aşağıda hər slaydda nəyi demək lazım olduğu və təxmini vaxt:

| # | Slayd | Vaxt | Nə deyirsən |
|---|---|---|---|
| 1 | Titul | 10 s | Salam, mövzunun adı, xülasənin beş paraqrafı üzrə gedəcəyini de. |
| 2 | Content | 10 s | Quruluşu bir cümlə ilə say. Vaxt azdırsa bu slaydı tez keç. |
| 3 | Relevance of the topic | 30 s | Üç səviyyə, üç rəqəm: 4.99 mln dollar (dünya), 8,257 insident və 72.9 % (Avropa), 2,982 insident və +28 % (Latviya). |
| 4 | Relevance: legal deadlines | 30 s | NIS2-nin üç müddəti: 24 saat, 72 saat, bir ay. Latviyada eyni müddətlər 1 sentyabr 2024-dən. Əsas fikir: belə müddətdə prosedur hamı üçün birmənalı olmalıdır. |
| 5 | Problem identification | 30 s | Playbook-lar mətn və ya istehsalçı kodu kimi yazılır. 76.7 % mətn; 24-dən 11-i kifayət qədər detallı deyil. |
| 6 | Existing solutions | 45 s | Cədvəli sətir-sətir: NIST (çevik, notasiya yoxdur), CACAO (maşın oxuyur, qrafik yoxdur), BPMN və SecBPMN (oxunaqlıdır, amma genişlənmələr standart deyil). Son cümlə: üçündən heç biri cavab prosedurunun standart qrafik təsvirini vermir. |
| 7 | Proposed approach | 25 s | Yalnız standart BPMN 2.0: təşkilat və CSIRT pool, rollar swimlane, müddətlər timer event, bildirişlər message flow, sübut və hesabatlar data object. |
| 8 | Aim, tasks, and methods | 35 s | Məqsəd: CyberFlow. Beş vəzifəni qısa say. Metodları bir cümlə ilə de. |
| 9 | Expected results and target audience | 30 s | Üç model, qaydalar, ölçülmüş sübut; hədəf ən azı 20 %. İstifadəçilər: CISO, SOC, auditor, CSIRT. Faydalar. |
| 10 | Further development | 25 s | Həll tam deyil: BPMN icra və simulyasiya etmir, oxucu öyrədilməlidir, CACAO ilə uyğunluq birə-bir deyil. Gələcək iş: CACAO-ya çevirmə, simulyasiya, yeni insident növləri. |
| 11–12 | References | 5 s | "The sources are listed in APA 7 format." Son slayddakı AI qeydini göstər. |

Cəmi təxminən 4 dəqiqə 30 saniyə. Müəllim 3 dəqiqə desə: 2-ci slaydı keç, 3 və 4-ü birlikdə
30 saniyəyə de, 6-cı slaydda hər həll üçün bir cümlə de.

## 6. Müəllimin verə biləcəyi suallar

Hər sualın altında əvvəl Azərbaycan dilində izah, sonra ingiliscə deyə biləcəyin qısa cavab var.

**1. Mövzu Latviya üçün niyə aktualdır?**
Çünki NIS2-nin hesabat müddətləri Latviyada 1 sentyabr 2024-dən qanunla məcburidir və CERT.LV-nin
əl ilə emal etdiyi insidentlər bir ildə 28 % artıb.
*"The NIS2 deadlines are binding in Latvia since 1 September 2024 through the National Cybersecurity
Law, and CERT.LV processed 2,982 incidents manually in 2025, 28% more than in 2024."*

**2. Əsas problem bir cümlə ilə nədir?**
*"Incident-handling procedures are still written mostly as prose or vendor-specific code, so they
are ambiguous and hard to verify, share and automate."*

**3. CACAO məhz təhlükəsizlik playbook-ları üçündür. Niyə onu yox, BPMN-i seçirsən?**
CACAO maşın üçündür: JSON-dur, öz qrafik notasiyası yoxdur, sadə playbook yüzlərlə sətirdir. İnsanlar
(menecer, hüquqşünas, auditor) onu oxuya bilmir. BPMN insanların oxuduğu qrafik dildir. Bunlar
rəqib deyil: gələcək işdə BPMN modelini CACAO-ya çevirmək planlaşdırılır.
*"CACAO is machine-readable JSON without a native graphical notation, so people cannot read it
easily. BPMN is the human-readable side. They complement each other: transforming the BPMN models
into CACAO is my further work."*

**4. Niyə UML activity diagram və ya adi flowchart yox?**
BPMN-də ayrı təşkilatlar üçün pool, rollar üçün lane, təşkilatlar arası mesaj üçün message flow və
müddətlər üçün timer event var. Bizim prosedurda əsas şey məhz budur: kim, kimə, hansı müddətdə
xəbər verir. Bundan əlavə mövzu müəllim tərəfindən BPMN 2.0 kimi verilib.
*"BPMN has pools for separate organisations, lanes for roles, message flows between organisations
and timer events for deadlines, which is exactly what an incident-reporting procedure needs."*

**5. Pool ilə swimlane-in fərqi nədir? Sequence flow ilə message flow-un fərqi?**
Pool ayrı iştirakçıdır (təşkilat, CSIRT); lane pool-un içində roldur. Sequence flow (bütöv ox)
yalnız bir pool-un içində gedir; pool-lar arasında yalnız message flow (qırıq ox) olur.
*"A pool is a separate participant; a lane is a role inside a pool. Sequence flows stay inside one
pool; between pools only message flows are allowed."*

**6. CyberFlow nədir? Mövcud məhsuldur?**
Yox. Bu, bizim təklif etdiyimiz "goal system"-in adıdır: metod (modelləşdirmə qaydaları) və model
toplusu. Hələ qurulmayıb; xülasə tədqiqat təklifidir.
*"CyberFlow is the name of my proposed goal system: a modelling method plus a repository of BPMN 2.0
models. It does not exist yet; the summary is a research proposal."*

**7. "Ən azı 20 %" haradan gəlir?**
Bu, ölçülmüş nəticə deyil, eksperiment üçün qoyulmuş hədəfdir (hipotez). Mətndə də "the target is"
yazılıb. Real rəqəm tabletop məşqindən sonra bilinəcək.
*"It is a target for the experiment, not a measured result and not a figure from the literature.
The real value will come from the tabletop exercise."*

**8. Necə yoxlayacaqsan? Verification ilə validation-ın fərqi?**
Verification: model notasiya qaydalarına və qanunun tələblərinə uyğundurmu (ekspert rəyi, yoxlama
siyahısı). Validation: model real işdə kömək edirmi; iki qrup eyni ssenarini biri mətn, biri BPMN
prosedurla keçir, səhvlər və ilk bildirişə qədər vaxt müqayisə olunur.
*"Verification checks the models against the notation and the legal requirements. Validation is a
tabletop exercise: one group uses the prose procedure, another the BPMN model, and I compare
procedural errors and the time to the first notification."*

**9. SecBPMN nədir və niyə onu işlətmirsən?**
SecBPMN biznes prosesinə təhlükəsizlik tələbləri (məxfilik, bütövlük və s.) annotasiya edir. O,
insidentə cavab prosedurunu təsvir etmir və standartın hissəsi deyil, ona görə ArisExpress kimi
standart BPMN alətləri onu tanımır, öz xüsusi aləti lazımdır.
*"SecBPMN annotates business processes with security requirements; it does not describe the response
procedure itself, and it is not part of the standard, so standard BPMN tools such as ArisExpress do
not support it."*

**10. Həllin məhdudiyyətləri nədir?**
5-ci paraqrafdakı üç bənd: BPMN icra və simulyasiya etmir; qrafik modeli oxumaq üçün təlim lazımdır;
CACAO ilə uyğunluq birə-bir deyil.
*"BPMN shows the logic but does not execute or simulate it; readers need training; and the mapping
to CACAO is not one-to-one."*

**11. "Mapping is not one-to-one" nə deməkdir?**
BPMN-in bəzi elementlərinin CACAO-da birbaşa qarşılığı yoxdur və əksinə, ona görə avtomatik çevirmə
üçün əlavə qaydalar lazımdır (Zych et al., 2023).
*"Some BPMN elements have no direct CACAO counterpart and the other way round, so an automatic
transformation needs additional rules."*

**12. Essential və important entities kimlərdir?**
NIS2-nin əlavələrində sadalanan sektorların (enerji, nəqliyyat, bank, səhiyyə, rəqəmsal
infrastruktur və s.) orta və böyük təşkilatları. Essential olanlara nəzarət daha sərtdir.
*"They are the two NIS2 categories of medium-sized and large organisations in the sectors listed in
the annexes of the directive; essential entities are supervised more strictly."*

**13. Bu mövzu sonrakı işlərlə necə bağlıdır?**
PR1 mövzunu və goal system-i müəyyən edir. T5L-də həmin goal system-in CLD-si və BPMN2 modeli
ArisExpress-də çəkilir.
*"PR1 defines the topic and the goal system; in T5L I draw the CLD of this goal system and its
BPMN2 model in ArisExpress."*

**14. AI-dan necə istifadə etmisən?**
Düzünü de: gecikdiyinə görə müəllim tam AI dəstəyinə icazə verib; generativ AI (Claude) mənbə
axtarışı, mətnin hazırlanması və istinadların formatlanması üçün işlədilib; bu, sənədin sonundakı
"Note"-da yazılıb; mətni oxuyub başa düşmüsən və hər rəqəmin mənbəyini göstərə bilirsən.
*"As agreed for the late submission, I used a generative AI tool, Claude, for information
retrieval, drafting and formatting the references; this is declared in the note. I have read the
sources behind each figure and can show where each one comes from."*

## 7. Göndərməzdən əvvəl yoxla

1. `VagifAsgarli-PR1.pdf` faylını aç və başdan sona oxu. Tarix "30 November 2026" yazılıb; başqa
   gün göndərsən, mənə de, tarixi dəyişim.
2. Fayl adı müəllimin tələb etdiyi kimidir: `FirstNameLastName-PR1.pdf` → `VagifAsgarli-PR1.pdf`.
3. PDF-i müəllimin tapşırıqda göstərdiyi e-poçt ünvanına göndər (son tarix: 2 dekabr 2026).
4. Təqdimatı (`.pptx`) da məktuba əlavə et və ya müdafiəyə özünlə gətir; müəllimin PR1 təqdimatını
   nə vaxt dinləyəcəyini ondan soruş.
5. Təqdimatı ən azı iki dəfə saatla ucadan məşq et.
