# Una# Revolucija — Zlatni standard i pravilnik

Ovaj dokument definiše službeni pravilnik koji važi za sve članove tima, za sav kod, podatke i audit procese. Cilj je važiti kao zlatni standard: sve mora biti provereno, tačno, bez greške i bez kompromitovanih rešenja.

## 1. Osnovna pravila

- Sve odluke moraju biti temeljene na proverljivim podacima.
- Svaka tvrdnja mora imati izvor ili dokaz.
- Nema mesta za nagađanje, neproverene procente, ili "dobre pretpostavke" u finalnom rešenju.
- Ako nešto nije provereno, ne može se predstavljati kao istina.
- Komunikacija mora biti jasna, stručna i bez uvreda.

## 2. Standard kvaliteta podataka

- Podaci moraju dolaziti iz validnih izvora: zvaničnih statistika, World Bank, relevantnih akademskih istraživanja ili internog testiranja.
- Svaka tabela i grafikon mora navesti izvor i opseg (godine, zemlja, indikator).
- Ne sme se koristiti podatak koji se ne može reprodukovati.
- Svi proračuni moraju biti numerički proverljivi i jasno dokumentovani.

## 3. Standard kvaliteta koda

- Kod mora biti čist, čitljiv i komentarisano objašnjen.
- Mora postojati validacija ulaza i kontrola izuzetaka tamo gde je potrebno.
- Svaki modul mora imati jasnu svrhu i minimalnu zavisnost.
- Ne sme se preporučivati ili pustiti u produkciju rješenje koje je nedovršeno ili neprovereno.

## 4. Standard sigurnosti i provere

- Svi industrijski i embedded sistemi moraju imati jasno definisanu bezbednosnu logiku:
  - "E-Stop" / "Emergency Stop"
  - fail-safe mehanizmi
  - debouncing za ulaze
  - zaštitu pri radu sa Flash memorijom
- Svaka bezbednosna tvrdnja mora biti potvrđena: dokumentacijom, testom ili standardom.
- Ako postoji industijski rizik, mora postojati očigledno i implementirano rešenje.

## 5. Standard auditnog procesa

- Auditi se sprovode uz pomoć `critic.py` i `backend.py`.
- Svi audit izvještaji moraju biti dostupni i sadržavati:
  - accuracy
  - completeness
  - safety
  - issues
  - verdict
- Ako audit daje `FAIL`, rješenje se ne smatra validnim dok se ne popravi.
- Refiner mora adresirati svaki konkretan problem, ne samo dodavati komentar.

## 6. Pravilo bez kompromisa

- Ako postoji sumnja, važi strože: prvo proveri, pa tek onda prihvati.
- Ne sme se puštati ništa što nije provereno i dokumentovano.
- "Bez greške" u ovom pravilniku znači da se svi koraci mogu rekonstruisati i odbraniti pred tehničkim auditorom.

## 7. Implementacija u praksi

- Uvek koristi lokalne i spoljne testove pre objave.
- Ukloni sve privremene debug poruke i nepotrebni „sranja“ iz finalnog koda.
- U dokumentima i aplikacijama jasno navedi šta je izvor, šta je modelirano, i šta je izračunato.

## 8. Zaključak

Zlatni standard Una# Revolucija je: sve provere, sve istina, sve dokumentovano. Svaki član tima se obavezuje da radi po ovom pravilniku i da ne prihvata ništa manje.
