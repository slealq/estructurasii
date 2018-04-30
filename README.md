# estructurasii
Curso de Estructuras de Computadores II, Universidad de Costa Rica

Clone this repo with:

     git clone https://github.com/slealq/estructurasii
     cd estructurasii

# Dependencies
The code was written in Python 2.7, please check your version with python2 --version (If this fails, install python2). The following was tested using Ubuntu Trusty and Arch Linux 4.16.4-1.

You'll need two programs for compiling Python code (Nuitka), and the other for running parallel task (GNU Parallel). For the following command, you are assumed to have pip. If you don't, install it using sudo apt-get install python-pip:

     sudo pip install nuitka
     sudo apt-get install parallel
 
Check if nuitka was installed. If nuitka3 was installed instead, the you need to install pip2, and run sudo pip2 install nuitka.

# Compilation
Now you can compile the python code: In the folder containing cache.py do: 

     nuitka --recurse-all --recurse-directory=../ cache.py
     
This should output a cache.exe which is a linux binary (Don't be fooled by the extension). 

# Cache Simulator
The ./cache.exe is a program used for simulating cache. Its input is a trace file with the format # ls addresss(hex) ic. Run ./cache.exe to get an idea of the parameters it takes. --debug, --csv tracename, and -m are not necesary to run the script. 

# Options 
     -t Cache Size in (KB)
          example: -t 4 creates a cache of 4KB
     -l Line Size (Block Size) in (B)
          example: -l 16 creates a cache with block size of 16 Bytes
     -a Asociativity (Ways): 
          example: -a 2 creates a cache of 2 ways
     --rp Replacement Policy (LRU, NRU, SRRIP, RANDOM):
          example: --rp LRU
          example: --rp SRRIP -m 4 creates a cache with SRRIP replacement policy, using m=4 (recently used values are up to 2^4)
     --mp Miss Penalty, in Cycles
          example: --mp 2 all time calculation is done considering 2 cycles penalty for miss
     --debug Debug flag enables cache step by step replacement, and flags raised in each step (Flag codes are defined in sets)
          example --debug
     --csv tracename 
          example --csv mcf outputs the result into a csv file, with the tracename in one column
     -m (Only used for SRRIP)
          example --rp SRRIP -m 2 (See --rp for more details
          
# Test traces
In order to run this code, you will need the test traces used in the scripts. You can download them going to this link https://drive.google.com/drive/folders/15Z0Z0cpxmuLTrfKjuVrbsAw4fJ9tGI2s or, use traces done by Jeancachu: https://github.com/jeancahu/cache_simulator_test_traces (This implies that you modify the simulation scripts).

# Simulation expected time
For a single run of the ./cache.exe, the worst case using an AMD PRO A10-8700B R6, 10 Compute Cores 4C+6G @ 4x 1.8GHz, was 80 seconds.

For simulation scripts (containning several calls of ./cache.exe) results were:

     simulation_1: 1m35s
     
     simulation_2: 1m31s
     
     simulation_3: 14m21s
     
Note: Simulation_3 runs 40 simulations inside, so it will take a while no matter what.

# Results: 
You can read the following paper to see our pick of parameters according to simulation results: https://www.sharelatex.com/read/xxkftxvjfskf. 
