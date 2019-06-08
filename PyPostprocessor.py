'''
    Python Postprocessor to get the dimension info of a hanging plate
'''
import numpy as np
import math

# get dimension info of a square plate
# return max_wid, horizontal dist between 2&3, max height, planar dist between 1&4
def get_dims(jobName, nside):
    myfile = jobName+"_output.txt"
    nn = nside * nside
    # read and save all coordinates
    coord = np.zeros([nn, 3], dtype = float)
    with open(myfile, 'r') as fin:
        for i in range(nn):
            line = fin.readline()
            xyz = np.fromstring(line, dtype=float, sep=' ')
            coord[i] = xyz

    # get coordinates of four corners
    #      3               4
    #      -----------------
    #      |               |
    #      |               |
    #      |               |
    #      -----------------
    #      1 (fixed)        2
    node1 = coord[0]
    node2 = coord[nside-1]
    node3 = coord[-nside]
    node4 = coord[-1]

    # dimensions vector measured between 1 and 4
    vecDist1 = node4 - node1
    nvec3 = np.array([0,0,1], dtype=float)

    # dimensions vector measured between 2 and 3
    vecDist2 = node2 - node3

    nvec2 = np.array([vecDist2[0], vecDist2[1], 0])
    nvec2 = nvec2 / np.linalg.norm(nvec2)
    
    nvec1 = np.cross(nvec3, nvec2)

    newfile = jobName+"_new.txt"
    with open(newfile, 'w') as fout:
        for i in range(nn):
            coord[i] = projNodes(nvec1, nvec2, nvec3, coord[i])
            line = "{:e} {:e} {:e}".format(coord[i,0], coord[i,1], coord[i,2])
            fout.write(line+"\n")

    # return max_wid, horizontal dist between 2&3, max height, planar dist between 1&4
    max_wid = coord[:,1].max() - coord[:,1].min()
    h_dist23 = abs(vecDist2[1])
    max_height = coord[-1,2]
    h_dist14 = np.linalg.norm(np.array([vecDist1[0],vecDist1[1]], dtype=float))
    info = "{:e} {:e} {:e} {:e}".format(max_wid, h_dist23, max_height, h_dist14)

    return info

# project nodes onto the given bases
def projNodes(nvec1, nvec2, nvec3, node):
    t_node = np.array([np.dot(node,nvec1), np.dot(node,nvec2), np.dot(node,nvec3)], dtype=float)
    return t_node