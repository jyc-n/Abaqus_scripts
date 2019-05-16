import numpy as np
import matplotlib as mpl
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt

class Geometry:
    # constructor, pass in num of nodes along length, width, and mesh size
    def __init__(self, t_nlen, t_nwid, t_dx, t_dy):
        self.__nlen = t_nlen
        self.__nwid = t_nwid
        self.__dx = t_dx
        self.__dy = t_dy

        self.nn = self.__nlen * self.__nwid
        self.nel = 2 * (self.__nlen-1) * (self.__nwid-1)
        self.coord = np.empty([self.nn, 3], dtype = float)
        self.conn = np.empty([self.nel, 3], dtype = int)

    # build mesh
    def buildMesh(self):
        self.__seeding()
        self.__meshing()

    # plot mesh
    def plotMesh(self):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        x = self.coord[:,0]
        y = self.coord[:,1]
        z = self.coord[:,2]

        for i in range(self.nel):
            iel = self.conn[i]
            index = np.array([iel[0]-1, iel[1]-1, iel[2]-1, iel[0]-1])
            el_x = x[index]
            el_y = y[index]
            el_z = z[index]

            l_x = (x[iel[0]-1] + x[iel[1]-1] + x[iel[2]-1]) / 3.0
            l_y = (y[iel[0]-1] + y[iel[1]-1] + y[iel[2]-1]) / 3.0
            l_z = (z[iel[0]-1] + z[iel[1]-1] + z[iel[2]-1]) / 3.0

            label = str(i+1)
            ax.text(l_x, l_y, l_z, label, color='b')

            ax.plot(el_x, el_y, el_z, lw=1, c='k', ls='-', marker='.')

        for i in range(self.nn):
            inn = self.coord[i]
            label = str(i+1)
            ax.text(inn[0], inn[1], inn[2], label, color='r')

        plt.show()
        # plt.savefig('mesh.png')

    # get boundary sets
    def getClamped(self):
        n_start = 1
        n_end = n_start + (self.__nwid-1) * self.__nlen
        e_start = 2
        e_end = e_start + (self.__nwid-2) * 2*(self.__nlen-1)
        return [str(n_start)+", "+str(n_end)+", "+str(self.__nlen),
                str(e_start)+", "+str(e_end)+", "+str(2*(self.__nlen-1))]

    # build nodal coordinates
    def __seeding(self, datum_opt=1):
        for i in range(0, self.__nwid):
            for j in range(0, self.__nlen):
                index = i * self.__nlen + j
                
                # original shape in xy plane
                if datum_opt == 1:
                    self.coord[index, 0] = j * self.__dx
                    self.coord[index, 1] = i * self.__dy
                    self.coord[index, 2] = 0.0

                # original shape in xz plane
                elif datum_opt == 2:
                    self.coord[index, 0] = j * self.__dx
                    self.coord[index, 1] = 0.0
                    self.coord[index, 2] = i * self.__dy

                # original shape in yz plane
                elif datum_opt == 3:
                    self.coord[index, 0] = 0.0
                    self.coord[index, 1] = j * self.__dx
                    self.coord[index, 2] = i * self.__dy

    # build connectivity
    def __meshing(self):
        for i in range(0, self.__nwid-1):
            for j in range(0, self.__nlen-1):
                el1 = 2 * ((self.__nwid-1) * i + j)
                el2 = el1 + 1
                self.conn[el1, 0] = i * self.__nlen + j + 1
                self.conn[el1, 1] = i * self.__nlen + j + 2
                self.conn[el1, 2] = (i+1) * self.__nlen + j + 2
                self.conn[el2, 0] = (i+1) * self.__nlen + j + 2
                self.conn[el2, 1] = (i+1) * self.__nlen + j + 1
                self.conn[el2, 2] = i * self.__nlen + j + 1
                
    # write coordinate file
    def writeXYZ(self, jobID):
        filename = "Job-" + str(jobID) + "-coordinates.txt"
        with open(filename, 'w') as fout:
            
            for inn in range(self.nn):
                fout.write("%6d, %12.8f, %12.8f, %12.8f\n" % (inn+1, self.coord[inn, 0], self.coord[inn, 1], self.coord[inn, 2]))    
    
    # write connectivity file
    def writeMesh(self, jobID):
        filename = "Job-" + str(jobID) + "-connectivity.txt"
        with open(filename, 'w') as fout:
            for iel in range(self.nel):
                fout.write("%6d, %6d, %6d, %6d\n" % (iel+1, self.conn[iel, 0], self.conn[iel, 1], self.conn[iel, 2]))