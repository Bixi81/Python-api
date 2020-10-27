from bs4 import BeautifulSoup 
import os, re, glob
from os.path import basename
import pandas as pd
from pandas import ExcelWriter
from string import digits
import string
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn import preprocessing
from sklearn import model_selection
from sklearn.linear_model import LogisticRegressionCV
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import TfidfVectorizer

# Lokale HTML laden
mypath = "C:\\Users\\User\\Documents\\Python\\konzernabschluss\\html\\0test\\"
mypath = "C:\\Users\\User\\Documents\\Python\\konzernabschluss\\html\\"
myfiles = glob.glob(mypath + "*.html")

# Lade Modell (Anteilsliste)
with open(mypath + "clf_anteilsliste.pkl", 'rb') as f:
    clf = pickle.load(f)

# Lade transformer
tf1 = pickle.load(open(mypath + "tfidf_anteilsliste.pkl", 'rb'))
tf1_new = TfidfVectorizer(analyzer='word', ngram_range=(1,2), lowercase = True, max_features = 20000, vocabulary = tf1.vocabulary_)

# Funktion um Strings aufzubereiten
def cleantext(mystring):
    mystring = str(mystring)
    mystring = mystring.replace("\n", "").replace("\r", "").replace("-", " ")
    mystring = mystring.lower()
    mystring = ''.join([i for i in mystring if not i.isdigit()])
    mystring = mystring.replace("ä","ae").replace("ö","oe").replace("ü","ue").replace("ß","ss").replace(";",",")
    mystring = mystring.translate(str.maketrans(' ', ' ', string.punctuation))
    mystring = ' '.join(mystring.split())
    return mystring

myglobalheaderlist = []
myglobalheaderlist_0 = []

for f in myfiles:
    ###########################################
    # Für jede HTML-Datei -> Laden
    filename = basename(f)
    filename = filename[:filename.rfind(".")]
    with open(f, "r", encoding="UTF-8") as ff:
        content = ff.read()
    ###########################################
    # Metadata
    # Inhalte auslesen -> Überschriften
    soup = BeautifulSoup(content, 'lxml')
    titles = soup.find_all("h3", {"class":"z_titel"})
    titles2 = soup.find_all("h3", {"class":"l_titel"})
    headers = soup.find_all("h4", {"class":"z_titel"})
    # Name des Unternehmens
    c_name = cleantext(titles[0].text) 
    c_name = c_name.replace(" ", "_")
    c_name = c_name.replace("aktiengesellschaft", "ag")
    c_name = c_name.replace("kommanditgesellschaft", "kg")
    # Shorten company name
    c_name_short = c_name[:20]
    # Ort
    c_ort = cleantext(headers[0].text)
    # Art des Dokuments
    c_type = cleantext(titles2[0].text)
    # Datum
    try:
        match = re.findall(r'\d{2}.\d{2}.\d{4}', c_type)
        if len(match)>0:
            if len(match)==1:
                c_zum = match[0]
            if len(match)==2:
                c_von = match[0]
                c_bis = match[1]
        if len(match)==0:
            match = re.findall(r'\d{4}', c_type)
            if len(match)>0:
                c_zum = match[0]
    except:
        pass
    print(" ===========> %s" %c_name)
    ###########################################
    # Tabellen finden und Inhalte lesen
    outertables = soup.find_all("div", {'class':'table-scroll-wrapper'}) # Äußere Tabelle
    nn = 1
    for table in outertables:
        ### Eigentliche (innere) Tabelle mit Tabelleninhalt
        t = table.find_all("table", {'class':'std_table'}) 
        ## WENN Länge t = 1 -> Tabelle / WENN Länge t = 0 -> Liste mit "Bulletpoints"
        if len(t)==1:
            # Elemente vor und nach der Tabelle finden um ggf. Beschreibung der Tabelle abzugreifen
            # Derzeit nur Inhalte vor der Tabelle
            #siblings = table.find_next_siblings()
            previous = table.find_previous_siblings()
            pre1 = ""
            pre2 = ""
            pre3 = ""
            if len(previous)>0:
                pre1 = cleantext(previous[0].text)
                pre1 = pre1[:100]
                pre1_raw = previous[0].text
            if len(previous)>1:
                pre2 = cleantext(previous[1].text)
                pre2 = pre2[:100]
                pre2_raw = previous[1].text
            # Category
            if previous[1].name=="h4" or previous[1].name=="h3" or previous[1].name=="p":
                cat = pre1 + " | " + pre2 
            else:
                cat = pre1
            cat = cleantext(cat)

            ###########################################
            # Spalten und Zellen der Tabelle(n) finden
            # Inhalte auslesen und zu Textkörper zusammenfügen
            rows = t[0].find_all('tr')
            nrows = len(rows)
            mycontent = ""
            collist = []
            for row in rows:
                cells = row.find_all("td")
                ncells = len(cells)
                collist.append(ncells)
                #print("R %s C %s" %(nrows,ncells))
                for cell in cells:
                    #print(cell.text)
                    mycontent = mycontent + " " + str(cell.text) +" "
                    #print(cell.text)
            # Textcontent
            mycontent = cleantext(mycontent)
            # Text -> "Header" und "Tabellentext" wird zur Vorhersage des Inhalts der Tabelle genutzt
            totalcontent = str(cat) + " " + str(mycontent)

            ###########################################
            # Setze DF manuell
            outfile = open(mypath+"temp_table.csv", 'w', newline='', encoding='utf8')
            rows = t[0].find_all('tr')
            for row in rows:
                cells = row.find_all("td")
                for cell in range(0,max(collist)):
                    # FALL: In dieser Zeile weniger Spalten als maximal vorhanden
                    if len(cells) == ((max(collist)/2)-1):
                        # Erste Spale in diesem Fall frei Lassen (ist normalerweise Index-Spalte)
                        cellcount = 0
                        if cell == 1:
                            outfile.write("ooo;")
                        # Even
                        if (cell & 1) == 0:
                            cellcontent = cells[cellcount].text
                            # Replace linebreak etc
                            cellcontent = cellcontent.replace("\n","").replace("\r","").replace(";"," ")
                            # Fill empty cells with zero (to preserve numeric)
                            if cellcontent == "":
                                cellcontent = "0"
                            # Check numeric and replace decimal delim
                            checkcontent = cellcontent
                            checkcontent = checkcontent.replace(".","").replace(",","").replace("EUR","").replace("€","").replace("-","").replace("*","").replace("%","")
                            if checkcontent.isdigit() == True:
                                cellcontent = cellcontent.replace(".", "")
                                cellcontent = cellcontent.replace(",", ".")
                            outfile.write(cellcontent + ";")
                            cellcount = cellcount+1
                        # Odd
                        if (cell & 1) == 1:
                            outfile.write("ooo;")

                    # FALL: Spalten = max. Spalten (normaler Fall)
                    if len(cells) == max(collist):
                        cellcontent = cells[cell].text
                        # Replace linebreak etc
                        cellcontent = cellcontent.replace("\n","").replace("\r","").replace(";"," ")
                        # Fill empty cells with zero (to preserve numeric)
                        if cellcontent == "":
                            cellcontent = "0"
                        # Check numeric and replace decimal delim
                        checkcontent = cellcontent
                        checkcontent = checkcontent.replace(".","").replace(",","").replace("EUR","").replace("€","").replace("-","").replace("*","").replace("%","")
                        if checkcontent.isdigit() == True:
                            cellcontent = cellcontent.replace(".", "")
                            cellcontent = cellcontent.replace(",", ".")
                        outfile.write(cellcontent + ";")
                        #print(cellcontent)
                    
                    # Sonstiges Format (bisher nicht aufgearbeitet -> Zeile wird nicht übernommen)
                    else:
                        pass

                outfile.write("\n")
            outfile.close()
            try:
                # DF Name
                tname = ""
                if len(pre1_raw)<3:
                    tname = pre2_raw
                else: 
                    tname = pre1_raw
                    if len(pre2_raw)<100:
                        tname = pre2_raw + "_" +  tname
                # Remove short words
                #tname = ' '.join(word for word in tname.split() if len(word)>2)
                # Replace
                tname = tname.replace("€", "EUR").replace("scrollen", "").replace("\n", "").replace("\r", "")
                tname = re.sub(r"\W+|_", " ", tname)
                tname = ' '.join(tname.split())
                tname = tname.replace(" ", "_")
                tname = tname.lower()
                # Shorten & prefix
                tname = "_" + tname[:130]
                # Lese DF als Pandas
                df = pd.read_csv(mypath+"temp_table.csv", sep=';')
                df = df.dropna(axis=1, how='all')
                # Get table headers to check content
                header = list(df.columns.values)
                header = ' '.join(header)
                header = header.lower()


                # TEMP append header entries to check all results
                

                #print(min(collist), max(collist))
                #print(df.columns.tolist())
                #print(c_name_short,str(nn),tname)
                filenamelist = ["konsolidierungskreis","anteilen_an_verbundenen_unternehmen","anteilsbe","beteiligungsbe","konsolidierte_tochter","konsolidierten_tochter","konsolidierte_bet","konsolidierten_bet","konsolidierte_unt","konsolidierten_unt","konsolidierte_ges", "konsolidierten_ges" ,"konsolidierte_ver" , "konsolidierten_ver" ,"anteile_an_beteiligung" ,"erbundene_unternehme" , "anteil_am_kapital" ,"assoziierte_unternehmen", "gemeinschaftsunternehmen"]
                headerlist = ["nicht konsolidierte","konsolidierte tochter","beteiligungsanteil","direkter anteil","vollkonsolidierte gesellsch","name und rechtsform","name, rechtsform","konzernanteile am kapital","verbundene unternehmen","name und sitz","company code","name, rechtsform, sitz","lokale währung", "name des unternehmens", "sitz des unternehmens","sitz der gesellschaft","name der gesellschaft","name und sitz der gesellschaft","anteil am kapital", "konsolidierte gesellschaften", "sitz der gesellschaft", "mittelbarer anteil", "unmittelbarer anteil"]
                if any(ext in tname for ext in filenamelist):
                    df.to_excel(mypath+"tables_anteilsbesitz//"+c_name_short+"_ANT_FN_"+str(nn)+tname+".xlsx",index=False)
                    for en in list(df.columns.values):
                        en = ' '.join(en.split())
                        myglobalheaderlist.append(en.lower())
                elif any(ext in header for ext in headerlist):
                    df.to_excel(mypath+"tables_anteilsbesitz//"+c_name_short+"_ANT_HE_"+str(nn)+tname+".xlsx",index=False)
                else:
                    df.to_excel(mypath+"tables//"+c_name_short+"_"+str(nn)+tname+".xlsx",index=False)
                    for en in list(df.columns.values):
                        myglobalheaderlist_0.append(en.lower())
            except Exception as e:
                print(e)
                pass
             
            os.remove(mypath+"temp_table.csv")
            nn = nn+1

print(set(myglobalheaderlist))

