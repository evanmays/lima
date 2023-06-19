from bs4 import BeautifulSoup
import requests
import traceback
from multiprocessing import Pool, cpu_count
# from utils import *
import os

TOKEN = "U4DMV*8nvpm3EOpvf69Rxw(("

STEM = [
    "stackoverflow",  # always do first since it's the largest
    "serverfault", "superuser", "webapps", "gaming", "webmasters", "gamedev", "stats", "math", "tex", "askubuntu",
    "unix", "wordpress", "cstheory", "softwareengineering", "electronics", "android", "physics", "dba", "scifi",
    "codereview", "codegolf", "quant", "drupal", "sharepoint", "sqa", "crypto", "dsp", "bitcoin", "linguistics",
    "scicomp", "biology", "mathematica", "psychology", "cs", "chemistry", "raspberrypi", "patents", "genealogy",
    "robotics", "expressionengine", "reverseengineering", "networkengineering", "opendata", "mathoverflow", "space",
    "sound", "astronomy", "tor", "ham", "arduiono", "cs50", "joomla", "datascience", "craftcms", "emacs", "economics",
    "engineering", "civicrm", "medicalsciences", "opensource", "elementaryos", "computergraphics", "hardwarerecs",
    "3dprinting", "ethereum", "retrocomputing" "monero", "ai", "sitecore", "iot", "devops", "bioinformatics",
    "cseducators", "iota", "stellar", "conlang", "quantumcomputing", "eosio", "tezos", "drones", "mattermodeling",
    "cardano", "proofassistants", "substrate", "bioacoustics", "solana", "lanugagedesign",
]

OTHER = [
    "meta", "cooking", "photo", "diy", "superuser", "gis", "money", "english", "stackapps", "ux", "apple", "rpg",
    "bicycles", "boardgames", "homebrew", "security", "writing", "video", "graphicdesign", "pm", "skeptics", "fitness",
    "mechanics", "parenting", "music", "judaism", "german", "japanese", "philosophy", "gardening", "travel", "french",
    "christianity", "hermeneutics" "history", "bricks", "spanish", "movies", "chinese", "poker", "outdoors",
    "martialarts", "sports", "academia", "worplace", "chess", "russian", "islam", "salesforce", "politics", "anime",
    "magento", "ell", "sustainability", "tridion", "freelancing", "blender", "bets", "italian", "pt", "aviation",
    "ebooks", "alcohol", "softwarerecs", "expatriates", "matheducators", "earthscience", "puzzling", "buddhism",
    "communitybuilding", "worldbuilding", "ja", "hsm", "lifehacks", "coffee", "vi", "musicfans", "woodworking", "ru",
    "rus", "mythology", "law", "portugese", "es", "latin", "languagelearning", "crafts", "korean", "esperanto",
    "literature", "vegetarianism", "ukrainian", "interpersonal", "or",
]

NICHE = []

ALL = STEM + OTHER + NICHE

# TODO fix the split between the sets.
# assert len(STEM) + len(OTHER) + len(NICHE) == 179, "Total sites should be 179, not " + str(len(STEM) + len(OTHER) + len(NICHE))
# assert len(STEM) == 75, "STEM sites should be 75, not " + str(len(STEM))
# assert len(OTHER) == 99, "OTHER sites should be 99, not " + str(len(OTHER))
# assert len(NICHE) == 5, "NICHE sites should be 5, not " + str(len(NICHE))
print("Stem Size", len(STEM))
print("Other Size", len(OTHER))
print("Niche Size", len(NICHE))

class Stack_Exchange_Downloader:
    def __init__(self, name):
        """
        :param name: name of stackexchange site to download.
        If all, will download all stackexchanges & metas.
        """
        sitesmap = requests.get(
            "https://ia600107.us.archive.org/27/items/stackexchange/Sites.xml"
        ).content
        self.name = (
            name.replace("http://", "")
            .replace("https://", "")
            .replace(".com", "")
            .replace(".net", "")
        )
        self.sites = {}
        self.parse_sitesmap(sitesmap)

    def parse_sitesmap(self, sitesmap):
        soup = BeautifulSoup(sitesmap, "lxml")
        for site in soup.find_all("row"):
            url = site["url"].replace("https://", "")
            site_name = site["tinyname"]
            download_link = "https://archive.org/download/stackexchange/" + url + ".7z"
            if url == "stackoverflow.com":
                download_link = "https://archive.org/download/stackexchange/stackoverflow.com-Posts.7z"
            self.sites[site_name] = {"url": url, "download": download_link}

    def download(self):
        dl_list = self.sites if self.name == "all" else {self.name: self.sites[self.name]}
        for k in dl_list:
            command = f"wget {dl_list[k]['download']} -P dumps"
            print(command)
            if os.system(command):
                raise Exception(f"Download for {k} failed!")

    def extract(self):
        extract_list = (
            self.sites if self.name == "all" else {self.name: self.sites[self.name]}
        )
        for k, site in extract_list.items():
            command = "py7zr x dumps/{} dumps/{}".format(
                site["download"].replace(
                    "https://archive.org/download/stackexchange/", ""
                ),
                k,
            )
            print(command)
            if os.system(command):
                raise Exception(f"Extraction for {k} failed!")


def download_and_process_single(name):
    try:
        name = name.strip().lower()
        os.makedirs("dumps", exist_ok=True)
        s = Stack_Exchange_Downloader(name)
        # assert set(ALL).issubset(set(s.sites.keys()))
        path_to_xml = f"dumps/{name}/Posts.xml"
        if name != "stackoverflow":
            path_to_7z = f"dumps/{s.sites[name]['url']}.7z"
        else:
            path_to_7z = "dumps/stackoverflow.com-Posts.7z"
        out_folder = f"out/{name}"
        os.makedirs(out_folder, exist_ok=True)
        if not os.path.isfile(path_to_xml):
            if not os.path.isfile(path_to_7z):
                s.download()  # download 7z if it's not downloaded already
            s.extract()  # extract 7z if it's not extracted already
            try:
                os.remove(path_to_7z)
            except FileNotFoundError:
                print(
                    "ERROR: FileNotFoundError: File {} not found".format(
                        s.sites[name]["url"]
                    )
                )
        # qa = QA_Pairer(path_to_xml, out_folder, name=name)
        # qa.main()

        # for f in os.listdir(f"dumps/{name}"):
        #     if f.endswith(".xml"):
        #         os.remove(os.path.join(f"dumps/{name}", f))
    except:
        traceback.print_exc()

SMALL_TEST = True
if __name__ == "__main__":
  if SMALL_TEST:
    download_and_process_single("stackoverflow") # useful for testing to run this and comment the below
  else:
    cpu_no = 64 # cpu_count() - 1
    p = Pool(cpu_no)
    p.map(download_and_process_single, ALL)
