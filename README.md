# Gailit-magister-2023

Karl Gustav Gailiti magistritöö *Leksikonide ja kaalude lisamine veebitekstide formaalsuse ja spontaansuse dimensioonide hindamise mudeli arendamiseks* jaoks loodud Pythoni skript, mis hindab sisendiks antud tekstide formaalsust ja spontaansust.

Tekstide hindamise skripti ja selleks vajalikud failid asuvad kõik kaustas *Programm*. Skripti nimi on `Tekstid Skoorideks.py`.

Skriptil on kohustuslik parameeter `--sisend`, millele tuleb anda kas ühe faili või kogu kausta nimi, mida soovitakse hinnata. Skript eeldab, et kõik failid, mis on kaustas, kuuluvad hindamisele.

Skriptil on teine parameeter `--tulemkaust`, mis tähistab väljundkausta nime. Kui väljundkausta nime ei määrata, väljastatakse tekstide skoorid kausta *Skoorid*. Iga faili hinnang väljastatakse sisendtekstile identse failinimega, sealhulgas laiendiga, kuid fail on ise struktuuri poolest JSON fail ning sisaldab teksti formaalsuse ja spontaansuse väärtuseid skaalal 0 kuni 1.

GitHubi kaust *Loendid* sisaldab programmi koostamisel kasutatud loendeid. Emotikonide ja tajuverbide loendid on loodud juba bakalaureusetöö raames. Lisatud on leksikonid neljal kujul: programmis kasutataval kujul (_Leksikonid_), kategooriate kaupa failidesse jaotatud kujul (_Leksikonid\_eraldi_), kategooriatesse jaotatud kujul koos sagedusloendis esinemiste arvu ja Ühendsõnastiku lisainformatsiooniga (_Leksikonid\_infoga_) ning lisaleksikonid, mis sisaldavad lisainformatsiooni, nagu EstNLTK oletamiseta morfoloogilisel analüüsil kõikide tundmatuks jäänud sõnade sõnaloendit (_Leksikonid\_meta_).

GitHubi kaust *Notebooks* sisaldab programmi koostamisel loodud Jupyter Notebook faile, mida kasutasin süsteemi koostamisel ja mis ei ole vajalikud skripti jooksutamiseks.

Eelnõuded:

EstNLTK 1.7.2

Autor: Karl Gustav Gailit

Korpus: Eesti keele ühendkorpus 2019, 2019. aasta veebitekstide alamkorpus.
Korpuse alamhulk: https://drive.google.com/file/d/1xGYB8hx0-3zTB5nZ6rsTyiXcDxhD1ukG/view?usp=sharing.
