﻿# brICk #

> Implemented between 2011 and 2016
> Author: Andreas Hartel
> Insititution: Kirchhoff-Insititut for Physics, Heidelberg University

brICk is a waf-based IC design work flow tool that offers design-independent build folder management. Multiple build runs of an IC design can be kept in parallel and can be switched between. Design source files, such as i.e. HDL code, tcl scripts and full custom design files can be copied into the components folder of the tool's directory structure. Their paths, given in a text file, will be used by brICk to hook into and allow it to execute the necessary tasks. These tasks may include

* abstract generation
* HDL code synthesis
* Place & Route
* Functional verification
* Formal verification
* Sign-off verification

Files resulting from these operations will always be avoided to be copied to the source file tree and will be put into a run-specific uniquely named result folder. In a first version, old runs will be kept, giving users the possibility to compare results of different runs (with different parameters or source code changes) to each other. However, brICk will not allow the user to recover and/or continue these runs once he has advanced to the next run.
In a future version, the user should be able to switch back to old runs and continue to work on them at any later point and at any given state. This can involve an abandonment of the strict distinction between source (i.e. input) file tree and result (i.e. output) file tree and make it necessary to copy the current task's tcl scripts and/or necessary other input files to the current run directory. To allow for continuation of past build runs, brICk will at least have to force the user to commit the current source file tree's state to the version control system and save the commit ID for later resumption.
Later on in the development of brICk, it should be possible to maintain different configurations to be able to keep one single brICk folder, holding in it's components folder the source files of different IC designs and making it even possible to switch between different designs.

brICk stands for |b|ackend |r|apid |IC| |k|it. It is intended as a hardware development counterpart to symwaf2ic, the central software build flow of the Electronic Vision(s) group which is also based on waf.
