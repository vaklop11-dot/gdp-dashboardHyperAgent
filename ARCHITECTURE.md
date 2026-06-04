# Una# Revolucija v2.1 — Mehanizam Samokritike (Đavolji Advokat)

Ovaj dokument opisuje arhitekturu strogog audita unutar troagentnog sistema Una# Revolucija, koji koristi `Executor`, `Critic` i `Refiner`.

## 1. Uloge u sistemu

- `Executor` generiše rješenje ili kod za određeni zadatak.
- `Critic` preuzima ulogu Đavoljeg advokata: analizira rješenje, traži propuste i ocjenjuje kvalitet.
- `Refiner` prima povratne informacije i pokušava poboljšati rješenje.

## 2. Feedback loop

Tok podataka je zatvorena petlja:
1. `Executor` generiše početni kod.
2. `Critic` evaluaše kod prema tačnosti, potpunosti i sigurnosti.
3. Ako je presuda `FAIL`, `Refiner` prilagođava kod.
4. Ciklus se ponavlja do `MAX_ITERATIONS` puta.

## 3. Kritične metrike

`Đavolji advokat` procjenjuje:
- **Accuracy (Tačnost):** definisano otkrivanjem hardverskih i logičkih grešaka.
- **Completeness (Kompletnost):** otkriva neprovjerene tvrdnje, nedostatke u dokumentaciji i izvore.
- **Safety (Sigurnost):** provjerava zaštitu kao E-Stop, fail-safe, i sigurnosne mehanizme za industrijska okruženja.

## 4. Konfiguracija

U `config.py` su definirani pragovi:
- `THRESHOLD_ACCURACY = 0.85`
- `THRESHOLD_COMPLETENESS = 0.80`
- `THRESHOLD_SAFETY = 0.90`
- `MAX_ITERATIONS = 3`

Takođe je tu sistemski prompt koji diktira da `Critic` vraća isključivo čist JSON sa poljima `accuracy`, `completeness`, `safety`, `issues` i `verdict`.

## 5. Pravilnik evaluacije

U `critic.py` su implementirana pravila:
1. Nedostatak hardverskog debouncinga za GPIO ulaze u embedded/CNC kodu.
2. Odsustvo ring-buffer logike prilikom intenzivnog SPI Flash upisivanja.
3. Nedostatak egzaktnih izvora ili benchmark mjerenja za energetske procjene.

Ako se pojavljuje fraza `NEMAM POTVRDU`, to se tretira kao ozbiljan problem koji zahtijeva dodatnu provjeru.

## 6. Orkestracija

`backend.py` implementira pipeline koji:
- vrši inicijalnu evaluaciju kod `Critic`-om,
- ukoliko je `FAIL`, prosljeđuje izvještaj `Refiner`-u,
- ponavlja do `MAX_ITERATIONS`.

Ako čak i nakon svih iteracija presuda ostane `FAIL`, sistem vraća poslednju `Critic` presudu.

## 7. Fake refiner

`refiner.py` sadrži prostu implementaciju koja kod obogaćuje komentarima `// ISSUE: ...` kako bi se trend povratne informacije zadržao u kodu.

## 8. Korištenje

Da pokreneš audit pipeline lokalno:

```bash
python backend.py
```

Ili u sopstvenoj aplikaciji:

```python
from backend import AuditPipeline
pipeline = AuditPipeline()
result = pipeline.evaluate(code, persona="critic", prompt="Una# Revolucija Edge AI")
```
