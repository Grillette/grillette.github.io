---
layout: post
title:  "SigSegV2 - Write up"
date:   2019-11-30 15:04:12
categories: Write up
author: Grillette
---
Last Week-end I attended SigSegV2 which is a french cybersecurity event with conferences all day and a CTF on site at night. There was a qualification phase where you had to succeed, at least one of the five challenges to be allowed to buy a ticket.
This article is a write up about some challenges I managed to flag during the event or even after. The event was really great, but I didn't stay late during the night so I didn't flagged a lot but that's something.

![Logo]({{ "assets/2019-11-30/logo.png" | absolute_url }} "Logo")

# Reverse
## Baby Android

### Challenge Description
![BabyAndroidChall]({{ "assets/2019-11-30/BabyAndroidChall.png" | absolute_url }} "BabyAndroidChall")


You can download the attached apk file here : [baby.apk]({{ "assets/2019-11-30/baby.apk" | absolute_url}})

### Introduction
I'm not really good at reversing stuff usually, but as this one was tagged easy I decided to give it a go. I also never reversed any apk file so I thought this was a great occasion to learn. I installed **jadx** which is a command line and GUI tool that produce Java source code from Android Dex and Apk files, as quoted on their [Github repo](https://github.com/skylot/jadx).


By launching Jadx GUI and opening the apk from the challenge we obtain the following Java classes :
![BabyAndroidClass]({{ "assets/2019-11-30/BabyAndroidClass.png" | absolute_url }} "BabyAndroidClass")

### Challenge Resolution
Now let's jump into the de-compiled code :
- First we check the *MainActivity* class

![BabyAndroidMain]({{ "assets/2019-11-30/BabyAndroidMain.png" | absolute_url }} "BabyAndroidMain")

In the red rectangle you can see the interesting part. If this statement is correct, then that means our flag is correct.
- We now have to dig deeper to reverse the flag.
We have to find out what ```chall.encode(flag)``` is doing, so let's dive into the **Chall** class.

![BabyAndroidChallClass]({{ "assets/2019-11-30/BabyAndroidChallClass.png" | absolute_url }} "BabyAndroidChallClass")

You can see here that the *encode* function is only calling 2 other functions. The *b64Encode* function is simply encoding a String in [base64](https://en.wikipedia.org/wiki/Base64) and returning the encoded String. You can now easily understand that our *encode* function is simply returning the base64 encoded String returned by the *otherEncode* function.

The first argument of this function is the flag that we need to find, the second argument is a key declared in this class.

```java
private String _key = "SigSegV2";
```

Inside the function, we have a for loop iterating other each byte of our flag variable, and each byte is xored with the **_key** variable. One important thing to know about the xor operation is that :
```
string1 ^ key = string2
string2 ^ key = string1
```
So if we know the key and one of the two strings we can retrieve the other string with a simple xor. In this case, we know the key, but also the base64 encoded result of the previous xor operation. By reversing this xor we can then get the flag.

We reverse the flag with a short python script
```python
import base64
import itertools

encodedString = "IAAAIAAAIEkRXV8KOlM4diFZVhc6IWZADFxUJxA3Kw=="

key = "SigSegV2"

decoded = base64.b64decode(encodedString)

print(''.join(chr(a ^ ord(b)) for a,b in zip(decoded,itertools.cycle(key))))
```

Here, we take the encoded string that we decode, we then xor each byte of the key and the decoded object.
We use **zip** to iterate over the *decoded* variable and the *key* at the same time. The iterator will stop when the shortest input iterable is exhausted and we don't want that to happen because our key is shorter than the string we have to xor. That's why we use **itertools.cycle** on the key so it does not stop iterating as a cycle.

For each iteration of those 2 variables we then xor *a* and *b* and use **chr()** to get a printable character.

Running this script we get this :
![BabyAndroidFlag]({{ "assets/2019-11-30/BabyAndroidFlag.png" | absolute_url }} "BabyAndroidFlag")

First flag ! :flags: :tada:

# Misc
## The Long Way

### Introduction

![TheLongWayChall]({{"assets/2019-11-30/TheLongWayChall.png" | absolute_url }} "TheLongWayChall")

The only resource for this challenge is the following img file : [the_long_way.img]({{"assets/2019-11-30/the_long_way.img" | absolute_url}})

### Challenge Description
Performing **file** on the challenge's file we end up with the following answer :

```
the_long_way.img: DOS/MBR boot sector
```

By looking on the Internet, we see that we can simply mount this *img* file on our system.
We use the following command :

```bash
sudo mount ./the_long_way.img ./tmp -o loop
```

### Challenge Resolution
By going into our ./tmp directory we can see a file name ```76```, and inside that file another one named ```111```, and so on...
With the challenge description we quickly grab the idea that we are going to dig deep into those folders, so let's write a little script ! :snake:
The aim will be to explore recursively every folder until the last one and get the complete path. Every folder's name is an [ASCII code](http://www.asciitable.com/) corresponding to a character. The final step is to convert each folder name to the corresponding character and get a big string with the flag buried in it.

I end up with the following code :
```python
import os
import sys

sys.setrecursionlimit(10000)

finish = ""
i=1

while i==1:
	for root, dirs, files in os.walk(".", topdown=False):
		path = root
		break

	if path == ".":
		i=0
	else:
		finish += path
		os.chdir(path)

finish = finish[6:].replace('.','')
finish = finish.split('/')
print(''.join(chr(int(i)) for i in finish))
```

So, to explain quickly, I use ```sys.setrecursionlimit(10000)``` to set a higher number of the recursion limit because I had an error on my for loop afterward. To explore the directories recursively, I use ```os.walk()``` in a for loop, it will give every path of the tree in our current directory. Here, the first occurrence gives the longest path he can go so we can break directly after getting the first path, no need to list every path. We can find the documentation [here](https://docs.python.org/3/library/os.html).

After using this, we noticed that our ```path``` variable is really long, but it's not the deepest we can go, the *walk()* function is limited, so we decided to use it several times until we really are at the end of the tree. That's why we have a while loop, for every round we concatenate the path to another variable to keep the total path stored and we change directory to this path. Which means, every round we go to the deepest directory that *walk()* can get and we repeat. We stop when the only directory detected is "." which mean there is no more folder.

Once that's done, we simply clean our output for dots and the beginning folder "/tmp", convert our string to a table of every ascii code and finally convert it to a readable string.
Here is the output :
![TheLongWayFlag]({{ "assets/2019-11-30/TheLongWayFlag.png" | absolute_url }} "TheLongWayFlag")


![TheLongWayFlagZoom]({{ "assets/2019-11-30/TheLongWayFlagZoom.png" | absolute_url }} "TheLongWayFlagZoom")


# Forensic
## Je rim et je ram

### Introduction
![RimRamChall]({{"assets/2019-11-30/RimRamChall.png" | absolute_url }} "RimRamChall")

I flagged this one after the end of the CTF but it was fun, so I still wanted to share.

And here is the file for this challenge : [yolo2.raw]({{"assets/2019-11-30/yolo2.raw" | absolute_url }})

### Challenge Description
It's time to use [volatility]("https://www.volatilityfoundation.org/") to do some great forensic. :mag:


First step is to gather some basic info on this file :

![RimRamImageinfo]({{"assets/2019-11-30/RimRamImageinfo.png" | absolute_url}} "RimRamImageinfo")

So our memory dump is likely to be from Windows Vista or Windows 2008.

We can also see what process were running on this system when the memory dump was created with the ```pstree``` command :

![RimRamPstree]({{"assets/2019-11-30/RimRamPstree.png" | absolute_url }} "RimRamImageinfo")

Nothing really suspicious here, but we still notice a notepad that can contain some useful stuff (like a flag) and Internet Explorer opened.

One important thing to do during the recon part in forensic is also to look the last commands with the ```cmdline``` instruction. But in this case, there was nothing interesting, so it's just a tip.

Time to go deeper !

### Challenge Resolution
With the previous command, we have the PID of the notepad executable, we can dump the memory of this process as follow :

```
volatility -f yolo2.raw --profile=VistaSP2x64 memdump --dump-dir=./ -p 156
```

With '156' the PID of the targeted process. This create a new file *156.dmp*.

It's time to fire up the magic tool of forensic : **grep** !

```
strings 156.dmp | grep sigsegv
```

And found two interesting file :

![RimRamGrepSigsegv]({{"assets/2019-11-30/RimRamGrepSigsegv.png" | absolute_url }} "RimRamGrepSigsegv")

Now that we have the name of the interesting files, we need to scan all files available in our dump in order to get the right offset to extract those files :

```
volatility -f yolo2.raw --profile=VistaSP2x64 filescan > filescan.txt
```

In this *filescan.txt* we have a lot of file listed (3858). So let's call our friend grep one more time.
![RimRamGrepUser]({{"assets/2019-11-30/RimRamGrepUser.png" | absolute_url}} "RimRamGrepUser")

We know have the offset in memory of **user.txt** which is **0x000000001bf0ff20**

To extract the right file :

```
volatility -f yolo2.raw --profile=VistaSP2x64 dumpfiles --dump-dir=./ -Q 0x000000001bf0ff20
```

And then :

![RimRamCat]({{"assets/2019-11-30/RimRamCat.png" | absolute_url }} "RimRamCat")

**BUT** ... As stated in the challenge description, if we found an easy flag, it's likely to be a fake one... So this is probably the fake, but we still try it ! I mean, you never know.

...It's a fake.
(Plus there is a typo in the flag format so it was clearly a fake but I just noticed it now)

My second guess was to look for the Internet Explorer history with the ```iehistory``` command.

![RimRamIehistory]({{"assets/2019-11-30/RimRamIehistory.png" | absolute_url }} "RimRamIehistory")

An other way of finding this url is to use ```clipboard```.

We go to the specified url and get the following website :

![RimRamCryptobin]({{"assets/2019-11-30/RimRamCryptobin.png" | absolute_url }} "RimRamCryptobin")

This is basically our flag but encrypted using [AES-256]("https://en.wikipedia.org/wiki/Advanced_Encryption_Standard").

We can visualize our encrypted flag like this :

```
{"iv":"EWZUNcKk43zayYoumeQOkg==","v":1,"iter":1000,"ks":256,"ts":64,
"mode":"ccm","adata":"","cipher":"aes","salt":"rcAukep0lGo=",
"ct":"a3yIjhXoX4083irg99IDSXuDR86zTlOELLiBZeME"}
```

Now we need to find the password to decrypt this.

I spent a lot of time on this part and mainly in wrong direction, the solution is not that hard so I'll go straight up to the correct way to find this password.
This time again we'll need grep and use the notepad dump we made before.

![RimRamPassword]({{"assets/2019-11-30/RimRamPassword.png" | absolute_url }} "RimRamPassword")

We use the ``` -e l``` option to read the file with little endian encoding.

Then back to the CryptoBin website, we enter the password and finally get the flag !

![RimRamFlag]({{"assets/2019-11-30/RimRamFlag.png" | absolute_url }} "RimRamFlag")


So that's it for this CTF Write-up ! The other flags I got were not worth a write up and I didn't flagged a lot. This was a really great event and CTF so I'm really looking forward to participate next year !
