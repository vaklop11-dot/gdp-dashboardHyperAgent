# Una# Industry CNC Controller

## Project metadata

- **Author:** Nermin
- **Project:** Industry Development v2.1
- **Phase:** Beta
- **Spec:** ESP32-S3 / MCPWM / TMP117 / Dual-chip SPI / E-stop NC

## Objective

Ovaj dokument opisuje finalne specifikacije za industrijski CNC kontroler koji treba da se razvije unutar Una# HyperAgent okvira.

## Ključne karakteristike

- Kontrola pokreta i brzine pomoću ESP32-S3 i MCPWM
- Precizno mjerenje temperature sa TMP117 senzorem
- Dual-chip SPI arhitektura za separation of concerns između upravljačkog i sigurnosnog sloja
- NC (normally closed) E-stop krug sa hardverskim fail-safe mehanizmom
- Integrisana sigurnosna logika: detekcija pregrevanja, detekcija prekida napajanja, validacija SPI prijenosa

## Preporučeni moduli

- `ESP32-S3` kao glavni upravljač
- `MCPWM` za generisanje preciznih PWM signala za osovinske motore
- `TMP117` za visokom preciznu temperaturu rada
- `Dual-chip SPI` za odvajanje sigurnosnih i funkcionalnih zadataka
- `E-stop NC` kao primarni sigurnosni prekid

## Povezivanje sa Una# HyperAgentom

Ovaj spec se može koristiti kao testni scenario za HyperAgent generiranje i audit:

- zadatak za `Analyzer` i `Planner`
- sigurno kodiranje i hardverski dizajn za `Executor`
- automatski audit za `Devil's Advocate`

## Napomena

Ovo je beta specifikacija. Završni inženjering i provjere se moraju izvršiti kroz proces Verifikacije, Validacije i Anomaly Logging.
