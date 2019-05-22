---
layout: post
title:  "INShAck - Write up"
date:   2019-05-18 15:04:12 +0200
categories: Write up
author: Grillette
---
  This article will present write-up of some challenges I've managed to flag during the INShAck CTF that was held from 05/02 to 05/05.

![Logo]({{ "assets/2019-05-18/LogoInshack.png" | absolute_url }} "Logo")

## Atchap - Web
### Challenge description
> This is a message to all ATchap employees. Our new communication software is now in a beta mode. To register, just enter you email address, you'll receive shortly the activation code.

### Introduction
We are given a web page of the company *Almost Tchap* wich ask for a valid email address to get a validation code by email.
By looking the webpage you can see a list of the company employees and their email address :
- Maud.Erateur@almosttchap.fr
- Guy.Liguili@almosttchap.fr
- Samira.Bien@almosttchap.fr

If we try to enter our personnal email address we get the following message : **You're not whitelisted or not part of the company..**

### Realisation
Fine, let's use our brain now. By looking at the challenge name we can think of the recent French governmental "secure" chat application [Tchap](http://www.tchap.fr/ "Tchap").
By looking on the internet we found a vulnerability disclosed quickly after the launch of the app. We can see the original blog post of the vuln exposure [there](https://medium.com/@fs0c131y/tchap-the-super-not-secure-app-of-the-french-government-84b31517d144 "Tchap vulnerability explanation") but to make it quick, to register to that application you needed an email address ending with either "@gouv.fr" or "@elysee.fr" to prove that you're from the french government. Turns out you can bypass this protection by modifying the payload with : **yourpersonnaladdress@wathever.com@validaddress@gouv.fr**

Now, let's go back to our challenge, if we enter one of the three valid email address, we got a message saying that the mail as been sent, let's try to exploit the vulnerability we just saw. We setup BurpSuite, enter a valid email address and start intercepting the traffic. We got our payload and can modify it as follow :
![Payload]({{ "assets/2019-05-18/payload.png" | absolute_url }} "Payload")
We can then check our email address to get our precious reward Yeaah !
![AtchapFlag]({{ "assets/2019-05-18/Atchapflag.png" | absolute_url }} "ATchap flag")

## Drone motion - Forensic
### Challenge description
> We intercepted a drone flying above a restricted area and retrieved a [log]({{ "assets/2019-05-18/sensors.log" | absolute_url }}) from its memory card.
> Help us find out what this drone was doing above our heads!

### Introduction
By looking at the log file and with the challenge description we understand that the file describe some drone movement. The log file speak from himself, we got some directions values and some acceleration values.
But we can notice that there are some negative acceleration values that are quite strange to describe a drone movement.
Anyway, we get the idea of the challenge: draw the course of our drone. So let's grab our favorite scripting language and code. :snake:

### Realisation
So the easiest way to plot the drone movement was to use [matplotlib](https://matplotlib.org/). The general idea of our program is to read the log file line by line, if it's a "dir" line we define a new direction, if it's an "accel" line, we move our point by the number indicated after the accel keyword in the file in the direction we stored and we draw our point.
After finishing our plot, we can't read any flag, we can see that we have the good intention but it's unreadable.
Considering it is a drone log file, we tried to draw it on 3 dimensions and look the plot under every possible angle to see our precious flag but we didn't get lucky.
![3DPlot]({{ "assets/2019-05-18/3Dplot.png" | absolute_url }} "3D plot")

We can almost see the flag but there is still some parasitic movement so we dive back into the log file and understand that we must clean the drone movement by deleting all the motion with a negative acceleration. We finally get the following script :
```python
import sys
import matplotlib.pyplot as plt
import numpy as np

plt.xlim(0,-2000)
plt.ylim(300,-500)

def main():
	f = open('sensors.log','r')
	f1 = f.readlines()

	lastDir = [0,0,0]

	coordinate_x = 0
	coordinate_y = 0

	array_x = []
	array_y = []

	for x in f1:
		instruc = x[16:]

		if instruc[:3] == 'dir':
			dire=instruc[6:len(instruc)-2]
			x,y,z=dire.split(',')
			x,y=x[2:],y[2:]
			lastDir=[x,y]

		elif instruc[:3] == 'acc':
			accel=instruc[7:]
			if int(accel) < 0:
				coordinate_x = coordinate_x+float(lastDir[0])*int(accel)
				coordinate_y = coordinate_y+float(lastDir[1])*int(accel)
				array_x = np.append(array_x, coordinate_x)
				array_y = np.append(array_y, coordinate_y)

		else:
				print('error:', instruc)

	plt.plot(array_x, array_y, label='flag')
	plt.legend()
	plt.show()

if __name__== "__main__":
	main()
```
Aaaand, we finally get our flag, it's pretty long so we have to move the plot to read it but it works.
![droneFlag]({{ "assets/2019-05-18/droneFlag.png" | absolute_url }} "Drone motion flag")
