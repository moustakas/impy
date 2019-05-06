From hoffman@oberon.Berkeley.EDU Wed Jan  3 10:25:59 2001
Date: Mon, 27 Nov 2000 17:15:54 -0800 (PST)
From: wilson hoffman <hoffman@oberon.Berkeley.EDU>
To: everyone@astron.Berkeley.EDU
Subject: mg command

I have just installed a new perl script in /usr/local/bin which is the 
ultimate grep command: Use man mg to see all it can do.

Extra nifty things you can do with mg are:
Grep recursively through a directory and subdirectories.  -R
Grep only in Text files  -T  or binary only -B 

files with .Z or .gz suffixes are uncompressed then grepped.

ar or tar  or zip archives are unarchived then the individual files
are searched. (unless you -Z )

Example of the niftyness:

  For example, you can find a string
          ``foobar''  from  all C source files and makefiles in
          directories under /usr/src  like this:

               mg -RP '*.c|[Mm]akefile' foobar /usr/src
				^	^	^(argument of R)
				^	^(searched for string)
				^(argument of P(regular expression))

-------------------------------------------------------------------------
Wilson Hoffman,  Astronomy Department, University of California, Berkeley
  whoffman@astro.berkeley.edu,   (510)642-7768
-------------------------------------------------------------------------
