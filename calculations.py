import math

def dist(p1, p2):
	v = (p1[0]-p2[0], p1[1]-p2[1])

	l = math.sqrt(sum([a*a for a in v]))
	return l

def length(v):
	return dist((0,0,0), v)

def normalize(v, thresold=0.0001):
	# normalize vector v

	l = math.sqrt(sum([a*a for a in v]))

	if l <= thresold:
		return (0,0)

	v = tuple([a/l for a in v])

	return v

def getDir(p1, p2):

	v = (p2[0]-p1[0], p2[1]-p1[1])

	return v
