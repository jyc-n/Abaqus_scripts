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
# from PyMesher import Geometry

MAX_THREADS = 24

def modify_inp(fileID, EModulus, thk):
    inp_in = "original1c.inp"
    jobName = "Job-"+str(fileID)
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


def run_inp(fileID):
    jobName = "Job-"+str(fileID)
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


def postprocess(fileID):
    odbName = "Job-"+str(fileID)+".odb"
    if not os.path.isfile(odbName):
        raise Exception(odbName+" doesn't exists!")
    else:
        subprocess.call(["/home/khalidjm/abaqus/Commands/abaqus", "cae", "noGUI=PyAbaqusPost.py", "--", odbName])


def get_max_dimensions(fileID):
    myfile = "Job-"+str(fileID)+"_output.txt"

    #! this need to match the exact number of nodes!
    nn = 441
    #! -----------------

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


def thread_run(fileID, E, thk):
    # run simulationss
    FLAG_COMPLETE = run_inp(fileID)

    # if the job completed in 1000 increments, continue
    if FLAG_COMPLETE:
        # read ODB files
        print("Postprocessing"+" Job-"+str(fileID))
        postprocess(fileID)
        # get maximum dimensions
        dim_info = str(E)+" "+str(thk)+" "+get_max_dimensions(fileID)
        print("Job-"+str(fileID)+" postprocessing completed. Dimensions fetched")
        return dim_info

    # if the job didn't complete in max increment, usually some error occured
    else:
        return "Job-"+str(fileID)+" has encountered errors!"


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
            # nside = 3
            # side_len = 0.5
            # dx = side_len/float(nside)
            # geo = Geometry(nside, nside, dx)
            # geo.doMesh()
            pass

        # must generate inp files before doing anything else
        elif cmd == 'modify':
            for i in range(len(list_t)):
                for j in range(len(list_E)):
                    thk = list_t[i]
                    E = list_E[j]
                    fileID = int(str(i+1)+str(j+1))
                    modify_inp(fileID, E, thk)

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
                    # check if inp file exists
                    inp_name = "Job-" + str(fileID) + ".inp"
                    if not os.path.isfile(inp_name):
                        # TODO: may need to throw exception
                        print(inp_name+" not found!")
                        continue
                    # apply async if looks good
                    result = pool.apply_async(thread_run, args=(fileID, E, thk, ))
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
        # kill all Abaqus processes
        subprocess.call(["pkill", "-u", "jingyuchen", "standard"])