"""Database seed route."""
import random
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter
from database import db

router = APIRouter(tags=["seed"])


@router.post("/seed")
async def seed_database():
    """Popola il database con dati di esempio ESPANSI (~600 prodotti)"""

    supermercati_data = [
        # === LOMBARDIA - Pioltello/Segrate/Cernusco (Milano Est) ===
        {"id": "coop-pioltello", "nome": "Coop Pioltello", "catena": "Coop", "indirizzo": "Via Roma 45, Pioltello MI", "lat": 45.4975, "lng": 9.3306, "regione": "Lombardia", "citta": "Pioltello", "orari": {"lun-sab": "08:00-21:00", "dom": "09:00-20:00"}, "telefono": "02 9267XXX", "servizi": ["parcheggio", "banco_gastronomia", "panetteria"]},
        {"id": "esselunga-pioltello", "nome": "Esselunga Pioltello", "catena": "Esselunga", "indirizzo": "Via Milano 120, Pioltello MI", "lat": 45.5012, "lng": 9.3245, "regione": "Lombardia", "citta": "Pioltello", "orari": {"lun-sab": "07:30-22:00", "dom": "08:00-21:00"}, "telefono": "02 9268XXX", "servizi": ["parcheggio", "banco_gastronomia", "bar", "farmacia"]},
        {"id": "lidl-pioltello", "nome": "Lidl Pioltello", "catena": "Lidl", "indirizzo": "Via Trieste 88, Pioltello MI", "lat": 45.4932, "lng": 9.3189, "regione": "Lombardia", "citta": "Pioltello", "orari": {"lun-sab": "08:00-21:30", "dom": "09:00-20:00"}, "telefono": "800 480XXX", "servizi": ["parcheggio", "panetteria"]},
        {"id": "eurospin-pioltello", "nome": "Eurospin Pioltello", "catena": "Eurospin", "indirizzo": "Via Bergamo 56, Pioltello MI", "lat": 45.4889, "lng": 9.3367, "regione": "Lombardia", "citta": "Pioltello", "orari": {"lun-sab": "08:30-20:00", "dom": "09:00-13:00"}, "telefono": "02 9269XXX", "servizi": ["parcheggio"]},
        {"id": "carrefour-segrate", "nome": "Carrefour Market Segrate", "catena": "Carrefour", "indirizzo": "Via Kennedy 15, Segrate MI", "lat": 45.4845, "lng": 9.2956, "regione": "Lombardia", "citta": "Segrate", "orari": {"lun-sab": "08:00-21:00", "dom": "09:00-20:00"}, "telefono": "02 2135XXX", "servizi": ["parcheggio", "banco_gastronomia", "sushi"]},
        {"id": "penny-pioltello", "nome": "Penny Market Pioltello", "catena": "Penny", "indirizzo": "Via Dante 22, Pioltello MI", "lat": 45.4901, "lng": 9.3298, "regione": "Lombardia", "citta": "Pioltello", "orari": {"lun-sab": "08:00-20:30", "dom": "09:00-13:00"}, "telefono": "02 9270XXX", "servizi": ["parcheggio"]},
        {"id": "md-segrate", "nome": "MD Discount Segrate", "catena": "MD", "indirizzo": "Via Verdi 78, Segrate MI", "lat": 45.4867, "lng": 9.3012, "regione": "Lombardia", "citta": "Segrate", "orari": {"lun-sab": "08:00-20:00", "dom": "09:00-13:30"}, "telefono": "02 2140XXX", "servizi": ["parcheggio"]},
        {"id": "conad-pioltello", "nome": "Conad City Pioltello", "catena": "Conad", "indirizzo": "Via Mazzini 33, Pioltello MI", "lat": 45.4958, "lng": 9.3278, "regione": "Lombardia", "citta": "Pioltello", "orari": {"lun-sab": "08:00-21:00", "dom": "09:00-20:00"}, "telefono": "02 9271XXX", "servizi": ["parcheggio", "banco_gastronomia"]},
        {"id": "aldi-segrate", "nome": "ALDI Segrate", "catena": "Aldi", "indirizzo": "Via Rivoltana 25, Segrate MI", "lat": 45.4823, "lng": 9.2898, "regione": "Lombardia", "citta": "Segrate", "orari": {"lun-sab": "08:00-21:00", "dom": "09:00-20:00"}, "telefono": "800 090XXX", "servizi": ["parcheggio", "panetteria"]},
        {"id": "despar-pioltello", "nome": "Despar Pioltello", "catena": "Despar", "indirizzo": "Via Garibaldi 15, Pioltello MI", "lat": 45.4941, "lng": 9.3334, "regione": "Lombardia", "citta": "Pioltello", "orari": {"lun-sab": "08:00-20:30", "dom": "09:00-13:00"}, "telefono": "02 9272XXX", "servizi": ["parcheggio"]},
        {"id": "unes-cernusco", "nome": "Unes Cernusco Sul Naviglio", "catena": "Unes", "indirizzo": "Via Torino 50, Cernusco sul Naviglio MI", "lat": 45.5012, "lng": 9.3367, "regione": "Lombardia", "citta": "Cernusco sul Naviglio", "orari": {"lun-sab": "08:00-21:00", "dom": "09:00-20:00"}, "telefono": "02 9274XXX", "servizi": ["parcheggio", "banco_gastronomia", "sushi"]},
        {"id": "iperal-pioltello", "nome": "Iperal Pioltello", "catena": "Iperal", "indirizzo": "Via Monza 88, Pioltello MI", "lat": 45.4990, "lng": 9.3198, "regione": "Lombardia", "citta": "Pioltello", "orari": {"lun-sab": "08:00-21:30", "dom": "09:00-20:00"}, "telefono": "02 9275XXX", "servizi": ["parcheggio", "banco_gastronomia", "panetteria", "farmacia"]},
        # === LOMBARDIA - Gallarate (Varese) ===
        {"id": "esselunga-gallarate-pegoraro", "nome": "Esselunga Gallarate Via Pegoraro", "catena": "Esselunga", "indirizzo": "Via Pegoraro 2, Gallarate VA", "lat": 45.6603, "lng": 8.7917, "regione": "Lombardia", "citta": "Gallarate", "orari": {"lun-sab": "07:30-22:00", "dom": "08:00-21:00"}, "telefono": "0331 77XXXX", "servizi": ["parcheggio", "banco_gastronomia", "bar"]},
        {"id": "esselunga-gallarate-borri", "nome": "Esselunga Gallarate Viale Borri", "catena": "Esselunga", "indirizzo": "Viale Borri 165, Gallarate VA", "lat": 45.6540, "lng": 8.7810, "regione": "Lombardia", "citta": "Gallarate", "orari": {"lun-sab": "07:30-22:00", "dom": "08:00-21:00"}, "telefono": "0331 78XXXX", "servizi": ["parcheggio", "banco_gastronomia", "farmacia"]},
        {"id": "conad-gallarate", "nome": "Conad City Gallarate", "catena": "Conad", "indirizzo": "Via Manzoni 15, Gallarate VA", "lat": 45.6590, "lng": 8.7900, "regione": "Lombardia", "citta": "Gallarate", "orari": {"lun-sab": "08:00-21:00", "dom": "09:00-20:00"}, "telefono": "0331 79XXXX", "servizi": ["parcheggio", "banco_gastronomia"]},
        {"id": "coop-gallarate", "nome": "Coop Gallarate", "catena": "Coop", "indirizzo": "Via Torino 33, Gallarate VA", "lat": 45.6620, "lng": 8.7880, "regione": "Lombardia", "citta": "Gallarate", "orari": {"lun-sab": "08:00-21:00", "dom": "09:00-20:00"}, "telefono": "0331 80XXXX", "servizi": ["parcheggio", "banco_gastronomia"]},
        {"id": "carrefour-gallarate", "nome": "Carrefour Market Gallarate", "catena": "Carrefour", "indirizzo": "Via Milano 88, Gallarate VA", "lat": 45.6550, "lng": 8.7830, "regione": "Lombardia", "citta": "Gallarate", "orari": {"lun-sab": "08:00-21:00", "dom": "09:00-20:00"}, "telefono": "0331 81XXXX", "servizi": ["parcheggio", "banco_gastronomia"]},
        {"id": "lidl-gallarate", "nome": "Lidl Gallarate", "catena": "Lidl", "indirizzo": "Via Cesare Battisti 20, Gallarate VA", "lat": 45.6580, "lng": 8.7950, "regione": "Lombardia", "citta": "Gallarate", "orari": {"lun-sab": "08:00-21:30", "dom": "09:00-20:00"}, "telefono": "800 480XXX", "servizi": ["parcheggio", "panetteria"]},
        {"id": "iperal-gallarate", "nome": "Iperal Gallarate", "catena": "Iperal", "indirizzo": "Via Varese 45, Gallarate VA", "lat": 45.6610, "lng": 8.8000, "regione": "Lombardia", "citta": "Gallarate", "orari": {"lun-sab": "08:00-21:30", "dom": "09:00-20:00"}, "telefono": "0331 82XXXX", "servizi": ["parcheggio", "banco_gastronomia", "panetteria"]},
        {"id": "ilgigante-gallarate", "nome": "Il Gigante Gallarate", "catena": "Il Gigante", "indirizzo": "Via Leonardo da Vinci 12, Gallarate VA", "lat": 45.6540, "lng": 8.7970, "regione": "Lombardia", "citta": "Gallarate", "orari": {"lun-sab": "08:00-21:00", "dom": "09:00-20:00"}, "telefono": "0331 83XXXX", "servizi": ["parcheggio", "banco_gastronomia", "panetteria"]},
        {"id": "md-gallarate", "nome": "MD Discount Gallarate", "catena": "MD", "indirizzo": "Via Roma 67, Gallarate VA", "lat": 45.6630, "lng": 8.7860, "regione": "Lombardia", "citta": "Gallarate", "orari": {"lun-sab": "08:00-20:00", "dom": "09:00-13:30"}, "telefono": "0331 84XXXX", "servizi": ["parcheggio"]},
        # === SICILIA - Catania ===
        {"id": "conad-catania-umberto", "nome": "Conad Via Umberto I Catania", "catena": "Conad", "indirizzo": "Via Umberto I 188, Catania CT", "lat": 37.5079, "lng": 15.0830, "regione": "Sicilia", "citta": "Catania", "orari": {"lun-sab": "08:00-21:00", "dom": "09:00-13:30"}, "telefono": "095 31XXXX", "servizi": ["parcheggio", "banco_gastronomia"]},
        {"id": "conad-catania-scannapieco", "nome": "Conad Via Scannapieco Catania", "catena": "Conad", "indirizzo": "Via Scannapieco 12, Catania CT", "lat": 37.5100, "lng": 15.0750, "regione": "Sicilia", "citta": "Catania", "orari": {"lun-sab": "08:00-21:00", "dom": "09:00-13:30"}, "telefono": "095 32XXXX", "servizi": ["parcheggio"]},
        {"id": "deco-catania-galermo", "nome": "Deco Via Galermo Catania", "catena": "Deco", "indirizzo": "Via Galermo 277, Catania CT", "lat": 37.5200, "lng": 15.0670, "regione": "Sicilia", "citta": "Catania", "orari": {"lun-sab": "08:00-21:00", "dom": "09:00-14:00"}, "telefono": "095 33XXXX", "servizi": ["parcheggio", "banco_gastronomia"]},
        {"id": "deco-catania-centro", "nome": "Deco Catania Centro", "catena": "Deco", "indirizzo": "Via Etnea 550, Catania CT", "lat": 37.5050, "lng": 15.0900, "regione": "Sicilia", "citta": "Catania", "orari": {"lun-sab": "08:00-20:30", "dom": "09:00-13:30"}, "telefono": "095 34XXXX", "servizi": ["banco_gastronomia"]},
        {"id": "eurospin-catania", "nome": "Eurospin Catania", "catena": "Eurospin", "indirizzo": "Viale Mario Rapisardi 100, Catania CT", "lat": 37.5150, "lng": 15.0580, "regione": "Sicilia", "citta": "Catania", "orari": {"lun-sab": "08:30-20:30", "dom": "09:00-13:00"}, "telefono": "095 35XXXX", "servizi": ["parcheggio"]},
        {"id": "lidl-catania", "nome": "Lidl Catania", "catena": "Lidl", "indirizzo": "Via Plebiscito 500, Catania CT", "lat": 37.5130, "lng": 15.0620, "regione": "Sicilia", "citta": "Catania", "orari": {"lun-sab": "08:00-21:30", "dom": "09:00-20:00"}, "telefono": "800 480XXX", "servizi": ["parcheggio", "panetteria"]},
        {"id": "ipercoop-catania", "nome": "Ipercoop Centro Sicilia Catania", "catena": "Ipercoop", "indirizzo": "Viale Jonio 67, Catania CT", "lat": 37.5000, "lng": 15.0950, "regione": "Sicilia", "citta": "Catania", "orari": {"lun-sab": "09:00-21:00", "dom": "09:00-21:00"}, "telefono": "095 36XXXX", "servizi": ["parcheggio", "banco_gastronomia", "panetteria", "farmacia"]},
        # === SICILIA - Palermo ===
        {"id": "conad-palermo", "nome": "Conad Palermo Via Liberta", "catena": "Conad", "indirizzo": "Via Liberta 212, Palermo PA", "lat": 38.1157, "lng": 13.3615, "regione": "Sicilia", "citta": "Palermo", "orari": {"lun-sab": "08:00-21:00", "dom": "09:00-13:30"}, "telefono": "091 61XXXX", "servizi": ["parcheggio", "banco_gastronomia"]},
        {"id": "deco-palermo", "nome": "Deco Palermo", "catena": "Deco", "indirizzo": "Via Notarbartolo 44, Palermo PA", "lat": 38.1100, "lng": 13.3580, "regione": "Sicilia", "citta": "Palermo", "orari": {"lun-sab": "08:00-21:00", "dom": "09:00-14:00"}, "telefono": "091 62XXXX", "servizi": ["parcheggio", "banco_gastronomia"]},
        {"id": "eurospin-palermo", "nome": "Eurospin Palermo", "catena": "Eurospin", "indirizzo": "Viale Regione Siciliana 2300, Palermo PA", "lat": 38.1200, "lng": 13.3650, "regione": "Sicilia", "citta": "Palermo", "orari": {"lun-sab": "08:30-20:30", "dom": "09:00-13:00"}, "telefono": "091 63XXXX", "servizi": ["parcheggio"]},
        {"id": "lidl-palermo", "nome": "Lidl Palermo", "catena": "Lidl", "indirizzo": "Via Ugo La Malfa 85, Palermo PA", "lat": 38.1180, "lng": 13.3700, "regione": "Sicilia", "citta": "Palermo", "orari": {"lun-sab": "08:00-21:30", "dom": "09:00-20:00"}, "telefono": "800 480XXX", "servizi": ["parcheggio", "panetteria"]},
        {"id": "ipercoop-palermo", "nome": "Ipercoop Forum Palermo", "catena": "Ipercoop", "indirizzo": "Via Lanza di Scalea 2311, Palermo PA", "lat": 38.1050, "lng": 13.3520, "regione": "Sicilia", "citta": "Palermo", "orari": {"lun-sab": "09:00-21:00", "dom": "09:00-21:00"}, "telefono": "091 64XXXX", "servizi": ["parcheggio", "banco_gastronomia", "panetteria", "farmacia"]},
    ]

    categorie_prodotti = {
        "Latticini": [("Latte Intero 1L","Granarolo","1L",1.49),("Latte Parzialmente Scremato 1L","Parmalat","1L",1.39),("Latte Scremato 1L","Zymil","1L",1.59),("Yogurt Bianco","Müller","125g",0.89),("Yogurt Greco","Fage","150g",1.29),("Yogurt Frutta","Danone","125g",0.79),("Mozzarella","Galbani","125g",1.29),("Mozzarella di Bufala","Fattorie Fiandino","125g",2.49),("Parmigiano Reggiano","Parmareggio","200g",4.99),("Grana Padano","Virgilio","200g",3.99),("Pecorino Romano","Locatelli","150g",4.49),("Burro","Lurpak","250g",2.49),("Burro Italiano","Granarolo","250g",1.99),("Ricotta","Santa Lucia","250g",1.79),("Mascarpone","Galbani","250g",2.29),("Stracchino","Nonno Nanni","200g",2.19),("Gorgonzola","Igor","150g",2.99),("Philadelphia","Kraft","150g",1.99),("Panna da Cucina","Parmalat","200ml",1.09),("Panna Montata","Hoplà","250ml",1.49)],
        "Pane e Cereali": [("Pane in Cassetta","Mulino Bianco","400g",1.89),("Pane Integrale","Mulino Bianco","400g",2.19),("Fette Biscottate","Mulino Bianco","315g",1.99),("Fette Biscottate Integrali","Mulino Bianco","315g",2.29),("Cornflakes","Kellogg's","375g",2.79),("Corn Flakes Integrali","Kellogg's","375g",3.19),("Muesli","Vitalis","600g",3.49),("Granola","Quaker","500g",3.99),("Pasta Spaghetti","Barilla","500g",0.99),("Pasta Penne","De Cecco","500g",1.29),("Pasta Fusilli","Barilla","500g",0.99),("Pasta Rigatoni","Rummo","500g",1.49),("Pasta Farfalle","Voiello","500g",1.39),("Pasta Orecchiette","Divella","500g",1.19),("Lasagne","Barilla","500g",2.49),("Riso Arborio","Scotti","1kg",2.19),("Riso Carnaroli","Riso Gallo","1kg",2.79),("Riso Basmati","Scotti","500g",1.99),("Farina 00","Caputo","1kg",0.89),("Farina Manitoba","Molino Rossetto","1kg",1.49),("Semola","De Cecco","1kg",1.19),("Crackers","Pavesi","500g",1.79)],
        "Frutta e Verdura": [("Mele Golden","Italia","1kg",1.99),("Mele Fuji","Italia","1kg",2.29),("Pere Conference","Italia","1kg",2.49),("Banane","Chiquita","1kg",1.49),("Arance","Sicilia","1kg",1.79),("Limoni","Sicilia","500g",1.29),("Mandarini","Sicilia","1kg",2.19),("Kiwi","Zespri","500g",2.49),("Fragole","Italia","250g",2.99),("Uva Bianca","Italia","500g",2.79),("Pomodori","Italia","1kg",2.29),("Pomodorini Ciliegino","Sicilia","500g",2.49),("Insalata Iceberg","Italia","1pz",0.99),("Lattuga Romana","Italia","1pz",1.19),("Rucola","Italia","100g",1.49),("Spinaci","Italia","400g",1.99),("Carote","Italia","1kg",1.29),("Patate","Italia","2kg",2.49),("Cipolle","Italia","1kg",1.19),("Aglio","Italia","200g",1.49),("Zucchine","Italia","1kg",2.29),("Melanzane","Italia","1kg",1.99),("Peperoni","Italia","1kg",2.99),("Funghi Champignon","Italia","400g",1.99),("Broccoli","Italia","500g",1.79),("Cavolfiore","Italia","1pz",1.99)],
        "Carne e Pesce": [("Petto di Pollo","AIA","500g",6.99),("Fusi di Pollo","AIA","600g",4.99),("Cosce di Pollo","AIA","1kg",5.49),("Macinato Bovino","Inalca","400g",5.49),("Macinato Misto","Inalca","400g",4.99),("Bistecca di Manzo","Chianina","300g",8.99),("Fettine di Vitello","Italia","400g",7.49),("Salsiccia","Aia","400g",3.99),("Prosciutto Cotto","Rovagnati","100g",2.49),("Prosciutto Crudo","San Daniele","80g",3.99),("Mortadella","Fini","150g",2.29),("Salame Milano","Citterio","100g",2.99),("Bresaola","Rigamonti","80g",3.99),("Speck","Senfter","100g",3.49),("Salmone Affumicato","Fjord","100g",3.99),("Tonno in Scatola","Rio Mare","160g",2.79),("Tonno all'Olio","Nostromo","160g",2.49),("Sgombro in Scatola","Rio Mare","125g",1.99),("Wurstel","Wudy","250g",1.99),("Cotechino","Modena","500g",4.99),("Filetti di Merluzzo","Findus","400g",5.99),("Bastoncini di Pesce","Findus","450g",4.49)],
        "Bevande": [("Acqua Naturale 6x1.5L","Sant'Anna","9L",2.49),("Acqua Frizzante 6x1.5L","San Pellegrino","9L",2.99),("Acqua Effervescente Naturale","Ferrarelle","6x1L",3.49),("Coca Cola","Coca-Cola","1.5L",1.69),("Coca Cola Zero","Coca-Cola","1.5L",1.69),("Fanta","Coca-Cola","1.5L",1.59),("Sprite","Coca-Cola","1.5L",1.59),("Pepsi","Pepsi","1.5L",1.49),("Succo Arancia","Santal","1L",1.49),("Succo ACE","Yoga","1L",1.39),("Succo Pesca","Santal","1L",1.49),("Succo Mela","Zuegg","1L",1.59),("Birra Lager","Peroni","66cl",1.29),("Birra Doppio Malto","Moretti","66cl",1.49),("Birra Artigianale","Ichnusa","50cl",1.99),("Vino Rosso","Tavernello","1L",2.49),("Vino Bianco","Tavernello","1L",2.49),("Prosecco","Mionetto","75cl",6.99),("Caffè Macinato","Lavazza","250g",3.99),("Caffè Capsule","Nespresso","10pz",4.99),("Tè Verde","Twinings","25pz",2.79),("Tè Nero","Twinings","25pz",2.79),("Camomilla","Star","20pz",1.99)],
        "Snack e Dolci": [("Biscotti Gocciole","Pavesi","500g",2.49),("Biscotti Macine","Mulino Bianco","350g",1.99),("Biscotti Pan di Stelle","Mulino Bianco","350g",2.49),("Biscotti Ringo","Pavesi","330g",1.79),("Nutella","Ferrero","400g",3.49),("Nutella","Ferrero","750g",5.99),("Cioccolato Fondente","Lindt","100g",2.99),("Cioccolato al Latte","Milka","100g",1.99),("Cioccolatini","Baci Perugina","200g",6.99),("Patatine","San Carlo","150g",1.99),("Patatine Rustiche","Amica Chips","200g",1.79),("Taralli","Fiore","250g",1.49),("Grissini","Mulino Bianco","280g",1.29),("Gelato Vaniglia","Algida","500ml",3.49),("Gelato Cioccolato","Häagen-Dazs","460ml",5.99),("Merendine Kinder","Ferrero","10pz",3.29),("Merendine Brioche","Mulino Bianco","10pz",2.79),("Cracker Salati","Mulino Bianco","500g",1.79),("Marmellata Fragole","Zuegg","320g",2.19),("Marmellata Albicocche","Zuegg","320g",2.19),("Miele","Ambrosoli","500g",4.99),("Creme Spalmabili","Novi","350g",2.99)],
        "Condimenti e Salse": [("Olio Extravergine","Monini","1L",7.99),("Olio Extravergine Bio","Carapelli","750ml",9.99),("Olio di Semi","Cuore","1L",2.49),("Aceto Balsamico","Ponti","250ml",2.99),("Aceto di Vino","Ponti","1L",1.29),("Sale Fino","Sale Marino","1kg",0.49),("Sale Grosso","Sale Marino","1kg",0.49),("Pepe Nero","Cannamela","50g",1.99),("Passata di Pomodoro","Mutti","700g",1.49),("Polpa di Pomodoro","Cirio","400g",0.99),("Pelati","Mutti","400g",1.19),("Concentrato di Pomodoro","Mutti","200g",1.49),("Pesto Genovese","Barilla","190g",2.49),("Pesto Rosso","Barilla","190g",2.29),("Maionese","Calvé","225ml",1.99),("Ketchup","Heinz","460g",2.29),("Senape","Maille","200g",1.99),("Dado","Star","10pz",1.49)],
        "Surgelati": [("Pizza Margherita","Buitoni","350g",2.99),("Pizza 4 Formaggi","Dr.Oetker","400g",3.49),("Lasagne Surgelate","Findus","600g",4.99),("Minestrone","Findus","750g",2.99),("Verdure Miste","Orogel","450g",1.99),("Piselli","Bonduelle","450g",1.79),("Fagiolini","Orogel","450g",1.89),("Spinaci Surgelati","Findus","450g",1.99),("Patate Fritte","McCain","750g",2.49),("Crocchette","Findus","400g",2.79),("Gelato Cono","Cornetto","4pz",3.99),("Gelato Stecco","Magnum","4pz",4.99)],
        "Igiene e Casa": [("Carta Igienica 8 rotoli","Scottex","8pz",4.99),("Carta Igienica 12 rotoli","Tenderly","12pz",6.99),("Carta da Cucina","Scottex","2pz",2.49),("Fazzoletti","Tempo","10pz",1.29),("Detersivo Piatti","Fairy","650ml",2.29),("Detersivo Piatti Eco","Svelto","500ml",1.99),("Detersivo Lavatrice","Dash","25 lavaggi",7.99),("Ammorbidente","Lenor","650ml",2.99),("Detersivo Pavimenti","Mastro Lindo","1L",2.49),("Sgrassatore","Chanteclair","625ml",2.19),("Candeggina","ACE","2L",1.99),("Spugne","Vileda","3pz",1.49),("Sacchetti Spazzatura","Domopak","20pz",1.99),("Pellicola","Domopak","50m",2.49),("Alluminio","Cuki","20m",1.99)],
        "Igiene Personale": [("Shampoo","Pantene","250ml",3.49),("Shampoo Antiforfora","Head&Shoulders","250ml",3.99),("Balsamo","L'Oréal","200ml",3.49),("Bagnoschiuma","Dove","500ml",2.99),("Sapone Mani","Dove","250ml",2.49),("Sapone Liquido","Palmolive","300ml",1.99),("Dentifricio","Colgate","75ml",1.99),("Dentifricio Sbiancante","Mentadent","75ml",2.49),("Spazzolino","Oral-B","2pz",2.99),("Collutorio","Listerine","500ml",3.99),("Deodorante Spray","Dove","150ml",2.99),("Deodorante Roll-on","Nivea","50ml",2.49),("Crema Mani","Neutrogena","75ml",3.99),("Crema Viso","Nivea","50ml",4.99),("Rasoio","Gillette","4pz",9.99),("Schiuma da Barba","Gillette","250ml",2.99)],
        "Baby e Infanzia": [("Pannolini Taglia 3","Pampers","50pz",14.99),("Pannolini Taglia 4","Pampers","46pz",12.99),("Pannolini Taglia 5","Huggies","42pz",11.99),("Salviette Umidificate","Huggies","72pz",2.99),("Latte in Polvere","Mellin","800g",19.99),("Omogeneizzato Frutta","Plasmon","4x100g",3.49),("Omogeneizzato Carne","Plasmon","2x80g",2.99),("Biscotti Baby","Plasmon","320g",2.99),("Pastina","Mellin","350g",2.49)],
        "Pet Food": [("Crocchette Cane","Purina","3kg",12.99),("Crocchette Gatto","Whiskas","1.5kg",7.99),("Scatolette Cane","Cesar","4x150g",4.99),("Scatolette Gatto","Sheba","4x85g",3.99),("Snack Cane","Pedigree","180g",2.99),("Lettiera Gatto","Catsan","5L",4.99)],
    }

    variazioni = {
        "coop-pioltello": 1.0, "esselunga-pioltello": 1.05, "lidl-pioltello": 0.85,
        "eurospin-pioltello": 0.80, "carrefour-segrate": 0.95, "penny-pioltello": 0.82,
        "md-segrate": 0.78, "conad-pioltello": 0.98, "aldi-segrate": 0.83,
        "despar-pioltello": 1.02, "unes-cernusco": 0.97, "iperal-pioltello": 1.03,
        "esselunga-gallarate-pegoraro": 1.06, "esselunga-gallarate-borri": 1.05,
        "conad-gallarate": 0.97, "coop-gallarate": 1.0, "carrefour-gallarate": 0.96,
        "lidl-gallarate": 0.84, "iperal-gallarate": 1.02, "ilgigante-gallarate": 0.99,
        "md-gallarate": 0.77,
        "conad-catania-umberto": 1.01, "conad-catania-scannapieco": 1.00,
        "deco-catania-galermo": 0.96, "deco-catania-centro": 0.98,
        "eurospin-catania": 0.82, "lidl-catania": 0.86, "ipercoop-catania": 1.04,
        "conad-palermo": 1.02, "deco-palermo": 0.97, "eurospin-palermo": 0.83,
        "lidl-palermo": 0.87, "ipercoop-palermo": 1.05,
    }

    prodotti_data = []
    for categoria, prodotti in categorie_prodotti.items():
        for nome, brand, formato, prezzo_base in prodotti:
            for sup in supermercati_data:
                variazione = variazioni[sup["id"]]
                prezzo = round(prezzo_base * variazione * random.uniform(0.95, 1.05), 2)
                in_offerta = random.random() < 0.12
                sconto = None
                prezzo_precedente = prezzo
                if in_offerta:
                    sconto = random.choice([10, 15, 20, 25, 30])
                    prezzo = round(prezzo * (1 - sconto/100), 2)
                prodotti_data.append({
                    "id": f"{nome.lower().replace(' ', '-')}-{sup['id']}",
                    "nome_prodotto": nome, "categoria": categoria, "brand": brand,
                    "formato": formato, "supermercato_id": sup["id"], "prezzo": prezzo,
                    "prezzo_precedente": prezzo_precedente if in_offerta else None,
                    "in_offerta": in_offerta, "sconto_percentuale": sconto,
                    "data_aggiornamento": datetime.now(timezone.utc).isoformat(),
                })

    await db.supermercati.delete_many({})
    await db.prodotti.delete_many({})
    await db.supermercati.insert_many(supermercati_data)
    await db.prodotti.insert_many(prodotti_data)

    await db.prodotti.create_index("nome_prodotto")
    await db.prodotti.create_index("categoria")
    await db.prodotti.create_index("supermercato_id")
    await db.prodotti.create_index("in_offerta")
    await db.prodotti.create_index("id")
    await db.utenti.create_index("email")
    await db.utenti.create_index("referral_code")
    await db.notifiche.create_index([("utente_id", 1), ("letta", 1)])
    await db.referrals.create_index("invitante_id")
    await db.liste_spesa.create_index("utente_id")

    return {"message": "Database popolato con successo",
            "supermercati": len(supermercati_data), "prodotti": len(prodotti_data),
            "categorie": len(categorie_prodotti)}
