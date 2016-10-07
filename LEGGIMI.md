# Convertitore di orario lezioni PoliMi in formato iCal

![Screenshot](screenshot.png "The scraper's main window")

## Utilizzo

```shell
$ python2 src/scraper.py
```

Il programma è in inglese e appare come sopra perché, come anche tu ben sai, il Poli fa tanto male alla salute, ma al tempo libero ne fa ancora di più. È già tanto se ho fatto questo programma, che se son fortunato dovrò usare soltanto 4 volte. Anche se molto probabilmente l'ho fatto perché (in)consciamente so di averne bisogno per più a lungo :'(

Utilizza il browser integrato per navigare verso la pagina dell'orario. I cookie sono salvati in `~/.config/poliscraper/cookies.sqlite`, per cui è possibile mantenere l'accesso aperto. Il tasto home in alto a destra offre una scorciatoia per l'[orario basato sul piano di studi](https://servizionline.polimi.it/portaleservizi/portaleservizi/controller/servizi/Servizi.do?evn_srv=evento&idServizio=398).

È possibile utilizzare un orario generato con l'apposito strumento del [manifesto degli studi](https://www4.ceda.polimi.it/manifesti/manifesti/controller/ManifestoPublic.do?lang=IT).

Quando ti trovi in una pagina supportata, il tasto *Scrape timetable* nella barra in alto diventa attivo. Cliccalo, salva il file iCal e importalo nella tua app per il calendario preferita ;)

### Importa su Google Calendar

1. Vai su [calendar.google.com](https://calendar.google.com).
1. Clicca la rotella dentata, *Impostazioni*, scheda *Calendari*.
1. *(Opzionale)* Crea un nuovo calendario. Non è strettamente necessario, ma, in caso di problemi, è molto più semplice cancellare un calendario piuttosto che riparare tutto a mano. 
1. Torna in *Impostazioni > Calendari*; seleziona *Importa calendario*.
1. Carica il file iCal generato. Stai attento a non importarlo nel calendario sbagliato.

## Risoluzione dei problemi

#### Il tasto "Scrape timetable" non si attiva

Devi utilizzare l'orario testuale. Quello sinottico non è supportato.

#### Mi appare un messaggio d'errore

Prima di lamentarti nel bug tracker, **assicurati di aver scaricato l'ultima revisione** da GitHub.

Se il problema persiste, attiva i parametri di debug, copia l'output del programma e postalo in un nuovo bug su GitHub.

    python src/scraper.py --debug-divs --debug-regex --debug-timetable

**Rimuovi le tue informazioni personali** dai log, e **[usa un pastebin](http://hastebin.com)** per postarlo. Posta le cagate su Facebook, non su GitHub. Grazie <3