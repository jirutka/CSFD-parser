# ČSFD Parser

Parser pro stránky filmů a vyhledávání na [ČSFD](http://www.csfd.cz).


## Poznámky

[ČSFD](http://www.csfd.cz) je nejznámější Česko-Slovenská filmová databáze. Obsahuje informace o více než čtvrt milionu českých a zahraničních filmů, dále informace o hercích, režisérech atd. Bohužel ale neposkytuje žádné veřejné API pro strojový přístup k datům, žádné webové služby. Jediný způsob, jakým z ní dostat data, je parsováním webových stránek. A přesně k tomu vznikl tento kód.

Webové stránky ČSFD mají sice doctype XHTML+RDFa, ale přitom jsem v nich žádné RDFa značky nenašel a dokonce nejsou ani _well-formed_. Nelze je proto přímo zpracovat jako XML. Všechny parsery, které jsem pro ČSFD našel (a jeden z nich jsem kdysi sám napsal), stránky parsují sadou složitých regulérních výrazů. Jejich vymýšlení sice může být poměrně zábavné procvičení mozkových závitů na dlouhé zimní večery, ale následné udržování a upravování při změně designu stránek je nesmírně náročné. Navíc takové řešení není příliš rychlé. Chtěl jsem proto zkusit trochu jiný přístup.

Tento parser není postavený na regulérních výrazech, ale místo toho využívá [HTML parser](http://lxml.de/), který ze stránky postaví XML DOM, nad kterým se poté dotazuje přes XPath. Lokalizace požadovaných elementů na stránce je díky XPath neuvěřitelně snadná a výsledný kód je krásně přehledný. Můžete sami porovnat například s [tímto](http://www.phpclasses.org/browse/file/33086.html) kódem.


## Požadavky

* Python 2.7 / 3.1
* [lxml](http://lxml.de/) (testováno na 2.3.1)


## Upozornění

Používejte tento kód pouze pro vlastní potřebu, nezneužívejte ho pro vykrádání databáze ČSFD!


## Licence

Tento projekt je uveřejněný pod licencí [LGPL version 3](http://www.gnu.org/licenses/lgpl.txt).

## Contributors

[Alex Rembish](http://github.com/rembish)
