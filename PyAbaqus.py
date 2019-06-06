'''
    Python Command File to run Abaqus
    including:
        mesher
        preprocessor
'''
import sys
import os
import time
import subprocess
import multiprocessing as mp
import numpy as np
import math
from PyPreprocessor import InpFile

MAX_THREADS = 24

# class SimCase:
    
#     # constructor, create a case with given parameters
#     def __init__(self, jobID, t_len=-1, t_wid=-1, t_nlen=-1, t_nwid=-1):
#         self.nlen = t_nlen
#         self.nwid = t_nwid
#         self.len  = t_len
#         self.wid  = t_wid
#         self.inp = InpFile(jobID, self.len, self.wid, self.nlen, self.nwid)

# class SimPool:

#     # constructor, need to specify the parameter lists
#     def __init__(self, l_nlen=False, l_nwid=False, l_E=False, l_thk=False):
#         self.list_nlen = []
#         self.list_nwid = []
#         self.list_E    = []
#         self.list_t    = []
#         self.list_ID   = []
#         self.list_case = []
        
#         # create parameter lists accordingly, usually 2 lists are used
#         if l_nlen and l_nwid:
#             self.list_nlen = list(range(25,75+1,5))
#             self.list_nwid = list(range(25,75+1,5))

#         if l_E and l_thk:
#             self.list_E = list(range(1,10))
#             self.list_E.extend(list(range(10,101,10)))
#             self.list_E = [i*1e5 for i in list_E]
#             self.list_t = list(range(1,11))
#             self.list_t = [i*1e-4 for i in list_t]

#     # modify a given source inp file
#     def modify(self, inp_in):
#         # modify and make copy
#         for i in range(len(self.list_t)):
#             for j in range(len(self.list_E)):
#                 thk = list_t[i]
#                 E = list_E[j]
#                 fileID = int(str(i+1)+str(j+1))
#                 modify_inp(inp_in, fileID, E, thk)

#     # run refinement test using 2 parameter lists (nlen, nid)
#     def refine(self):

#         all_results = []
#         all_errors = []

#         sidelen = 0.1
#         #* the following operations are in parallel
#         pool = mp.Pool(processes=MAX_THREADS)

#         for i in range(self.list_nlen):
#             jobName = "Job-"+str(i+1)+str(i+1)
#             self.__preprocess(jobName, sidelen, self.list_nlen[i])
    
#             # check if inp file exists
#             inp_name = jobName + ".inp"
#             if not os.path.isfile(inp_name):
#                 # TODO: may need to throw exception
#                 print(inp_name+" not found!")
#                 continue
#             # apply async if looks good
#             result = pool.apply_async(thread_run, args=(jobName, E, thk, ))
#             all_results.append(result)

#         pool.close()
#         pool.join()
#         #* --------------------------- end parallel
            
#         # organize all results, and write good results to file
#         out_file = "max_dim.txt"
#         fout = open(out_file, 'w')
#         for item in all_results:
#             res = item.get()
#             if "errors" in res:
#                 all_errors.append(res)
#             else:
#                 # print dimension infos
#                 fout.write(res+"\n")
#         fout.close()

#         # check and write errors to file
#         if len(all_errors) != 0:
#             with open("error_msg.txt", 'w') as msg:
#                 for i in all_errors:
#                     msg.write(i+"\n")
#         else:
#             print("No errors! Good!")

#     # preprocessing
#     def __preprocess(self, jobID, sidelen, nside):
#         t_case = InpFile(jobID, sidelen, sidelen, nside, nside)
#         t_case.writeInp()
#         print(jobID+" preprocess completed successfully")
#         self.list_case.append(t_case)


# preprocessing, create inp files for a given job
def preprocess(jobName, t_len, t_wid, t_nlen, t_nwid):
    t_case = InpFile(jobName, t_len, t_wid, t_nlen, t_nwid)
    t_case.writeInp3()
    print(jobName+" preprocess completed successfully")
    # return t_case.geo.nn

# modify the E and thk for a given input file
def modify_inp(inp_in, jobName, EModulus, thk):
    inp_out = jobName+".inp"
    fout = open(inp_out, 'w')
    with open(inp_in, 'r') as fin:
        for line in fin:
            fout.write(line)
            # modify thickness
            if "Shell Section" in line:
                fin.readline()
                fout.write( str(thk) + ", 3\n" )
                continue
            # modify Young's modulus
            if "Elastic" in line:
                fin.readline()
                fout.write( "{:e}".format(EModulus) + ", 0.3\n" )
                continue

# run given inp file, check if the job complete, manually terminate the abaqus process
def run_inp(jobName):
    inpFile = jobName+".inp"
    staFile = jobName+".sta"

    if not os.path.isfile(inpFile):
        raise Exception(jobName+" not found")

    print(jobName+".inp found. Abaqus launched")

    # run single job
    # subprocess.call(["/home/khalidjm/abaqus/Commands/abaqus", "j="+jobName, "input="+inpFile])

    # parallel simulation
    cmd = "/home/khalidjm/abaqus/Commands/abaqus j="+jobName+" input="+inpFile
    SimProcess = subprocess.Popen(cmd, shell=True)
    SimProcess.communicate()

    # manually check if job completed
    jobComplete = False
    while jobComplete == False:
        # If file doesn't exist, let us continue
        if not os.path.isfile(staFile):
            continue

        with open(staFile, 'r') as myfile:
            line = ""
            for line in myfile:
                continue

            # if jobs finished successfully
            if "COMPLETED SUCCESSFULLY" in line:
                jobComplete = True
                break
            elif "HAS NOT BEEN COMPLETED" in line:
                jobComplete = False
                # Kill standard
                print(jobName+" has encountered error, killing Abaqus process...")
                break
            else:
                jobComplete = False
        time.sleep(5)

    # Kill standard
    subprocess.call(["/home/khalidjm/abaqus/Commands/abaqus","terminate","job="+jobName])
    # subprocess.call(["fuser", "-k", jobName+"*"])
    return jobComplete


def postprocess(jobName):
    odbName = jobName+".odb"
    if not os.path.isfile(odbName):
        raise Exception(odbName+" doesn't exists!")
    else:
        subprocess.call(["/home/khalidjm/abaqus/Commands/abaqus", "cae", "noGUI=PyAbaqusPost.py", "--", odbName])

#! this needs to match the exact number of nodes!
def get_max_dimensions(jobName, nn = 441):
    myfile = jobName+"_output.txt"

    # read all coordinates
    with open(myfile, 'r') as fin:
        xcoord = np.empty(nn, dtype = float)
        ycoord = np.empty(nn, dtype = float)
        zcoord = np.empty(nn, dtype = float)
        for i in range(nn):
            line = fin.readline()
            coord = np.fromstring(line, dtype=float, sep=' ')
            xcoord[i] = coord[0]
            ycoord[i] = coord[1]
            zcoord[i] = coord[2]

    # rotate to find max width
    max_angle1 = 0
    max_angle2 = 0
    max_xspan = 0.0
    max_yspan = 0.0
    for angle in range(90):
        rad = float(angle)/180.0 * math.pi
        matR = np.matrix(  [[ math.cos(rad), math.sin(rad), 0.0],
                            [-math.sin(rad), math.cos(rad), 0.0],
                            [0.0, 0.0, 1.0]], dtype=float)
        for i in range(nn):
            t_xyz = np.array([[xcoord[i]], [ycoord[i]], [zcoord[i]]], dtype = float)
            t_xyz = matR * t_xyz
            xcoord[i] = t_xyz[0]
            ycoord[i] = t_xyz[1]
            zcoord[i] = t_xyz[2]

        # get maximum span
        xspan = xcoord.max() - xcoord.min()
        yspan = ycoord.max() - ycoord.min()
        zspan = zcoord.max() - zcoord.min()

        if max_xspan < xspan:
            max_xspan = xspan
            max_angle1 = angle
        if max_yspan < yspan:
            max_yspan = yspan
            max_angle2 = angle
        # info = "{:4.1f}".format(angle) + " " + "{:e}".format(xspan) + " " + "{:e}".format(yspan) + " " + "{:e}".format(zspan)
        # print(info)

    # format and write to file, (angle, width, height)
    if max_xspan > max_yspan:
        info = "{:4.1f}".format(max_angle1) + " " + "{:e}".format(max_xspan) + " " + "{:e}".format(zspan)
    else:
        info = "{:4.1f}".format(max_angle2+90) + " " + "{:e}".format(max_yspan) + " " + "{:e}".format(zspan)
    return info


def thread_run(jobName, var1, var2):
    # run simulations
    FLAG_COMPLETE = run_inp(jobName)

    # if the job completed in 1000 increments, continue
    if FLAG_COMPLETE:
        # read ODB files
        print("Postprocessing "+"jobName")
        postprocess(jobName)
        # get maximum dimensions
        dim_info = str(var1)+" "+str(var2)+" "+get_max_dimensions(jobName)
        print(jobName+" postprocessing completed. Dimensions fetched")
        return dim_info

    # if the job didn't complete in max increment, usually some error occured
    else:
        return jobName+" has encountered errors!"

# run single case after re-meshing
def case_run(jobName):
    # run simulations
    FLAG_COMPLETE = run_inp(jobName)

    # if the job completed in 1000 increments, continue
    if FLAG_COMPLETE:
        # read ODB files
        postprocess(jobName)
        return jobName+" postprocessing completed. Coordinates fetched"

    # if the job didn't complete in max increment, usually some error occured
    else:
        return jobName+" has encountered errors!"

if __name__ == "__main__":
    args = sys.argv
    if len(args) != 2:
        sys.exit("Must give an argument!")

    try:
        # parameters
        list_E = list(range(1,10))
        list_E.extend(list(range(10,101,10)))
        list_E = [i*1e5 for i in list_E]
        list_t = list(range(1,11))
        list_t = [i*1e-4 for i in list_t]

        #! delete this
        # list_E = [1e5, 1e6, 1e7]
        # list_t = [1e-3]
        #! ----------
        list_ID = []

        # meshing
        cmd = args[-1]
        if cmd == 'pre':
            fileID = 11
            jobName = "Job-"+str(fileID)

            width = 0.1
            nwid  = 21
            dx = width/float(nwid)
            # list_nlen = np.arange(20, 80+1, 10)
            # list_len = list_nlen * dx
            preprocess(jobName, 0.1, 0.1, nwid, nwid)
            # preprocess(jobName, list_len[1], width, list_nlen[1], nwid)

        # must generate inp files before doing anything else
        # modify E and thk in a given inp file
        elif cmd == 'modify':
            # source inp file
            inp_in = "original1c.inp"
            # modify and make copy
            for i in range(len(list_t)):
                for j in range(len(list_E)):
                    thk = list_t[i]
                    E = list_E[j]
                    fileID = int(str(i+1)+str(j+1))
                    modify_inp(inp_in, fileID, E, thk)

        # simply run a single simulation
        elif cmd == 'srun':
            jobName = "Job-11"
            run_inp(jobName)

        # get max dimension of a single file
        elif cmd == 'max':
            jobName = "Job-77"
            print(get_max_dimensions(jobName, 1600))

        # run refinement test
        elif cmd == 'refine':
            all_results = []
            all_errors = []
            sidelen = 0.1
            list_nlen = list(range(20+1,75+1+1,5))
            list_nwid = list(range(20+1,75+1+1,5))

            #* the following operations are in parallel
            pool = mp.Pool(processes=MAX_THREADS)

            for i in range(len(list_nlen)):
                nside = list_nlen[i]
                fileID = int(str(i+1)+str(i+1))
                jobName = "Job-"+str(fileID)
                preprocess(jobName, sidelen, sidelen, nside, nside)
                # check if inp file exists
                inp_name = jobName + ".inp"
                if not os.path.isfile(inp_name):
                    # TODO: may need to throw exception
                    print(inp_name+" not found!")
                    continue
                # apply async if looks good
                result = pool.apply_async(case_run, args=(jobName, ))
                all_results.append(result)

            pool.close()
            pool.join()
            #* --------------------------- end parallel
            
            # organize all results, and write good results to file
            out_file = "results_all.txt"
            fout = open(out_file, 'w')
            for item in all_results:
                res = item.get()
                if "errors" in res:
                    all_errors.append(res)
                else:
                    # print dimension infos
                    fout.write(res+"\n")
            fout.close()

            # check and write errors to file
            if len(all_errors) != 0:
                with open("error_msg.txt", 'w') as msg:
                    for i in all_errors:
                        msg.write(i+"\n")
            else:
                print("No errors! Good!")

        # run with different aspect ratio
        elif cmd == 'ratio':
            all_results = []
            all_errors = []
            width = 0.1
            nwid  = 20
            dx = width/float(nwid)
            list_nlen = np.arange(20, 80+1, 10)
            list_len = list_nlen * dx

            #* the following operations are in parallel
            pool = mp.Pool(processes=MAX_THREADS)

            for i in range(len(list_nlen)):
                nlen = list_nlen[i]
                jobName = "Job-"+str(i+1)+str(i+1)
                preprocess(jobName, list_len[i], width, nlen, nwid)
                # check if inp file exists
                inp_name = jobName + ".inp"
                if not os.path.isfile(inp_name):
                    # TODO: may need to throw exception
                    print(inp_name+" not found!")
                    continue
                # apply async if looks good
                result = pool.apply_async(thread_run, args=(jobName, list_len[i], width, ))
                all_results.append(result)

            pool.close()
            pool.join()
            #* --------------------------- end parallel
            
            # organize all results, and write good results to file
            out_file = "max_dim.txt"
            fout = open(out_file, 'w')
            for item in all_results:
                res = item.get()
                if "errors" in res:
                    all_errors.append(res)
                else:
                    # print dimension infos
                    fout.write(res+"\n")
            fout.close()

            # check and write errors to file
            if len(all_errors) != 0:
                with open("error_msg.txt", 'w') as msg:
                    for i in all_errors:
                        msg.write(i+"\n")
            else:
                print("No errors! Good!")

        # run multiple simulation
        elif cmd == 'run':

            #* the following operations are in parallel
            pool = mp.Pool(processes=MAX_THREADS)

            all_results = []
            all_errors = []
            for i in range(len(list_t)):
                for j in range(len(list_E)):
                    thk = list_t[i]
                    E = list_E[j]
                    fileID = int(str(i+1)+str(j+1))
                    jobName = "Job-"+str(fileID)
                    # check if inp file exists
                    inp_name = jobName + ".inp"
                    if not os.path.isfile(inp_name):
                        # TODO: may need to throw exception
                        print(inp_name+" not found!")
                        continue
                    # apply async if looks good
                    result = pool.apply_async(thread_run, args=(jobName, E, thk, ))
                    all_results.append(result)

            pool.close()
            pool.join()
            #* --------------------------- end parallel
            
            # organize all results, and write good results to file
            out_file = "max_dim.txt"
            fout = open(out_file, 'w')
            for item in all_results:
                res = item.get()
                if "errors" in res:
                    all_errors.append(res)
                else:
                    # print dimension infos
                    fout.write(res+"\n")
            fout.close()

            # check and write errors to file
            if len(all_errors) != 0:
                with open("error_msg.txt", 'w') as msg:
                    for i in all_errors:
                        msg.write(i+"\n")
            else:
                print("No errors! Good!")


        elif cmd == "clear":
            # TODO: implement a clear command
            # subprocess.call(["rm !(*.py|*.inp)"], shell=True, executable="/bin/bash")
            pass

        else:
            raise Exception("Wrong Commands")

    except Exception as err:
        print(err.args[0])
        sys.exit("Exception caught, existing...")

    finally:
        # only do this on linux, skip it for mac
        if sys.platform != "darwin":
            # kill all Abaqus processes
            subprocess.call(["pkill", "-u", "jingyuchen", "standard"])