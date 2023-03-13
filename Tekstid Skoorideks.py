#!/usr/bin/env python
# coding: utf-8

from estnltk import Text
import json
import os
from collections import defaultdict
import string 
import nltk
from collections import Counter
import re
from argparse import ArgumentParser


#Tajuverbide keskmise arvutamine
def tajuverbide_keskmine(oletamisega):
    with open("Loendid\\tajuverbid\wordnet_tajuverbid.txt", "r", encoding = "utf8") as fr:
        lines = fr.readlines()
        tajuverbid = [verb.strip() for verb in lines]
        
    all_verbs = 0
    only_tajuverbs = 0

    for lemma, postag in zip(oletamisega.lemmas, oletamisega.postags):
        if postag == "V":
            all_verbs += 1
            if lemma in tajuverbid:
                only_tajuverbs += 1
    # Kui tekstis ei leidu verbe, tagastab -1
    if all_verbs == 0:
        return -1
    return only_tajuverbs / float(all_verbs)

#Korduvate tähtede leidmine
def leia_korduvad_tähed(oletamisega):
    rx = re.compile(r'[^\d\s.:,;\(\)\[\]][.:,;\(\)\[\]][^\d\s.:,;\(\)\[\]]', re.IGNORECASE)
    rxx = rx.findall(oletamisega.text)
    return len(rxx)


# Korduvate (mitte kokku kleepunud) sõnade leidmine
def korduvate_sõnade_arv(oletamisega):
    rx = re.compile(r"(\b\w+\b)(\s+\1)+", re.IGNORECASE)
    rxx = rx.findall(oletamisega.text)

    return len(rxx)

#Kokkukleepunud kirjavahemärkide leidmine
def leia_kokkukleepunud_kirjavahemärgid(oletamisega):
    rx = re.compile(r'\D\s?[,.!?][^\d\s]')
    rxx = rx.findall(oletamisega.text)
    return len(rxx)

# Leiab kolm korda korduvad vähemalt kahetähelised jupid
def leia_korduvad_jupid(oletamisega):
    rx = re.compile(r"([a-zA-ZüÜõÕäÄöÖšŠžŽ])\1{3,}|([a-zA-ZüÜõÕäÄöÖšŠžŽ]{2,})\1{2,}", re.IGNORECASE)
    rxx = rx.findall(oletamisega.text)
    return len(rxx)

#Tundmatude sõnade osakaalu leidmine
def luhemate_tundmatute_osakaal(oletamiseta):
    analuusita = 0
    koik = 0

    for word in oletamiseta.words:
        if word["analysis"] == []:
            # Vaatab, et ei oleks ainult punktuatsioon
            if not all(char in string.punctuation for char in word["text"]):
                # Kui esitäht on suur, on ilmselt pärisnimi
                if word["text"][0] == word["text"][0].lower():
                    if len(word["text"]) <= 10:
                        analuusita += 1
                        continue
                # Kontrollib, et sõna ei oleks läbinisti suur
                # Kui on, eeldab, et pole ikkagi tegu pärisnimega
                elif len(word["text"]) > 1:
                    if word["text"][1] != word["text"][1].lower():
                        analuusita += 1
                else:
                    # Ka ühe tähemärgi pikkused tundmatud sõnad märgib analüüsita
                    analuusita += 1
    # Kui tekstis ei leidu sõnu, tagastab -1
    if len(oletamiseta.words) == 0:
        return -1
    return analuusita / len(oletamiseta.words)

#Esimese, teise ja kolmanda isiku osakaalu leidmine verbidest
def verbide_isikute_osakaalud(oletamisega):
    # Tunnuste lõpud, EstNLTK dokumentatsioonist
    # Ei kordu omavahel
    esi_tunnused = ['sime', 'me', 'nuksime', 'nuksin', 'gem', 'ksin', 'n', 'sin', 'ksime']
    teine_tunnused = ['te', 'o', 'nuksite', 'd', 'site', 'ge', 'ksite']
    kolmas_tunnused = ['s', 'gu', 'vad', 'b']
    
    # Loeb kokku isikute kaupa ja kõik isikud kokku
    arv_koik = 0
    arv_esimene = 0
    arv_teine = 0
    arv_kolmas = 0
    
    # Vaatab iga sõna analüüsi
    for analysis in oletamisega.analysis:
        # Kui pole mitmese analüüsiga
        if len(analysis) == 1:
            analysis = analysis[0]
            # Kui tegu on verbiga
            if analysis['partofspeech'] == "V":
                #Jätab meelde sõnalõpu
                form = analysis['form']
                # Vaatab, kas tunnus on loendis, ja suurendab vastavalt skoori
                if form in esi_tunnused:
                    arv_koik += 1
                    arv_esimene += 1
                    continue
                # Vaatab, kas tunnus on loendis, ja suurendab vastavalt skoori
                elif form in teine_tunnused:
                    arv_koik += 1
                    arv_teine += 1
                    continue
                # Vaatab, kas tunnus on loendis, ja suurendab vastavalt skoori
                elif form in kolmas_tunnused:
                    arv_koik += 1
                    arv_kolmas += 1
                    continue
    # Kui tekstis ei leidu isikulisi verbe, tagastab -1
    if arv_koik == 0:
        return -1, -1, -1
    # Tagastab kõik kolm osaarvu
    return arv_esimene/arv_koik, arv_teine/arv_koik, arv_kolmas/arv_koik

#Esimese, teise ja kolmanda isiku osakaalu leidmine asesõnadest
def asesonade_isikute_osakaalud(oletamisega):
    # Loeb kokku isikute kaupa ja kõik isikud kokku
    arv_koik = 0
    arv_esimene = 0
    arv_teine = 0
    arv_kolmas = 0
    
    # Vaatab iga sõna analüüsi
    for analysis in oletamisega.analysis:
        # Kui pole mitmese analüüsiga
        if len(analysis) == 1:
            analysis = analysis[0]
            # Kui tegu on asesõnaga
            if analysis['partofspeech'] == "P":
                #Jätab meelde asesõna
                lemma = analysis['lemma']
                #Vaatab asesõna algvormi ja suurendab vastavat skoori
                if lemma == 'mina':
                    arv_koik += 1
                    arv_esimene += 1
                    continue
                #Vaatab asesõna algvormi ja suurendab vastavat skoori
                #Teietamine automaatselt sama, mis sinatamine (sina mitmuse analüüs)
                elif lemma == 'sina':
                    arv_koik += 1
                    arv_teine += 1
                    continue
                #Vaatab asesõna algvormi ja suurendab vastavat skoori
                elif lemma == 'tema':
                    arv_koik += 1
                    arv_kolmas += 1
                    continue
    # Kui tekstis ei leidu asesõnu, tagastab -1
    if arv_koik == 0:
        return -1, -1, -1
    # Tagastab kõik kolm osaarvu
    return arv_esimene/arv_koik, arv_teine/arv_koik, arv_kolmas/arv_koik

#Umbisikuliste verbide osakaalu leidmine tekstist
def passiivi_osakaal(oletamisega):
    # Tunnuste lõpud, EstNLTK dokumentatsioonist
    tunnused = ['takse', 'ti', 'tav', 'tuks', 'tagu', 'tama', 'tud', 'tuvat', 'tavat', 'taks', 'ta']
    
    # Loeb kokku tunnuste kaupa ja kõik kokku
    arv_koik = 0
    arv_passiiv = 0
    
    # Vaatab iga sõna analüüsi
    for analysis in oletamisega.analysis:
        # Kui pole mitmese analüüsiga
        if len(analysis) == 1:
            analysis = analysis[0]
            # Kui tegu on verbiga
            if analysis['partofspeech'] == "V":
                #Jätab meelde sõnalõpu
                form = analysis['form']
                # Vaatab, kas tunnus on loendis, ja suurendab vastavalt skoori
                if form in tunnused:
                    arv_koik += 1
                    arv_passiiv += 1
                    continue
                else:
                    arv_koik += 1
        # Kui on mitmese analüüsiga
        else:
            leidub_passiivne = False
            # Vaatab kõiki analüüse
            # Kui vähemalt üks on passiivi analüüsiga
            # Märgib kogu leiduva vormi passiivseks
            for analuus in analysis:
                if analuus['partofspeech'] == "V":
                    # Vaatab, kas tunnus on loendis, ja märgib, et järelikult on passiiviga
                    if analuus['form'] in tunnused:
                        leidub_passiivne = True
                        break
            
            if leidub_passiivne:
                arv_koik += 1
                arv_passiiv += 1
            else:
                arv_koik += 1
    # Kui tekstis ei leidu verbe, tagastab -1
    if arv_koik == 0:
        return -1
    # Tagastab osaarvu
    return arv_passiiv/arv_koik

#Nud-partitsiibiga verbide osakaalu leidmine tekstist
def nud_osakaal(oletamisega):
    # Tunnuste lõpud, EstNLTK dokumentatsioonist
    tunnused = ['nud']
    
    # Loeb kokku tunnuste kaupa ja kõik kokku
    arv_koik = 0
    arv_tunnus = 0
    
    # Vaatab iga sõna analüüsi
    for analysis in oletamisega.analysis:
        # Kui pole mitmese analüüsiga
        if len(analysis) == 1:
            analysis = analysis[0]
            # Kui tegu on verbiga
            if analysis['partofspeech'] == "V":
                #Jätab meelde sõnalõpu
                form = analysis['form']
                # Vaatab, kas tunnus on loendis, ja suurendab vastavalt skoori
                if form in tunnused:
                    arv_koik += 1
                    arv_tunnus += 1
                    continue
                else:
                    arv_koik += 1
        # Kui on mitmese analüüsiga
        else:
            leidub_tunnusega = False
            # Vaatab kõiki analüüse
            # Kui vähemalt üks on passiivi analüüsiga
            # Märgib kogu leiduva vormi passiivseks
            for analuus in analysis:
                if analuus['partofspeech'] == "V":
                    # Vaatab, kas tunnus on loendis, ja märgib, et järelikult on passiiviga
                    if analuus['form'] in tunnused:
                        leidub_tunnusega = True
                        break
            
            if leidub_tunnusega:
                arv_koik += 1
                arv_tunnus += 1
            else:
                arv_koik += 1
    # Kui tekstis ei leidu verbe, tagastab -1
    if arv_koik == 0:
        return -1
    # Tagastab osaarvu
    return arv_tunnus/arv_koik

#Vat-partitsiibiga verbide osakaalu leidmine tekstist
def vat_osakaal(oletamisega):
    # Tunnuste lõpud, EstNLTK dokumentatsioonist
    tunnused = ['vat']
    
    # Loeb kokku tunnuste kaupa ja kõik kokku
    arv_koik = 0
    arv_tunnus = 0
    
    # Vaatab iga sõna analüüsi
    for analysis in oletamisega.analysis:
        # Kui pole mitmese analüüsiga
        if len(analysis) == 1:
            analysis = analysis[0]
            # Kui tegu on verbiga
            if analysis['partofspeech'] == "V":
                #Jätab meelde sõnalõpu
                form = analysis['form']
                # Vaatab, kas tunnus on loendis, ja suurendab vastavalt skoori
                if form in tunnused:
                    arv_koik += 1
                    arv_tunnus += 1
                    continue
                else:
                    arv_koik += 1
        # Kui on mitmese analüüsiga
        else:
            leidub_tunnusega = False
            # Vaatab kõiki analüüse
            # Kui vähemalt üks on passiivi analüüsiga
            # Märgib kogu leiduva vormi passiivseks
            for analuus in analysis:
                if analuus['partofspeech'] == "V":
                    # Vaatab, kas tunnus on loendis, ja märgib, et järelikult on passiiviga
                    if analuus['form'] in tunnused:
                        leidub_tunnusega = True
                        break
            
            if leidub_tunnusega:
                arv_koik += 1
                arv_tunnus += 1
            else:
                arv_koik += 1
    # Kui tekstis ei leidu verbe, tagastab -1
    if arv_koik == 0:
        return -1
    # Tagastab osaarvu
    return arv_tunnus/arv_koik

def vale_tähesuurus_osakaal(oletamisega):
    vale_väike = 0
    ainult_suur = 0
    # Kõikide sõnade arv (ignoreerib kirjavahemärke)
    kõik_arv = 0

    # Vaatab iga lauset tekstis ükshaaval
    for sentence in oletamisega.split_by_sentences():
        kõik_arv += 1
        # Vaatab lause esimest sõna eraldi
        # Kas esimene sõna on täis väiketähed või täis suurtähed
        if sentence.words[0]['text'].islower():
            vale_väike += 1
        elif sentence.words[0]['text'].isupper():
            # Vaatab, et ei oleks ühe tähe suurune
            if len(sentence.words[0]['text']) > 1:
                ainult_suur += 1
        # Vaatab iga ülejäänud sõna lauses
        for word in sentence.words[1:]:
            # Kui sõna on ühe tähe pikkune või ainult kirjavahemärgid, jätab selle sõna vahele
            if len(word) == 1 or all(char in string.punctuation for char in word["text"]):
                continue
            kõik_arv += 1
            # Vaatab iga sõna, kas on vaid suurtähed
            if word["text"].isupper():
                # Vaatab, et ei oleks lühendi analüüsiga
                lyhend = False
                for analysis in word['analysis']:
                    if 'Y' == analysis['partofspeech']:
                        lyhend = True
                        break
                if not lyhend:
                    ainult_suur += 1
    # Kui tekstis ei sõnu, tagastab -1
    if kõik_arv == 0:
        return -1, -1
    return vale_väike/kõik_arv, ainult_suur/kõik_arv

def kirjavigadega_osaarv(oletamisega):
    kirjavigadega = 0
    # Vaatleb EstNLTK-sse sisse ehitatud kirjavigade mooduli abil kirjavigu
    for spellcheck, oletamisega_analysis in list(zip(oletamisega.spellcheck_results, oletamisega.analysis)):
        # Kui tegu on kirjaveaga sõnaga
        if spellcheck['spelling'] == False:
            nimi = False
            # Vaatab, et tegu poleks pärisnimega
            for analysis in oletamisega_analysis:
                if analysis['partofspeech'] == 'H':
                    nimi = True
            if not nimi:
                # Kui pole nimi, määrab kirjaveaks
                kirjavigadega += 1
    # Tagastab kirjavigadega sõnade protsendi
        # Kui tekstis ei ole sõnu, tagastab -1
    if len(oletamisega.analysis) == 0:
        return -1, -1
    return kirjavigadega / len(oletamisega.analysis)

def formaalsus(andmed):
    skoor = 0
    
    tunnus_TTR = andmed["TTR"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_TTR == -1:
        skoor += 0
    # Jagasin polaarse tunnuse korpuse alusel 11-ks võrdseks osaks, et hinnata
    # <= 9.1%
    elif tunnus_TTR <= 0.450412:
        skoor -= 5
    # <= 18.2%
    elif tunnus_TTR <= 0.520466:
        skoor -= 4
    # <= 27.3%
    elif tunnus_TTR <= 0.571429:
        skoor -= 3
    # <= 36.3%
    elif tunnus_TTR <= 0.611948:
        skoor -= 2
    # <= 45.4%
    elif tunnus_TTR <= 0.647191:
        skoor -= 1
    # <= 54.5%
    elif tunnus_TTR <= 0.679739:
        skoor += 0
    # <= 63.6%
    elif tunnus_TTR <= 0.709795:
        skoor += 1
    # <= 72.7%
    elif tunnus_TTR <= 0.740260:
        skoor += 2
    # <= 81.8%
    elif tunnus_TTR <= 0.772973:
        skoor += 3
    # <= 90.9%
    elif tunnus_TTR <= 0.813333:
        skoor += 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor += 5
    
    skoor_isik = 0
    
    tunnus_a1i = andmed["asesõnade_esimese_isiku_osaarv"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_a1i == -1:
        skoor_isik -= 0
    # Jagasin mitte-polaarse tunnuse korpuse alusel 6-ks võrdseks osaks, et hinnata
    # <= 16.7%
    elif tunnus_a1i <= 0.000000:
        skoor_isik -= 0
    # <= 33.3%
    elif tunnus_a1i <= 0.242424:
        skoor_isik -= 1
    # <= 50%
    elif tunnus_a1i <= 0.500000:
        skoor_isik -= 2
    # <= 66.7%
    elif tunnus_a1i <= 0.666667:
        skoor_isik -= 3
    # <= 83.3%
    elif tunnus_a1i <= 0.894737:
        skoor_isik -= 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor_isik -= 5
    
    tunnus_a2i = andmed["asesõnade_teise_isiku_osaarv"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_a2i == -1:
        skoor_isik -= 0
    # Jagasin mitte-polaarse tunnuse korpuse alusel 6-ks võrdseks osaks, et hinnata
    # <= 50%
    elif tunnus_a2i == 0.000000:
        skoor_isik -= 0
    # <= 66.7%
    elif tunnus_a2i <= 0.200000:
        skoor_isik -= 3
    # <= 83.3%
    elif tunnus_a2i <= 0.500000:
        skoor_isik -= 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor_isik -= 5
    
    tunnus_v1i = andmed["verbide_esimese_isiku_osaarv"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_v1i == -1:
        skoor_isik -= 0
    # Jagasin mitte-polaarse tunnuse korpuse alusel 6-ks võrdseks osaks, et hinnata
    # <= 33.3%
    elif tunnus_v1i == 0.000000:
        skoor_isik -= 0
    # <= 50%
    elif tunnus_v1i <= 0.105263:
        skoor_isik -= 2
    # <= 66.7%
    elif tunnus_v1i <= 0.222222:
        skoor_isik -= 3
    # <= 83.3%
    elif tunnus_v1i <= 0.375000:
        skoor_isik -= 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor_isik -= 5
    
    tunnus_v2i = andmed["verbide_teise_isiku_osaarv"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_v2i == -1:
        skoor_isik -= 0
    # Jagasin mitte-polaarse tunnuse korpuse alusel 6-ks võrdseks osaks, et hinnata
    # <= 16.7%
    elif tunnus_v2i <= 0.000000:
        skoor_isik -= 0
    # <= 33.3%
    elif tunnus_v2i <= 0.058824:
        skoor_isik -= 1
    # <= 50%
    elif tunnus_v2i <= 0.125000:
        skoor_isik -= 2
    # <= 66.7%
    elif tunnus_v2i <= 0.200000:
        skoor_isik -= 3
    # <= 83.3%
    elif tunnus_v2i <= 0.333333:
        skoor_isik -= 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor_isik -= 5
    
    # Vähendan isikute mõju skoorile, kuna need on omavahel seotud
    skoor += (skoor_isik / 4)
    skoor_isik = 0
    
    tunnus_a3i = andmed["asesõnade_kolmanda_isiku_osaarv"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_a3i == -1:
        skoor_isik += 0
    # Jagasin mitte-polaarse tunnuse korpuse alusel 6-ks võrdseks osaks, et hinnata
    # <= 33.3%
    elif tunnus_a3i == 0.000000:
        skoor_isik += 0
    # <= 50%
    elif tunnus_a3i <= 0.200000:
        skoor_isik += 2
    # <= 66.7%
    elif tunnus_a3i <= 0.416667:
        skoor_isik += 3
    # <= 83.3%
    elif tunnus_a3i <= 0.800000:
        skoor_isik += 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor_isik += 5
    
    tunnus_v3i = andmed["verbide_kolmanda_isiku_osaarv"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_v3i == -1:
        skoor_isik += 0
    # Jagasin mitte-polaarse tunnuse korpuse alusel 6-ks võrdseks osaks, et hinnata
    # <= 16.7%
    elif tunnus_v3i <= 0.400000:
        skoor_isik += 0
    # <= 33.3%
    elif tunnus_v3i <= 0.536585:
        skoor_isik += 1
    # <= 50%
    elif tunnus_v3i <= 0.666667:
        skoor_isik += 2
    # <= 66.7%
    elif tunnus_v3i <= 0.800000:
        skoor_isik += 3
    # <= 83.3%
    elif tunnus_v3i <= 0.945946:
        skoor_isik += 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor_isik += 5
    
    # Vähendan isikute mõju skoorile, kuna need on omavahel seotud
    skoor += (skoor_isik / 2)
    
    tunnus_emotikonide_arv = andmed["emotikonide_arv"]
    # Binaarse tunnuse (on või ei ole) skoor on vastavalt kas 5 või 0
    if tunnus_emotikonide_arv > 0.0000:
        skoor -= 5
    
    tunnus_kaudse_kõneviisi_osakaal = andmed["kaudse_kõneviisi_osakaal"]
    # Binaarse tunnuse (on või ei ole) skoor on vastavalt kas 5 või 0
    if tunnus_kaudse_kõneviisi_osakaal > 0.0000:
        skoor += 5
    
    tunnus_nud = andmed["nud-partitsiibiga_verbide_osakaal"]
        # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_nud == -1:
        skoor_isik -= 0
    # Jagasin mitte-polaarse tunnuse korpuse alusel 6-ks võrdseks osaks, et hinnata
    # <= 16.7%
    elif tunnus_nud == 0.000000:
        skoor -= 0
    # <= 33.3%
    elif tunnus_nud <= 0.011429:
        skoor -= 1
    # <= 50%
    elif tunnus_nud <= 0.031250:
        skoor -= 2
    # <= 66.7%
    elif tunnus_nud <= 0.049180:
        skoor -= 3
    # <= 83.3%
    elif tunnus_nud <= 0.073529:
        skoor -= 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor -= 5
    
    tunnus_passiiv = andmed["passiivi_osakaal"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_passiiv == -1:
        skoor_isik += 0
    # Jagasin mitte-polaarse tunnuse korpuse alusel 6-ks võrdseks osaks, et hinnata
    # <= 16.7%
    elif tunnus_passiiv <= 0.019608:
        skoor += 0
    # <= 33.3%
    elif tunnus_passiiv <= 0.043011:
        skoor += 1
    # <= 50%
    elif tunnus_passiiv <= 0.065246:
        skoor += 2
    # <= 66.7%
    elif tunnus_passiiv <= 0.095808:
        skoor += 3
    # <= 83.3%
    elif tunnus_passiiv <= 0.148138:
        skoor += 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor += 5
    
    tunnus_käändsõnad = andmed["käändsõnade_osaarv"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_käändsõnad == -1:
        skoor += 0
    # Jagasin polaarse tunnuse korpuse alusel 11-ks võrdseks osaks, et hinnata
    # <= 9.1%
    elif tunnus_käändsõnad <= 0.333333:
        skoor -= 5
    # <= 18.2%
    elif tunnus_käändsõnad <= 0.378481:
        skoor -= 4
    # <= 27.3%
    elif tunnus_käändsõnad <= 0.415044:
        skoor -= 3
    # <= 36.4%
    elif tunnus_käändsõnad <= 0.447115:
        skoor -= 2
    # <= 45.5%
    elif tunnus_käändsõnad <= 0.475958:
        skoor -= 1
    # <= 54.5%
    elif tunnus_käändsõnad <= 0.502941:
        skoor += 0
    # <= 63.6%
    elif tunnus_käändsõnad <= 0.527778:
        skoor += 1
    # <= 72.7%
    elif tunnus_käändsõnad <= 0.552941:
        skoor += 2
    # <= 81.8%
    elif tunnus_käändsõnad <= 0.581395:
        skoor += 3
    # <= 90.9%
    elif tunnus_käändsõnad <= 0.619570:
        skoor += 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor += 5
    
    tunnus_lemmapikkus = andmed["lemmapikkuse_osaarv"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_lemmapikkus == -1:
        skoor += 0
    # Jagasin polaarse tunnuse korpuse alusel 11-ks võrdseks osaks, et hinnata
    # <= 9.1%
    elif tunnus_lemmapikkus <= 4.401786:
        skoor -= 5
    # <= 18.2%
    elif tunnus_lemmapikkus <= 4.543703:
        skoor -= 4
    # <= 27.3%
    elif tunnus_lemmapikkus <= 4.657800:
        skoor -= 3
    # <= 36.4%
    elif tunnus_lemmapikkus <= 4.760417:
        skoor -= 2
    # <= 45.5%
    elif tunnus_lemmapikkus <= 4.854926:
        skoor -= 1
    # <= 54.5%
    elif tunnus_lemmapikkus <= 4.949524:
        skoor += 0
    # <= 63.6%
    elif tunnus_lemmapikkus <= 5.045977:
        skoor += 1
    # <= 72.7%
    elif tunnus_lemmapikkus <= 5.153620:
        skoor += 2
    # <= 81.8%
    elif tunnus_lemmapikkus <= 5.282090:
        skoor += 3
    # <= 90.9%
    elif tunnus_lemmapikkus <= 5.468645:
        skoor += 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor += 5
    
    #Paneb skoori vahemikku -1 ja 1
    if skoor < 0:
        return skoor / (5+5+5+5+5 + (20/4))
    else:
        return skoor / (5+5+5+5+5 + (10/2))

def spontaansus(andmed):
    skoor = 0
    
    tunnus_TTR = andmed["TTR"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_TTR == -1:
        skoor += 0
    # Jagasin polaarse tunnuse korpuse alusel 11-ks võrdseks osaks, et hinnata
    # <= 9.1%
    elif tunnus_TTR <= 0.450412:
        skoor += 5
    # <= 18.2%
    elif tunnus_TTR <= 0.520466:
        skoor += 4
    # <= 27.3%
    elif tunnus_TTR <= 0.571429:
        skoor += 3
    # <= 36.3%
    elif tunnus_TTR <= 0.611948:
        skoor += 2
    # <= 45.4%
    elif tunnus_TTR <= 0.647191:
        skoor += 1
    # <= 54.5%
    elif tunnus_TTR <= 0.679739:
        skoor += 0
    # <= 63.6%
    elif tunnus_TTR <= 0.709795:
        skoor -= 1
    # <= 72.7%
    elif tunnus_TTR <= 0.740260:
        skoor -= 2
    # <= 81.8%
    elif tunnus_TTR <= 0.772973:
        skoor -= 3
    # <= 90.9%
    elif tunnus_TTR <= 0.813333:
        skoor -= 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor -= 5
    
    tunnus_emotikonide_arv = andmed["emotikonide_arv"]
    # Binaarse tunnuse (on või ei ole) skoor on vastavalt kas 5 või 0
    if tunnus_emotikonide_arv > 0.0000:
        skoor += 5
    
    skoor_kirjavead = 0
    
    tunnus_kirjavigadega = andmed["kirjavigadega_osaarv"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_kirjavigadega == -1:
        skoor += 0
    # Jagasin mitte-polaarse tunnuse korpuse alusel 6-ks võrdseks osaks, et hinnata
    # Ei käsitle kirjavigasid binaarsetena, kuna neid võib olla vale-positiivseid (nt pärisnimesid)
    # <= 16.7%
    elif tunnus_kirjavigadega == 0.000000:
        skoor_kirjavead += 0
    # <= 33.3%
    elif tunnus_kirjavigadega <= 0.007508:
        skoor_kirjavead += 1
    # <= 50%
    elif tunnus_kirjavigadega <= 0.012698:
        skoor_kirjavead += 2
    # <= 66.7%
    elif tunnus_kirjavigadega <= 0.020690:
        skoor_kirjavead += 3
    # <= 83.3%
    elif tunnus_kirjavigadega <= 0.035088:
        skoor_kirjavead += 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor_kirjavead += 5
        
    tunnus_luhemate_tundmatute_osakaal = andmed["luhemate_tundmatute_osakaal"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_kirjavigadega == -1:
        skoor += 0
    # Jagasin mitte-polaarse tunnuse korpuse alusel 6-ks võrdseks osaks, et hinnata
    # Ei käsitle kirjavigasid binaarsetena, kuna neid võib olla vale-positiivseid (nt pärisnimesid)
    # <= 16.7%
    elif tunnus_luhemate_tundmatute_osakaal == 0.000000:
        skoor_kirjavead += 0
    # <= 33.3%
    elif tunnus_luhemate_tundmatute_osakaal <= 0.002433:
        skoor_kirjavead += 1
    # <= 50%
    elif tunnus_luhemate_tundmatute_osakaal <= 0.006711:
        skoor_kirjavead += 2
    # <= 66.7%
    elif tunnus_luhemate_tundmatute_osakaal <= 0.011628:
        skoor_kirjavead += 3
    # <= 83.3%
    elif tunnus_luhemate_tundmatute_osakaal <= 0.02170:
        skoor_kirjavead += 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor_kirjavead += 5
    
    skoor += (skoor_kirjavead / 2)
    
    tunnus_lemmapikkus = andmed["lemmapikkuse_osaarv"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_lemmapikkus == -1:
        skoor += 0
    # Jagasin polaarse tunnuse korpuse alusel 11-ks võrdseks osaks, et hinnata
    # <= 9.1%
    elif tunnus_lemmapikkus <= 4.401786:
        skoor += 5
    # <= 18.2%
    elif tunnus_lemmapikkus <= 4.543703:
        skoor += 4
    # <= 27.3%
    elif tunnus_lemmapikkus <= 4.657800:
        skoor += 3
    # <= 36.4%
    elif tunnus_lemmapikkus <= 4.760417:
        skoor += 2
    # <= 45.5%
    elif tunnus_lemmapikkus <= 4.854926:
        skoor += 1
    # <= 54.5%
    elif tunnus_lemmapikkus <= 4.949524:
        skoor += 0
    # <= 63.6%
    elif tunnus_lemmapikkus <= 5.045977:
        skoor -= 1
    # <= 72.7%
    elif tunnus_lemmapikkus <= 5.153620:
        skoor -= 2
    # <= 81.8%
    elif tunnus_lemmapikkus <= 5.282090:
        skoor -= 3
    # <= 90.9%
    elif tunnus_lemmapikkus <= 5.468645:
        skoor -= 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor -= 5
    
    tunnus_tajuverbide_osaarv = andmed["tajuverbide_osaarv"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_tajuverbide_osaarv == -1:
        skoor += 0
    # Jagasin mitte-polaarse tunnuse korpuse alusel 6-ks võrdseks osaks, et hinnata
    # <= 16.7%
    elif tunnus_tajuverbide_osaarv <= 0.044118:
        skoor += 0
    # <= 33.3%
    elif tunnus_tajuverbide_osaarv <= 0.085714:
        skoor += 1
    # <= 50%
    elif tunnus_tajuverbide_osaarv <= 0.117647:
        skoor += 2
    # <= 66.7%
    elif tunnus_tajuverbide_osaarv <= 0.150000:
        skoor += 3
    # <= 83.3%
    elif tunnus_tajuverbide_osaarv <= 0.192652:
        skoor += 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor += 5
    
    tunnus_kokkukleepunud_kirjavahemärkide_arv = andmed["kokkukleepunud_kirjavahemärkide_arv"]
    # Binaarse tunnuse (on või ei ole) skoor on vastavalt kas 5 või 0
    if tunnus_kokkukleepunud_kirjavahemärkide_arv > 0.0000:
        skoor += 5
    
    tunnus_korduvate_juppide_arv = andmed["korduvate_juppide_arv"]
    # Binaarse tunnuse (on või ei ole) skoor on vastavalt kas 5 või 0
    if tunnus_korduvate_juppide_arv > 0.0000:
        skoor += 5
    
    tunnus_läbinisti_suur = andmed["läbinisti_suur"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_läbinisti_suur == -1:
        skoor += 0
    # Jagasin mitte-polaarse tunnuse korpuse alusel 6-ks võrdseks osaks, et hinnata
    # Ei käsitle kirjavigasid binaarsetena, kuna neid võib olla vale-positiivseid (nt pärisnimesid)
    # <= 16.7%
    elif tunnus_läbinisti_suur == 0.000000:
        skoor += 0
    # <= 66.7%
    elif tunnus_läbinisti_suur <= 0.002037:
        skoor += 3
    # <= 83.3%
    elif tunnus_läbinisti_suur <= 0.009217:
        skoor += 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor += 5
    
    tunnus_puuduva_suure_algustähega = andmed["puuduva_suure_algustähega"]
    # Binaarse tunnuse (on või ei ole) skoor on vastavalt kas 5 või 0
    if tunnus_puuduva_suure_algustähega > 0.0000:
        skoor += 5
        
    tunnus_a1i = andmed["asesõnade_esimese_isiku_osaarv"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_a1i == -1:
        skoor += 0
    # Jagasin mitte-polaarse tunnuse korpuse alusel 6-ks võrdseks osaks, et hinnata
    # <= 16.7%
    elif tunnus_a1i <= 0.000000:
        skoor += 0
    # <= 33.3%
    elif tunnus_a1i <= 0.242424:
        skoor += 1
    # <= 50%
    elif tunnus_a1i <= 0.500000:
        skoor += 2
    # <= 66.7%
    elif tunnus_a1i <= 0.666667:
        skoor += 3
    # <= 83.3%
    elif tunnus_a1i <= 0.894737:
        skoor += 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor += 5
    
    #Paneb skoori vahemikku -1 ja 1, kuid 0 jääb 0-ks
    if skoor < 0:
        return skoor / (5 + 5)
    else:
        return skoor / (5 + 5 + (10/2) + 5 + 5 + 5 + 5 + 5 + 5 + 5)


# Jooksutamisele

if __name__ == '__main__':
    # Parse arguments
    parser = ArgumentParser()
    parser.add_argument("--hinda", dest="hinda",
                        help="Hinnatav fail või kaust", required=True)
    parser.add_argument("--kaust", dest="kaust",
                        help="Kaust, kuhu skoorid väljastatakse", default="Skoorid/")
    
    args = parser.parse_args()
    
    hinda = args.hinda
    kaust = args.kaust
    
    failinimed = []
    
    # Kui tegu on kaustaga
    if os.path.isdir(hinda):
        for path, dirs, files in os.walk(hinda):
            os.makedirs(os.path.join(kaust, path), exist_ok=True)
            failinimed = [os.path.join(path, filename) for filename in files if not os.path.isdir(filename)]
    # Kui tegu on failiga
    else:
        os.makedirs(os.path.dirname(kaust), exist_ok=True)
        failinimed = [hinda]
    
    # Loeb emotikonid sisse
    emotikonid = []

    for failinimi in ["wikipedia_emoticons_list.txt", "Unicode_emoticons_list.txt", "looks.wtf.txt", "unicode_emojis.txt"]:
        with open("Loendid/emotikonid/"+failinimi, "r", encoding="UTF-8") as fr:
            for line in fr.readlines():
                # Väiketähestab
                emotikonid.append(line.strip().lower())
    # Eemaldab korduvad emotikonid
    emotikonid = list(set(emotikonid))

    # Mõned emotikonid võivad olla ka kokkukleepumise tõttu olla väärpositiivsed (":pole")
    emotikonid_probleemsed = []
    with open("Loendid/emotikonid/wikipedia_emoticons_sp.txt", "r", encoding="UTF-8") as fr:
        for line in fr.readlines():
            # Väiketähestab
            emotikonid_probleemsed.append(line.strip().lower())
    # Eemaldab korduvad emotikonid 
    emotikonid_probleemsed = list(set(emotikonid_probleemsed))
    
    # Vaatab kõiki hinnatavaid faile
    for filename in failinimed:
        # Avab faili
        with open(filename, "r", encoding="UTF-8") as f:
            
            # Loeb failist vaid sisu, ignoreerib XML-i metainfot
            pure = ""
            for line in f.readlines():
                if line[0] == "<" and line[-1] == ">":
                    continue
                else:
                    pure = pure + "\n" + line

            # Regexiga leiab kõik potentsiaalsed emojid tekstist (kahe kooloni vaheline whitespaceita tekst)
            emojid = re.findall(":\S+?:", pure)
            # Eemaldab leitud emojide hulgast väärvasted
            wrong = [":http:", ":https:"]
            for value in wrong:
                while value in emojid:
                    emojid.remove(value)
            # Eemaldab emojid tekstist, et nende sisu ei peetaks sõnadeks 
            for emoji in emojid:
                pure = pure.replace(emoji, "")

            # Otsib tekstist emotikone ja paneb need nimekirja
            emotikonid_leitud = []
            for emotikon in emotikonid:
                emotikonid_leitud.extend(re.findall(re.escape(emotikon), pure, re.IGNORECASE))
                # Eemaldab tekstist leitud emotikonid, et need sõnestamisel lahku löömisel need keskmiseid ei mõjutaks
                pure = re.sub(re.escape(emotikon), '', pure, re.IGNORECASE)
            # Vaatab tekstist eraldi emotikone, mis võivad olla ka kokkukleepumise tulemusel väärpositiivsed vasted
            # Lisaks eemaldad leitud emotikonid
            sobivad = []
            for emotikon in emotikonid_probleemsed:
                # Kui "silmad" on viimane emotikoni osa, kontrollib, et emotikoni ees ei oleks tegu tähemärgiga ehk et poleks seoses sõnaga
                if emotikon[-1] == ":":
                    sobivad.extend(re.findall(re.escape(emotikon), "\n".join(re.findall("\W"+re.escape(emotikon), pure, re.IGNORECASE)), re.IGNORECASE))
                    pure = re.sub("(\W)"+re.escape(emotikon), '\1', pure, re.IGNORECASE)
                # Vastasel juhul kontrollib seda emotikoni lõpust
                else:
                    sobivad.extend(re.findall(re.escape(emotikon), "\n".join(re.findall(re.escape(emotikon)+"\W", pure, re.IGNORECASE)), re.IGNORECASE))
                    pure = re.sub(re.escape(emotikon)+"(\W)", '\1', pure, re.IGNORECASE)

            # Väljastatavate andmete sõnastik
            andmed = defaultdict(float)
                    
            # Jätab meelde emotikonide arvud ja loendid vigade kontrollimiseks
            andmed['emotikonide_arv'] = len(emojid) + len(emotikonid_leitud) + len(sobivad)

            # Teeb morfoloogilise analüüsi nii tundmatude analüüsi oletamisega ja oletamiseta
            oletamisega = Text(pure)
            oletamiseta = Text(pure, disambiguate=False, guess=False, propername=False)

            oletamisega.tag_analysis()
            oletamiseta.tag_analysis()

            # Loeb kokku lemmade arvud ja käänduvate lemmade arvud
            kõikide_lemmade_arv = 0
            ainult_käänduvate_lemmade_arv = 0

            for lemma, postag in zip(oletamisega.lemmas, oletamisega.postags):
                kõikide_lemmade_arv += 1
                # Kui tegu on käänduva lemmaga
                if postag in ["A", "C", "G", "H", "K", "N", "O", "S", "U", "Y"]:
                    ainult_käänduvate_lemmade_arv += 1

            # Loeb kokku lemmad lahutades liitsõnad osasõnadeks
            lemmas_subwords = []
            for tokens in oletamisega.root_tokens:
                # Kui tegu on sõnega ja mitte loendiga
                if isinstance(tokens[0], str):
                    for token in tokens:
                        # Kui kõik tähemärgid ei ole punktuatsioonimärgid
                        if not all(char in string.punctuation for char in token):
                            lemmas_subwords.append(token)
                # Kui tegu on loendiga, võtab esimese tõlgenduse
                else:
                    for token in tokens[0]:
                        # Kui kõik tähemärgid ei ole punktuatsioonimärgid
                        if not all(char in string.punctuation for char in token):
                            lemmas_subwords.append(token)

            # Võtab sõnade algvormid, ignoreerib kirjavahemärke
            lemmad = [lemma.split("|")[0] for lemma in oletamisega.lemmas if not all(char in string.punctuation for char in lemma)]

            # Arvutab TTR-i, keskmise lemma osasõna pikkuse ja käänduvate lemmade osaarvu
            andmed['TTR'] = len(Counter(lemmad))/len(lemmad)
            andmed['lemmapikkuse_osaarv'] = sum(map(len, lemmas_subwords))/len(lemmas_subwords)
            andmed['käändsõnade_osaarv'] = ainult_käänduvate_lemmade_arv/kõikide_lemmade_arv
            
            # Arvutab tajuverbide osaarvu kõikidest verbidest ja jätab meelde
            andmed['tajuverbide_osaarv'] = tajuverbide_keskmine(oletamisega)
            
            # Arvutab lühikeste tundmatu morfanalüüsi saanud sõnade osaarvu
            andmed['luhemate_tundmatute_osakaal'] = luhemate_tundmatute_osakaal(oletamiseta)
            
            # Loendab kokku vähemalt kolm korda korduvad tähed sõna sees
            andmed['korduvate_tähtede_arv'] = leia_korduvad_tähed(oletamisega)
            
            # Loendab kokku sõnadesse kokku kleepunud kirjavahemärkide arvu
            andmed['kokkukleepunud_kirjavahemärkide_arv'] = leia_kokkukleepunud_kirjavahemärgid(oletamisega)
            
            # Leiab verbide isikute protsendid (kui palju on 1., 2. ja 3. isik)
            verbide_isikute_protsendid = verbide_isikute_osakaalud(oletamisega)
            andmed['verbide_esimese_isiku_osaarv'] = verbide_isikute_protsendid[0]
            andmed['verbide_teise_isiku_osaarv'] = verbide_isikute_protsendid[1]
            andmed['verbide_kolmanda_isiku_osaarv'] = verbide_isikute_protsendid[2]
            
            # Leiab asesõnade isikute protsendid (kui palju on 1., 2. ja 3. isik)
            asesonade_isikute_protsendid = asesonade_isikute_osakaalud(oletamisega)
            andmed['asesõnade_esimese_isiku_osaarv'] = asesonade_isikute_protsendid[0]
            andmed['asesõnade_teise_isiku_osaarv'] = asesonade_isikute_protsendid[1]
            andmed['asesõnade_kolmanda_isiku_osaarv'] = asesonade_isikute_protsendid[2]
            
            # Leiab passiivi osakaalu ja jätab meelde
            andmed['passiivi_osakaal'] = passiivi_osakaal(oletamisega)
            
            # Leiab nud-partitsiibi osakaalu ja jätab meelde
            andmed['nud-partitsiibiga_verbide_osakaal'] = nud_osakaal(oletamisega)
            
            # Leiab kaudse kõneviisi osakaalu ja jätab meelde
            andmed['kaudse_kõneviisi_osakaal'] = vat_osakaal(oletamisega)
            
            # Leiab, kui palju tekstist on väikese algustähega või läbinisti suur
            valed_suurused = vale_tähesuurus_osakaal(oletamisega)
            andmed['puuduva_suure_algustähega'] = valed_suurused[0]
            andmed['läbinisti_suur'] = valed_suurused[1]
            
            # Leiab korduvate sõnade arvu
            andmed['korduvate_sõnade_arv'] = korduvate_sõnade_arv(oletamisega)
            
            # Leiab korduvate kokkukleepunud "juppide" arvu
            # nt silbid aga ka muud arbitraarsed kordused üle 2 tähe ja 3 korduse
            andmed['korduvate_juppide_arv'] = leia_korduvad_jupid(oletamisega)
            
            # Leiab kirjavigadega sõnade (mitte nimede) osaarvu
            andmed['kirjavigadega_osaarv'] = kirjavigadega_osaarv(oletamisega)
            
            # Teisendab tunnused skoorideks
            skoorid = dict()
            
            skoorid["formaalsus"] = formaalsus(andmed)
            skoorid["spontaansus"] = spontaansus(andmed)
            
            #Skoor faili
            target_filename = os.path.join(kaust, filename)
            
            with open(target_filename, "w", encoding="UTF-8") as fw:
                json.dump(skoorid, fw, sort_keys=True, indent=4)