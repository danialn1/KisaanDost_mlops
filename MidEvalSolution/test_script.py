#!/usr/bin/python

import sys

def main():
	if len(sys.argv)>1:
		print(f'Your message was "{sys.argv[1]}"')
	else:
		print("I am experiencing technical difficulties right now")

if __name__=="__main__":
	main()
