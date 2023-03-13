# Gailit-baka-2021
Karl Gustav Gailit bakalaureusetöö *Spontaansuse ja formaalsuse kui dimensionaalse tekstimudeli dimensioonide automaatne hindamine veebitekstides* jaoks loodud Pythoni skript, mis hindab sisendiks antud tekstide formaalsust ja spontaansust.

Tekstide hindamise skripti nimi on `Tekstid Skoorideks.py`.

Skriptil on kohustuslik parameeter `--hinda`, millele tuleb anda kas ühe faili või kogu kausta nimi, mida hinnata. Skript eeldab, et kõik failid, mis on kaustas, kuuluvad hindamisele.

Skriptil on teine parameeter `--kaust`, mis on väljundkausta nimi. Kui väljundkausta ei määrata, väljastatakse tekstide skoorid kausta *Skoorid*. Failide skoorid väljastatakse samade faililaiendite ning failistruktuuriga, nagu on sisendtekstidel.

GitHubi kaust *Loendid* sisaldab programmi jooksutamiseks vajalikke emotikonide ja tajuverbide loendeid. Kaust *Loendid* peab olema skripti kasutamisel skriptiga samas kaustas.

GitHubi kaust *Notebooks* sisaldab programmi koostamisel loodud Jupyter Notebook faile, mida kasutasin süsteemi koostamisel ja mis ei ole vajalikud skripti jooksutamiseks.

Eelnõuded:
`
EstNLTK 1.4.1
`

Autor: Karl Gustav Gailit

Korpus: Eesti keele ühendkorpus 2019, 2019. aasta veebitekstide alamkorpus.
Korpuse alamhulk: https://drive.google.com/file/d/1xGYB8hx0-3zTB5nZ6rsTyiXcDxhD1ukG/view?usp=sharing.
