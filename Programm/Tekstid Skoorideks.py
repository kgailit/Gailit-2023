#!/usr/bin/env python
# coding: utf-8

from estnltk import Span, Layer, Text
from estnltk.converters import text_to_json, json_to_text
from estnltk.taggers import VabamorfTagger

import json
import os
from collections import Counter, defaultdict
import string 
import nltk
import re
import math
from argparse import ArgumentParser



#Kokkukleepunud kirjavahemärkide leidmine
def leia_kokkukleepunud_kirjavahemärgid(oletamisega):
    rx = re.compile(r'\D\s?[,.!?][^\d\s]')
    rxx = rx.findall(oletamisega.text)
    return len(rxx)

# Leiab kolm korda korduvad vähemalt kahetähelised jupid
def leia_korduvad_jupid(oletamisega):
    rx = re.compile(r"([a-zA-ZüÜõÕäÄöÖšŠžŽ])\1{3,}|([a-zA-ZüÜõÕäÄöÖšŠžŽ]{2,})\2{2,}", re.IGNORECASE)
    rxx = rx.findall(oletamisega.text)
    return len(rxx)

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
    for analysis in oletamisega.morph_analysis:
        # Kui pole mitmese analüüsiga
        if len(analysis.partofspeech) == 1:
            pos = analysis.partofspeech[0]
            # Kui tegu on verbiga
            if pos == "V":
                #Jätab meelde sõnalõpu
                form = analysis.form[0]
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
    for analysis in oletamisega.morph_analysis:
        # Kui pole mitmese analüüsiga
        if len(analysis.partofspeech) == 1:
            pos = analysis.partofspeech[0]
            # Kui tegu on asesõnaga
            if pos == "P":
                #Jätab meelde asesõna
                lemma = analysis.lemma[0]
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
    for analysis in oletamisega.morph_analysis:
        # Kui pole mitmese analüüsiga
        if len(analysis.partofspeech) == 1:
            pos = analysis.partofspeech[0]
            # Kui tegu on verbiga
            if pos == "V":
                #Jätab meelde sõnalõpu
                form = analysis.form[0]
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
            for pos, form in zip(analysis.partofspeech, analysis.form):
                if pos == "V":
                    # Vaatab, kas tunnus on loendis, ja märgib, et järelikult on passiiviga
                    if form in tunnused:
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
    for analysis in oletamisega.morph_analysis:
        # Kui pole mitmese analüüsiga
        if len(analysis.partofspeech) == 1:
            pos = analysis.partofspeech[0]
            # Kui tegu on verbiga
            if pos == "V":
                #Jätab meelde sõnalõpu
                form = analysis.form[0]
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
            for pos, form in zip(analysis.partofspeech, analysis.form):
                if pos == "V":
                    # Vaatab, kas tunnus on loendis, ja märgib, et järelikult on passiiviga
                    if form in tunnused:
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
    for analysis in oletamisega.morph_analysis:
        # Kui pole mitmese analüüsiga
        if len(analysis.partofspeech) == 1:
            pos = analysis.partofspeech[0]
            # Kui tegu on verbiga
            if pos == "V":
                #Jätab meelde sõnalõpu
                form = analysis.form[0]
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
            for pos, form in zip(analysis.partofspeech, analysis.form):
                if pos == "V":
                    # Vaatab, kas tunnus on loendis, ja märgib, et järelikult on passiiviga
                    if form in tunnused:
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
    for sentence in oletamisega.sentences:
        kõik_arv += 1
        # Vaatab lause esimest sõna eraldi
        # Kas esimene sõna on täis väiketähed või täis suurtähed
        if sentence.words[0].text.islower():
            vale_väike += 1
        elif sentence.words[0].text.isupper():
            # Vaatab, et ei oleks ühe tähe suurune
            if len(sentence.words[0].text) > 1:
                ainult_suur += 1
        # Vaatab iga ülejäänud sõna lauses
        for word in sentence.words[1:]:
            # Kui sõna on ühe tähe pikkune või ainult kirjavahemärgid, jätab selle sõna vahele
            if len(word.text) == 1 or all(char in string.punctuation for char in word.text):
                continue
            kõik_arv += 1
            # Vaatab iga sõna, kas on vaid suurtähed
            if word.text.isupper():
                # Vaatab, et ei oleks lühendi analüüsiga
                lyhend = False
                if 'Y' not in word.morph_analysis.partofspeech:
                    ainult_suur += 1
                    
    # Kui tekstis ei sõnu, tagastab -1
    if kõik_arv == 0:
        return -1, -1
    return vale_väike/kõik_arv, ainult_suur/kõik_arv

def sõnaloendi_osaarv(oletamisega):
    kokku = len(oletamisega.words)
    loendis = 0
    
    for word in oletamisega.words:
        sona = word.text.lower()
        lemmad = word.lemma
        if sona in sõnaloend:
            loendis += 1
        else:
            for lemma in lemmad:
                if lemma.lower() in sõnaloend:
                    loendis += 1
                    break
        
    return loendis/kokku

def teisenda_vahemikku(algne, maksimum, miinimum):
    uus = ((algne - miinimum) / (maksimum - miinimum))
    
    if uus > 1:
        return 1.0
    elif uus < 0:
        return 0.0
    else:
        return uus

def formaalsus(andmed):
    
    skoor = 0
    skoor_temp = 0
    
    tunnus_TTR = andmed["TTR"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_TTR == -1:
        skoor_temp += 0
    # Jagasin polaarse tunnuse korpuse alusel 11-ks võrdseks osaks, et hinnata
    # <= 9.1%
    elif tunnus_TTR <= 0.450412:
        skoor_temp -= 5
    # <= 18.2%
    elif tunnus_TTR <= 0.520466:
        skoor_temp -= 4
    # <= 27.3%
    elif tunnus_TTR <= 0.571429:
        skoor_temp -= 3
    # <= 36.3%
    elif tunnus_TTR <= 0.611948:
        skoor_temp -= 2
    # <= 45.4%
    elif tunnus_TTR <= 0.647191:
        skoor_temp -= 1
    # <= 54.5%
    elif tunnus_TTR <= 0.679739:
        skoor_temp += 0
    # <= 63.6%
    elif tunnus_TTR <= 0.709795:
        skoor_temp += 1
    # <= 72.7%
    elif tunnus_TTR <= 0.740260:
        skoor_temp += 2
    # <= 81.8%
    elif tunnus_TTR <= 0.772973:
        skoor_temp += 3
    # <= 90.9%
    elif tunnus_TTR <= 0.813333:
        skoor_temp += 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor_temp += 5
    
    kaal = 8.80
    skoor += skoor_temp * kaal
    skoor_temp = 0
    
    tunnus_a1i = andmed["asesõnade_esimese_isiku_osaarv"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_a1i == -1:
        skoor_temp -= 0
    # Jagasin mitte-polaarse tunnuse korpuse alusel 6-ks võrdseks osaks, et hinnata
    # <= 16.7%
    elif tunnus_a1i <= 0.000000:
        skoor_temp -= 0
    # <= 33.3%
    elif tunnus_a1i <= 0.242424:
        skoor_temp -= 1
    # <= 50%
    elif tunnus_a1i <= 0.500000:
        skoor_temp -= 2
    # <= 66.7%
    elif tunnus_a1i <= 0.666667:
        skoor_temp -= 3
    # <= 83.3%
    elif tunnus_a1i <= 0.894737:
        skoor_temp -= 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor_temp -= 5
    
    kaal = 7.97
    skoor += skoor_temp * kaal
    skoor_temp = 0
    
    tunnus_a2i = andmed["asesõnade_teise_isiku_osaarv"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_a2i == -1:
        skoor_temp -= 0
    # Jagasin mitte-polaarse tunnuse korpuse alusel 6-ks võrdseks osaks, et hinnata
    # <= 50%
    elif tunnus_a2i == 0.000000:
        skoor_temp -= 0
    # <= 66.7%
    elif tunnus_a2i <= 0.200000:
        skoor_temp -= 3
    # <= 83.3%
    elif tunnus_a2i <= 0.500000:
        skoor_temp -= 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor_temp -= 5
    
    kaal = 4.19
    skoor += skoor_temp * kaal
    skoor_temp = 0
    
    tunnus_v1i = andmed["verbide_esimese_isiku_osaarv"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_v1i == -1:
        skoor_temp -= 0
    # Jagasin mitte-polaarse tunnuse korpuse alusel 6-ks võrdseks osaks, et hinnata
    # <= 33.3%
    elif tunnus_v1i == 0.000000:
        skoor_temp -= 0
    # <= 50%
    elif tunnus_v1i <= 0.105263:
        skoor_temp -= 2
    # <= 66.7%
    elif tunnus_v1i <= 0.222222:
        skoor_temp -= 3
    # <= 83.3%
    elif tunnus_v1i <= 0.375000:
        skoor_temp -= 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor_temp -= 5
    
    kaal = 12.82
    skoor += skoor_temp * kaal
    skoor_temp = 0
    
    tunnus_v2i = andmed["verbide_teise_isiku_osaarv"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_v2i == -1:
        skoor_temp -= 0
    # Jagasin mitte-polaarse tunnuse korpuse alusel 6-ks võrdseks osaks, et hinnata
    # <= 16.7%
    elif tunnus_v2i <= 0.000000:
        skoor_temp -= 0
    # <= 33.3%
    elif tunnus_v2i <= 0.058824:
        skoor_temp -= 1
    # <= 50%
    elif tunnus_v2i <= 0.125000:
        skoor_temp -= 2
    # <= 66.7%
    elif tunnus_v2i <= 0.200000:
        skoor_temp -= 3
    # <= 83.3%
    elif tunnus_v2i <= 0.333333:
        skoor_temp -= 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor_temp -= 5
    
    kaal = 5.48
    skoor += skoor_temp * kaal
    skoor_temp = 0
    
    tunnus_a3i = andmed["asesõnade_kolmanda_isiku_osaarv"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_a3i == -1:
        skoor_temp += 0
    # Jagasin mitte-polaarse tunnuse korpuse alusel 6-ks võrdseks osaks, et hinnata
    # <= 33.3%
    elif tunnus_a3i == 0.000000:
        skoor_temp += 0
    # <= 50%
    elif tunnus_a3i <= 0.200000:
        skoor_temp += 2
    # <= 66.7%
    elif tunnus_a3i <= 0.416667:
        skoor_temp += 3
    # <= 83.3%
    elif tunnus_a3i <= 0.800000:
        skoor_temp += 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor_temp += 5
    
    kaal = 2.44
    skoor += skoor_temp * kaal
    skoor_temp = 0
    
    tunnus_v3i = andmed["verbide_kolmanda_isiku_osaarv"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_v3i == -1:
        skoor_temp += 0
    # Jagasin mitte-polaarse tunnuse korpuse alusel 6-ks võrdseks osaks, et hinnata
    # <= 16.7%
    elif tunnus_v3i <= 0.400000:
        skoor_temp += 0
    # <= 33.3%
    elif tunnus_v3i <= 0.536585:
        skoor_temp += 1
    # <= 50%
    elif tunnus_v3i <= 0.666667:
        skoor_temp += 2
    # <= 66.7%
    elif tunnus_v3i <= 0.800000:
        skoor_temp += 3
    # <= 83.3%
    elif tunnus_v3i <= 0.945946:
        skoor_temp += 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor_temp += 5
    
    kaal = 12.72
    skoor += skoor_temp * kaal
    skoor_temp = 0
    
    tunnus_emotikonide_arv = andmed["emotikonide_arv"]
    # Binaarse tunnuse (on või ei ole) skoor_temp on vastavalt kas 5 või 0
    if tunnus_emotikonide_arv > 0.0000:
        skoor_temp -= 5
    
    kaal = 9.64
    skoor += skoor_temp * kaal
    skoor_temp = 0
    
    tunnus_kaudse_kõneviisi_osakaal = andmed["kaudse_kõneviisi_osakaal"]
    # Binaarse tunnuse (on või ei ole) skoor_temp on vastavalt kas 5 või 0
    if tunnus_kaudse_kõneviisi_osakaal > 0.0000:
        skoor_temp += 5
    
    kaal = 1.96
    skoor += skoor_temp * kaal
    skoor_temp = 0
    
    tunnus_nud = andmed["nud-partitsiibiga_verbide_osakaal"]
        # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_nud == -1:
        skoor_temp -= 0
    # Jagasin mitte-polaarse tunnuse korpuse alusel 6-ks võrdseks osaks, et hinnata
    # <= 16.7%
    elif tunnus_nud == 0.000000:
        skoor_temp -= 0
    # <= 33.3%
    elif tunnus_nud <= 0.011429:
        skoor_temp -= 1
    # <= 50%
    elif tunnus_nud <= 0.031250:
        skoor_temp -= 2
    # <= 66.7%
    elif tunnus_nud <= 0.049180:
        skoor_temp -= 3
    # <= 83.3%
    elif tunnus_nud <= 0.073529:
        skoor_temp -= 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor_temp -= 5
    
    kaal = 4.03
    skoor += skoor_temp * kaal
    skoor_temp = 0
    
    tunnus_passiiv = andmed["passiivi_osakaal"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_passiiv == -1:
        skoor_temp += 0
    # Jagasin mitte-polaarse tunnuse korpuse alusel 6-ks võrdseks osaks, et hinnata
    # <= 16.7%
    elif tunnus_passiiv <= 0.019608:
        skoor_temp += 0
    # <= 33.3%
    elif tunnus_passiiv <= 0.043011:
        skoor_temp += 1
    # <= 50%
    elif tunnus_passiiv <= 0.065246:
        skoor_temp += 2
    # <= 66.7%
    elif tunnus_passiiv <= 0.095808:
        skoor_temp += 3
    # <= 83.3%
    elif tunnus_passiiv <= 0.148138:
        skoor_temp += 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor_temp += 5
    
    kaal = 9.83
    skoor += skoor_temp * kaal
    skoor_temp = 0
    
    tunnus_käändsõnad = andmed["käändsõnade_osaarv"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_käändsõnad == -1:
        skoor_temp += 0
    # Jagasin polaarse tunnuse korpuse alusel 11-ks võrdseks osaks, et hinnata
    # <= 9.1%
    elif tunnus_käändsõnad <= 0.333333:
        skoor_temp -= 5
    # <= 18.2%
    elif tunnus_käändsõnad <= 0.378481:
        skoor_temp -= 4
    # <= 27.3%
    elif tunnus_käändsõnad <= 0.415044:
        skoor_temp -= 3
    # <= 36.4%
    elif tunnus_käändsõnad <= 0.447115:
        skoor_temp -= 2
    # <= 45.5%
    elif tunnus_käändsõnad <= 0.475958:
        skoor_temp -= 1
    # <= 54.5%
    elif tunnus_käändsõnad <= 0.502941:
        skoor_temp += 0
    # <= 63.6%
    elif tunnus_käändsõnad <= 0.527778:
        skoor_temp += 1
    # <= 72.7%
    elif tunnus_käändsõnad <= 0.552941:
        skoor_temp += 2
    # <= 81.8%
    elif tunnus_käändsõnad <= 0.581395:
        skoor_temp += 3
    # <= 90.9%
    elif tunnus_käändsõnad <= 0.619570:
        skoor_temp += 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor_temp += 5
    
    kaal = 20.75
    skoor += skoor_temp * kaal
    skoor_temp = 0
    
    tunnus_lemmapikkus = andmed["lemmapikkuse_osaarv"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_lemmapikkus == -1:
        skoor_temp += 0
    # Jagasin polaarse tunnuse korpuse alusel 11-ks võrdseks osaks, et hinnata
    # <= 9.1%
    elif tunnus_lemmapikkus <= 4.401786:
        skoor_temp -= 5
    # <= 18.2%
    elif tunnus_lemmapikkus <= 4.543703:
        skoor_temp -= 4
    # <= 27.3%
    elif tunnus_lemmapikkus <= 4.657800:
        skoor_temp -= 3
    # <= 36.4%
    elif tunnus_lemmapikkus <= 4.760417:
        skoor_temp -= 2
    # <= 45.5%
    elif tunnus_lemmapikkus <= 4.854926:
        skoor_temp -= 1
    # <= 54.5%
    elif tunnus_lemmapikkus <= 4.949524:
        skoor_temp += 0
    # <= 63.6%
    elif tunnus_lemmapikkus <= 5.045977:
        skoor_temp += 1
    # <= 72.7%
    elif tunnus_lemmapikkus <= 5.153620:
        skoor_temp += 2
    # <= 81.8%
    elif tunnus_lemmapikkus <= 5.282090:
        skoor_temp += 3
    # <= 90.9%
    elif tunnus_lemmapikkus <= 5.468645:
        skoor_temp += 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor_temp += 5
    
    kaal = 18.50
    skoor += skoor_temp * kaal
    skoor_temp = 0
    
    tunnus_leksikon = andmed["leksikonides_esinevade_osaarv"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_leksikon == -1:
        skoor_temp -= 0
    # Jagasin mitte-polaarse tunnuse korpuse alusel 6-ks võrdseks osaks, et hinnata
    # <= 50%
    elif tunnus_leksikon <= 0:
        skoor_temp -= 0
    # <= 66.7%
    elif tunnus_leksikon <= 0.001346:
        skoor_temp -= 3
    # <= 83.3%
    elif tunnus_leksikon <= 0.005435:
        skoor_temp -= 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor_temp -= 5
    
    kaal = 6.30
    skoor += skoor_temp * kaal
    skoor_temp = 0
    
    # Väljastab ühtlustatud skoori
    return teisenda_vahemikku(skoor, 366, -448)

def spontaansus(andmed):
    
    skoor = 0
    skoor_temp = 0
    
    tunnus_TTR = andmed["TTR"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_TTR == -1:
        skoor_temp += 0
    # Jagasin polaarse tunnuse korpuse alusel 11-ks võrdseks osaks, et hinnata
    # <= 9.1%
    elif tunnus_TTR <= 0.450412:
        skoor_temp += 5
    # <= 18.2%
    elif tunnus_TTR <= 0.520466:
        skoor_temp += 4
    # <= 27.3%
    elif tunnus_TTR <= 0.571429:
        skoor_temp += 3
    # <= 36.3%
    elif tunnus_TTR <= 0.611948:
        skoor_temp += 2
    # <= 45.4%
    elif tunnus_TTR <= 0.647191:
        skoor_temp += 1
    # <= 54.5%
    elif tunnus_TTR <= 0.679739:
        skoor_temp += 0
    # <= 63.6%
    elif tunnus_TTR <= 0.709795:
        skoor_temp -= 1
    # <= 72.7%
    elif tunnus_TTR <= 0.740260:
        skoor_temp -= 2
    # <= 81.8%
    elif tunnus_TTR <= 0.772973:
        skoor_temp -= 3
    # <= 90.9%
    elif tunnus_TTR <= 0.813333:
        skoor_temp -= 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor_temp -= 5
    
    kaal = 9.46
    skoor += skoor_temp * round(kaal ** (1/1.4), 2)
    skoor_temp = 0
    
    tunnus_emotikonide_arv = andmed["emotikonide_arv"]
    # Binaarse tunnuse (on või ei ole) skoor_temp on vastavalt kas 5 või 0
    if tunnus_emotikonide_arv > 0.0000:
        skoor_temp += 5
    
    kaal = 11.15
    skoor += skoor_temp * round(kaal ** (1/1.4), 2)
    skoor_temp = 0
    
    tunnus_lemmapikkus = andmed["lemmapikkuse_osaarv"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_lemmapikkus == -1:
        skoor_temp += 0
    # Jagasin polaarse tunnuse korpuse alusel 11-ks võrdseks osaks, et hinnata
    # <= 9.1%
    elif tunnus_lemmapikkus <= 4.401786:
        skoor_temp += 5
    # <= 18.2%
    elif tunnus_lemmapikkus <= 4.543703:
        skoor_temp += 4
    # <= 27.3%
    elif tunnus_lemmapikkus <= 4.657800:
        skoor_temp += 3
    # <= 36.4%
    elif tunnus_lemmapikkus <= 4.760417:
        skoor_temp += 2
    # <= 45.5%
    elif tunnus_lemmapikkus <= 4.854926:
        skoor_temp += 1
    # <= 54.5%
    elif tunnus_lemmapikkus <= 4.949524:
        skoor_temp += 0
    # <= 63.6%
    elif tunnus_lemmapikkus <= 5.045977:
        skoor_temp -= 1
    # <= 72.7%
    elif tunnus_lemmapikkus <= 5.153620:
        skoor_temp -= 2
    # <= 81.8%
    elif tunnus_lemmapikkus <= 5.282090:
        skoor_temp -= 3
    # <= 90.9%
    elif tunnus_lemmapikkus <= 5.468645:
        skoor_temp -= 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor_temp -= 5
        
    kaal = 14.95
    skoor += skoor_temp * round(kaal ** (1/1.4), 2)
    skoor_temp = 0
    
    tunnus_kokkukleepunud_kirjavahemärkide_arv = andmed["kokkukleepunud_kirjavahemärkide_arv"]
    # Binaarse tunnuse (on või ei ole) skoor_temp on vastavalt kas 5 või 0
    if tunnus_kokkukleepunud_kirjavahemärkide_arv > 0.0000:
        skoor_temp += 5
        
    kaal = 11.40
    skoor += skoor_temp * round(kaal ** (1/1.4), 2)
    skoor_temp = 0
    
    tunnus_korduvate_juppide_arv = andmed["korduvate_juppide_arv"]
    # Binaarse tunnuse (on või ei ole) skoor_temp on vastavalt kas 5 või 0
    if tunnus_korduvate_juppide_arv > 0.0000:
        skoor_temp += 5
        
    kaal = 3.14
    skoor += skoor_temp * round(kaal ** (1/1.4), 2)
    skoor_temp = 0
    
    tunnus_läbinisti_suur = andmed["läbinisti_suur"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_läbinisti_suur == -1:
        skoor_temp += 0
    # Jagasin mitte-polaarse tunnuse korpuse alusel 6-ks võrdseks osaks, et hinnata
    # Ei käsitle kirjavigasid binaarsetena, kuna neid võib olla vale-positiivseid (nt pärisnimesid)
    # <= 16.7%
    elif tunnus_läbinisti_suur == 0.000000:
        skoor_temp += 0
    # <= 66.7%
    elif tunnus_läbinisti_suur <= 0.002037:
        skoor_temp += 3
    # <= 83.3%
    elif tunnus_läbinisti_suur <= 0.009217:
        skoor_temp += 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor_temp += 5
        
    kaal = 6.11
    skoor += skoor_temp * round(kaal ** (1/1.4), 2)
    skoor_temp = 0
    
    tunnus_puuduva_suure_algustähega = andmed["puuduva_suure_algustähega"]
    # Binaarse tunnuse (on või ei ole) skoor_temp on vastavalt kas 5 või 0
    if tunnus_puuduva_suure_algustähega > 0.0000:
        skoor_temp += 5
        
    kaal = 16.53
    skoor += skoor_temp * round(kaal ** (1/1.4), 2)
    skoor_temp = 0
    
    tunnus_a1i = andmed["asesõnade_esimese_isiku_osaarv"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_a1i == -1:
        skoor_temp += 0
    # Jagasin mitte-polaarse tunnuse korpuse alusel 6-ks võrdseks osaks, et hinnata
    # <= 16.7%
    elif tunnus_a1i <= 0.000000:
        skoor_temp += 0
    # <= 33.3%
    elif tunnus_a1i <= 0.242424:
        skoor_temp += 1
    # <= 50%
    elif tunnus_a1i <= 0.500000:
        skoor_temp += 2
    # <= 66.7%
    elif tunnus_a1i <= 0.666667:
        skoor_temp += 3
    # <= 83.3%
    elif tunnus_a1i <= 0.894737:
        skoor_temp += 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor_temp += 5
        
    kaal = 8.29
    skoor += skoor_temp * round(kaal ** (1/1.4), 2)
    skoor_temp = 0
    
    tunnus_käändsõnad = andmed["käändsõnade_osaarv"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_käändsõnad == -1:
        skoor_temp += 0
    # Jagasin polaarse tunnuse korpuse alusel 11-ks võrdseks osaks, et hinnata
    # <= 9.1%
    elif tunnus_käändsõnad <= 0.333333:
        skoor_temp += 5
    # <= 18.2%
    elif tunnus_käändsõnad <= 0.378481:
        skoor_temp += 4
    # <= 27.3%
    elif tunnus_käändsõnad <= 0.415044:
        skoor_temp += 3
    # <= 36.4%
    elif tunnus_käändsõnad <= 0.447115:
        skoor_temp += 2
    # <= 45.5%
    elif tunnus_käändsõnad <= 0.475958:
        skoor_temp += 1
    # <= 54.5%
    elif tunnus_käändsõnad <= 0.502941:
        skoor_temp += 0
    # <= 63.6%
    elif tunnus_käändsõnad <= 0.527778:
        skoor_temp -= 1
    # <= 72.7%
    elif tunnus_käändsõnad <= 0.552941:
        skoor_temp -= 2
    # <= 81.8%
    elif tunnus_käändsõnad <= 0.581395:
        skoor_temp -= 3
    # <= 90.9%
    elif tunnus_käändsõnad <= 0.619570:
        skoor_temp -= 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor_temp -= 5
        
    kaal = 23.01
    skoor += skoor_temp * round(kaal ** (1/1.4), 2)
    skoor_temp = 0
    
    tunnus_leksikon = andmed["leksikonides_esinevade_osaarv"]
    # Kui tunnust tekstis ei leidunud, ei mõjuta see skoori
    if tunnus_leksikon == -1:
        skoor_temp += 0
    # Jagasin mitte-polaarse tunnuse korpuse alusel 6-ks võrdseks osaks, et hinnata
    # <= 50%
    elif tunnus_leksikon <= 0:
        skoor_temp += 0
    # <= 66.7%
    elif tunnus_leksikon <= 0.001346:
        skoor_temp += 3
    # <= 83.3%
    elif tunnus_leksikon <= 0.005435:
        skoor_temp += 4
    # <= 100% (ka suuremad, kui korpuses leiduvad)
    else:
        skoor_temp += 5
        
    kaal = 9.03
    skoor += skoor_temp * round(kaal ** (1/1.4), 2)
    skoor_temp = 0
    
    # Väljastab ühtlustatud skoori
    return teisenda_vahemikku(skoor, 268, -103)

# Jooksutamisele

if __name__ == '__main__':
    # Parse arguments
    parser = ArgumentParser()
    parser.add_argument("--sisend", dest="hinda",
                        help="Hinnatav fail või kaust", required=True)
    parser.add_argument("--tulemkaust", dest="kaust",
                        help="Kaust, kuhu skoorid väljastatakse", default="Skoorid/")
    
    args = parser.parse_args()
    
    hinda = args.hinda
    kaust = args.kaust.strip() + "/"
    
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
    
    #Loeb sisse leksikoni
    sõnaloend = None

    with open("Loendid/Leksikonid/koos.txt", "r", encoding="UTF-8") as fr:
        sõnaloend = [i.strip().lower() for i in fr.readlines()]
    
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
    
    oletamisega_morph_tagger = VabamorfTagger(guess=True, propername=True, disambiguate=True)
    
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
            
            oletamisega.tag_layer(['words', 'sentences', 'compound_tokens'])
        
            oletamisega_morph_tagger.tag( oletamisega )

            # Loeb kokku lemmade arvud ja käänduvate lemmade arvud
            kõikide_lemmade_arv = 0
            ainult_käänduvate_lemmade_arv = 0

            for lemma, postag in zip(oletamisega.lemma, oletamisega.partofspeech):
                kõikide_lemmade_arv += 1
                # Kui tegu on käänduva lemmaga
                # Vaatab ainult esimest sõnaliiki (et välistada käändelsi verbivorme omadussõnade hulgast)
                if postag[0] in ["A", "C", "G", "H", "K", "N", "O", "P", "S", "U", "Y"]:
                    ainult_käänduvate_lemmade_arv += 1
            lemmas_subwords = []
            for tokens in oletamisega.root_tokens:
                lemmad = None
                # Võtab lemmade loendist esimese tõlgenduse:
                lemmad = tokens[0]
                # Vaatab iga lemmat tekstis
                for lemma in lemmad:
                    # Kui kõik tähemärgid ei ole punktuatsioonimärgid
                    if not all(char in string.punctuation for char in lemma):
                        lemmas_subwords.append(lemma)

            # Võtab sõnade algvormid, ignoreerib kirjavahemärke
            lemmad = [lemma[0] for lemma in oletamisega.lemma  if not all(char in string.punctuation for char in lemma)]

            # Arvutab TTR-i, keskmise lemma osasõna pikkuse ja käänduvate lemmade osaarvu
            andmed['TTR'] = len(Counter(lemmad))/len(lemmad)
            andmed['lemmapikkuse_osaarv'] = sum(map(len, lemmas_subwords))/len(lemmas_subwords)
            andmed['käändsõnade_osaarv'] = ainult_käänduvate_lemmade_arv/kõikide_lemmade_arv
            
            
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

            # Leiab korduvate kokkukleepunud "juppide" arvu
            # nt silbid aga ka muud arbitraarsed kordused üle 2 tähe ja 3 korduse
            andmed['korduvate_juppide_arv'] = leia_korduvad_jupid(oletamisega)

            andmed['leksikonides_esinevade_osaarv'] = sõnaloendi_osaarv(oletamisega)
            
            # Teisendab tunnused skoorideks
            skoorid = dict()
            
            skoorid["formaalsus"] = formaalsus(andmed)
            skoorid["spontaansus"] = spontaansus(andmed)
            
            #Skoor faili
            target_filename = os.path.join(kaust, filename)
            
            with open(target_filename, "w", encoding="UTF-8") as fw:
                json.dump(skoorid, fw, sort_keys=True, indent=4)