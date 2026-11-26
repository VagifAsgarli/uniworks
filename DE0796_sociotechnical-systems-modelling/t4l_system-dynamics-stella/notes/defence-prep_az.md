# T4L: modelin izahı, nümayiş planı və ehtimal olunan suallar

Əvvəlcə [`stella-guide_az.md`](stella-guide_az.md) ilə modeli STELLA-da qur və ya aç. Bu sənəd
modelin **nə olduğunu və niyə belə qurulduğunu** izah edir ki, müdafiədə sərbəst danışa biləsən.

## 1. Əsas anlayışlar (müəllimin nəzəri sualları)

**Stocks and Flows modeli nədir?**
System Dynamics-in kəmiyyət modelidir. **Stock** yığımdır, sistemin müəyyən andakı vəziyyətini
göstərir (məsələn, canavarların sayı). **Flow** stock-u dolduran və ya boşaldan sürətdir (ildə
doğulan balalar). Stock yalnız öz flow-ları ilə dəyişir, ona görə gecikmələri stock-lar yaradır.
Riyazi olaraq bu, diferensial tənlikdir: `Stock(t) = Stock(t − DT) + (inflow − outflow) × DT`.
**Converter** sabit ədəd və ya köməkçi hesablamadır. **Action connector** bir elementin başqasının
tənliyində istifadə olunduğunu göstərir.

**CLD ilə Stocks and Flows modelinin fərqi?**

| | CLD | Stocks and Flows |
|---|---|---|
| Məqsəd | quruluşu anlamaq: nə nəyə, hansı istiqamətdə təsir edir | davranışı hesablamaq: nə qədər və nə vaxt |
| Elementlər | dəyişənlər, "+" və "−" oxlar, R və B dövrələri | stock, flow, converter, action connector |
| Ədədlər | yoxdur | hər elementin qiyməti və ya tənliyi var |
| Zaman | görünmür (yalnız gecikmə işarəsi) | açıqdır: qrafik və cədvəl |
| Nəticə | izah və əsaslandırılmış fikir | əyrilər, cədvəllər, "nə olar, əgər..." təcrübələri |
| Zəif tərəfi | hansı dövrənin güclü olduğunu deyə bilmir | qiymətlər və fərziyyələr tələb edir |

## 2. CLD-dən modelə keçid

CLD-də dövrələri daşıyan dörd dəyişən **stock** oldu, oxlar isə **flow** və **converter**:

| CLD-də | Modeldə |
|---|---|
| Wolves, Deers, Vegetation, Beavers | dörd stock |
| Wolf births (R1), Deers → Wolf births (B1) | flow `wolf births` = Wolves born per deer eaten × predation |
| Wolves → Deers (B1) | flow `predation` = Kill coefficient × Wolves × Deers |
| Pack fights, diseases (B2) | converter `Pack fights and diseases` (flow `wolf deaths`-in içində) |
| Vegetation → Deer births (B3) | converter `Deer capacity` (flow `deer births`-i məhdudlaşdırır) |
| Deers → Vegetation (B3) | flow `browsing` |
| Hunting permits (B4) | slider `Deer hunting rate` |
| Winter severity; Bears, cougars | slider `Winter severity`, converter `Bears and cougars rate` |
| Vegetation → Beavers (R3) | converter-lər `Willow habitat`, `Free habitat` (flow `colony growth`) |
| Beaver ponds → Vegetation (R3) | converter `Beaver ponds effect` (flow `regrowth`) |
| Coyotes, Carcasses, Scavengers | modeldə yoxdur: dörd stock-a geri təsir etmirlər |

## 3. Hər stock-un məntiqi

**Wolves.**
- `wolf births = Wolves born per deer eaten × predation`: canavar nə qədər çox maral ovlasa, o
  qədər çox bala sağ qalır (0.032 bala hər ovlanan marala).
- `wolf deaths = Wolves × (Wolf death rate + Pack fights and diseases + Wolf hunting rate)`: təbii ölüm
  (0.15), sıxlıqdan asılı əlavə ölüm (`Strife coefficient × Wolves`: canavar çox olanda dalaşma və
  xəstəlik artır) və insan ovu (slider, standart 0).

**Deers.**
- `deer births = Deer birth rate × Deers × MAX(0, 1 − Deers / Deer capacity)`: məntiqi (logistik)
  artım. Sürü yemin dözə bildiyi saya (`Deer capacity`) yaxınlaşdıqca artım yavaşıyır.
  `Deer capacity = Grassland capacity + Browse capacity gain × Vegetation / 100`: bitki örtüyü
  yaxşılaşanda tutum artır (25 250 + 8 000-ə qədər).
- `deer deaths = Deers × (Deer death rate × Winter severity + Bears and cougars rate + Deer hunting
  rate)`: qış ölümü (0.04, slider ilə vurulur), ayı və puma (0.02), ovçular (0.05, slider).
- `predation = Kill coefficient × Wolves × Deers`: canavarların ildə ovladığı maral. Əmsal 0.0012:
  17 000 maral olanda bir canavar ildə 0.0012 × 17 000 = 20 maral ovlayır (parkda sayılıb: 18–22).

**Vegetation** (söyüd və ağcaqovağın vəziyyəti, torpağın dözə bildiyinin faizi ilə).
- `regrowth = Vegetation growth rate × Vegetation × MAX(0, 1 − Vegetation/100) × Beaver ponds
  effect`: 100%-ə yaxınlaşdıqca yavaşıyır; qunduz bəndləri suyu qaldıranda sürətlənir
  (`Beaver ponds effect = 1 + 0.3 × Beavers / 30`).
- `browsing = Browsing per 1000 deers × Vegetation × Deers / 1000`: maralların yediyi.

**Beavers** (koloniya sayı).
- `colony growth = Beaver growth rate × Beavers × Free habitat`. `Willow habitat` bitkinin 15%-dən
  yuxarı hissəsidir (hündür söyüd olan çayların payı); `Free habitat = Willow habitat − Beavers /
  Beaver capacity` hələ tutulmamış payıdır.
- `colony loss = Beavers × Beaver loss rate` (ildə 5%).

## 4. Qiymətləri haradan götürmüşəm ("own initial values")

- **31 canavar**: 1995–1996-da buraxılan real say.
- **17 000 maral**: 1995-dəki sayım.
- **1 qunduz koloniyası**: 1996-da şimal otlağında tapılan say.
- **Vegetation 20%**: öz fərziyyəm (güclü otarılmış).
- **Qalan sürətlər**: öz qiymətlərimdir. İki şərtlə seçmişəm: (a) canavarsız model 1995-ci il
  vəziyyətində dayanır (17 000 maral, 20%, 1 koloniya); (b) 31 canavarla baza gedişi parkdakı
  sayımlara oxşayır.

Baza gedişi ilə sayımların müqayisəsi:

| | Modeldə | Parkda sayılıb |
|---|---|---|
| Canavarların zirvəsi | 167 (2002) | 174 (2003) |
| Canavarlar uzun müddətdə | 90–105 | 83–123 (2009-dan bəri) |
| Maral, 2010 | 6 003 | 6 070 |
| Maral, 2025 | 7 279 | 7 226 |
| Qunduz koloniyası, 2015 | 18.7 | 18 |

## 5. Təcrübələrin izahı

| Təcrübə | Nə dəyişdi | Nə oldu və niyə |
|---|---|---|
| **E1 baza** | heç nə | Canavar sürətlə artır (R1), 2002-də 167. Ovlanma doğumu üstələyir, maral 2010-da 6 000-ə düşür (B1). Maral azalınca canavar da azalır (B1, B2). Sonra hər ikisi sönən dalğalarla 102 canavar və 7 000 marala gəlir. Bitki 20%-dən 72%-ə, qunduz 1-dən 19 koloniyaya qalxır, təxminən 10 il gecikmə ilə (R3) |
| **E2 canavarsız** | Wolves released = 0 | 50 il heç nə dəyişmir: 17 000 maral, 21% bitki, 1 koloniya. Bu, 1995-dən əvvəlki park: stabil, amma kasıb vəziyyət |
| **E3 maral ovu yox** | Deer hunting rate = 0 | Maral əvvəl çox qalır, canavar buna cavab verir (zirvə 204, son 133). Maral cəmi 15% çox olur (8 090): ovçuların götürmədiyini canavar götürür |
| **E4 canavar ovlanır** | Wolf hunting rate = 0.15 | Canavar 74-də qalır, maral 10 073 (43% çox), bitki 58%, qunduz 14.6. İnsanın canavar haqqında qərarı söyüdə və qunduza çatır |
| **E5 sərt qış** | Winter severity = 2 | Maral 6 281, canavar 77 (yem az), bitki 75% və qunduz 20.5 (ən yüksək). Qış ovlanmanın bir hissəsini əvəz edir |
| **E6 100 canavar** | Wolves released = 100 | Zirvə daha yüksək və tez (191, 1999), maral daha dərin düşür (5 734), amma son vəziyyət E1 ilə eynidir. Tarazlıq başlanğıc saydan asılı deyil: bu, stabillik deməkdir |

## 6. Nəticələr (resursların perspektivi)

1. **Wolves**: özləri və ovları ilə məhdudlaşır, uzun müddətdə 100 ətrafı. Ən böyük risk insan
   ovudur.
2. **Deers**: kiçik, amma sabit sürü, təxminən 7 000 (əvvəlki 17 000-in 41%-i). Çökmür.
3. **Vegetation**: ən yaxşı perspektiv, amma yavaş: 20 ildə 20%-dən 72%-ə, yalnız canavar olanda.
4. **Beavers**: 1-dən 19 koloniyaya, marallar azalandan təxminən 10 il sonra.
5. **Stabillik**: bütün gedişlər bir tarazlığa gəlir; dalğalar B1-dəki gecikmədən yaranır və
   sönür. Canavarsız sistem ikinci, kasıb vəziyyətdə dayanır.
6. **Məhdudiyyət**: model sadədir, sürətlər mənimdir. Reallıqda maralın azalmasında ovçular,
   qışlar, quraqlıq və ayılar da rol oynayıb. Model istiqaməti və gecikməni göstərir, proqnoz
   vermir.

## 7. STELLA-da canlı nümayiş (3–4 dəqiqə)

1. **MODEL layer**: "Dörd stock: Wolves, Deers, Vegetation, Beavers. Borular flow-lardır, dairələr
   converter-lər, nazik oxlar action connector-lər. `predation` flow-u Deers-dən çıxır və
   `wolf births`-ə bağlanır: bu, CLD-dəki B1 dövrəsidir."
2. **Interface layer**, **Run**: "31 canavarla baza gedişi. Canavar qalxır, maral düşür, sonra
   hər ikisi tarazlaşır."
3. Slider `Wolves released` = 0, **Run**: "Canavarsız heç nə dəyişmir."
4. **Restore**, slider `Wolf hunting rate` = 0.15, **Run**: "Canavar ovlananda maral çox, bitki
   və qunduz az olur."
5. **Restore**, slider `Winter severity` = 2, **Run**: "Sərt qışda maral və canavar az, bitki çox."
6. **Table**: "Əyrilərin arxasındakı ədədlər."

## 8. Ehtimal olunan suallar və qısa cavablar

**1. Niyə məhz bu dörd stock?**
CLD-də dövrələri daşıyan və yığılan kəmiyyətlər bunlardır. Coyotes və Scavengers dövrə
bağlamır, ona görə modelə salmamışam.

**2. Stock ilə converter-in fərqi nədir?**
Stock yığır və yaddaşı var (dünənki qiyməti bu günə təsir edir). Converter hər addımda yenidən
hesablanır, yaddaşı yoxdur.

**3. DT nədir, niyə 0.25?**
Hesablama addımı. 0.25 il, yəni ildə dörd addım. Kiçik DT daha dəqiqdir; 0.25 bu model üçün
kifayətdir: DT-ni 0.125 edəndə canavar zirvəsi 167 əvəzinə 165 olur, son vəziyyət dəyişmir.

**4. Hansı inteqrasiya üsulu?**
Euler: `Stock(t) = Stock(t − DT) + (inflow − outflow) × DT`. STELLA-nın standart üsuludur.

**5. `predation` niyə Wolves × Deers hasili ilə verilib?**
Ovlanma həm canavarın, həm maralın sayından asılıdır: canavar çoxdursa çox ovlanır, maral
çoxdursa hər canavar daha asan ov tapır. Bu, klassik yırtıcı–ov (Lotka–Volterra) quruluşudur.

**6. MAX(0, ...) nə üçündür?**
Mötərizədəki ifadə mənfi ola bilər (məsələn, maral tutumdan çox olanda). MAX onu sıfırda
saxlayır ki, doğum mənfi olmasın.

**7. Model reallığa uyğundurmu?**
Əsas rəqəmlərə oxşayır (canavar zirvəsi, maral 2010 və 2025, qunduz 2015), amma sadələşdirilib.
Sürətlər mənim seçimimdir, ölçülmüş qiymətlər deyil. Protokolda "Limits" bəndində yazmışam.

**8. Niyə dalğalanma var?**
B1 dövrəsində gecikmə var: canavar maralın sayına dərhal yox, bir neçə ildən sonra cavab verir.
Gecikməli balanced dövrə sönən dalğa verir.

**9. Slider-lər nəyi göstərir?**
İnsanın və təbiətin təsirini: neçə canavar buraxılır, canavar və maral nə qədər ovlanır, qış
nə qədər sərtdir. Hər biri dörd stock-un son vəziyyətini dəyişir.

**10. Button-lar nə edir?**
Run modeli işlədir, Stop dayandırır, Restore slider-ləri başlanğıc vəziyyətə qaytarır.

**11. E1 və E6 niyə eyni yerdə bitir?**
Tarazlıq nöqtəsi başlanğıc saydan yox, sürətlərdən asılıdır. Bu, sistemin stabil olduğunu
göstərir.

**12. Canavarsız niyə heç nə dəyişmir?**
Başlanğıc qiymətləri elə seçmişəm ki, canavarsız sistem tarazlıqda olsun (doğum = ölüm + ov).
Bu, 1995-dən əvvəlki parkı təsvir edir.

**13. Modeli necə yoxlamısan?**
Üç yolla: (1) canavarsız gediş tarazlıqda qalır; (2) baza gedişi parkdakı sayımlara oxşayır;
(3) STELLA cədvəlindəki ədədlər eyni tənliklərin ayrıca hesablaması ilə üst-üstə düşür.

**14. Modeli nə ilə hazırlamısan?**
Müəllimin icazəsi ilə süni intellektin köməyi ilə layihələndirilib və yoxlanılıb (protokolun
sonundakı qeyd). Model STELLA-da qurulub və nümayiş STELLA-da edilir.

**15. Modeli necə yaxşılaşdırmaq olar?**
Bizon və quraqlıq əlavə etmək, qışı təsadüfi etmək, ov sürətini maralın sayından asılı etmək
(B4 dövrəsini tam bağlamaq), çay hidrologiyasını nəzərə almaq.
