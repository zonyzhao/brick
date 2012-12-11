import os,re
from waflib import Task,Errors,Node,TaskGen,Configure,Node,Logs

def configure(conf):
	"""This function gets called by waf upon loading of this module in a configure method"""

	conf.load('brick_general')

	if not conf.env.BRICK_LOGFILES:
		conf.env.BRICK_LOGFILES = './logfiles'
	conf.env['SYNOPSYS_DCSHELL'] = 'dc_shell'
	conf.env['SYNOPSYS_DCSHELL_OPTIONS'] = [
			#'-topo',
		]



@TaskGen.feature('synopsys_dcshell')
def create_synopsys_dcshell_task(self):
	# assemble file names for tcl scripts
	self.main_tcl_script = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'dc_shell_'+self.toplevel+'.tcl'))
	self.sourcelist_tcl_script = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'dc_shell_sourcelist_'+self.toplevel+'.tcl'))
	self.setup_tcl_script = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'dc_shell_setup.tcl'))

	if not getattr(self,'verilog_sources',None):
		self.verilog_sources = []
	if not getattr(self,'systemverilog_sources',None):
		self.systemverilog_sources = []
	if not getattr(self,'vhdl_sources',None):
		self.vhdl_sources = []


	# check for existance of results dir
	# the actual results dir is a subdirectory of BRICK_RESULTS
	# called dc_shell_$DESIGN_NAME
	self.results_dir = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),self.env.BRICK_RESULTS))
	if not self.results_dir.find_dir('dc_shell_'+self.toplevel):
		self.results_dir = self.results_dir.make_node('dc_shell_'+self.toplevel)
		self.results_dir.mkdir()
	else:
		self.results_dir = self.results_dir.make_node('dc_shell_'+self.toplevel)
	if not self.results_dir.find_dir('results'):
		self.results_dir.make_node('results').mkdir()
	if not self.results_dir.find_dir('reports'):
		self.results_dir.make_node('reports').mkdir()

	output_netlist = self.results_dir.find_node('results').find_node(self.toplevel+'.v')

	# load extra package with tcl templates
	from synopsys_dcshell_tcl import dc_shell_setup_tcl, dc_shell_main_tcl
	# write main tcl script
	f = open(self.main_tcl_script.abspath(),"w")
	f.write(dc_shell_main_tcl % (
				self.sourcelist_tcl_script.abspath(),
				self.setup_tcl_script.abspath(),
				'{'+' '.join([x.abspath() for x in getattr(self,'search_paths',[])])+'}',
				getattr(self,'constraints_file','0')))
	f.close()

	# write setup tcl script (containing mostly process specific data)
	# the only variable input here is the DESIGN_NAME a.k.a. self.toplevel
	f = open(self.setup_tcl_script.abspath(),"w")
	f.write(dc_shell_setup_tcl[getattr(self,'process','default')] % (self.toplevel))
	f.close()

	# write out the source list
	f = open(self.sourcelist_tcl_script.abspath(),"w")
	try:
		sourcelist_string = "set systemverilog_source_list [list \\\n"+" \\\n".join([x.abspath() for x in self.systemverilog_sources])+" \\\n]\n\n"
		sourcelist_string += "set verilog_source_list [list \\\n"+" \\\n".join([x.abspath() for x in self.verilog_sources])+" \\\n]\n\n"
		sourcelist_string += "set vhdl_source_list [list \\\n"+" \\\n".join([x.abspath() for x in self.vhdl_sources])+" \\\n]\n\n"
	except AttributeError:
		Logs.error('You have given an undefined node object as netlist for feature "synopsys_dcshell".')

	f.write(sourcelist_string)
	f.close()

	t = self.create_task('synopsysDcshellTask', self.systemverilog_sources+self.verilog_sources, output_netlist)


class synopsysDcshellTask(Task.Task):
	vars = ['SYNOPSYS_DCSHELL','SYNOPSYS_DCSHELL_OPTIONS']

	def run(self):
		run_str = '%s %s -f %s' % (self.env.SYNOPSYS_DCSHELL, " ".join(self.env.SYNOPSYS_DCSHELL_OPTIONS), self.generator.main_tcl_script.abspath())
		out = ""
		try:
			out = self.generator.bld.cmd_and_log(run_str)#, quiet=Context.STDOUT)
		except Exception as e:
			out = e.stdout + e.stderr

		logfile = self.generator.path.get_bld().make_node(os.path.join(self.generator.path.bld_dir(),self.env.BRICK_LOGFILES,'dc_shell_'+self.generator.toplevel+'.log'))
		f = open(logfile.abspath(),'w')
		f.write(out)
		f.close()

		return 0


