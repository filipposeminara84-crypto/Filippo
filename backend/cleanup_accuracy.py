"""One-off accuracy cleanup: chains, non-supermarkets, synthetic offers, DC categories."""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne
from dotenv import load_dotenv
from store_discovery import _identify_chain, _is_excluded
from catalog_generator import TERM_TO_CATEGORY

load_dotenv()


async def main():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]

    # 0) Remove fictional seed stores (approximate coordinates) + their products
    seed_stores = await db.supermercati.find({'fonte': {'$ne': 'osm'}}, {'_id': 0, 'id': 1, 'nome': 1}).to_list(200)
    seed_ids = [s['id'] for s in seed_stores]
    if seed_ids:
        r1 = await db.supermercati.delete_many({'id': {'$in': seed_ids}})
        r2 = await db.prodotti.delete_many({'supermercato_id': {'$in': seed_ids}})
        print(f"0) Removed {r1.deleted_count} seed stores, {r2.deleted_count} products")

    # 1) Remove non-supermarket POIs (drugstores, cash&carry, malls) + their products
    stores = await db.supermercati.find({'fonte': 'osm'}, {'_id': 0, 'id': 1, 'nome': 1, 'catena': 1}).to_list(5000)
    excluded_ids = {s['id'] for s in stores if _is_excluded(s['nome'])}
    if excluded_ids:
        r1 = await db.supermercati.delete_many({'id': {'$in': list(excluded_ids)}})
        r2 = await db.prodotti.delete_many({'supermercato_id': {'$in': list(excluded_ids)}})
        removed_names = sorted({s['nome'] for s in stores if s['id'] in excluded_ids})
        print(f"1) Removed {r1.deleted_count} non-supermarket POIs, {r2.deleted_count} products")
        print(f"   Names: {removed_names}")

    # 2) Reclassify chains with word-boundary matching
    fixed = 0
    for s in stores:
        if s['id'] in excluded_ids:
            continue
        new_chain = _identify_chain(s['nome'])
        if new_chain != s['catena']:
            await db.supermercati.update_one({'id': s['id']}, {'$set': {'catena': new_chain}})
            print(f"   Chain fix: {s['nome']!r}: {s['catena']!r} -> {new_chain!r}")
            fixed += 1
    print(f"2) Reclassified {fixed} store chains")

    # 3) Disable synthetic offers (non-doveconviene), restoring pre-discount price
    fake = await db.prodotti.find(
        {'in_offerta': True, 'fonte_prezzo': {'$ne': 'doveconviene'}},
        {'_id': 0, 'id': 1, 'prezzo': 1, 'prezzo_precedente': 1}
    ).to_list(100000)
    ops = []
    for p in fake:
        prezzo = p.get('prezzo_precedente') or p['prezzo']
        ops.append(UpdateOne({'id': p['id']}, {'$set': {
            'prezzo': prezzo, 'in_offerta': False,
            'sconto_percentuale': None, 'prezzo_precedente': None,
        }}))
    if ops:
        res = await db.prodotti.bulk_write(ops)
        print(f"3) Disabled {res.modified_count} synthetic offers (restored original prices)")
    else:
        print("3) No synthetic offers found")

    # 4) Remap DC categories (search_term -> standard) + extract brand from "Brand - Product"
    dc = await db.prodotti.find(
        {'fonte_prezzo': 'doveconviene'},
        {'_id': 0, 'id': 1, 'nome_prodotto': 1, 'categoria': 1, 'brand': 1}
    ).to_list(200000)
    ops = []
    for p in dc:
        upd = {}
        cat = p.get('categoria', '')
        if cat in TERM_TO_CATEGORY:
            upd['categoria'] = TERM_TO_CATEGORY[cat]
        nome = p.get('nome_prodotto', '')
        if ' - ' in nome and not p.get('brand'):
            brand, prod_name = nome.split(' - ', 1)
            upd['brand'] = brand
            upd['nome_prodotto'] = prod_name
        if upd:
            ops.append(UpdateOne({'id': p['id']}, {'$set': upd}))
    if ops:
        res = await db.prodotti.bulk_write(ops)
        print(f"4) Fixed {res.modified_count} DC products (category/brand)")
    else:
        print("4) DC products already clean")

    total_stores = await db.supermercati.count_documents({})
    total_offers = await db.prodotti.count_documents({'in_offerta': True})
    dc_offers = await db.prodotti.count_documents({'in_offerta': True, 'fonte_prezzo': 'doveconviene'})
    print(f"FINAL: stores={total_stores} (all OSM real), offers={total_offers}, real_doveconviene={dc_offers}")


asyncio.run(main())
