# T4L: Yellowstone modelini STELLA-da necə qurmalı, işlətməli və şəkillərini çəkməli

Bu təlimat iki yol üçün yazılıb. Müəllim köhnə STELLA ilə işləyir (tapşırıqda "STM format", öz
modeli `.STM` faylıdır), ona görə **A yolu əsasdır**; B yolu yalnız 9.0.4 tapılmasa:

| Səndə olan proqram | Yol | Vaxt |
|---|---|---|
| **STELLA 9.0.4** (müəllimin slaydlarındakı köhnə versiya, fayl `.STM`) | **A yolu**: modeli əl ilə qurursan | 1,5–2 saat |
| **Stella Architect** (yeni versiya, sınaq lisenziyası, fayl `.stmx`) | **B yolu**: hazır faylı açırsan, yalnız Interface qatını qurursan | 30–40 dəqiqə |

Hər iki yolda model eynidir: 4 stock, 9 flow, 28 converter, 41 connector. Bütün tənliklərin
tam siyahısı [`../outputs/model/model-specification.md`](../outputs/model/model-specification.md)
faylındadır. Modelin MODEL qatında necə görünməli olduğu
[`../outputs/model/model-layer_expected.png`](../outputs/model/model-layer_expected.png) şəklindədir
(bu şəkli mən çəkmişəm, protokola qoyulmur; protokola yalnız STELLA-nın öz ekran şəkli qoyulur).

Müəllimin terminləri: **Stock**, **Flow**, **Converter**, **Action connector**, **MODEL layer**,
**Interface layer**, **Equation**. Müdafiədə bu sözləri işlət.

---

## A yolu: STELLA 9.0.4-də əl ilə qurmaq

### A1. Hazırlıq

1. STELLA-nı aç. Sol kənardakı yuxarı/aşağı ox düymələri ilə qatlar arasında keçilir:
   **Interface**, **Map**, **Model**, **Equation**. **Model** qatına keç.
2. Sol kənarda qlobus (🌐) və ya **χ²** işarəli düymə var. Onu bas ki, **χ²** görünsün. Bu,
   "modelləşdirmə rejimi"dir: tənliyi yazılmamış elementlərin üstündə **?** görünəcək.
3. Menyu **Run > Run Specs...**: `From: 1995`, `To: 2045`, `DT: 0.25`, `Unit of time: Years`,
   `Integration Method: Euler's Method`. **OK**.

### A2. Dörd stock və onların flow-ları

Alətlər zolağında dörd əsas alət var: düzbucaqlı (**Stock**), boru (**Flow**), dairə (**Converter**),
ox (**Action connector**). Element qoymaq üçün aləti seç, səhifədə bas və adını yaz.

Flow çəkmək qaydası: Flow alətini seç, boş yerdə basıb saxla və stock-un **içinə** qədər sürüklə
(giriş axını, inflow); çıxış axını (outflow) üçün stock-un içindən başla və boş yerə sürüklə. Boş
ucda bulud görünür.

Əvvəlcə dörd stock-u `model-layer_expected.png` şəklindəki kimi yerləşdir (Wolves yuxarı solda,
Deers sağda ortada, Beavers aşağı solda, Vegetation aşağı sağda), sonra flow-ları çək:

| Stock | Giriş flow (inflow) | Çıxış flow-lar (outflow) |
|---|---|---|
| `Wolves` | `wolf births` | `wolf deaths` |
| `Deers` | `deer births` | `deer deaths`, `predation` |
| `Vegetation` | `regrowth` | `browsing` |
| `Beavers` | `colony growth` | `colony loss` |

`Deers` stock-unun üç flow-u var: `deer births` soldan girir, `deer deaths` sağa çıxır,
`predation` yuxarıya çıxır.

### A3. Converter-lər

Converter alətini seç və aşağıdakı 28 dairəni qoy. Sabit ədədi olanlara dərhal iki dəfə basıb
(double-click) qiymətini yaz və **OK** bas.

| Converter | Qiymət | | Converter | Qiymət |
|---|---|---|---|---|
| `Wolves released` | 31 | | `Deer hunting rate` | 0.05 |
| `Wolves born per deer eaten` | 0.032 | | `Initial vegetation` | 20 |
| `Wolf death rate` | 0.15 | | `Vegetation growth rate` | 0.35 |
| `Strife coefficient` | 0.0012 | | `Browsing per 1000 deers` | 0.0165 |
| `Wolf hunting rate` | 0 | | `Initial beaver colonies` | 1 |
| `Initial deers` | 17000 | | `Beaver growth rate` | 2 |
| `Kill coefficient` | 0.0012 | | `Willow threshold` | 15 |
| `Deer birth rate` | 0.3 | | `Beaver capacity` | 30 |
| `Grassland capacity` | 25250 | | `Beaver loss rate` | 0.05 |
| `Browse capacity gain` | 8000 | | `Beaver effect` | 0.3 |
| `Deer death rate` | 0.04 | | | |
| `Winter severity` | 1 | | | |
| `Bears and cougars rate` | 0.02 | | | |

Tənliyi olan beş converter (qiymətini hələ yazma, əvvəlcə connector-ları çək):
`Fights and diseases`, `Deer capacity`, `Willow habitat`, `Free habitat`, `Beaver ponds effect`.

### A4. Action connector-lər (41 ədəd)

Connector alətini seç, mənbə elementin üstündə basıb saxla və hədəf elementə sürüklə. Hədəf flow
olanda oxu flow-un ortasındakı dairəyə (klapana) apar. Siyahı "haradan → haraya":

**Wolves bölməsi**
- `Wolves born per deer eaten` → `wolf births`
- `predation` → `wolf births`
- `Wolves` → `wolf deaths`
- `Wolf death rate` → `wolf deaths`
- `Fights and diseases` → `wolf deaths`
- `Wolf hunting rate` → `wolf deaths`
- `Strife coefficient` → `Fights and diseases`
- `Wolves` → `Fights and diseases`

**Deers bölməsi**
- `Deer birth rate` → `deer births`
- `Deers` → `deer births`
- `Deer capacity` → `deer births`
- `Deers` → `deer deaths`
- `Deer death rate` → `deer deaths`
- `Winter severity` → `deer deaths`
- `Bears and cougars rate` → `deer deaths`
- `Deer hunting rate` → `deer deaths`
- `Kill coefficient` → `predation`
- `Wolves` → `predation`
- `Deers` → `predation`
- `Grassland capacity` → `Deer capacity`
- `Browse capacity gain` → `Deer capacity`
- `Vegetation` → `Deer capacity`

**Vegetation bölməsi**
- `Vegetation growth rate` → `regrowth`
- `Vegetation` → `regrowth`
- `Beaver ponds effect` → `regrowth`
- `Browsing per 1000 deers` → `browsing`
- `Vegetation` → `browsing`
- `Deers` → `browsing`

**Beavers bölməsi**
- `Beaver growth rate` → `colony growth`
- `Beavers` → `colony growth`
- `Free habitat` → `colony growth`
- `Beavers` → `colony loss`
- `Beaver loss rate` → `colony loss`
- `Vegetation` → `Willow habitat`
- `Willow threshold` → `Willow habitat`
- `Willow habitat` → `Free habitat`
- `Beavers` → `Free habitat`
- `Beaver capacity` → `Free habitat`
- `Beaver effect` → `Beaver ponds effect`
- `Beavers` → `Beaver ponds effect`
- `Beaver capacity` → `Beaver ponds effect`

Qeyd: `Wolves released`, `Initial deers`, `Initial vegetation`, `Initial beaver colonies`
converter-lərindən stock-lara connector **çəkilmir** (STELLA stock-a connector qəbul etmir). Onlar
stock-un başlanğıc qiymətində adı ilə yazılır (A5-ə bax).

### A5. Tənliklər

Hər elementə iki dəfə bas. Pəncərənin yuxarısındakı **Required Inputs** siyahısında ona
connector ilə bağlanmış elementlər görünür; adın üstünə basanda tənliyə düşür. Tənliyi aşağıdakı
kimi yaz (boşluq əvəzinə alt xətt `_` avtomatik qoyulur).

**Stock-ların başlanğıc qiyməti** (stock-a iki dəfə bas, `INITIAL(...) =` xanasına yaz;
**Non-negative** işarəsi qoyulu qalsın):

| Stock | Başlanğıc qiymət |
|---|---|
| `Wolves` | `Wolves_released` |
| `Deers` | `Initial_deers` |
| `Vegetation` | `Initial_vegetation` |
| `Beavers` | `Initial_beaver_colonies` |

Əgər STELLA 9 stock-un başlanğıc xanasında converter adını qəbul etməsə (siyahıda görünməsə),
ədədin özünü yaz: 31, 17000, 20, 1. Bu halda `Wolves released` slider-i əvəzinə Interface
qatında `Wolves` stock-una **Knob** bağlayacaqsan (A7-də qeyd var).

**Flow-lar** (hamısı **UNIFLOW** qalsın):

| Flow | Tənlik |
|---|---|
| `wolf births` | `Wolves_born_per_deer_eaten*predation` |
| `wolf deaths` | `Wolves*(Wolf_death_rate+Fights_and_diseases+Wolf_hunting_rate)` |
| `deer births` | `Deer_birth_rate*Deers*MAX(0, 1-Deers/Deer_capacity)` |
| `deer deaths` | `Deers*(Deer_death_rate*Winter_severity+Bears_and_cougars_rate+Deer_hunting_rate)` |
| `predation` | `Kill_coefficient*Wolves*Deers` |
| `regrowth` | `Vegetation_growth_rate*Vegetation*MAX(0, 1-Vegetation/100)*Beaver_ponds_effect` |
| `browsing` | `Browsing_per_1000_deers*Vegetation*Deers/1000` |
| `colony growth` | `Beaver_growth_rate*Beavers*Free_habitat` |
| `colony loss` | `Beavers*Beaver_loss_rate` |

**Tənlikli converter-lər:**

| Converter | Tənlik |
|---|---|
| `Fights and diseases` | `Strife_coefficient*Wolves` |
| `Deer capacity` | `Grassland_capacity+Browse_capacity_gain*Vegetation/100` |
| `Willow habitat` | `MAX(0, (Vegetation-Willow_threshold)/(100-Willow_threshold))` |
| `Free habitat` | `MAX(0, Willow_habitat-Beavers/Beaver_capacity)` |
| `Beaver ponds effect` | `1+Beaver_effect*Beavers/Beaver_capacity` |

Hamısını yazandan sonra heç bir elementin üstündə **?** qalmamalıdır. Qalıbsa, həmin elementin
connector-u və ya tənliyi çatmır.

### A6. Qrafik və cədvəl (Model qatında yoxlama üçün)

1. Alətlər zolağından **Graph Pad** seç, boş yerə qoy, iki dəfə bas. Sol siyahıdan `Wolves` və
   `Deers` seçib **>>** ilə sağa keçir. Title: `Wolves and Deers`. **OK**.
2. **Table Pad** qoy, iki dəfə bas, `Wolves`, `Deers`, `Vegetation`, `Beavers` seç.
   `Report interval: 5`. **OK**.
3. **Run > Run** (Ctrl+R). Cədvəli C bölməsindəki rəqəmlərlə tutuşdur.

### A7. Interface qatı (müəllimin tələbi: slider və button)

Sol kənardakı yuxarı oxla **Interface** qatına keç.

1. **Slider** alətini seç, səhifəyə dörd slider qoy. Hər birinə iki dəfə bas, siyahıdan
   converter-i seç və hədləri yaz:

   | Slider | Min | Max | Increment (addım) |
   |---|---|---|---|
   | `Wolves released` | 0 | 100 | 1 |
   | `Wolf hunting rate` | 0 | 0.3 | 0.01 |
   | `Deer hunting rate` | 0 | 0.2 | 0.01 |
   | `Winter severity` | 0.5 | 3 | 0.1 |

   (A5-də stock-a ədəd yazmalı oldunsa: `Wolves released` slider-i əvəzinə **Knob** alətini qoy
   və `Wolves` stock-una bağla, 0–100.)
2. **Button** alətini seç, üç düymə qoy. Hər birinə iki dəfə bas, **Menu** seçimini et və
   əməliyyatı seç:
   - `Run` (Run menyusu: Run)
   - `Stop` (Run menyusu: Stop)
   - `Restore` (Restore menyusu: All Devices, yəni bütün slider-ləri başlanğıc vəziyyətə qaytarır)
3. **Graph Pad** qoy: `Wolves`, `Deers`. İkinci Graph Pad: `Vegetation`, `Beavers`.
4. İstəsən dörd **Numeric Display** qoy (`Wolves`, `Deers`, `Vegetation`, `Beavers`): son
   qiymətləri ədədlə göstərir.
5. **Text Box** ilə başlıq yaz: `Yellowstone: Wolves, Deers, Vegetation and Beavers`.

### A8. Saxlamaq

**File > Save As...**, ad: `VagifAsgarli-T4L.STM`. Müəllimin istədiyi "STM format" budur.

---

## B yolu: Stella Architect-də hazır faylı açmaq

### B1. Faylı aç

1. Repodan `t4l_system-dynamics-stella/outputs/model/Yellowstone_with-interface.stmx` faylını
   kompüterinə yüklə.
2. Stella Architect-i aç, **File > Open** ilə faylı seç.
3. Yoxla: MODEL görünüşündə diaqram `model-layer_expected.png` şəklinə oxşayır, heç bir
   elementdə **?** yoxdur, aşağıda iki qrafik və bir cədvəl var.
4. Pəncərənin yuxarı sol küncündəki düymə ilə **Interface** görünüşünə keç. Orada dörd slider,
   üç düymə (Run, Stop, Restore all) və iki qrafik görünməlidir.

Əgər Interface boşdursa və ya fayl açılmırsa: `Yellowstone.stmx` faylını aç (burada yalnız
model var) və Interface-i B2 ilə özün qur. Əgər o da açılmasa, A yolundakı kimi əl ilə qur və
mənə xəta mesajının şəklini göndər.

Kiçik kosmetik düzəliş: əgər `Deers` və ya `Vegetation` adı borunun və ya oxun üstünə düşübsə,
adı mausla tutub boş yerə çək.

### B2. Interface-i əl ilə qurmaq (lazım olsa)

1. Interface görünüşündə alətlər zolağından **Slider** seç, səhifəyə qoy, sağdakı paneldə
   dəyişəni seç (`Wolves released`), Min 0, Max 100. Eyni qayda ilə: `Wolf hunting rate`
   (0–0.3), `Deer hunting rate` (0–0.2), `Winter severity` (0.5–3).
2. **Button** qoy, paneldə Action: **Run**; ikinci düymə: **Stop**; üçüncü: **Restore All
   Devices**. Düymələrin üstünə `Run`, `Stop`, `Restore` yaz.
3. **Graph** qoy: `Wolves`, `Deers`. İkinci Graph: `Vegetation`, `Beavers`.
4. **Text Box**: `Yellowstone: Wolves, Deers, Vegetation and Beavers`.

### B3. Saxlamaq

**File > Save As**, ad: `VagifAsgarli-T4L.stmx`. Stella Architect köhnə `.STM` formatında
saxlamır; bunu müəllimə məktubda bir cümlə ilə yazırıq (README-də mətn var).

---

## C. Rəqəmlərin yoxlanması (hər iki yol üçün)

Standart qiymətlərlə (31 wolves) **Run** edəndən sonra cədvəl bu rəqəmləri göstərməlidir
(yuvarlaqlaşdırma fərqi ola bilər, ±1):

| Year | Wolves | Deers | Vegetation | Beavers |
|---|---|---|---|---|
| 1995 | 31.0 | 17000 | 20.0 | 1.0 |
| 2000 | 145.3 | 11734 | 23.7 | 1.1 |
| 2005 | 150.6 | 7030 | 38.7 | 2.8 |
| 2010 | 110.3 | 6003 | 59.3 | 12.2 |
| 2015 | 92.1 | 6315 | 71.2 | 18.7 |
| 2020 | 90.0 | 6912 | 73.2 | 19.8 |
| 2025 | 95.7 | 7279 | 72.1 | 19.5 |
| 2030 | 101.8 | 7300 | 71.3 | 19.1 |
| 2035 | 103.9 | 7160 | 71.4 | 19.1 |
| 2040 | 103.0 | 7049 | 71.9 | 19.3 |
| 2045 | 101.6 | 7022 | 72.2 | 19.4 |

Rəqəmlər fərqlidirsə: (1) Run Specs-də DT 0.25 və Euler olduğunu yoxla; (2) fərqlənən stock-un
flow tənliklərini A5 cədvəli ilə hərf-hərf tutuşdur; (3) düzəlməsə, Equation qatının şəklini
mənə göndər.

## D. Təcrübələr və ekran şəkilləri

Hər təcrübədən əvvəl **Restore** düyməsini bas, slider-i dəyiş, **Run** bas, sonra Interface
qatının şəklini çək (slider-lər və qrafiklər bir şəkildə görünsün).

| № | Təcrübə | Slider dəyişikliyi | 2045-ci ildə gözlənilən nəticə (Wolves / Deers / Vegetation / Beavers) |
|---|---|---|---|
| E1 | Baza: 31 canavar buraxılır | heç nə | 102 / 7022 / 72 / 19.4 |
| E2 | Canavar yoxdur | `Wolves released` = 0 | 0 / 17036 / 21 / 1.2 |
| E3 | Maral ovu yoxdur | `Deer hunting rate` = 0 | 133 / 8090 / 68 / 17.9 |
| E4 | Canavarlar ovlanır | `Wolf hunting rate` = 0.15 | 74 / 10073 / 58 / 14.6 |
| E5 | Sərt qışlar | `Winter severity` = 2 | 77 / 6281 / 75 / 20.5 |
| E6 | 100 canavar buraxılır | `Wolves released` = 100 | 101 / 7025 / 72 / 19.5 |

Çəkiləcək şəkillər (PNG), adları dəqiq belə olsun və hamısını mənə göndər:

| Fayl adı | Nəyin şəkli |
|---|---|
| `01_model-layer.png` | MODEL qatı: bütün diaqram bir ekranda (lazım olsa kiçilt, zoom out) |
| `02_interface_E1.png` | Interface qatı, E1-dən sonra |
| `03_table_E1.png` | Cədvəl (Table), E1-dən sonra, 1995–2045 sətirləri görünsün |
| `04_interface_E2.png` | Interface qatı, E2-dən sonra |
| `05_interface_E3.png` | Interface qatı, E3-dən sonra |
| `06_interface_E4.png` | Interface qatı, E4-dən sonra |
| `07_interface_E5.png` | Interface qatı, E5-dən sonra |
| `08_interface_E6.png` | Interface qatı, E6-dan sonra |
| `09_equations.png` | Equation qatı (tənliklərin siyahısı; bir neçə şəkil ola bilər) |

Şəkilləri alan kimi protokolu və təqdimatı son variantda yığıram (qaralamada onların yerində
qırmızı çərçivəli qeyd var).

## E. Müəllimə göndəriləcək fayllar (T4L)

1. Protokol: `VagifAsgarli-T4L.pdf` (çap edib imzalayırsan, skan edib PDF kimi göndərirsən və ya
   PDF-ə imza şəklini qoyursan).
2. Model: `VagifAsgarli-T4L.STM` (9.0.4) və ya `VagifAsgarli-T4L.stmx` (Stella Architect).
3. Təqdimat: `VagifAsgarli-T4L-presentation.pptx`.

Ünvan: `egils.ginters@rtu.lv`. Müdafiədə modeli öz kompüterində STELLA-da açıb işlədirsən:
slider-i dəyişirsən, **Run** basırsan, qrafiki izah edirsən.

## F. Tez-tez çıxan problemlər

| Problem | Həll |
|---|---|
| Elementin üstündə **?** qalır | Tənlik yazılmayıb və ya Required Inputs-dakı bir giriş tənlikdə istifadə olunmayıb |
| "Circular connection" xətası | Connector-u səhv istiqamətdə çəkmisən; A4 siyahısı ilə yoxla |
| Flow stock-a yapışmır (bulud qalır) | Flow-u silib yenidən çək, ucunu stock-un içində burax (stock rəngi dəyişəndə) |
| Qrafik düz xətt göstərir | `Wolves released` = 0 qalıb və ya Run Specs 1995–2045 deyil |
| Slider siyahısında converter yoxdur | Slider yalnız sabit ədədli converter-ə bağlanır; tənlikli converter-ə olmaz |
| Qiymətlər mənfiyə düşür | Stock-da Non-negative işarəsi yoxdur və ya flow BIFLOW edilib |
