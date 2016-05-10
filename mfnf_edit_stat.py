import requests
import itertools

from datetime import datetime

API_URL="https://de.wikibooks.org/w/api.php"

def wb_query(params):
    params["action"] = "query"
    params["format"] = "json"

    return requests.get(API_URL, params=params).json()

def wb_list(method, params):
    params["list"] = method
    result = []

    while True:
        api_result = wb_query(params)

        result.extend(api_result["query"][method])

        if "continue" in api_result:
            params.update(api_result["continue"])
        else:
            return result


def mfnf_all_pages():
    return wb_list("allpages", { "apprefix": "Mathe für Nicht-Freaks", "aplimit": 1000 })

def edits_for_page(articleid):
    result = []
    params = {
        "prop": "revisions",
        "pageids": articleid,
        "rvprop": "ids|timestamp|user|size",
        "rvlimit": 500,
        "rvdir": "newer"
    }

    while True:
        api_result = wb_query(params)

        result.extend(api_result["query"]["pages"][str(articleid)]["revisions"])

        if "continue" in api_result:
            params.update(api_result["continue"])
        else:
            return result

def mfnf_all_edits():
    for article in mfnf_all_pages():
        print(article["title"])
        edits = edits_for_page(article["pageid"])

        assert len(edits) > 0

        edits[0]["diffsize"] = edits[0]["size"]
        for i in range(1, len(edits)):
            edits[i]["diffsize"] = max(edits[i]["size"]-edits[i-1]["size"],0)

        for edit in edits:
            edit["title"] = article["title"]
            edit["timestamp"] = datetime.strptime(edit["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
            yield edit

def mfnf_50euro_edits():
    edits_by_user = dict()

    for edit in mfnf_all_edits():
        if edit["timestamp"] > datetime(2015,5,11):
            if edit["user"] not in edits_by_user:
                edits_by_user[edit["user"]] = []

            edits_by_user[edit["user"]].append(edit)

    for user, edits in edits_by_user.items():
        edits.sort(key = lambda x : x["timestamp"])

        r = []

        for edit in edits:
            r.append(edit)

            if sum(map(lambda x: x["diffsize"], r)) > 15000:
                yield r
                r = []

def log_50euro_edits():
    def fmtedit(edit):
        u = "https://de.wikibooks.org/w/index.php?oldid="
        result = ""

        result += "[" + u + str(edit["revid"])
        result += " " + datetime.strftime(edit["timestamp"], "%d.%m.%Y %H:%M") + "]"

        return result

    def fmttitles(edits):
        titles = set(map(lambda x: x["title"], edits))

        return ", ".join(map(lambda x:
                "[[" + x + "|" + x.replace("Mathe für Nicht-Freaks: ", "") + "]]",
            titles))

    edits = list(mfnf_50euro_edits())

    edits.sort(key = lambda x: x[-1]["timestamp"])

    n = 0

    with open("50euro_stat.txt", "w") as f:
        f.write('{| class="wikitable sortable"\n')
        f.write('! Nr\n')
        f.write('! Autor\n')
        f.write('! Beleg\n')
        f.write('! Bearbeitete Artikel\n')

        for e in itertools.islice(edits, 100):
            n += 1
            f.write("|-\n")
            f.write("| %s\n" % n)
            f.write("| [[Benutzer:%s|%s]]\n" % (e[0]["user"], e[0]["user"]))
            f.write("| [[Spezial:Beiträge/%s|Benutzerbeiträge]]" % e[0]["user"])
            f.write(" von %s" % fmtedit(e[0]))
            f.write(" bis %s" % fmtedit(e[-1]))
            f.write("\n| ")
            f.write(fmttitles(e))
            f.write("\n")

        f.write("|}")

def show_stats():
    result = 0
    users = set()
    for edit in mfnf_all_edits():
        result += 1
        users.add(edit["user"])
    print("Autoren: %s" % users)
    print("Anzahl Autoren: %s" % len(users))
    print("Bearbeitungen: %s" % result)
    print("Artikelanzahl: %s" % len(list(mfnf_all_pages())))

def new_articles_since(start):
    articles = mfnf_all_pages()

    def article_time(article):
        rev = edits_for_page(article["pageid"])[0]

        return datetime.strptime(rev["timestamp"], "%Y-%m-%dT%H:%M:%SZ")

    return len(list(filter(lambda x: x > start, map(article_time, articles))))

if __name__ == "__main__":
    #log_50euro_edits()
    print(new_articles_since(datetime(2016, 1, 1)))
