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
from PyPreprocessor import InpFile
from PyPostprocessor import get_dims

#* Object for a single case
class SimCase:
    
    # constructor, create a case with given parameters
    def __init__(self, jobName, t_len, t_wid, t_nlen, t_nwid, t_thk, t_E):
        self.nlen = t_nlen
        self.nwid = t_nwid
        self.len  = t_len
        self.wid  = t_wid
        self.thk  = t_thk
        self.E    = t_E
        self.jobName = jobName
        self.inp = InpFile(jobName, self.len, self.wid, self.nlen, self.nwid, self.thk, self.E)
        self.FLAG_SUCCESS = False

    # write inp
    def writeInpFile(self, opt):
        if opt == 1:
            #* cantilever
            self.inp.writeInp1()
        elif opt == 2:
            #* hanging
            self.inp.writeInp2()
        elif opt == 3:
            #* simply supported
            self.inp.writeInp3()
        else:
            raise "wrong input file options, only 1, 2, 3 allowed!"

    # run single case
    def run(self):
        inpFile = self.jobName+".inp"
        staFile = self.jobName+".sta"
        if not os.path.isfile(inpFile):
            raise Exception(self.jobName+" not found")

        print(self.jobName+".inp found. Abaqus launched")

        # run job in subprocess
        cmd = "/home/khalidjm/abaqus/Commands/abaqus j="+self.jobName+" input="+inpFile
        SimProcess = subprocess.Popen(cmd, shell=True)
        SimProcess.communicate()

        # manually check if job completed
        jobComplete = False
        while jobComplete == False:
            # If file doesn't exist, let us continue
            if not os.path.isfile(staFile):
                continue
            # look for keywords
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
                    print(self.jobName+" has encountered error, killing Abaqus process...")
                    break
                else:
                    jobComplete = False
            time.sleep(5)

        # Kill standard
        subprocess.call(["/home/khalidjm/abaqus/Commands/abaqus","terminate","job="+self.jobName])
        self.FLAG_SUCCESS = jobComplete

    # postprocess single case (read ODB)
    def post_case(self):
        # get deformed coordinates from Abaqus ODB
        odbName = self.jobName+".odb"
        if not os.path.isfile(odbName):
            raise Exception(odbName+" doesn't exists!")
        else:
            subprocess.call(["/home/khalidjm/abaqus/Commands/abaqus", "cae", "noGUI=PyAbaqusPost.py", "--", odbName])

#* Object for simulation pool
class SimPool:

    # constructor, need to specify the parameter lists
    def __init__(self, FLAG_TYPE, t_list1=[], t_list2=[], nthreads=24):
        self.list1       = t_list1
        self.list2       = t_list2
        self.list_case   = []
        self.nCases      = 0
        self.simType     = FLAG_TYPE      # True - parameter test, False - refinement test
        self.max_threads = nthreads

        self.all_logs = []
        self.all_errors = []
        self.all_dims = {}

    # preprocess all cases (generate inp files)
    def pre_all(self, opt, side_len=0.1, nside=20, thk=3e-4, E=2e6):

        # parameter test
        if self.simType:
            for i, E in enumerate(self.list1):
                for j, thk in enumerate(self.list2):
                    jobName = "Job-"+str(i+1)+str(j+1)

                    # create case and generate inp file
                    t_case = SimCase(jobName, side_len, side_len, nside, nside, thk, E)
                    t_case.writeInpFile(opt)

                    # add to case list
                    self.list_case.append(t_case)
                    print(jobName+" preprocess completed successfully")
                    self.nCases = self.nCases + 1

        # refinement test
        else:
            for i, nside in enumerate(self.list1):
                jobName = "Job-"+str(i+1)+str(i+1)

                # create case and generate inp file
                t_case = SimCase(jobName, side_len, side_len, nside, nside, thk, E)
                t_case.writeInpFile(opt)

                # add to case list
                self.list_case.append(t_case)
                print(jobName+" preprocess completed successfully")
                self.nCases = self.nCases + 1

    # run single case after re-meshing
    def run_case(self, icase, FLAG_GET_DIMS):
        # run simulations
        icase.run()

        # if the job completed in 1000 increments, continue
        if icase.FLAG_SUCCESS:
            # read ODB files
            icase.post_case()
            info = ""
            if FLAG_GET_DIMS:
                # get dimension info
                info = get_dims(icase.jobName, icase.nlen)
            return (icase.jobName + " postprocessing completed. Coordinates fetched!" + info)

        # if the job didn't complete in max increment, usually some error occured
        else:
            return icase.jobName+" has encountered errors!"
    
    # run all cases parallelly
    def run_all(self, FLAG_GET_DIMS=True):

        if self.nCases != len(self.list_case):
            raise "Number of cases does match!"

        #* the following operations are in parallel
        t_pool = mp.Pool(processes=self.max_threads)

        for icase in self.list_case:
            # check if inp file exists
            inp_name = icase.jobName + ".inp"
            if not os.path.isfile(inp_name):
                print(inp_name+" not found!")       # TODO: may need to throw exception
                continue
            # apply async if looks good
            t_pool.apply_async(self.run_case, args=(icase, FLAG_GET_DIMS,), callback=self.log_results)
            
        t_pool.close()
        t_pool.join()
        #* --------------------------- end parallel

    # save results to list
    def log_results(self, result):
        self.all_logs.append(result)

    # collect results
    def get_results(self):    
        # organize all results, and write good results to file
        out_file = "logs_all.txt"
        fout = open(out_file, 'w')
        for item in self.all_logs:
            if "errors" in item:
                self.all_errors.append(item)
            else:
                # get dimension infos
                jobName = item.split(" ",1)[0]
                t_str = item.split("!",1)
                self.all_dims[jobName] = t_str[-1]
                # print logs
                fout.write(t_str[0]+"\n")
        fout.close()

        # check and write errors to file
        if len(self.all_errors) != 0:
            with open("error_msg.txt", 'w') as msg:
                for i in self.all_errors:
                    msg.write(i+"\n")
        else:
            print("No errors! Good!")

    # write all parameters info
    def get_params_info(self, FLAG_GET_DIMS):
        out_file = "dims_all.txt"
        fout = open(out_file, 'w')
        fout.write("len\t wid\t nlen\t nwid\t thk\t E\t max_wid\t h_dist23\t max_height\t h_dist14\n")
        for icase in self.list_case:
            case_data = "{:.3f} {:.3f} {:d} {:d} {:e} {:e}".format(
                        icase.len, icase.wid, icase.nlen, icase.nwid, icase.thk, icase.E)
            if FLAG_GET_DIMS:
                info = self.all_dims[icase.jobName]
                case_data = case_data + " " + info + "\n"
                fout.write(case_data)
        fout.close()

# main function
def main():
    args = sys.argv
    if len(args) != 2:
        sys.exit("Must give an argument!")

    try:
        cmd = args[-1]

        # meshing and generate 1 inp
        if cmd == 'pre':
            # list for refinement test
            list1 = [20]
            list2 = list1
            FLAG_TYPE = False     # True - parameter test, False - refinement test
            inp_opt = 2
            t_Pool = SimPool(FLAG_TYPE, list1, list2)
            t_Pool.pre_all(inp_opt, 0.1, 20, 3e-4, 2e6)

        # simply run a single simulation
        elif cmd == 'srun':
            # list for refinement test
            list1 = [20]
            list2 = list1
            FLAG_TYPE = False     # True - parameter test, False - refinement test
            GET_DIMS = True
            inp_opt = 2
            t_Pool = SimPool(FLAG_TYPE, list1, list2)
            t_Pool.pre_all(inp_opt)       # use default parameters
            # t_Pool.run_case(0, True)
            t_Pool.run_all(GET_DIMS)
            t_Pool.get_results()
            t_Pool.get_params_info(GET_DIMS)

        # get dimension infos of a square hanging plate
        elif cmd == 'dim':
            # list_nside = list(range(20,75+1,5))
            # for i in range(len(list_nside)):
            #     nside = list_nside[i]
            #     fileID = int(str(i+1)+str(i+1))
            #     jobName = "Job-"+str(fileID)
            #     print(get_dims(jobName, nside))
            for i in range(4):
                nside = 20
                fileID = int(str(i+1)+str(i+1))
                jobName = "Job-"+str(fileID)
                print(get_dims(jobName, nside))

        # run refinement test
        elif cmd == 'refine':
            # list for refinement test
            list1 = list(range(25,75+1,5))
            # list1 = [20, 25, 30]
            list2 = list1
            FLAG_TYPE = False     # True - parameter test, False - refinement test
            GET_DIMS = True
            inp_opt = 2
            t_Pool = SimPool(FLAG_TYPE, list1, list2)
            t_Pool.pre_all(inp_opt)       # use default parameters
            t_Pool.run_all(GET_DIMS)
            t_Pool.get_results()
            t_Pool.get_params_info(GET_DIMS)

        # run with different aspect ratio
        elif cmd == 'ratio':
            raise "to be implemented..."

        # run multiple simulation
        elif cmd == 'param':
            # list for varying E (list1) and thk (list2)
            list1 = list(range(1,10))
            list1.extend(list(range(10,101,10)))
            list1 = [i*1e5 for i in list1]
            list2 = list(range(1,11))
            list2 = [i*1e-4 for i in list2]
            FLAG_TYPE = True     # True - parameter test, False - refinement test
            GET_DIMS = True
            inp_opt = 2
            t_Pool = SimPool(FLAG_TYPE, list1, list2)
            t_Pool.pre_all(inp_opt)       # use default parameters
            t_Pool.run_all(GET_DIMS)
            t_Pool.get_results()
            t_Pool.get_params_info(GET_DIMS)


        elif cmd == "clear":
            # TODO: implement a clear command
            # subprocess.call(["rm !(*.py|*.inp)"], shell=True, executable="/bin/bash")
            raise "to be implemented..."

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

if __name__ == "__main__":
    main()