#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper des couvertures officielles VF des tomes de One Piece.

Source : wiki One Piece FR (onepiece.fandom.com/fr), fichiers
« Tome_<N>_Couverture_VF_Infobox.png » hébergés sur static.wikia.nocookie.net,
téléchargés en taille originale puis convertis en JPG.

Nommage tvdb4 (Absolute Series Scanner / HAMA) :

    Season<saison><lettre>.jpg      ex. Season1a.jpg = Tome 1

  - <saison> : l'arc de tvdb4.mapping.xml (One Piece, tvdbid 81797) qui
    contient la majorité des chapitres du tome ;
  - <lettre> : le rang du tome dans cette saison (a, b, c, ..., z, aa, ab...).

Utilisation :
    python onepiece_posters.py                   # mode interactif (départ / arrivée)
    python onepiece_posters.py 1-10 25-30 91     # plusieurs plages
    python onepiece_posters.py 100-              # du tome 100 au dernier paru
    python onepiece_posters.py tout --lister     # affiche le découpage, ne télécharge rien

Dépendance : Pillow (pip install pillow) pour la conversion en JPG.
Sans Pillow, les images sont enregistrées telles quelles en PNG.
"""

import argparse
import io
import json
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:
    from PIL import Image
except ImportError:  # conversion JPG impossible, on garde le PNG d'origine
    Image = None


API = "https://onepiece.fandom.com/fr/api.php"
USER_AGENT = "OnePiecePosterScraper/1.0 (script personnel, usage non commercial)"
DOSSIER_PAR_DEFAUT = Path(__file__).resolve().parent / "posters"
FICHIER_COUVERTURE = "Fichier:Tome_{numero}_Couverture_{version}_Infobox.png"
LOT_API = 50  # nombre max de titres par requête MediaWiki

# Saisons tvdb4 de One Piece, d'après tvdb4.mapping.xml :
# (saison, premier chapitre du manga couvert par l'arc, nom de l'arc).
# Un arc anime 100 % hors-série (saison 9, « G8 ») ne couvre aucun chapitre :
# son premier chapitre vaut None et il n'aura donc aucun tome.
SAISONS = [
    (1, 1, "East Blue - Gathering the Crew"),       # Romance Dawn -> Baratie
    (2, 69, "Arlong Park"),
    (3, 96, "Entering into the Grand Line"),        # Loguetown + Reverse Mountain
    (4, 106, "Whiskey Peak and Little Garden"),
    (5, 130, "Drum Island"),
    (6, 155, "Alabasta"),
    (7, 218, "Jaya Arc"),
    (8, 237, "Skypiea"),
    (9, None, "The Naval Fortress G8"),             # hors-série anime
    (10, 303, "Davy Back Games - The Foxy Pirate Crew"),
    (11, 322, "Water Seven"),
    (12, 375, "Enies Lobby"),                       # + Post-Enies Lobby
    (13, 442, "Thriller Bark"),
    (14, 490, "Sabaody Archipelago"),
    (15, 514, "Island of Women / Amazon Lily"),
    (16, 525, "Impel Down"),
    (17, 550, "Marineford"),
    (18, 581, "Post-War Arc"),
    (19, 598, "Fishman Island"),                    # + Retour à Sabaody
    (20, 654, "Punk Hazard"),
    (21, 700, "Dressrosa"),
    (22, 802, "Zou Arc"),
    (23, 825, "Whole Cake Island Arc"),
    (24, 903, "Reverie Arc"),
    (25, 909, "Wano Arc"),
    (26, 1058, "Egg Head Island Arc"),
    (27, 1126, "Elbaph"),
]

# Pour forcer un tome dans une saison précise (prioritaire sur le calcul
# automatique). Exemple : {90: 25} range le tome 90 dans la saison 25.
FORCER_SAISON = {}

NOMS_SAISONS = {saison: nom for saison, _, nom in SAISONS}


# --------------------------------------------------------------------------- #
# Réseau
# --------------------------------------------------------------------------- #

def telecharger(url, essais=4):
    """GET avec quelques nouvelles tentatives en cas d'erreur réseau."""
    for essai in range(essais):
        try:
            requete = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(requete, timeout=120) as reponse:
                return reponse.read()
        except HTTPError as erreur:
            if erreur.code < 500 and erreur.code != 429 or essai == essais - 1:
                raise
        except (URLError, TimeoutError, ConnectionError):
            if essai == essais - 1:
                raise
        time.sleep(2 ** essai)


def api(**parametres):
    parametres.update(format="json", formatversion="2")
    return json.loads(telecharger(API + "?" + urlencode(parametres)))


def par_lots(elements, taille=LOT_API):
    elements = list(elements)
    for i in range(0, len(elements), taille):
        yield elements[i:i + taille]


# --------------------------------------------------------------------------- #
# Tomes, saisons et lettres
# --------------------------------------------------------------------------- #

def chapitres_du_tome(wikitexte):
    """Extrait (premier, dernier) chapitre du champ « chapitres » de l'infobox."""
    champ = re.search(r"^\s*\|\s*chapitres\s*=(.*)$", wikitexte, re.M | re.I)
    if not champ:
        return None
    valeur = champ.group(1)
    # Cas normal : « [[Chapitre 911|911]] à [[Chapitre 921|921]] (11 chapitres)<ref>…</ref> »
    numeros = [int(n) for n in re.findall(r"\[\[\s*Chapitre\s+(\d+)", valeur, re.I)]
    if not numeros:  # texte brut « 911 à 921 » : on retire refs et parenthèses
        valeur = re.sub(r"<ref[^>]*/>|<ref.*?(?:</ref>|$)|\(.*?\)", "", valeur)
        numeros = [int(n) for n in re.findall(r"\d+", valeur)][:2]
    return (min(numeros), max(numeros)) if numeros else None


def recuperer_tomes():
    """Renvoie {numéro de tome: (premier chapitre, dernier chapitre) ou None}
    pour tous les tomes qui ont une page sur le wiki (1, 2, 3... jusqu'au
    premier manquant)."""
    tomes = {}
    debut = 1
    while True:
        titres = ["Tome %d" % n for n in range(debut, debut + LOT_API)]
        donnees = api(action="query", prop="revisions", rvprop="content",
                      rvslots="main", titles="|".join(titres))
        dernier_lot = False
        for page in donnees["query"]["pages"]:
            numero = re.fullmatch(r"Tome (\d+)", page["title"])
            if not numero:
                continue
            numero = int(numero.group(1))
            if page.get("missing"):
                dernier_lot = True
                continue
            revisions = page.get("revisions")
            contenu = revisions[0]["slots"]["main"]["content"] if revisions else ""
            tomes[numero] = chapitres_du_tome(contenu)
        if dernier_lot:
            break
        debut += LOT_API
    # On s'arrête au premier trou : les pages au-delà sont des pages spéciales.
    resultat, numero = {}, 1
    while numero in tomes:
        resultat[numero] = tomes[numero]
        numero += 1
    return resultat


def saison_du_chapitre(chapitre):
    saison_trouvee = None
    for saison, premier, _ in SAISONS:
        if premier is not None and premier <= chapitre:
            saison_trouvee = saison
    return saison_trouvee


def lettre(rang):
    """0 -> a, 25 -> z, 26 -> aa, 27 -> ab..."""
    texte, rang = "", rang + 1
    while rang:
        rang, reste = divmod(rang - 1, 26)
        texte = chr(ord("a") + reste) + texte
    return texte


def decouper(tomes):
    """Renvoie {tome: (saison, lettre)} pour tous les tomes connus."""
    saison_par_tome = {}
    saison_precedente = 1
    for numero in sorted(tomes):
        if numero in FORCER_SAISON:
            saison = FORCER_SAISON[numero]
        elif tomes[numero]:
            premier, dernier = tomes[numero]
            # Saison majoritaire ; à égalité, la plus ancienne l'emporte.
            compte = Counter(saison_du_chapitre(c) for c in range(premier, dernier + 1))
            saison = compte.most_common(1)[0][0]
        else:
            # Chapitres inconnus (tome tout juste annoncé) : même saison que le précédent.
            saison = saison_precedente
        saison_par_tome[numero] = saison
        saison_precedente = saison

    nommage, rangs = {}, Counter()
    for numero in sorted(saison_par_tome):
        saison = saison_par_tome[numero]
        nommage[numero] = (saison, lettre(rangs[saison]))
        rangs[saison] += 1
    return nommage


# --------------------------------------------------------------------------- #
# Couvertures
# --------------------------------------------------------------------------- #

def infos_couvertures(numeros, version):
    """Renvoie {tome: imageinfo} pour les couvertures existantes (VF ou VO)."""
    infos = {}
    for lot in par_lots(numeros):
        titres = [FICHIER_COUVERTURE.format(numero=n, version=version) for n in lot]
        donnees = api(action="query", prop="imageinfo", iiprop="url|size",
                      titles="|".join(titres))
        for page in donnees["query"]["pages"]:
            numero = re.search(r"Tome[ _](\d+)[ _]", page["title"])
            if numero and page.get("imageinfo"):
                infos[int(numero.group(1))] = page["imageinfo"][0]
    return infos


def enregistrer(info, destination_sans_extension, qualite):
    """Télécharge l'image originale et l'enregistre en JPG (ou PNG sans Pillow)."""
    url = info["url"]
    # Sans « format=original », le CDN renvoie une version WebP recompressée.
    url += ("&" if "?" in url else "?") + "format=original"
    contenu = telecharger(url)

    if Image is None:
        destination = destination_sans_extension.with_suffix(".png")
        temporaire = destination.with_name(destination.name + ".part")
        temporaire.write_bytes(contenu)
    else:
        destination = destination_sans_extension.with_suffix(".jpg")
        temporaire = destination.with_name(destination.name + ".part")
        image = Image.open(io.BytesIO(contenu))
        if image.mode in ("RGBA", "LA", "P"):
            image = image.convert("RGBA")
            fond = Image.new("RGB", image.size, (255, 255, 255))
            fond.paste(image, mask=image.split()[-1])
            image = fond
        image.convert("RGB").save(temporaire, "JPEG", quality=qualite,
                                  optimize=True, progressive=True)
    os.replace(temporaire, destination)
    return destination


# --------------------------------------------------------------------------- #
# Choix des tomes
# --------------------------------------------------------------------------- #

def parser_plages(textes, dernier_tome):
    """« 1-10 25-30,91 100- tout » -> liste triée de numéros de tomes."""
    texte = " ".join(textes)
    texte = re.sub(r"\s*(?:-|à|\.\.)\s*", "-", texte)
    tomes = set()
    for morceau in re.split(r"[\s,;]+", texte.strip()):
        if not morceau:
            continue
        if morceau.lower() in ("tout", "tous", "all", "*"):
            tomes.update(range(1, dernier_tome + 1))
            continue
        plage = re.fullmatch(r"(\d*)-(\d*)|(\d+)", morceau)
        if not plage or morceau == "-":
            raise ValueError("plage invalide : « %s »" % morceau)
        if plage.group(3):
            debut = fin = int(plage.group(3))
        else:
            debut = int(plage.group(1)) if plage.group(1) else 1
            fin = int(plage.group(2)) if plage.group(2) else dernier_tome
        if debut > fin:
            debut, fin = fin, debut
        tomes.update(range(max(debut, 1), fin + 1))
    if not tomes:
        raise ValueError("aucun tome demandé")
    return sorted(tomes)


def demander_entier(question, defaut):
    while True:
        reponse = input("%s [%d] : " % (question, defaut)).strip()
        if not reponse:
            return defaut
        if reponse.isdigit() and int(reponse) >= 1:
            return int(reponse)
        print("  -> entrez un numéro de tome (nombre entier positif).")


def demander_plages(dernier_tome):
    print("Tomes disponibles sur le wiki : 1 à %d (Entrée = valeur par défaut)" % dernier_tome)
    tomes = set()
    numero_plage = 1
    while True:
        print("\nPlage n°%d" % numero_plage)
        debut = demander_entier("  Tome de départ ", 1)
        fin = demander_entier("  Tome d'arrivée", dernier_tome)
        if debut > fin:
            debut, fin = fin, debut
        tomes.update(range(debut, fin + 1))
        if input("Ajouter une autre plage ? (o/N) : ").strip().lower() not in ("o", "oui", "y", "yes"):
            return sorted(tomes)
        numero_plage += 1


# --------------------------------------------------------------------------- #
# Programme principal
# --------------------------------------------------------------------------- #

def main():
    analyseur = argparse.ArgumentParser(
        description="Télécharge les couvertures VF des tomes de One Piece "
                    "nommées au format tvdb4 (Season1a.jpg = Tome 1).")
    analyseur.add_argument("plages", nargs="*",
                           help="tomes à télécharger : 1-10 25-30 91 100- ou « tout » "
                                "(sans argument : mode interactif)")
    analyseur.add_argument("-d", "--dossier", type=Path, default=DOSSIER_PAR_DEFAUT,
                           help="dossier de destination (défaut : %(default)s)")
    analyseur.add_argument("-l", "--lister", action="store_true",
                           help="affiche le découpage tome -> saison sans rien télécharger")
    analyseur.add_argument("--vo", action="store_true",
                           help="si la couverture VF n'existe pas encore, prendre la VO")
    analyseur.add_argument("-f", "--ecraser", action="store_true",
                           help="retélécharge les images déjà présentes")
    analyseur.add_argument("-q", "--qualite", type=int, default=95,
                           help="qualité JPEG de 1 à 100 (défaut : %(default)s)")
    args = analyseur.parse_args()

    print("Lecture de la liste des tomes sur le wiki One Piece FR...")
    tomes = recuperer_tomes()
    if not tomes:
        sys.exit("Impossible de lire la liste des tomes sur le wiki.")
    dernier_tome = max(tomes)
    nommage = decouper(tomes)

    try:
        demandes = parser_plages(args.plages, dernier_tome) if args.plages else demander_plages(dernier_tome)
    except ValueError as erreur:
        sys.exit("Erreur : %s (exemple valide : 1-10 25-30 91 100-)" % erreur)
    except (KeyboardInterrupt, EOFError):
        sys.exit("\nAnnulé.")

    inexistants = [n for n in demandes if n not in tomes]
    demandes = [n for n in demandes if n in tomes]
    if inexistants:
        print("Ignorés (pas encore de page sur le wiki) : tomes %d à %d"
              % (inexistants[0], inexistants[-1]) if len(inexistants) > 1
              else "Ignoré (pas encore de page sur le wiki) : tome %d" % inexistants[0])
    if not demandes:
        sys.exit("Aucun tome à traiter.")

    if args.lister:
        for numero in demandes:
            saison, suffixe = nommage[numero]
            chapitres = tomes[numero]
            print("Tome %3d  ch. %-11s -> Season%d%s.jpg  (%s)" % (
                numero, "%d-%d" % chapitres if chapitres else "?",
                saison, suffixe, NOMS_SAISONS.get(saison, "?")))
        return

    if Image is None:
        print("Attention : Pillow n'est pas installé, les images seront enregistrées en PNG.\n"
              "            Pour du JPG : pip install pillow")
    args.qualite = min(max(args.qualite, 1), 100)
    args.dossier.mkdir(parents=True, exist_ok=True)
    extension = ".jpg" if Image else ".png"

    a_telecharger = []
    deja_presents = 0
    for numero in demandes:
        saison, suffixe = nommage[numero]
        cible = args.dossier / ("Season%d%s" % (saison, suffixe))
        if cible.with_suffix(extension).exists() and not args.ecraser:
            deja_presents += 1
        else:
            a_telecharger.append(numero)

    print("Recherche des couvertures VF...")
    infos = {n: (info, "VF") for n, info in infos_couvertures(a_telecharger, "VF").items()}
    manquants = [n for n in a_telecharger if n not in infos]
    if manquants and args.vo:
        infos.update({n: (info, "VO") for n, info in infos_couvertures(manquants, "VO").items()})

    print("Destination : %s\n" % args.dossier)
    telecharges, echecs, sans_couverture = 0, [], []
    for numero in a_telecharger:
        saison, suffixe = nommage[numero]
        nom = "Season%d%s" % (saison, suffixe)
        if numero not in infos:
            sans_couverture.append(numero)
            print("Tome %3d -> %-14s pas de couverture VF sur le wiki%s"
                  % (numero, nom, "" if args.vo else " (option --vo pour la VO)"))
            continue
        info, version = infos[numero]
        try:
            fichier = enregistrer(info, args.dossier / nom, args.qualite)
        except Exception as erreur:  # on continue avec les tomes suivants
            echecs.append(numero)
            print("Tome %3d -> %-14s ÉCHEC : %s" % (numero, nom, erreur))
            continue
        telecharges += 1
        print("Tome %3d -> %-14s %s %dx%d" % (numero, fichier.name, version,
                                             info.get("width", 0), info.get("height", 0)))
        time.sleep(0.5)  # politesse envers le CDN

    print("\nTerminé : %d téléchargé(s), %d déjà présent(s)%s%s." % (
        telecharges, deja_presents,
        ", %d sans couverture" % len(sans_couverture) if sans_couverture else "",
        ", %d échec(s)" % len(echecs) if echecs else ""))
    if deja_presents and not args.ecraser:
        print("(option --ecraser pour retélécharger les images déjà présentes)")


if __name__ == "__main__":
    main()
