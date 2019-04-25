import numpy as np

class Geometry:
    def __init__(self, t_nlen, t_nwid, t_dx):
        self.__nlen = t_nlen
        self.__nwid = t_nwid
        self.__dx = t_dx
        self.nn = self.__nlen * self.__nwid
        self.nel = 2 * (self.__nlen-1) * (self.__nwid-1)
        self.coord = np.empty([self.nn, 3], dtype = float)
        self.conn = np.empty([self.nel, 3], dtype = int)

    def doMesh(self):
        self.__seeding(1)
        self.__meshing()

    # build nodal coordinates
    def __seeding(self, datum_opt):
        for i in range(0, self.__nwid):
            for j in range(0, self.__nlen):
                index = i * self.__nlen + j
                if datum_opt == 1:
                    self.coord[index, 1] = j * self.__dx
                    self.coord[index, 2] = i * self.__dx
                    self.coord[index, 3] = 0.0
                elif datum_opt == 2:
                    self.coord[index, 1] = j * self.__dx
                    self.coord[index, 2] = 0.0
                    self.coord[index, 3] = i * self.__dx
                elif datum_opt == 3:
                    self.coord[index, 1] = 0.0
                    self.coord[index, 2] = j * self.__dx
                    self.coord[index, 3] = i * self.__dx

    # build connectivity
    def __meshing(self):
        for i in range(0, self.__nwid):
            for j in range(0, self.__nlen):
                el1 = 2 * ((self.__nwid-1) * i + j)
                el2 = el1 + 1
                self.conn[el1, 1] = i * self.__nlen + j + 1
                self.conn[el1, 2] = i * self.__nlen + j + 2
                self.conn[el1, 3] = (i+1) * self.__nlen + j + 2
                self.conn[el2, 1] = (i+1) * self.__nlen + j + 2
                self.conn[el2, 2] = (i+1) * self.__nlen + j + 1
                self.conn[el2, 3] = i * self.__nlen + j + 1
                
    # visualize the mesh
    def drawMesh(self):
        print('Coordinates\n')
        print('%f')
                