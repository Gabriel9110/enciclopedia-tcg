# Enciclopedia del TCG: come pubblicarlo e come modificarlo

Il sito è fatto di file di testo. Un programma (`motore/build.py`) li trasforma in pagine web
ogni volta che salvi una modifica, e GitHub le mette online da solo. Non serve un server,
non serve un database, e l'hosting è gratuito.

```
contenuti/   una pagina del sito = un file .md (testo con poche regole di formattazione)
mazzi/       una scheda di mazzo = un file .md
dati/        pagina iniziale (home.yml), formati e famiglie dei mazzi (mazzi.yml), dati delle carte
static/      PDF, copertine, icona del sito
modelli/     file da copiare quando aggiungi una pagina o un mazzo
sito.yml     titolo, indirizzo, testo in fondo alle pagine, elenco dei set
motore/      il generatore, lo stile e lo script (di solito non si toccano)
```

---

## Parte 1 · Mettere il sito online (una volta sola, circa 20 minuti)

### 1. Crea un account GitHub
Vai su <https://github.com/signup> e registrati. Il nome utente comparirà nell'indirizzo
provvisorio del sito (`nomeutente.github.io`), quindi scegline uno presentabile.

### 2. Installa GitHub Desktop
Scaricalo da <https://desktop.github.com>, aprilo e accedi con l'account appena creato.
È il modo più semplice per caricare tutta la cartella in un colpo solo (dal sito di GitHub
si possono caricare al massimo 100 file per volta, e qui sono di più).

### 3. Crea il repository
1. Estrai lo zip in una cartella, per esempio `Documenti/enciclopedia-tcg`.
2. In GitHub Desktop: **File → Add local repository**, scegli la cartella.
   Comparirà l'avviso che non è un repository: clicca **create a repository**,
   lascia il nome `enciclopedia-tcg` e conferma.
3. In basso a sinistra scrivi un messaggio come `Prima versione` e clicca **Commit to main**.
4. Clicca **Publish repository** in alto. Togli la spunta **Keep this code private**:
   con un account gratuito, GitHub Pages funziona solo con repository pubblici.

### 4. Attiva la pubblicazione
1. Apri il repository su github.com (in GitHub Desktop: **Repository → View on GitHub**).
2. Vai in **Settings → Pages**.
3. In **Build and deployment → Source** scegli **GitHub Actions**.
4. Vai nella scheda **Actions**: il lavoro "Pubblica il sito" parte da solo (se non è
   partito, aprilo e clicca **Run workflow**). Dopo un paio di minuti diventa verde.
5. Il sito è online su `https://nomeutente.github.io/enciclopedia-tcg/`.

### 5. Scrivi l'indirizzo nelle impostazioni
Apri `sito.yml` e alla voce `indirizzo` metti l'indirizzo vero del sito, senza barra finale.
Serve alla mappa per Google e alla pagina di errore. Salva e pubblica (vedi Parte 2).

### 6. Facoltativo: un dominio tuo
1. Compra un dominio (per esempio da Cloudflare, Aruba, Register.it, OVH): pochi euro l'anno.
2. Su GitHub: **Settings → Pages → Custom domain**, scrivi il dominio e salva.
3. Dal pannello di chi ti ha venduto il dominio, aggiungi i record DNS che GitHub indica
   nella guida <https://docs.github.com/pages/configuring-a-custom-domain-for-your-github-pages-site>.
   Per `www.tuodominio.it` basta un record **CNAME** verso `nomeutente.github.io`.
4. Quando GitHub mostra il segno verde, spunta **Enforce HTTPS**.
5. Aggiorna `indirizzo` in `sito.yml` con il nuovo dominio.

Il titolo che compare sul sito si cambia in `sito.yml`, alla voce `titolo`.

### 7. Facoltativo: farti trovare su Google
Registra il sito su <https://search.google.com/search-console> e invia la mappa
`https://tuoindirizzo/sitemap.xml`, che il generatore crea da solo.

---

## Parte 2 · Modificare il sito

Ogni modifica salvata nel ramo `main` rimette online il sito in circa due minuti.
Puoi lavorare in due modi.

**Dal browser (comodo per piccole correzioni).** Su github.com apri il file, clicca la
matita (**Edit this file**), modifica, poi **Commit changes**. Fatto.

**Dal computer (comodo per lavori lunghi).** Modifica i file nella cartella con qualsiasi
editor (consiglio Visual Studio Code, gratuito). Poi in GitHub Desktop scrivi un messaggio,
**Commit to main** e **Push origin**.

### Correggere un testo
Le pagine sono in `contenuti/`, divise per volume. Il nome del file contiene l'indirizzo della
pagina: `contenuti/vol4-parte2/04-ex-deoxys.md` è la pagina `/ex-deoxys/`.

Regole di scrittura (Markdown):

| Scrivi | Ottieni |
| --- | --- |
| `## Titolo di sezione` | un titolo |
| `**testo**` | **grassetto** |
| `*testo*` | *corsivo* |
| `- voce` | un elenco puntato |
| `[testo](https://indirizzo)` | un collegamento esterno |
| `[EX Deoxys](#ex-deoxys)` | un collegamento a un'altra pagina del sito |
| una riga vuota | un nuovo paragrafo |

Le tabelle si scrivono con le barre verticali, come quelle già presenti nei file.
Nelle tabelle, i tipi (Erba, Fuoco…) e i pesi (Dominante, Top, Medio…) diventano etichette colorate da soli.

**Anteprime delle carte.** Non devi fare niente: ogni nome di carta in inglese scritto nel
testo diventa un'anteprima. La versione della carta viene scelta in base a `set_carte`
nell'intestazione della pagina. Se un nome comune viene collegato a sproposito, aggiungilo a
`non_collegare` in `sito.yml`.

**La riga `<!-- fine attacco -->`** separa il paragrafo in evidenza all'inizio della pagina dal
resto del testo. Se non c'è, la pagina parte direttamente con il testo.

### Aggiungere una pagina
1. Copia `modelli/nuova-pagina.md` nella cartella giusta di `contenuti/`.
2. Rinominala con un numero davanti: il numero decide l'ordine nell'indice
   (`03-...` viene dopo `02-...`). Puoi usare anche `02b-...` per inserire una pagina in mezzo.
3. Compila l'intestazione tra le due righe `---` e scrivi il testo.

### Titoli per Google
Ogni pagina riceve da sola un titolo pensato per la ricerca, per esempio
«EX Deoxys (2005): carte, mazzi e meta del GCC Pokémon · Storia del GCC».
Per sceglierlo tu, aggiungi nell'intestazione `titolo_seo: ...`; per la frase che compare
sotto il titolo nei risultati, `descrizione: ...` (circa 150 caratteri).

### Aggiungere un volume
1. Crea una cartella in `contenuti/`, per esempio `contenuti/vol5/`.
2. In `dati/home.yml`, sotto `volumi:`, aggiungi un blocco come quelli esistenti
   (numero, nome, titolo, anni, colore, prima pagina).
3. Se il volume ha più parti, aggiungi `parte: 1` (2, 3…) alle pagine e una voce
   `parti_volume_5:` in `dati/home.yml`, come quella del Volume IV.
4. Aggiungi i codici dei nuovi set in fondo a `set_in_ordine` in `sito.yml`
   (per la 4ª generazione: `dp1`, `dp2`, `dp3`, `dp4`, `dp5`, `dp6`, `dp7`, `pl1`…;
   l'elenco completo è su <https://github.com/PokemonTCG/pokemon-tcg-data/tree/master/cards/en>).
   I dati di quelle carte vengono scaricati da soli alla prima pubblicazione.

### Aggiungere un mazzo
1. Copia `modelli/nuovo-mazzo.md` in `mazzi/` con un numero davanti.
2. Compila l'intestazione. `formato` e `famiglia` devono esistere in `dati/mazzi.yml`:
   per una stagione nuova aggiungi lì il formato (nome, periodo, colore, pagina, set_carte).
3. Sotto `## Lista` scrivi una carta per riga: `4 Electabuzz (B 20)`.
4. La stima di vittoria, le varianti della stessa famiglia e i ruoli degli Allenatori
   si calcolano da soli.

### Aggiungere un PDF
1. Metti il PDF in `static/pdf/` e la copertina (JPG, 320×452 circa) in `static/img/`,
   con lo stesso nome.
2. In `dati/home.yml`, sotto `pdf:`, aggiungi file (senza estensione), volume, titolo e pagine.

### Cambiare la pagina iniziale
Tutto è in `dati/home.yml`: apertura, ere del meta, campioni del mondo, costanti, volumi, PDF.

---

## Se qualcosa va storto

- **Il sito non si aggiorna.** Apri la scheda **Actions** su GitHub. Una X rossa indica un errore:
  apri il lavoro e leggi l'ultima parte del passaggio `python motore/build.py`. I messaggi sono
  in italiano e indicano il file e il problema (per esempio un campo mancante nell'intestazione).
- **Avvisi.** Il generatore segnala anche cose che non bloccano la pubblicazione, come una lista
  con più o meno di 60 carte o un collegamento a una pagina che non esiste. Li trovi nello stesso punto.
- **Errore nell'intestazione.** Di solito è un testo con i due punti `:` non messo tra apici.
  Scrivi `in_breve: 'Testo: con i due punti'`, con gli apici.
- **Tornare indietro.** Su GitHub ogni modifica resta nella cronologia (**History** di un file):
  puoi sempre recuperare una versione precedente. In GitHub Desktop: tasto destro sul commit → **Revert**.

## Vedere il sito sul tuo computer prima di pubblicarlo (facoltativo)

Serve Python 3 (<https://www.python.org/downloads/>). Dalla cartella del sito:

```
pip install -r requirements.txt
python motore/build.py
python -m http.server 8000 -d dist
```

Poi apri <http://localhost:8000> nel browser.

## Alternativa a GitHub Pages
Il file `netlify.toml` è già pronto: su <https://app.netlify.com> scegli
**Add new site → Import an existing project**, collega il repository GitHub e conferma.
Netlify legge da solo comando e cartella. Va bene anche Cloudflare Pages con
comando `pip install -r requirements.txt && python motore/build.py` e cartella `dist`.
