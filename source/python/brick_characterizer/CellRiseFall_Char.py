from timingsignal import TimingSignal
from brick_characterizer.CharBase import CharBase


class CellRiseFall_Char(CharBase):

    def __init__(self,toplevel,output_filename,temperature,use_spectre=False):

        self.toplevel = toplevel
        self.output_filename = output_filename

        self.input_rise_time = 0.1
        self.load_capacitance = 0.01
        self.clock_rise_time = 0.1 #ns
        self.signal_rise_time = 0.1 #ns
        self.initial_delay = 0.4 #ns
        self.simulation_length = 12.0 #ns

        self.slew_lower_rise = 0.3
        self.slew_upper_rise = 0.7
        self.slew_lower_fall = 0.3
        self.slew_upper_fall = 0.7

        self.stimulus_signals = []

        self.delays = {}
        self.transitions = {}

        super(CellRiseFall_Char,self).__init__(temperature,use_spectre)

    def get_delays(self):
        return self.delays

    def get_transitions(self):
        return self.transitions

    def get_first_table_param(self):
        return self.get_input_rise_time()

    def get_second_table_param(self):
        return self.get_load_capacitance()

    def get_input_rise_time(self):
        return self.input_rise_time

    def set_input_rise_time(self,value):
        self.input_rise_time = value

    def get_load_capacitance(self):
        return self.load_capacitance

    def set_load_capacitance(self,value):
        self.load_capacitance = value

    def whats_my_name(self):
        return 'CellRiseFall_Char_inTr'+str(self.input_rise_time)+'_cap'+str(self.load_capacitance)

    def log_my_name(self):
        return self.state+'\tin'+str(self.input_rise_time)+'\tcap'+str(self.load_capacitance)

    def next_step(self):
        # this class has only one step
        if self.state == 'init':
            self.state = 'delay'

            self.write_spice_file()
            if not self.run() == 0:
                return 1
            self.check_timing()

            self.state = 'done'

            return 0

        return 0

    def get_current_filename(self):
        import os
        name,ext = os.path.splitext(self.output_filename)
        return name+'_inTr'+str(self.input_rise_time)+'_cap'+str(self.load_capacitance)+'_'+self.state+ext

    def add_timing_signals(self,clocks,tim_sig):

        self.clocks = clocks

        if self.added_static_signals:
            for name in clocks.iterkeys():
                if self.static_signals.has_key(name):
                    raise Exception('Clock signal '+name+' has already been defined as a static signal.')

        for signal,related in self.itersignals(tim_sig,
                                               eval_index_expression=True):
                if self.added_static_signals:
                    if self.static_signals.has_key(signal):
                        raise Exception('Timing signal '+signal+' has already been defined as a static signal.')

                t = TimingSignal(signal,related)
                self.timing_signals[signal] = t
                # The following list stores a unique list of the stimulus
                # signals for later pulse source generation in the net list
                self.stimulus_signals.append(t.stimulus())

                self.delays[signal] = []
                self.transitions[signal] = []

        self.stimulus_signals = set(self.stimulus_signals)
        self.added_timing_signals = True


    def generate_timing_signals(self):

        for name,direction in self.clocks.iteritems():
            self.generate_clock_edge(name,direction)
            self.add_probe(name)

        for signal in self.stimulus_signals:
            self.generate_two_edges(signal,self.signal_rise_time,self.initial_delay,self.initial_delay)
            #self.logger_debug("Generating edge for "+signal+" with rising delay "+str(self.initial_delay)+ " and falling delay "+str(self.initial_delay))
            self.add_probe(signal)
            self.set_initial_condition(signal,self.low_value)

        for signal_name,signal_obj in self.timing_signals.iteritems():
            self.add_probe(signal_name)
            self.add_capacitance(signal_name,self.load_capacitance)
            if signal_obj.unateness() == 'positive_unate':
                self.set_initial_condition(signal_name,self.low_value)
            elif signal_obj.unateness() == 'negative_unate':
                self.set_initial_condition(signal_name,self.high_value)
            else:
                raise Exception('Probe signal '+signal_name+' has unknown unate-ness. Please specify \'positive_unate\' or \'negative_unate\'')


    def generate_clock_edge(self,name,direction):
        self.append_out('V'+name+' '+name+' 0 pwl(')
        if direction == 'R':
            self.append_out('+ 0.0000000e+00 0.0000000e+00')
            self.append_out('+ '+str(self.timing_offset-self.clock_period*1.0 - self.clock_rise_time*0.5)+'e-9 '+str(self.low_value))
            self.append_out('+ '+str(self.timing_offset-self.clock_period*1.0 + self.clock_rise_time*0.5)+'e-09 '+str(self.high_value))
            self.append_out('+ '+str(self.timing_offset-self.clock_period*0.5)+'e-9 '+str(self.high_value))
            self.append_out('+ '+str(self.timing_offset-self.clock_period*0.5 + self.clock_rise_time)+'e-09 '+str(self.low_value))

            self.append_out('+ '+str(self.timing_offset - self.clock_rise_time*0.5)+'e-9 '+str(self.low_value))
            self.append_out('+ '+str(self.timing_offset + self.clock_rise_time*0.5)+'e-09 '+str(self.high_value))

            self.append_out('+ '+str(self.timing_offset+self.clock_period*0.5)+'e-9 '+str(self.high_value))
            self.append_out('+ '+str(self.timing_offset+self.clock_period*0.5 + self.clock_rise_time)+'e-09 '+str(self.low_value))
            self.append_out('+ '+str(self.timing_offset+self.clock_period*1.0 - self.clock_rise_time*0.5)+'e-9 '+str(self.low_value))
            self.append_out('+ '+str(self.timing_offset+self.clock_period*1.0 + self.clock_rise_time*0.5)+'e-09 '+str(self.high_value))

            self.append_out('+ '+str(self.timing_offset+self.clock_period*1.5)+'e-9 '+str(self.high_value))
            self.append_out('+ '+str(self.timing_offset+self.clock_period*1.5 + self.clock_rise_time)+'e-09 '+str(self.low_value))
            self.append_out('+ '+str(self.timing_offset+self.clock_period*2.0 - self.clock_rise_time*0.5)+'e-9 '+str(self.low_value))
            self.append_out('+ '+str(self.timing_offset+self.clock_period*2.0 + self.clock_rise_time*0.5)+'e-09 '+str(self.high_value))

        else:
            self.append_out('+ 0.0000000e+00 '+str(self.high_value)+'000000e+00')
            self.append_out('+ '+str(self.timing_offset-self.clock_period*1.0 - self.clock_rise_time*0.5)+'e-9 '+str(self.high_value))
            self.append_out('+ '+str(self.timing_offset-self.clock_period*1.0 + self.clock_rise_time*0.5)+'e-09 '+str(self.low_value))
            self.append_out('+ '+str(self.timing_offset-self.clock_period*0.5)+'e-9 '+str(self.low_value))
            self.append_out('+ '+str(self.timing_offset-self.clock_period*0.5 + self.clock_rise_time)+'e-09 '+str(self.high_value))

            self.append_out('+ '+str(self.timing_offset - self.clock_rise_time*0.5)+'e-9 '+str(self.high_value))
            self.append_out('+ '+str(self.timing_offset + self.clock_rise_time*0.5)+'e-09 '+str(self.low_value))

            self.append_out('+ '+str(self.timing_offset+self.clock_period*0.5)+'e-9 '+str(self.low_value))
            self.append_out('+ '+str(self.timing_offset+self.clock_period*0.5 + self.clock_rise_time)+'e-09 '+str(self.high_value))
            self.append_out('+ '+str(self.timing_offset+self.clock_period*1.0 - self.clock_rise_time*0.5)+'e-9 '+str(self.high_value))
            self.append_out('+ '+str(self.timing_offset+self.clock_period*1.0 + self.clock_rise_time*0.5)+'e-09 '+str(self.low_value))

            self.append_out('+ '+str(self.timing_offset+self.clock_period*1.5)+'e-9 '+str(self.low_value))
            self.append_out('+ '+str(self.timing_offset+self.clock_period*1.5 + self.clock_rise_time)+'e-09 '+str(self.high_value))
            self.append_out('+ '+str(self.timing_offset+self.clock_period*2.0 - self.clock_rise_time*0.5)+'e-9 '+str(self.high_value))
            self.append_out('+ '+str(self.timing_offset+self.clock_period*2.0 + self.clock_rise_time*0.5)+'e-09 '+str(self.low_value))


    def generate_two_edges(self,signal,transition_time,rising_delay,falling_delay):
        self.append_out('V'+signal+' '+signal+' 0 pwl(')

        start_time = self.timing_offset - rising_delay
        start_time_2 = self.timing_offset*2 - falling_delay
        first_value = self.low_value
        second_value = self.high_value

        self.append_out('+ 0.0000000e+00 '+str(first_value)+'e+00')
        self.append_out('+ '+str(start_time)+'e-9 '+str(first_value)+'e+0')
        self.append_out('+ '+str(start_time+transition_time)+'e-09 '+str(second_value)+'e+00)')
        self.append_out('+ '+str(start_time_2)+'e-9 '+str(second_value)+'e+00')
        self.append_out('+ '+str(start_time_2+transition_time)+'e-09 '+str(first_value)+'e+00)')

    def add_capacitance(self,signal_name,capacitance):
        self.append_out('C'+signal_name+' '+signal_name+' 0 '+str(capacitance)+'pf')

    def add_pseudo_static_signals(self,signals):
        """Pseudo-Static signals in the case of an Output timing
        characterization are the input timing signals. The function
        *do_characterization* passes the input timing signals to this function.
        It assigns zero to all of them during simulation."""

        if not self.added_timing_signals:
            raise Exception('Cannot add pseudo-static signals before timing_signals have been added. Please call this function afterwards.')

        not_known = lambda name: not name in self.stimulus_signals and not self.clocks.has_key(name)
        for signal,related in self.itersignals(signals):
            if not_known(signal):
                self.static_signals[signal] = 0

        self.added_static_signals = True


    def check_timing(self):
        # parse result file
        # after this step, all edges are identified
        if not self.parse_print_file() == 0:
            return 1
        # find clock edge
        clock_edges = {}
        for clock_name, clock_dir in self.clocks.iteritems():
            if not clock_edges.has_key(clock_name):
                clock_edges[clock_name] = []
            if (clock_dir == 'R'):
                clock_edges[clock_name].append(self.get_rising_edges(clock_name)[1*3+1])
                clock_edges[clock_name].append(self.get_rising_edges(clock_name)[3*3+1])
                # cnt = 0
                # for edge in self.get_rising_edges(clock_name)[1,4,2]:
                    # if cnt == 1:
                        # clock_edges[clock_name].append(edge)
                    # cnt = cnt + 1 if cnt < 2 else 0
                self.logger_debug( "Rising edge of "+clock_name+" at "+" ".join([str(x) for x in clock_edges[clock_name]]))
            else:
                clock_edges[clock_name].append(self.get_falling_edges(clock_name)[1*3+1])
                clock_edges[clock_name].append(self.get_falling_edges(clock_name)[3*3+1])
                # cnt = 0
                # for edge in self.get_falling_edges(clock_name):
                    # if cnt == 1:
                        # clock_edges[clock_name].append(edge)
                    # cnt = cnt + 1 if cnt < 2 else 0
                self.logger_debug( "Falling edge of "+clock_name+" at "+" ".join([str(x) for x in clock_edges[clock_name]]))



        for timing_signal in self.timing_signals.itervalues():
            # some alias pointers
            stimulus = timing_signal.stimulus()
            probe = timing_signal.name()
            probe_lc = probe
            if not self.use_spectre:
                probe_lc = probe.lower()
            # initial timing values
            delta_t = [0,0]
            tran = [0,0]

            self.logger_debug( "Rising edges of "+probe+" at "+" ".join([str(x) for x in self.get_rising_edges(probe_lc)]))
            self.logger_debug( "Falling edges of "+probe+" at "+" ".join([str(x) for x in self.get_falling_edges(probe_lc)]))

            if timing_signal.unateness() == 'positive_unate':
                r_edges_probe = self.get_rising_edges(probe_lc)
                if r_edges_probe:
                    while len(r_edges_probe) > 0:
                        lower  = r_edges_probe.pop(0)
                        middle = r_edges_probe.pop(0)
                        upper  = r_edges_probe.pop(0)
                        # get switching point
                        delta_t[0] = middle - clock_edges[timing_signal.clock()][0]
                        # get rising transition
                        tran[0] = upper - lower
                        if delta_t[0] < 0 or delta_t[0] > self.timing_offset*1.e-9:
                            self.logger_debug("Rising edge at "+str(middle)+" for signal " \
                                              +probe+" too far away from clock edge")
                            delta_t[0] = self.infinity
                        else:
                            self.logger_debug( "Delay: "+str(delta_t[0]))
                            break
                else:
                    self.logger_error("Rising edge for signal "+probe+" not found but expected.")
                    return 1

                f_edges_probe = self.get_falling_edges(probe_lc)
                if f_edges_probe:
                    while len(f_edges_probe) > 0:
                        lower  = f_edges_probe.pop(0)
                        middle = f_edges_probe.pop(0)
                        upper  = f_edges_probe.pop(0)
                        # get threshold time for switching point
                        delta_t[1] = middle - clock_edges[timing_signal.clock()][1]
                        # get threshold time for falling transition upper
                        tran[1] = upper-lower
                        if delta_t[1] < 0 or delta_t[1] > self.timing_offset*1.e-9:
                            self.logger_debug("Falling edge at "+str(middle)+" for signal " \
                                              +probe+" too far away from clock edge")
                            delta_t[1] = self.infinity
                        else:
                            self.logger_debug( "Delay: "+str(delta_t[1]))
                            break
                else:
                    self.logger_error("Falling edge for signal "+probe+" not found but expected.")
                    return 1


            elif timing_signal.unateness() == 'negative_unate':
                f_edges_probe = self.get_falling_edges(probe_lc)
                if f_edges_probe:
                    while len(f_edges_probe) > 0:
                        lower  = f_edges_probe.pop(0)
                        middle = f_edges_probe.pop(0)
                        upper  = f_edges_probe.pop(0)
                        # get threshold time for switching point
                        delta_t[1] = middle - clock_edges[timing_signal.clock()][0]
                        # get threshold time for rising transition upper
                        tran[1] = upper - lower
                        if delta_t[1] < 0 or delta_t[1] > self.timing_offset*1.e-9:
                            self.logger_debug("Falling edge at "+str(middle)+" for signal " \
                                              +probe+" too far away from clock edge")
                            delta_t[1] = self.infinity
                        else:
                            self.logger_debug( "Delay: "+str(delta_t[1]))
                            break
                else:
                    self.logger_error("Falling edge for signal "+probe_lc+" not found but expected.")
                    return 1

                r_edges_probe = self.get_rising_edges(probe_lc)
                if r_edges_probe:
                    while len(r_edges_probe) > 0:
                        lower  = r_edges_probe.pop(0)
                        middle = r_edges_probe.pop(0)
                        upper  = r_edges_probe.pop(0)
                        # get threshold time for switching point
                        delta_t[0] = middle - clock_edges[timing_signal.clock()][1]
                        # get threshold time for rising transition upper
                        tran[0] = upper - lower
                        if delta_t[0] < 0 or delta_t[0] > self.timing_offset*1.e-9:
                            self.logger_debug("Rising edge at "+str(middle)+" for signal " \
                                              +probe+" too far away from clock edge")
                            delta_t[0] = self.infinity
                        else:
                            self.logger_debug( "Delay: "+str(delta_t[0]))
                            break
                else:
                    self.logger_error("Rising edge for signal "+probe_lc+" not found but expected.")
                    return 1

            self.delays[probe] = delta_t
            self.transitions[probe] = tran

            self.logger_debug('Delays for signal \''+probe+'\' are rising: '+str(self.delays[probe][0])+' and falling: '+str(self.delays[probe][1]))
            self.logger_debug('Transition times for signal \''+probe+'\' are rising: '+str(self.transitions[probe][0])+' and falling: '+str(self.transitions[probe][1]))

        return 0

    def parse_print_file(self):
        import subprocess,os
        call = ''
        if self.use_spectre:
            call = ['python', os.environ['BRICK_DIR']+'/source/python/brick_characterizer/parse_print_file_spectre.py', self.get_printfile_name(), str(self.high_value*self.rise_threshold), str(self.high_value*self.fall_threshold), str(self.high_value*self.slew_lower_rise), str(self.high_value*self.slew_upper_rise), str(self.high_value*self.slew_lower_fall), str(self.high_value*self.slew_upper_fall)]
        else:
            call = ['python', os.environ['BRICK_DIR']+'/source/python/brick_characterizer/parse_print_file.py', self.get_printfile_name(), str(self.high_value*self.rise_threshold), str(self.high_value*self.fall_threshold), str(self.high_value*self.slew_lower_rise), str(self.high_value*self.slew_upper_rise), str(self.high_value*self.slew_lower_fall), str(self.high_value*self.slew_upper_fall)]

        self.logger_debug(" ".join(call))
        returncode = subprocess.call(call)

        if not returncode == 0:
            return 1

        import pickle
        with open(self.get_printfile_name()+'_rising') as input:
            self.rising_edges = pickle.load(input)
        with open(self.get_printfile_name()+'_falling') as input:
            self.falling_edges = pickle.load(input)

        return 0
