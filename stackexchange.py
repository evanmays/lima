from bs4 import BeautifulSoup
import math
import jsonlines
import requests
import traceback
from multiprocessing import Pool, cpu_count
import os, re
import xml.etree.ElementTree as etree
from collections import defaultdict
from tqdm import tqdm
import numpy as np

TOKEN = "U4DMV*8nvpm3EOpvf69Rxw(("

STEM = [
    "stackoverflow",  # always do first since it's the largest
    "serverfault", "superuser", "webapps", "gaming", "webmasters", "gamedev", "stats", "math", "tex", "askubuntu",
    "unix", "wordpress", "cstheory", "softwareengineering", "electronics", "android", "physics", "dba", "scifi",
    "codereview", "codegolf", "quant", "drupal", "sharepoint", "sqa", "crypto", "dsp", "bitcoin", "linguistics",
    "scicomp", "biology", "mathematica", "psychology", "cs", "chemistry", "raspberrypi", "patents", "genealogy",
    "robotics", "expressionengine", "reverseengineering", "networkengineering", "opendata", "mathoverflow", "space",
    "sound", "astronomy", "tor", "ham", "arduino", "cs50", "joomla", "datascience", "craftcms", "emacs", "economics",
    "engineering", "civicrm", "health", "opensource", "elementaryos", "computergraphics", "hardwarerecs",
    "3dprinting", "ethereum", "retrocomputing", "monero", "ai", "sitecore", "iot", "devops", "bioinformatics",
    "cseducators", "iota", "stellar", "conlang", "quantumcomputing", "eosio", "tezos", "drones", "materials",
    "cardano", "proofassistants", "substrate", "bioacoustics", "solana", "languagedesign",
]

OTHER = [
    "cooking", "photo", "diy", "superuser", "gis", "money", "english", "stackapps", "ux", "apple", "rpg",
    "bicycles", "boardgames", "homebrew", "security", "writers", "avp", "graphicdesign", "pm", "skeptics", "fitness",
    "mechanics", "parenting", "music", "judaism", "german", "japanese", "philosophy", "gardening", "travel", "french",
    "christianity", "hermeneutics", "history", "bricks", "spanish", "movies", "chinese", "poker", "outdoors",
    "martialarts", "sports", "academia", "workplace", "chess", "russian", "islam", "salesforce", "politics", "anime",
    "magento", "ell", "sustainability", "tridion", "freelancing", "blender", "italian", "pt", "aviation",
    "ebooks", "beer", "softwarerecs", "expatriates", "matheducators", "earthscience", "puzzling", "buddhism",
    "moderators", "worldbuilding", "ja", "hsm", "lifehacks", "coffee", "vi", "musicfans", "woodworking", "ru",
    "rus", "mythology", "law", "portuguese", "es", "latin", "languagelearning", "crafts", "korean", "esperanto",
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

def header_info(xml_path):
    os.system("head {}".format(xml_path))


def handle_unicode_errors(txt):
    return txt.encode('utf-8', 'replace').decode()


def is_question(elem_attribs):
    if elem_attribs["PostTypeId"] is not None:
        if elem_attribs["PostTypeId"] == "1":
            return True
    return False


def is_answer(elem_attribs):
    if elem_attribs["PostTypeId"] is not None:
        if elem_attribs["PostTypeId"] == "2":
            return True
    return False


def filter_newlines(text):
    return re.sub("\n{3,}", "\n\n", text)


def is_accepted_answer(a_attribs, q_attribs):
    assert is_question(q_attribs), "Must be a question to have an accepted answer"
    assert is_answer(a_attribs), "Must be an answer to be an accepted answer"
    if q_attribs["AcceptedAnswerId"] is not None:
        if q_attribs["AcceptedAnswerId"] == a_attribs["Id"]:
            return True
    else:
        return False


def has_answers(elem_attribs):
    assert is_question(elem_attribs), "Must be a question to have answers"
    if elem_attribs["AnswerCount"] is not None:
        if int(elem_attribs["AnswerCount"]):
            return True
    return False


def trim_attribs(elem_attribs, attrib_type="question"):
    """deletes non-useful data from attribs dict for questions / answers, returns remaining"""
    if attrib_type == "question":
        to_keep = ['Id', 'Body', 'Title', 'Tags', 'AnswerCount', 'AcceptedAnswerId', 'PostTypeId', 'Score']
        to_delete = [x for x in elem_attribs.keys() if x not in to_keep]
        [elem_attribs.pop(x, None) for x in to_delete]
        elem_attribs["ParsedAnswers"] = 0
        elem_attribs["Answers"] = {}
    elif attrib_type == "answer":
        to_keep = ['Id', 'Body', 'Score']
        new_dict = {}
        for item in to_keep:
            new_dict[item] = elem_attribs[item]
        return new_dict
    else:
        raise Exception('Unrecognized attribute type - please specify either question or answer')

class QA_Pairer():

    def __init__(self, xml_path, name=None, out_folder="out"):
        """Makes a text dataset from StackExchange dumps"""
        self.xml_path = xml_path
        if name is None:
            self.name = os.path.dirname(xml_path).replace("dumps/", "")
        else:
            self.name = name
        # dict to save questions
        self.questions = defaultdict(lambda: None, {})
        # folder to save txt files to
        self.out_folder = out_folder
        self.output_buffer = []

    def questions_count(self):
        count = 0
        for event, elem in tqdm(etree.iterparse(self.xml_path, events=('end',)), desc="Parsing {} XML file".format(self.name)):
            if elem.tag == "row":
                attribs = defaultdict(lambda: None, elem.attrib)
                if is_question(attribs):
                    count += 1
        return count
    def main(self):
        """iterates through SE xmls and:

        - stores PostTypeId="1" with AcceptedAnswerIds / Answers.
        - when an AcceptedAnswerId or Answer > min_score is reached, it should:
            > concat the Question & Accepted answer
            > Clean markup / HTML
            > Output to txt file
            > Delete from memory

        """
        os.makedirs(self.out_folder, exist_ok=True)
        for event, elem in tqdm(etree.iterparse(self.xml_path, events=('end',)), desc="Parsing {} XML file".format(self.name)):
            if len(self.output_buffer) > 1000:
                break # we'll do some manual filtering from here to get down to our actual dataset.
            if elem.tag == "row":
                try:
                    attribs = defaultdict(lambda: None, elem.attrib)
                    if is_question(attribs):
                        if has_answers(attribs):
                            trim_attribs(attribs, "question")
                            self.questions[attribs["Id"]] = attribs
                        else:
                            # if the question has no answers, discard it
                            continue
                    elif is_answer(attribs):
                        self.add_answer(attribs)
                        self.check_complete(attribs)
                    elem.clear() # saves memory... these are big XML files
                except:
                    traceback.print_exc()
        output = sorted(self.output_buffer, key=lambda x: x['question_score'], reverse=True)
        jsonlines.open(f"json-out/{self.name}.jsonl", mode='w').write_all(output)

    def add_answer(self, a_attribs):
        """
        Adds answer to its parent question in self.questions if it's either an accepted answer or above self.min_score.
         If answer is an accepted answer, it gets appended to the AcceptedAnswer field, otherwise it gets appended to
         OtherAnswers.

         Also increments the question's 'ParsedAnswers' field. When ParsedAnswers = AnswerCount, the question is deleted
         from memory and saved to a text file.

        :param a_attribs: Answer's attribute dict
        """
        assert is_answer(a_attribs), "Must be an answer to add to parent"
        if a_attribs is not None and self.questions[a_attribs["ParentId"]] is not None:
            if is_accepted_answer(a_attribs, self.questions[a_attribs["ParentId"]]):
                self.questions[a_attribs["ParentId"]]["Answers"][a_attribs["Id"]] = trim_attribs(a_attribs, "answer")
                self.questions[a_attribs["ParentId"]]["ParsedAnswers"] += 1
            else:
                # TODO why might an answer not have a score?
                assert "Score" in a_attribs and a_attribs["Score"]
                # score = int(a_attribs["Score"]) if a_attribs["Score"] is not None else 0
                if a_attribs["Id"] is not None:
                    parent = self.questions[a_attribs["ParentId"]]
                    if parent is not None:
                        self.questions[a_attribs["ParentId"]]["Answers"][a_attribs["Id"]] = trim_attribs(a_attribs, "answer")
                        self.questions[a_attribs["ParentId"]]["ParsedAnswers"] += 1
                else:
                    # TODO why would an answer not have an ID?
                    self.questions[a_attribs["ParentId"]]["ParsedAnswers"] += 1

    def check_complete(self, a_attribs):
        """
        checks if the parent question of the previously added answer has no future answers, and if so,
        removes from dict and prints to file.
        """
        parent = self.questions[a_attribs["ParentId"]]
        if a_attribs is not None and parent is not None:
            assert "Score" in parent, parent
            if parent["AnswerCount"] is not None and parent["ParsedAnswers"] is not None:
                if int(parent["ParsedAnswers"]) == int(parent['AnswerCount']):
                    self.questions.pop(a_attribs["ParentId"], None)
                    if parent["Answers"] is not None and len(parent["Answers"]) > 0:
                        if parent["Title"] is not None:
                            title_str = BeautifulSoup(parent["Title"], "lxml").get_text()
                        if parent["Body"] is not None:
                            body_str = BeautifulSoup(parent["Body"], "lxml").get_text()
                        if parent["Answers"] is not None:
                            ans_obj = max(parent["Answers"].values(), key=lambda item: int(item["Score"]))
                            ans = BeautifulSoup(ans_obj["Body"], "lxml").get_text()
                            ans_score = int(ans_obj["Score"])
                            if len(ans) < 1200 or len(ans) > 4096 or ans_score < 10:
                                return
                        try:
                            self.output_buffer.append({
                                'title': filter_newlines(title_str) if parent["Title"] is not None else "",
                                'description': filter_newlines(body_str) if parent["Body"] is not None else "",
                                'answer': filter_newlines(ans) if parent["Answers"] is not None else "",
                                'question_score': parent["Score"],
                                'answer_score': ans_score
                            })
                        except:
                            self.output_buffer.append({
                                'title': filter_newlines(handle_unicode_errors(BeautifulSoup(parent["Title"], "html.parser").get_text())) if parent["Title"] is not None else "",
                                'description': filter_newlines(handle_unicode_errors(BeautifulSoup(parent["Body"], "html.parser").get_text())) if parent["Body"] is not None else "",
                                'answer': filter_newlines(handle_unicode_errors(ans)) if parent["Answers"] is not None else "",
                                'question_score': parent["Score"],
                                'answer_score': ans_score
                            })

def download_and_process_single(name):
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
    qa = QA_Pairer(path_to_xml, out_folder=out_folder, name=name)
    qa.main()

    # for f in os.listdir(f"dumps/{name}"):
    #     if f.endswith(".xml"):
    #         os.remove(os.path.join(f"dumps/{name}", f))

def cnt(name):
    name = name.strip().lower()
    s = Stack_Exchange_Downloader(name)
    # assert set(ALL).issubset(set(s.sites.keys()))
    path_to_xml = f"dumps/{name}/Posts.xml"
    qa = QA_Pairer(path_to_xml, out_folder="blahblahblah", name=name)
    return qa.questions_count()

SMALL_TEST = False
if __name__ == "__main__":
#   if SMALL_TEST:
#     download_and_process_single("webapps") # useful for testing to run this and comment the below
#   else:
#     cpu_no = cpu_count() - 1
#     p = Pool(cpu_no)
#     p.map(download_and_process_single, OTHER)

    sizes = Pool(47).map(cnt, OTHER)
    r = Pool(47).map(cnt, OTHER)

    # how do we do sampling here? softmax will just push the biggest community to 1.0...
    # print(softmax(r, temperature=3.0))

    # this sampling does not follow the paper. not sure how they did it...
    r = np.array(r)
    desired_counts = list((r / r.sum() * 200).astype(np.int32))
    ord = sorted(zip(range(len(desired_counts)), desired_counts), key=lambda item:item[1])
    for i in range(200 - sum(desired_counts)):
        desired_counts[ord[i % len(ord)][0]] += 1
    print(list(zip(OTHER, desired_counts)))