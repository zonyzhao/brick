import os,re
from waflib import Task,Errors,Node,TaskGen,Configure,Node,Logs

def configure(conf):
	conf.load('brick_general')

	"""This function gets called by waf upon loading of this module in a configure method"""
	if not conf.env.BRICK_LOGFILES:
		conf.env.BRICK_LOGFILES = './logfiles'
	conf.env['CALIBRE_DRC'] = 'calibre'
	conf.env['CALIBRE_DRC_OPTIONS'] = [
			'-64', '-hier', '-turbo' ,'-turbo_all',
		]


@TaskGen.feature('calibre_drc')
def create_calibre_drc_task(self):

	self.rule_file = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'calibre_drc_rules_'+self.cellname))

	self.output_file_base = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),self.env.BRICK_RESULTS,self.cellname))
	self.svdb = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),self.env.BRICK_RESULTS,'svdb'))
	if not os.path.exists(self.svdb.abspath()):
		self.svdb.mkdir()

	output = self.output_file_base.change_ext('.drc.results')
	input = [self.layout_gds]

	f = open(self.rule_file.abspath(),"w")
	f.write("""
LAYOUT PATH "{0}"
LAYOUT PRIMARY {1}
LAYOUT SYSTEM GDSII
LAYOUT CASE YES

//LAYOUT RENAME TEXT "/</\\[/g" "/>/\\]/g"

DRC RESULTS DATABASE "{2}.drc.results"
DRC MAXIMUM RESULTS ALL
DRC MAXIMUM VERTEX 4096

DRC CELL NAME NO
DRC SUMMARY REPORT "{2}.drc.summary" REPLACE

VIRTUAL CONNECT COLON NO
VIRTUAL CONNECT REPORT NO

DRC ICSTATION YES

""".format(self.layout_gds.abspath(),self.cellname,self.output_file_base.abspath()))

	if hasattr(self,'unselect_checks') and len(self.unselect_checks)>0:
		f.write('DRC UNSELECT CHECK\n')
		for line in getattr(self,'unselect_checks',[]):
			f.write('\t"'+line+'"\n')

	for inc in self.includes:
		f.write('\nINCLUDE '+inc.abspath())
		input.append(inc)

	f.close()


	t = self.create_task('calibreDrcTask', input, output)

class calibreDrcTask(Task.Task):
	vars = ['CALIBRE_DRC','CALIBRE_DRC_OPTIONS']
	def run(self):
		conditional_options = ""
		if hasattr(self.generator,'hcells'):
			conditional_options += ' -hcell '+self.generator.hcells_file.abspath()
		run_str = '%s -drc %s %s %s' % (self.env.CALIBRE_DRC, conditional_options, " ".join(self.env.CALIBRE_DRC_OPTIONS), self.generator.rule_file.abspath())
		out = ""
		try:
			out = self.generator.bld.cmd_and_log(run_str)#, quiet=Context.STDOUT)
		except Exception as e:
			out = e.stdout

		logfile = self.generator.path.get_bld().make_node(os.path.join(self.generator.path.bld_dir(),self.env.BRICK_LOGFILES,'calibre_drc_'+self.generator.cellname+'.log'))
		f = open(logfile.abspath(),'w')
		f.write(out)
		f.close()

		found_error = 0
		with open(logfile.abspath(),'r') as lgf:
			for line in lgf:
				if re.match('LVS completed. INCORRECT',line):
					print line
					found_error = 1
				elif re.match('ERROR:',line):
					print line
					found_error = 1
				#elif re.match('@W: CL218',line):
				#	print line
				#	found_error = 1

		return found_error

		return 0

@TaskGen.feature('calibre_rve_drc')
def create_calibre_rve_drc_task(self):
	if not self.report:
		Logs.error('Please name an existing report file for feature \'cds_rve_drc\'')
		return

	t = self.create_task('calibreRveDrcTask', self.report)

@Task.always_run
class calibreRveDrcTask(Task.Task):
	run_str = "${CALIBRE_DRC} -rve -drc ${SRC[0].abspath()}"

# for convenience
@Configure.conf
def calibre_drc(bld,*k,**kw):
	set_features(kw,'calibre_drc')
	return bld(*k,**kw)

# vim: noexpandtab: