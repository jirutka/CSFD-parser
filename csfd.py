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
#

import re

from sys import version_info
if version_info < (3, 0):
    from urllib import urlencode
else:
    from urllib.parse import urlencode

from lxml.html import parse

############################  C O N S T A N T S  #############################

BASE_URL = "http://www.csfd.cz"
MOVIES_URL = "http://www.csfd.cz/film/"
SEARCH_URL = "http://www.csfd.cz/hledat/"

##############################  C L A S S E S  ###############################

class Movie(object):
    """
    Třída reprezentující stránku filmu na ČSFD. Při vytvoření instance načte
    a zparsuje stránku daného filmu.
    """

    # Mapování čísla vlajky na kód země (ISO 3166-1)
    _MAP_FLAG_ISO = {
        1 : 'US',  # USA
        2 : 'GB',  # Velká Británie
        3 : 'AU',  # Austrálie
        4 : 'DE',  # Německo
        5 : 'AT',  # Rakousko
        6 : 'CA',  # Kanada
        7 : 'DK',  # Dánsko
        8 : 'FI',  # Finsko
        10 : 'HU', # Maďarsko
        11 : 'NL', # Nizozemí
        12 : 'PL', # Polsko
        13 : 'RU', # Rusko
        14 : 'SE', # Švédsko
        15 : 'CH', # Švýcarsko
        16 : 'TH', # Thajsko
        17 : 'TR', # Turecko
        18 : 'BE', # Belgie
        19 : 'FR', # Francie
        21 : 'IE', # Irsko
        22 : 'IT', # Itálie
        23 : 'ES', # Španělština
        25 : 'NO', # Norsko
        27 : 'AR', # Argentina
        30 : 'PT', # Portugalsko
        31 : 'TJ', # Tádžikistán
        33 : 'JP', # Japonsko
        34 : 'CZ', # Česká Republika
        35 : 'AU', # Austrálie
        36 : 'CZ', # Česká Republika
        37 : 'BG', # Bulharsko
        41 : 'EG', # Egypt
        47 : 'DE', # Německo
        48 : 'DE', # Německo
        49 : 'CN', # Čína
        52 : 'SK', # Slovensko
        55 : 'PE', # Peru
        62 : 'IS', # Island
        # TODO
    }

    _RE_FLAG_NUM = re.compile("_([0-9]+)")

    def __init__(self, url):
        """
        @param url: celá URL stránky filmu
        @type url: string
        """
        self.actors = list()
        self.best_rank = None
        self.content = None
        self.controversial_rank = None
        self.countries = list()
        self.directors = list()
        self.favorite_rank = None
        self.genres = list()
        self.imdb_url = None
        self.music = list()
        self._names = {}
        self.posters = list()
        self.rating = None
        self.runtime_str = None
        self.url = url
        self.website_url = None
        self.worst_rank = None
        self.year = None

        self._fetch_data(url)

    def _fetch_data(self, url):
        """
        Načte HTML stránku filmu z dané URL, zparsuje a získá z ní požadovaná data.

        @param url: celá URL stránky filmu
        """

        # zparsuje HTML a vytvoří XML DOM
        doc = parse(url).getroot()

        # sekce profilu filmu
        profile = doc.xpath("//div[@id='profile']/div/div[2]")[0]
    
        # názvy v dalších zemích
        for item in profile.xpath("ul[@class='names']/li"):
            country = self._convert_flag(item.find('img').get('src'))
            # existuje-li pro jednu zemi více názvů, chceme jen ten první
            if (country in self._names): continue
            self._names[country] = item.find('h3').text.strip()

        # oficiální název v ČR
        self._names['CZ'] = profile.xpath("h1/text()")[0].strip()

        # žánry
        raw_genres = profile.xpath("p[@class='genre']/text()")
        if (raw_genres):
            self.genres = list( i.strip() for i in raw_genres[0].split('/') )

        # země, rok, stopáž
        try:
            raw_cyr = profile.xpath("p[@class='origin']/text()")[0]
            cyr = list( i.strip() for i in raw_cyr.split(',') )

            # stopáž (celý řetězec; může obsahovat i stopáž režisérského střihu apod.)
            if ("min" in cyr[-1]):
                self.runtime_str = cyr.pop()
    
            # rok
            if (cyr[-1].isdigit()):
                self.year = int( cyr.pop() )

            # země
            self.countries = list( i.strip() for i in cyr.pop().split('/') )

        except IndexError: pass

        # režiséři
        for item in profile.xpath(u"div[h4='Režie:']//a"):
            person = Person(item.text, BASE_URL + item.get('href'))
            self.directors.append(person)

        # hudební skldatelé
        for item in profile.xpath("div[h4='Hudba:']//a"):
            person = Person(item.text, BASE_URL + item.get('href'))
            self.music.append(person)

        # herci
        for item in profile.xpath(u"div[h4='Hrají:']//a"):
            person = Person(item.text, BASE_URL + item.get('href'))
            self.actors.append(person)

        # obsah
        try:
            self.content = doc.xpath("//div[@id='plots']/div[2]//div/text()")[1].strip()
        except IndexError: pass

        # sekce hodnocení a žebříčků
        doc_rating = doc.xpath("//div[@id='rating']")[0]

        # hodnocení
        try:
            rating = doc_rating.xpath("h2/text()")[0].strip('%')
            self.rating = int( rating )
        except IndexError: pass

        # umístění v žebříčku nejlepších
        try:
            rank = doc_rating.xpath("//a[contains(@href, 'nejlepsi')]/text()")[0]
            self.best_rank = int( rank.split('.')[0] )
        except IndexError: pass

        # umíštění v žebříčku nejhorších
        try:
            rank = doc_rating.xpath("//a[contains(@href, 'nejhorsi')]/text()")[0]
            self.worst_rank = int( rank.rsplit('.')[0] )
        except IndexError: pass

        # umístění v žebříčku nejoblíbenějších
        try:
            rank = doc_rating.xpath("//a[contains(@href, 'nejoblibenejsi')]/text()")[0]
            self.favorite_rank = int( rank.split('.')[0] )
        except IndexError: pass

        # umístění v žebříčku nejrozporuplnějších
        try:
            rank = doc_rating.xpath("//a[contains(@href, 'nejrozporuplnejsi')]/text()")[0]
            self.controversial_rank = int( rank.split('.')[0] )
        except IndexError: pass

        # všechny plakáty (vč. hlavního)
        regexp = re.compile("url\('(.*)'")
        for raw in doc.xpath("//div[@id='posters']/div[2]//div/@style"):
            link = regexp.search(raw).group(1).replace('\\', '')
            self.posters.append(link)

        # pokud je k dispozici jen jeden plakát, tak se negeneruje sekce "posters",
        # takže musí načíst ze sekce "poster"
        if (len(self.posters) == 0):
            try:
                self.posters.append(doc.xpath("//div[@id='poster']/img/@src")[0])
            except IndexError: pass

        # odkaz na IMDb.com
        try: 
            self.imdb_url = doc.xpath("//div[@id='share']//a[@title='profil na IMDb.com']/@href")[0]
        except IndexError: pass

        # odkaz na oficiální web filmu
        try:
            self.website_url = doc.xpath("//div[@id='share']//a[@class='www']/@href")[0]
        except IndexError: pass

    def _convert_flag(self, flag_url):
        """
        Z dané URL (nebo názvu) obrázku vlajky určí kód její země (ISO 3166-1).
        Pokud nenajde mapování pro danou vlajku, vrátí pomlčku -.

        @param flag_url: URL nebo název obrázku vlajky
        @return: kód země v ISO 3166-1
        @rtype: string
        """

        flag_num = int( Movie._RE_FLAG_NUM.search(flag_url).group(1) )

        try:
            return Movie._MAP_FLAG_ISO[flag_num]
        except KeyError:
            return '-'

    def _origo_name_code(self):
        """
        Pokusí se určit, ke které zemi se vztahuje původní název filmu a vrátí
        kód této země.

        @return: kód země v ISO 3166-1
        @rtype: string
        """
        codes = set( self._names.keys() )

        # české filmy je nutné ošetřit explicitně, podle první země produkce
        if (self.countries and self.countries[0] in ["Česko", "Československo"]):
            return 'CZ'

        # na zahraniční filmy lze použít vylučovací metodu
        else:
            try:
                codes.remove('CZ')
                codes.remove('SK')
            except KeyError: pass
        
            if (len(codes) == 0):
                return 'CZ'
            elif (len(codes) == 1):
                return codes.pop()
            elif (len(codes) > 1):
                try:
                    codes.remove('US')
                except KeyError: pass
                return codes.pop()

    @property
    def names(self):
        """
        Vrátí všechny názvy filmu jako slovník {kód země : název filmu}. Kódy
        zemí jsou v ISO 3166-1.
        
        @return: názvy filmu
        @rtype: dict(str:str)
        """
        return self._names

    @property
    def origo_name(self):
        """
        Vrátí původní název filmu (tj. název z produkční země). Určení toho,
        který název je původní, není stoprocentně spolehlivé, ale v drtivé
        většině případů by mělo fungovat.

        @return: původní název filmu
        @rtype: string
        """
        return self._names[self._origo_name_code()]

    @property
    def runtime(self):
        """
        Vrátí standardní stopáž filmu jako číslo (ořízne případnou další
        stopáž uvedenou v závorce).
        
        @return: stopáž filmu
        @rtype: int
        """
        return int( self.runtime_str.split()[0] ) if self.runtime_str else None

class MovieSearchResult(object):
    """
    Třída reprezentující položku filmu z výsledků hledání na ČSFD. Obsahuje 
    pouze základní informace dostupné ze stránky s výsledky a poskytuje 
    metodu pro získání objektu obsahující kompletní informace ze stránky filmu. 
    """

    def __init__(self, name, name_alt, year, url):
        """
        @param name: český název
        @type name: string
        @param name_alt: druhý název (většinou původní název filmu)
        @type name_alt: string
        @param year: rok vydání
        @type year: int
        @param url: celá URL stránky filmu
        @type url: string
        """
        self.name = name
        self.name_alt = name_alt
        self.url = url
        self.year = year

    def get_movie(self):
        """
        Načte a vrátí objekt obsahující kompletní informace o filmu.

        @return: objekt filmu
        @rtype: Movie
        """

        return get_movie(self.url)

class Person(object):
    """
    Třída reprezentující odkaz na osobu (např. režiséra, herce...) Obsahuje 
    její jméno a URL stránky profilu na ČSFD.
    """
    
    def __init__(self, name, profile_url):
        """
        @param name: celé jméno
        @type name: string
        @param profile_url: celá URL stránky profilu
        @type profile_url: string
        """
        self.name = name
        self.profile_url = profile_url

############################  F U N C T I O N S  #############################

def find_movie(text):
    """
    Vyhledá film na ČSFD podle daného názvu a vrátí seznam nalezených 
    výsledků.

    @param text: název filmu (klíčová slova)
    @type text: string
    @return: seznam výsledků
    @rtype: list(MovieSearchResult)
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
        try:
            year = int( gcy.split(',')[-1].strip() )
        except ValueError:
            year = None

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

def get_movie(id_or_url):
    """
    Načte a vrátí objekt obsahující kompletní informace ze stránky filmu na 
    ČSFD podle její URL nebo ID filmu.

    @param id_or_url: ID filmu nebo celá URL stránky filmu
    @type id_or_url: string | int
    @return: objekt filmu
    @rtype: Movie
    """

    if(str(id).isdigit()):
        url = MOVIES_URL + str(id_or_url)
    else:
        url = id_or_url

    return Movie(url)
