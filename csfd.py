#!/usr/bin/python3
# -*- coding: utf-8 -*-
# encoding: utf-8

##############################################################################
# Copyright (c) 2011 Jakub Jirutka <jakub@jirutka.cz>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the  GNU Lesser General Public License for
# more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

##############################################################################
#
#                               ČSFD parser
#
# Parser pro stránky filmů a vyhledávání na Česko-Slovenské Filmové Databázi.
#
# Upozornění: Používejte tento kód pouze pro vlastní potřebu, nezneužívejte ho 
# pro vykrádání databáze ČSFD!
# 
# @author Jakub Jirutka <jakub@jirutka.cz>
# @version 1.0 beta
# @date 2011-12-15
#

from urllib.request import Request, urlopen
from urllib.parse import urlencode
from lxml.html import parse
import re


############################  C O N S T A N T S  #############################

BASE_URL = "http://www.csfd.cz"
MOVIES_URL = "http://www.csfd.cz/film/"
SEARCH_URL = "http://www.csfd.cz/hledat/"



##############################  C L A S S E S  ###############################

class Movie:
    """
    Třída reprezentující stránku filmu na ČSFD. Při vytvoření instance načte
    a zparsuje stránku daného filmu.
    """

    # Mapování čísla vlajky na kód jazyka
    _MAP_FLAG_LANG = {
        1 : 'en',  # USA
        2 : 'en',  # Velká Británie
        3 : 'en',  # Austrálie
        4 : 'de',  # Německo
        5 : 'de',  # Rakousko
        6 : 'en',  # Kanada
        7 : 'da',  # Dánsko
        8 : 'fi',  # Finsko
        10 : 'hu', # Maďarsko
        11 : 'nl', # Nizozemí
        12 : 'pl', # Polsko
        13 : 'ru', # Rusko
        14 : 'sv', # Švédsko
        15 : 'de', # Švýcarsko
        16 : 'th', # Thajsko
        17 : 'tr', # Turecko
        18 : 'nl', # Belgie
        19 : 'fr', # Francie
        21 : 'ga', # Irsko
        22 : 'it', # Itálie
        23 : 'es', # Španělština
        25 : 'no', # Norsko
        27 : 'es', # Argentina
        30 : 'pt', # Portugalština
        31 : 'tg', # Tádžikistán
        33 : 'jp', # Japonsko
        34 : 'cs', # Česká Republika
        35 : 'en', # Austrálie
        36 : 'cs', # Česká Republika
        37 : 'bg', # Bulharsko
        41 : 'ar', # Egypt
        47 : 'de', # Německo
        48 : 'de', # Německo
        49 : 'zh', # Čína
        52 : 'sk', # Slovensko
        55 : 'fa', # Peru
        62 : 'is', # Island
        # TODO
    }

    _RE_FLAG_NUM = re.compile("_([0-9]+)")


    def __init__(self, url):
        self.actors = list()
        self.best_rank = None
        self.content = None
        self.controversial_rank = None
        self.countries = list()
        self.directors = list()
        self.favorite_rank = None
        self.genres = list()
        self.imbd_url = None
        self.music = list()
        self.names = {}
        self.posters = list()
        self.rating = None
        self.runtime = None
        self.website_url = None
        self.worst_rank = None
        self.year = None

        self._fetch_data(url)


    def _fetch_data(self, url):
        """
        Načte HTML stránku filmu z dané URL, zparsuje a získá z ní požadovaná data.

        - url: celá URL stránky filmu [string]
        """

        doc = parse(url).getroot()

        profile = doc.xpath("//div[@id='profile']/div/div[2]")[0]

        # český název
        self.names['cs'] = profile.xpath("h1/text()")[0].strip()
    
        # ostatní názvy
        for item in profile.xpath("ul[@class='names']/li"):
            lang = self._convert_lang(item.find('img').get('src'))
            self.names[lang] = item.find('h3').text.strip()

        # žánry
        raw_genres = profile.xpath("p[@class='genre']/text()")
        if (raw_genres):
            self.genres = list( i.strip() for i in raw_genres[0].split('/') )

        # země, rok, stopáž
        try:
            raw_cyr = profile.xpath("p[@class='origin']/text()")[0]
            cyr = list( i.strip() for i in raw_cyr.split(',') )

            # stopáž
            if (cyr[-1].endswith("min")):
                self.runtime = cyr.pop().rstrip(' min')
    
            # rok
            if (cyr[-1].isdigit()):
                self.year = cyr.pop()

            # země
            self.countries = [i for i in cyr]

        except IndexError: pass

        # režiséři
        for item in profile.xpath("div[h4='Režie:']//a"):
            person = Person(item.text, BASE_URL + item.get('href'))
            self.directors.append(person)

        # hudební skldatelé
        for item in profile.xpath("div[h4='Hudba:']//a"):
            person = Person(item.text, BASE_URL + item.get('href'))
            self.music.append(person)

        # herci
        for item in profile.xpath("div[h4='Hrají:']//a"):
            person = Person(item.text, BASE_URL + item.get('href'))
            self.actors.append(person)

        # obsah
        try:
            self.content = doc.xpath("//div[@id='plots']/div[2]//div/text()")[1].strip()
        except IndexError: pass


        doc_rating = doc.xpath("//div[@id='rating']")[0]

        # hodnocení
        try:
            rating = doc_rating.xpath("h2/text()")[0].strip('%')
            self.rating = int(rating)
        except IndexError: pass

        # umístění v žebříčku nejlepších
        try:
            rank = doc_rating.xpath("//a[contains(@href, 'nejlepsi')]/text()")[0]
            self.best_rank = int(rank.split('.')[0])
        except IndexError: pass

        # umíštění v žebříčku nejhorších
        try:
            rank = doc_rating.xpath("//a[contains(@href, 'nejhorsi')]/text()")[0]
            self.worst_rank = int(rank.rsplit('.')[0])
        except IndexError: pass

        # umístění v žebříčku nejoblíbenějších
        try:
            rank = doc_rating.xpath("//a[contains(@href, 'nejoblibenejsi')]/text()")[0]
            self.favorite_rank = int(rank.split('.')[0])
        except IndexError: pass

        # umístění v žebříčku nejrozporuplnějších
        try:
            rank = doc_rating.xpath("//a[contains(@href, 'nejrozporuplnejsi')]/text()")[0]
            self.controversial_rank = int(rank.split('.')[0])
        except IndexError: pass

        # main poster
        try:
            self.posters.append(doc.xpath("//div[@id='poster']/img/@src")[0])
        except IndexError: pass

        # all posters
        regexp = re.compile("url\('(.*)'")
        for raw in doc.xpath("//div[@id='posters']/div[2]//div/@style"):
            link = regexp.search(raw).group(1).replace('\\', '')
            self.posters.append(link)

        # Link to IMDb.com
        try: 
            self.imbd_url = doc.xpath("//div[@id='share']//a[@title='profil na IMDb.com']/@href")[0]
        except IndexError: pass

        # Link to official website
        try:
            self.website_url = doc.xpath("//div[@id='share']//a[@class='www']/@href")[0]
        except IndexError: pass


    def _convert_lang(self, flag_url):
        """
        Podle dané URL nebo názvu obrázku vlajky určí jazyk, který reprezentuje, 
        a vrátí kód tohoto jazyka v ISO 639-1. Pokud nenajde mapování pro danou
        vlajku, vrátí pomlčku -.

        - flag_url: URL nebo název obrázku vlajky [string]
        - return: kód jazyka [string]
        """

        flag_num = int( Movie._RE_FLAG_NUM.search(flag_url).group(1) )

        try:
            return Movie._MAP_FLAG_LANG[flag_num]
        except KeyError:
            return '-'


    @property
    def origo_lang(self):
        """
        Podle dostupných názvů pro různé jazyky se pokusí určit, který z nich
        je původní název filmu (tj. název v jazyku produkční země) a vrátí
        kód jazyka (v ISO 639-1).

        - return: jazyk původního název filmu [string]
        """

        langs = set(self.names.keys())

        if (self.countries.count('Česko') or self.countries.count('Československo')):
            return 'cs'

        else:
            try:
                langs.remove('cs')
                langs.remove('sk')
            except KeyError: pass
        
            if (len(langs) == 0):
                return 'cs'
            elif (len(langs) == 1):
                return langs.pop()
            elif (len(langs) > 1):
                try:
                    langs.remove('en')
                except KeyError: pass
                return langs.pop()


    @property
    def origo_name(self):
        """
        Vrátí původní název filmu (tj. název v jazyku produkční země), určený
        podle metody origo_lang().

        - return: původní název filmu [string]
        """

        return self.names[self.origo_lang]



class MovieSearchResult:
    """
    Třída reprezentující položku filmu z výsledků hledání na ČSFD. Obsahuje 
    pouze základní informace dostupné ze stránky s výsledky a poskytuje 
    metodu pro získání objektu obsahující kompletní informace ze stránky filmu. 
    """

    def __init__(self, name, name_alt, year, url):
        self.name = name
        self.name_alt = name_alt
        self.url = url
        self.year = year


    def get_movie(self):
        """
        Načte a vrátí objekt obsahující kompletní informace o filmu.

        - return: objekt filmu [Movie]
        """

        return get_movie(self.url)



class Person:
    """
    Třída reprezentující odkaz na osobu (např. režiséra, herce...) Obsahuje 
    její jméno a URL stránky profilu na ČSFD.
    """
    
    def __init__(self, name, profile_url):
        self.name = name
        self.profile_url = profile_url




############################  F U N C T I O N S  #############################

def find_movie(text):
    """
    Vyhledá film na ČSFD podle daného názvu a vrátí seznam nalezených 
    výsledků.

    - text: název filmu (klíčová slova) [string]
    - return: seznam výsledků [list(MovieSearchResult)]
    """

    # TODO ošetřit přesměrování přímo na stránku filmu při jednoznačném výsledku

    results = list()

    url = SEARCH_URL + '?' + urlencode({'q' : text})
    doc = parse(url).getroot()

    doc_movies = doc.xpath("//div[@id='search-films']/div[1]")[0]

    # nalezené filmy - první výsledky
    for item in doc_movies.xpath("ul[1]/li"):
        a = item.find("h3/a")

        # český název
        name = a.text

        # URL stránky filmu
        url = BASE_URL + a.get('href')

        # barva podle hodnocení
        color = a.get('class')

        # druhý název (většinou původní název filmu)
        try :
            name_alt = item.xpath("span[@class='search-name']/text()")[0].strip('()')
        except IndexError: 
            name_alt = ""

        # žánry (nejsou všechny), země, rok
        gcy = item.find("p").text

        # rok vydání
        year = int( gcy.split(',')[-1].strip() )

        results.append( MovieSearchResult(name, name_alt, year, url) )

    # nalezené filmy - další výsledky
    for item in doc_movies.xpath("ul[2]/li"):
        a = item.find("a")

        # český název
        name = a.text

        # URL stránky filmu
        url = BASE_URL + a.get('href')

        # barva podle hodnocení
        color = a.get('class')

        # druhý název (většinou původní název filmu)
        try:
            name_alt = item.xpath("span[@class='search-name']/text()")[0].strip('()')
        except IndexError:
            name_alt = ""

        # rok vydání
        year = int( item.xpath("span[@class='film-year']/text()")[0].strip('()') )

        results.append( MovieSearchResult(name, name_alt, year, url) )


    return results



def get_movie(id):
    """
    Načte a vrátí objekt obsahující kompletní informace ze stránky filmu na 
    ČSFD podle její URL nebo ID filmu.

    - id: ID filmu nebo celá URL stránky filmu [string]
    - return: objekt filmu [Movie]
    """

    if(str(id).isdigit()):
        url = MOVIES_URL + str(id)
    else:
        url = id

    return Movie(url)
