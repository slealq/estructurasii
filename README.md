# estructurasii
Curso de Estructuras de Computadores II, Universidad de Costa Rica

# Dependencias:
The code was written in Python 2.7, please check your version with python2 --version (If this fails, install python2). The following was tested using Ubuntu Trusty and Arch Linux 4.16.4-1.

You'll need two programs for compiling Python code (Nuitka), and the other for running parallel task (GNU Parallel). For the following command, you are assumed to have pip. If you don't, install it using sudo apt-get install python-pip:

     sudo pip install nuitka
     sudo apt-get install parallel
 

Luego compilar con:

      nuitka --recurse-all cache.py

=> El ejecutable (.exe) se puede correr como ./cache.exe (es un binario de python)

Para informacion del uso, usar ./cache.exe -h
