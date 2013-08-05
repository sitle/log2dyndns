#!/usr/bin/python
#
# Version OBJET
#
import re
import random
import mechanize 
from BeautifulSoup import BeautifulSoup
import socket # pour interrogation dns
import urllib # pour l'update, mechanize bug pour faire un simple get ...

# DEBUT DE LA CLASSE
class log2dyndns(object):
    def __init__(self):
        self.version = '1.0'
        self.site = 'https://account.dyn.com'
        self.checkip_site = 'http://checkip.dyndns.org'

    def setAccount(self,account):
        self.account = account

    def getAccount(self):
        return self.account

    def setPassword(self,password):
        self.password = password

    def setSite(self,site):
        self.site = site

    def getVersion(self):
        return self.version

    def doConnect(self):
        self.br = mechanize.Browser()

        self.br.set_handle_robots(False)
        self.br.set_handle_redirect(True)
        self.br.set_handle_referer(True)
        r = self.br.open(self.site)

        counter = 0
        for form in self.br.forms():
            if "submit=Log in" in str(form):
                self.br.select_form(nr = counter)
            counter += 1

        self.br.form['username'] = self.account
        self.br.form['password'] = self.password
        self.html = self.br.submit().read()

    def doUpdate(self,dnsdomainname):
        # si changement, envoie de la modification
        # recuperation du code retour
        # si maj ok -> ok
        # si maj non ok -> authentification ?
        # si maj non ok -> je recommence 3 fois toute les 5 secondes et notification
        br = mechanize.Browser()
        r = br.open(self.checkip_site)
        html = r.read()
        current_ipaddress = re.sub(r'\n','',html)
        current_ipaddress = re.sub(r'^.*: ','',current_ipaddress)
        current_ipaddress = re.sub(r'<.*$','',current_ipaddress)
        resolv_dnsdomain = socket.gethostbyname(dnsdomainname)

        # check si on doit le faire pour ne pas incrementer le compteur 'abuse' de dyndns.org
        if current_ipaddress == resolv_dnsdomain:
            print "You don't need to update", dnsdomainname+". Your current IP address :", resolv_dnsdomain
        else:
            # ben on update
            # je dois appeler ce lien http://username:password@members.dyndns.org/nic/update?hostname=yourhostname&myip=ipaddress&wildcard=NOCHG&mx=NOCHG&backmx=NOCHG
            #link_update = "https://"+self.account+":"+self.password+"@members.dyndns.org/nic/update?hostname="+dnsdomainname+"&myip="+current_ipaddress+"&wildcard=NOCHG&mx=NOCHG&backmx=NOCHG"
            link_update = "https://"+self.account+":"+self.password+"@members.dyndns.org/nic/update?hostname="+dnsdomainname+"&myip="+current_ipaddress+"&wildcard=NOCHG&mx=NOCHG&backmx=NOCHG" 
            opener = urllib.FancyURLopener()
            code_erreur = opener.open(link_update).read()
            # la, il faut tous les tester
            # good -> ok
            # nochg -> ok mais on ne devrait jamais tomber sur cette erreur
            # notfqdn -> pas ok, la valeur du dnsdomainname n'est pas un fqdn
            # nohost -> pas ok, cas d'une faute de frappe ou d'un domain qui n'est pas sur le bon compte
            # numhost -> pas gerer, je ne comprends cette erreur
            # abuse -> pas ok du tout, le compte est bloque
            if re.search('good.*$',code_erreur):
                newip = re.sub('good ','',code_erreur)
                return "Update successfull !!! New IP address is "+newip+" for "+dnsdomainname
            elif re.search('nochg.*$',code_erreur):
                baseip = re.sub('nochg ','',code_erreur)
                return "No need to change your IP !!! Your current IP address is "+baseip+" for "+dnsdomainname
            else:
                return code_erreur

    def isConnect(self):
        check_state = "False"
        resultat = self.html.split('\n')
        regex = re.compile(r'(.*)Welcome(.*)'+self.account,re.IGNORECASE)
        for ligne in resultat: 
            if regex.match(ligne):
                check_state = "True"
                break
        return check_state

    def getState(self):
        count_host = 0  #Initialise le compteur du nombre d'hote du compte dyndns
        req = self.br.follow_link(text='My Hosts')
        data_html = req.read()

        if "No Hostnames Registered" not in data_html:
            soup = BeautifulSoup(data_html)
            table = soup.find('table', id='dyndnshostnames')
            rows = table.findAll('tr')
            list_hostname = list()

            for tr in rows:
                cols = tr.findAll('td')
                for td in cols:
                    text = td.find(text=True)
                    text2 = text.strip("\r\n")
                    text = str(text2).replace("\r"," ").replace("\n"," ").replace("\r\n"," ")
                    #print text
                    list_hostname.append(text)
                count_host += 1
            # retirer 2 au nombre d'hote compte afin d'exclure les lignes dyndns
            # hostnames et l'entete du tableau
            count_host -= 2

        # deconnexion
        self.br.follow_link(text='Log Out')
        mechanize.CookieJar.clear

        # affichage du nombre d'hote et de la liste de ces hotes
        print "\nHosts for", self.account, ":", count_host

        
        nombre_de_caracter_colonne1 = 24
        nombre_de_caracter_colonne2 = 20
        nombre_de_caracter_colonne3 = 30
        nombre_de_tiret = nombre_de_caracter_colonne1 + nombre_de_caracter_colonne2 + nombre_de_caracter_colonne3

        reports = ""
        if count_host > 0:
            
            reports += nombre_de_tiret*"-"
            reports += "\n"
            reports += 'Hostname'.rjust(nombre_de_caracter_colonne1)
            reports += 'Ip adress'.rjust(nombre_de_caracter_colonne2)
            reports += 'Last seen'.rjust(nombre_de_caracter_colonne3)
            reports += "\n"
            reports += nombre_de_tiret*"-"
            reports += "\n"
            item = 0
            i = 0
            while item < count_host:
                hostname = list_hostname[i+1]
                ip_addr = list_hostname[i+3]
                last_seen = list_hostname[i+4]

                reports += hostname.rjust(nombre_de_caracter_colonne1)
                reports += ip_addr.rjust(nombre_de_caracter_colonne2)
                reports += last_seen.rjust(nombre_de_caracter_colonne3)
                reports += "\n"

                i += 5
                item += 1

            reports += nombre_de_tiret*"-"
            reports += "\n"

        return reports

# FIN DE LA CLASSE

# DEBUT DU SCRIPT
import argparse

def update_data(user,password,hostname):
  myupdate = log2dyndns()
  myupdate.setAccount(user)
  myupdate.setPassword(password)
  myupdate.doUpdate(hostname)

def get_data(user,password,listing):
    laclass = log2dyndns()
    laclass.setSite('https://account.dyn.com')
    laclass.setAccount(user)
    laclass.setPassword(password)
    laclass.doConnect()

    if laclass.isConnect() == "True":
        if listing == True:
            print laclass.getState()
        else:
            print "Successfully connected with", laclass.getAccount(),"account."
    else:
        print "Can't retrieve data with user", laclass.getAccount()

def get_data_from_files(listing):
    comptes = {}

    file = open("dyndns.conf")
    while 1:
        lines = file.readlines(100000)
        if not lines:
            break
        for line in lines:
            # je passe les lignes de commentaires du fichier de parametre
            if re.search('^#.*$',line):
                continue
            # je passe les lignes vides
            if re.search('^\n',line):
                continue
            account = re.sub(':.*','',line)
            account = re.sub(r'\'','',account)
            account = re.sub(r'\n','',account)
            password = re.sub('^.*:','',line)
            password = re.sub(r'\'','',password)
            password = re.sub(r'\n','',password)
            comptes[account] = password
    for compte, password in comptes.items():
        get_data(compte,password,listing)

def main():
    parser = argparse.ArgumentParser(add_help=True,description='Manage your Dyndns Account.')

    parser.add_argument('-u', action="store", dest='user', help='dyndns account (required)', default='None')
    parser.add_argument('-p', action="store", dest='password', help='dyndns password (required)', default='None')
    parser.add_argument('--hostname', action="store", dest='hostname', help='dns domain name of your host (use only with --create, --delete, --update options)', default='None')
    parser.add_argument('--create', action="store_true", dest='create_hostname', help='create a domain name for your host on dyndns (optionnal)', default='None')
    parser.add_argument('--delete', action="store_true", dest='delete_hostname', help='delete an existing domain name on your dyndns account (optionnal)', default='None')
    parser.add_argument('--update', action="store_true", dest='update_hostname', help='update ip address of your host on dyndns (optionnal)', default='None')
    parser.add_argument('-l','--list', action="store_true", dest="listing", help="list hosts on your account (optionnal)", default=False)
    parser.add_argument('-c', '--config', action="store_true", dest="dictionnaire", help='use dictionnary, you need to create dyndns.conf file (optionnal)', default=False)

    args = parser.parse_args()

    if args.dictionnaire == True:
        get_data_from_files(args.listing)
    elif args.update_hostname == True and args.hostname != 'None':
      update_data(args.user,args.password,args.hostname)
    elif args.user == 'None' or args.password == 'None':
        print parser.parse_args(['-h'])
    else:
        get_data(args.user,args.password,args.listing)


if __name__ == "__main__":
    main()